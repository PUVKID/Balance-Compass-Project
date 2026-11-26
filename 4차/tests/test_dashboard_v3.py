import copy
import json
import tempfile
import unittest
import http.client
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from run_dashboard import Handler
from pathlib import Path
from run_dashboard import load_summary, load_status


def fixture():
    metrics = dict(n=2, mae=1., rmse=1., coverage=.9, width=2., interval_score=2.)
    splits = dict(train=2, validation=2, calibration=2, test=2)
    target = dict(selected_model='ridge', validation={'ridge':dict(mae=1., rmse=1.)}, metrics=metrics, groups=[dict(region='서울',n=2,mae=1.,coverage=.9)], split_counts=splits)
    return dict(mode='SYNTHETIC',status='completed',rows=16,targets={k:copy.deepcopy(target) for k in ['jeonse','monthly']},split_counts={k:splits for k in ['jeonse','monthly']},artifacts=[],audit={},limitations=[])


class DashboardTests(unittest.TestCase):
    def read(self, data):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'summary.json').write_text(json.dumps(data), encoding='utf-8')
            return load_summary(root)

    def test_valid_modes(self):
        for mode in ['REAL','SYNTHETIC']:
            data=fixture(); data['mode']=mode
            self.assertEqual(self.read(data)['mode'],mode)

    def test_nested_artifacts_rejected(self):
        for item in ['x',None,{'id':'x','title':'x','csv':22}]:
            data=fixture(); data['artifacts']=[item]
            with self.assertRaises(ValueError): self.read(data)

    def test_missing_required_rejected(self):
        for key in ['rows','status','targets','split_counts','artifacts']:
            data=fixture(); del data[key]
            with self.assertRaises(ValueError): self.read(data)
        data=fixture(); data['targets']={}
        with self.assertRaises(ValueError): self.read(data)

    def test_numbers_strict(self):
        for value in [True,'2',float('inf'),float('nan'),-1]:
            data=fixture(); data['rows']=value
            with self.assertRaises(ValueError): self.read(data)
        data=fixture(); data['targets']['jeonse']['metrics']['coverage']=2
        with self.assertRaises(ValueError): self.read(data)

    def test_nested_metrics_rejected(self):
        for value in [None,[],{'n':2}]:
            data=fixture(); data['targets']['jeonse']['metrics']=value
            with self.assertRaises(ValueError): self.read(data)

    def test_provenance_removed(self):
        data=fixture();data['provenance']={'path':'E:/secret'}
        self.assertNotIn('provenance',self.read(data))

    def test_progress_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'p.json'; path.write_text(json.dumps(dict(status='stopped_by_user',output='E:/secret',started_at='2026-11-26',stop_reason='E:/secret')),encoding='utf-8')
            collection=Path(folder)/'c.json';collection.write_text(json.dumps(dict(stage='completed',processed=48,total=48,rows=4845086,months={'secret':'path'})),encoding='utf-8')
            data=load_status(None,path,collection)
            self.assertEqual(data['mode'],'UNCONNECTED')
            self.assertEqual(data['execution']['status'],'stopped_by_user')
            self.assertEqual(data['collection']['rows'],4845086)
            self.assertNotIn('secret',json.dumps(data))

    def test_execution_stage_and_finished_time_exposed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'p.json'
            value=dict(status='completed',stage='analysis',finished_at='2026-11-26T21:00:00+09:00',output='E:/secret')
            path.write_text(json.dumps(value),encoding='utf-8')
            data=load_status(None,path)['execution']
            self.assertEqual(data['stage'],'analysis')
            self.assertEqual(data['finished_at'],value['finished_at'])
            self.assertNotIn('output',data)

class HTTPTests(unittest.TestCase):
    def request(self, result, path, headers=None):
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,result=result))
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            conn.request('GET',path,headers=headers or {})
            response=conn.getresponse();body=response.read();conn.close()
            return response.status,body
        finally:
            server.shutdown();server.server_close();worker.join()

    def test_formulas_stylesheet_is_served(self):
        status,body=self.request(None,'/formulas.css')
        self.assertEqual(status,200)
        self.assertTrue(body)

    def test_unconnected_status(self):
        status,body=self.request(None,'/api/status')
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['api_version'],1)

    def test_nested_bad_file_is_controlled(self):
        with tempfile.TemporaryDirectory() as folder:
            data=fixture();data['artifacts']=['x']
            (Path(folder)/'summary.json').write_text(json.dumps(data),encoding='utf-8')
            status,body=self.request(Path(folder),'/artifact/x.csv')
            self.assertEqual(status,404);self.assertIn('error',json.loads(body))

    def test_error_hides_absolute_path(self):
        with tempfile.TemporaryDirectory() as folder:
            status,body=self.request(Path(folder),'/api/status')
            self.assertEqual(status,404);self.assertNotIn(folder.encode(),body)

    def test_raw_progress_and_source_not_served(self):
        for path in ['/학습진행.json','/run_dashboard.py','/../run_dashboard.py','/artifact/audit_rows.csv']:
            self.assertEqual(self.request(None,path if path.isascii() else '/%ED%95%99%EC%8A%B5%EC%A7%84%ED%96%89.json')[0],404)

    def test_cross_site_and_host_rejected(self):
        self.assertEqual(self.request(None,'/api/status',{'Host':'attacker.invalid'})[0],403)
        self.assertEqual(self.request(None,'/api/status',{'Sec-Fetch-Site':'cross-site'})[0],403)

if __name__=='__main__': unittest.main()
