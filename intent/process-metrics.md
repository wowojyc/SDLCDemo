# 意图：SDLC 过程指标采集——补齐手册要求的三项过程度量

## 意图 / 作者 / 状态 / 来源 / 类型
- 意图：把需求链路的时间维度变成可度量的事实——采集 intent 存活率、spec 返工次数、需求周期三项过程指标，让"AI 原生流程是否真的比传统流程快"有证据可查
- 作者：AI（trae 起草，Qoder 评审修订 v2）｜状态：草稿（评审修订 v2，待 Gate 1 批准）｜来源：Issue #29
- 类型：实现型（产采集脚本）+ 规则型（改 intent 模板与类型体系）——类型字段设计见「设计决策 A」

## 问题
仓库目前只有产品指标（`metrics/ci_test_failure_rate.json` + `scripts/detect_drift.py`），过程指标整层缺失。对照 Anthropic《AI-Native SDLC Playbook》，手册每个阶段（Plan/Design/Build）都配先行/滞后度量：

- **Plan 阶段滞后指标**——intent 存活率：被允许进入下一阶段（产出 spec 或 plan）的 intent 占比。手册原文"产品负责人允许进入第二阶段的 intent.md 所占比例"。仓库现状：无从得知登记的意图有多少推进到设计/实现，无法判断需求收口环节是否健康。
- **Design 阶段滞后指标**——spec 返工次数：spec.md 在 plan.md 首次提交之后的提交次数。手册原文"提交第一份 plan.md 以后，spec.md 又发生了多少次提交"。仓库现状：无法判断设计是否在实现开始后频繁返工。
- **端到端先行指标**——需求周期：intent.md 首次提交到链路末端产物首次提交的时间差。手册原文"从提交 intent.md 到提交 spec.md 的时间""两个 Git 时间戳可以直接提供数据"。仓库现状：无法回答"一条需求从登记到落地要多久"。

没有这些度量，就无法回答"一条需求从登记到落地要多久、多少需求真正落地"——至少先让流程时延可测、可积累（跨项目"更快"的对比结论留待样本积累后）。

补充（评审修订 v2）："存活"不能只看代码——intent 存在**调研/梳理型**（完成形态是结论而非代码）与**规则/工具型**（产出是脚本/CI/规则文件而非 src/）。反例：flow-tracking 无 spec/plan 却真实落地了 audit_artifacts.py——按"文档推进"口径会被误判未存活。

## 设计决策（评审修订 v2，已确认）
- **A. intent 加"类型"字段**（六字段 → 七字段）：`实现型 / 规则工具型 / 调研梳理型`。人工/AI 在 intent 头部填写，脚本确定性读取——不靠 AI 猜类型（守 audit_artifacts.py 确定性铁律）
- **B. 三型完成形态映射**（存活判定按类型分派）：
  - 实现型：spec/plan（按需）+ 代码落地 + PR merge
  - 规则工具型：脚本/CI/规则文件落地 + PR merge（flow-tracking、evals 改造属此类）
  - 调研梳理型：结论产出（intent 内"结论"节更新或产出分析文档）→ 归档；判定 = 已归档 + 结论节非空
- **C. 存量回填**：3 个归档 intent 标注类型（ci-failure-rate-feed=实现、tags-webpage=实现、flow-tracking=规则工具）→ 存活率 2/3 → 3/3，误判消失
- **D. 周期口径**（实证：文档常批量提交，纯 git 文档时间戳差=0 失真）：
  - 终点：merge commit 时间——**纯 git 可得**（已验证：merge commit 的 %B 含 "Closes #xx"，正则提取 → Issue → intent 来源字段 → slug）
  - 起点：Issue created_at（gh API，与 collect_ci_failure_rate.py 同风格 urllib + token）；降级模式（无 token）：intent 首次提交时间（纯 git，"登记→合并"时延，语义略窄）

