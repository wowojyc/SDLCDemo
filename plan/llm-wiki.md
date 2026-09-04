# Plan：仓库级 LLM Wiki——Karpathy 原版模式实例化（技术方案）

> 来源：Issue #32（intent v1 已批准 / spec 草案）
> 状态：草案（Gate 2）

## 1. 目标回顾

交付 `wiki/` 长青知识层：Schema（wiki/AGENTS.md）+ index.md + log.md + pages/ 首批 4 节点（2 concept + 2 decision），全部由 archive 逆向编译；根 AGENTS.md 加一行指路。纯文档需求（规则工具型），无 src/ 代码、无新依赖、不改 hooks/CI。落地过程本身即 Schema Ingest/Query/Lint 的首次演示。

## 2. 改动文件清单

| 文件 | 动作 | 内容 |
|---|---|---|
| `wiki/AGENTS.md` | 新增 | Schema（spec §4 六小节：角色/结构/页面约定/Ingest/Query/Lint/边界） |
| `wiki/index.md` | 新增 | 内容目录：4 节点一行摘要 + 链接，concepts/decisions 分组 |
| `wiki/log.md` | 新增 | 初始条目：`## [2026-09-04] ingest | llm-wiki 落地——首批 4 节点由 archive 编译` |
| `wiki/pages/concepts/artifact-chain-state-machine.md` | 新增 | 产物链状态机（spec §5 行 1） |
| `wiki/pages/concepts/doc-transient-persistent-boundary.md` | 新增 | 文档时态边界（spec §5 行 2） |
| `wiki/pages/decisions/hooks-python-zero-dep.md` | 新增 | hooks 零依赖决策（spec §5 行 3） |
| `wiki/pages/decisions/review-non-blocking.md` | 新增 | REVIEW 不阻塞决策（spec §5 行 4） |
| `AGENTS.md` | 修改 | Architecture 节追加 wiki 指路一行（spec §6） |
| `intent/llm-wiki.md` | 修改 | 头部状态"起草（Gate 1）"→"已批准（Gate 1）" |

（spec/plan 两文档随实现 PR 一并提交，作为本需求产物链）

## 3. 实施步骤（文档先行，单 commit 落地）

### Step 1：素材核对（只读，不提交）
1. 精读 `intent/archive/flow-tracking.md`、`scripts/audit_artifacts.py` 主逻辑 → 提炼产物链状态机的机制与"断链"定义
2. 精读 `README.md` §六设计要点、`REVIEW.md` 头部、`.githooks/commit-msg` → 提炼 hooks 零依赖与 REVIEW 不阻塞的决策脉络（含被拒方案）
3. 精读 `intent/llm-wiki.md` 设计决策 E → 提炼 Transient/Persistent 边界

### Step 2：写 Schema（wiki/AGENTS.md）
按 spec §4 大纲逐小节写；语言：中文大白话；明确"归档 → 编译"触发（PR 含 archive/ 移动时）、Query 先读 index、Lint 随 Ingest 顺带 + 定期

### Step 3：编译首批 4 节点（Ingest 演示）
每页遵守 spec §3.2 约定（头部来源行、相对链接互链、冲突以代码为准）：
- concept ×2：产物链状态机、文档时态边界
- decision ×2：hooks 零依赖（含被拒的 bash/jq 方案）、REVIEW 不阻塞（含"AI 不批准不阻塞"原则）
- 页面间互链：doc-transient-persistent-boundary ↔ artifact-chain-state-machine；hooks-python-zero-dep ↔ review-non-blocking（都引用 AGENTS.md 语境时）

### Step 4：index.md + log.md
- index：4 节点一行摘要 + 相对链接，分组列出
- log：初始 ingest 条目（格式 `## [YYYY-MM-DD] ingest | 说明`）

### Step 5：AGENTS.md 指路 + intent 状态更新
- Architecture 节追加 spec §6 行（保持一页内）
- intent/llm-wiki.md 状态改为"已批准（Gate 1）"

### Step 6：验证（全绿后提交）
1. `make test` + `make lint` → 输出贴入汇报
2. `python scripts/audit_artifacts.py` → 确认进度表正常（wiki/ 不干扰产物链判定；intent/llm-wiki.md 显示活跃）
3. Query 演示：按 Schema 读 wiki/index.md → 回答"为什么 hooks 用 Python？"→ 应引用 decisions/hooks-python-zero-dep.md（汇报中演示）
4. Lint 演示：核对 index 覆盖 4 页、页面互链无断链（汇报中列出）
5. commit：`docs(wiki): LLM Wiki 落地——Schema + index/log + 首批 4 节点编译 (#32)`

### Step 7：推送 + PR
- push `docs/llm-wiki` → 开 PR（body 含 Closes #32 + 验证输出 + 测试文件改动声明"无"）

## 4. 关键实现决策

| 决策点 | 方案 | 依据 |
|---|---|---|
| Schema 与根 AGENTS.md 关系 | wiki/AGENTS.md 独立成文，根 AGENTS.md 只加指路一行 | spec Q4；根总纲一页内约束（AGENTS.md L3） |
| pages 分类 | concepts/ + decisions/ 两层 | spec Q3 |
| 首批节点数量与选题 | 4 页（2+2），全部有 archive/代码/README 实据 | spec §5；"不写无来源结论"约定 |
| wiki 提交方式 | 随本需求 PR（含 archive 语义的编译）一次提交 | spec Q1；本需求即规则工具型完整交付 |
| 文档回合验证 | 本会话已写文件，Stop 前必须 `make test` | spec Q2；auto-lint 脏标记机制 |

## 5. 风险与证明方式

| 风险 | 概率/影响 | 缓解 |
|---|---|---|
| Schema 写得像模板而非工作流，AI 不会照做 | 中/高 | 每节给"触发条件 → 步骤"；本需求落地即 Ingest 实证，Query/Lint 在验收中演示 |
| 首批节点内容与 archive 偏差（编译失真） | 低/中 | 每页强制来源行；Step 1 素材精读后再写；页面注明"与代码冲突以代码为准" |
| 根 AGENTS.md 撑破一页 | 低/低 | 只加一行（36→37 行），验证时目检 |
| wiki/ 干扰 audit_artifacts 产物链判定 | 低/中 | audit 只扫 intent/spec/plan 顶层（脚本行为既定）；Step 6.2 实测确认 |
| hook 拦截纯文档回合 | 确定（机制如此）/低 | 不豁免；Step 6.1 跑 make test 通过即解锁 Stop |

## 6. 验收标准（映射 spec §7）

完成后逐项自检 spec §7 勾选清单，并把 make test/lint 原始输出、audit 进度表、Query/Lint 演示结果贴入 PR body。
