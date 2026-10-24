"""عميل ASGI صغير للاختبارات (لا httpx): يستدعي التطبيق مباشرة ``await app(scope, receive, send)``."""
from __future__ import annotations

import asyncio
import json
from urllib.parse import urlsplit


class Response:
    def __init__(self, status: int, headers: dict, body: bytes):
        self.status, self.headers, self.body = status, headers, body

    def json(self):
        return json.loads(self.body.decode("utf-8"))

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")


async def _call(app, method: str, url: str) -> Response:
    u = urlsplit(url)
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method, "scheme": "http",
             "path": u.path, "raw_path": u.path.encode(), "query_string": u.query.encode(), "root_path": "",
             "headers": [(b"host", b"testserver")], "client": ("127.0.0.1", 1), "server": ("testserver", 80)}
    sent, got = [], {"done": False}

    async def receive():
        if not got["done"]:
            got["done"] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.sleep(3600)

    async def send(msg):
        sent.append(msg)

    await app(scope, receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    hdr = {k.decode().lower(): v.decode() for k, v in start["headers"]}
    return Response(start["status"], hdr, body)


class Client:
    def __init__(self, app):
        self.app = app

    def request(self, method: str, url: str) -> Response:
        return asyncio.run(_call(self.app, method, url))

    def get(self, url: str) -> Response:
        return self.request("GET", url)