## 预期成果
- `scripts/collect_cycle_metrics.py`：从 Git 历史确定性采集三项过程指标，输出 JSON（机器可读）与 Markdown（人读进度表）
  - 纯函数 `survival_rate(intent_slugs, promoted_slugs) -> float`：算存活率
  - 纯函数 `rework_count(spec_timestamps, plan_first_ts) -> int`：算 spec 返工次数
  - 纯函数 `cycle_seconds(intent_first_ts, end_ts) -> int | None`：算需求周期
  - I/O 层用 `git log --follow --format=%ct` 拿提交时间戳（--follow 跨归档重命名追踪，已验证）
- `tests/test_collect_cycle_metrics.py`：三个纯函数的边界单测（空集合、None、同时戳、负周期等）
- 可选：`metrics/process_metrics.json`：采集结果落盘，供后续 `detect_drift.py` 扩展为过程指标漂移检测

## 受影响的用户和系统
- 工程负责人/产品负责人：能用量化数据回答"我们的需求链路是否健康"
- `scripts/` 目录：新增 `collect_cycle_metrics.py`，与现有 `audit_artifacts.py`（链路状态）、`collect_ci_failure_rate.py`（产品指标）、`detect_drift.py`（漂移检测）并列
- `tests/` 目录：新增 `test_collect_cycle_metrics.py`，与现有测试一一对应
- `metrics/` 目录：可选新增 `process_metrics.json`（与 `ci_test_failure_rate.json` 并列）
- 不影响：`src/`、`AGENTS.md`、`.qoder/`、`.github/workflows/`（本需求只加采集，不改 CI/规则）

## 约束
- 零新增依赖：只用 Python 标准库（`subprocess`/`json`/`argparse`/`statistics`/`pathlib`/`urllib`），与 `collect_ci_failure_rate.py` 同一风格
- 数据源保持确定性：只读 Git 历史与（可选）GitHub API，不靠手改状态字段，不用 AI 判断——与 `audit_artifacts.py`/`detect_drift.py` 同一铁律
- 需求类型是人工填写项（intent 头部），脚本只读不推断；存量缺失类型的 intent 按归档时间回填或排除统计
- 计数用 `int`（返工次数、周期秒数），存活率用 `float`（0.0~1.0）——遵守 AGENTS.md
- 每个对外函数有 docstring 和对应单测——遵守 AGENTS.md
- 错误用异常或退出码抛出，不返回 `None` 伪装成功——遵守 AGENTS.md
- 纯函数不碰 I/O（可单测），I/O 封装在 `_` 开头函数里——与 `collect_ci_failure_rate.py` 同一分层
- `--follow` 跨重命名追踪已验证：`intent/<slug>.md` 归档移动到 `intent/archive/<slug>.md` 后，git log --follow 返回完整历史

## 待确认问题
1. 是否需要把这个采集挂到 CI（如 maintenance-scan 或独立 workflow）定期跑？还是先做成手动脚本，验证数据有效再自动化？（倾向：先手动）
2. 过程指标是否也要进 `detect_drift.py` 的漂移检测（如"存活率连续 3 次采集下降"）？还是先只采集不告警？（倾向：后置，detect_drift 多指标化是独立改造）
3. 周期口径（设计决策 D）：起点用 Issue created_at（API）还是降级 intent 首次提交（纯 git）？确认后写进 spec
4. intent 类型字段是否同步回 sdlc-template 模板仓库（避免模板漂移）？

---

> 七字段模板：意图/作者/状态/来源/类型 · 问题 · 预期成果 · 受影响的用户和系统 · 约束 · 待确认问题。
> 来源字段：原始需求先在 GitHub 开 Issue 登记，intent.md 是它的 MRD（市场需求文档），来源填 Issue 编号（如 #12）；无关联 Issue 填 —。
> 类型字段：实现型 / 规则工具型 / 调研梳理型（主型单选，人工填——脚本据此判定需求完成形态，见 spec/process-metrics.md §2）。
> 归档规则：需求完成（PR 合并）后，intent/spec/plan 三份文档一起移入各自 archive/，audit 只统计顶层活跃文档。
> 字段固定，但内容用大白话写——不是填表，是让 AI 能直接读懂。
