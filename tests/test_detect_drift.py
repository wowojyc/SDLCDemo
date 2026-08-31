"""detect_drift.detect 的单元测试 —— 重点覆盖"单调漂移"判定边界。"""

from scripts.detect_drift import detect


def test_insufficient_history_returns_log():
    result = detect([1], 2.0)
    assert result["tier"] == "insufficient_data"
    assert result["action"] == "log"


def test_few_points_descending_does_not_flag_drift():
    # 回归：原 bug 中"全部下降"分支未受 len>=6 保护，样本不足也误判漂移
    result = detect([3, 2], 1.8)
    assert result["tier"] == "1sigma"
    assert "单调漂移" not in result["reason"]


def test_few_points_ascending_does_not_flag_drift():
    result = detect([1, 2], 2.4)
    assert result["tier"] == "1sigma"
    assert "单调漂移" not in result["reason"]


def test_six_points_monotonic_descending_flags_drift():
    # 6 点以上持续同向（即使 σ 档位只有 1σ）→ 升档到 2σ
    result = detect([6, 5, 4, 3, 2, 1], 0.2)
    assert result["tier"] == "2sigma"
    assert result["action"] == "diagnose"
    assert "单调漂移" in result["reason"]


def test_six_points_monotonic_ascending_flags_drift():
    result = detect([1, 2, 3, 4, 5, 6], 6.8)
    assert result["tier"] == "2sigma"
    assert "单调漂移" in result["reason"]
