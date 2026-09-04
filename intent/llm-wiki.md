# 意图：仓库级 LLM Wiki——Karpathy 原版模式实例化（独立 wiki/ 目录 + AGENTS.md Schema）

## 意图 / 作者 / 状态 / 来源 / 类型
- 意图：把 Karpathy 原版 LLM Wiki 模式实例化到本仓库，建立跨需求的长青知识层——需求归档时把决策与教训"编译"进 wiki/，让每次新会话的 AI 都能继承历史知识，而不是每次从零发现
- 作者：AI（Qoder）｜状态：起草（Gate 1）｜来源：Issue #32
- 类型：规则/工具型（产出 wiki/ 目录 + Schema 规则文件 + 首批知识节点，非 src/ 代码）

## 问题
仓库的需求链路（Issue → intent → spec → plan）在 PR 合并后即归档终止：每条需求的**决策与教训沉睡在 archive/ 里**，无法跨会话复利。后果：

- 新会话的 AI 只能靠 `AGENTS.md` 里几条浅层规则防错，无法继承深度知识（"hooks 为何用 Python 零依赖""REVIEW 为何设计为不阻塞合并""产物链状态机为何不靠手改状态字段"）；
- archive 里已实证过的教训（如过程指标口径返工 2 次、GH006 数据分支经验）随会话消失，未来可能重蹈覆辙；
- 缺一层"长青知识层"：需求文档（Transient）回答"这次做什么"，没人回答"这个库一直怎么被 AI 正确地改"（Persistent）。

对照 Karpathy LLM Wiki 模式（2026-04，gist 442a6bf5）：不是 RAG（每次从原始文档重新检索、无积累），而是**持续编译**——LLM 读取新来源后把知识编译进结构化 wiki，wiki 成为所有后续查询的起点。本仓库已有 Raw 层（archive/ + git 历史）、已有 Schema 机制（AGENTS.md / .qoder/rules/），缺的正是 Wiki 层与"归档 → 编译"的触发约定。

## 设计决策（已确认，随 Gate 2 细化）
- **A. 采用 Karpathy 原版而非 Astra 工程化变体**：不加 TTL、强制 frontmatter、submodule、MCP server 等治理加装；结构、约定、工具均从简、随实践共演化（原版文档明确"有意保持抽象"）
- **B. Schema 以独立 `wiki/AGENTS.md` 承载**（用户拍板方案 B）：根 `AGENTS.md` 只加一行指路，保持"总纲一页内"约束
- **C. 独立 `wiki/` 目录**（用户拍板）：`AGENTS.md`（Schema）+ `index.md`（内容目录）+ `log.md`（时序日志）+ `pages/`（首批节点）
- **D. 首批节点从 archive 逆向编译**（≥2 页）：如"产物链状态机"concept 页（flow-tracking/audit_artifacts）+ "hooks 零依赖"decision 页（process-metrics 等），每页带来源溯源
- **E. 边界分工**：`intent/spec/plan` = 需求时态文档（归档即死）；`wiki/` = 跨需求长青知识（持续演化）；"需求归档动作 → 触发知识编译"写入 Schema

## 预期成果
- `wiki/AGENTS.md`：Schema——声明结构（index/log/pages 布局）、页面约定（溯源、矛盾标注）、Ingest/Query/Lint 三工作流，含"归档 → 编译"触发约定
- `wiki/index.md`：内容目录（每页一行摘要 + 链接，按类组织）
- `wiki/log.md`：时序日志（`## [YYYY-MM-DD] ingest/query/lint | 说明`，可 grep 解析）
- `wiki/pages/concepts/`、`wiki/pages/decisions/`：首批 ≥2 个节点从 archive 编译，带来源 Issue #xx / archive 链接
- 根 `AGENTS.md`：加一行 wiki 指路（保持一页内）
- 可选：README 目录结构节同步标注 `wiki/`

## 受影响的用户和系统
- AI（Qoder 等 agent）：新会话可先读 wiki/index.md 定位长青知识，减少重复踩坑
- 人类维护者：wiki 层人读、AI 写，评审走 PR（复用现有分支保护）
- 目录树：新增 `wiki/`（AGENTS.md / index.md / log.md / pages/），与 intent/spec/plan/archive 并列
- `AGENTS.md`：加一行指路（极小改动）
- 不影响：`src/`、`tests/`、`.qoder/hooks/`、`.github/workflows/`（本需求只加知识层，不改规则与 CI）

## 约束
- 零新增依赖：纯 Markdown 文件，无脚本、无构建——遵守 AGENTS.md
- Karpathy 原版克制原则：不加 Astra 工程化加装（TTL、强制 frontmatter、submodule、MCP server）
- 根 AGENTS.md 保持"一页内"（设计要点第 3 条），wiki 指路只加一行
- 页面溯源要求：每个 wiki 节点标注来源（Issue #xx 或 archive/ 文档链接），不写无来源结论
- commit message 必须引用 Issue #32；改动走 docs 分支 + PR（遵守仓库流程）
- 不修改 `intent/spec/plan` 归档文件内容（Raw 层不可变，只读不写）

## 待确认问题
1. wiki 日常维护（Lint 修页、Query 回写）的 commit 与"commit 必须引用 Issue"的调和：每次小维护都开 Issue 太重——是否约定"wiki 变更跟随最近一次需求 PR"？还是允许 wiki-only commit 复用本 Issue 编号（#32）？（倾向：随需求 PR 走，独立 wiki 维护开轻量 chore Issue）
2. 纯文档改动与 `verify-before-stop` hook 的交互：只改 wiki/ 文件的回合是否按"纯读"豁免，还是仍需跑 `make test`？（需读 hook 逻辑后定）
3. `pages/` 子目录是否先按 concepts/decisions 分，还是从单层开始随内容演化？（原版倾向后者，但首批内容已明确两类，倾向先分）
4. Schema 随实践共演化的更新路径：直接在 wiki/AGENTS.md 上改（走 PR），是否有必要像 .qoder/rules 那样"一页内"限制？（倾向：Schema 允许超一页，但控制信息密度）

---

> 七字段模板：意图/作者/状态/来源/类型 · 问题 · 预期成果 · 受影响的用户和系统 · 约束 · 待确认问题。
> 来源字段：原始需求先在 GitHub 开 Issue 登记，intent.md 是它的 MRD（市场需求文档），来源填 Issue 编号（如 #12）；无关联 Issue 填 —。
> 类型字段：实现型 / 规则工具型 / 调研梳理型（主型单选，人工填——脚本据此判定需求完成形态，见 spec/process-metrics.md §2）。
> 归档规则：需求完成（PR 合并）后，intent/spec/plan 三份文档一起移入各自 archive/，audit 只统计顶层活跃文档。
> 字段固定，但内容用大白话写——不是填表，是让 AI 能直接读懂。
