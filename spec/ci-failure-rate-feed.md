# Spec：CI 失败率真实采集接入维护闭环

> 对应 intent：`intent/ci-failure-rate-feed.md`（Issue #18）。本文档定"做什么、按什么标准验收"，实现顺序见 `plan/ci-failure-rate-feed.md`。

## 1. 现状事实（已核实）

- `metrics/ci_test_failure_rate.json`：示例数据（`_说明` 自认），无任何环节写入真实值
- `maintenance-scan.yml` detect job：读 `values[-1]` → `detect_drift.py` 分档 → 永远 normal（示例值静止）
- `detect_drift.py`：**不读 bands.yaml**——σ 阈值（1/2/3σ + 最近 6 点单调漂移升 2σ）硬编码在脚本内；bands.yaml 是"层级/动作设计声明"，当前为模板占位态
- `maintenance-scan.yml` 的 job 结构（detect → diagnose[2σ] / act[3σ]）与 bands.yaml tiers 一致，注释引用 bands.yaml

## 2. 功能规格

### F1 采集脚本 `scripts/collect_ci_failure_rate.py`（新建，纯标准库）

**职责**：拉取最近 N 次 main push 的 ci.yml 运行结果 → 统计失败率 → 追加一条到 `metrics/ci_test_failure_rate.json`（滚动保留上限 M 条）。

**纯函数（可单测）** `failure_rate(runs: list[dict]) -> float`：
- 输入为 GitHub Actions runs API 的 item 列表（每项含 `conclusion`）
- 分母：`conclusion ∈ {success, failure, timed_out, action_required}` 的 run（cancelled / skipped / stale 不算——非 CI 判定结果）
- 分子：分母中 `conclusion != success` 的 run
- 返回 0.0~1.0 的比率（空列表 → 0.0）

**CLI**（`python scripts/collect_ci_failure_rate.py`）：
- 环境变量读取：`GH_TOKEN`（必填）、`GITHUB_REPOSITORY`（owner/repo，必填）；URL 用标准库 `urllib.request`
- API：`GET /repos/{owner}/{repo}/actions/runs?workflow_id=ci.yml&event=push&per_page={N}`（只统计 main push 的 run——PR run 与分支开发噪声不计入主干健康度）
- N 默认 30；追加后 values 保留最近 M=60 条（超限从头部裁剪）
- 写文件：读现有 JSON（兼容缺文件/缺 values 字段）→ 追加 → 原子写回（先写临时文件再 replace）；文件顶层保留 `_说明`/`metric`/`unit` 字段
- stdout 输出追加后的最新值（供 workflow 使用）；异常时非零退出并输出 `::error::`

### F2 `maintenance-scan.yml`：detect 前插入 collect job

- **决定：新 job `collect`（permissions: contents: write），detect job 改为 `needs: collect`**（detect 保持只读权限）
- collect job steps：checkout → setup-python → `python scripts/collect_ci_failure_rate.py`（env: GH_TOKEN=`${{ github.token }}`）→ `git add metrics/ci_test_failure_rate.json` → commit（message：`metrics: 追加 CI 失败率采样 (#18) [skip ci]`——引用 #18 防 check-commit-refs 误伤，`[skip ci]` 防递归触发 ci.yml）→ `git push`（推 main：本 workflow 只 schedule/manual 触发，无递归风险；`git config user` 设为 `github-actions[bot]`）
- 容错：collect job 整体 `continue-on-error: true`（采集失败可见但不断链）；detect 用 `if: always()` 保证即便 collect 失败也继续检测（读旧值）
- detect job 权限不变（只读）；VALUE 来源不变（`values[-1]` 现在就是真实值）；diagnose/act 不变

### F3 `bands.yaml`：真实化 + 如实声明

- `metric: ci_test_failure_rate`（去掉 `<指标名>` 占位）
- `baseline: rolling_30d`、`rules: western_electric` 保留（与 detect_drift.py 行为一致：30 次窗口 + WE 规则）
- 补注释：σ 阈值实现在 `scripts/detect_drift.py`（硬编码 WE 规则），bands.yaml 声明层级与动作（log/diagnose/act），二者由 maintenance-scan.yml 的 job 结构绑定
- 删除文件尾部"填写提示（填完可删）"整段

### F4 `metrics/ci_test_failure_rate.json`：清空示例历史

- 首采前把 values 清空（示例数据污染真实基线）——`_说明` 更新为"由 maintenance-scan 每日采集追加，勿手改"
- 冷启动：前 1-2 次采集 detect 会报 `insufficient_data`（脚本要求 ≥2 个历史点），属预期，日志可见即可

## 3. 验收标准（对应 Issue #18）

- [ ] F1 脚本存在，`failure_rate()` 有单元测试（tests/test_collect_ci_failure_rate.py：全 success / 含失败 / cancelled 排除 / 空列表边界）
- [ ] F2 collect job 就位；手动触发 maintenance-scan 后 metrics 文件出现真实追加 commit（message 含 #18 + [skip ci]），且**未**触发新的 ci.yml run（[skip ci] 生效实证）
- [ ] F3 bands.yaml 无模板占位（无 `<指标名>`、无"填完可删"）
- [ ] F4 metrics values 从真实采样重建（非示例数据）
- [ ] make test 全绿、make lint 零告警
- [ ] Gate 1→5 全流程走完并发布 v0.1.1

## 4. 明确不做什么

- 不改 detect_drift.py 的分档逻辑（σ 阈值迁移到 bands.yaml 解析属于另一个需求，超出本次范围）
- 不改 ci.yml 的 4 checks 门禁
- 不做 PR run 的失败率统计（只统计 main push）
- 不引入任何新依赖
