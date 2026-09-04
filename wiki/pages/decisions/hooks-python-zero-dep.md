# 决策：Hooks 用 Python 标准库实现，零依赖（含 qodercli 调用的坑）

> 类型：decision ｜ 来源：Issue #18/#29 + README §六设计要点 + .githooks/ 与 .qoder/hooks/ 实测 ｜ 更新：2026-09-04

## 决策

本地 hooks（`.qoder/hooks/*.py` 与 `.githooks/` 里调 Python 的部分）**只用 Python 标准库**，不新增任何依赖；`README` 与 `AGENTS.md` 明令"零新增依赖"。

具体表现为：
- `.qoder/hooks/` 全部 `.py`：用标准库 `json/threading/os/sys` 解析 IDE 注入的 stdin JSON，**无需安装 jq**
- `commit-msg`：用 bash `case` 通配而非 `[[ =~ ]]` 正则检查 Issue 引用（bash 会把 `=~` 模式里的 `#` 当注释起始，`#[0-9]+` 直接解析报错）
- `pre-push`：定位 Qoder CLI 后**直接用 node 执行 bundle JS**，不走 npm 的 sh 包装脚本

## 为什么（决策脉络）

1. **Windows + 裁剪版 git-bash 缺 POSIX 工具**：`sed/dirname/uname` 等缺失，npm 全局包生成的 sh 包装脚本静默失效——本地 AI 审查会无声跳过，看似通过实则没审。实测教训（Issue #18 端到端演习后沉淀）。
2. **跨平台一致性**：仓库要在 Windows（用户本地）与 GitHub Actions（Ubuntu）双环境跑，bash 专有技巧或平台依赖会让 hook 行为分叉。
3. **可测试、可诊断**：Python 纯标准库逻辑可拆纯函数配单测（如 audit_artifacts.py 同款风格），bash 长脚本难测且报错晦涩。
4. **守住"必须 100% 拦住"的底线**：hook 是硬防护层，任何静默失效都直接击穿防护——依赖越少，失效面越小。

## 被拒的方案

| 方案 | 拒绝原因 |
|---|---|
| bash + jq 解析 stdin JSON | jq 非 Windows 标配；README 明确"无需安装 jq"；多一层外部依赖即多一处静默失效点 |
| npm sh 包装脚本调用 qodercli | 裁剪版 git-bash 缺 `sed/dirname/uname`，包装脚本跑不起来（已实测踩坑） |
| `[[ =~ ]]` 正则做 Issue 检查 | bash 5.2 中 `#` 被当注释起始符，正则直接报错（已实测踩坑，改用 `case *'#'[0-9]*`） |

## 适用边界

- 适用：本地 git hooks、Qoder hooks、需要跨平台确定性执行的脚本层
- 失效边界：若未来 hook 需要调用厂商 CLI（如 qodercli），仍可引入（用 node 直跑 bundle 的方式），但**不引入包装脚本层**
- 注意：`.githooks/` 文件本身是 bash（git hooks 要求可执行脚本），这里的"Python 化"指**内部逻辑**优先 Python/标准库，外壳保持 bash 以便被 git 调用

## 相关

- [AI 审查不阻塞合并](review-non-blocking.md)：本地 pre-push 审查调用的同一套定位逻辑
- [文档时态边界](../concepts/doc-transient-persistent-boundary.md)：本决策如何从需求沉淀为长青知识（Issue #32 Ingest 示例）
