#!/usr/bin/env python3
"""Qoder hook 公共工具：读取 IDE 注入的 stdin JSON。

IDE 以 `bash -c "python .qoder/hooks/xxx.py"` 方式执行 hook，
工作目录为项目根目录。stdin JSON 为事件上下文（session_id/cwd/
tool_name/tool_input 等）。

给 stdin 读取加 5 秒兜底：若 IDE 未关闭 stdin 写端，读取会永久
阻塞导致 hook 被 IDE 超时杀掉；超时后返回空 dict，hook 按放行
处理（不因解析失败误拦截）。
"""

import json
import sys
import threading


def read_input(timeout: float = 5.0) -> dict:
    """读取 hook 输入 JSON，解析失败或超时返回空 dict。"""
    result: list = []

    def _read() -> None:
        try:
            result.append(sys.stdin.read())
        except OSError:
            # 读失败按无输入处理，hook 放行（见模块注释）
            result.append("")

    thread = threading.Thread(target=_read, daemon=True)
    thread.start()
    thread.join(timeout)

    raw = result[0] if result else ""
    try:
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}
