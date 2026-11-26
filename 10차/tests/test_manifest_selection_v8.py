"""실제 학습 없이 실행기가 선택한 입력 경로와 해시를 끝까지 추적한다."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rentlab import experiment_runner as runner


class ManifestSelectionTests(unittest.TestCase):
    def setup_files(self, folder):
        root=folder/'collection';root.mkdir()
        (root/'수집진행.json').write_text(json.dumps(dict(stage='completed',processed=48,normalized=48)),encoding='utf8')
        (root/'학습진행.json').write_text('{"status":"stopped_by_user"}',encoding='utf8')
        (root/'자료_manifest.json').write_text('{"legacy":true}',encoding='utf8')
        expanded=folder/'expanded';expanded.mkdir();selected=expanded/'자료_manifest.json'
        selected.write_text('{"selected":true}',encoding='utf8')
        return root,selected

    def test_plan_names_selected_manifest_without_writes(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);root,selected=self.setup_files(folder);before=(root/'학습진행.json').read_bytes()
            text=io.StringIO()
            with contextlib.redirect_stdout(text):
                result=runner.main(['--root',str(root),'--run-dir',str(folder/'new'),'--manifest',str(selected),'--with-holdout','서울특별시'])
            self.assertEqual(result,0);plan=json.loads(text.getvalue())
            self.assertEqual(plan['manifest'],str(selected.resolve()))
            self.assertFalse(plan['execute']);self.assertEqual(len(plan['runs']),2)
            self.assertFalse((folder/'new').exists());self.assertEqual((root/'학습진행.json').read_bytes(),before)

    def test_both_runs_and_analysis_use_selected_input(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);root,selected=self.setup_files(folder);before=(root/'학습진행.json').read_bytes();calls=[]
            def fake_run(output,**kwargs):
                calls.append(kwargs);return dict(mode='SYNTHETIC',rows=48)
            with patch.object(runner,'combine_results') as combine:
                result=runner.execute(root,folder/'new',run=fake_run,with_holdout='서울특별시',manifest_path=selected)
            self.assertEqual(result,0);self.assertEqual([c['manifest'] for c in calls],[selected.resolve()]*2)
            self.assertEqual(combine.call_args.args[3],selected.resolve())
            state=json.loads((folder/'new/학습진행.json').read_text(encoding='utf8'))
            self.assertEqual(state['manifest'],str(selected.resolve()))
            self.assertEqual(state['manifest_sha256'],hashlib.sha256(selected.read_bytes()).hexdigest())
            self.assertEqual((root/'학습진행.json').read_bytes(),before)

    def test_missing_explicit_manifest_never_falls_back_or_runs(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);root,selected=self.setup_files(folder);calls=[]
            result=runner.execute(root,folder/'new',run=lambda *a,**k:calls.append(k),manifest_path=selected.with_name('missing.json'))
            self.assertEqual(result,2);self.assertEqual(calls,[])
            state=json.loads((folder/'new/학습진행.json').read_text(encoding='utf8'))
            self.assertEqual(state['status'],'failed')

    def test_changed_selected_manifest_stops_before_holdout(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);root,selected=self.setup_files(folder);calls=[]
            def fake_run(output,**kwargs):
                calls.append(kwargs);selected.write_text('{"changed":true}',encoding='utf8');return dict(mode='SYNTHETIC',rows=48)
            result=runner.execute(root,folder/'new',run=fake_run,with_holdout='서울특별시',manifest_path=selected)
            self.assertEqual(result,2);self.assertEqual(len(calls),1)
            state=json.loads((folder/'new/학습진행.json').read_text(encoding='utf8'))
            self.assertIn('manifest 변경',state['error'])

    def test_changed_selected_manifest_cannot_complete_single_run(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);root,selected=self.setup_files(folder)
            def fake_run(output,**kwargs):
                selected.write_text('{"changed":true}',encoding='utf8');return dict(mode='SYNTHETIC',rows=48)
            result=runner.execute(root,folder/'new',run=fake_run,manifest_path=selected)
            self.assertEqual(result,2)
            state=json.loads((folder/'new/학습진행.json').read_text(encoding='utf8'))
            self.assertEqual(state['status'],'failed');self.assertIn('manifest 변경',state['error'])
