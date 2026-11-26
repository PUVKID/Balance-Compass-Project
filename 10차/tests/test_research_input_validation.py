import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from rentlab.research_metrics import write_research_results, AnalysisConfig


class PersistedResearchTests(unittest.TestCase):
    config = AnalysisConfig(bootstrap_replicates=99)

    def fixture(self, root, region=None):
        root.mkdir(exist_ok=True)
        test = pd.DataFrame(dict(source_row_id=['0001', '0002', '0003', '0004'],
                                 cluster_id=['a', 'b', 'c', 'd'], actual_won=[100.] * 4,
                                 prediction_won=[100.] * 4, prediction_ai_won=[100.] * 4,
                                 prediction_global_median_won=[110., 101., 101., 101.],
                                 region=['서울특별시 강남구'] * 3 + ['부산광역시 중구'], date=['2025-02-01'] * 4))
        if region:
            test = test[test.region.str.startswith(region + ' ')].copy()
        cal = pd.DataFrame(dict(source_row_id=[f'cal:{i}' for i in range(20)],
                                cluster_id=[f'cal:{i}' for i in range(20)], actual_won=[100.] * 20,
                                prediction_won=[99.] * 20, region=['부산광역시 중구'] * 20,
                                date=['2024-08-01'] * 20))
        test.to_csv(root / 'jeonse_predictions.csv', index=False)
        cal.to_csv(root / 'jeonse_calibration_predictions.csv', index=False)
        counts = dict(train=20, validation=10, calibration=len(cal), test=len(test))
        summary = dict(mode='SYNTHETIC', holdout_region=region,
                       provenance={'sources': [dict(sha256='a' * 64, snapshot_id='fixture', rows=100)]},
                       split_counts={'jeonse': counts}, targets={'jeonse': dict(
                           split_counts=counts, validation={'global_median': {'mae': 10}},
                           train_target_median_won=100, train_price_quantiles_won=[90, 95, 100, 105, 110, 120])})
        (root / 'summary.json').write_text(json.dumps(summary), encoding='utf-8')
        return test, cal, summary

    def run_writer(self, root, summary, held=None):
        return write_research_results(root, summary, config=self.config, holdout_result=held)

    def test_duplicate_and_blank_source_ids_rejected_before_output(self):
        for value in ['0001', '', '  ']:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); test, _, summary = self.fixture(root)
                test.loc[1, 'source_row_id'] = value
                test.to_csv(root / 'jeonse_predictions.csv', index=False)
                with self.assertRaisesRegex(ValueError, '식별|ID'):
                    self.run_writer(root, summary)
                self.assertFalse((root / 'hypothesis_results.json').exists())

    def test_count_mismatch_and_overlapping_calibration_ids_rejected(self):
        for overlap in [False, True]:
            with self.subTest(overlap=overlap), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); test, cal, summary = self.fixture(root)
                if overlap:
                    cal.loc[0, 'source_row_id'] = '0001'
                    cal.to_csv(root / 'jeonse_calibration_predictions.csv', index=False)
                else:
                    test.iloc[:3].to_csv(root / 'jeonse_predictions.csv', index=False)
                with self.assertRaises(ValueError):
                    self.run_writer(root, summary)

    def test_missing_declared_csv_and_missing_count_rejected(self):
        for missing_count in [False, True]:
            with self.subTest(missing_count=missing_count), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, _, summary = self.fixture(root)
                if missing_count:
                    del summary['targets']['jeonse']['split_counts']
                else:
                    (root / 'jeonse_calibration_predictions.csv').unlink()
                with self.assertRaises(ValueError):
                    self.run_writer(root, summary)

    def test_unknown_modes_rejected(self):
        for mode in ['synthetic', '', None, 'REALISH']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, _, summary = self.fixture(root)
                summary['mode'] = mode
                with self.assertRaisesRegex(ValueError, 'mode|모드'):
                    self.run_writer(root, summary)

    def test_real_requires_provenance_even_without_holdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, _, summary = self.fixture(root)
            summary['mode'] = 'REAL'; summary['provenance'] = {}
            with self.assertRaisesRegex(ValueError, '출처|스냅숏|provenance'):
                self.run_writer(root, summary)

    def test_h5_rejects_other_city_or_incomplete_seoul(self):
        for region in ['서울특별시', '부산광역시']:
            with self.subTest(region=region), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); ordinary = root / 'ordinary'; held = root / 'held'
                _, _, summary = self.fixture(ordinary)
                test, _, hs = self.fixture(held, region=region)
                if region == '서울특별시':
                    test = test.iloc[:2]
                    hs['targets']['jeonse']['split_counts']['test'] = 2
                    hs['split_counts']['jeonse']['test'] = 2
                    test.to_csv(held / 'jeonse_predictions.csv', index=False)
                    (held / 'summary.json').write_text(json.dumps(hs), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, '서울|집합|홀드아웃'):
                    self.run_writer(ordinary, summary, held)

    def test_valid_complete_h5_and_exact_consumed_file_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); ordinary = root / 'ordinary'; held = root / 'held'
            _, _, summary = self.fixture(ordinary)
            self.fixture(held, region='서울특별시')
            result = self.run_writer(ordinary, summary, held)
            h5 = next(r for r in result['hypotheses'] if r['id'] == 'H5' and r['target'] == 'jeonse')
            self.assertEqual(h5['n'], 3)
            self.assertTrue(all(r['decision'] != 'support' for r in result['hypotheses']))
            evidence = result['input_files']
            self.assertEqual(len(evidence), 5)
            for record in evidence:
                path = (ordinary if record['role'] == 'ordinary' else held) / record['path']
                self.assertEqual(record['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_empty_undeclared_inputs_remain_unmeasured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_writer(root, {'mode': 'SYNTHETIC', 'targets': {}})
            self.assertTrue(all(r['status'] == 'unmeasured' for r in result['hypotheses']))
            self.assertEqual(result['artifacts'][0]['status'], 'unmeasured')


if __name__ == '__main__':
    unittest.main()
