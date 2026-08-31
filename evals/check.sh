#!/bin/bash
# eval 判定脚本：对照 example.json 里的 checks 逐项判定，全过才算通过。
# 用法：./evals/check.sh <eval.json> <result.json>
#
# 这里给的是骨架，按你们实际的检查类型补齐即可。
# 核心思路：判定必须**确定性**（命令跑没跑过、文件含不含某串），不要靠 AI 自己说"我做好了"。

set -u
EVAL_FILE="$1"
RESULT_FILE="$2"

pass=0
fail=0

# 1) 拿 eval 里声明的测试命令，逐个跑一遍
for cmd in $(jq -r '.checks[] | select(.type=="command_succeeds") | .value' "$EVAL_FILE"); do
  if eval "$cmd" > /dev/null 2>&1; then
    pass=$((pass+1))
  else
    echo "FAIL: $cmd"
    fail=$((fail+1))
  fi
done

# 2) 文件包含检查
while IFS= read -r line; do
  path=$(echo "$line" | jq -r '.path')
  value=$(echo "$line" | jq -r '.value')
  if [ -f "$path" ] && grep -q "$value" "$path"; then
    pass=$((pass+1))
  else
    echo "FAIL: $path 中未找到 $value"
    fail=$((fail+1))
  fi
done < <(jq -c '.checks[] | select(.type=="file_contains")' "$EVAL_FILE")

echo "---- $(basename "$EVAL_FILE") ---- 通过 $pass / 失败 $fail"

if [ "$fail" -gt 0 ]; then
  exit 1
fi
exit 0
