# BeautyModel-Lab

BeautyModel-Lab is a course collaboration workspace for a beauty recommendation project focused on two scenarios:
- Scientific skincare recommendation (skin concern -> ingredient/product suggestions)
- Trend-aware recommendation (hot keywords -> similar/alternative product suggestions)

The repo is designed for limited, compliant data supply and iterative model improvement.

## Project goals
- Build a reproducible MVP with constrained enterprise data.
- Use a stable loop: data sampling -> distillation/update -> evaluation -> release.
- Keep outputs explainable, safe, and aligned with compliance rules.

## Repository structure
- `docs/`: project guidance and operating standards
- `.github/ISSUE_TEMPLATE/`: issue templates for task splitting and collaboration

## Docs quick links
- Data support package index: `docs/00-README-数据支持包.md`
- Data supply and grading policy: `docs/01-数据供给与分级策略.md`
- Data dictionary template: `docs/02-数据字典模板.md`
- Two-week iteration SOP: `docs/03-两周迭代SOP.md`
- Evaluation and release gates: `docs/04-评测与发布门槛.md`
- Data budget example: `docs/05-data_budget.yaml.example`
- Sampling report template: `docs/06-sampling_report-template.md`
- Data quality report template: `docs/07-data_quality_report-template.md`
- Data/ sampling technical design: `docs/08-技术方案-数据维度与采样设计.md`
- Distillation flywheel technical design: `docs/09-技术方案-蒸馏与多轮对撞飞轮.md`
- Experiment design and milestones: `docs/10-实验设计与里程碑.md`

## Collaboration workflow
1. Open an issue using the templates in `.github/ISSUE_TEMPLATE/`.
2. Align scope, data budget, and acceptance criteria.
3. Execute in a 2-week iteration and update docs/reports.
4. Submit PR with evidence (sampling/eval/risk reports).

## License / usage
This repository is for course collaboration and research communication.
Any business-sensitive dataset must follow the agreed data contract and compliance boundary.
