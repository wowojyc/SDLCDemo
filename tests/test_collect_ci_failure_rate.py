"""collect_ci_failure_rate 的单元测试 —— 失败率统计与滚动历史裁剪。"""

from scripts.collect_ci_failure_rate import append_value, failure_rate


def _run(conclusion: str) -> dict:
    return {"conclusion": conclusion}


def test_all_success_returns_zero():
    runs = [_run("success"), _run("success"), _run("success")]
    assert failure_rate(runs) == 0.0


def test_failure_ratio_is_correct():
    runs = [_run("success") for _ in range(8)] + [_run("failure") for _ in range(2)]
    assert failure_rate(runs) == 0.2


def test_timed_out_counts_as_failure():
    runs = [_run("success"), _run("success"), _run("timed_out")]
    assert failure_rate(runs) == 1 / 3


def test_action_required_counts_as_failure():
    runs = [_run("success"), _run("action_required")]
    assert failure_rate(runs) == 0.5


def test_cancelled_and_skipped_excluded_from_denominator():
    # 若 cancelled/skipped 误入分母，比例会是 1/3≈0.333；正确排除后应为 0.5
    runs = [_run("success"), _run("cancelled"), _run("skipped"), _run("failure")]
    assert failure_rate(runs) == 0.5


def test_stale_excluded():
    runs = [_run("success"), _run("stale"), _run("failure")]
    assert failure_rate(runs) == 0.5


def test_empty_list_returns_zero():
    assert failure_rate([]) == 0.0


def test_append_value_normal():
    assert append_value([0.1, 0.2], 0.3, cap=60) == [0.1, 0.2, 0.3]


def test_append_value_trims_head_when_over_cap():
    values = [round(i * 0.01, 2) for i in range(1, 61)]  # 60 条
    result = append_value(values, 0.61, cap=60)
    assert len(result) == 60
    assert result[0] == 0.02  # 头部 0.01 被裁掉
    assert result[-1] == 0.61


def test_append_value_exact_cap_no_trim():
    values = [0.1, 0.2, 0.3]
    result = append_value(values, 0.4, cap=3)
    assert result == [0.2, 0.3, 0.4]
