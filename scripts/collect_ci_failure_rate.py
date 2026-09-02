"""CI 失败率采集 —— 把真实数据喂给维护闭环（maintenance-scan）。

背景：metrics/ci_test_failure_rate.json 此前只有示例数据，没有任何环节写入真实值，
maintenance-scan 每天检测的是静止值，永远不会触发 diagnose/act。

本脚本补齐"传感器"：拉最近 N 次 main push 的 ci.yml 运行结果 → 统计失败率
→ 追加一条到 metrics 历史（滚动保留上限 M 条）。由 maintenance-scan 的
collect job 每日调用；纯函数部分（failure_rate / append_value）可单测。

用法:
    GH_TOKEN=xxx GITHUB_REPOSITORY=owner/repo python scripts/collect_ci_failure_rate.py

输出（stdout）:
    追加后的最新失败率，如 0.0333
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# GitHub Actions runs API 的判定集合：cancelled/skipped/stale 不是 CI 判定结果，不进分母
_COUNTED = {"success", "failure", "timed_out", "action_required"}
_N_RUNS = 30      # 采集窗口：最近 N 次 main push 的 ci.yml run
_CAP = 60         # metrics 历史保留上限（约两个月日采）
_REPO_ROOT = Path(__file__).resolve().parent.parent
_METRICS_FILE = _REPO_ROOT / "metrics" / "ci_test_failure_rate.json"


def failure_rate(runs: list[dict]) -> float:
    """给定 GitHub runs API 的 item 列表，统计失败率（0.0~1.0）。

    分母 = conclusion 属于 {success, failure, timed_out, action_required} 的 run；
    分子 = 分母中非 success 的 run。空列表返回 0.0。
    """
    counted = [r for r in runs if r.get("conclusion") in _COUNTED]
    if not counted:
        return 0.0
    failed = sum(1 for r in counted if r.get("conclusion") != "success")
    return failed / len(counted)


def append_value(values: list[float], value: float, cap: int = _CAP) -> list[float]:
    """追加一个采样值，超出 cap 时从头部裁剪（滚动窗口）。"""
    return (values + [value])[-cap:]


def _fetch_runs(token: str, repo: str) -> list[dict]:
    """调用 GitHub Actions runs API，返回 ci.yml 最近 N 次 push 事件的 run 列表。"""
    url = (
        f"https://api.github.com/repos/{repo}/actions/runs"
        f"?workflow_id=ci.yml&event=push&per_page={_N_RUNS}"
    )
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "collect-ci-failure-rate",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("workflow_runs", [])


def _load_history(path: Path) -> dict:
    """读 metrics JSON；文件缺失或字段不全时返回空历史骨架。"""
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("values", [])
            return data
    return {"_说明": "由 maintenance-scan 每日采集追加，勿手改", "metric": "ci_test_failure_rate",
            "unit": "ratio", "values": []}


def _save_history(path: Path, data: dict) -> None:
    """原子写回：先写同目录临时文件再替换，避免半截文件。"""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    token = os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        print("::error::缺少环境变量 GH_TOKEN 或 GITHUB_REPOSITORY", file=sys.stderr)
        return 1

    try:
        runs = _fetch_runs(token, repo)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"::error::拉取 ci.yml runs 失败：{exc}", file=sys.stderr)
        return 1

    if not runs:
        # 空列表视为数据异常（本仓库必有 push run），不写假数据，告警后跳过
        print("::warning::最近窗口内没有 ci.yml 的 push run，跳过本次采样")
        return 0

    rate = round(failure_rate(runs), 4)
    data = _load_history(_METRICS_FILE)
    data["values"] = append_value(data.get("values", []), rate)
    _save_history(_METRICS_FILE, data)
    print(rate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
