"""통합 writer 중 입력 변경은 완료 상태로 승격하지 않는다. 실제 학습은 호출하지 않는다."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rentlab import experiment_runner as runner


class AnalysisCompletionGuardTests(unittest.TestCase):
    def check_mutation(self, changed_file):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / 'collection'
            root.mkdir()
            (root / '수집진행.json').write_text(json.dumps(dict(stage='completed', processed=48, normalized=48)), encoding='utf-8')
            stopped = root / '학습진행.json'
            stopped.write_text('{"status":"stopped_by_user"}', encoding='utf-8')
            original_stop = stopped.read_bytes()
            manifest = root / '자료_manifest.json'
            manifest.write_text('{"selected":true}', encoding='utf-8')
            code_root = base / 'code'
            (code_root / 'rentlab').mkdir(parents=True)
            engine = code_root / 'rentlab/engine.py'
            engine.write_text('# frozen controlled fixture\n', encoding='utf-8')
            expected_hash = hashlib.sha256((manifest if changed_file == 'manifest' else engine).read_bytes()).hexdigest()
            calls = []

            def fake_run(output, **kwargs):
                calls.append(kwargs)
                return dict(mode='SYNTHETIC', rows=48)

            def fake_combine(*args, **kwargs):
                target = manifest if changed_file == 'manifest' else engine
                target.write_text('changed during analysis', encoding='utf-8')
                return {}

            with patch.object(runner, 'ROOT', code_root), patch.object(runner, 'combine_results', side_effect=fake_combine) as combine:
                result = runner.execute(root, base / 'new-run', run=fake_run, with_holdout='서울특별시', manifest_path=manifest)
            state = json.loads((base / 'new-run/학습진행.json').read_text(encoding='utf-8'))
            self.assertEqual(len(calls), 2)
            combine.assert_called_once()
            self.assertEqual(result, 2)
            self.assertEqual(state['status'], 'failed')
            self.assertIn('통합 분석 후', state['error'])
            self.assertIn('manifest' if changed_file == 'manifest' else '엔진 코드', state['error'])
            self.assertEqual(state[changed_file + '_sha256'], expected_hash)
            self.assertEqual(stopped.read_bytes(), original_stop)

    def test_manifest_changed_during_analysis_cannot_complete(self):
        self.check_mutation('manifest')

    def test_engine_changed_during_analysis_cannot_complete(self):
        self.check_mutation('engine')
