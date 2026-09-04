# Spec：仓库级 LLM Wiki——Karpathy 原版模式实例化（PRD）

> 来源：Issue #32（intent/llm-wiki.md，已批准）
> 状态：草案（Gate 2）

## 1. 背景与范围

仓库需求链路（Issue → intent → spec → plan → archive）归档即终止，决策与教训沉睡在 archive/，无法跨会话复利。本需求按 Karpathy 原版 LLM Wiki 模式建立长青知识层：新增 `wiki/` 目录（Schema + index + log + pages），需求归档时把知识"编译"进来。

**范围**：`wiki/` 目录全新建（AGENTS.md / index.md / log.md / pages/ 首批节点）+ 根 `AGENTS.md` 加一行指路。
**非范围**：不改 hooks（Q2 拍板结论）；不改 CI/workflows；不改 `.qoder/rules/`；不动 archive 内容（Raw 层只读）；不加 Astra 工程化加装（TTL/frontmatter/submodule/MCP）；不建 scripts/lint 工具（首批手工 Lint）。

## 2. 待确认问题拍板（intent 遗留 4 问）

| # | 问题 | 拍板结论 | 依据 |
|---|---|---|---|
| Q1 | wiki 维护 commit 与"必须引用 Issue"的调和 | **wiki 变更永不独立提交**：① 随需求 PR 提交（归档动作与编译同 PR）；② 纯 wiki 维护（Lint 修页、Query 回写）开轻量 chore Issue 走独立分支（仓库已有先例：#29 收尾 chore/archive-29 → PR #31） | commit-msg hook 强制 `#数字`，本地+CI 双保险（AGENTS.md） |
| Q2 | 纯文档改动与 verify-before-stop 的交互 | **不改 hook，wiki 维护回合同样须跑 `make test`**：auto-lint 对任何 Write/Edit 写脏标记（不区分文件类型），Stop hook 只查标记存在性——纯文档回合也会被拦，保持"改了文件必须验证"兜底不开口子 | `.qoder/hooks/auto-lint.py` L26-34、`verify-before-stop.py` L37-46 |
| Q3 | pages/ 目录是否先分类 | **先分两层**：`pages/concepts/`（定义，永远为真）+ `pages/decisions/`（历史决策）。首批内容已明确两类，先分不赌未来；出现实体类页面时再演化 | intent 设计决策 D；原版"结构随实践演化"允许先落地已知形态 |
| Q4 | Schema 篇幅限制 | **wiki/AGENTS.md 不强制一页内**（区别于根 AGENTS.md）：它是"需要时读"非常驻注入，允许超一页但控制信息密度；根 AGENTS.md 只加一行指路保持一页 | AGENTS.md L3"保持在一页内"约束针对常驻总纲 |

## 3. wiki 目录结构规范

```
wiki/
├─ AGENTS.md            # Schema：wiki 结构 / 页面约定 / Ingest-Query-Lint 工作流
├─ index.md             # 内容目录：每页一行摘要 + 链接（concepts/decisions 分组）
├─ log.md               # 时序日志：## [YYYY-MM-DD] ingest/query/lint | 说明
└─ pages/
   ├─ concepts/         # 定义页（永远为真）：产物链状态机、文档时态边界…
   └─ decisions/        # 决策页（ADR）：hooks 零依赖、REVIEW 不阻塞…
```

### 3.1 各文件职责

| 文件 | 职责 | 写入者 |
|---|---|---|
| `wiki/AGENTS.md` | Schema：声明结构/约定/三工作流；"归档 → 编译"触发约定；供 AI 维护 wiki 时读取 | 人机共演化（AI 起草、人审 PR） |
| `wiki/index.md` | 每页一行摘要 + 链接，按类组织；LLM 查询先读这里 | AI（每次 Ingest 更新） |
| `wiki/log.md` | 追加式时序日志，`## [YYYY-MM-DD] ingest | 说明` 格式（可 grep 解析） | AI（每次操作追加） |
| `wiki/pages/concepts/*.md` | 定义类知识页（本仓库机制/边界，永远为真） | AI（人审） |
| `wiki/pages/decisions/*.md` | 决策类知识页（ADR：当时为什么这么选，含被拒方案） | AI（人审） |

### 3.2 页面约定（写入 Schema）

