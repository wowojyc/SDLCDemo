# Todo API

一个最小可跑的待办清单服务，用来演示 **Qoder（本地 agent）+ GitHub（平台自动化）** 如何跑通 AI 原生开发闭环。

> 核心思路：**文件即唯一事实来源，AI 只经有闸门的路由行动，人只做分诊与拍板。**

**当前需求**：[intent/intent.md](intent/intent.md) —— 待办清单支持标签（尚未实现，留给 AI 做）。

---

## 一、能力分工

| 层 | 谁负责 | 具体能力 |
|---|---|---|
| **本地 agent** | **Qoder** | `AGENTS.md`（每次会话自动读）· `.qoder/rules/*.md`（按 glob / 模型决策按需加载 ≈ Skills）· **Hooks（12 事件）** · 计划模式 · 并行会话 · 子代理 |
| **协作平台** | **GitHub** | PR + 分支保护 + code owner（CR 闸门）· Actions（evals / CI / 定时扫描）· Issues（分诊队列）· 全程留痕 = 审计链 |
| **连接层** | **git** | 本地产出的文件提交后，触发平台层自动化 |

### 需求链路：Issue → MRD → PRD → 代码

| 载体 | 语义 | 谁写 |
|---|---|---|
| GitHub Issue | **原始需求**（登记处，人和自动化都在这里开） | 人 / maintenance-scan |
| `intent/<slug>.md` | **MRD** 市场需求文档：为什么做、给谁、怎么算成 | 发起者 + AI 追问收口 |
| `spec.md` | **PRD** 产品需求文档：做成什么样、约束、验收方式 | AI（人审核） |
| `plan.md` | 技术方案：文件清单、顺序、风险、证明方式 | AI（人审核） |

**状态怎么追**：不靠手改状态字段——产物链本身就是状态机。`scripts/audit_artifacts.py`
按序检查 intent → spec → plan → 代码 → 测试，最后一个存在的环节即当前阶段；
下游存在而上游缺失视为**断链**（违反流程顺序）。每次 push / PR 由 CI 输出进度表。
`intent/` 下每个需求一份 MRD（`intent/<slug>.md`），需求完成（PR 合并）后移入
`intent/archive/` 归档——audit 只统计顶层活跃文件，历史记录不干扰当前链路。

**代码必须关联 Issue**：commit message 必须含 `#数字`（GitHub 自动把 commit 挂到 Issue
时间线）。本地 `.githooks/commit-msg` 强制；被 `--no-verify` 绕过时，云端 `ci.yml` 兜底再查。
PR 写 `Closes #xx`，合并即关闭 Issue —— 一条需求从登记到合并全程留痕。

### Qoder Hooks 能做什么（这是"硬防护"层）

| 事件 | 本仓库的用法 | 对应原课 |
|---|---|---|
| `Stop`（通过后清标记） | 校验通过则清除"已跑测试"与"会话改动"标记（IDE 无 SessionStart，等效替代） | — |
| `PreToolUse` + `exit 2` | 拦危险命令、拦改测试文件 | 03.5 硬防护 |
| `PostToolUse` | 写完文件自动 lint | 03.5 硬防护 |
| `Stop` + `exit 2` | **改过文件但没跑测试不许停**（纯读回合自动放行） | 03.7 反馈闭环兜底 |
| `PermissionRequest` | 危险动作转人工审批 | 05.2 审批网关 |

---

## 二、目录结构

```
.
├─ AGENTS.md                     Qoder 项目规则（四段 + 验证块）
├─ intent/<slug>.md               01 规划：每需求一份 MRD（六字段 + 来源 Issue，完成即归档）
├─ spec.md / plan.md             02/03 设计：spec（PRD）/ plan（技术方案），由 AI 生成
├─ REVIEW.md                     05 部署：CR 审查标准（人写的尺子）
├─ bands.yaml                    06 维护：越界响应层级
├─ .qoder/
│  ├─ rules/api-conventions.md   按需加载的规则（≈ Skill）
│  └─ hooks/*.py                 4 个钩子脚本（Python 标准库，零依赖）
├─ qoder-settings.example.json   hooks + permissions 配置示例
├─ src/ tests/ Makefile          最小可跑项目（一条命令跑测试）
├─ .githooks/{pre-commit,commit-msg,pre-push}   git 层兜底（测试 / Issue 关联 / 本地审查）
├─ evals/                        04 测试：评估套件
├─ scripts/detect_drift.py       06 维护：确定性检测（不用 AI 判断）
├─ scripts/audit_artifacts.py    链路审计：产物链状态推导（确定性）
├─ metrics/                      指标历史（检测脚本的输入）
└─ .github/
   ├─ prompts/review.md          PR 审查提示词（引用 REVIEW.md）
   └─ workflows/
      ├─ ci.yml                  基础 CI
      ├─ pr-review.yml           05：AI 自动审 PR
      ├─ agent-evals.yml         04：持续评估（配置变更 + 定时）
      └─ maintenance-scan.yml    06：定期检测 + 分档响应
```

---

## 三、跑通五关

### Gate 0 · 地基
```bash
pip install -r requirements-dev.txt
make test     # 应全绿，并在 .git/ 写入"已跑测试"标记
make lint

git config core.hooksPath .githooks   # 启用提交前兜底
```

