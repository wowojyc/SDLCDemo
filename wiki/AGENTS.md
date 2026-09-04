# Wiki Schema（wiki/AGENTS.md）

> 本文件指导你（LLM）维护本仓库的 `wiki/` 长青知识层。人机共同演化：实践中有效的工作流请追加回本文件（走 PR，引用 Issue）。

## 角色：wiki 是什么

`intent/` `spec/` `plan/` 回答"**这次需求做什么**"——时态文档，PR 合并后移入 `archive/`，归档即"死"。
`wiki/` 回答"**这个库一直怎么被 AI 正确地改**"——长青知识层，跨需求持续演化，不随归档消失。

**归档 → 编译**：需求收尾（文档移入 archive/）时，把其中的决策、教训、反模式编译进 wiki 页面，而不是让知识沉睡在 archive 里。

## 结构

```
wiki/
├─ AGENTS.md              # 本文件（Schema）
├─ index.md               # 内容目录：每页一行摘要 + 链接，按类组织
├─ log.md                 # 时序日志：## [YYYY-MM-DD] ingest/query/lint | 说明
└─ pages/
   ├─ concepts/           # 定义页：永远为真（机制、边界、判定规则）
   └─ decisions/          # 决策页（ADR）：当时为什么这么选，含被拒方案
```

## 页面约定

1. 每页头部一行元信息：`> 类型：concept/decision ｜ 来源：Issue #xx / archive 链接 ｜ 更新：YYYY-MM-DD`——不写无来源结论
2. 提及相关页面必须用相对链接互链（如 `[产物链状态机](pages/concepts/artifact-chain-state-machine.md)`）
3. 页面与代码/AGENTS.md 冲突时，以代码和 AGENTS.md 为准，并更新页面、标注更新日期
4. 语言：中文大白话，AI 能直接读懂（对齐 intent 模板文风）

## 工作流

### Ingest（摄入）—— 触发：需求归档动作（PR 含 archive/ 移动时）

1. 读归档文档（intent/spec/plan 的 archive 版本）与相关代码，提取**跨需求仍成立的决策/教训**（"这次怎么做"的不编译，只编译"以后一直怎么改"）
2. 新建或更新 `pages/` 相关节点（一个需求归档可能触及 2–4 页）
3. 更新 `index.md`（新增/修订行摘要）
4. `log.md` 追加一条（`## [YYYY-MM-DD] ingest | <slug> 归档编译`）
5. 随该 PR 一起提交（commit 引用 Issue；wiki 变更永不独立提交）

### Query（查询）—— 触发：被问"为什么 / 怎么设计 / 踩过什么坑"

1. 先读 `index.md` 定位相关页面，再深入阅读
2. 回答带页面引用
3. 产出了有价值的综合/对比/分析 → 经用户确认后回写为新页面（探索不消失在聊天里）

### Lint（健康检查）—— 触发：每次 Ingest 时顺带 + 定期（如每月）

检查并输出清单：页面矛盾 / 被新事实取代的过时声明 / 孤立页（index 未收录或无人链入）/ 被提及但缺独立页的重要概念 / 断链。修复随 chore Issue 提交。

## 边界（防三套真相）

- 不重复根 `AGENTS.md`（常驻总纲，一页内）与 `.qoder/rules/`（按需加载的操作约束）——wiki 只收它们装不下的深度知识
- 不改 `intent/spec/plan` 的 archive 文件（Raw 层只读）
- wiki 维护遵守仓库全部既有规则：commit 必须引用 Issue、改动需 `make test` 通过、走分支 + PR
