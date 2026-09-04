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

## 已知失效模式：审查故障仍报“审查通过”（实测 2026-09-04，两次触发）

本地 Qoder（qoderclicn/qodercli）**运行期失败**（额度超限 / 网络中断 / CLI 崩溃）时，pre-push 的结论行依然打印“审查通过”并放行。实测细节：额度超限消息会出现在回显里（qodercli 把错误打到 stdout 进入 `$result`），但它与“审查通过”**并存**——错误可见、结论仍是通过，稍不留意就忽略。

机制链（.githooks/pre-push）：
1. **退出码被吞**：`result=$(node ... 2>/dev/null || true)`——CLI 非零退出码被 `|| true` 吞掉，后续无从知晓调用失败；stderr 被丢弃，但错误走 stdout 进了 `$result`（实测额度消息被 echo 出来）
2. **判定只看内容模板**：python 判断只认“`## Important` 段里有无方括号标签”——无发现正文（“无。”）和报错文本都**没有**该段 → 同样判“无发现” → `exit 0`
3. **不对称提示**：CLI 缺失、review.md 缺失两个**能预知**的分支都有显式提示（“跳过 AI 审查”）；唯独运行期失败没有“跳过”字样——失败被包装成通过

根因：审查脚本用“输出内容是否含发现项”推断“审查是否执行”，而调用失败（非零退出码）信息被吞——内容判断无法覆盖失败路径，非阻塞审查因此存在“故障 = 通过”缺口。

应对（现状下）：
- push 后扫一眼 pre-push 回显：出现额度 / error / exceeded 等字样但结论是“审查通过” → 视为未审查，手动补审或重 push
- 云端 pr-review.yml 是第二道防线（同一套尺子），但只覆盖 PR 场景

改进方向（未实施）：保留退出码（去掉 `|| true` 或记录 `$?`），非零时打 warning 并中止 push，或至少明示“审查未完成，请人工确认”——把故障降级变成显式降级。

## 相关

- [Hooks 用 Python 标准库零依赖](hooks-python-zero-dep.md)：承载本决策的本地执行层（同一条防护链）
- [文档时态边界](../concepts/doc-transient-persistent-boundary.md)：REVIEW.md 的尺子角色属于长青知识的一部分
