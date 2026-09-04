# 产物链状态机

> 类型：concept ｜ 来源：Issue #4（intent/archive/flow-tracking.md）+ scripts/audit_artifacts.py ｜ 更新：2026-09-04

## 是什么

需求链路是一个**产物链**，每环一个提交到 git 的产物：

```
Issue（原始需求）→ intent/<slug>.md（MRD）→ spec/<slug>.md（PRD）
→ plan/<slug>.md（技术方案）→ src/（代码）→ tests/（测试）
```

`scripts/audit_artifacts.py` 把"需求走到哪一步"变成**确定性事实**：文件存在性与顺序全部脚本算，不用 AI 判断、不靠手改状态字段，结果可复现、可审计、有单测。

## 判定规则（记牢这三条）

1. **阶段 = 活跃需求文档链最靠后的环节**（intent → spec → plan；src/tests 是仓库共享现状，只展示、不推高阶段）
2. **断链 = 顶层 spec/plan 的 slug 不在活跃 intent 里**——孤儿文档（需求源头缺失，或需求已归档但文档没跟着归档）
3. **文档链是弹性的**：intent 必有（登记处）；spec/plan 按需——不需要设计/开发的需求可以没有

## 为什么这么设计

- **不手改状态字段**：人工维护的"状态"容易与代码事实脱节，脚本推导的"事实状态"永远真实（需求链路自动追踪的初衷，Issue #4）
- **目录结构即状态机**：顶层 = 活跃（进行中），`archive/` = 已完成——归档后目录天然区分，无需额外状态字段
- **AI 只做断链后的诊断**：检测保持确定性；越界/断链后的"为什么、怎么办"才轮到 AI 判断（与 detect_drift.py 同一铁律）

## 实战验证（Issue #29 / #32）

- process-metrics 需求（#29）：intent/spec/plan 三份文档随 PR #31 一起移入各自 archive/，audit 输出进度表确认归档兜底生效
- 本需求（#32）：intent/llm-wiki.md 活跃期间顶层 spec/plan 与 intent 同名同 slug，断链检测不误报；wiki/ 目录独立于产物链，不参与阶段判定

## 相关

- [文档时态边界](doc-transient-persistent-boundary.md)：归档即"死" vs 长青知识层的分工
- 代码事实：scripts/audit_artifacts.py（README §目录结构有说明）
