"""audit_artifacts.audit 的单元测试 —— 覆盖产物链各阶段与断链判定。"""

from pathlib import Path

from scripts.audit_artifacts import audit


def _touch(root: Path, rel: str) -> None:
    """在临时目录里造一个文件（自动建父目录）。"""
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")


def test_empty_root_is_none_stage_and_ok(tmp_path):
    result = audit(tmp_path)
    assert result["stage"] == "none"
    assert result["ok"] is True
    assert not result["broken_links"]


def test_only_intent_is_intent_stage(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    result = audit(tmp_path)
    assert result["stage"] == "intent"
    assert result["ok"] is True


def test_intent_spec_is_spec_stage(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    _touch(tmp_path, "spec.md")
    result = audit(tmp_path)
    assert result["stage"] == "spec"
    assert result["ok"] is True


def test_full_chain_ends_at_tests(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    _touch(tmp_path, "spec.md")
    _touch(tmp_path, "plan.md")
    _touch(tmp_path, "src/todos.py")
    _touch(tmp_path, "tests/test_todos.py")
    result = audit(tmp_path)
    assert result["stage"] == "tests"
    assert result["ok"] is True


def test_src_without_py_does_not_count(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    _touch(tmp_path, "spec.md")
    _touch(tmp_path, "plan.md")
    (tmp_path / "src").mkdir()
    result = audit(tmp_path)
    assert result["stage"] == "plan"


def test_tests_without_test_files_does_not_count(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    _touch(tmp_path, "spec.md")
    _touch(tmp_path, "plan.md")
    _touch(tmp_path, "src/todos.py")
    (tmp_path / "tests").mkdir()
    result = audit(tmp_path)
    assert result["stage"] == "src"


def test_spec_without_intent_is_broken(tmp_path):
    _touch(tmp_path, "spec.md")
    result = audit(tmp_path)
    assert result["ok"] is False
    assert any("intent" in b for b in result["broken_links"])


def test_code_without_plan_is_broken(tmp_path):
    _touch(tmp_path, "intent/intent.md")
    _touch(tmp_path, "spec.md")
    _touch(tmp_path, "src/todos.py")
    result = audit(tmp_path)
    assert result["ok"] is False
    assert any("plan" in b for b in result["broken_links"])

def test_archived_intent_does_not_count(tmp_path):
    # 归档（intent/archive/）里的 MRD 不算活跃：顶层无 *.md 则 intent 环节缺失，spec 变成断链
    _touch(tmp_path, "intent/archive/tags-webpage.md")
    _touch(tmp_path, "spec.md")
    result = audit(tmp_path)
    assert result["stage"] == "spec"
    assert result["ok"] is False
    assert any("intent" in b for b in result["broken_links"])
