# 决策：AI 审查不阻塞、不批准合并——REVIEW.md 是人写给 AI 的尺子

> 类型：decision ｜ 来源：Issue #23 + REVIEW.md + .github/prompts/review.md + README §六 ｜ 更新：2026-09-04

## 决策

PR 的 AI 审查（本地 pre-push + 云端 pr-review.yml）**只提建议，不阻塞也不批准合并**：发现项分级（Important/Nit）贴在 PR 评论，是否合并由 code owner 通过分支保护决定。REVIEW.md 是**人写给 AI 的"尺子"**（审查标准），不是 AI 审完生成的报告。

## 为什么

1. **写代码的 agent 无从批准自己的代码**：让 AI 自审自批等于没有审查。批准必须来自人（分支保护 + code owner），审查与批准权力分离。
2. **AI 审查会误报**（实测教训，Issue #23）：脱离完整上下文或误解需求时，"Important" 级误报会阻塞正常合并、消耗人的分诊精力——所以重要级判断要求"能给确切代码证据"，宁可漏报不可错报（防臆测条款）。
3. **保持主线可用**：审查意见若硬性阻塞，会让绕过审查（如直接 push main 或 --no-verify）成为诱惑；非阻塞 + 人拍板反而让流程可持续。

## 配套机制（少了这些决策不成立）

| 机制 | 作用 |
|---|---|
| 三轮审查标签（Bugs/Security/Compliance） | 按 REVIEW.md 跑三遍，每条发现贴轮次标签 |
| Important/Nit 分级 + Nit ≤ 5 条收敛 | 噪声收敛：风格问题不淹没真问题 |
| "不报"清单（生成目录 src/gen/、CI 已强制的项） | 防无效发现 |
| 本地 pre-push 只拦 Important（语义判断，非字符串匹配） | 本地审查发现 Important 才中止 push；Nit 只提示 |
| 云端 pr-review.yml 非阻塞（贴评论） | 跨协作方（网页开 PR）也能被审，但不设卡 |

## 被拒的方案

| 方案 | 拒绝原因 |
|---|---|
| AI 审查发现 Important 就硬性阻塞合并 | 误报代价高（人被迫处理假警报）；approval 权力应留在人 |
| AI 直接批准（self-approve） | agent 不能批准自己的代码；分支保护只认 code owner |
| 靠字符串匹配判断"有无发现" | AI 按模板总是输出 "## Important" 标题（即使无发现），必须语义判断（pre-push 用 python 提取段落再判） |

## 适用边界

- 适用：AI 审查环节（本地 pre-push、云端 pr-review.yml 都遵守同一套尺子）
- 失效边界：若未来要"有 Important 就不让合并"，应读 check run 的机器可读严重度计数自己配门禁（REVIEW.md 注释里给了指引），而不是让 AI 直接阻塞

## 已知失效模式：审查故障 = 静默放行（实测 2026-09-04）

本地 Qoder（qoderclicn/qodercli）**运行期失败**时（额度超限 / 网络中断 / CLI 崩溃），pre-push 不报错、不提示，静默放行——与"审查通过（无 Important）"在输出上不可区分。

机制链（.githooks/pre-push）：
1. **CLI 调用吞错**：`result=$(node ... 2>/dev/null || true)`——stderr 丢弃、非零退出码被 `|| true` 吞掉
2. **空输出 = 无发现**：空文本没有 `## Important` 段 → python 语义判断判定"无发现" → `exit 0` 放行
3. **不对称提示**：CLI 缺失、review.md 缺失两个**能预知**的分支都有显式提示（"跳过 AI 审查"）；唯独运行期失败**无提示**——防护链上唯一的静默缺口

根因：非阻塞审查的价值押在"审查跑了且诚实报告"上，但脚本无法区分"审过、无发现"与"没审"——能预知的缺失可显式降级，运行期失败只能事后从输出察觉。

应对（现状下）：
- push 后扫一眼 pre-push 回显：审查秒回 / 输出异常短时警惕静默降级，手动补审或重 push
- 云端 pr-review.yml 是第二道防线（同一套尺子），但只覆盖 PR 场景

改进方向（未实施）：result 为空时打 warning 提示"审查未完成"，把静默降级变成显式降级——需区分"CLI 没输出"与"AI 答无发现"（后者按模板必有内容），不能误伤正常通过。

## 相关

- [Hooks 用 Python 标准库零依赖](hooks-python-zero-dep.md)：承载本决策的本地执行层（同一条防护链）
- [文档时态边界](../concepts/doc-transient-persistent-boundary.md)：REVIEW.md 的尺子角色属于长青知识的一部分
