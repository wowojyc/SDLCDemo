#!/usr/bin/env python3
"""PreToolUse(Bash) —— 拦截危险命令。

对应 03.5「构建时的硬防护」：确定性拦截，不依赖模型理解。
exit 2 = 阻塞，stderr 注入对话让 Agent 知道被拦了以及原因。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import read_input

# 危险模式清单（按团队实际需要增删）
DANGEROUS = re.compile(
    r"rm -rf|rm -fr|mkfs|dd if=|chmod -R 777|git push .*--force|git clean -fd|:\(\)\{"
)


def main() -> int:
    """读取命令并判断是否命中危险模式。"""
    data = read_input()
    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if DANGEROUS.search(command):
        print(f"已阻止危险命令：{command}", file=sys.stderr)
        print("如确需执行，请由人手动在终端运行，并在 PR 中说明理由。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
