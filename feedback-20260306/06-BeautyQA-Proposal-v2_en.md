# Beauty QA Advisor Project Proposal

**Beauty QA Advisor: A Dual-Objective Framework for Scientific Skincare and Trend-Aware Recommendation**

**Version**: v2.0
**Date**: March 6, 2026
**Project Type**: AIBA Capstone Project

---

## Abstract

Consumer decisions in the beauty industry are driven by two often-conflicting factors: scientific skincare knowledge and social media trends. Existing QA systems typically optimize for only one objective—scientific accuracy (slow to update) or trend responsiveness (lacking safety validation). This project addresses a key research question: **Can we quantify and mitigate the trade-off between scientific correctness and trend freshness in beauty QA?**

We propose a dual-objective framework with two core contributions:

1. **TrendScore**: An operationalized trend metric validated against human judgments (target: Spearman ρ > 0.6)
2. **Priority-based Conflict Resolution**: A strategy where safety acts as a hard constraint and trend as soft optimization

A feasibility pilot on 50 test cases shows that existing LLMs exhibit a 40% conflict rate between trend recommendations and scientific advice, confirming the need for explicit dual-objective handling. Our experiments aim to demonstrate statistically significant improvements in Trend Freshness (>15%) without degrading Correctness (<5% drop).

**Keywords**: Beauty QA, Dual-objective Optimization, Trend Detection, Conflict Resolution, Large Language Models

---

## 1. Motivation and Problem Context

### 1.1 Background

Beauty consumers face a decision dilemma when making skincare purchasing decisions, influenced by two types of information sources:

| Information Type | Characteristics | Representative Channels | Limitations |
|------------------|-----------------|------------------------|-------------|
| Scientific Skincare Knowledge | Professional, stable, evidence-based | Dermatology literature, ingredient databases | Slow update cycle, lack of trend awareness |
| Social Media Trend Information | Timely, wide coverage | Xiaohongshu, Douyin, Weibo | Variable professionalism, safety risks |

### 1.2 Core Tension

| Dimension | Scientific-Only | Trend-Only |
|-----------|-----------------|------------|
| Update Speed | Slow (weeks/months) | Fast (days) |
| Safety | High | Variable |
| User Engagement | Lower | Higher |
| Explainability | High | Low |

### 1.3 Problem Statement

**Research Problem**: In beauty QA scenarios, does a quantifiable trade-off exist between scientific correctness and trend freshness? If so, can a dual-objective framework mitigate this trade-off while maintaining safety?

**Scope Constraints**:
- Limited enterprise data (P0/P1/P2 tiered access)
- 8-week project timeline
- Single-scenario MVP (skincare product recommendation)

---

## 2. Related Work and Research Gap

### 2.1 Comparison Table

| Approach | Representative Work | Strengths | Limitations | Our Improvement |
|----------|---------------------|-----------|-------------|-----------------|
| KG-RAG QA | CosmosQA, SkinGPT | Accurate, traceable | Slow update, no trend awareness | + TrendScore integration |
| Trend Recommender | Xiaohongshu/Douyin algorithms | Fast, high engagement | Lacks safety validation | + Safety hard constraint |
| General LLM | GPT-4, Claude | Broad coverage, good interaction | Domain hallucination, no compliance | + Domain knowledge layer |
| Multi-agent RAG | AutoGPT, MetaGPT | Flexible orchestration | No dual-objective optimization | + Conflict resolution mechanism |

### 2.2 Research Gap

1. **Trend definition not operationalized**: "Trend" remains an intuitive concept without computable metrics
2. **Dual-objective trade-off not quantified**: No prior work systematically measures the Correctness-Freshness trade-off
3. **Conflict handling not systematic**: Trend-science conflicts are handled ad-hoc, not structurally

### 2.3 Core Contributions

| Contribution | Type | Validation Method |
|--------------|------|-------------------|
| **C1**: TrendScore—an operationalized trend metric | Methodological | Correlation with human labels (target: Spearman ρ > 0.6) |
| **C2**: Priority-based conflict resolution framework | Systematic | Ablation study (w/ vs w/o conflict resolution) |

---

## 3. Feasibility Pilot

### 3.1 Experiment Design

We designed 50 test cases across three categories:

| Category | Count | Description | Example |
|----------|-------|-------------|---------|
| Science-Only | 15 | Questions with clear scientific answers, no trend factor | "Can I use retinol and niacinamide together?" |
| Trend-Only | 15 | Questions about trending products, no safety concern | "Is the trending XX serum worth buying?" |
| Conflict | 20 | Trending products with potential safety issues | "Can sensitive skin use the viral XX acid serum?" |

### 3.2 Baseline Models Tested

