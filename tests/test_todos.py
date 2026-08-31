import pytest

from src.todos import Todo, add, clean_tags, complete, completed, filter_by_tag, pending, sorted_by_priority


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


def test_add_stores_tags_lowercased_stripped_deduped():
    todos: list[Todo] = []
    t = add(todos, "写周报", tags=["工作", " 工作 ", "Work"])
    assert t.tags == ["工作", "work"]


def test_add_cleans_before_limit_check():
    # 6 个原始标签，去重后只剩 3 个，不报错
    t = add([], "标题", tags=["a", "a", "b", "b", "c", "c"])
    assert t.tags == ["a", "b", "c"]


def test_add_rejects_more_than_max_tags():
    with pytest.raises(ValueError):
        add([], "标题", tags=["a", "b", "c", "d"])


def test_add_blank_tags_ignored():
    t = add([], "标题", tags=["  ", "", "  "])
    assert t.tags == []


def test_clean_tags_normalizes():
    assert clean_tags([" 工作 ", "WORK", "工作", ""]) == ["工作", "work"]


def test_filter_by_tag_case_insensitive_and_sorted():
    todos: list[Todo] = []
    add(todos, "低优先", tags=["Work"])
    add(todos, "高优先", tags=["work"], priority=5)
    assert [t.title for t in filter_by_tag(todos, "WORK")] == ["高优先", "低优先"]


def test_filter_by_tag_excludes_untagged_and_blank():
    todos: list[Todo] = []
    add(todos, "无标签")
    add(todos, "有标签", tags=["家里"])
    assert [t.title for t in filter_by_tag(todos, "家里")] == ["有标签"]
    assert filter_by_tag(todos, "   ") == []


def test_completed_returns_only_done_sorted():
    todos: list[Todo] = []
    a = add(todos, "完成的高优先", priority=9)
    complete(todos, a.id)
    add(todos, "未完成", priority=5)
    b = add(todos, "完成的低优先")
    complete(todos, b.id)
    assert [t.title for t in completed(todos)] == ["完成的高优先", "完成的低优先"]
