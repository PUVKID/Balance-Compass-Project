"""로컬 연구 결과를 읽기 전용으로 제공한다."""
import argparse
import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
import mimetypes

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


def load_summary(result):
    if result is None:
        return {"mode": "UNCONNECTED", "status": "실제 자료 미연결", "rows": None,
                "targets": {}, "artifacts": [], "limitations": ["과거 클라우드 CSV는 이 컴퓨터에서 확보하지 못했습니다. 전국 본실험은 미실행입니다."]}
    path = contained_file(result, "summary.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("mode") not in {"REAL", "SYNTHETIC"}:
        raise ValueError("결과 유형을 확인할 수 없습니다")
    # 원본 경로나 취득 URL 전체는 브라우저 API에 노출하지 않는다.
    data.pop("provenance", None)
    return data


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, result=None, **kwargs):
        self.result = result
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
                payload = json.dumps(load_summary(self.result), ensure_ascii=False, allow_nan=False).encode("utf-8")
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
                source = contained_file(ROOT / "web", relative)
            mime = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
            self.send_bytes(source.read_bytes(), mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.send_bytes(json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", 404)

    def log_message(self, fmt, *args):
        # 파일 경로나 입력 내용을 운영 로그에 복제하지 않는다.
        return


def main():
    parser = argparse.ArgumentParser(description="Balance Compass 읽기 전용 화면")
    parser.add_argument("--result", type=Path, help="summary.json이 있는 결과 폴더")
    parser.add_argument("--port", type=int, default=8776)
    args = parser.parse_args()
    result = args.result.resolve() if args.result else None
    if result:
        load_summary(result)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, result=result))
    print(f"Balance Compass: http://127.0.0.1:{server.server_port} (읽기 전용)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
