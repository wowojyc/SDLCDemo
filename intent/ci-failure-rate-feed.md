# 意图：CI 失败率真实采集接入维护闭环（端到端演习）

## 意图 / 作者 / 状态 / 来源
- 意图：把维护闭环（maintenance-scan）从"空转"变成"真检测"——CI 失败率真实采集、写入历史、bands.yaml 真实化；同时作为一次完整的 Gate 1→5 端到端演习
- 作者：demo｜状态：已批准｜来源：Issue #18

## 问题
`metrics/ci_test_failure_rate.json` 是示例数据（文件自认），没有任何环节统计真实 CI 失败率并追加写入。maintenance-scan 每天定时跑但读的是静止示例值（永远 normal 档），diagnose/act 永不触发——SDLC 维护反馈环是半截的。`bands.yaml` 仍是模板占位态（`metric: <指标名>`、填完可删提示未清理），没有成为本仓库的真实配置。

## 预期成果
- `scripts/collect_ci_failure_rate.py`（新建，标准库）：调 GitHub API 拉最近 N 次 ci.yml run，统计失败率，追加到 `metrics/ci_test_failure_rate.json`（历史长度设上限，滚动窗口）
- `maintenance-scan.yml`：detect 之前加采集步骤（有每日 schedule，不需要动 ci.yml）；写回仓库的 commit 带 `[skip ci]` + 引用 #18，不递归触发 CI、不被 check-commit-refs 误伤
- `bands.yaml`：清理模板占位，成为本仓库真实配置（指标名/基线/规则与 detect_drift.py 实际行为对齐）
- maintenance-scan 手动触发可见"当前值"来自真实统计；越界时 diagnose/act 链路可被真实数据触发
- 演习走完 Gate 1→5：Issue → intent/spec/plan → TDD 实现 → PR 4/4 → 发版 v0.1.1

## 受影响的用户和系统
- 开发者：CI 每次 push 会多跑一次"浪费性"检查？（需确认 [skip ci] 生效）；maintenance-scan 的 run 开始有实际产出
- 系统：`scripts/collect_ci_failure_rate.py`（新建）、`.github/workflows/maintenance-scan.yml`（加采集 job/步骤 + 写权限）、`metrics/ci_test_failure_rate.json`（真实数据）、`bands.yaml`（真实化）、`tests/`（新脚本对应测试）

## 约束
- 零新增依赖：采集脚本只用 Python 标准库
- 检测保持确定性：统计/分档不用 AI 判断，AI 只做越界后的诊断（沿用现有设计）
- 写回 metrics 不得递归触发 CI（[skip ci]）且 commit 必须引用 #18（防 check-commit-refs）
- ci.yml 尽量不动（避免影响 4 checks 门禁）
- 测试文件改动遵守 README「测试文件改动规则」（新建测试文件属白名单）

## 待确认问题
- 采集窗口：最近 N 次 run 取多少？（建议 N=30，与 rolling 基线匹配，可在 spec 里定）
- 历史上限：metrics values 保留多少条？（建议 60，约两个月日采）
- 失败率定义：conclusion != success 都算失败？（含 cancelled/skipped 的处置在 spec 里定）
- 写回时机：每次 schedule 跑 maintenance-scan 时采一次（每日），还是每次 main push 后采？（建议前者，随 maintenance-scan 节奏）
