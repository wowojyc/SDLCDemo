"""HTTP 层（薄）：只做参数校验与转发，业务逻辑全在 src/todos.py。

零依赖实现（标准库 http.server），方便 demo 直接 `make run`。
生产项目请换成 FastAPI / Flask 等，分层原则不变。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .todos import Todo, add, complete, completed, filter_by_tag, pending

# 演示用内存存储；真实项目请换成持久化
_TODOS: list[Todo] = []

# 页面文件：相对本文件定位，不依赖启动时的工作目录
_INDEX_HTML = Path(__file__).resolve().parent.parent / "web" / "index.html"


def _todo_dict(todo: Todo) -> dict:
    """序列化一条待办（含标签）。"""
    return {
        "id": todo.id,
        "title": todo.title,
        "priority": todo.priority,
        "tags": todo.tags,
    }


class Handler(BaseHTTPRequestHandler):
    """处理 /todos（GET 查、POST 增、POST /{id}/complete 完成）与 /（页面）。"""

    def _respond(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str) -> None:
        """统一错误结构，不把栈信息吐给调用方。"""
        self._respond(status, {"error": {"code": code, "message": message}})

    def _serve_index(self) -> None:
        try:
            body = _INDEX_HTML.read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_index()
            return
        if parsed.path != "/todos":
            self.send_error(404)
            return
        params = parse_qs(parsed.query)
        tag = params.get("tag", [None])[0]
        done = params.get("done", [None])[0]
        items = completed(_TODOS) if done == "true" else pending(_TODOS)
        if tag is not None:
            items = filter_by_tag(items, tag)
        self._respond(200, [_todo_dict(t) for t in items])

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/todos":
            self._create_todo()
            return
        if parsed.path.startswith("/todos/") and parsed.path.endswith("/complete"):
            self._complete_todo()
            return
        self.send_error(404)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}

    def _create_todo(self) -> None:
        """新增待办：边界先校验类型，业务规则交给领域层。"""
        payload = self._read_json()
        title = payload.get("title", "")
        if not isinstance(title, str) or not title.strip():
            self._error(400, "invalid_title", "title 不能为空")
            return
        raw_tags = payload.get("tags", [])
        if not isinstance(raw_tags, list):
            self._error(400, "invalid_tags", "tags 必须是数组")
            return
        try:
            todo = add(_TODOS, title, payload.get("priority", 0), tags=raw_tags)
        except ValueError as exc:
            # 到这里只剩标签超限一种情况（标题已在边界校验）
            self._error(400, "invalid_tags", str(exc))
        else:
            self._respond(201, _todo_dict(todo))

    def _complete_todo(self) -> None:
        """标记完成：id 非数字或不存在都返回 404 统一错误结构。"""
        parsed = urlparse(self.path)
        try:
            todo_id = int(parsed.path.split("/")[2])
        except (IndexError, ValueError):
            self._error(404, "not_found", "待办不存在")
            return
        try:
            todo = complete(_TODOS, todo_id)
        except KeyError as exc:
            self._error(404, "not_found", str(exc))
        else:
            self._respond(200, _todo_dict(todo))


def main() -> None:
    print("listening on http://127.0.0.1:8000/todos")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()


if __name__ == "__main__":
    main()
