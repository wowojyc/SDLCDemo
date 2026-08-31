"""HTTP 层接口测试：直接实例化 Handler 模拟请求，不起真实端口。"""

from __future__ import annotations

import io
import json

import pytest

from src.api import Handler, _TODOS


class _SilentHandler(Handler):
    def log_message(self, *args) -> None:  # noqa: ANN001
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


def test_get_todos_empty():
    status, data = _request("GET", "/todos")
    assert status == 200
    assert data == []


def test_post_todo_with_tags_then_get():
    status, data = _request("POST", "/todos", {"title": "写周报", "tags": ["工作", "Work"]})
    assert status == 201
    assert data["tags"] == ["工作", "work"]
    status, data = _request("GET", "/todos")
    assert status == 200
    assert data[0]["title"] == "写周报"
    assert data[0]["tags"] == ["工作", "work"]


def test_post_todo_without_tags_matches_old_behavior():
    status, data = _request("POST", "/todos", {"title": "买牛奶"})
    assert status == 201
    assert data["tags"] == []
    status, data = _request("GET", "/todos")
    assert [t["title"] for t in data] == ["买牛奶"]


def test_post_todo_too_many_tags_400():
    status, data = _request("POST", "/todos", {"title": "x", "tags": ["a", "b", "c", "d"]})
    assert status == 400
    assert data["error"]["code"] == "invalid_tags"


def test_post_todo_tags_not_list_400():
    status, data = _request("POST", "/todos", {"title": "x", "tags": "工作"})
    assert status == 400
    assert data["error"]["code"] == "invalid_tags"


def test_post_todo_blank_title_400():
    status, data = _request("POST", "/todos", {"title": "   "})
    assert status == 400
    assert data["error"]["code"] == "invalid_title"


def test_get_todos_filter_by_tag_case_insensitive():
    _request("POST", "/todos", {"title": "开会", "tags": ["Work"]})
    _request("POST", "/todos", {"title": "写周报", "tags": ["工作"]})
    _request("POST", "/todos", {"title": "买牛奶"})
    status, data = _request("GET", "/todos?tag=WORK")
    assert status == 200
    assert [t["title"] for t in data] == ["开会"]


def test_get_todos_done_true_returns_completed():
    _request("POST", "/todos", {"title": "做完了"})
    _request("POST", "/todos", {"title": "没做完"})
    status, _ = _request("POST", "/todos/1/complete")
    status, data = _request("GET", "/todos?done=true")
    assert status == 200
    assert [t["title"] for t in data] == ["做完了"]
    status, data = _request("GET", "/todos")
    assert [t["title"] for t in data] == ["没做完"]


def test_complete_endpoint_ok_and_idempotent():
    _request("POST", "/todos", {"title": "x"})
    status, data = _request("POST", "/todos/1/complete")
    assert status == 200
    assert data["id"] == 1
    status, _ = _request("POST", "/todos/1/complete")
    assert status == 200


def test_complete_missing_id_404():
    status, data = _request("POST", "/todos/999/complete")
    assert status == 404
    assert data["error"]["code"] == "not_found"


def test_complete_non_numeric_id_404():
    status, _ = _request("POST", "/todos/abc/complete")
    assert status == 404


def test_get_index_serves_page():
    status, _ = _request("GET", "/")
    assert status == 200


def test_unknown_path_404():
    status, _ = _request("GET", "/unknown")
    assert status == 404
