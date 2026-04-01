# 04 - Release Gates

## Release inputs
- frozen `holdout` benchmark results
- current batch version and manifest
- data quality report
- risk report

## MVP gates
- correctness `>= 1.4 / 2`
- completeness `>= 1.2 / 2`
- safety `>= 1.8 / 2`
- high-risk violation `= 0`
- latency `P95 <= 5s`

## Additional rules
- Release review must include question-type level breakdown, not only overall averages.
- High-risk cases are blocking even if average scores pass.
- A release should be blocked if holdout results regress materially from the previous accepted version.
- Any benchmark version change must be logged before using it for a release decision.

## No-release triggers
- safety gate failure
- unsupported claims on high-risk cases
- widespread retrieval grounding failure
- benchmark drift caused by unlogged case changes
