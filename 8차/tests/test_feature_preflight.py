import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class FeaturePreflightTests(unittest.TestCase):
    def fixture(self,root):
        (root/'source.csv').write_text('id,value\n1,3\n',encoding='utf8')
        (root/'obs.csv').write_text('entity_key,feature,value,valid_from,valid_to,published_at,source_id,record_id\n001,base_rate,3,2024-01-01,,2024-01-01T00:00:00+09:00,s,001\n',encoding='utf8')
        d=dict(status='verified_feature_snapshot',features=['base_rate'],key_column='region',path='obs.csv',rows=1,
               sha256=hashlib.sha256((root/'obs.csv').read_bytes()).hexdigest(),sources=[dict(source_id='s',path='source.csv',
               rows=1,sha256=hashlib.sha256((root/'source.csv').read_bytes()).hexdigest(),source_url='https://example.org',
               status='acquired_current_snapshot',acquired_at='2026-11-27T00:00:00+09:00')])
        path=root/'features.json';path.write_text(json.dumps(d),encoding='utf8');return path

    def test_valid_input_reports_scope_and_provenance_without_model_import(self):
        from rentlab.feature_preflight import inspect_snapshot
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.fixture(root)
            report=inspect_snapshot(path)
            self.assertEqual(report['status'],'validated_input_only')
            self.assertEqual(report['observations'],1)
            self.assertEqual(report['feature_profile']['base_rate']['rows'],1)
            self.assertEqual(report['manifest_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertFalse(report['training_started'])
            self.assertFalse(report['historical_availability_proven'])
            result=subprocess.run([sys.executable,'-B','-X','utf8','-c',
                "from rentlab.feature_preflight import inspect_snapshot; import sys; inspect_snapshot(sys.argv[1]); assert 'rentlab.engine' not in sys.modules; assert 'sklearn' not in sys.modules",str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_absent_and_malformed_inputs_fail_closed(self):
        from rentlab.feature_preflight import inspect_snapshot
        self.assertEqual(inspect_snapshot()['status'],'missing_input')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'features.json';path.write_text('[]')
            report=inspect_snapshot(path)
            self.assertEqual(report['status'],'invalid_input')
            self.assertFalse(report['training_started'])

    def test_cli_writes_new_report_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.fixture(root);out=root/'report.json'
            args=[sys.executable,'-B','-X','utf8','-m','rentlab.feature_preflight','--features',str(path),'--output',str(out)]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            before=out.read_bytes();result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertEqual(out.read_bytes(),before)

    def test_corrupt_source_and_unknown_encoding_produce_invalid_report(self):
        for kind in ['quote','encoding','nul']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=self.fixture(root);descriptor=json.loads(path.read_text())
                if kind=='quote':(root/'source.csv').write_text('id,value\n1,"broken\n',encoding='utf8')
                elif kind=='nul':(root/'source.csv').write_bytes(b'id,value\n1,3\x00junk\n')
                else:descriptor['sources'][0]['encoding']='unknown-codec'
                descriptor['sources'][0]['sha256']=hashlib.sha256((root/'source.csv').read_bytes()).hexdigest()
                path.write_text(json.dumps(descriptor));out=root/'report.json'
                result=subprocess.run([sys.executable,'-B','-X','utf8','-m','rentlab.feature_preflight','--features',str(path),'--output',str(out)],capture_output=True,text=True)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertEqual(json.loads(out.read_text())['status'],'invalid_input')


if __name__=='__main__':unittest.main()
