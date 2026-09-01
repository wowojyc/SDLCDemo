"""PostToolUse(Write|Edit) —— 写完文件自动 lint，并记录"会话改动"标记。

对应 03.5：「改完即格式化/lint，别让代码风格漂移累积」。
PostToolUse 不阻塞流程（exit 0），只把问题反馈给 Agent 让它自己修。
ruff 未安装时静默跳过（环境里没有就不打扰）。

兼任"会话脏标记"：任何 Write/Edit 都写 .git/sdlc-changed，
供 Stop hook 区分「改过代码的回合」（必须跑测试）与「纯讨论回合」（放行）。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import read_input


def main() -> int:
    """记录会话改动标记；对 .py 文件运行 ruff check（仅检查，不 --fix）。"""
    data = read_input()
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or None
    file_path = tool_input.get("file_path") or ""

    # 先记"会话改过文件"（对任何文件类型都记，不限于 .py）
    if cwd and file_path:
        marker = Path(cwd) / ".git" / "sdlc-changed"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()

    if not file_path.endswith(".py") or shutil.which("ruff") is None:
        return 0

    try:
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0

    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        print("lint 发现问题，请修复：", file=sys.stderr)
        print("\n".join(output.splitlines()[:20]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
