# Data Quality Report Template

## 1. Metadata
- Iteration:
- Report owner:
- Generated at:
- Input manifest:

## 2. Quality Gates (Pass/Fail)
| Gate | Threshold | Actual | Pass/Fail |
|---|---|---:|---|
| Primary key uniqueness | 100% |  |  |
| Field completeness | >=95% |  |  |
| Duplicate rate | <=2% |  |  |
| Timestamp validity | >=98% |  |  |
| Trend freshness | <=7 days |  |  |
| Compliance rule load success | 100% |  |  |

## 3. Table-Level Profile
| Table | Row count | Null rate | Duplicate rate | Freshness | Notes |
|---|---:|---:|---:|---|---|
| product_sku |  |  |  |  |  |
| ingredient_knowledge |  |  |  |  |  |
| review_feedback |  |  |  |  |  |
| trend_signal |  |  |  |  |  |
| compliance_rule |  |  |  |  |  |

## 4. Field-Level Critical Checks
### 4.1 product_sku
| Field | Null rate | Invalid rate | Notes |
|---|---:|---:|---|
| sku_id |  |  |  |
| category_l1 |  |  |  |
| price_band |  |  |  |
| efficacy_tags |  |  |  |
| inci_list |  |  |  |

### 4.2 review_feedback
| Field | Null rate | Invalid rate | Notes |
|---|---:|---:|---|
| review_id |  |  |  |
| sku_id |  |  |  |
| review_date |  |  |  |
| sentiment |  |  |  |
| risk_terms |  |  |  |

## 5. Distribution Drift (Optional but recommended)
- Compare with previous iteration:
  - Category ratio drift:
  - Price band drift:
  - Sentiment drift:
  - Trend keyword overlap:

## 6. Issues Found
| Severity | Issue | Impact | Fix action | Owner | ETA |
|---|---|---|---|---|---|
| High/Med/Low |  |  |  |  |  |

## 7. Remediation Summary
- Fixed before training:
- Deferred to next iteration:

## 8. Release Decision
- Data quality status: PASS / FAIL
- Blockers:
- Approved by:
