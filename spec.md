# spec：待办标签 + 网页页面

> 依据 [intent/intent.md](intent/intent.md)（已收口，无遗留待确认问题）。本文只描述设计，不涉及代码实现。

## 一、功能

### 1. 领域层（src/todos.py，纯函数）

| 变更 | 说明 |
|---|---|
| `Todo.tags` 新字段 | `list[str]`，默认空列表，存储统一小写 |
| `add()` 支持 `tags` | 清洗规则：去首尾空白 → 丢弃空串 → 统一小写 → 去重；**最多 3 个**，超限抛 `ValueError`（沿用现有异常风格） |
| 新增 `filter_by_tag(todos, tag)` | 精确匹配（调用方传入的 tag 先转小写），返回结果按优先级排序 |
| 新增 `completed(todos)` | 只返回已完成的，按优先级排序（与现有 `pending` 对应） |
| 现有函数 | `add` / `complete` / `pending` / `sorted_by_priority` 语义不变 |

### 2. HTTP 层（src/api.py，薄层只做校验与转发）

| 接口 | 行为 |
|---|---|
| `GET /todos` | **现状不变**：未完成、按优先级；响应条目**新增 `tags` 字段**（additive，不破坏旧字段） |
| `GET /todos?tag=工作` | 在默认结果（未完成）上按标签过滤，大小写不敏感（`tag=工作` 与 `tag=Work` 等价） |
| `GET /todos?done=true` | 返回已完成列表（页面只读展示用），同样按优先级排序 |
| `POST /todos` | 请求体可选 `tags` 数组；校验失败返回 400，错误结构 `{"error": {"code": "invalid_tags", "message": ...}}` |
| `POST /todos/{id}/complete` | **新端点**（现有 HTTP 层没有完成操作）；标记完成，找不到 id 返回 404 统一错误结构；幂等（重复完成返回 200 同结果） |
| `GET /` | 返回 `web/index.html`（`text/html; charset=utf-8`）；仅精确匹配根路径，其余路径维持现有 404 |

约束落实：参数校验在边界（规则 1）、错误响应统一结构（规则 2）、不改已有字段语义（规则 3）。

### 3. 页面（web/index.html，新建）

原生 HTML/CSS/JS 单文件，无构建、无框架、零依赖：

- **未完成列表**：标题 + 标签徽标 + "完成"按钮
- **已完成列表**：只读，标记完成的条目移到这里
- **新增表单**：标题输入 + 标签输入（逗号分隔，最多 3 个）
- **标签筛选**：输入框筛选未完成列表
- 全部通过 `fetch` 调 `/todos` API，不直连存储；UTF-8 中文

## 二、数据流

```
页面加载 ──> GET /todos ─────────────> 渲染未完成列表
        └─> GET /todos?done=true ───> 渲染已完成列表
新增待办 ──> POST /todos {title, tags} ──> 201 ──> 重载列表
标签筛选 ──> GET /todos?tag=xxx ────────> 重渲染未完成列表
标记完成 ──> POST /todos/{id}/complete ──> 200 ──> 重载列表
```

## 三、系统变更清单

| 文件 | 变更类型 |
|---|---|
| `src/todos.py` | 改：`Todo.tags`、`add` 支持 tags；新增 `filter_by_tag`、`completed` |
| `src/api.py` | 改：GET 支持 `tag` / `done` 参数、POST 接受 `tags`；新增 `POST /{id}/complete`、`GET /` 静态托管 |
| `web/index.html` | 新建：页面 |
| `tests/test_todos.py` | 改：补 tags 清洗/上限/筛选/大小写用例 |
| `tests/test_api.py` | 新建：接口测试（当前 `api.py` 0% 覆盖，规则"每个新接口至少一个测试"） |

## 四、所需约束

- 零第三方依赖：领域层纯标准库，页面原生 HTML/CSS/JS，HTTP 仍用 `http.server`
- 不带 `tag` / `done` 参数时，GET /todos 结果与现状完全一致
- 排序：priority 降序，同优先级 created_at 升序（只排一个字段是错的）
- 标签：统一小写存储与匹配、单条最多 3 个、筛选为精确匹配
- 计数与金额用 `int`，不用 `float`
- 每个对外函数有 docstring + 对应单元测试

## 五、关注点（实现前需确认，未确认时按默认走）

1. **tag 筛选范围**：`GET /todos?tag=` 只在**未完成**列表内过滤（页面场景需要）；intent 原文"只返回带该标签的待办"未区分完成状态。默认按未完成内过滤。
2. **多标签筛选**：`tag` 参数只接受单个值；出现多个 `tag` 参数时取第一个，其余忽略（暂不支持 AND/OR 语义）。
3. **标签清洗**：空串/全空格丢弃；清洗后全为空视为未提供标签（不报错）；去重后超 3 个才报 `invalid_tags`。
4. **complete 幂等**：对已完成条目重复调用 `POST /{id}/complete` 返回 200 同结果，不报错。
5. **响应字段扩展**："返回结果与现在完全一致"按**筛选行为**理解；响应条目新增 `tags` 字段属 additive，不违反"不改已有字段语义"。
6. **页面错误提示**：无 JS 框架，表单/请求错误用行内文本提示（不放栈信息）。
7. **静态托管**：`GET /` 只服务根路径；页面内引用的资源（如有）也要由 api.py 托管，避免 404。

## 六、验收方式（Gate 3 用）

- `make test` 全绿：新增用例覆盖——tags 清洗（空白/去重/小写）、上限校验、按标签筛选（含大小写不敏感）、`completed`、complete 端点（含 404/幂等）、`GET /` 托管、`tag`/`done` 参数缺省行为
- `make lint` 零告警
- `make run` 后浏览器访问 `http://127.0.0.1:8000/`：四操作（新增带标签 / 筛选 / 标记完成 / 查看已完成）手动走通
