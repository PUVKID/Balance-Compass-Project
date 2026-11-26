"""실제 수집·학습 없는 실행 경계 회귀 검사."""
import json
from pathlib import Path
import tempfile
import unittest
from rentlab.runtime import RunLock, atomic_json, save_owned_state
from rentlab.experiment_runner import main

class RuntimeTests(unittest.TestCase):
    def test_atomic_json_and_stop_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json"
            atomic_json(p, {"run_id":"a", "status":"stopped_by_user"})
            self.assertFalse(save_owned_state(p, {"run_id":"a", "status":"completed"}))
            self.assertEqual(json.loads(p.read_text())["status"], "stopped_by_user")
            self.assertEqual(list(Path(d).glob("*.tmp")), [])
    def test_lock_excludes_and_releases(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"lock"
            with RunLock(p):
                with self.assertRaises(RuntimeError):
                    with RunLock(p): pass
            with RunLock(p): pass
    def test_plan_does_not_create_or_change_stop(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/"학습진행.json"
            atomic_json(p, {"status":"stopped_by_user"})
            before=p.read_bytes()
            self.assertEqual(main(["--root",d,"--run-dir",str(root/"new")]),0)
            self.assertEqual(before,p.read_bytes())
            self.assertFalse((root/"new").exists())
    def test_existing_run_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"학습진행.json"; atomic_json(p,{"status":"stopped_by_user"})
            before=p.read_bytes()
            self.assertEqual(main(["--root",d,"--run-dir",d,"--execute"]),2)
            self.assertEqual(before,p.read_bytes())
class AcquisitionTests(unittest.TestCase):
    def test_enrichment_output_can_feed_runner(self):
        import csv
        from rentlab.acquire import MONTHS, COLUMNS, request_form, sha256, enrich_local
        from rentlab.experiment_runner import execute
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"raw";root.mkdir();records={}
            for month in MONTHS:
                source=root/f"{month}.csv"
                with source.open("w",encoding="utf-8-sig",newline="") as stream:
                    writer=csv.writer(stream);writer.writerow(["NO",*COLUMNS,"번지","단지명"])
                    writer.writerow(["1","서울특별시 강남구","40",month,"1","1000","10","2","2000","신규","1-1","가단지"])
                records[month]={"raw_path":source.name,"raw_sha256":sha256(source),"raw_bytes":source.stat().st_size,
                    "raw_encoding":"utf-8-sig","request":request_form(month),"official_precheck_count":1,"rows":1,
                    "source_url":"https://example.invalid/public.csv","acquired_at":"2026-11-26T00:00:00+09:00"}
            atomic_json(root/"원본취득목록.json",{"snapshot_id":"controlled48","files":records})
            output=Path(d)/"enriched"
            self.assertEqual(enrich_local(root,output),0)
            self.assertEqual(execute(output,Path(d)/"run",run=lambda *a,**k:{"mode":"SYNTHETIC","rows":48}),0)
            progress=json.loads((output/"수집진행.json").read_text(encoding="utf-8"))
            self.assertEqual((progress["processed"],progress["normalized"],progress["rows"]),(48,48,48))
    def fixture(self, root):
        import csv
        from rentlab.acquire import COLUMNS, Collector, request_form, sha256
        collector=Collector(root)
        source=Path(root)/"원본"/"sample.partial"
        with source.open("w",encoding="utf-8-sig",newline="") as stream:
            writer=csv.writer(stream)
            writer.writerow(["NO",*COLUMNS,"번지","단지명"])
            writer.writerow(["1","서울시 강남구","40","202202","1","1000","10","2","2000","신규","1-1","가단지"])
        record={"raw_path":"원본/전국_아파트_전월세_202202.csv", "raw_sha256":sha256(source),
                "raw_bytes":source.stat().st_size,"raw_encoding":"utf-8-sig", "request":request_form("202202"),
                "official_precheck_count":1,"rows":1}
        return collector,source,record
    def test_raw_journal_recovers_both_crash_windows(self):
        from rentlab.runtime import atomic_json
        for published in (False,True):
            with self.subTest(published=published), tempfile.TemporaryDirectory() as d:
                c,src,r=self.fixture(d); target=Path(d)/r["raw_path"]
                atomic_json(c.journal_path,{"month":"202202","kind":"raw","temporary":src.relative_to(Path(d)).as_posix(),"target":r["raw_path"],"record":r})
                if published: src.rename(target)
                c.recover("202202")
                self.assertEqual(c.files["202202"]["rows"],1)
                self.assertTrue(target.exists()); self.assertFalse(c.journal_path.exists())
    def test_corrupt_journal_and_unknown_existing_rejected(self):
        from rentlab.runtime import atomic_json
        with tempfile.TemporaryDirectory() as d:
            c,src,r=self.fixture(d); target=Path(d)/r["raw_path"]
            target.write_bytes(b"unknown")
            with self.assertRaises(ValueError): c.resume_raw("202202")
            atomic_json(c.journal_path,{"month":"202202","kind":"raw","temporary":src.relative_to(Path(d)).as_posix(),"target":r["raw_path"],"record":r})
            with self.assertRaises(ValueError): c.recover("202202")
            self.assertEqual(target.read_bytes(),b"unknown")
    def test_lineage_and_normalized_recovery(self):
        import csv
        from rentlab.acquire import inspect_csv, sha256
        with tempfile.TemporaryDirectory() as d:
            c,src,r=self.fixture(d); target=Path(d)/r["raw_path"];src.rename(target)
            c.files["202202"]=r; c.normalize("202202")
            # 영수증 저장 직후 저널 잔존 상태를 다시 검증한다.
            c.recover("202202")
            output=Path(d)/r["normalized"]["path"]
            with output.open(encoding="utf-8-sig",newline="") as stream: row=next(csv.DictReader(stream))
            self.assertEqual(row["source_row_id"],sha256(target)+":1")
            self.assertEqual(len(row["cluster_id"]),64)
    def test_interrupt_and_external_stop_preserved(self):
        from rentlab.experiment_runner import execute
        for external in (False,True):
            with self.subTest(external=external), tempfile.TemporaryDirectory() as d:
                root=Path(d);atomic_json(root/"수집진행.json",{"stage":"completed","processed":48,"normalized":48})
                (root/"자료_manifest.json").write_text("{}")
                run_dir=root/"new"
                def controlled(*args,**kwargs):
                    if external:
                        atomic_json(run_dir/"학습진행.json",{"status":"stopped_by_user","stopped_at":"external","run_id":"external"})
                        return {"mode":"REAL","rows":1}
                    raise KeyboardInterrupt()
                self.assertEqual(execute(root,run_dir,run=controlled),130)
                state=json.loads((run_dir/"학습진행.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"],"stopped_by_user")
                if external:self.assertEqual(state["stopped_at"],"external")

class ProcessAndHTTPTests(unittest.TestCase):
    def test_lock_released_after_process_kill(self):
        import subprocess, sys
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"lock"
            code="from rentlab.runtime import RunLock; import os,sys; lock=RunLock(sys.argv[1]); lock.__enter__(); print('locked',flush=True); sys.stdin.readline(); os._exit(7)"
            child=subprocess.Popen([sys.executable,"-B","-X","utf8","-c",code,str(path)],stdout=subprocess.PIPE,stdin=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),"locked")
                with self.assertRaises(RuntimeError):
                    with RunLock(path):pass
            finally:
                child.stdin.write("exit\n");child.stdin.flush();child.stdin.close()
                self.assertEqual(child.wait(timeout=10),7);child.stdout.close()
            with RunLock(path):pass
    def test_fake_http_provenance_and_limit(self):
        from unittest.mock import patch
        from rentlab.acquire import Collector, CHECK, DOWNLOAD, KST
        from datetime import datetime
        fixture=AcquisitionTests()
        with tempfile.TemporaryDirectory() as d:
            c,source,record=fixture.fixture(d)
            body=source.read_bytes();source.unlink()
            class Response:
                status_code=206
                headers={"Content-Type":"text/csv"}
                url="https://example.invalid/final.csv"
                content=b'{"cnt":1}'
                def json(self):return {"cnt":1}
                def raise_for_status(self):pass
                def iter_content(self,*args):yield body
                def __enter__(self):return self
                def __exit__(self,*args):pass
            class Session:
                def __init__(self):self.calls=[]
                def post(self,url,**kwargs):self.calls.append(url);return Response()
            c.session=Session()
            with patch("rentlab.acquire.time.sleep"):
                c.collect("202202")
            self.assertEqual(c.session.calls,[CHECK,DOWNLOAD])
            self.assertEqual(c.files["202202"]["http"]["status_code"],206)
            self.assertEqual(c.files["202202"]["http"]["final_url"],Response.url)
            atomic_json(c.attempt_path,{datetime.now(KST).date().isoformat():100})
            with self.assertRaises(ValueError):c.collect("202203")
            self.assertEqual(c.session.calls,[CHECK,DOWNLOAD])

class RecoveryValidationTests(unittest.TestCase):
    def test_normalized_prepublication_crash_recovered(self):
        from unittest.mock import patch
        fixture=AcquisitionTests()
        with tempfile.TemporaryDirectory() as d:
            c,src,r=fixture.fixture(d);src.rename(Path(d)/r["raw_path"]);c.files["202202"]=r
            with patch("rentlab.acquire.os.link",side_effect=OSError("controlled crash before publish")):
                with self.assertRaises(OSError):c.normalize("202202")
            c.recover("202202")
            self.assertTrue((Path(d)/c.files["202202"]["normalized"]["path"]).exists())
    def test_recovery_rejects_request_and_official_count(self):
        from rentlab.runtime import atomic_json
        fixture=AcquisitionTests()
        for field,value in (("request",{}),("official_precheck_count",2)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as d:
                c,src,r=fixture.fixture(d);r[field]=value
                atomic_json(c.journal_path,{"month":"202202","kind":"raw","temporary":src.relative_to(Path(d)).as_posix(),"target":r["raw_path"],"record":r})
                with self.assertRaises(ValueError):c.recover("202202")
                self.assertFalse((Path(d)/r["raw_path"]).exists())

class HoldoutRunnerTests(unittest.TestCase):
    def test_holdout_plan_is_read_only(self):
        import contextlib,io
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            stdout=io.StringIO()
            with patch("rentlab.experiment_runner.execute") as execute,contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["--root",d,"--run-dir",str(Path(d)/"new"),"--with-holdout","서울특별시"]),0)
            plan=json.loads(stdout.getvalue())
            self.assertEqual(len(plan["runs"]),2)
            self.assertIn("가설통합결과",plan["analysis"])
            execute.assert_not_called()
            self.assertEqual(list(Path(d).iterdir()),[])

