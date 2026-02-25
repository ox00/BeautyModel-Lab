# Contributing Guide

Thanks for contributing to BeautyModel-Lab.

## 1) Before you start
- Read `README.md` and `docs/00-README-数据支持包.md`.
- Confirm your task has a linked Issue.
- Do not upload raw sensitive data or PII.

## 2) Branch and commit
- Branch naming:
  - `feat/<short-topic>`
  - `docs/<short-topic>`
  - `fix/<short-topic>`
- Commit message style:
  - `feat: ...`
  - `docs: ...`
  - `fix: ...`
  - `chore: ...`

## 3) Pull request requirements
Each PR should include:
- What changed and why.
- Linked issue.
- Affected docs/files.
- Validation evidence (when relevant):
  - sampling report
  - data quality report
  - eval report
  - risk/compliance notes

## 4) Data and compliance rules
- Follow `docs/01-数据供给与分级策略.md`.
- Respect P0/P1/P2 boundaries.
- If in doubt, provide aggregated features instead of raw text.
- Do not share data externally beyond approved course collaboration.

## 5) Review checklist
- [ ] Scope matches issue acceptance criteria.
- [ ] No sensitive raw data committed.
- [ ] Docs updated if process/schema changed.
- [ ] Quality gates considered (`docs/04-评测与发布门槛.md`).
