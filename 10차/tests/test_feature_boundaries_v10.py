"""실제 취득/학습 없이 식별키·원행 인덱스·생성 열 경계를 검사한다."""
import unittest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal
from rentlab.feature_store import join_features, validate_observations
from rentlab.spatial_features import station_features


class FeatureBoundaryTests(unittest.TestCase):
    def origins(self):
        return pd.DataFrame(dict(cluster_id=['seoul','busan'],latitude=[37.5,35.18],longitude=[127.,129.07]))
    def facilities(self):
        return pd.DataFrame(dict(facility_id=['s','b1','b2'],latitude=[37.5,35.18,35.18001],longitude=[127.,129.07,129.07001],line=['L1','L2','L3']))
    def contracts(self):
        return pd.DataFrame(dict(source_row_id=['a','b','c'],cluster_id=['01','1','missing'],date=['2025-01-02']*3))
    def observations(self):
        return pd.DataFrame([dict(entity_key=key,feature='households',value=value,valid_from='2020-01-01',valid_to='',published_at='2024-01-01T00:00:00+09:00',source_id='fixture',record_id=str(i)) for i,(key,value) in enumerate([('01',120),('1',240)])])
    def test_duplicate_origin_index_preserves_distinct_values_and_index(self):
        origins=self.origins();fac=self.facilities();expected=station_features(origins,fac)
        origins.index=pd.Index([7,7],name='original_row');before=origins.copy(deep=True)
        actual=station_features(origins,fac)
        self.assertEqual(actual.stations_1000m.tolist(),[1,2])
        self.assertEqual(actual.lines_1000m.tolist(),[1,2])
        self.assertTrue(actual.index.equals(origins.index))
        assert_frame_equal(actual.reset_index(drop=True),expected.reset_index(drop=True))
        assert_frame_equal(origins,before)
    def test_invalid_coordinates_with_duplicate_index_remain_missing(self):
        origins=self.origins();origins.index=[8,8];origins['latitude']=np.nan
        actual=station_features(origins,self.facilities())
        self.assertEqual(actual.coordinate_status.tolist(),['missing','missing'])
        self.assertFalse(actual.attrs['historical_availability_proven'])
        self.assertIn('not walking',actual.attrs['distance'])
        self.assertTrue(actual.station_distance_m.isna().all())
        self.assertTrue(actual.index.equals(origins.index))
    def test_observation_identifiers_must_be_strings(self):
        for field in ('entity_key','source_id','record_id'):
            with self.subTest(field=field):
                obs=self.observations();obs.loc[0,field]=1
                with self.assertRaisesRegex(ValueError,'문자열'):
                    validate_observations(obs)
    def test_contract_identifiers_must_not_be_coerced(self):
        for field in ('source_row_id','cluster_id'):
            with self.subTest(field=field):
                contracts=self.contracts();contracts.loc[0,field]=1
                with self.assertRaisesRegex(ValueError,'문자열'):
                    join_features(contracts,self.observations())
    def test_every_generated_column_collision_is_rejected_without_mutation(self):
        for field in ('households','households__record','households__missing'):
            with self.subTest(field=field):
                contracts=self.contracts();contracts[field]='preserve';before=contracts.copy(deep=True)
                with self.assertRaisesRegex(ValueError,'충돌'):
                    join_features(contracts,self.observations())
                assert_frame_equal(contracts,before)
    def test_spatial_identifiers_cannot_mix_numeric_and_string_labels(self):
        for field in ('cluster_id','facility_id','line'):
            with self.subTest(field=field):
                origins=self.origins();fac=self.facilities()
                (origins if field=='cluster_id' else fac).loc[0,field]=1
                with self.assertRaisesRegex(ValueError,'문자열'):
                    station_features(origins,fac)
    def test_distinct_string_keys_and_unknown_key_preserve_contracts(self):
        contracts=self.contracts();contracts.index=[4,4,6];contracts.loc[contracts.cluster_id.eq('missing'),'cluster_id']=None
        frame,audit=join_features(contracts,self.observations())
        self.assertEqual(frame.households.iloc[:2].tolist(),[120.,240.])
        self.assertTrue(pd.isna(frame.households.iloc[2]))
        self.assertEqual(frame.source_row_id.tolist(),contracts.source_row_id.tolist())
        self.assertTrue(frame.index.equals(contracts.index))
        self.assertEqual(audit['features']['households']['unmatched_rows'],1)

if __name__=='__main__':unittest.main()
