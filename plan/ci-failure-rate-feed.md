# Plan：CI 失败率真实采集接入维护闭环

> 对应 intent/spec（Issue #18）。顺序执行，每步有明确产物；提交拆分遵守 pre-commit 规则（实现与测试分两次提交）。

## 分支

`feat/ci-failure-rate`（从 origin/main 建）

## 步骤

### Step 1 · TDD：先写测试（新建文件，protect-tests 放行）
- 新建 `tests/test_collect_ci_failure_rate.py`：
  - `failure_rate()` 纯函数用例：全 success → 0.0；含 failure → 比例正确；timed_out/action_required 计入失败；cancelled/skipped/stale 排除（不进分母）；空列表 → 0.0
  - 追加/裁剪逻辑用例：`append_value(values, v, cap=60)` 超限头部裁剪
- 跑 `make test`：新用例失败（模块不存在）→ 红，符合 TDD

### Step 2 · 实现 `scripts/collect_ci_failure_rate.py`
- 纯函数：`failure_rate(runs)`、`append_value(values, v, cap)`
- CLI：urllib 拉 `GET /repos/{owner}/{repo}/actions/runs?workflow_id=ci.yml&event=push&per_page=30`（env：GH_TOKEN / GITHUB_REPOSITORY）→ 算失败率 → 追加写回 metrics JSON（原子写；保留顶层字段）→ stdout 打印最新值
- 跑 `make test` → 全绿；`make lint` → 零告警

### Step 3 · bands.yaml 真实化 + metrics 初始化
- `bands.yaml`：`metric: ci_test_failure_rate`；删"填完可删"段；补"σ 阈值实现在 detect_drift.py"说明注释
- `metrics/ci_test_failure_rate.json`：values 清空（示例数据移除），`_说明` 改"由 maintenance-scan 每日采集追加，勿手改"

### Step 4 · maintenance-scan.yml 加 collect job
- 新 job `collect`（contents: write，continue-on-error: true）：checkout → setup-python → 跑采集脚本 → commit（`metrics: 追加 CI 失败率采样 (#18) [skip ci]`，user=github-actions[bot]）→ push
- detect job：`needs: collect` + `if: always()`；其余不动

### Step 5 · 本地验证
- `make test`（全绿，含新测试）+ `make lint`（零告警）
- 模拟冒烟：本地对 `failure_rate` 用样例 run 列表跑一遍

### Step 6 · 提交（拆两次，引用 #18）
1. commit 1（实现+文档）：collect 脚本 + bands.yaml + metrics + maintenance-scan.yml + intent（状态已更新）/spec/plan 文档
2. commit 2（测试）：`tests/test_collect_ci_failure_rate.py`

### Step 7 · PR + 门禁
- push 分支 → 开 PR（Closes #18）→ 4/4 checks 全绿（含云端 AI review）→ 用户 approve 合并

### Step 8 · 合并后实证（验收）
- 手动触发 maintenance-scan（workflow_dispatch）→ 观察：collect job 追加真实值 commit（带 #18 + [skip ci]）→ 未触发新 ci.yml run → detect 输出真实"当前值"（冷启动期可能 insufficient_data，属预期）
- 核对 Issue #18 验收项逐条打勾

### Step 9 · 归档
- intent/spec/plan 三份移入各自 `archive/`（git mv）

### Step 10 · 发版 v0.1.1（Gate 4.5）
- `git tag v0.1.1 && git push origin v0.1.1` → release.yml 门禁（test/lint + 格式校验）→ Release 生成（notes 含本 PR）

## 风险与预案
- `[skip ci]` 不生效 → ci.yml 会被 collect push 触发一次：无害（非递归），检查 ci run 日志确认是否触发，若触发则改用 ci.yml `paths-ignore: ['metrics/**']` 兜底
- collect 脚本 API 403（token 权限）→ run 黄（continue-on-error），检查 workflow permissions
- 冷启动 insufficient_data → 属设计预期（≥2 个点后才分档），连续跑 2-3 天后正常

## 执行修正记录（PR #19 合并后实证发现，2026-09-02）

### 实证结果（Step 8 首次执行，run 33605657971）
- ✅ 采集真实失败率 0.2143（窗口内 ci.yml run 如实统计）
- ✅ 本地 commit 生成（`metrics: 追加 CI 失败率采样 (#18)`）
- ❌ `git push origin HEAD:main` 被拒：`GH006: Protected branch update failed`——**main 分支保护要求一切变更走 PR，workflow 的 GITHUB_TOKEN 无法直推**（bot 非 admin，enforce_admins 开关均无法绕过）
- ✅ 容错按设计生效：collect 失败但 run 整体绿（continue-on-error），detect 用 `if: always()` 照常读旧值，diagnose/act 正常 skip

### 根因
spec 决策「collect job 直接 push main」与 main 分支保护互斥；本地测试无法暴露，只有云端真实 run 可见。

### 修正（PR #20）
- **写回改走独立数据分支 `metrics-data`**（不受保护）：ci.yml 只监听 push main → 推数据分支天然不触发 CI（原风险表「[skip ci] 不生效」风险消除）；main 上 metrics 文件降级为冷启动种子
- collect job：切到 `metrics-data` 最新（首次从 main 起步）→ 从 main 取最新脚本（reset 取消 stage，commit 只含 metrics）→ 采集 → commit（#18 溯源）→ `git push origin HEAD:metrics-data`
- detect job：新增「载入 metrics 历史」步骤（fetch + checkout 数据分支文件，只读）
- spec F2/F4 + bands.yaml 数据流注释 + metrics 种子说明同步更新

### 修正后需重跑验证（Step 8 二次执行）
1. PR #20 4/4 全绿 → merge
2. 手动触发 maintenance-scan → 验证：`metrics-data` 分支出现真实追加 commit；未触发新 ci.yml run；detect 输出真实当前值（冷启动期可能 insufficient_data，属预期）
3. 通过后续 Step 9（归档）→ Step 10（发版 v0.1.1）
