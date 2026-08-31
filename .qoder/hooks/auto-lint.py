"""PostToolUse(Write|Edit) —— 写完 .py 自动跑 lint。

对应 03.5：「改完即格式化/lint，别让代码风格漂移累积」。
PostToolUse 不阻塞流程（exit 0），只把问题反馈给 Agent 让它自己修。
ruff 未安装时静默跳过（环境里没有就不打扰）。
"""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import read_input


def main() -> int:
    """对 .py 文件运行 ruff check（仅检查，不 --fix）。"""
    data = read_input()
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or None
    file_path = tool_input.get("file_path") or ""

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
