"""Stop —— Agent 想结束回合时，检查本次会话是否跑过测试。

这是 03.7「反馈闭环」的硬性兜底：
  AGENTS.md 里的验证块是"软指令"（靠模型自觉），
  这个 hook 是"硬拦截"（确定性，不看模型心情）。

判定依据：
  · .git/sdlc-changed   —— 会话内是否 Write/Edit 过文件（由 auto-lint.py 写）
  · .git/sdlc-test-run  —— make test 成功后写入的标记
只拦截「改过文件但没跑测试」的回合；纯讨论回合（只读）直接放行。
IDE 不支持 SessionStart 事件，无法在会话开始清标记；因此改为在
Stop 检查通过后主动删除标记——等效替代清标记职责，保证每个会话
都从"未测试"状态开始。

exit 2 = 阻止 Agent 停止，stderr 作为消息注入对话让它继续工作。
"""

import os
import sys

from hook_common import read_input


def _try_remove(path: str) -> None:
    """尽力删除标记文件，失败静默（标记本就可选）。"""
    try:
        os.remove(path)
    except OSError:
        pass


def main() -> int:
    """只读回合放行；改过文件的回合必须通过测试才能停止。"""
    data = read_input()
    cwd = data.get("cwd") or os.getcwd()
    git_dir = os.path.join(cwd, ".git")

    # 非 git 仓库（无 .git 目录）→ 无标记机制，直接放行
    if not os.path.isdir(git_dir):
        return 0

    changed_marker = os.path.join(git_dir, "sdlc-changed")
    test_marker = os.path.join(git_dir, "sdlc-test-run")

    # 会话只读（没 Write/Edit 过任何文件）→ 直接放行，
    # 但清理可能残留的测试标记（只读会话里手动跑过 make test 的场景）
    if not os.path.exists(changed_marker):
        _try_remove(test_marker)
        return 0

    if not os.path.exists(test_marker):
        print("检测到代码修改但未运行测试，请先执行 make test 并确保测试通过后再停止会话。", file=sys.stderr)
        print("并把命令的原始输出粘贴到你的总结里（不要只说'测试已通过'）。", file=sys.stderr)
        return 2

    # 通过后删除两个标记：等效替代 SessionStart 的清标记职责，
    # 让下一个会话从"未测试"状态开始
    _try_remove(test_marker)
    _try_remove(changed_marker)
    return 0


if __name__ == "__main__":
    sys.exit(main())
