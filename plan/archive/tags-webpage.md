# plan：待办标签 + 网页页面

> 依据 [intent/intent.md](intent/intent.md) 与 [spec.md](spec.md)。本文只给方案，不修改任何代码。

## 一、要改动的文件

| 文件 | 动作 | 内容 |
|---|---|---|
| `src/todos.py` | 改 | `Todo.tags` 字段；`add()` 支持 tags（清洗→小写→去重→上限 3）；新增 `filter_by_tag()`、`completed()` |
| `src/api.py` | 改 | GET 支持 `tag` / `done` 参数；POST 接受 `tags`；新增 `POST /{id}/complete`、`GET /` 静态托管 |
| `web/index.html` | 新建 | 单页：未完成列表 / 已完成列表 / 新增表单 / 标签筛选，fetch 调 API |
| `tests/test_todos.py` | 改 | 补 tags 领域用例 |
| `tests/test_api.py` | 新建 | 接口用例（当前 api.py 0% 覆盖） |

## 二、工作顺序（依赖驱动，每步跑 `make test`）

1. **领域层** `src/todos.py`：先加 `Todo.tags` 与 `add` 的 tags 清洗/校验，再补 `filter_by_tag`、`completed`（纯函数，无依赖，最先做）
2. **领域测试** `tests/test_todos.py`：补全部领域用例 → `make test` 全绿再往下
3. **HTTP 层** `src/api.py`：GET 参数 → POST tags → complete 端点 → `GET /` 静态托管（依赖 1）
4. **接口测试** `tests/test_api.py`：补接口用例 → `make test` 全绿
5. **页面** `web/index.html`：四区块 + fetch 交互（依赖 3 可用）
6. **总验证**：`make test` + `make lint` + `make run` 手动走四操作

## 三、证明方式（每个能力对应什么测试）

**领域层（test_todos.py 新增用例）**
- `add` 带 tags → 存入小写、去空白、去重
- `add` 清洗后 tags 超 3 个 → `ValueError`
- `add` 全空/无 tags → 与现状一致（tags 为空列表）
- `filter_by_tag` → 精确匹配、大小写不敏感、结果按优先级排序
- `completed` → 只含 done 条目、按优先级排序
- 现有 5 个用例不回归

**接口层（test_api.py 新增用例）**
- `GET /todos` 不带参数 → 与旧行为一致（未完成 + 按优先级），条目含新增 `tags` 字段
- `GET /todos?tag=工作` → 过滤生效且大小写不敏感
- `GET /todos?done=true` → 只返回已完成
- `POST /todos` 带 tags → 201；不带 → 与现状一致
- `POST /todos` 超 3 标签 → 400 `invalid_tags`（统一错误结构）
- `POST /todos/{id}/complete` → 200；不存在 id → 404；重复完成 → 200 幂等
- `GET /` → 200 `text/html` 且含页面内容；`GET /unknown` → 404

## 四、风险与对策

| 风险 | 对策 |
|---|---|
| api.py 测试需要给 `BaseHTTPRequestHandler` 造环境，写法不熟易卡 | 用 `BytesIO` 模拟 `rfile/wfile` 直接实例化 `Handler`，不真起端口；如太绕则用 `HTTPServer` + 真实请求（测试内起临时服务） |
| Windows 路径分隔符导致静态文件读取失败 | `pathlib.Path` 定位 `web/index.html`，不用手拼路径 |
| 中文查询参数（`tag=工作`）编解码 | 服务端用 `urllib.parse.urlparse().query` + `parse_qs` 解码（默认 UTF-8） |
| 标签上限校验顺序：先清洗后校验 | 清洗（去空白/小写/去重）完成后再数个数，避免 "工作, 工作" 这类输入误报 |
| 页面 fetch 相对路径 | 页面与 API 同源（同一 http.server），用相对路径 `/todos`，无跨域问题 |

## 五、验收（Gate 3 完成标准）

- [ ] `make test` 全绿（新旧用例一起），原始输出贴总结
- [ ] `make lint` 零告警
- [ ] `make run` 后浏览器访问 `http://127.0.0.1:8000/`：新增（带标签）→ 筛选 → 标记完成 → 已完成列表出现，四操作走通
