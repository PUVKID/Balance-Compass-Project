import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from rentlab import feature_store


def school(**changes):
    row = dict(학교ID='S1', 학교명='학교', 설립일자='2000-03-01', 운영상태='운영',
               위도='37', 경도='127', 데이터기준일자='2024-10-01')
    row.update(changes)
    return row


class FacilityQualityTests(unittest.TestCase):
    def qualify(self, rows, kind='SCHOOL', as_of='2024-12-31', reference_start='2024-01-01'):
        from rentlab.facility_quality import qualify_rows
        return qualify_rows(rows, kind, as_of=as_of, reference_start=reference_start)

    def test_park_duplicate_id_never_first_latest_or_average(self):
        rows = [dict(관리번호='P1', 공원명='A', 위도='37', 경도='127', 지정고시일='2000-01-01',
                     데이터기준일자='2024-10-01', 공원면적='10')]
        rows.append({**rows[0], '공원명': 'B', '위도': '37.1'})
        result = self.qualify(rows, 'PARK')
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['eligible_rows'], [])
        self.assertEqual(result['identifier_duplicate_groups'], 1)
        self.assertEqual(result['identifier_coordinate_conflicts'], 1)
        self.assertEqual(result['reason_counts']['ambiguous_identifier'], 2)
        self.assertFalse(result['all_rows_eligible'])

    def test_rail_stale_and_line_key_not_physical_identity(self):
        row = dict(역번호='1', 역사명='역', 운영기관명='기관', 노선번호='L1', 역위도='37', 역경도='127', 데이터기준일자='2021-04-09')
        result = self.qualify([row], 'RAIL', as_of='2026-11-27', reference_start='2026-01-01')
        self.assertIn('stale_reference', result['row_status'][0]['reasons'])
        self.assertIn('physical_identity_unproven', result['row_status'][0]['reasons'])
        self.assertIn('start_date_unknown', result['row_status'][0]['reasons'])

    def test_future_and_missing_start_dates_preserved(self):
        for text, expected in [('2026-03-01', 'future_start'), ('', 'start_date_unknown')]:
            with self.subTest(text=text):
                result = self.qualify([school(설립일자=text)])
                self.assertEqual(result['rows'], 1)
                self.assertIn(expected, result['row_status'][0]['reasons'])
                self.assertFalse(result['all_rows_eligible'])

    def test_future_reference_invalid_coordinates_and_inactive_school(self):
        for change, reason in [(dict(데이터기준일자='2025-01-01'), 'future_reference'),
                               (dict(경도='137.2'), 'invalid_coordinates'),
                               (dict(운영상태='폐교'), 'inactive_or_unknown_operation')]:
            with self.subTest(change=change):
                result = self.qualify([school(**change)])
                self.assertIn(reason, result['row_status'][0]['reasons'])

    def test_snapshot_eligibility_not_historical_or_complete_inventory_proof(self):
        result = self.qualify([school()])
        self.assertEqual(result['eligible_rows'], [1])
        self.assertTrue(result['all_rows_eligible'])
        self.assertFalse(result['historical_availability_proven'])
        self.assertFalse(result['source_completeness_proven'])

    def test_kapt_future_approval_and_unknown_reference_are_blocked(self):
        row = {'단지코드': 'K1', '단지명': '단지', '사용승인일': '20260301', '세대수': '100'}
        result = self.qualify([row], 'KAPT', as_of='2025-12-31', reference_start='2025-01-01')
        self.assertIn('future_start', result['row_status'][0]['reasons'])
        self.assertIn('reference_date_unknown', result['row_status'][0]['reasons'])

    def fixture(self, folder, feature='primary_distance_m'):
        source = folder / 'school.csv'
        with source.open('w', encoding='utf-8-sig', newline='') as stream:
            row = school(); writer = csv.DictWriter(stream, fieldnames=list(row))
            writer.writeheader(); writer.writerow(row)
        observations = pd.DataFrame([dict(entity_key='x', feature=feature, value=10,
                                         valid_from='2024-12-31', valid_to='',
                                         published_at='2024-12-31T12:00:00+09:00',
                                         source_id='school', record_id='r1')])
        observations.to_csv(folder / 'obs.csv', index=False)
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        descriptor = dict(path='obs.csv', sha256=digest(folder/'obs.csv'), rows=1,
                          features=[feature], key_column='cluster_id', status='verified_feature_snapshot',
                          sources=[dict(path=source.name, sha256=digest(source), rows=1, source_id='school',
                                        source_url='https://example.org/school', status='acquired_current_snapshot',
                                        acquired_at='2024-12-31T00:00:00+09:00')])
        return descriptor, observations

    def proof(self, folder, descriptor):
        from rentlab.facility_quality import source_report
        source = descriptor['sources'][0]
        report = source_report(folder / source['path'], source_id=source['source_id'], kind='SCHOOL',
                               as_of='2024-12-31', reference_start='2024-01-01')
        path = folder / 'quality.json'; path.write_text(json.dumps(report), encoding='utf-8')
        descriptor['quality_reports'] = [dict(source_id=source['source_id'], path=path.name,
                                              sha256=hashlib.sha256(path.read_bytes()).hexdigest())]
        return report

    def test_facility_features_require_source_bound_recomputed_quality_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); descriptor, _ = self.fixture(root)
            with self.assertRaisesRegex(ValueError, '시설|자격|quality'):
                feature_store.validate_feature_manifest(descriptor, root)
            self.proof(root, descriptor)
            self.assertEqual(len(feature_store.validate_feature_manifest(descriptor, root)), 1)
            report = json.loads((root/'quality.json').read_text())
            report['all_rows_eligible'] = False
            (root/'quality.json').write_text(json.dumps(report))
            descriptor['quality_reports'][0]['sha256'] = hashlib.sha256((root/'quality.json').read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, '자격|재계산|quality'):
                feature_store.validate_feature_manifest(descriptor, root)

    def test_unknown_quality_cannot_backdate_current_facility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); descriptor, obs = self.fixture(root)
            self.proof(root, descriptor)
            obs['valid_from'] = '2022-01-01'; obs.to_csv(root/'obs.csv', index=False)
            descriptor['sha256'] = hashlib.sha256((root/'obs.csv').read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, '과거|유효|시점'):
                feature_store.validate_feature_manifest(descriptor, root)

    def test_quality_report_cannot_be_reused_for_wrong_feature_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); descriptor, _ = self.fixture(root, feature='park_distance_m')
            self.proof(root, descriptor)
            with self.assertRaisesRegex(ValueError, '종류|kind|시설'):
                feature_store.validate_feature_manifest(descriptor, root)


if __name__ == '__main__':
    unittest.main()
