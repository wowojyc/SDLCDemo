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

## [2026-09-04] ingest | 路径 A 首次演练：pre-push 审查故障仍报通过（Issue #32）
- 更新 decisions/review-non-blocking.md：新增“已知失效模式：审查故障仍报‘审查通过’”节
- 教训：本地 Qoder 运行期失败（额度超限）→ `|| true` 吞退出码 + 判定只看模板（错误文本无 `## Important` 段）→ 结论行仍“审查通过”；失败被包装成通过
- 实测触发两次（额度超限回显与“审查通过”并存），页面初稿推断不精确已按实测修正（Schema 约定：冲突以实测为准）
- 来源：.githooks/pre-push 代码实证 + push 实测 + prompts/review.md 模板核验