**配置 Qoder Hooks**（把示例配置合并进你的 settings）：
```bash
# Qoder CLI：     ~/.qoder/settings.json  或 项目级 .qoder/settings.json（可提交 git）
# QoderWork CN：  ~/.qoderwork/settings.json
# 复制 qoder-settings.example.json 的内容进去后，需要重启 Qoder 才生效
```

> 前置：脚本用 Python 标准库解析 stdin JSON，无需安装 jq。

**验收**：新开会话，让 AI 改 `tests/` 下任一文件 → 被 hook 拦下并提示原因。

### Gate 1 · 需求收口
先在 GitHub 开 Issue 登记原始需求，再手写（或改写）`intent/intent.md`
（六字段，来源字段填 Issue 编号）。提交进 git。
**验收**：找一个没参与的人读，他能说清"要什么、为什么、怎么算成"。

### Gate 2 · 设计 + 计划
```
读取 intent/intent.md，产出 spec.md：功能、数据流、系统变更、所需约束，
以及明确标出的关注点（尤其你无法满足或相互矛盾的地方）。
不要修改任何代码，只写 spec.md。
```
```
读取 intent/intent.md 和 spec.md，产出 plan.md：要改动的具体文件、工作顺序、
风险、以及用什么测试证明做对了。先不要修改任何代码，只给方案。
```
**验收**：spec 有关注点；plan 有文件清单 + 证明方式。你接受后才进下一关。

### Gate 3 · 写码 + 自验
```bash
git checkout -b feat/待办标签   # 先建 feature 分支，本关所有提交都落在这个分支
```
```
按 plan.md 实现。每改完一个文件就跑 make test。
全部完成后跑 make test 和 make lint，把原始输出贴在你的总结里。
如果测试失败，改代码，不要改测试。
```
**验收（三条都要）**：
- [ ] 测试全绿
- [ ] 总结里有真实命令输出
- [ ] **故意埋一个失败测试** → AI 是改代码还是改测试？（改代码才对；改测试说明 hook 没生效）

### Gate 4 · 评审
```bash
git push origin feat/待办标签   # 推送 feature 分支（不是 main）
# 网页上开 PR：feat/待办标签 → main，触发 ci.yml + pr-review.yml
```
> 注意：直接 push main 无法开 PR（main→main 无 diff），`pr-review.yml` 不会触发，评审环节会被绕过。

`.github/workflows/pr-review.yml` 自动跑：读 `REVIEW.md` → AI 审 → 贴评论。
在仓库 Settings → Secrets 配 `LLM_API_KEY`（硅基流动，https://cloud.siliconflow.com 获取）。
不配则云端审查自动跳过（不是失败），本地 pre-push 审查不受影响。

**验收**：发现项按严重度分级、带轮次标签、Nit ≤ 5 条；你只判断意图与风险。

### （可选）Gate 5 · 维护闭环
```bash
# 手动测分档：给一个明显异常的值
python scripts/detect_drift.py --metric ci_test_failure_rate \
  --value 0.35 --history-file metrics/ci_test_failure_rate.json
# 预期：tier=3sigma，action=act，退出码 2
```
Actions 里 `maintenance-scan` 每天 03:00 跑；也可手动触发并传 value。
**验收**：3σ 时自动开 Issue 进人的分诊队列（现在修 / 排期 / 忽略）。

---

## 四、四个工作流各管什么

| 工作流 | 触发 | 干什么 | 对应阶段 |
|---|---|---|---|
| `ci.yml` | push / PR | 跑测试 + lint | 地基 |
| `pr-review.yml` | PR 开启/更新 | 按 REVIEW.md 审，贴评论 | 05 部署 |
| `agent-evals.yml` | 配置变更 + 每天 02:00（北京时间，UTC 18:00） | 跑 eval 套件，掉分就失败 | 04 测试 |
| `maintenance-scan.yml` | 每天 03:00 + 手动 | 确定性检测 → 分档响应 | 06 维护 |

---

## 五、设计要点（别改坏的地方）

1. **检测必须确定性**：`detect_drift.py` 不用 AI 判断越界；AI 只负责越界后的诊断。
2. **AI 不批准、不阻塞合并**：PR 审查只是建议，批准走 code owner + 分支保护。
3. **规则文件控制在一页内**：细节放 `.qoder/rules/`，按需加载。
4. **Hooks 管底线，规则管常见**：必须 100% 守住的（不许改测试）用 hook；其余用规则文件。
5. **本地 hooks 用 qodercli，远端 CI 不再依赖它**：pre-push/pre-commit 用本地已登录的 Qoder 审查；
   远端 CI 的 AI 环节统一走 `LLM_API_KEY`（OpenAI 兼容协议），换供应商只改 Secret。
6. **需求可回溯**：commit 必须引用 Issue（本地 commit-msg + 云端 CI 双保险）；
   链路状态由 `audit_artifacts.py` 确定性推导，不靠手改状态字段。

---

## 六、已知限制

- Qoder 配置**不支持热加载**，改完 `settings.json` 需重启。
- QoderWork CN 的 hooks 配置目前是**用户级**（`~/.qoderwork/settings.json`），不能随仓库分发；Qoder CLI 支持项目级 `.qoder/settings.json`。
- 本仓库的 eval 套件是单条示例，真实使用建议 20–50 条。
- `metrics/` 是示例数据，实际应接 Prometheus / CI API。

---

*方法论来自 Anthropic《The AI-Native SDLC Playbook》；Qoder 能力信息来自 docs.qoder.com 与阿里云帮助中心公开文档（2026-08）。*
