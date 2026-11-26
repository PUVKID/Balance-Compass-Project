"""기본은 계획만 출력하며 명시적 실행은 새 실행 폴더만 사용한다."""
from __future__ import annotations
import argparse
import contextlib
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import traceback
import uuid
from .runtime import RunLock, atomic_json, now, save_owned_state

ROOT = Path(__file__).resolve().parents[1]


def execute(root, run_dir, run=None, with_holdout=None, analysis_writer=None):
    root, run_dir = Path(root).resolve(), Path(run_dir).resolve()
    if with_holdout not in (None, "서울특별시"):
        raise ValueError("고정 홀드아웃은 서울특별시입니다")
    # 기존 폴더·상태·로그에는 쓰기 전에 거부한다.
    if run_dir.exists():
        raise ValueError(f"새 실행 폴더가 필요합니다: {run_dir}")
    with RunLock(root / ".experiment.lock"):
        run_dir.mkdir(parents=True, exist_ok=False)
        state_path = run_dir / "학습진행.json"
        state = {"run_id": uuid.uuid4().hex, "pid": os.getpid(), "started_at": now(),
                 "status": "running", "stage": "validating", "output": str(run_dir / "결과"), "cpu_threads": 2}
        with (run_dir / "실제학습_실행로그.txt").open("x", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                atomic_json(state_path, state)
                try:
                    progress = json.loads((root / "수집진행.json").read_text(encoding="utf-8"))
                    if progress.get("stage") != "completed" or progress.get("processed") != 48 or progress.get("normalized") != 48:
                        raise ValueError("48개월 원본 취득과 전처리가 완료되지 않았습니다")
                    manifest = root / "자료_manifest.json"
                    state["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
                    state["engine_sha256"] = hashlib.sha256((ROOT / "rentlab" / "engine.py").read_bytes()).hexdigest()
                    state["stage"] = "engine"
                    if not save_owned_state(state_path, state):
                        return 130
                    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
                        os.environ[key] = "2"
                    if run is None:
                        from .engine import run
                    result = run(run_dir / "결과", manifest=manifest)
                    if with_holdout:
                        state["stage"] = "holdout"
                        if not save_owned_state(state_path, state):
                            return 130
                        if hashlib.sha256(manifest.read_bytes()).hexdigest() != state["manifest_sha256"]:
                            raise ValueError("일반 실행 후 manifest 변경")
                        if hashlib.sha256((ROOT / "rentlab" / "engine.py").read_bytes()).hexdigest() != state["engine_sha256"]:
                            raise ValueError("일반 실행 후 엔진 코드 변경")
                        held = run(run_dir / "홀드아웃결과", manifest=manifest, holdout_region=with_holdout)
                        state["stage"] = "analysis"
                        if not save_owned_state(state_path, state):
                            return 130
                        if hashlib.sha256(manifest.read_bytes()).hexdigest() != state["manifest_sha256"]:
                            raise ValueError("홀드아웃 실행 후 manifest 변경")
                        if hashlib.sha256((ROOT / "rentlab" / "engine.py").read_bytes()).hexdigest() != state["engine_sha256"]:
                            raise ValueError("홀드아웃 실행 후 엔진 코드 변경")
                        combine_results(run_dir, result, held, manifest, with_holdout, writer=analysis_writer)
                        state["analysis"] = str(run_dir / "가설통합결과")
                    state.update(status="completed", stage="completed", mode=result["mode"], rows=result["rows"])
                except KeyboardInterrupt:
                    state.update(status="stopped_by_user", stage="stopped_by_user")
                except Exception as error:
                    state.update(status="failed", stage="failed", error_type=type(error).__name__, error=str(error))
                    traceback.print_exc()
                finally:
                    state["finished_at"] = now()
                    if not save_owned_state(state_path, state):
                        state["status"] = "stopped_by_user"
        return 0 if state["status"] == "completed" else (130 if state["status"] == "stopped_by_user" else 2)


def combine_results(run_dir, main_summary, held_summary, manifest, region, writer=None):
    """두 학습 결과의 입력·행 조건을 검증하고 별도 복사본에서만 분석한다."""
    for summary, expected in ((main_summary, None), (held_summary, region)):
        if summary.get("holdout_region") != expected:
            raise ValueError("결과의 홀드아웃 조건 불일치")
        if summary.get("provenance", {}).get("manifest") != str(manifest.resolve()):
            raise ValueError("결과의 manifest 경로 불일치")
    sources = main_summary.get("provenance", {}).get("sources")
    if not sources or sources != held_summary.get("provenance", {}).get("sources"):
        raise ValueError("일반/홀드아웃 원본 provenance 불일치")
    if main_summary.get("mode") != held_summary.get("mode"):
        raise ValueError("일반/홀드아웃 결과 모드 불일치")
    from .input_contracts import validate_holdout_settings
    validate_holdout_settings(main_summary,held_summary)
    run_dir = Path(run_dir)
    main_dir, held_dir = run_dir / "결과", run_dir / "홀드아웃결과"
    for target in ("jeonse", "monthly"):
        rows, columns = [], []
        for folder in (main_dir, held_dir):
            with (folder / f"{target}_predictions.csv").open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                required = {"source_row_id", "actual_won", "region", "date"}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError("홀드아웃 비교 필수 행 식별·정답·지역 칼럼 누락")
                columns.append(reader.fieldnames)
                frame = list(reader)
            index = {row["source_row_id"]: row for row in frame}
            if len(index) != len(frame) or "" in index:
                raise ValueError("홀드아웃 비교 행 식별자 중복 또는 누락")
            rows.append(index)
        if columns[0] != columns[1]:
            raise ValueError("일반/홀드아웃 테스트 칼럼 불일치")
        ordinary, held = rows
        expected_ids = {key for key, row in ordinary.items() if row["region"] == region or row["region"].startswith(region + " ")}
        if not expected_ids or set(held) != expected_ids:
            raise ValueError("일반/홀드아웃의 서울 테스트 행 집합 불일치")
        for key, row in held.items():
            if any(row[field] != ordinary[key][field] for field in ("actual_won", "region", "date")):
                raise ValueError("동일 테스트 행의 정답·지역·계약일 불일치")
            if "cluster_id" in row and "cluster_id" in ordinary[key] and row["cluster_id"] != ordinary[key]["cluster_id"]:
                raise ValueError("동일 테스트 행의 단지 식별자 불일치")
    output = run_dir / "가설통합결과"
    output.mkdir(exist_ok=False)
    copied_held = output / "홀드아웃"
    copied_held.mkdir()
    evidence = []
    for source_dir, destination in ((main_dir, output), (held_dir, copied_held)):
        for target in ("jeonse", "monthly"):
            for suffix in ("predictions.csv", "calibration_predictions.csv"):
                source = source_dir / f"{target}_{suffix}"
                target_path = destination / source.name
                shutil.copy2(source, target_path)
                evidence.append({"source":str(source), "copy":str(target_path), "sha256":hashlib.sha256(target_path.read_bytes()).hexdigest()})
    # 실제 분석 함수도 홀드아웃 조건·원본 지문을 확인하므로 summary를 함께 복사한다.
    held_summary_source = held_dir / "summary.json"
    copied_summary = copied_held / "summary.json"
    if json.loads(held_summary_source.read_text(encoding="utf-8")) != held_summary:
        raise ValueError("홀드아웃 반환값과 저장 summary 불일치")
    shutil.copy2(held_summary_source, copied_summary)
    evidence.append({"source":str(held_summary_source), "copy":str(copied_summary),
                     "sha256":hashlib.sha256(copied_summary.read_bytes()).hexdigest()})
    summary = copy.deepcopy(main_summary)
    atomic_json(output / "입력검증.json", {"manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
                                         "holdout_region":region, "files":evidence})
    if writer is None:
        from .research_metrics import write_research_results
        writer = write_research_results
    research = writer(output, summary, holdout_result=copied_held)
    summary["research"] = research
    summary["research_hypotheses"] = research["hypotheses"]
    summary["artifacts"] = research.get("artifacts", [])
    summary["analysis_only"] = True
    summary["holdout_comparison_region"] = region
    atomic_json(output / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--with-holdout", choices=["서울특별시"], help="고정 서울 홀드아웃과 별도 통합 분석 추가")
    args = parser.parse_args(argv)
    if not args.execute:
        runs = [{"output":str(args.run_dir.resolve() / "결과"), "holdout_region":None}]
        if args.with_holdout:
            runs.append({"output":str(args.run_dir.resolve() / "홀드아웃결과"), "holdout_region":args.with_holdout})
        print(json.dumps({"status":"planned", "root":str(args.root.resolve()), "run_dir":str(args.run_dir.resolve()), "execute":False,
                          "runs":runs, "analysis":str(args.run_dir.resolve() / "가설통합결과") if args.with_holdout else None}, ensure_ascii=False))
        return 0
    try:
        return execute(args.root, args.run_dir, with_holdout=args.with_holdout)
    except (ValueError, OSError, RuntimeError) as error:
        print(str(error))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
