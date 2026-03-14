from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "base-line-0312"
DELIVERY_DIR = REPO_ROOT / "data" / "deliveries" / "2026-03-14-baseline-v1"
PRODUCT_FILE = RAW_DIR / "product-2026-03-12.xlsx"
INGREDIENT_FILE = RAW_DIR / "化妆品成分&功效&作用机理-knowleage.xlsx"
COMPLIANCE_DIR = RAW_DIR / "法规文件_中国"


@dataclass
class TableReport:
    name: str
    rows: int
    duplicates: int
    required_nulls: dict[str, int]
    notes: list[str]


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_tags(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    parts = re.split(r"[，,、/|；;]+", text)
    seen: list[str] = []
    for part in parts:
        item = part.strip()
        if item and item not in seen:
            seen.append(item)
    return "|".join(seen)


def normalize_timestamp(value: object, monthly_bucket: bool = False) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = normalize_text(value)
    if monthly_bucket and re.fullmatch(r"\d{6}", text):
        return f"{text[:4]}-{text[4:6]}-01 00:00:00"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return pd.to_datetime(text, format=fmt).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            continue
    try:
        parsed = pd.to_datetime(text)
    except (ValueError, TypeError):
        return ""
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def split_price_band(value: object) -> tuple[str, str, str]:
    text = normalize_text(value)
    if not text:
        return "", "", ""
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if not nums:
        return text, "", ""
    if len(nums) == 1:
        return text, nums[0], nums[0]
    return text, nums[0], nums[1]


def load_source_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    product = pd.read_excel(PRODUCT_FILE, sheet_name="product")
    review = pd.read_excel(PRODUCT_FILE, sheet_name="review_feedback")
    trend = pd.read_excel(PRODUCT_FILE, sheet_name="trend_signal")
    return product, review, trend


def build_product_table(df: pd.DataFrame) -> tuple[pd.DataFrame, TableReport]:
    renamed = df.rename(
        columns={
            "spu_id（商品id）": "product_id",
            "brand（品牌）": "brand",
            "category_lv1（一级类目）": "category_lv1",
            "category_lv2（二级类目）": "category_lv2",
            "price_band（价格带）": "price_band",
            "launch_date（上架日期）": "launch_date",
            "core_claims（核心卖点）": "core_claims",
        }
    ).copy()
    price_parts = renamed["price_band"].apply(split_price_band)
    renamed["price_band_raw"] = price_parts.apply(lambda item: item[0])
    renamed["price_min"] = price_parts.apply(lambda item: item[1])
    renamed["price_max"] = price_parts.apply(lambda item: item[2])
    renamed["launch_date"] = renamed["launch_date"].apply(normalize_timestamp)
    renamed["core_claims"] = renamed["core_claims"].apply(normalize_tags)
    renamed = renamed[
        [
            "product_id",
            "brand",
            "category_lv1",
            "category_lv2",
            "price_band_raw",
            "price_min",
            "price_max",
            "launch_date",
            "core_claims",
        ]
    ].rename(columns={"price_band_raw": "price_band"})
    report = build_report(
        name="product_sku",
        df=renamed,
        required_cols=["product_id", "brand", "category_lv1", "category_lv2", "launch_date"],
        notes=[],
    )
    return renamed, report


def build_review_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, TableReport]:
    renamed = df.rename(
        columns={
            "review_id（评论id）": "review_id",
            "spu_id（商品id）": "product_id",
            "source（来源渠道,默认taobao）": "source",
            "rating_bucket（评分，1-5分）": "rating_bucket",
            "sentiment_tag（情感标签，好坏）": "sentiment_tag",
            "effect_tags（效果标签）": "effect_tags",
            "issue_tags（问题标签）": "issue_tags",
            "content（评论内容）": "content",
            "created_at（评论时间）": "created_at",
        }
    ).copy()
    renamed["rating_bucket"] = renamed["rating_bucket"].fillna("unknown").astype(str)
    renamed["effect_tags"] = renamed["effect_tags"].apply(normalize_tags)
    renamed["issue_tags"] = renamed["issue_tags"].apply(normalize_tags)
    renamed["created_at"] = renamed["created_at"].apply(normalize_timestamp)
    renamed["content"] = renamed["content"].apply(normalize_text)

    p0 = renamed[
        [
            "review_id",
            "product_id",
            "source",
            "rating_bucket",
            "sentiment_tag",
            "effect_tags",
            "issue_tags",
            "created_at",
        ]
    ].copy()
    p1 = renamed[
        [
            "review_id",
            "product_id",
            "source",
            "rating_bucket",
            "sentiment_tag",
            "effect_tags",
            "issue_tags",
            "content",
            "created_at",
        ]
    ].copy()
    notes = []
    if (p0["rating_bucket"] == "unknown").all():
        notes.append("rating_bucket source column is empty; filled with unknown for this batch.")
    report = build_report(
        name="review_feedback",
        df=p0,
        required_cols=["review_id", "product_id", "source", "created_at"],
        notes=notes,
    )
    return p0, p1, report