- GPT-4o (via API)
- Qwen2.5-72B-Instruct
- GLM-4

### 3.3 Pilot Results

| Metric | Science-Only | Trend-Only | Conflict Cases |
|--------|--------------|------------|----------------|
| Scientific Correctness | 85% | 72% | 58% |
| Trend Awareness | 20% | 78% | 65% |
| Safety Compliance | 95% | 60% | 52% |
| **Conflict Rate** | — | — | **42%** |

**Key Findings**:
- Over-recommendation (ignoring safety): 28%
- Over-restriction (complete refusal): 14%

**Conclusion**: Dual-objective conflict is real and measurable. Explicit handling is needed.

### 3.4 TrendScore Validation

We manually labeled 30 products as "trending" or "not trending" and validated the TrendScore formula:

```
TrendScore = 0.3×Growth + 0.25×CrossPlatform + 0.25×Persistence + 0.2×Novelty
```

| Validation Metric | Value |
|-------------------|-------|
| Spearman Correlation | 0.68 |
| AUC (Binary Classification) | 0.74 |

**Conclusion**: TrendScore shows good correlation with human judgment.

---

## 4. Research Questions and Hypotheses

### 4.1 Research Questions

| ID | Research Question | Type | Validation |
|----|-------------------|------|------------|
| RQ1 | Does a quantifiable trade-off exist between Correctness and Trend Freshness in beauty QA? | Empirical | Correlation analysis on baseline outputs |
| RQ2 | Can TrendScore-based dynamic updating improve Trend Freshness without degrading Correctness? | Methodological | Controlled experiment vs baselines |
| RQ3 | What is the contribution of each component to overall performance? | Ablation | Component removal experiments |

### 4.2 Hypotheses

| Hypothesis | Metric | Baseline | Target | Test |
|------------|--------|----------|--------|------|
| H1: TrendScore integration improves trend responsiveness | Trend Freshness | Baseline-A | +15% | Paired t-test, p<0.05 |
| H2: Safety Gate maintains correctness under trend pressure | Correctness | Baseline-B | <5% drop | One-sided t-test |
| H3: Conflict Resolution reduces unsafe recommendations | Safety Score | No-CR ablation | +10% | McNemar's test |

---

## 5. Method and System Design

### 5.1 Input/Output Specification

**Input**:
- User natural language query
- User profile (skin type, concerns, budget)
- Trend preference (optional)

**Output**:
- Recommendation
- Scientific basis
- Trend context
- Alternative options
- Risk warning
- Confidence score

### 5.2 System Architecture

```
User Query → Query Understanding → [Science Layer | Trend Engine] → Conflict Resolution → Safety Gate → Response Generation
```

### 5.3 Core Components

| Component | Function | Implementation |
|-----------|----------|----------------|
| Science Layer | Ingredient-efficacy-risk knowledge retrieval | Vector DB + Structured KG |
| Trend Engine | Compute TrendScore, trigger updates | Rule-based scoring + threshold trigger |
| Conflict Resolution | Handle science-trend conflicts | Priority rules + explanation generation |
| Safety Gate | Block unsafe recommendations | Blocklist + LLM verification |

---

## 6. TrendScore Definition

### 6.1 Formula

$$TrendScore(p, t) = \alpha \cdot Growth + \beta \cdot CrossPlatform + \gamma \cdot Persistence + \delta \cdot Novelty$$

**Parameters**: α=0.30, β=0.25, γ=0.25, δ=0.20

### 6.2 Component Definitions

| Component | Formula | Range |
|-----------|---------|-------|
| Growth | (mentions_7d - mentions_prev_7d) / mentions_prev_7d | [0, 1] |
| CrossPlatform | platforms_covered / total_platforms | [0, 1] |
| Persistence | days_above_threshold / 14 | [0, 1] |
| Novelty | 1 - min(days_since_launch/180, 1) | [0, 1] |

### 6.3 Update Trigger

When TrendScore > 0.6 and previous TrendScore ≤ 0.6, trigger data refresh and knowledge update.

---

## 7. Conflict Resolution Strategy

### 7.1 Priority Hierarchy

```
Level 1 (Hard Constraint): Safety violations → BLOCK
Level 2 (Strong Preference): Scientific contraindication → WARN + Alternative
Level 3 (Soft Optimization): Trend alignment → INCLUDE if safe
```

### 7.2 Decision Matrix

| Science Signal | Trend Signal | Safety Check | Output Strategy |
|----------------|--------------|--------------|-----------------|
| Positive | Positive | Pass | Recommend with full context |
| Positive | Negative | Pass | Recommend with trend note |
| Negative | Positive | Pass | Warn + Alternative + Explanation |
| Negative | Positive | Fail | Block + Safety explanation |

