"""공식 전국 월별 CSV를 순차 취득하고 원본을 보존한 채 학습 칼럼을 추출한다."""
from __future__ import annotations

import argparse
import calendar
from collections import Counter
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

import requests

from .runtime import RunLock, atomic_json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://rt.molit.go.kr/pt/xls/xls.do"
CHECK = "https://rt.molit.go.kr/pt/xls/ptXlsDownDataCheck.do"
DOWNLOAD = "https://rt.molit.go.kr/pt/xls/ptXlsCSVDown.do"
SNAPSHOT = "collection20261126"
COLUMNS = ["시군구", "전용면적(㎡)", "계약년월", "계약일", "보증금(만원)", "월세금(만원)", "층", "건축년도", "계약구분"]
MONTHS = [f"{year}{month:02}" for year in range(2022, 2026) for month in range(1, 13)]
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log(message, root):
    line = f"{datetime.now(KST).isoformat()} {message}"
    print(line, flush=True)
    with (root / "수집로그.txt").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(line + "\n")


def preserve_response(response, month, kind, root):
    # 실패 본문은 쿠키·요청 인증 헤더 없이 최대 1MiB만 보존한다.
    target = root / "원본" / f"실패응답_{month}_{kind}_{uuid.uuid4().hex}.bin"
    captured = 0
    with target.open("xb") as output:
        for chunk in response.iter_content(65536):
            remaining = 1024 * 1024 - captured
            if remaining <= 0:
                break
            output.write(chunk[:remaining])
            captured += min(len(chunk), remaining)
    log(f"실패 본문 보존: {target.name}, HTTP {response.status_code}, 최대 1MiB 제한, 기록 {captured}바이트", root)
    return target


def require_http_success(response, month, kind, root):
    try:
        response.raise_for_status()
    except requests.HTTPError:
        preserve_response(response, month, kind, root)
        raise


def http_metadata(response, endpoint):
    return {"endpoint": endpoint, "final_url": response.url, "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", "")}


def request_form(month):
    if month not in MONTHS:
        raise ValueError("고정된 2022–2025의 48개월만 지원합니다")
    year, number = int(month[:4]), int(month[4:])
    form = {key: "" for key in ["sidoNm", "sggNm", "emdNm", "loadNm", "areaNm", "hsmpNm", "mobileAt", "srhNewRonSecd", "srhSidoCd", "srhSggCd", "srhEmdCd", "srhRoadNm", "srhLoadCd", "srhHsmpCd", "srhArea", "srhFromAmount", "srhToAmount", "srhLrArea"]}
    form.update(srhThingNo="A", srhDelngSecd="2", srhAddrGbn="1", srhLfstsSecd="1",
                srhFromDt=f"{year}-{number:02}-01", srhToDt=f"{year}-{number:02}-{calendar.monthrange(year, number)[1]}")
    return form


def detect_encoding(path):
    # 전체 파일을 메모리에 올리지 않고 엄격한 디코딩 가능 여부를 확인한다.
    for encoding in ["utf-8-sig", "cp949"]:
        try:
            with path.open("r", encoding=encoding, errors="strict", newline="") as stream:
                for _ in iter(lambda: stream.read(1024 * 1024), ""):
                    pass
            return encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"지원하지 않는 원본 인코딩: {path.name}")


