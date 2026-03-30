from typing import Optional
from pydantic import BaseModel, Field

class ProductSKU(BaseModel):
    product_id: str
    brand: Optional[str] = None
    category_lv1: Optional[str] = None
    category_lv2: Optional[str] = None
    price_band: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    launch_date: Optional[str] = None
    core_claims: Optional[str] = None

class IngredientKnowledge(BaseModel):
    ingredient_id: str
    name_cn: Optional[str] = None
    inci_name: Optional[str] = None
    cas_no: Optional[str] = None
    synonyms: Optional[str] = None
    use_purpose_2023: Optional[str] = None
    efficacy_2023: Optional[str] = None
    literature_evidence: Optional[str] = None
    efficacy_relation: Optional[str] = None
    mechanism_legacy: Optional[str] = None
    mechanism_id_1: Optional[str] = None
    reference_1: Optional[str] = None
    mechanism_id_2: Optional[str] = None
    reference_2: Optional[str] = None

class ComplianceRule(BaseModel):
    rule_id: str
    jurisdiction: Optional[str] = None
    source_category: Optional[str] = None
    source_title: Optional[str] = None
    source_file: Optional[str] = None
    source_sheet: Optional[str] = None
    effective_date: Optional[str] = None
    rule_type: Optional[str] = None
    rule_level: Optional[str] = None
    chapter: Optional[str] = None
    article_no: Optional[str] = None
    entity_name_cn: Optional[str] = None
    entity_name_en: Optional[str] = None
    inci_name: Optional[str] = None
    cas_no: Optional[str] = None
    applicable_scope: Optional[str] = None
    limit_value: Optional[str] = None
    warning_text: Optional[str] = None
    requirement_text: Optional[str] = None
    remarks: Optional[str] = None

class ReviewFeedback(BaseModel):
    review_id: str
    product_id: str
    source: Optional[str] = None
    rating_bucket: Optional[str] = None
    sentiment_tag: Optional[str] = None
    effect_tags: Optional[str] = None
    issue_tags: Optional[str] = None
    created_at: Optional[str] = None

class TrendSignal(BaseModel):
    trend_id: str
    keyword: str
    topic_cluster: Optional[str] = None
    heat_index: Optional[float] = None
    growth_monthly: Optional[float] = None
    platform: Optional[str] = None
    captured_at: Optional[str] = None
