#!/bin/bash
# PreToolUse（matcher: Write|Edit）—— 拦住 Agent 修改测试文件
#
# 这是"反馈闭环"的保险丝：防止 Agent 为了让测试变绿而去改测试。
# 没有这一条，03.7 的闭环会被"作弊"架空。
#
# exit 2 = 阻塞工具执行，stderr 内容注入对话反馈给 Agent

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // ""')

case "$file_path" in
  */tests/*|*test_*.py|*_test.py|*.test.js|*.spec.ts|*/conftest.py)
    echo "不允许修改测试文件：$file_path" >&2
    echo "测试失败时应该改 src/ 下的实现代码。" >&2
    echo "如确需调整测试，请由人手动修改，并在 PR 里说明理由。" >&2
    exit 2
    ;;
esac

exit 0
