"""产物链状态推导 —— 把"需求链路"变成可审计的确定性事实。

链路（每环一个提交的产物）：
    Issue（原始需求）→ intent/intent.md（MRD）→ spec.md（PRD）→ plan.md（技术方案）
    → src/（代码）→ tests/（测试）

关键设计（与 detect_drift.py 同一铁律）：
  **检测保持确定性** —— 不用 AI 判断链路状态。
  文件存在性与顺序全部脚本算，结果可复现、可审计、有单测。

判读规则：
  · 状态 = 最后一个存在的环节（下游产物存在即隐含上游已通过，无需手改状态字段）
  · 断链 = 下游存在而某一上游缺失（违反流程顺序，需人工介入）

用法:
    # JSON 输出（机器可读，退出码供 CI 判断）
    python scripts/audit_artifacts.py

    # 人读的进度表
    python scripts/audit_artifacts.py --format markdown

输出（stdout，JSON）:
    {"stage": "tests", "stage_label": "已测试（测试已就位）", "ok": true,
     "artifacts": [{"name": "intent", "path": "intent/intent.md", "label": "...",
                    "exists": true}, ...],
     "broken_links": []}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 产物链定义：顺序即流程，后一环存在即隐含前一环已通过
ARTIFACTS: list[dict] = [
    {"name": "intent", "path": "intent/intent.md", "kind": "file", "label": "01 规划 · MRD"},
    {"name": "spec", "path": "spec.md", "kind": "file", "label": "02 设计 · PRD"},
    {"name": "plan", "path": "plan.md", "kind": "file", "label": "03 计划 · 技术方案"},
    {"name": "src", "path": "src", "kind": "src", "label": "04 构建 · 代码"},
    {"name": "tests", "path": "tests", "kind": "tests", "label": "05 测试 · 用例"},
]

STAGE_LABELS: dict[str, str] = {
    "none": "无需求（链路未启动）",
    "intent": "需求已登记（MRD 已提交）",
    "spec": "设计中（PRD 已产出）",
    "plan": "已计划（技术方案已产出）",
    "src": "已实现（代码已提交）",
    "tests": "已测试（测试已就位）",
}


def artifact_exists(root: Path, item: dict) -> bool:
    """按产物类型判定是否存在：文件直查；src 需有 .py；tests 需有 test_*.py。"""
    p = root / item["path"]
    if item["kind"] == "src":
        return p.is_dir() and any(p.glob("*.py"))
    if item["kind"] == "tests":
        return p.is_dir() and any(p.glob("test_*.py"))
    return p.is_file()


def audit(root: Path) -> dict:
    """推导产物链状态：各产物存在性、当前阶段、断链清单。"""
    artifacts = [
        {
            "name": item["name"],
            "path": item["path"],
            "label": item["label"],
            "exists": artifact_exists(root, item),
        }
        for item in ARTIFACTS
    ]
    stage = "none"
    for a in artifacts:
        if a["exists"]:
            stage = a["name"]
    broken: list[str] = []
    for i, a in enumerate(artifacts):
        if not a["exists"]:
            continue
        missing = [p["name"] for p in artifacts[:i] if not p["exists"]]
        if missing:
            broken.append(
                f"{a['name']}（{a['path']}）已存在，但上游缺失：{', '.join(missing)}"
            )
    return {
        "stage": stage,
        "stage_label": STAGE_LABELS.get(stage, stage),
        "ok": not broken,
        "artifacts": artifacts,
        "broken_links": broken,
    }


def to_markdown(result: dict) -> str:
    """把审计结果渲染成人读的进度表。"""
    lines = ["## 需求链路进度", "", "| 阶段 | 产物 | 状态 |", "|---|---|---|"]
    for a in result["artifacts"]:
        mark = "✅" if a["exists"] else "⬜"
        lines.append(f"| {a['label']} | `{a['path']}` | {mark} |")
    lines += ["", f"**当前阶段**：{result['stage_label']}"]
    if result["broken_links"]:
        lines += ["", "**⚠️ 断链告警**（下游存在而上游缺失，违反流程顺序）："]
        lines += [f"- {b}" for b in result["broken_links"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="推导需求链路状态（确定性，无 AI 参与）")
    ap.add_argument("--root", type=Path, default=Path("."), help="仓库根目录（默认当前目录）")
    ap.add_argument("--format", choices=("json", "markdown"), default="json")
    args = ap.parse_args()

    # Windows 控制台默认 GBK，强制 UTF-8 输出，避免 emoji/中文打印崩溃（重定向不受影响）
    sys.stdout.reconfigure(encoding="utf-8")

    result = audit(args.root)
    if args.format == "markdown":
        print(to_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 退出码供 CI 使用：断链 = 1，其余 0
    return 1 if result["broken_links"] else 0


if __name__ == "__main__":
    sys.exit(main())
