"""过程指标采集 —— 把需求链路的时间维度变成可度量的事实。

背景：metrics/ci_test_failure_rate.json 只覆盖产品指标，过程指标整层缺失——无法回答
"一条需求从登记到落地要多久、多少需求真正落地"。对照 Anthropic《AI-Native SDLC
Playbook》，Plan/Design/Build 阶段都应配先行/滞后度量。本脚本补齐三项：

    M1 intent 存活率 —— 按类型分派完成证据（实现/规则工具型：含 Closes #Issue 的
       merge commit，无 Issue 或早期直推则归档动作兜底；调研梳理型：归档 + 结论节非空）
    M2 spec 返工次数 —— plan 首次提交之后 spec 的内容修改提交次数
       （--diff-filter=M 排除新增与归档重命名）
    M3 需求周期 —— 起点 Issue created_at（API 模式）/ intent 首次提交（git 降级）；
       终点 merge commit（%B 解析 Closes #Issue，纯 git）或归档 rename 兜底

口径细节见 spec/process-metrics.md §3。确定性铁律：只读 Git 历史与（可选）GitHub API，
不用 AI 判断；需求类型是人工填写项（intent 头部），脚本只读不推断，未知值告警不静默。

用法:
    python scripts/collect_cycle_metrics.py [--format json|markdown]
环境变量（可选）:
    GH_TOKEN + GITHUB_REPOSITORY=owner/repo —— 提供时周期起点用 Issue created_at
    （API 模式）；缺失时降级 git 模式（intent 首次提交，语义略窄，stderr 标注）。

输出（stdout）:
    JSON：{"generated_at", "mode", "survival", "rework", "cycle", "requirements"}
    Markdown：人读进度表（存活明细 / 返工表 / 周期表）
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_INTENT_DIR = _REPO_ROOT / "intent"
_ARCHIVE_DIR = _INTENT_DIR / "archive"

# 类型枚举：主型单选；未知值告警不静默
KNOWN_TYPES = ("实现型", "规则工具型", "调研梳理型")
# GitHub 自动写进 merge commit 的关键词：close/fix/resolve 家族 + #Issue
_CLOSES_RE = re.compile(r"(?i)\b(?:close[sd]?|fix(?:es|ed)?|resolve[sd]?)\s+#(\d+)")
_TYPE_RE = re.compile(r"类型[:：]\s*([^\s｜|（）()]+)")
_SOURCE_RE = re.compile(r"来源[:：]\s*Issue\s*#(\d+)")


def survival_rate(completed: int, total: int) -> float:
    """需求完成率（0.0~1.0）；分母为 0 时返回 0.0（无数据不算失败）。"""
    if total <= 0:
        return 0.0
    return completed / total


def rework_count(spec_m_ts: list[int], plan_first_ts: int) -> int:
    """plan 首次提交之后 spec 的内容修改次数；同 commit（等于）不算返工。"""
    return sum(1 for ts in spec_m_ts if ts > plan_first_ts)


def cycle_seconds(start: int | None, end: int | None) -> int | None:
    """需求周期秒数；任一端缺失或终点早于起点（数据异常）返回 None，不伪装成功。"""
    if start is None or end is None or end < start:
        return None
    return end - start


def closes_from_body(body: str) -> set[int]:
    """从 merge commit 完整 message（%B）提取 Closes/Fixes/Resolves 引用的 Issue 号。"""
    return {int(m) for m in _CLOSES_RE.findall(body)}


def read_type(header: str) -> str | None:
    """从 intent 头部取类型字段值；缺失返回 None，未知值原样返回（由调用方告警）。"""
    m = _TYPE_RE.search(header)
    return m.group(1) if m else None


def _git_log_ts(rel: str, diff_filter: str = "") -> list[int]:
    """git log 指定文件（--follow）指定 diff 类型提交的时间戳（秒，最新在前）。

    diff_filter 为空时不过滤（全历史）；--follow 跨归档重命名追踪：对已移动到
    archive/ 的文档，从原路径也能取到历史。
    """
    cmd = ["git", "log", "--follow", "--format=%ct", "--", rel]
    if diff_filter:
        cmd.insert(3, f"--diff-filter={diff_filter}")
    out = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=_REPO_ROOT,
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(f"git log {rel} 失败：{out.stderr.strip()}")
    return [int(line) for line in out.stdout.splitlines() if line.strip()]


def _git_ts_any(rel_candidates: list[str], diff_filter: str) -> list[int]:
    """按优先级尝试候选路径（归档路径优先），返回升序时间戳；全空返回 []。"""
    for rel in rel_candidates:
        ts = _git_log_ts(rel, diff_filter)
        if ts:
            return sorted(ts)
    return []


def _git_first_ts(rel_candidates: list[str]) -> int | None:
    """文档诞生时间（最早 commit，跨归档 rename 追踪）。

    --follow 对多跳改名（早期 plan.md → plan/<slug>.md → plan/archive/<slug>.md）
    可能漏 --diff-filter=A，此时回退无过滤取最早时间戳。
    """
    for rel in rel_candidates:
        ts = _git_log_ts(rel, "A")
        if ts:
            return min(ts)
        all_ts = _git_log_ts(rel)
        if all_ts:
            return min(all_ts)
    return None


def _scan_merges() -> dict[int, int]:
    """全历史 merge commit 扫描：{Issue 号: 最近含 Closes 的 merge 时间戳}。

    %x00 分块（commit message 不含 NUL）防 %B 多行打乱行解析；块内 %ct%x1f%B。
    多 PR 需求（如 #18 有 4 个 PR）取最大值 = 收尾 merge。
    """
    out = subprocess.run(
        ["git", "log", "--merges", "--format=%x00%ct%x1f%B"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=_REPO_ROOT,
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(f"git log --merges 失败：{out.stderr.strip()}")
    by_issue: dict[int, int] = {}
    for chunk in out.stdout.split("\x00"):
        if "\x1f" not in chunk:
            continue
        ts_str, body = chunk.split("\x1f", 1)
        ts = int(ts_str)
        for issue in closes_from_body(body):
            if issue not in by_issue or ts > by_issue[issue]:
                by_issue[issue] = ts
    return by_issue


def _fetch_issue_created(repo: str, issue: int, token: str) -> int | None:
    """GitHub API 取 Issue created_at（epoch 秒）；失败告警返回 None（调用方兜底降级）。"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "collect-cycle-metrics",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"::warning::拉取 Issue #{issue} 创建时间失败：{exc}", file=sys.stderr)
        return None
    created = data.get("created_at", "")
    if not created:
        return None
    parsed = dt.datetime.strptime(created[:-1] + "+00:00", "%Y-%m-%dT%H:%M:%S%z")
    return int(parsed.replace(tzinfo=dt.timezone.utc).timestamp())


