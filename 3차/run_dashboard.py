"""로컬 연구 결과를 읽기 전용으로 제공한다."""
import argparse
import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
import mimetypes
import math

ROOT = Path(__file__).resolve().parent


def contained_file(root, relative):
    """상대 경로만 허용하고 폴더 밖 파일과 연결 파일을 거부한다."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or ":" in relative or "\\" in relative:
        raise ValueError("허용하지 않는 파일 경로입니다")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise ValueError("파일 연결은 제공하지 않습니다")
    candidate = current.resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise ValueError("파일을 찾을 수 없습니다")
    return candidate


def require(condition):
    if not condition:
        raise ValueError("결과 자료의 형식 또는 필수 항목이 올바르지 않습니다")


def numeric(value, nullable=False, integer=False, ratio=False):
    if value is None and nullable:
        return
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0)
    require(not integer or type(value) is int)
    require(not ratio or value <= 1)


def validate_summary(data):
    require(isinstance(data, dict) and data.get("mode") in {"REAL", "SYNTHETIC"})
    require(data.get("status") == "completed")
    numeric(data.get("rows"), integer=True)
    require(isinstance(data.get("targets"), dict) and set(data["targets"]) == {"jeonse", "monthly"})
    require(isinstance(data.get("split_counts"), dict))
    for name, target in data["targets"].items():
        require(isinstance(target, dict) and isinstance(target.get("selected_model"), str))
        validation = target.get("validation")
        require(isinstance(validation, dict) and target["selected_model"] in validation)
        for scores in validation.values():
            require(isinstance(scores, dict))
            for key in ("mae", "rmse"):
                numeric(scores.get(key))
        scores = target.get("metrics")
        require(isinstance(scores, dict))
        for key in ("n", "mae", "rmse", "coverage", "width", "interval_score"):
            require(key in scores)
            numeric(scores[key], nullable=key in {"coverage", "width", "interval_score"}, integer=key == "n", ratio=key == "coverage")
        for splits in (data["split_counts"].get(name), target.get("split_counts")):
            require(isinstance(splits, dict) and set(splits) == {"train", "validation", "calibration", "test"})
            for value in splits.values():
                numeric(value, integer=True)
        require(data["split_counts"][name] == target["split_counts"])
        require(scores["n"] == target["split_counts"]["test"])
        require(isinstance(target.get("groups"), list))
        for group in target["groups"]:
            require(isinstance(group, dict) and isinstance(group.get("region"), str))
            for key in ("n", "mae", "coverage"):
                numeric(group.get(key), nullable=key == "coverage", integer=key == "n", ratio=key == "coverage")
    require(isinstance(data.get("artifacts"), list))
    for item in data["artifacts"]:
        require(isinstance(item, dict))
        require(all(isinstance(item.get(key), str) for key in ("id", "title")))
        require(item.get("status") in {"measured", "unmeasured"})
        for key in ("csv", "png"):
            value = item.get(key)
            require(value is None or isinstance(value, str))
            if value is not None:
                rel = Path(value)
                require(bool(value) and not rel.is_absolute() and ".." not in rel.parts and ":" not in value and "\\" not in value and rel.suffix.lower() == "." + key)
        require(item["status"] != "measured" or bool(item.get("csv")))
    for item in data["artifacts"]:
        for key in ("displayed_rows", "total_rows"):
            if key in item:
                numeric(item[key], integer=True)
        if "displayed_rows" in item and "total_rows" in item:
            require(item["displayed_rows"] <= item["total_rows"])
        for field in ("panels", "panel_metadata"):
            if field in item:
                require(isinstance(item[field], list))
                for panel in item[field]:
                    require(isinstance(panel, dict))
                    for key in ("displayed_rows", "total_rows"):
                        numeric(panel.get(key), integer=True)
                    require(panel["displayed_rows"] <= panel["total_rows"])
    if "research_hypotheses" in data:
        require(isinstance(data["research_hypotheses"], list))
        for item in data["research_hypotheses"]:
            require(isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("title"), str))
            require(item.get("status") in {"measured", "unmeasured", "partial"})
            require(item.get("target") in {"jeonse", "monthly"})
            if item.get("effect") is not None:
                require(type(item["effect"]) in (int, float) and math.isfinite(item["effect"]))
            if item.get("ci") is not None:
                require(isinstance(item["ci"], list) and len(item["ci"]) == 2)
                require(all(type(x) in (int, float) and math.isfinite(x) for x in item["ci"]))
    require(isinstance(data.get("audit", {}), dict))
    require(isinstance(data.get("limitations", []), list) and all(isinstance(x, str) for x in data.get("limitations", [])))
    # 비유한 수치는 추가 분석 필드에서도 허용하지 않는다.
    json.dumps(data, allow_nan=False)


def load_summary(result):
    if result is None:
        return {"mode": "UNCONNECTED", "status": "결과 미연결", "rows": None,
                "targets": {}, "artifacts": [], "limitations": ["완료된 평가 결과가 연결되지 않았습니다. 수집·실행 상태는 별도로 확인합니다."]}
    path = contained_file(result, "summary.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_summary(data)
    data.pop("provenance", None)
    return data


def read_progress(path, collection=False):
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        require(isinstance(data, dict))
        keys = ("stage", "processed", "total", "normalized", "rows", "current_month", "updated_at") if collection else ("status", "stage", "started_at", "completed_at", "finished_at", "stopped_at", "updated_at")
        result = {key: data[key] for key in keys if key in data}
        for key in ("processed", "total", "normalized", "rows"):
            if key in result:
                numeric(result[key], integer=True)
        for key in set(result) - {"processed", "total", "normalized", "rows"}:
            require(result[key] is None or isinstance(result[key], str))
        return result
    except (ValueError, OSError, TypeError):
        return {"status": "unavailable", "message": "진행 기록을 읽을 수 없습니다"}


def load_status(result, progress=None, collection_progress=None):
    data = load_summary(result)
    data["api_version"] = 1
    data["execution"] = read_progress(progress)
    data["collection"] = read_progress(collection_progress, collection=True)
    return data


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, result=None, progress=None, collection_progress=None, **kwargs):
        self.result = result
        self.progress = progress
        self.collection_progress = collection_progress
        super().__init__(*args, **kwargs)

    def send_bytes(self, payload, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        # DNS 재바인딩 등으로 외부 호스트가 루프백 서버를 읽는 것을 차단한다.
        hosts = self.headers.get_all("Host", [])
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            allowed_hosts.update({"127.0.0.1", "localhost"})
        if len(hosts) != 1 or hosts[0].lower() not in allowed_hosts:
            self.send_bytes(b"Forbidden host", "text/plain", 403)
            return
        # 다른 웹사이트가 로컬 결과를 읽도록 CORS를 허용하지 않는다.
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.send_bytes(b"Forbidden", "text/plain", 403)
            return
        try:
            path = unquote(urlparse(self.path).path)
            if path == "/api/status":
                payload = json.dumps(load_status(self.result, self.progress, self.collection_progress), ensure_ascii=False, allow_nan=False).encode("utf-8")
                self.send_bytes(payload, "application/json; charset=utf-8")
                return
            if path.startswith("/artifact/"):
                if self.result is None:
                    raise ValueError("연결된 결과가 없습니다")
                relative = path.removeprefix("/artifact/")
                data = load_summary(self.result)
                allowed = {str(a[k]) for a in data.get("artifacts", []) for k in ("csv", "png") if a.get(k)}
                if relative not in allowed or Path(relative).suffix.lower() not in {".csv", ".png"}:
                    raise ValueError("공개 대상으로 등록되지 않은 결과입니다")
                source = contained_file(self.result, relative)
            else:
                relative = "index.html" if path == "/" else path.lstrip("/")
                if relative not in {"index.html", "app.js", "style.css", "NanumGothic-Bold.ttf", "OFL.txt", "formulas.html", "formulas.css"}:
                    raise ValueError("공개 파일이 아닙니다")
                source = contained_file(ROOT / "web", relative)
            mime = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
            self.send_bytes(source.read_bytes(), mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.send_bytes(json.dumps({"error": "요청한 자료를 읽을 수 없습니다. 결과 형식과 연결 설정을 확인해 주세요."}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", 404)

    def log_message(self, fmt, *args):
        # 파일 경로나 입력 내용을 운영 로그에 복제하지 않는다.
        return


def main():
    parser = argparse.ArgumentParser(description="Balance Compass 읽기 전용 화면")
    parser.add_argument("--result", type=Path, help="summary.json이 있는 결과 폴더")
    parser.add_argument("--progress", type=Path, help="읽을 학습 진행 JSON 파일")
    parser.add_argument("--collection-progress", type=Path, help="읽을 수집 진행 JSON 파일")
    parser.add_argument("--port", type=int, default=8776)
    args = parser.parse_args()
    result = args.result.resolve() if args.result else None
    if result:
        load_summary(result)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, result=result, progress=args.progress.resolve() if args.progress else None, collection_progress=args.collection_progress.resolve() if args.collection_progress else None))
    print(f"Balance Compass: http://127.0.0.1:{server.server_port} (읽기 전용)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
