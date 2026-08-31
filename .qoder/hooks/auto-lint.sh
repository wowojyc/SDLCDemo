#!/bin/bash
# PostToolUse（matcher: Write|Edit）—— 写完文件自动跑 lint
#
# 对应 03.5：「改完即格式化/lint，别让代码风格漂移累积」。
# PostToolUse 不阻塞流程（exit 0），只把问题反馈给 Agent 让它自己修。

input=$(cat)
cwd=$(echo "$input" | jq -r '.cwd // ""')
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null

file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

case "$file_path" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      # 只做检查，不 --fix：让 Agent 自己决定怎么改，避免静默改动
      output=$(ruff check "$file_path" 2>&1)
      if [ $? -ne 0 ]; then
        echo "lint 发现问题，请修复："
        echo "$output" | head -20
      fi
    fi
    ;;
esac

exit 0
