# Wiki 日志

> 追加式时序日志：wiki 演化的完整时间线。条目格式：`## [YYYY-MM-DD] 操作 | 说明`（可用 `grep "^## \["` 解析）。

## [2026-09-04] ingest | llm-wiki 落地（Issue #32）
- 建立 wiki/ 长青知识层：Schema（AGENTS.md）+ index.md + log.md + pages/（concepts/ + decisions/）
- 首批 4 节点由 archive 逆向编译（本需求自身即 Ingest 演示）：
  - concepts/artifact-chain-state-machine.md ← Issue #4 flow-tracking + audit_artifacts.py
  - concepts/doc-transient-persistent-boundary.md ← Issue #32 设计决策 E
  - decisions/hooks-python-zero-dep.md ← Issue #18/#29 + README §六 + hooks 实测
  - decisions/review-non-blocking.md ← Issue #23 + REVIEW.md + prompts/review.md

## [2026-09-04] lint + schema 演化 | llm-wiki 初始化补全（Issue #32）
- lint：修复 2 处跨目录断链（decisions/ 页链接 concepts/ 缺 ../），复检无断链、无孤立页
- schema 演化：AGENTS.md 新增“发起（人视角）”节——随时可对话触发 ingest/query/lint，不再只依赖归档动作；README 目录与知识收口节同步
