# Wiki 索引

> 本仓库的长青知识层索引。**查询时先读这里**定位相关页面，再深入阅读。
> 维护：每次 Ingest/Query 回写后更新（见 [AGENTS.md](AGENTS.md)）。
> 想往 wiki 加知识？对话里说“把 XX ingest 进 wiki”即可，发起方式见 [AGENTS.md](AGENTS.md)（人视角入口）。

## Concepts（定义：机制、边界、判定规则）

| 页面 | 摘要 |
|---|---|
| [产物链状态机](pages/concepts/artifact-chain-state-machine.md) | 需求链路 = 产物链；阶段由 audit_artifacts.py 确定性推导（不靠手改状态），断链 = 孤儿文档，文档链弹性（intent 必有，spec/plan 按需） |
| [文档时态边界](pages/concepts/doc-transient-persistent-boundary.md) | intent/spec/plan 是时态文档（归档即死），wiki 是长青知识（跨需求演化）；归档动作触发知识编译 |

## Decisions（历史决策：为什么这么选）

| 页面 | 摘要 |
|---|---|
| [Hooks 用 Python 标准库零依赖](pages/decisions/hooks-python-zero-dep.md) | hooks 只用 Python 标准库：裁剪 git-bash 缺 POSIX 工具、npm sh 包装脚本静默失效、`[[ =~ ]]` 的 # 注释陷阱——避免一切静默失效点 |
| [AI 审查不阻塞、不批准合并](pages/decisions/review-non-blocking.md) | REVIEW.md 是人写给 AI 的尺子；审查只提建议，批准走 code owner + 分支保护；防臆测宁可漏报不可错报；已知失效模式：审查运行期故障会静默放行 |

---

*更新：2026-09-04（首批 4 节点，来源 Issue #4/#18/#23/#29/#32 archive 编译；review-non-blocking 补已知失效模式节）*
