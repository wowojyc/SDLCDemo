#!/bin/bash
# PreToolUse（matcher: Bash）—— 拦住危险命令
#
# 对应 03.5「构建时的硬防护」：确定性拦截，不依赖模型理解。
# exit 2 = 阻塞，stderr 注入对话让 Agent 知道被拦了以及原因。

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# 危险模式清单（按团队实际需要增删）
if echo "$command" | grep -Eq 'rm -rf|rm -fr|mkfs|dd if=|chmod -R 777|git push .*--force|git clean -fd|:(){'; then
  echo "已阻止危险命令：$command" >&2
  echo "如确需执行，请由人手动在终端运行，并在 PR 中说明理由。" >&2
  exit 2
fi

exit 0
