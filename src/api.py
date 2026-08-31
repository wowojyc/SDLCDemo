"""HTTP 层（薄）：只做参数校验与转发，业务逻辑全在 src/todos.py。

零依赖实现（标准库 http.server），方便 demo 直接 `make run`。
生产项目请换成 FastAPI / Flask 等，分层原则不变。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .todos import Todo, add, pending

# 演示用内存存储；真实项目请换成持久化
_TODOS: list[Todo] = []


class Handler(BaseHTTPRequestHandler):
    """只处理 /todos 一个端点，GET 查未完成（按优先级）、POST 新增。"""

    def _respond(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server 约定的方法名
        if urlparse(self.path).path != "/todos":
            self.send_error(404)
            return
        self._respond(
            200,
            [
                {"id": t.id, "title": t.title, "priority": t.priority}
                for t in pending(_TODOS)
            ],
        )

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/todos":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")

        try:
            todo = add(_TODOS, payload.get("title", ""), payload.get("priority", 0))
        except ValueError as exc:
            # 统一错误结构，不把栈信息吐给调用方
            self._respond(400, {"error": {"code": "invalid_title", "message": str(exc)}})
        else:
            self._respond(201, {"id": todo.id, "title": todo.title})


def main() -> None:
    print("listening on http://127.0.0.1:8000/todos")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()


if __name__ == "__main__":
    main()
