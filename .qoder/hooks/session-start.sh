#!/bin/bash
# SessionStart —— 新会话开始时，清除"本次会话已跑过测试"的标记
#
# 作用：配合 verify-before-stop.sh，形成闭环
#   会话开始（清标记）→ Agent 干活 → 跑 make test（写标记）→ Stop 校验标记
# 这样每个会话都必须真正跑一次测试，才能报告"做完了"。
#
# 输入：stdin JSON，通用字段 session_id / cwd / hook_event_name
# 输出：exit 0 通过（stdout JSON 可选，用于注入上下文）

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd // ""')
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null

rm -f .git/sdlc-test-run 2>/dev/null

exit 0
