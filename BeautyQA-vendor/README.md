# Third-Party Dependencies

This directory stores external codebases used by the project.

Current contents:
- `MediaCrawler/` - upstream crawler engine used by `BeautyQA-TrendAgent/`

Working rule:
- do not mix project-owned business logic into this directory
- upgrade or replace third-party code here explicitly
- keep project integration logic in first-party modules such as `BeautyQA-TrendAgent/`
