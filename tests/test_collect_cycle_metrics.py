"""collect_cycle_metrics 纯函数的单元测试 —— 覆盖空集合/None/同 commit/负周期等边界。"""

import pytest

from scripts.collect_cycle_metrics import (
    closes_from_body,
    cycle_seconds,
    read_type,
    rework_count,
    survival_rate,
)

# --- survival_rate：按类型分派的完成率 ---

def test_survival_empty_total_returns_zero():
    assert survival_rate(0, 0) == 0.0


def test_survival_partial_ratio():
    assert survival_rate(2, 3) == pytest.approx(2 / 3)


def test_survival_all_completed_is_one():
    assert survival_rate(3, 3) == 1.0


# --- rework_count：plan 首次提交后的 spec 内容修改次数 ---

def test_rework_empty_timestamps_is_zero():
    assert rework_count([], 1000) == 0


def test_rework_all_before_plan_is_zero():
    assert rework_count([100, 200], 1000) == 0


def test_rework_counts_only_after_plan_first_commit():
    assert rework_count([100, 2000, 3000], 1500) == 2


def test_rework_same_commit_as_plan_not_counted():
    # 回归：spec/plan 同 commit（本仓库实证）不算返工——严格大于
    assert rework_count([1000, 2000], 1000) == 1


# --- cycle_seconds：需求周期，任一端缺失 → None ---

def test_cycle_missing_start_is_none():
    assert cycle_seconds(None, 2000) is None


def test_cycle_missing_end_is_none():
    assert cycle_seconds(1000, None) is None


def test_cycle_negative_is_none():
    # 数据异常（终点早于起点）不伪装成功
    assert cycle_seconds(3000, 1000) is None


def test_cycle_normal_difference():
    assert cycle_seconds(1000, 2500) == 1500


# --- closes_from_body：从 merge commit %B 提取 Issue 号 ---

def test_closes_single():
    assert closes_from_body("feat(x): 双轨修正 (Closes #27)") == {27}


def test_closes_multiple_issues():
    assert closes_from_body("feat(x): a (Closes #12, Closes #13)") == {12, 13}


def test_closes_case_insensitive_variants():
    body = "fix(x): y\n\ncloses #4\nresolves #5"
    assert closes_from_body(body) == {4, 5}


def test_closes_none_returns_empty_set():
    assert closes_from_body("feat(x): 与 Issue 无关的改动") == set()


def test_closes_issue_number_not_pr():
    # 只认 # 前缀数字，不误吞正文其他 # 引用
    assert closes_from_body("见 #100 讨论，Closes #27") == {27}


# --- read_type：从 intent 头部读类型字段 ---

def test_read_type_present():
    header = "# 意图：x\n\n## 意图 / 作者 / 状态 / 来源 / 类型\n- 作者：demo｜状态：已批准｜来源：Issue #4｜类型：规则工具型"
    assert read_type(header) == "规则工具型"


def test_read_type_missing_returns_none():
    header = "# 意图：x\n\n## 意图 / 作者 / 状态 / 来源\n- 作者：demo｜状态：已批准｜来源：Issue #18"
    assert read_type(header) is None


def test_read_type_unknown_value_returned_as_is():
    # 未知值原样返回，由调用方告警（不静默吞掉拼写错误）
    assert read_type("- 作者：demo｜类型：调研") == "调研"


def test_read_type_stops_at_parenthesis():
    # 回归：类型值后跟说明文字（括号）不污染枚举——取到纯枚举值
    assert read_type("- 类型：实现型（主型；兼改模板体系）") == "实现型"
