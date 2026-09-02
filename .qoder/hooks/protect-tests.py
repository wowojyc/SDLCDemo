"""PreToolUse(Write|Edit) —— 测试文件的"意图闸门"。

这是"反馈闭环"的保险丝：防止 Agent 为了让测试变绿而去改测试
（放宽断言 / 删用例 / 跳过失败用例）。
保险丝判断不了意图，只能按粒度拦截：
- 新建测试文件（文件不存在）→ 放行：TDD 测试先行的正常动作
- 修改已有测试文件 → 转人工：新增覆盖（合理跟进）还是放宽断言（作弊）由人判断

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
    if not TEST_PATTERNS.search(file_path):
        return 0
    if not os.path.exists(file_path):
        # 新建测试文件：TDD 测试先行，放行（不打扰，静默通过）
        return 0
    print(f"修改已有测试文件需人工确认：{file_path}", file=sys.stderr)
    print("TDD 新增覆盖（补用例）是正常动作；放宽断言（改/删断言迁就实现）是作弊。", file=sys.stderr)
    print("请由人判断后手动修改，并在 PR 里说明理由。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
