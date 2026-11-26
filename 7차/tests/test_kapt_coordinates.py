import unittest
import json
import hashlib
import tempfile
from pathlib import Path
from rentlab.kapt_coordinates import validate_coordinates,prepare_snapshot,SOURCE_PROJ


class CoordinateTests(unittest.TestCase):
    def test_projection_axes_and_duplicate_point(self):
        row=dict(kaptCode='A1',xCoord=200000,yCoord=500000)
        result=validate_coordinates([row,row])[0]
        self.assertEqual(result['coordinate_status'],'valid_current_map_point')
        self.assertAlmostEqual(result['longitude'],127.0007,places=3)
        self.assertAlmostEqual(result['latitude'],38.0027,places=3)
        self.assertEqual(result['source_rows'],2)

    def test_conflicts_and_missing_not_averaged_or_zero_filled(self):
        result=validate_coordinates([dict(kaptCode='A1',xCoord=200000,yCoord=500000),
                                     dict(kaptCode='A1',xCoord=200010,yCoord=500010),
                                     dict(kaptCode='A2',xCoord=None,yCoord=500000),
                                     dict(kaptCode='A3',xCoord=0,yCoord=0),
                                     dict(kaptCode='A4',xCoord=float('nan'),yCoord=500000)])
        self.assertEqual(result[0]['coordinate_status'],'conflicting_coordinates')
        self.assertTrue(all(r['latitude'] is None for r in result))

    def test_empty_or_missing_code_rejected(self):
        for rows in [[],[dict(kaptCode='',xCoord=200000,yCoord=500000)]]:
            with self.assertRaises(ValueError):validate_coordinates(rows)

    def test_snapshot_rejects_tampered_method_and_records_actual_month(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'raw';raw.mkdir()
            page=b'<map id="map_11" title="Seoul"></map>';method=SOURCE_PROJ.encode()
            payload=json.dumps({'resultList':[dict(kaptCode='A1',xCoord=200000,yCoord=500000)]}).encode()
            (raw/'source_page.html').write_bytes(page);(raw/'coordinate_method.js').write_bytes(method);(raw/'poi_11.json').write_bytes(payload)
            manifest=dict(rows=1,source_page_sha256=hashlib.sha256(page).hexdigest(),coordinate_method_sha256=hashlib.sha256(method).hexdigest(),receipts=[dict(path='poi_11.json',sha256=hashlib.sha256(payload).hexdigest(),rows=1,province_code='11',request=dict(bjdCode='11',searchDate='202501'))])
            (raw/'manifest.json').write_text(json.dumps(manifest))
            result=prepare_snapshot(raw,root/'good')
            self.assertEqual(result['search_month'],'202501')
            self.assertIn('202501',' '.join(result['limitations']))
            (raw/'coordinate_method.js').write_bytes(method+b' altered')
            with self.assertRaises(ValueError):prepare_snapshot(raw,root/'bad')

    def test_snapshot_rejects_receipt_geography_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'raw';raw.mkdir()
            page=b'<map id="map_11" title="Seoul"></map>';method=SOURCE_PROJ.encode()
            payload=json.dumps({'resultList':[dict(kaptCode='A1',xCoord=200000,yCoord=500000)]}).encode()
            (raw/'source_page.html').write_bytes(page);(raw/'coordinate_method.js').write_bytes(method);(raw/'poi_11.json').write_bytes(payload)
            manifest=dict(rows=1,source_page_sha256=hashlib.sha256(page).hexdigest(),coordinate_method_sha256=hashlib.sha256(method).hexdigest(),receipts=[dict(path='poi_11.json',sha256=hashlib.sha256(payload).hexdigest(),rows=1,province_code='11',request=dict(bjdCode='26',searchDate='202501'))])
            (raw/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):prepare_snapshot(raw,root/'bad')


if __name__=='__main__':unittest.main()