def build_trend_table(df: pd.DataFrame) -> tuple[pd.DataFrame, TableReport]:
    renamed = df.rename(
        columns={
            "trend_id（趋势id）": "trend_id",
            "keyword（趋势词）": "keyword",
            "topic_cluster（话题簇）": "topic_cluster",
            "heat_index（热度指数）": "heat_index",
            "growth_md（月增长率）": "growth_monthly",
            "platform（平台,默认taobao）": "platform",
            "captured_at（采集时间）": "captured_at",
        }
    ).copy()

    def build_trend_id(row: pd.Series) -> str:
        source = "|".join(
            [
                normalize_text(row.get("keyword")),
                normalize_text(row.get("platform")),
                normalize_text(row.get("captured_at")),
            ]
        )
        return "trend_" + hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]

    renamed["captured_at"] = renamed["captured_at"].apply(lambda value: normalize_timestamp(value, monthly_bucket=True))
    renamed["keyword"] = renamed["keyword"].apply(normalize_text)
    renamed["topic_cluster"] = renamed["topic_cluster"].apply(normalize_text)
    renamed["trend_id_base"] = renamed.apply(build_trend_id, axis=1)
    renamed["trend_id_seq"] = renamed.groupby("trend_id_base").cumcount()
    renamed["trend_id"] = renamed.apply(
        lambda row: row["trend_id_base"] if row["trend_id_seq"] == 0 else f"{row['trend_id_base']}_{int(row['trend_id_seq'])}",
        axis=1,
    )
    renamed = renamed.drop(columns=["trend_id_base", "trend_id_seq"])
    report = build_report(
        name="trend_signal",
        df=renamed,
        required_cols=["trend_id", "keyword", "platform", "captured_at"],
        notes=["Source provides monthly growth (`growth_md`) and monthly capture bucket (`YYYYMM`)."],
    )
    return renamed, report


def read_xlsx_sheet_via_xml(path: Path, sheet_name: str) -> list[list[str]]:
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pkg_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

    def col_to_index(cell_ref: str) -> int:
        letters = "".join(ch for ch in cell_ref if ch.isalpha())
        index = 0
        for char in letters:
            index = index * 26 + ord(char.upper()) - 64
        return index - 1

    def cell_text(cell: ET.Element, shared: list[str]) -> str:
        inline = cell.find(f"{{{main_ns}}}is")
        if inline is not None:
            return "".join(node.text or "" for node in inline.iter(f"{{{main_ns}}}t")).strip()
        value = cell.find(f"{{{main_ns}}}v")
        if value is None or value.text is None:
            return ""
        if cell.attrib.get("t") == "s":
            return shared[int(value.text)]
        return value.text.strip()

    with ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall(f"{{{main_ns}}}si"):
                shared_strings.append("".join(node.text or "" for node in item.iter(f"{{{main_ns}}}t")).strip())

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {item.attrib["Id"]: item.attrib["Target"] for item in relationships.findall(f"{{{pkg_ns}}}Relationship")}

        target = None
        for sheet in workbook.findall(f".//{{{main_ns}}}sheet"):
            if sheet.attrib.get("name") == sheet_name:
                rel_id = sheet.attrib.get(f"{{{rel_ns}}}id")
                target = rel_map[rel_id]
                break
        if target is None:
            raise KeyError(f"Sheet not found: {sheet_name}")

        sheet_xml = target if target.startswith("xl/") else f"xl/{target}"
        root = ET.fromstring(archive.read(sheet_xml))
        rows: list[list[str]] = []
        for row in root.findall(f".//{{{main_ns}}}sheetData/{{{main_ns}}}row"):
            cells = row.findall(f"{{{main_ns}}}c")
            if not cells:
                continue
            row_values: list[str] = []
            for cell in cells:
                index = col_to_index(cell.attrib.get("r", "A1"))
                while len(row_values) <= index:
                    row_values.append("")
                row_values[index] = cell_text(cell, shared_strings)
            rows.append(row_values)
        return rows


