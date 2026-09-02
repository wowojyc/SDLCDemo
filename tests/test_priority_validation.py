"""priority 边界校验测试：非法值拒绝（400 invalid_priority），合法值正常创建。"""

from __future__ import annotations

import io
import json

import pytest

from src.api import _TODOS, Handler


class _SilentHandler(Handler):
    def log_message(self, *args) -> None:
        pass


@pytest.fixture(autouse=True)
def _clean_todos():
    _TODOS.clear()
    yield
    _TODOS.clear()


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
    """模拟一次请求，返回 (状态码, 解析后的 JSON 响应体；非 JSON 时为 None)。"""
    lines = [f"{method} {path} HTTP/1.1", "Host: localhost"]
    raw_body = b""
    if body is not None:
        raw_body = json.dumps(body).encode("utf-8")
        lines.append(f"Content-Length: {len(raw_body)}")
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + raw_body
    wfile = io.BytesIO()
    handler = _SilentHandler.__new__(_SilentHandler)
    handler.rfile = io.BytesIO(raw)
    handler.wfile = wfile
    handler.handle()
    wfile.seek(0)
    head, _, payload = wfile.getvalue().partition(b"\r\n\r\n")
    status = int(head.split(b" ")[1])
    try:
        data = json.loads(payload.decode("utf-8")) if payload else None
    except json.JSONDecodeError:
        data = None
    return status, data


@pytest.mark.parametrize(
    "bad", ["abc", 1.5, -1, 100, True], ids=["non-numeric", "float", "negative", "over-99", "bool"]
)
def test_post_todo_invalid_priority_400(bad):
    status, data = _request("POST", "/todos", {"title": "x", "priority": bad})
    assert status == 400
    assert data["error"]["code"] == "invalid_priority"


def test_post_todo_priority_default_ok():
    status, data = _request("POST", "/todos", {"title": "x"})
    assert status == 201
    assert data["priority"] == 0


def test_post_todo_priority_zero_ok():
    status, data = _request("POST", "/todos", {"title": "x", "priority": 0})
    assert status == 201
    assert data["priority"] == 0


def test_post_todo_priority_max_ok():
    status, data = _request("POST", "/todos", {"title": "x", "priority": 99})
    assert status == 201
    assert data["priority"] == 99
