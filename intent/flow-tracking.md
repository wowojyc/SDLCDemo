# 意图：需求链路自动追踪——产物链状态推导 + commit 强制关联 Issue

## 意图 / 作者 / 状态 / 来源
- 意图：让需求从 Issue 到代码的每一步可自动追踪、可回溯——产物链状态确定性推导，commit 强制关联 Issue
- 作者：demo｜状态：已批准｜来源：Issue #4

## 问题
intent/spec/plan/代码走到哪一步，目前靠人肉对比文件判断；intent.md 手写"状态"字段容易和代码事实脱节。commit 不关联 Issue，一条需求从登记到合并无法回溯；多人协作时不知道需求进行到哪个环节。

## 预期成果
- `scripts/audit_artifacts.py`：确定性推导产物链状态（intent → spec → plan → 代码 → 测试），最后一个存在的环节即当前阶段；下游存在而上游缺失 = 断链告警
- commit message 必须引用 Issue（#数字）：本地 `.githooks/commit-msg` 强制；本地被 `--no-verify` 跳过时，云端 `ci.yml` 兜底再查
- `intent/` 目录改为每需求一份 MRD（`intent/<slug>.md`），头部"来源"字段关联 Issue；需求完成（合并）后移入 `intent/archive/` 归档
- CI 每次 push/PR 输出链路进度表到 Step Summary

## 受影响的用户和系统
- 开发者：提交习惯改变（commit 必须带 #Issue）；看进度不再靠猜
- 系统：`scripts/audit_artifacts.py`（新建）、`.githooks/commit-msg`（新建）、`.github/workflows/ci.yml`（新增 job）、`intent/` 目录结构（多文件 + 归档）

## 约束
- 零新增依赖：脚本只用 Python 标准库
- 检测保持确定性：不用 AI 判断链路状态；AI 只做断链后的诊断
- 不自动改状态字段：自动化只推导"事实状态"，批准/合并仍是人的决策
- 文档体系：Issue = 原始需求，intent.md = MRD（市场需求文档），spec.md = PRD（产品需求文档）

## 待确认问题
已确认（2026-09-02）：
- 方案 A：intent/ 下每需求一个文件，完成即归档（移入 intent/archive/）
- commit 约束双保险：本地 commit-msg hook + 云端 ci.yml 检查
无遗留问题。

---

> 六字段模板：意图/作者/状态 · 问题 · 预期成果 · 受影响的用户和系统 · 约束 · 待确认问题。
> 来源字段：原始需求先在 GitHub 开 Issue 登记，intent.md 是它的 MRD（市场需求文档），来源填 Issue 编号（如 #12）；无关联 Issue 填 —。
> 归档规则：需求完成（PR 合并）后，本文件移入 intent/archive/，audit 只统计顶层活跃 MRD。
> 字段固定，但内容用大白话写——不是填表，是让 AI 能直接读懂。