def rows_to_dataframe(rows: list[list[str]], min_fields: int = 3) -> pd.DataFrame:
    header_index = 0
    for idx, row in enumerate(rows):
        non_empty = [item for item in row if normalize_text(item)]
        if len(non_empty) >= min_fields:
            header_index = idx
            break
    header = [normalize_text(item) for item in rows[header_index]]
    width = len(header)
    normalized_rows = []
    for row in rows[header_index + 1 :]:
        current = [normalize_text(item) for item in row[:width]]
        if len(current) < width:
            current.extend([""] * (width - len(current)))
        if any(current):
            normalized_rows.append(current)
    return pd.DataFrame(normalized_rows, columns=header)


def build_ingredient_table() -> tuple[pd.DataFrame, TableReport]:
    standard_rows = read_xlsx_sheet_via_xml(INGREDIENT_FILE, "标准成分-功效-作用机理（新）")
    relation_rows = read_xlsx_sheet_via_xml(INGREDIENT_FILE, "成分-功效-机理-文献（新）")
    standard_df = rows_to_dataframe(standard_rows)
    relation_df = rows_to_dataframe(relation_rows)

    standard = standard_df.rename(
        columns={
            "成分编号": "ingredient_id",
            "成分名称": "name_cn",
            "INCI 名称": "inci_name",
            "CAS号": "cas_no",
            "同义词，多个逗号分隔": "synonyms",
            "最新使用目的(2023)": "use_purpose_2023",
            "功效（2023）": "efficacy_2023",
            "文献验证功效": "literature_evidence",
        }
    ).copy()
    standard = standard[
        [column for column in ["ingredient_id", "name_cn", "inci_name", "cas_no", "synonyms", "use_purpose_2023", "efficacy_2023", "literature_evidence"] if column in standard.columns]
    ]

    relation = relation_df.rename(
        columns={
            "成分编号": "ingredient_id",
            "功效": "efficacy_relation",
            "机理（旧）": "mechanism_legacy",
            "机理序号1": "mechanism_id_1",
            "参考资料": "reference_1",
            "机理序号2": "mechanism_id_2",
            "参考资料2": "reference_2",
        }
    ).copy()
    keep_cols = [column for column in ["ingredient_id", "efficacy_relation", "mechanism_legacy", "mechanism_id_1", "reference_1", "mechanism_id_2", "reference_2"] if column in relation.columns]
    relation = relation[keep_cols]

    def collapse(values: Iterable[object]) -> str:
        items: list[str] = []
        for value in values:
            item = normalize_text(value)
            if item and item not in items:
                items.append(item)
        return "|".join(items)

    relation_grouped = relation.groupby("ingredient_id", dropna=False).agg(collapse).reset_index()
    merged = standard.merge(relation_grouped, on="ingredient_id", how="left")
    report = build_report(
        name="ingredient_knowledge",
        df=merged,
        required_cols=["ingredient_id", "name_cn", "inci_name"],
        notes=["Ingredient workbook was parsed via XML because the source xlsx has style metadata incompatible with openpyxl read mode."],
    )
    return merged, report