def _load_intents() -> list[dict]:
    """扫描 intent 顶层（活跃）与 archive/（已归档），读 slug/来源 Issue/类型/结论节。"""
    rows: list[dict] = []
    for directory, archived in ((_INTENT_DIR, False), (_ARCHIVE_DIR, True)):
        if not directory.is_dir():
            continue
        for p in sorted(directory.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            m = _SOURCE_RE.search(text)
            rows.append(
                {
                    "slug": p.stem,
                    "source_issue": int(m.group(1)) if m else None,
                    "type": read_type(text),
                    "archived": archived,
                    "has_conclusion": "## 结论" in text,
                }
            )
    return rows


def _fmt_ts(ts: int | None) -> str:
    """epoch 秒 → 'YYYY-MM-DD HH:MM UTC'；None → '—'。"""
    if ts is None:
        return "—"
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def _evaluate(rows: list[dict], merges: dict[int, int], api_mode: bool, repo: str, token: str) -> list[dict]:
    """逐需求判定：完成证据、返工、周期（确定性组装，供输出层渲染）。"""
    out: list[dict] = []
    for it in rows:
        slug = it["slug"]
        issue = it["source_issue"]
        typ = it["type"]
        if typ is not None and typ not in KNOWN_TYPES:
            print(f"::warning::intent/{slug}.md 类型未知：{typ}（应为 {'/'.join(KNOWN_TYPES)}）", file=sys.stderr)

        merge_ts = merges.get(issue) if issue is not None else None
        arch_ts = _git_ts_any([f"intent/archive/{slug}.md"], "R")
        arch_first = arch_ts[0] if arch_ts else None

        # 完成证据按类型分派（spec M1）
        if typ == "调研梳理型":
            completed = bool(it["archived"] and it["has_conclusion"])
            evidence = "归档 + 结论节" if completed else ("归档中无结论节" if it["archived"] else "未归档")
        else:
            # 实现/规则工具型：merge Closes 优先，归档 rename 兜底（无 Issue / 早期直推）
            completed = merge_ts is not None or arch_first is not None
            if merge_ts is not None:
                evidence = f"merge Closes #{issue} @ {_fmt_ts(merge_ts)}"
            elif arch_first is not None:
                evidence = f"归档 rename @ {_fmt_ts(arch_first)}"
            else:
                evidence = "进行中（无 merge / 未归档）"

        # M2 返工：plan 首次提交之后 spec 的内容修改（无 plan 不适用）
        spec_m = _git_ts_any([f"spec/archive/{slug}.md", f"spec/{slug}.md"], "M")
        plan_first = _git_first_ts([f"plan/archive/{slug}.md", f"plan/{slug}.md"])
        rework = rework_count(spec_m, plan_first) if plan_first is not None else None

        # M3 周期：起点 Issue created_at（api）/ intent 首次提交（git 降级）；终点 merge 或归档
        if api_mode and issue is not None:
            start = _fetch_issue_created(repo, issue, token)
        else:
            start = _git_first_ts([f"intent/archive/{slug}.md", f"intent/{slug}.md"])
        end = merge_ts if merge_ts is not None else arch_first
        cycle = cycle_seconds(start, end)

        out.append(
            {
                "slug": slug,
                "type": typ,
                "source_issue": issue,
                "archived": it["archived"],
                "completed": completed,
                "evidence": evidence,
                "rework": rework,
                "cycle_seconds": cycle,
                "start": start,
                "end": end,
            }
        )
    return out


def _render_json(generated: str, mode: str, rows: list[dict], total: int, completed: int) -> str:
    """组装机器可读 JSON（含三指标与逐需求明细）。"""
    return json.dumps(
        {
            "generated_at": generated,
            "mode": mode,
            "survival": {"completed": completed, "total": total, "rate": survival_rate(completed, total)},
            "rework": [
                {"slug": r["slug"], "count": r["rework"]} for r in rows if r["rework"] is not None
            ],
            "cycle": [
                {
                    "slug": r["slug"],
                    "cycle_seconds": r["cycle_seconds"],
                    "start": _fmt_ts(r["start"]),
                    "end": _fmt_ts(r["end"]),
                }
                for r in rows
                if r["cycle_seconds"] is not None
            ],
            "requirements": [
                {
                    "slug": r["slug"],
                    "type": r["type"],
                    "source_issue": r["source_issue"],
                    "archived": r["archived"],
                    "completed": r["completed"],
                    "evidence": r["evidence"],
                    "rework": r["rework"],
                    "cycle_seconds": r["cycle_seconds"],
                }
                for r in rows
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def _render_markdown(mode: str, rows: list[dict], total: int, completed: int) -> str:
    """渲染人读进度表（存活明细 / 返工表 / 周期表）。"""
    lines = [f"## SDLC 过程指标（{mode} 模式）", ""]
    lines.append(f"### M1 intent 存活率：{completed}/{total} = {survival_rate(completed, total):.0%}")
    lines.append("| slug | 类型 | 完成 | 证据 |")
    lines.append("|---|---|---|---|")
    for r in rows:
        if r["archived"]:
            mark = "✅" if r["completed"] else "❌"
            lines.append(f"| `{r['slug']}` | {r['type'] or '—'} | {mark} | {r['evidence']} |")
    lines += ["", "### M2 spec 返工次数（plan 首次提交后的内容修改）"]
    lines.append("| slug | 返工 | 明细 |")
    lines.append("|---|---|---|")
    for r in rows:
        if r["rework"] is not None:
            detail = "0（spec/plan 同 commit 或一次写对）" if r["rework"] == 0 else f"{r['rework']} 次"
            lines.append(f"| `{r['slug']}` | {r['rework']} | {detail} |")
    lines += ["", "### M3 需求周期"]
    lines.append("| slug | 起点 | 终点 | 周期 |")
    lines.append("|---|---|---|---|")
    for r in rows:
        if r["cycle_seconds"] is not None:
            secs = r["cycle_seconds"]
            if secs >= 86400:
                dur = f"{secs / 86400:.1f} 天"
            elif secs >= 3600:
                dur = f"{secs / 3600:.1f} 小时"
            elif secs >= 60:
                dur = f"{secs / 60:.1f} 分钟"
            else:
                dur = "<1 分钟"
            lines.append(
                f"| `{r['slug']}` | {_fmt_ts(r['start'])} | {_fmt_ts(r['end'])} | {dur} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="采集 SDLC 过程指标（确定性，无 AI 参与）")
    ap.add_argument("--format", choices=("json", "markdown"), default="json")
    args = ap.parse_args()

    # Windows 控制台默认 GBK，强制 UTF-8 输出，避免 emoji/中文打印崩溃（重定向不受影响）
    sys.stdout.reconfigure(encoding="utf-8")

    token = os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    api_mode = bool(token and repo)
    if not api_mode:
        print("::warning::无 GH_TOKEN/GITHUB_REPOSITORY，周期起点降级为 intent 首次提交（git 模式）", file=sys.stderr)

    rows = _evaluate(_load_intents(), _scan_merges(), api_mode, repo, token)

    archived = [r for r in rows if r["archived"]]
    completed = sum(1 for r in archived if r["completed"])
    total = len(archived)
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    if args.format == "markdown":
        print(_render_markdown("api" if api_mode else "git", rows, total, completed))
    else:
        print(_render_json(generated, "api" if api_mode else "git", rows, total, completed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
