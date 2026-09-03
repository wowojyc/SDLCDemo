# Spec：SDLC 过程指标采集（PRD）

> 来源：Issue #29（intent/process-metrics.md v2，已批准）
> 状态：已批准（Gate 2）

## 1. 背景与范围

仓库已有产品指标闭环（metrics/ci_test_failure_rate.json + maintenance-scan），过程指标整层缺失。本需求补齐三项过程指标（intent 存活率 / spec 返工次数 / 需求周期）并引入 intent 类型字段。

**范围**：`scripts/collect_cycle_metrics.py`（新）+ `tests/test_collect_cycle_metrics.py`（新）+ intent 模板与存量回填 + README 表述。
**非范围**：不挂 CI（先手动）；不进 detect_drift（多指标化后置）；不改 audit_artifacts.py 判定逻辑。

## 2. intent 类型字段（七字段）

### 2.1 字段设计

头部小节从 `## 意图 / 作者 / 状态 / 来源` 扩展为 `## 意图 / 作者 / 状态 / 来源 / 类型`；作者行追加 `｜类型：<型>`。

枚举（单选主型）：
| 类型 | 典型产出 | 完成证据 |
|---|---|---|
| 实现型 | src/ 代码（或 scripts/ 脚本） | 含 `Closes #Issue` 的 merge commit |
| 规则工具型 | 规则/hook/CI/文档体系文件 | 同上 |
| 调研梳理型 | 结论（intent 内"结论"节或分析文档） | intent 已归档 且 结论节非空 |

> 主型单选；跨型需求（如本需求：产脚本 + 改模板）按主要产出选型。类型为人工填写项，脚本只读不推断（确定性铁律）。

### 2.2 改动点

| 文件 | 改动 |
|---|---|
| `README.md` L57、L108 | "六字段" → "七字段（意图/作者/状态/来源/类型）" |
| `intent/process-metrics.md` | 底部模板注释更新为七字段说明（自身即示范） |
| `intent/archive/ci-failure-rate-feed.md` | 头部回填 `｜类型：实现型` |
| `intent/archive/tags-webpage.md` | 头部回填 `｜类型：实现型` |
| `intent/archive/flow-tracking.md` | 头部回填 `｜类型：规则工具型` |

## 3. 指标口径（确定性定义）

### M1 intent 存活率

- 分母：全部已归档 intent（含早期来源 — 的）
- 分子（按类型分派完成证据）：
  - 实现型 / 规则工具型：存在含 `Closes #Issue` 的 merge commit（来源 — 的需求无 Issue：以归档动作为完成证据）
  - 调研梳理型：已归档 且 "## 结论" 节非空
- 输出：比率 + 明细（每个 intent 的判定与证据）
- **实证结果**（2026-09-03 首跑）：3 个归档需求全存活 → 1.0。flow-tracking（#4）无 merge commit（早期直推 main），按归档 rename 兜底判定存活——兜底机制生效，不再误判

### M2 spec 返工次数

- 定义：`plan/<slug>.md` 首次提交之后，`spec/<slug>.md` 的内容修改（`--diff-filter=M`，排除新增 A 与归档重命名 R）提交次数
- 实现：`git log --follow --diff-filter=M --format=%ct -- spec/<slug>.md`，计数时间戳 > plan 首次提交时间戳的条目
- 边界：无 plan 的需求 → 不适用（不计入）；spec/plan 同 commit（本仓库实证）→ 0
- 实证结果（2026-09-03 首跑）：ci-failure-rate-feed = **2 次真实返工**（演习中修 collect job 的两次 fix commit 同步修订了 spec 内容，+20/-5、+2/-1）——指标捕获到真实返工，机制有效；此前"存量全 0"的预期不成立（AI 也返工，只是返工发生在修 bug 时）

### M3 需求周期

- 起点：
  - 有 Issue：Issue `created_at`（GitHub API；`GH_TOKEN` + repo 可得时启用，模式 `api`）
  - 无 token 或无 Issue：intent 首次提交时间（`--diff-filter=A`，模式 `git`，输出标注语义略窄）
- 终点（**纯 git，已验证**：merge commit 的 `%B` 含 PR 标题与 `Closes #xx`）：
  - 取所有含 `Closes #Issue` 的 merge commit 时间戳最大值（多 PR 需求 = 收尾 merge）
  - 兜底：早期直推 main 的需求无 merge commit（实证：早期历史无 merge 提交）→ 归档 rename 时间
