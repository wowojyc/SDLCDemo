# Todo API

> 这是 Qoder 的项目规则文件，每次会话自动读取。保持在一页内，细节放 `.qoder/rules/`。

## Commands
- Test: `make test`（健康输出示例：`3 passed in 0.42s`）
- Lint: `make lint`（健康输出示例：`All checks passed!`）
- Run: `make run`

## Conventions
- Python 3.11+，标准库优先，**不随意新增依赖**
- 计数与金额用 `int`，不用 `float`
- 每个对外函数都要有 docstring 和对应单元测试
- 错误用异常抛出，不返回 `None` 伪装成功
- commit message 必须引用 Issue（`#数字`）：本地 commit-msg 与云端 CI 双重强制

## Architecture
- `src/todos.py`：领域逻辑（纯函数，不碰 I/O）
- `src/api.py`：HTTP 层（薄，只做参数校验与转发）
- `tests/`：pytest，与 `src/` 目录结构一一对应
- `src/gen/`：生成目录，**禁止手改**

## Things AI gets wrong
- **不要为了让测试通过而修改 `tests/` 下的文件**——测试失败要改 `src/`
- 不要擅自升级依赖版本
- 排序要**先按 priority 降序、再按 created_at 升序**，只排一个字段是错的
- 不要用 `float` 表示优先级

## Verifying your work
- Test: `make test`（必须全绿；绝不跳过或删除失败的测试）
- Lint: `make lint`（零告警）

Run both before reporting any task complete, and paste the output.
If a test fails, fix the code, not the test.
