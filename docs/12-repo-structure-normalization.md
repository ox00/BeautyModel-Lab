# Repo Structure Normalization

## Purpose

This document defines the target repository structure for the next phase of the project.

The goal is not to rename things cosmetically. The goal is to make ownership, module boundaries, and shared assets clear enough that:

- QA development can move independently
- Trend crawling can move independently
- docs, evaluation, and data assets stay shared
- future refactors do not mix self-owned code and third-party code

## Decision Summary

We will keep the current repository name for now.

The repository should be treated as a lightweight monorepo with:

- one shared collaboration layer
- one QA core module
- one trend collection module

## Target Structure

```text
repo-root/
  BeautyQA-core/
  BeautyQA-TrendAgent/
  BeautyQA-vendor/
  docs/
  data/
  scripts/
  .github/
  README.md
  CONTRIBUTING.md
```

## Directory Responsibilities

### `BeautyQA-core/`

Purpose:
- code for the QA / RAG / retrieval / orchestration path
- prompt logic, retrieval logic, QA pipeline, evaluation adapters

Should contain:
- source code
- tests
- local module README
- dependency definition if needed

Should not contain:
- trend crawler code
- third-party crawler source dump
- shared project docs

### `BeautyQA-TrendAgent/`

Purpose:
- self-owned trend monitoring and crawling orchestration code
- task generation, keyword expansion, crawl scheduling, result normalization

Should contain:
- backend service code
- config owned by our project
- tests
- module README

Should not contain:
- full third-party crawler repository copies as if they were first-party code
- QA core code

### `BeautyQA-vendor/`

Purpose:
- external codebases or vendorized tools used by project modules

Current expected use:
- keep `MediaCrawler` here instead of mixing it into `BeautyQA-TrendAgent/`

Why:
- separates project-owned code from upstream code
- makes upgrades and replacements easier
- reduces confusion about ownership

### `docs/`

Purpose:
- shared project documentation
- architecture, scope, evaluation, progress, collaboration rules

This remains a public layer for the whole repository, not for one module only.

### `data/`

Purpose:
- shared datasets, evaluation assets, trend-monitor inputs, deliveries, and intermediate machine-readable assets

This also remains shared and should not be moved under one code module.

### `scripts/`

Purpose:
- shared project scripts
- setup helpers, normalization scripts, evaluation helpers, migration helpers

These scripts should work across modules when possible.

## Current Repo Status

The first round of normalization is already in place:

- `BeautyQA-core/` now has a minimal module skeleton
- `BeautyQA-TrendAgent/` already exists and contains real work
- vendor crawler code is now isolated from first-party trend-monitor code

The next step is not another rename. The next step is to keep implementation and ownership aligned with this structure.

## Recommended Immediate Adjustments

### 1. Keep repo name unchanged for now

Reason:
- structure clarity matters more than label changes
- renaming the repository now adds communication cost without solving boundary problems

### 2. Formalize the repo as a monorepo

Meaning:
- one repository
- multiple first-level modules
- shared docs/data/evaluation layer

This should be how the team talks about the project from now on.

### 3. Separate first-party and third-party code

Recommended target:

```text
BeautyQA-TrendAgent/
  backend/
  config/
  tests/
  README.md

BeautyQA-vendor/
  MediaCrawler/
```

Do not keep long-term structure like:

```text
BeautyQA-TrendAgent/MediaCrawler-main/MediaCrawler-main
```

That layout is hard to explain and hard to maintain.

### 4. Turn `BeautyQA-core/` into a real module quickly

Minimum expected skeleton:

```text
BeautyQA-core/
  README.md
  src/ or app/
  tests/
```

This minimum skeleton is already created and should now be used as the actual QA code entry.

## Ownership Boundary

### Shared layer

Shared by the whole project:
- `docs/`
- `data/`
- `scripts/`
- `.github/`

### QA ownership

Owned primarily by the QA / RAG path:
- `BeautyQA-core/`

### Trend monitoring ownership

Owned primarily by the trend collection path:
- `BeautyQA-TrendAgent/`

### Third-party ownership

Not project-owned business logic:
- `BeautyQA-vendor/`

This boundary matters for reviews, refactors, and future onboarding.

## Migration Order

Recommended order:

1. freeze the target structure in docs
2. keep `BeautyQA-TrendAgent/` focused on first-party trend-monitor code
3. start real QA implementation under `BeautyQA-core/`
4. keep external crawler code under `BeautyQA-vendor/`
5. then decide whether a repository rename is still necessary

This order is safer because it changes the real engineering boundary before changing external naming.

## What Not To Do

- do not rename the repository first
- do not mix third-party crawler code into first-party module boundaries
- do not move shared `docs/` or `data/` under one module
- do not use directory names to represent git branches
- do not leave `BeautyQA-core/` as a fake module with no real implementation

## Definition Of Done

This normalization can be considered complete when:

- `BeautyQA-TrendAgent/` contains only project-owned trend-monitor code
- vendor crawler code is isolated under `BeautyQA-vendor/`
- `BeautyQA-core/` has a minimal usable skeleton
- root `README.md` reflects the monorepo structure
- team members can explain the repo in one sentence:
  - shared assets at root, QA core in `BeautyQA-core/`, trend monitoring in `BeautyQA-TrendAgent/`, external dependencies in `BeautyQA-vendor/`
