#!/usr/bin/env python3
"""Stop —— Agent 想结束回合时，检查本次会话是否跑过测试。

这是 03.7「反馈闭环」的硬性兜底：
  AGENTS.md 里的验证块是"软指令"（靠模型自觉），
  这个 hook 是"硬拦截"（确定性，不看模型心情）。

判定依据：Makefile 的 test 目标在成功后会写入 .git/sdlc-test-run 标记。
IDE 不支持 SessionStart 事件，无法在会话开始清标记；因此改为在
Stop 检查通过后主动删除标记——等效替代清标记职责，保证每个会话
都从"未测试"状态开始，不跑 make test 就无法正常停止。

exit 2 = 阻止 Agent 停止，stderr 作为消息注入对话让它继续工作。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import read_input


def main() -> int:
    """检查测试标记：不存在则阻止停止，存在则通过并删除标记。"""
    data = read_input()
    cwd = data.get("cwd") or os.getcwd()
    marker = os.path.join(cwd, ".git", "sdlc-test-run")

    if not os.path.exists(marker):
        print("本次会话还没有运行过测试。", file=sys.stderr)
        print("请先执行 make test 并确保全绿，再报告任务完成；", file=sys.stderr)
        print("并把命令的原始输出粘贴到你的总结里（不要只说'测试已通过'）。", file=sys.stderr)
        return 2

    # 通过后删除标记：等效替代 SessionStart 的清标记职责，
    # 让下一个会话从"未测试"状态开始
    try:
        os.remove(marker)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
