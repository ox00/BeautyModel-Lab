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
- `docs/`: active MVP working docs (minimal set)
- `docs/archive/`: legacy docs snapshots
- `feedback-20260306/`: proposal iteration and mentor discussion package
- `.github/ISSUE_TEMPLATE/`: issue templates for task splitting and collaboration

## Active docs (single entry first)
- Main entry: `docs/README.md`
- MVP scope: `docs/01-mvp-scope.md`
- Architecture: `docs/02-system-architecture.md`
- Data contract: `docs/03-data-contract.md`
- Component contract: `docs/04-component-contract.md`
- Evaluation protocol: `docs/05-eval-protocol.md`
- Roadmap and owners: `docs/06-roadmap-owner.md`
- Domain FAQ: `docs/07-domain-faq.md`

## Collaboration workflow
1. Open an issue using `.github/ISSUE_TEMPLATE/`.
2. Align scope, contract, and acceptance criteria.
3. Execute in weekly cadence and update only active docs.
4. Submit PR with required evidence (sampling/eval/risk reports).

## License / usage
This repository is for course collaboration and research communication.
Any business-sensitive dataset must follow the agreed data contract and compliance boundary.
