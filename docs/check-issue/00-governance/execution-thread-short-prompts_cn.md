# 执行线程短口令

## 用途

这份文档给开新线程时快速复制用。

适用场景：
- 你已经确定任务包
- 只想先把执行线程拉起来
- 详细边界和回测要求仍然以对应任务包为准

## TA-001

```text
负责 TA-001：只在 BeautyQA-TrendAgent 内按 docs/14、docs/15 和 docs/check-issue/20-trendagent/TA-001-trendagent-to-qa-contract-adoption.md 落 first-party trend_signal 输出路径，禁止修改 BeautyQA-vendor/MediaCrawler 和 QA 侧逻辑，交付 changed files、implementation summary、1 个 sample trend_signal、backtest result、open risks，若 contract 不足先暂停并回报 architecture-control。
```

## QA-001

```text
负责 QA-001：只在 BeautyQA-core 内按 docs/14、docs/15 和 docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md 接入 first-party trend_signal retrieval，禁止引入 vendor crawler 依赖或直接读取 vendor raw table，交付 changed files、implementation summary、1 个有 trend evidence 的 QA 例子、1 个 trend evidence 缺失或过期的 QA 例子、backtest result、open risks，若 schema 或 contract 不足先暂停并回报 architecture-control。
```

## QA-002

```text
负责 QA-002：只在 BeautyQA-core 内按 docs/14、docs/15、docs/check-issue/30-qacore/QA-001-review.md 和 docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md 修正 QA 趋势证据门控，必须加入 high-risk safety gating、把 legacy CSV 兼容从主运行路径剥离、补齐 stale/low-confidence/high-risk 回测，禁止引入 vendor crawler 依赖或放松 first-party contract 边界，交付 changed files、implementation summary、回测结果、open risks，若 contract 不足先暂停并回报 architecture-control。
```

## QA-003

```text
负责 QA-003：只在 BeautyQA-core 内按 docs/14、docs/15 和 docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md 把 QA 侧实现收紧回 trend_signal ingestion + retrieval/evidence assembly 边界，保留 first-party contract 读取、freshness/confidence/risk metadata 透传与 graceful fallback，但不要在这个子任务里固化最终 safety/compliance answer policy；若 QA-002 已把回答治理写进 runtime，请降级为 metadata/flag 输出或可插拔 hook，交付 changed files、implementation summary、回归说明、backtest result、open risks。
```

## QA-004

```text
负责 QA-004：只在 BeautyQA-core 内按 docs/16-trend-signal-to-qa-usage-guide.md 和 docs/check-issue/30-qacore/QA-004-trend-evidence-layer-integration.md 落 trend evidence layer，范围只包含 first-party trend_signal ingestion、evidence item parsing、retrieval/filter hooks、trend context block 输出与 trace/debug 字段保留，不处理主 QA 系统的最终回答治理，交付 changed files、implementation summary、sample trend context output、backtest result、open risks。
```

## INT-001

```text
负责 INT-001：按 docs/check-issue/40-integration/INT-001-e2e-smoke-test.md 做最小端到端 smoke test，验证 cleaned_trend_data -> trend_signal -> QA evidence ingestion 这条链真实可跑，范围只限 sample 数据、最小 fixture、最小联调脚本与回测报告，不扩成正式 benchmark，不修改 vendor crawler，交付 changed files、smoke test run result、sample inputs/outputs、open risks。
```

## EVAL-001

```text
负责 EVAL-001：按 docs/check-issue/50-evaluation/EVAL-001-benchmark-v1.md 设计 benchmark v1，产出 dev/holdout 结构、case 清单、覆盖矩阵、评分执行说明与首版资产组织方案，重点验证 trend evidence 应该用、可以用但不能主导、缺失时应回退三类场景，不在本任务里追求大规模数据生成，交付 changed files、benchmark package summary、coverage matrix、open risks。
```

## 关于 `trend_keyword_expansion_spec_cn.md`

这份 spec 只影响 `TA-003`，不影响 `TA-001` 和 `QA-001` 开工。

处理建议：
- 如果近期要启动 `TA-003`，最好先把 `data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md` 提交进主干。
- 如果暂时不启动 `TA-003`，可以先不提交；到时把 spec 文件一并发给执行线程也可以。

更直接的判断：
- `TA-001` 和 `QA-001` 现在可以直接开工。
- `TA-003` 最好在 spec 已进仓库后再开工。
