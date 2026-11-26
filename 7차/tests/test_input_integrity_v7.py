import copy
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from rentlab import feature_store
from rentlab.research_metrics import AnalysisConfig, write_research_results
import test_expansion as expansion_fixtures
import test_research_input_validation as research_fixtures


class InputIntegrityTests(unittest.TestCase):
    def test_physical_feature_domains(self):
        f=expansion_fixtures.ExpansionTests()
        for feature,value in [('population',-1),('stations_500m',.5),('park_distance_m',-1),
                              ('coverage_ratio',101),('households',0),('max_floor',2.5)]:
            with self.subTest(feature=feature):
                obs=f.observations().iloc[[0]].assign(feature=feature,value=value)
                with self.assertRaises(ValueError):feature_store.join_features(f.contracts(),obs)

    def test_signed_changes_and_floor_ratios_remain_valid(self):
        f=expansion_fixtures.ExpansionTests()
        for feature,value in [('population_yoy',-.5),('base_rate',-.1),('floor_area_ratio',350),('relative_floor',-.1)]:
            obs=f.observations().iloc[[0]].assign(feature=feature,value=value)
            frame,_=feature_store.join_features(f.contracts(),obs)
            self.assertEqual(frame[feature].iloc[0],value)

    def test_manifest_must_validate_full_observation_schema(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'source.csv').write_text('id,value\n1,10\n',encoding='utf8')
            (root/'obs.csv').write_text('feature,source_id\nbase_rate,s\n',encoding='utf8')
            descriptor=dict(status='verified_feature_snapshot',features=['base_rate'],key_column='region',path='obs.csv',
                            rows=1,sha256=hashlib.sha256((root/'obs.csv').read_bytes()).hexdigest(),sources=[dict(
                                source_id='s',path='source.csv',rows=1,sha256=hashlib.sha256((root/'source.csv').read_bytes()).hexdigest(),
                                status='acquired_current_snapshot',source_url='https://example.org',acquired_at='2026-11-27T00:00:00+09:00')])
            with self.assertRaises(ValueError):feature_store.validate_feature_manifest(descriptor,root)

    def test_duplicate_csv_headers_and_extra_cells_rejected(self):
        fixture=research_fixtures.PersistedResearchTests()
        for change in ['duplicate','extra','short','blank']:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);_,_,summary=fixture.fixture(root)
                path=root/'jeonse_predictions.csv';lines=path.read_text().splitlines()
                if change=='duplicate':
                    lines[0]+=',actual_won';lines[1:]=[line+',900' for line in lines[1:]]
                elif change=='extra':lines[1]+=',extra'
                elif change=='short':lines[1]=lines[1].rsplit(',',1)[0]
                else:lines.insert(2,'')
                path.write_text('\n'.join(lines)+'\n')
                with self.assertRaises(ValueError):write_research_results(root,summary,config=fixture.config)

    def test_holdout_fixed_model_conditions_cannot_differ(self):
        fixture=research_fixtures.PersistedResearchTests()
        for field in ['versions','estimator_details']:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);ordinary=root/'main';held=root/'held'
                _,_,summary=fixture.fixture(ordinary);_,_,other=fixture.fixture(held,'서울특별시')
                summary['targets']['jeonse'][field]={'python':'3.12'} if field=='versions' else {'ridge':{'parameters':{'alpha':1}}}
                other['targets']['jeonse'][field]={'python':'3.11'} if field=='versions' else {'ridge':{'parameters':{'alpha':9}}}
                (held/'summary.json').write_text(json.dumps(other),encoding='utf8')
                with self.assertRaises(ValueError):write_research_results(ordinary,summary,config=fixture.config,holdout_result=held)

    def test_missing_cluster_column_cannot_silently_downgrade_h5_identity(self):
        f=research_fixtures.PersistedResearchTests()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);test,_,summary=f.fixture(root)
            test.drop(columns='cluster_id').to_csv(root/'jeonse_predictions.csv',index=False)
            with self.assertRaises(ValueError):write_research_results(root,summary,config=f.config)

    def test_nul_must_not_truncate_ids_or_numbers(self):
        fixture=research_fixtures.PersistedResearchTests()
        for before,after in [('0001','0001\x00TAIL'),('100.0','100.0\x00junk')]:
            with self.subTest(before=before),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);_,_,summary=fixture.fixture(root)
                path=root/'jeonse_predictions.csv'
                path.write_bytes(path.read_bytes().replace(before.encode(),after.encode(),1))
                with self.assertRaises(ValueError):write_research_results(root,summary,config=fixture.config)

    def test_config_integer_fields_are_real_integers(self):
        for key,value in [('bootstrap_replicates',100.5),('minimum_clusters',float('nan')),
                          ('minimum_group_n',True),('minimum_group_clusters',2.5),('seed',-1),('seed',True)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):AnalysisConfig(**{key:value})


if __name__=='__main__':unittest.main()