def inspect_csv(path, month, expected, encoding, destination=None):
    source_digest = sha256(path)
    rows, regions, categories = 0, Counter(), Counter()
    output = None
    try:
        with path.open("r", encoding=encoding, errors="strict", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = None
            for index, row in enumerate(reader):
                if row and row[0] == "NO":
                    header = row
                    break
                if index >= 99:
                    raise ValueError(f"100개 안내행 안에 공식 NO 머리글 없음: {month}")
            if header is None or len(set(header)) != len(header) or not set(COLUMNS).issubset(header):
                raise ValueError(f"공식 CSV 필수 칼럼 누락 또는 중복: {month}")
            columns = COLUMNS + (["해제사유발생일"] if "해제사유발생일" in header else [])
            indexes = [header.index(name) for name in columns]
            if destination is not None:
                output = destination.open("x", encoding="utf-8-sig", newline="")
                writer = csv.writer(output)
                writer.writerow(columns + ["source_row_id", "cluster_id"])
            month_index, region_index, contract_index = [header.index(name) for name in ["계약년월", "시군구", "계약구분"]]
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    raise ValueError(f"CSV 칼럼 수 오류: {month}, 본문 {rows + 1}행")
                if row[month_index] != month:
                    raise ValueError(f"요청월과 다른 계약월: {month}, 본문 {rows + 1}행")
                rows += 1
                words = row[region_index].split()
                regions[words[0] if words else "<미상>"] += 1
                categories[row[contract_index]] += 1
                if output is not None:
                    # 칼럼 선택만 수행한다. 날짜·금액·계약구분 문자열과 정확히 같은 행을 보존한다.
                    parcel = ["번지"] if "번지" in header else ["본번", "부번"]
                    keys = ["시군구", *parcel, "단지명"]
                    values = [row[header.index(key)].strip() for key in keys] if all(key in header for key in keys) else []
                    cluster = hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest() if values and all(values) else ""
                    writer.writerow([row[index] for index in indexes] + [f"{source_digest}:{rows}", cluster])
        if rows != expected:
            raise ValueError(f"공식 사전 건수 불일치: {month}, 공식={expected}, CSV={rows}")
        return {"rows": rows, "columns": header, "province_counts": dict(regions), "contract_categories": dict(categories)}
    finally:
        if output is not None:
            output.close()


class Collector:
    def __init__(self, root, snapshot_id=SNAPSHOT):
        self.root = Path(root).resolve()
        self.snapshot_id = snapshot_id
        self.run_id = uuid.uuid4().hex
        self.journal_path = self.root / "취득저널.json"
        self.attempt_path = self.root / "다운로드시도.json"
        (self.root / "원본").mkdir(exist_ok=True)
        (self.root / "전처리").mkdir(exist_ok=True)
        self.receipt_path = self.root / "원본취득목록.json"
        self.receipt = json.loads(self.receipt_path.read_text(encoding="utf-8")) if self.receipt_path.exists() else {"snapshot_id": self.snapshot_id, "files": {}}
        if self.receipt.get("snapshot_id") != self.snapshot_id:
            raise ValueError("기존 수집 스냅숏이 현재 실행과 다릅니다")
        self.files = self.receipt["files"]
        self.progress_path = self.root / "수집진행.json"
        previous = json.loads(self.progress_path.read_text(encoding="utf-8")) if self.progress_path.exists() else {}
        self.errors = previous.get("errors", [])
        self.session = None
        self.current_month = None
        self.current_stage = "starting"
        self.issued_downloads = 0

    def progress(self, stage, current=None):
        self.current_stage = stage
        self.current_month = current
        value = {"run_id": self.run_id, "pid": os.getpid(), "status": stage, "snapshot_id": self.snapshot_id, "stage": stage, "processed": len(self.files), "total": len(MONTHS),
                 "normalized": sum("normalized" in entry for entry in self.files.values()),
                 "rows": sum(entry["rows"] for entry in self.files.values()), "current_month": current,
                 "updated_at": now(), "errors": self.errors,
                 "months": {month: {"rows": entry["rows"], "official_precheck_count": entry["official_precheck_count"],
                                      "province_counts": entry.get("province_counts", {}), "encoding": entry["raw_encoding"]} for month, entry in self.files.items()}}
        if self.progress_path.exists():
            previous = json.loads(self.progress_path.read_text(encoding="utf-8"))
            if previous.get("stage") == "stopped_by_user" or previous.get("status") == "stopped_by_user":
                raise KeyboardInterrupt("외부 중단 기록을 보존합니다")
        atomic_json(self.progress_path, value)

    def save_receipt(self):
        self.receipt["updated_at"] = now()
        atomic_json(self.receipt_path, self.receipt)

    def checked_path(self, relative):
        path = (self.root / relative).resolve(strict=True)
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError("취득 기록 경로가 실험 폴더 밖을 가리킵니다")
        return path

    def prepare_publish(self, month, kind, temporary, target, record):
        if target.exists():
            raise ValueError(f"기존 파일을 보존합니다: {target}")
        atomic_json(self.journal_path, {"month":month, "kind":kind, "temporary":temporary.relative_to(self.root).as_posix(),
                                       "target":target.relative_to(self.root).as_posix(), "record":record})
        # 링크 생성은 POSIX에서도 기존 목적지를 덮어쓰지 않는다. 같은 볼륨에서만 게시한다.
        os.link(temporary, target)
        temporary.unlink()

    def recover(self, month):
        if not self.journal_path.exists():
            return
        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        pending_month = journal["month"]
        if pending_month not in MONTHS:
            raise ValueError("저널 요청월 범위 오류")
        record = journal["record"]
        if record["request"] != request_form(pending_month):
            raise ValueError("저널 요청 조건 불일치")
        kind = journal["kind"]
        if kind not in ("raw", "normalized"):
            raise ValueError("저널 종류 오류")
        metadata = record if kind == "raw" else record["normalized"]
        relative = record["raw_path"] if kind == "raw" else metadata["path"]
        expected_target = f"원본/전국_아파트_전월세_{pending_month}.csv" if kind == "raw" else f"전처리/학습_전월세_{pending_month}.csv"
        if relative != expected_target or journal["target"] != expected_target:
            raise ValueError("저널 목적 경로 불일치")
        target = self.root / relative
        candidate = self.checked_path(relative if target.exists() else journal["temporary"])
        digest = metadata["raw_sha256"] if kind == "raw" else metadata["sha256"]
        size = metadata["raw_bytes"] if kind == "raw" else metadata["bytes"]
        if sha256(candidate) != digest or candidate.stat().st_size != size:
            raise ValueError("저널 파일 해시·크기 불일치")
        if kind == "raw":
            info = inspect_csv(candidate, pending_month, int(record["official_precheck_count"]), record["raw_encoding"])
            if info["rows"] != record["rows"]:
                raise ValueError("저널 원본 행 수 불일치")
        else:
            source = self.checked_path(record["raw_path"])
            if sha256(source) != record["raw_sha256"] or source.stat().st_size != record["raw_bytes"]:
                raise ValueError("저널 전처리 원본 불일치")
            inspect_csv(source, pending_month, int(record["official_precheck_count"]), record["raw_encoding"])
            with candidate.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                if not set(COLUMNS + ["source_row_id", "cluster_id"]).issubset(reader.fieldnames or []):
                    raise ValueError("저널 전처리 칼럼 불일치")
                count = sum(1 for row in reader if row["계약년월"] == pending_month)
            if count != metadata["rows"] or count != record["rows"]:
                raise ValueError("저널 전처리 행 수 불일치")
        if not target.exists():
            os.link(candidate, target)
            candidate.unlink()
        self.files[pending_month] = record
        self.save_receipt()
        self.journal_path.unlink()

    def resume_raw(self, month):
        self.recover(month)
        record = self.files.get(month)
        target = self.root / "원본" / f"전국_아파트_전월세_{month}.csv"
        if record is None and target.exists():
            raise ValueError(f"SHA 취득 기록 없는 기존 원본은 재사용·덮어쓰기하지 않습니다: {month}")
        if record is None:
            return False
        path = self.checked_path(record["raw_path"])
        if path != target.resolve() or sha256(path) != record["raw_sha256"] or path.stat().st_size != record["raw_bytes"]:
            raise ValueError(f"재사용 원본 경로·해시·크기 불일치: {month}")
        if record["request"] != request_form(month):
            raise ValueError(f"재사용 원본 요청 조건 불일치: {month}")
        inspection = inspect_csv(path, month, int(record["official_precheck_count"]), record["raw_encoding"])
        record.update(inspection)
        self.files[month] = record
        self.save_receipt()
        self.progress("collecting", month)
        log(f"재사용 검증 {month}: {record['rows']}행, SHA 일치", self.root)
        return True

    def connect(self):
        if self.session is not None:
            return
        self.session = requests.Session()
        response = self.session.get(SOURCE, timeout=(30, 60))
        require_http_success(response, self.current_month, "페이지", self.root)
        if "전국 자료제공 계약일자 범위는 최대 1개월" not in response.text or "/pt/xls/ptXlsCSVDown.do" not in response.text:
            raise ValueError("공식 페이지의 전국 월별 제공 조건을 확인할 수 없습니다")
        log("공식 전국 최대 1개월 제공 조건 확인; 단일 HTTP 세션으로 순차 취득", self.root)

    def collect(self, month):
        self.connect()
        today = datetime.now(KST).date()
        known_daily = sum(datetime.fromisoformat(entry["acquired_at"]).astimezone(KST).date() == today for entry in self.files.values())
        attempts = json.loads(self.attempt_path.read_text(encoding="utf-8")) if self.attempt_path.exists() else {}
        day = today.isoformat()
        if max(known_daily, attempts.get(day, 0)) >= 100 or self.issued_downloads >= 100:
            raise ValueError("일일 또는 이번 실행의 다운로드 100회 상한에 도달했습니다")
        form = request_form(month)
        headers = {"Referer": SOURCE}
        time.sleep(1)
        check = self.session.post(CHECK, data=form, headers=headers, timeout=(30, 90))
        require_http_success(check, month, "사전검사", self.root)
        try:
            result = check.json()
        except ValueError:
            preserve_response(check, month, "사전검사본문", self.root)
            raise
        if result.get("error") or isinstance(result.get("cnt"), bool):
            raise ValueError(f"공식 사전 검사 거부: {json.dumps(result, ensure_ascii=False)}")
        expected = int(result.get("cnt", 0))
        if expected <= 0:
            raise ValueError(f"공식 사전 건수 없음: {month}")
        time.sleep(1)
        self.issued_downloads += 1
        # 네트워크 요청 전에 시도를 영속화해 중단 후에도 상한을 유지한다.
        attempts[day] = max(known_daily, attempts.get(day, 0)) + 1
        atomic_json(self.attempt_path, attempts)
        target = self.root / "원본" / f"전국_아파트_전월세_{month}.csv"
        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".partial")
        self.progress("downloading", month)
        try:
            with self.session.post(DOWNLOAD, data=form, headers=headers, timeout=(30, 180), stream=True) as response:
                require_http_success(response, month, "다운로드", self.root)
                if "html" in response.headers.get("Content-Type", "").lower():
                    preserve_response(response, month, "HTML", self.root)
                    raise ValueError(f"CSV 대신 HTML 응답: {month}")
                response_metadata = http_metadata(response, DOWNLOAD)
                size = 0
                with temporary.open("xb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if not chunk:
                            continue
                        if size == 0 and (b"<html" in chunk[:4096].lower() or b"<!doctype html" in chunk[:4096].lower()):
                            output.write(chunk)
                            raise ValueError(f"CSV 본문 대신 HTML 오류 응답: {month}")
                        size += len(chunk)
                        if size > 200 * 1024 * 1024:
                            raise ValueError(f"단일 월 원본 200MiB 안전 상한 초과: {month}")
                        output.write(chunk)
                    output.flush()
                    os.fsync(output.fileno())
            if size < 200:
                raise ValueError(f"비정상적으로 짧은 CSV: {month}")
            encoding = detect_encoding(temporary)
            inspection = inspect_csv(temporary, month, expected, encoding)
            record = {"raw_path": target.relative_to(self.root).as_posix(), "raw_sha256": sha256(temporary), "raw_bytes": size,
                      "raw_encoding": encoding, "acquired_at": now(), "request": form, "source_url": SOURCE,
                      "official_precheck_count": expected, "http": response_metadata,
                      "precheck": {"response": result, "body_sha256": hashlib.sha256(check.content).hexdigest(),
                                   "http": http_metadata(check, CHECK)}, **inspection}
            # 저널을 먼저 기록한 뒤 기존 목적지를 덮어쓰지 않는 링크로 게시한다.
            if target.exists():
                raise ValueError(f"동시에 생성된 원본을 보존합니다: {month}")
            self.prepare_publish(month, "raw", temporary, target, record)
            self.files[month] = record
            self.save_receipt()
            self.progress("collecting", month)
            log(f"공식 취득 {month}: {inspection['rows']}행, 사전 건수 차이 0, {size}바이트, {encoding}", self.root)
        except BaseException:
            # 실패 응답·부분 수신은 .partial에 그대로 보존하고 자동 재시도하지 않는다.
            raise

    def normalize(self, month):
        self.recover(month)
        record = self.files[month]
        source = self.checked_path(record["raw_path"])
        if sha256(source) != record["raw_sha256"]:
            raise ValueError(f"전처리 직전 원본 SHA 불일치: {month}")
        target = self.root / "전처리" / f"학습_전월세_{month}.csv"
        if target.exists():
            previous = record.get("normalized")
            if previous is None or previous["path"] != target.relative_to(self.root).as_posix() or previous["sha256"] != sha256(target):
                raise ValueError(f"검증된 기록 없는 기존 전처리 파일 보존: {month}")
            log(f"전처리 재사용 {month}: SHA 일치", self.root)
            return
        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".partial")
        inspection = inspect_csv(source, month, record["rows"], record["raw_encoding"], temporary)
        digest = sha256(temporary)
        if target.exists():
            raise ValueError(f"동시에 생성된 전처리 파일을 보존합니다: {month}")
        normalized = {"path": target.relative_to(self.root).as_posix(), "sha256": digest,
                      "bytes": temporary.stat().st_size, "rows": inspection["rows"], "created_at": now(),
                      "lineage": "raw_sha256:row_ordinal", "cluster_key": "sha256(region,parcel,complex_name); missing fields yield empty"}
        self.prepare_publish(month, "normalized", temporary, target, {**record, "normalized": normalized})
        record["normalized"] = normalized
        self.save_receipt()
        self.progress("normalizing", month)
        log(f"칼럼 추출 {month}: {inspection['rows']}행, 원문 값·중복 행 보존", self.root)

    def manifest(self):
        entries = []
        for month in MONTHS:
            record = self.files[month]
            normalized = record["normalized"]
            entries.append({"path": normalized["path"], "sha256": normalized["sha256"], "rows": normalized["rows"],
                            "source_url": record["source_url"], "acquired_at": record["acquired_at"], "snapshot_id": self.snapshot_id,
                            "raw_path": record["raw_path"], "raw_sha256": record["raw_sha256"], "raw_encoding": record["raw_encoding"],
                            "request": record["request"], "official_precheck_count": record["official_precheck_count"],
                            "contract_month": month, "province_counts": record["province_counts"]})
        atomic_json(self.root / "자료_manifest.json", {"snapshot_id": self.snapshot_id, "created_at": now(), "files": entries,
                                                  "transform": "필수 칼럼 추출 및 UTF-8-sig 기록만 수행; 원문 값과 중복 행 유지"})

    def execute(self, local_only=False):
        with RunLock(self.root / ".collector.lock"):
            # 잠금을 얻은 후 최신 영수증을 읽어 오래된 스냅숏 발행을 막는다.
            if self.receipt_path.exists():
                self.receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
                if self.receipt.get("snapshot_id") != self.snapshot_id:
                    raise ValueError("기존 수집 스냅숏이 현재 실행과 다릅니다")
                self.files = self.receipt["files"]
            return self._execute(local_only)

    def _execute(self, local_only=False):
        try:
            self.progress("collecting")
            for month in MONTHS:
                self.current_month = month
                if not self.resume_raw(month):
                    if local_only:
                        raise ValueError(f"로컬 원본이 없습니다: {month}")
                    self.collect(month)
            log("48개월 원본 확보·공식 건수 대조 완료; 이후 전처리 시작", self.root)
            self.progress("normalizing")
            for month in MONTHS:
                self.current_month = month
                self.normalize(month)
            self.manifest()
            self.progress("completed")
            log(f"완료: 48개월, 총 {sum(entry['rows'] for entry in self.files.values())}행; 공식 건수 차이 모두 0", self.root)
            return 0
        except KeyboardInterrupt:
            if not self.progress_path.exists() or json.loads(self.progress_path.read_text(encoding="utf-8")).get("stage") != "stopped_by_user":
                try:
                    self.progress("stopped_by_user", self.current_month)
                except KeyboardInterrupt:
                    pass
            return 130
        except Exception as error:
            failure = {"at": now(), "month": self.current_month, "stage": self.current_stage,
                       "error_type": type(error).__name__, "error": str(error), "argv": sys.argv,
                       "cwd": str(Path.cwd()), "automatic_retry": False}
            self.errors.append(failure)
            try:
                self.progress("failed", self.current_month)
            except KeyboardInterrupt:
                return 130
            log(f"중단: {failure['month']} {failure['error_type']}: {failure['error']}; 자동 재시도 없음", self.root)
            return 2
        finally:
            if self.session is not None:
                self.session.close()


