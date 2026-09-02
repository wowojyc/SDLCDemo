"""audit_artifacts.audit 的单元测试 —— 覆盖需求维度文档链与孤儿断链判定。"""

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
    assert result["requirements"] == []


def test_only_intent_is_intent_stage(tmp_path):
    _touch(tmp_path, "intent/flow-tracking.md")
    result = audit(tmp_path)
    assert result["stage"] == "intent"
    assert result["ok"] is True
    assert result["requirements"][0]["stage"] == "intent"


def test_intent_spec_is_spec_stage(tmp_path):
    _touch(tmp_path, "intent/flow-tracking.md")
    _touch(tmp_path, "spec/flow-tracking.md")
    result = audit(tmp_path)
    assert result["stage"] == "spec"
    assert result["ok"] is True


def test_full_doc_chain_ends_at_plan(tmp_path):
    _touch(tmp_path, "intent/flow-tracking.md")
    _touch(tmp_path, "spec/flow-tracking.md")
    _touch(tmp_path, "plan/flow-tracking.md")
    result = audit(tmp_path)
    assert result["stage"] == "plan"
    assert result["ok"] is True


def test_plan_without_spec_is_allowed(tmp_path):
    # 弹性链：不需要设计的需求可以直接 intent + plan
    _touch(tmp_path, "intent/flow-tracking.md")
    _touch(tmp_path, "plan/flow-tracking.md")
    result = audit(tmp_path)
    assert result["stage"] == "plan"
    assert result["ok"] is True


def test_spec_without_plan_is_allowed(tmp_path):
    # 弹性链：不需要开发的需求可以只有 spec
    _touch(tmp_path, "intent/flow-tracking.md")
    _touch(tmp_path, "spec/flow-tracking.md")
    result = audit(tmp_path)
    assert result["stage"] == "spec"
    assert result["ok"] is True


def test_orphan_spec_is_broken(tmp_path):
    # 孤儿文档：spec 存在但无对应活跃 intent
    _touch(tmp_path, "spec/ghost.md")
    result = audit(tmp_path)
    assert result["ok"] is False
    assert any("spec/ghost.md" in b for b in result["broken_links"])


def test_archived_spec_left_active_is_broken(tmp_path):
    # 归档遗漏：intent 已归档，但 spec 还留在顶层 → 孤儿断链
    _touch(tmp_path, "intent/archive/tags-webpage.md")
    _touch(tmp_path, "spec/tags-webpage.md")
    result = audit(tmp_path)
    assert result["ok"] is False
    assert any("spec/tags-webpage.md" in b for b in result["broken_links"])


def test_archived_docs_do_not_count(tmp_path):
    # 归档的完整文档链不算活跃：全部归档后 stage=none
    _touch(tmp_path, "intent/archive/tags-webpage.md")
    _touch(tmp_path, "spec/archive/tags-webpage.md")
    _touch(tmp_path, "plan/archive/tags-webpage.md")
    result = audit(tmp_path)
    assert result["stage"] == "none"
    assert result["ok"] is True


def test_src_without_py_does_not_count(tmp_path):
    _touch(tmp_path, "intent/flow-tracking.md")
    (tmp_path / "src").mkdir()
    result = audit(tmp_path)
    assert result["artifacts"][3]["exists"] is False
    assert result["stage"] == "intent"


def test_tests_without_test_files_does_not_count(tmp_path):
    _touch(tmp_path, "intent/flow-tracking.md")
    (tmp_path / "tests").mkdir()
    result = audit(tmp_path)
    assert result["artifacts"][4]["exists"] is False
    assert result["stage"] == "intent"


def test_shared_src_tests_do_not_raise_stage(tmp_path):
    # 代码/测试是仓库共享现状：有代码但需求只有 intent，stage 仍是 intent
    _touch(tmp_path, "intent/flow-tracking.md")
    _touch(tmp_path, "src/todos.py")
    _touch(tmp_path, "tests/test_todos.py")
    result = audit(tmp_path)
    assert result["stage"] == "intent"
    assert result["ok"] is True
