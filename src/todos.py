"""待办清单领域逻辑。

纯函数，不做任何 I/O，方便单测覆盖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable


@dataclass
class Todo:
    """一条待办。priority 越大越优先（int，不用 float）。"""

    id: int
    title: str
    priority: int = 0
    done: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )


def add(todos: list[Todo], title: str, priority: int = 0) -> Todo:
    """新增一条待办，返回新条目。标题为空则抛 ValueError。"""
    if not title or not title.strip():
        raise ValueError("title 不能为空")
    new_id = max((t.id for t in todos), default=0) + 1
    todo = Todo(id=new_id, title=title.strip(), priority=int(priority))
    todos.append(todo)
    return todo


def complete(todos: list[Todo], todo_id: int) -> Todo:
    """把某条标记为完成并返回。找不到就抛 KeyError（不返回 None 伪装成功）。"""
    for t in todos:
        if t.id == todo_id:
            t.done = True
            return t
    raise KeyError(f"找不到 id={todo_id} 的待办")


def sorted_by_priority(todos: Iterable[Todo]) -> list[Todo]:
    """按 priority 降序；同优先级按 created_at 升序（先来的在前）。"""
    return sorted(todos, key=lambda t: (-t.priority, t.created_at))


def pending(todos: Iterable[Todo]) -> list[Todo]:
    """只返回未完成的，按优先级排序。"""
    return sorted_by_priority([t for t in todos if not t.done])
