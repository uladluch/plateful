#!/usr/bin/env python3
"""Приёмник снимка: страница сети отправляет снятое сюда, мы кладём на диск.

    python3 backend/scripts/catch_snapshot.py backend/cache/mcdonalds.json

Нужен там, где сеть не пускает ни curl, ни Python (смотрит на отпечаток
TLS), и меню снимается настоящим браузером — см. `backend/data/collect/`.
Из страницы наружу ведёт только один путь: её CSP закрывает `connect-src`,
но не `form-action`, поэтому снимок приходит обычной формой, а не fetch.

Слушает только петлю, живёт до Ctrl-C и берёт ровно одну отправку.
"""
from __future__ import annotations

import http.server
import json
import sys
from pathlib import Path

PORT = 8977


def handler(out: Path):
    class Catch(http.server.BaseHTTPRequestHandler):

        def _cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            text = body.decode("utf-8", errors="replace")
            # `enctype=text/plain` шлёт «имя=значение»: имя поля наше.
            if text.startswith("d="):
                text = text[2:]
            payload = json.loads(text)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            size = len(payload) if isinstance(payload, (list, dict)) else "?"
            print(f"принято: {size} записей → {out}")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args) -> None:
            pass

    return Catch


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    out = Path(sys.argv[1]).resolve()
    print(f"жду снимок на http://127.0.0.1:{PORT}/ → {out}")
    server = http.server.HTTPServer(("127.0.0.1", PORT), handler(out))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nостановлен")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
