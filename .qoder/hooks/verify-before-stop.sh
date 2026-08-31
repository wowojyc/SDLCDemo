#!/bin/bash
# Stop —— Agent 想结束回合时，检查本次会话是否跑过测试
#
# 这是 03.7「反馈闭环」的硬性兜底：
#   AGENTS.md 里的验证块是"软指令"（靠模型自觉），
#   这个 hook 是"硬拦截"（确定性，不看模型心情）。
#
# 判定依据：Makefile 的 test 目标在成功后会写入 .git/sdlc-test-run 标记，
#           SessionStart hook 在会话开始时清除它。
#
# exit 2 = 阻止 Agent 停止，stderr 作为消息注入对话让它继续工作

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd // ""')
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null

if [ ! -f .git/sdlc-test-run ]; then
  echo "本次会话还没有运行过测试。" >&2
  echo "请先执行 make test 并确保全绿，再报告任务完成；" >&2
  echo "并把命令的原始输出粘贴到你的总结里（不要只说'测试已通过'）。" >&2
  exit 2
fi

exit 0