def build_compliance_manifest() -> pd.DataFrame:
    records = []
    for path in sorted(COMPLIANCE_DIR.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        category = "regulation_doc"
        if "原料目录" in relative_path:
            category = "ingredient_regulation"
        records.append(
            {
                "source_file": relative_path,
                "file_type": path.suffix.lower().lstrip("."),
                "category": category,
                "jurisdiction": "CN",
                "processing_status": "raw_reference",
            }
        )
    return pd.DataFrame(records)


def build_report(name: str, df: pd.DataFrame, required_cols: list[str], notes: list[str]) -> TableReport:
    required_nulls: dict[str, int] = {}
    for column in required_cols:
        if column not in df.columns:
            required_nulls[column] = len(df)
            continue
        required_nulls[column] = int(df[column].apply(lambda value: normalize_text(value) == "").sum())
    duplicates = 0
    primary = required_cols[0] if required_cols else None
    if primary and primary in df.columns:
        duplicates = int(df[primary].duplicated().sum())
    return TableReport(name=name, rows=int(len(df)), duplicates=duplicates, required_nulls=required_nulls, notes=notes)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def write_manifest(manifest_rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(manifest_rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_quality_report(reports: list[TableReport], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Baseline 0312 Quality Report", ""]
    for report in reports:
        lines.append(f"## {report.name}")
        lines.append(f"- rows: {report.rows}")
        lines.append(f"- duplicates on primary key: {report.duplicates}")
        null_desc = ", ".join(f"{key}={value}" for key, value in report.required_nulls.items())
        lines.append(f"- required field null counts: {null_desc}")
        if report.notes:
            for note in report.notes:
                lines.append(f"- note: {note}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_readme(path: Path) -> None:
    content = """# Baseline 0312 Delivery

This folder contains the cleaned delivery package for the baseline batch imported on 2026-03-14.

## Structure
- `p0/`: safe structured package for training and team sharing
- `p1/`: restricted package containing raw review text
- `refs/`: source manifests and reference-only materials
- `reports/`: quality report and batch manifest

## Notes
- `review_feedback` source ratings are empty in this batch; the cleaned package keeps `rating_bucket=unknown`.
- `trend_signal` source uses monthly growth and monthly capture buckets; cleaned timestamps are normalized to the first day of the month.
- `ingredient_knowledge` is parsed from the source workbook via XML because the original workbook styles are not fully compatible with `openpyxl` read mode.
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    product_raw, review_raw, trend_raw = load_source_tables()
    product, product_report = build_product_table(product_raw)
    review_p0, review_p1, review_report = build_review_tables(review_raw)
    trend, trend_report = build_trend_table(trend_raw)
    ingredient, ingredient_report = build_ingredient_table()
    compliance_manifest = build_compliance_manifest()

    write_csv(product, DELIVERY_DIR / "p0" / "product_sku.csv")
    write_csv(review_p0, DELIVERY_DIR / "p0" / "review_feedback.csv")
    write_csv(trend, DELIVERY_DIR / "p0" / "trend_signal.csv")
    write_csv(ingredient, DELIVERY_DIR / "p0" / "ingredient_knowledge.csv")
    write_csv(review_p1, DELIVERY_DIR / "p1" / "review_feedback_raw.csv")
    write_csv(compliance_manifest, DELIVERY_DIR / "refs" / "compliance_source_manifest.csv")

    manifest_rows = [
        {"table_name": "product_sku", "level": "P0", "rows": len(product), "path": "p0/product_sku.csv"},
        {"table_name": "review_feedback", "level": "P0", "rows": len(review_p0), "path": "p0/review_feedback.csv"},
        {"table_name": "trend_signal", "level": "P0", "rows": len(trend), "path": "p0/trend_signal.csv"},
        {"table_name": "ingredient_knowledge", "level": "P0", "rows": len(ingredient), "path": "p0/ingredient_knowledge.csv"},
        {"table_name": "review_feedback_raw", "level": "P1", "rows": len(review_p1), "path": "p1/review_feedback_raw.csv"},
        {"table_name": "compliance_source_manifest", "level": "REF", "rows": len(compliance_manifest), "path": "refs/compliance_source_manifest.csv"},
    ]
    write_manifest(manifest_rows, DELIVERY_DIR / "reports" / "data_manifest.csv")
    write_quality_report(
        [product_report, review_report, trend_report, ingredient_report],
        DELIVERY_DIR / "reports" / "quality_report.md",
    )
    write_readme(DELIVERY_DIR / "README.md")


if __name__ == "__main__":
    main()