1. 每页头部元信息行：`> 类型：concept/decision ｜ 来源：Issue #xx / archive 链接 ｜ 更新：YYYY-MM-DD`（溯源要求，不写无来源结论）
2. 提及相关页面用相对链接互链（`[产物链状态机](../concepts/xxx.md)`）
3. 与仓库现状冲突时以代码和 AGENTS.md 为准，更新页面并标注日期
4. 页面语言：中文，大白话，AI 能直接读懂（对齐 intent 模板文风）

## 4. Schema（wiki/AGENTS.md）内容大纲

| 小节 | 内容 |
|---|---|
| **角色** | wiki = 长青知识层：intent/spec/plan 回答"这次做什么"（归档即死），wiki 回答"这个库一直怎么被 AI 正确地改"（持续演化） |
| **结构** | §3.1 文件树 + 职责表 |
| **页面约定** | §3.2 四条 |
| **Ingest 工作流** | 触发 = 需求归档动作（PR 含 archive/ 移动时）：读归档文档 → 提取决策/教训 → 新建或更新 pages/ 节点（可能触 2-4 页）→ 更新 index.md → 追加 log.md → 随该 PR 提交 |
| **Query 工作流** | 被问"为什么/怎么设计/踩过什么坑"时：先读 index.md 定位 → 读相关页 → 回答带引用 → 有价值的综合经用户确认回写为新页 |
| **Lint 工作流** | 触发 = 每次 Ingest 时顺带 + 定期（如每月）：查矛盾/过时声明/孤立页/缺页/断链 → 清单随 chore Issue 修复 |
| **边界** | 不重复 AGENTS.md（常驻总纲）与 .qoder/rules/（操作约束）；不改 archive（Raw 只读）；wiki 维护遵守全部既有规则（commit 引用 Issue、make test 验证） |

## 5. 首批节点清单（Ingest 演示 = 本需求自身）

| 页面 | 类型 | 内容 | 来源 |
|---|---|---|---|
| `pages/concepts/artifact-chain-state-machine.md` | concept | 产物链状态机：intent→spec→plan 文档链即状态、断链=孤儿文档、归档分离活跃/历史、audit_artifacts.py 确定性推导不靠手改状态 | Issue #4 + `intent/archive/flow-tracking.md` + `scripts/audit_artifacts.py` |
| `pages/concepts/doc-transient-persistent-boundary.md` | concept | 文档时态边界：intent/spec/plan 是 Transient（PR 合并即终），wiki 是 Persistent（跨需求演化）；归档动作触发知识编译 | Issue #32（本需求设计决策 E） |
| `pages/decisions/hooks-python-zero-dep.md` | decision | 为何 hooks 用 Python 标准库零依赖（跨平台、无 jq/node 假设、可单测），替代被拒方案（bash/jq） | Issue #18/#29 + README §六 + `.githooks/`、`.qoder/hooks/` |
| `pages/decisions/review-non-blocking.md` | decision | 为何 AI 审查不阻塞合并：建议只提意见，批准走 code owner + 分支保护（防 agent 自批自合）；REVIEW.md 是人写给 AI 的"尺子"非报告 | Issue #23 + `REVIEW.md` + `.github/prompts/review.md` |

## 6. 根 AGENTS.md 改动

Architecture 节追加一行（保持一页内，当前 36 行 → 37 行）：

```
- `wiki/`：长青知识层（决策/教训跨需求复用；结构见 wiki/AGENTS.md，查询先读 wiki/index.md）
```

## 7. 验收方式

- [ ] `wiki/` 四件套齐备（AGENTS.md/index.md/log.md/pages/），Schema 覆盖 §4 六小节
- [ ] 首批 4 节点就位，每页带来源（Issue #xx 或 archive 链接），符合 §3.2 约定
- [ ] 根 AGENTS.md 只有一行指路、全文仍在"一页内"
- [ ] **Query 演示**：按 Schema 走一遍——读 index.md → 回答"为什么 hooks 用 Python？"→ 引用 decisions/hooks-python-zero-dep.md
- [ ] **Ingest 演示**：本次落地本身即 Ingest（首批节点由 archive 编译而来），log.md 有条目
- [ ] **Lint 演示**：检查首批页面无孤立页/断链（index 全覆盖）
- [ ] `make test` + `make lint` 全绿；`python scripts/audit_artifacts.py` 进度表正常（wiki/ 不影响产物链判定）