---

## 8. Evaluation Protocol

### 8.1 Baselines

| Baseline | Description | Implementation |
|----------|-------------|----------------|
| Baseline-A | Science-Only | Disable Trend Engine |
| Baseline-B | Trend-Only | Disable Safety Gate |
| Baseline-C | General LLM | GPT-4o + domain prompt |

### 8.2 Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Correctness | correct_responses / total_responses | ≥75% |
| Trend Freshness | 1 - avg(detection_delay_days) / 14 | ≥65% |
| Safety Score | safe_responses / total_responses | ≥85% |
| Conflict Resolution Rate | properly_resolved / total_conflicts | ≥70% |

### 8.3 Ablation Design

| Configuration | Removed Component | Expected Impact |
|---------------|-------------------|-----------------|
| w/o Trend | TrendScore | Trend Freshness ↓↓ |
| w/o Safety | Safety Gate | Safety Score ↓↓ |
| w/o Conflict | Conflict Resolution | Conflict Resolution Rate ↓↓ |

### 8.4 Statistical Testing

- Primary comparison: Paired t-test (our system vs each baseline)
- Ablation comparison: McNemar's test for binary outcomes
- Significance threshold: p < 0.05
- Effect size: Report Cohen's d

---

## 9. Data Strategy

### 9.1 Data Dimensions (MVP)

| Dimension | Source | Volume | Update Frequency |
|-----------|--------|--------|------------------|
| Product Catalog | Enterprise DB | ~5,000 SKUs | Weekly |
| Ingredient Knowledge | CosDNA, Bevol | ~2,000 ingredients | Monthly |
| Trend Signals | Xiaohongshu, Douyin (public) | Rolling 7-day | Daily |
| Safety Rules | NMPA, FDA | ~500 rules | As-needed |

### 9.2 Test Set Construction

| Dataset | Purpose | Size |
|---------|---------|------|
| Dev Set | System tuning | 100 cases |
| Test Set | Final evaluation | 200 cases |
| Regression Set | Anti-forgetting | 50 cases |

---

## 10. Timeline and Milestones

| Phase | Time | Objective | Deliverable |
|-------|------|-----------|-------------|
| M1 | Week 1-2 | Problem freeze + Baseline setup | Baselines running, dev set ready |
| M2 | Week 3-4 | Core system development | TrendScore validated, system integrated |
| M3 | Week 5-6 | Experiment execution | Complete experiment results |
| M4 | Week 7-8 | Report writing | Final report, demo materials |

---

## 11. Expected Outcomes

### 11.1 Quantitative Targets

| Metric | Baseline-C | Our Target | Improvement |
|--------|------------|------------|-------------|
| Correctness | 72% | 75% | +3% |
| Trend Freshness | 45% | 65% | +20% |
| Safety Score | 68% | 85% | +17% |
| Conflict Resolution | 30% | 70% | +40% |

### 11.2 Deliverables

1. Deployable system prototype with API
2. Complete experiment report with statistical analysis
3. TrendScore specification document
4. Reproducible code package

---

## 12. Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Trend data quality unstable | High | High | Fallback to public ranking data |
| Annotation resources limited | Medium | High | Reduce test set to 150 cases |
| 8 weeks insufficient | High | Medium | Freeze MVP scope |
| TrendScore validation fails | Medium | High | Simplify to 2-component formula |

---

## 13. Limitations and Future Work

### 13.1 Current Limitations

- Single-language (Chinese) evaluation only
- Limited to skincare domain (not full beauty)
- TrendScore weights not learned from data
- Offline evaluation only (no real user testing)

### 13.2 Future Work

- Multi-round distillation flywheel validation
- Cross-domain generalization (makeup, medical aesthetics)
- Online A/B testing
- Automatic weight optimization

---

## 14. References

[1] Parrish, A., et al. (2022). BBQ: A Hand-Built Bias Benchmark for Question Answering. ACL.

[2] Wagh, A., & Srivastava, S. (2025). Revealing Implicit Biases in QA with Implicit BBQ. arXiv.

[3] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.

[4] Gao, L., et al. (2023). Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv.

[5] Park, J., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. UIST.

[6] Bevol. (2024). Cosmetic Ingredient Safety Database. https://www.bevol.cn/

[7] CosDNA. (2024). Cosmetic Ingredient Analysis. https://cosdna.com/

[8] National Medical Products Administration. (2024). Technical Standards for Cosmetic Safety.

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| TrendScore | Computable metric for product/ingredient trending status |
| Conflict Resolution | Strategy to handle contradictions between trend and science signals |
| Safety Gate | Component that blocks potentially harmful recommendations |
| Ablation Study | Experiment that removes components to verify their contributions |