def enrich_local(root, output):
    """기존 원본/영수증은 읽기만 하고 새 폴더에 행 연결 칼럼을 추가한다."""
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("행 연결 보강에는 새 출력 폴더가 필요합니다")
    receipt = json.loads((root / "원본취득목록.json").read_text(encoding="utf-8"))
    if set(receipt["files"]) != set(MONTHS):
        raise ValueError("검증 가능한 48개월 원본 영수증이 필요합니다")
    output.mkdir(parents=True, exist_ok=False)
    entries = []
    for month in MONTHS:
        record = receipt["files"][month]
        source = (root / record["raw_path"]).resolve(strict=True)
        if not source.is_relative_to(root) or sha256(source) != record["raw_sha256"] or source.stat().st_size != record["raw_bytes"]:
            raise ValueError(f"원본 경로·해시·크기 불일치: {month}")
        if record["request"] != request_form(month):
            raise ValueError(f"원본 요청 조건 불일치: {month}")
        target = output / f"학습_전월세_{month}.csv"
        inspection = inspect_csv(source, month, int(record["official_precheck_count"]), record["raw_encoding"], target)
        if inspection["rows"] != record["rows"]:
            raise ValueError(f"원본 영수증 행 수 불일치: {month}")
        entries.append({"path":target.name, "sha256":sha256(target), "rows":inspection["rows"],
                        "source_url":record["source_url"], "acquired_at":record["acquired_at"],
                        "snapshot_id":receipt["snapshot_id"], "contract_month":month,
                        "raw_sha256":record["raw_sha256"], "raw_path":str(source), "request":record["request"]})
    atomic_json(output / "자료_manifest.json", {"snapshot_id":receipt["snapshot_id"], "created_at":now(), "files":entries,
                                               "transform":"원문 값 보존; source_row_id 및 가능한 cluster_id만 추가"})
    # 새 입력 루트가 다음 실행기의 완료 계약을 만족하도록 로컬 검증 완료를 기록한다.
    # 원본 취득 시각을 새 다운로드 시각으로 바꾸지 않는다.
    atomic_json(output / "수집진행.json", {"stage":"completed", "processed":len(entries), "total":len(MONTHS),
        "normalized":len(entries), "rows":sum(entry["rows"] for entry in entries), "updated_at":now(),
        "source":"verified_local_enrichment", "network_downloaded":False, "snapshot_id":receipt["snapshot_id"]})
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot-id", default=SNAPSHOT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--local-only", action="store_true", help="네트워크 없이 기존 검증 원본만 별도 루트에서 변환")
    parser.add_argument("--enrich-output", type=Path, help="기존 48개월 원본에서 새 폴더에 행 연결 보강; --local-only 필수")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status":"planned", "months": MONTHS, "execute":False, "root":str(args.root.resolve()), "local_only":args.local_only}, ensure_ascii=False))
        return 0
    if args.enrich_output:
        if not args.local_only:
            parser.error("--enrich-output은 --local-only가 필요합니다")
        return enrich_local(args.root, args.enrich_output)
    return Collector(args.root, args.snapshot_id).execute(local_only=args.local_only)


if __name__ == "__main__":
    raise SystemExit(main())
