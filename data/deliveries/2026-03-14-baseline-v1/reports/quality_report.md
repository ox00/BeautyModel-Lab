# Baseline 0312 Quality Report

## product_sku
- rows: 1000
- duplicates on primary key: 0
- required field null counts: product_id=0, brand=0, category_lv1=0, category_lv2=0, launch_date=0

## review_feedback
- rows: 29698
- duplicates on primary key: 0
- required field null counts: review_id=0, product_id=0, source=0, created_at=0
- note: rating_bucket source column is empty; filled with unknown for this batch.

## trend_signal
- rows: 300
- duplicates on primary key: 0
- required field null counts: trend_id=0, keyword=0, platform=0, captured_at=0
- note: Source provides monthly growth (`growth_md`) and monthly capture bucket (`YYYYMM`).

## ingredient_knowledge
- rows: 8985
- duplicates on primary key: 0
- required field null counts: ingredient_id=0, name_cn=0, inci_name=43
- note: Ingredient workbook was parsed via XML because the source xlsx has style metadata incompatible with openpyxl read mode.
