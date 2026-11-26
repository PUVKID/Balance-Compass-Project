"""3차 엔진 입력과 학습기 고정 계약의 회귀 검사."""
import json
import tempfile
import types
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from rentlab import engine as e

class EngineV3Tests(unittest.TestCase):
    def prepared(self):
        return e.prepare(e.synthetic_data())[0]

    def test_optional_cancel_missing_is_unobserved(self):
        raw = e.synthetic_data().iloc[:3].copy()
        raw['해제사유발생일'] = [np.nan, '', '20250101']
        data, audit = e.prepare(raw)
        self.assertEqual(data.exclusion_reason.tolist(), ['', '', 'cancelled'])
        self.assertEqual(audit['cancellation_observability']['unobserved_rows'], 1)
        self.assertEqual(audit['cancellation_observability']['observed_rows'], 2)

    def test_strict_date_shapes_and_calendar(self):
        raw = e.synthetic_data().iloc[:6].copy()
        raw['계약년월'] = ['20221', '202201', '202202', '202201', '202402', '202201']
        raw['계약일'] = ['01', '001', '29', '1', '29', '1.0']
        data, _ = e.prepare(raw)
        self.assertEqual(data.exclusion_reason.tolist(), ['invalid_date']*3 + ['', '', 'invalid_date'])

    def test_floor_and_build_year(self):
        raw = e.synthetic_data().iloc[:5].copy()
        raw['층'] = ['', 'abc', '1.5', '-1', '3']
        raw['건축년도'] = ['2000', '2000', '2000', '2000.5', '2000']
        data, audit = e.prepare(raw)
        self.assertEqual(data.exclusion_reason.tolist(), ['', 'invalid_floor', 'invalid_floor', 'invalid_build_year', ''])
        self.assertEqual(audit['missing_floor_rows'], 1)

    def test_projected_duplicate_and_lineage(self):
        raw = pd.concat([e.synthetic_data().iloc[:1]]*2, ignore_index=True)
        raw['source_file'] = ['fixture.csv']*2
        data, audit = e.prepare(raw)
        self.assertEqual(audit['projected_duplicate_rows_retained'], 1)
        self.assertNotIn('identical_rows_retained', audit)
        self.assertEqual(data.source_row_id.nunique(), 2)
        self.assertTrue(data.cluster_id.isna().all())

    def test_manifest_schema_controlled(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'manifest.json'
            for value in [[], None, {'files':[{'path':[],'sha256':'0'*64,'rows':1,'source_url':'https://x','acquired_at':{},'snapshot_id':'x'}]}]:
                path.write_text(json.dumps(value), encoding='utf-8')
                with self.assertRaises(ValueError):
                    e.read_manifest(path)

    def test_exact_region_not_collapsed(self):
        frame = pd.DataFrame({'area': np.ones(100), 'region': [f'시도{i//10} 구{i}' for i in range(100)]})
        processor = e.preprocessor(['area'])
        transformed = processor.fit_transform(frame)
        if hasattr(transformed, 'toarray'):
            transformed = transformed.toarray()
        self.assertEqual(len(np.unique(transformed, axis=0)), 100)

    def test_candidates_lineage_and_frozen_edges(self):
        data = self.prepared()
        data = data.loc[data.rent.gt(0)].copy()
        first, test, frames = e.fit_target(data, 'monthly', None)
        names = {'global_median','region_median','ridge','hist_gradient_boosting'}
        self.assertEqual(set(first['candidate_test_metrics']), names)
        for column in ['source_row_id','cluster_id','prediction_ai_won','prediction_no_deposit_won'] + [f'prediction_{name}_won' for name in names]:
            self.assertIn(column, test)
            self.assertIn(column, frames['calibration'])
        changed = data.copy()
        changed.loc[changed.date.dt.year.eq(2025), 'rent'] *= 100
        second, _, _ = e.fit_target(changed, 'monthly', None)
        for key in ['train_price_edges_won','train_target_median_won','best_ai_model','no_deposit_best_ai_model']:
            self.assertEqual(first[key], second[key])
        self.assertEqual(first['train_price_edges_won'], np.unique(np.quantile(data.loc[data.date.dt.year.le(2023),'rent'], [0,.2,.4,.6,.8,1])).tolist())

    def test_hgb_preserves_all_upper_regions(self):
        frame = pd.DataFrame({'area': np.ones(100), 'region': [f'시도{i//10} 구{i} 동{i}' for i in range(100)]})
        hierarchy = e.HierarchicalRegions().fit_transform(frame)
        processor = e.preprocessor(['area'], hierarchical=True)
        result = processor.fit_transform(hierarchy)
        self.assertEqual(len(np.unique(result, axis=0)), 100)
        self.assertEqual(len(processor.named_transformers_['hierarchy'].categories_[1]), 100)
        self.assertEqual(processor.named_transformers_['category'].max_categories, 64)

    def test_group_artifacts_use_target_train_edges_and_counts(self):
        data = self.prepared()
        results, tests = {}, {}
        for target, mask in [('jeonse', data.rent.eq(0)), ('monthly', data.rent.gt(0))]:
            results[target], tests[target], _ = e.fit_target(data.loc[mask], target, None)
        summary = {'mode':'SYNTHETIC', 'targets':results, 'audit':{'excluded_by_reason':{}}, 'split_counts':{k:v['split_counts'] for k,v in results.items()}}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            artifacts = e.write_artifacts(output, summary, data, tests)
            table = pd.read_csv(output/'price_test_mae.csv')
            for target, frame in tests.items():
                section = table.loc[table.target.eq(target)]
                self.assertEqual(section.n.sum(), len(frame))
                self.assertAlmostEqual(np.average(section.value, weights=section.n), results[target]['metrics']['mae'])
                self.assertEqual(section.interval_n.sum(), len(frame))
                self.assertAlmostEqual(np.average(section.coverage, weights=section.interval_n), results[target]['metrics']['coverage'])
            for item in artifacts:
                if item['status'] == 'measured':
                    self.assertTrue(all(panel['displayed_rows'] <= 50 for panel in item['panels']))
                    self.assertEqual(item['row_limit_per_panel'], 50)

    def test_all_missing_floor_artifacts_remain_unmeasured(self):
        data = self.prepared()
        data['floor'] = np.nan
        results, tests = {}, {}
        for target, mask in [('jeonse', data.rent.eq(0)), ('monthly', data.rent.gt(0))]:
            results[target], tests[target], _ = e.fit_target(data.loc[mask], target, None)
        summary = {'mode':'SYNTHETIC', 'targets':results, 'audit':{'excluded_by_reason':{}}, 'split_counts':{k:v['split_counts'] for k,v in results.items()}}
        with tempfile.TemporaryDirectory() as folder:
            artifacts = e.write_artifacts(Path(folder), summary, data, tests)
            floor = next(item for item in artifacts if item['id'] == 'floor_test_mae')
            self.assertEqual(floor['status'], 'unmeasured')

    def test_run_writes_all_splits_before_research_and_times(self):
        raw = e.synthetic_data()
        raw = raw.loc[raw['계약년월'].isin(['202201','202401','202407','202501'])].copy()
        module = types.ModuleType('rentlab.research_metrics')
        calls = []
        def research(output, summary):
            for target in ('jeonse','monthly'):
                for suffix in ('predictions','validation_predictions','calibration_predictions'):
                    frame = pd.read_csv(output / f'{target}_{suffix}.csv')
                    self.assertTrue({'source_row_id','cluster_id','date','region','actual_won','prediction_won','lower_won','upper_won','prediction_ai_won'}.issubset(frame.columns))
                if target == 'monthly':
                    self.assertIn('prediction_no_deposit_won', frame)
            calls.append(summary['created_at'])
            return {'hypotheses':[], 'artifacts':[]}
        module.write_research_results = research
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'result'
            with patch.dict(sys.modules, {'rentlab.research_metrics':module}), patch.object(e, 'synthetic_data', return_value=raw), patch.object(e, 'write_artifacts', return_value=[]):
                result = e.run(output, synthetic=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result['status'], 'completed')
            self.assertLessEqual(result['created_at'], result['completed_at'])
            self.assertEqual(json.loads((output/'summary.json').read_text(encoding='utf-8'))['completed_at'], result['completed_at'])

    def test_each_plot_panel_reports_fifty_row_limit(self):
        data = self.prepared()
        results, tests = {}, {}
        for target, mask in [('jeonse', data.rent.eq(0)), ('monthly', data.rent.gt(0))]:
            results[target], tests[target], _ = e.fit_target(data.loc[mask], target, None)
            results[target]['groups'] = [{'region':f'지역{i}', 'n':1, 'mae':1, 'coverage':1} for i in range(60)]
        summary = {'mode':'SYNTHETIC','targets':results,'audit':{'excluded_by_reason':{}},'split_counts':{k:v['split_counts'] for k,v in results.items()}}
        with tempfile.TemporaryDirectory() as folder, patch.object(e, 'PURPOSES', [('regional_coverage','지역별 구간 포함률')]):
            item = e.write_artifacts(Path(folder), summary, data, tests)[0]
            self.assertEqual(item['displayed_rows'], 100)
            self.assertEqual(item['total_rows'], 120)
            self.assertEqual(len(item['panels']), 2)
            self.assertTrue(all(panel['truncated'] and panel['displayed_rows'] == 50 and panel['total_rows'] == 60 for panel in item['panels']))

if __name__ == '__main__':
    unittest.main()
