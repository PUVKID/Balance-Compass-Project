import tempfile
import unittest
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

from rentlab import engine
from rentlab import public_sources, feature_store, expansion


class ExpansionTests(unittest.TestCase):
    def contracts(self):
        return pd.DataFrame({'source_row_id':['a','b','c'], 'cluster_id':['x','x','y'],
                             'date':pd.to_datetime(['2025-01-02']*3), 'region':['서울']*3})

    def observations(self):
        return pd.DataFrame([
            dict(entity_key='x',feature='households',value=120,valid_from='2020-01-01',valid_to='',
                 published_at='2024-01-01T00:00:00+09:00',source_id='fixture',record_id='1'),
            dict(entity_key='x',feature='households',value=999,valid_from='2020-01-01',valid_to='',
                 published_at='2025-01-02T00:00:00+09:00',source_id='fixture',record_id='2')])

    def test_asof_excludes_same_day_and_preserves_unmatched(self):
        frame,audit=feature_store.join_features(self.contracts(),self.observations(),mode='strict_asof')
        self.assertEqual(len(frame),3)
        self.assertEqual(frame.households.iloc[:2].tolist(),[120,120])
        self.assertTrue(pd.isna(frame.households.iloc[2]))
        self.assertEqual(audit['features']['households']['matched_rows'],2)

    def test_duplicate_vintage_rejected(self):
        obs=self.observations().iloc[[0,0]]
        with self.assertRaises(ValueError):feature_store.join_features(self.contracts(),obs)

    def test_expired_and_future_validity_excluded(self):
        obs=self.observations().iloc[[0]].copy();obs['valid_to']='2025-01-02'
        f,_=feature_store.join_features(self.contracts(),obs)
        self.assertTrue(f.households.isna().all())
        obs['valid_to']='';obs['valid_from']='2025-01-03'
        f,_=feature_store.join_features(self.contracts(),obs)
        self.assertTrue(f.households.isna().all())

    def test_rejects_target_and_nonfinite_and_missing_key(self):
        for col,val in [('feature','actual_won'),('value',float('inf')),('entity_key','')]:
            obs=self.observations().iloc[[0]].copy();obs[col]=val
            with self.assertRaises(ValueError):feature_store.join_features(self.contracts(),obs)

    def test_snapshot_does_not_claim_historical_availability(self):
        obs=self.observations().iloc[[0]].copy();obs['published_at']='2026-01-01T00:00:00+09:00'
        f,_=feature_store.join_features(self.contracts(),obs)
        self.assertTrue(f.households.isna().all())
        f,a=feature_store.join_features(self.contracts(),obs,mode='retrospective_snapshot')
        self.assertEqual(f.households.iloc[0],120)
        self.assertFalse(a['historical_availability_proven'])

    def test_duplicate_contract_id_and_colliding_column_rejected(self):
        for f in [pd.concat([self.contracts(),self.contracts().iloc[[0]]]), self.contracts().assign(households=5)]:
            with self.assertRaises(ValueError):feature_store.join_features(f,self.observations())

    def test_standard_page_count_and_shape(self):
        h={'totalCount':3,'columList':[{'columCode':'ID','columNm':'아이디'}]}
        self.assertEqual(len(public_sources.validate_pages(h,[[{'ID':1},{'ID':2}],[{'ID':3}]])),3)
        for pages in [[[{'ID':1}]], [[{'ID':1}],[{'ID':1}],[{'ID':1}]], [[{'bad':1},{'ID':2},{'ID':3}]]]:
            with self.assertRaises(ValueError):public_sources.validate_pages(h,pages)

    def test_readiness_missing_sources_and_unproven_labels(self):
        r=expansion.readiness([],mode='strict_asof',labels_verified=False)
        self.assertFalse(r['ready'])
        self.assertIn('label_availability_unproven',r['blockers'])
        self.assertIn('external_features_missing',r['blockers'])

    def test_extra_numeric_reaches_model_and_no_deposit_ablation(self):
        data=engine.prepare(engine.synthetic_data())[0]
        data=data[data.exclusion_reason.eq('') & data.rent.gt(0)].copy()
        data['households']=np.arange(len(data))%4
        result,test,_=engine.fit_target(data,'monthly',None,extra_numeric=['households'])
        self.assertIn('households',result['input_numeric'])
        self.assertIn('households',result['no_deposit_input_numeric'])
        self.assertNotIn('deposit',result['no_deposit_input_numeric'])
        self.assertEqual(len(test),result['split_counts']['test'])

    def test_comparison_same_rows_and_fixed_model(self):
        data=engine.prepare(engine.synthetic_data())[0]
        data=data[data.exclusion_reason.eq('') & data.rent.gt(0)].copy()
        data['households']=np.arange(len(data))%5
        result,predictions=expansion.run_comparison(data,'monthly',{'building':['households']})
        self.assertEqual(result['inference_role'],'exploratory')
        self.assertEqual(len(predictions),result['n'])
        self.assertEqual(result['comparisons']['without_building']['model'],result['full_model'])
        self.assertTrue(np.isfinite(predictions['prediction_full_won']).all())

    def test_paired_cluster_ci_known_effect_and_missing_clusters(self):
        frame=pd.DataFrame({'cluster_id':[str(i) for i in range(25)],'actual_won':[10]*25,
                            'prediction_full_won':[10]*25,'prediction_basic_won':[12]*25})
        result=expansion.paired_cluster_ci(frame,'prediction_basic_won')
        self.assertEqual(result['effect_won'],2)
        self.assertEqual(result['ci_won'],[2,2])
        self.assertEqual(result['family_adjustment'],'none; exploratory pointwise interval')
        frame.loc[0,'cluster_id']=''
        self.assertIsNone(expansion.paired_cluster_ci(frame,'prediction_basic_won')['ci_won'])

    def test_ambiguous_overlapping_versions_and_naive_publication_rejected(self):
        obs=self.observations().iloc[[0]].copy()
        other=obs.copy();other['valid_from']='2021-01-01';other['record_id']='3'
        with self.assertRaises(ValueError):feature_store.join_features(self.contracts(),pd.concat([obs,other]))
        obs['published_at']='2024-01-01'
        with self.assertRaises(ValueError):feature_store.join_features(self.contracts(),obs)

    def test_facility_counts_do_not_double_count_station_lines(self):
        from rentlab import spatial_features
        origins=pd.DataFrame({'cluster_id':['x','y'],'latitude':[37,37],'longitude':[127,np.nan]})
        facilities=pd.DataFrame({'facility_id':['s','s','t'],'latitude':[37,37,37.02],
                                 'longitude':[127,127,127],'line':['1','2','3']})
        f=spatial_features.station_features(origins,facilities)
        self.assertAlmostEqual(f.station_distance_m.iloc[0],0,places=6)
        self.assertEqual(f.stations_1000m.iloc[0],1)
        self.assertEqual(f.lines_1000m.iloc[0],2)
        self.assertTrue(pd.isna(f.station_distance_m.iloc[1]))
        self.assertEqual(f.coordinate_status.iloc[1],'missing')

    def test_source_feature_manifest_rejects_unverified_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest={'status':'verified_feature_snapshot','features':['households'],'path':'none.csv','sha256':'0'*64}
            with self.assertRaises(ValueError):feature_store.validate_feature_manifest(manifest,Path(tmp))

    def test_group_metrics_keep_interval_coverage_and_width(self):
        f=pd.DataFrame({'actual_won':[10,30],'prediction_full_won':[10,10],
                        'lower_full_won':[5,5],'upper_full_won':[15,15]})
        m=expansion.prediction_metrics(f,'prediction_full_won')
        self.assertEqual(m['coverage'],.5)
        self.assertEqual(m['width'],10)
        self.assertEqual(m['interval_score'],160)

    def test_missing_station_line_is_not_zero(self):
        from rentlab import spatial_features
        origins=pd.DataFrame({'cluster_id':['x'],'latitude':[37],'longitude':[127]})
        fac=pd.DataFrame({'facility_id':['s'],'latitude':[37],'longitude':[127],'line':[None]})
        with self.assertRaises(ValueError):spatial_features.station_features(origins,fac)

    def test_korea_facility_coordinate_outlier_rejected(self):
        from rentlab import spatial_features
        origins=pd.DataFrame({'cluster_id':['x'],'latitude':[37],'longitude':[127]})
        fac=pd.DataFrame({'facility_id':['s'],'latitude':[37],'longitude':[137.2],'line':['1']})
        with self.assertRaises(ValueError):spatial_features.station_features(origins,fac)

    def test_source_rows_and_acquisition_time_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.csv';source.write_text('id,value\n1,10\n2,20\n',encoding='utf-8')
            obs=root/'obs.csv';self.observations().iloc[[0]].assign(feature='base_rate').to_csv(obs,index=False)
            m={'status':'verified_feature_snapshot','features':['base_rate'],'key_column':'cluster_id',
               'path':'obs.csv','sha256':hashlib.sha256(obs.read_bytes()).hexdigest(),'rows':1,'sources':[
                 {'source_id':'fixture','status':'acquired_current_snapshot','source_url':'https://example.org',
                  'path':'source.csv','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':999,
                  'acquired_at':'2026-11-26T00:00:00+09:00','encoding':'utf-8'}]}
            with self.assertRaises(ValueError):feature_store.validate_feature_manifest(m,root)
            m['sources'][0]['rows']=2;m['sources'][0]['acquired_at']='garbage'
            with self.assertRaises(ValueError):feature_store.validate_feature_manifest(m,root)
            m['sources'][0]['acquired_at']='2026-11-26T00:00:00+09:00'
            self.assertEqual(len(feature_store.validate_feature_manifest(m,root)),1)

    def test_holdout_rejects_price_features_without_derivation_audit(self):
        data=engine.prepare(engine.synthetic_data())[0]
        data=data[data.exclusion_reason.eq('') & data.rent.gt(0)].copy()
        data['monthly_median_per_m2']=data.rent  # 고의 누수 제어 입력, 실측 아님
        with self.assertRaisesRegex(ValueError,'홀드아웃 가격 집계'):
            expansion.run_comparison(data,'monthly',{'lagged_prices':['monthly_median_per_m2']},holdout='합성시 지역0')


if __name__=='__main__':unittest.main()