- 周期 = 终点 − 起点（秒）；任一端缺失 → `null`
- 实证结果（2026-09-03 首跑，git 降级模式）：ci-failure-rate-feed = 0.0 天（intent 提交 07:38 → merge 08:21）；tags-webpage = 1.8 天（intent 08-31 → 归档 09-02）；flow-tracking = 0.1 天——git 模式只测"文档链推进到收尾"时延。**API 模式**（Issue created_at 起点，同日实证）：#18 = 1.0 小时（Issue 07:20 创建 → merge 08:21）、#4 = 2.8 小时——起点精度提升（Issue 先开、intent 后写，方向正确）；本仓库历史需求均在 1~2 天内完成（演习节奏），区分度待真实团队数据积累

## 4. 采集脚本规格（collect_cycle_metrics.py）

风格对齐 `collect_ci_failure_rate.py`：模块 docstring（背景/用法/输出）→ 常量 → 纯函数 → `_` I/O → main 退出码。

### 4.1 纯函数（全部可单测）

| 函数 | 签名 | 语义 |
|---|---|---|
| `survival_rate` | `(completed: int, total: int) -> float` | total=0 → 0.0；完成/总数 |
| `rework_count` | `(spec_m_ts: list[int], plan_first_ts: int) -> int` | 统计 > plan_first_ts 的条目 |
| `cycle_seconds` | `(start: int \| None, end: int \| None) -> int \| None` | 任一端缺失 → None；负值按数据异常处理（返回 None 或由调用方告警） |
| `closes_from_body` | `(body: str) -> set[int]` | 从 merge %B 提取 `Closes #n`（正则，大小写不敏感） |
| `read_type` | `(header_lines: str) -> str \| None` | 从 intent 头部取 `类型：` 值；缺失 → None |

### 4.2 I/O 层（`_` 前缀）

- `_git_log_ts(path, diff_filter, follow=True) -> list[int]`：subprocess 调 `git log`，utf-8 解码
- `_scan_merges() -> dict[int, int]`：`git log --merges --format=%ct%x1f%B` 全历史扫描 → {issue: max_merge_ts}（`%x1f` 分隔防换行污染）
- `_fetch_issue_created(owner, repo, issue_no, token) -> int`：urllib 拉 `/repos/{o}/{r}/issues/{n}`（与 collect_ci_failure_rate 同风格）
- `_load_intents(root) -> list[dict]`：扫描 `intent/archive/*.md` + `intent/*.md`，读 slug/来源 Issue/类型/结论节
- `_archive_ts(root, slug) -> int \| None`：归档 rename commit 时间

### 4.3 CLI 与输出

```
python scripts/collect_cycle_metrics.py [--format json|markdown]
环境变量：GH_TOKEN（可选）、GITHUB_REPOSITORY（可选，owner/repo）
```
- JSON（stdout）：`{"generated_at", "mode": "api"|"git", "survival": {...}, "rework": {...}, "cycle": {...}, "requirements": [...]}`
- Markdown：人读进度表（存活明细 / 返工表 / 周期表）
- 退出码：0（数据异常字段告警 stderr，不阻断——采集非门禁）

## 5. 验收方式

1. `make test` 全绿（新增单测 ~12 用例：空集合、None、同 commit、负周期、正则提取、类型缺失等）
2. `make lint` 零告警
3. 真实数据实证（手动跑，非 CI）：`python scripts/collect_cycle_metrics.py --format markdown`，输出与 git log 手算抽查一致：
   - ci-failure-rate-feed：存活 ✓、返工 0、周期 > 0（#18 → #22）
   - flow-tracking：存活 ✓（规则工具型判定生效）
4. README/intent 模板表述一致（无残留"六字段"）

## 6. 数据现实与风险（已实证）

| 风险 | 缓解 |
|---|---|
| 早期需求直推 main 无 merge commit（< #18 前） | 终点兜底 = 归档时间；验收以 #18 后需求为主 |
| 文档批量提交 → git 时间戳粒度粗 | 周期起点用 Issue created_at（API 模式）；git 模式输出标注 |
| merge %B 中文/多行解析 | `%x1f` 分隔 + 正则 `Closes #\d+`（已验证 6 条历史全命中） |
| Windows git 输出编码 | subprocess 显式 utf-8 解码（git for windows 默认 utf-8 管道输出） |
| 类型字段漂移（新 intent 忘填） | 脚本对缺失类型告警（stderr）不静默；模板注释示范 |