class HoldoutExecutionTests(unittest.TestCase):
    def controlled(self, root, changes=None, stop=False):
        import csv
        calls=[]
        def run(output,manifest,holdout_region=None):
            calls.append(holdout_region);output.mkdir()
            summary={"mode":"REAL","rows":2,"holdout_region":holdout_region,"targets":{target:{"versions":{"python":"controlled"},"estimator_details":{"ridge":{"parameters":{"alpha":1},"actual_n_iter":1}}} for target in ("jeonse","monthly")},
                     "provenance":{"manifest":str(manifest.resolve()),"sources":[{"sha256":"a"*64,"snapshot_id":"controlled","rows":2}]}}
            rows=[{"source_row_id":"a","actual_won":"10","region":"서울특별시 강남구","date":"2025-01-01","cluster_id":"c","prediction_won":"9"}]
            if not holdout_region:rows.append({**rows[0],"source_row_id":"b","region":"부산광역시 중구","cluster_id":"d"})
            if holdout_region and changes:changes(rows,summary)
            for target in ("jeonse","monthly"):
                calibration=[{**rows[0],"region":"부산광역시 중구","date":"2024-07-01","source_row_id":target+":cal:a"}] if rows else []
                counts={"train":2,"validation":1,"calibration":len(calibration),"test":len(rows)}
                summary["targets"][target]["split_counts"]=counts
                summary.setdefault("split_counts",{})[target]=counts
                for suffix in ("predictions.csv","calibration_predictions.csv"):
                    with (output/f"{target}_{suffix}").open("w",encoding="utf-8-sig",newline="") as stream:
                        writer=csv.DictWriter(stream,fieldnames=["source_row_id","actual_won","region","date","cluster_id","prediction_won"])
                        writer.writeheader();writer.writerows(calibration if suffix == "calibration_predictions.csv" else [{**row,"source_row_id":target+":"+row["source_row_id"]} for row in rows])
            atomic_json(output/"summary.json",summary)
            if stop and not holdout_region:
                atomic_json(output.parent/"학습진행.json",{"status":"stopped_by_user","stopped_at":"controlled"})
            return summary
        return run,calls
    def root(self,d):
        root=Path(d)
        atomic_json(root/"수집진행.json",{"stage":"completed","processed":48,"normalized":48})
        (root/"자료_manifest.json").write_text("{}")
        return root
    def test_two_mock_runs_and_analysis_copies(self):
        from rentlab.experiment_runner import execute
        with tempfile.TemporaryDirectory() as d:
            root=self.root(d);run,calls=self.controlled(root);new=root/"new"
            def writer(output,summary,holdout_result):
                self.assertFalse((output/"jeonse_predictions.csv").samefile(new/"결과"/"jeonse_predictions.csv"))
                self.assertFalse((holdout_result/"jeonse_predictions.csv").samefile(new/"홀드아웃결과"/"jeonse_predictions.csv"))
                self.assertEqual(summary["holdout_region"],None)
                return {"hypotheses":[]}
            self.assertEqual(execute(root,new,run=run,with_holdout="서울특별시",analysis_writer=writer),0)
            self.assertEqual(calls,[None,"서울특별시"])
            self.assertEqual(json.loads((new/"결과"/"summary.json").read_text(encoding="utf-8"))["holdout_region"],None)
            self.assertTrue((new/"가설통합결과"/"입력검증.json").exists())
    def test_real_analysis_writer_consumes_copied_holdout_summary(self):
        from rentlab.experiment_runner import execute
        with tempfile.TemporaryDirectory() as d:
            root=self.root(d);run,calls=self.controlled(root);new=root/"new"
            code=execute(root,new,run=run,with_holdout="서울특별시")
            self.assertEqual(code,0,(new/"실제학습_실행로그.txt").read_text(encoding="utf-8"))
            copied=new/"가설통합결과"/"홀드아웃"/"summary.json"
            self.assertEqual(copied.read_bytes(),(new/"홀드아웃결과"/"summary.json").read_bytes())
            result=json.loads((new/"가설통합결과"/"hypothesis_results.json").read_text(encoding="utf-8"))
            h5=[row for row in result["hypotheses"] if row["id"] == "H5"]
            self.assertEqual(len(h5),2)
            self.assertTrue(all(row["n"] == 1 and row["effect"] == 0 for row in h5))

    def test_mismatches_fail_before_analysis(self):
        from rentlab.experiment_runner import execute
        mutations=[lambda rows,s:rows[0].update(date="2025-02-01"),
                   lambda rows,s:rows[0].update(cluster_id="other"),
                   lambda rows,s:rows.append(rows[0].copy()),
                   lambda rows,s:rows.clear(),
                   lambda rows,s:s["provenance"].update(sources=[{"sha256":"changed"}]),
                   lambda rows,s:s["targets"]["monthly"]["versions"].update(python="different"),
                   lambda rows,s:s["targets"]["jeonse"]["estimator_details"]["ridge"]["parameters"].update(alpha=2)]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root=self.root(d);run,_=self.controlled(root,changes=mutation);new=root/"new"
                self.assertEqual(execute(root,new,run=run,with_holdout="서울특별시",analysis_writer=lambda *a,**k:self.fail("analysis called")),2)
                self.assertFalse((new/"가설통합결과").exists())
    def test_external_stop_prevents_second_run(self):
        from rentlab.experiment_runner import execute
        with tempfile.TemporaryDirectory() as d:
            root=self.root(d);run,calls=self.controlled(root,stop=True);new=root/"new"
            self.assertEqual(execute(root,new,run=run,with_holdout="서울특별시"),130)
            self.assertEqual(calls,[None]);self.assertFalse((new/"홀드아웃결과").exists())
            self.assertEqual(json.loads((new/"학습진행.json").read_text(encoding="utf-8"))["stopped_at"],"controlled")

if __name__ == "__main__": unittest.main()
