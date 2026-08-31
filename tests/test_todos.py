import pytest

from src.todos import Todo, add, complete, pending, sorted_by_priority


def test_add_assigns_incrementing_ids():
    todos: list[Todo] = []
    a = add(todos, "写 intent.md", priority=2)
    b = add(todos, "跑通 demo", priority=1)
    assert (a.id, b.id) == (1, 2)
    assert len(todos) == 2


def test_add_rejects_blank_title():
    with pytest.raises(ValueError):
        add([], "   ")


def test_complete_marks_done_and_raises_when_missing():
    todos: list[Todo] = []
    t = add(todos, "验收 Gate 0")
    assert complete(todos, t.id).done is True
    with pytest.raises(KeyError):
        complete(todos, 999)


def test_sorted_by_priority_then_created_at():
    todos = [
        Todo(id=1, title="低", priority=1, created_at="2026-01-01T00:00:00"),
        Todo(id=2, title="高但更晚", priority=5, created_at="2026-01-02T00:00:00"),
        Todo(id=3, title="高且更早", priority=5, created_at="2026-01-01T12:00:00"),
    ]
    assert [t.id for t in sorted_by_priority(todos)] == [3, 2, 1]


def test_pending_excludes_done():
    todos: list[Todo] = []
    a = add(todos, "做完了的", priority=9)
    complete(todos, a.id)
    add(todos, "还没做", priority=1)
    assert [t.title for t in pending(todos)] == ["还没做"]
