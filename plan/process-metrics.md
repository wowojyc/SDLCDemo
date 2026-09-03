# Plan：SDLC 过程指标采集（技术方案）

> 来源：Issue #29（intent v2 已批准 / spec 已批准）
> 状态：已批准（Gate 2）

## 1. 目标回顾

交付 `scripts/collect_cycle_metrics.py`（三指标确定性采集）+ 单测 + intent 类型字段（七字段）体系落地。纯函数分层对齐 `collect_ci_failure_rate.py`；不改 audit/detect 逻辑；不挂 CI。

## 2. 改动文件清单

| 文件 | 动作 | 内容 |
|---|---|---|
| `scripts/collect_cycle_metrics.py` | 新增 | 采集脚本（spec §4） |
| `tests/test_collect_cycle_metrics.py` | 新增 | 纯函数单测 ~12 用例 |
| `README.md` | 修改 ×2 | L57 目录注释、L108 Gate 1："六字段"→"七字段" |
| `intent/process-metrics.md` | 修改 | 底部模板注释七字段化 |
| `intent/archive/{ci-failure-rate-feed,tags-webpage,flow-tracking}.md` | 修改 ×3 | 头部回填类型字段 |

（spec/plan 两文档随实现 PR 一并提交，作为本需求产物链）

## 3. 实施步骤（TDD，三段提交）

### Step 1：类型体系落地（docs commit）
1. README ×2 处 + process-metrics 底部注释七字段化
2. 存量 3 个归档 intent 头部回填（ci-failure-rate-feed=实现型 / tags-webpage=实现型 / flow-tracking=规则工具型）
3. commit：`docs(intent): intent 模板七字段化（类型字段）+ 存量回填 (#29)`

### Step 2：测试先行（红）
1. 写 `tests/test_collect_cycle_metrics.py`，覆盖：
   - `survival_rate`：0/0→0.0、2/3、全完成→1.0
   - `rework_count`：空→0、全在 plan 前→0、plan 后 N 次→N、同 commit→0
   - `cycle_seconds`：None 任一端→None、负周期→None、正常差
   - `closes_from_body`：单/多 Closes、大小写（closes/fixes）、无→空集、中文混杂 body
   - `read_type`：有类型行/缺失→None/未知值原样返回
2. 跑 `make test` 确认失败（脚本不存在 import 错）——红

### Step 3：实现（绿）
1. `scripts/collect_cycle_metrics.py`（spec §4 规格）：
   - 纯函数 5 个（含 docstring）
   - I/O：`_git_log_ts`（`git log --follow --diff-filter={M,A} --format=%ct`）、`_scan_merges`（`git log --merges --format=%ct%x1f%B` + `closes_from_body` 汇总 max）、`_archive_ts`（`--diff-filter=R` 归档 rename）、`_load_intents`（读 archive/ + 顶层、正则提来源 Issue 与类型、查"## 结论"节）、`_fetch_issue_created`（urllib，token 可选）
   - main：模式判定（GH_TOKEN+GITHUB_REPOSITORY → api；否则 git 降级并标注）→ 组装输出 → JSON/Markdown
2. `make test` 全绿 → commit：`feat(metrics): 过程指标采集脚本 collect_cycle_metrics + 单测 (#29)`
3. `make lint` 零告警

### Step 4：真实数据实证（不提交）
1. `python scripts/collect_cycle_metrics.py --format markdown` 手动跑
2. 抽查对照（git log 手算）：ci-failure-rate-feed 存活证据（#18 的 merge max）、返工 0、周期 > 0；flow-tracking 存活（#4 merge 或归档兜底）
3. 实证结果截留到汇报，PR body 附"验证"节

## 4. 关键实现决策

| 决策点 | 方案 | 依据 |
|---|---|---|
| 周期起点 | API 模式（Issue created_at）/ git 降级（intent A 时间）双模式 | spec M3；实证文档批量提交失真 |
| 周期终点 | merge commit %B 解析 `Closes #\d+` 取 max；无则归档 rename 时间 | 已验证 6 条 merge 历史全命中 |
| 完成证据 | 有 Issue → merge Closes；来源 — → 归档即完成 | tags-webpage 无 Issue 先例 |
| 返工统计 | `--diff-filter=M` 排除 A/R | 归档 rename 不算返工 |
| merge 扫描防污染 | `%x1f` 分隔 ct 与 body | PR body 多行含中文 |

## 5. 风险与应对

| 风险 | 应对 |
|---|---|
| 早期直推 main（< #18）无 merge commit → 终点缺失 | 归档 rename 兜底；验收以 #18 后为主 |
| 本地无 GH_TOKEN → 周期起点失真 | git 降级模式 + stderr 标注（不静默） |
| `#4`（flow-tracking）merge commit 是否存在待实证 | Step 4 抽查；不存在则归档兜底判定存活 |
| hooks 拦截（protect-tests） | 只新建 tests 文件不改已有；commit 消息带 (#29) 过 check-commit-refs |
| Windows 编码 | subprocess capture utf-8；`_scan_merges` 用分隔符不靠行解析 |

## 6. 验证与门禁

1. `make test` 全绿（61 + ~12 = ~73 passed）
2. `make lint` 零告警
3. Step 4 实证输出与手算一致（PR body 附输出）
4. 开 PR（Closes #29）→ 全量 checks 绿 → 用户 merge → 三文档归档收尾
