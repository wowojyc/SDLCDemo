"""PreToolUse(Write|Edit) —— 拦截修改测试文件。

这是"反馈闭环"的保险丝：防止 Agent 为了让测试变绿而去改测试。
没有这一条，03.7 的闭环会被"作弊"架空。

exit 2 = 阻塞工具执行，stderr 内容注入对话反馈给 Agent。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import read_input

# 测试文件路径模式（兼容 / 与 \ 分隔符）
TEST_PATTERNS = re.compile(
    r"(^|[/\\])tests[/\\]"
    r"|test_.*\.py$"
    r"|_test\.py$"
    r"|\.test\.js$"
    r"|\.spec\.ts$"
    r"|(^|[/\\])conftest\.py$"
)


def main() -> int:
    """读取目标文件路径并判断是否为测试文件。"""
    data = read_input()
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if TEST_PATTERNS.search(file_path):
        print(f"不允许修改测试文件：{file_path}", file=sys.stderr)
        print("测试失败时应该改 src/ 下的实现代码。", file=sys.stderr)
        print("如确需调整测试，请由人手动修改，并在 PR 里说明理由。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
