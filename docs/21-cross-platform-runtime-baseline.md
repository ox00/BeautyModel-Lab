# Cross-Platform Runtime Baseline

## Position

For the current TrendAgent line, a theme keyword should not be tied to only one social platform by default.

The baseline position is:

- the same normalized theme may be observed on `xiaohongshu`, `douyin`, and `bilibili`
- platform difference should mainly live in expansion strategy, revisit policy, and risk control
- `taobao` and `industry_news` remain reference-only sources, not crawler targets

In short:

`same theme -> multi-platform crawl baseline -> platform-specific query expansion`

## Why

The older seed mental model was too close to:

- one keyword
- one suggested platform list
- one scheduler path

That is too narrow for the current project reality.

For beauty/personal-care trend observation:

- the topic usually propagates across multiple social platforms
- platform vocabulary differs
- evidence style differs
- refresh rhythm differs

But the theme itself is often shared.

So the planning model should separate:

- theme-level platform coverage
- platform-level query expansion

## Practical Rule

When building runtime baseline seeds:

- default crawl targets: `xiaohongshu | douyin | bilibili`
- preserve reference sources from the original keyword metadata
- let each platform produce its own approved seed queries and rule-based expansions

This means:

- do not require the seed CSV to pre-enumerate every platform combination before runtime can be tested
- do not flatten all platforms into the same query list

## What Changes In First-Party Logic

The first-party baseline seeding path should:

1. take one or more keyword ids
2. project them onto the shared crawl baseline
3. generate platform-specific approved registry rows
4. materialize query schedule state for each query unit

Current standard script:

```bash
./.venv/bin/python scripts/bootstrap_runtime_baseline.py --keyword-id 14
```

Platform-scoped example:

```bash
./.venv/bin/python scripts/bootstrap_runtime_baseline.py --keyword-id 14 --platform xhs bili
```

Dry run:

```bash
./.venv/bin/python scripts/bootstrap_runtime_baseline.py --keyword-id 14 --dry-run
```

## Non-Goals

- this does not mean every runtime cycle must always hit all platforms
- this does not remove cooldown, dedup, or watchlist tiering
- this does not make `xhs` high-frequency

Platform safety still applies:

- `xhs`: sparse, low-frequency verification and production cadence
- `dy`: normal repeated verification path
- `bili`: lower-risk validation and long-form evidence supplement

## Engineering Consequence

Seed design and cleaning pipeline should now be understood as:

- `keyword registry`: theme-level business anchor
- `expansion registry`: platform-specific query layer
- `query schedule state`: per-platform observation cadence
- `cleaning pipeline`: per-platform raw-table adapter into one unified cleaned evidence model

The key point is:

the seed is shared at theme level; the platform specialization happens below the seed, not inside the seed itself.
