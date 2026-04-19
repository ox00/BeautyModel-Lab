from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from .models import TrendEvidence, TrendSignal

_DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class TrendRetrievalConfig:
    freshness_days: int = 7
    min_trend_score: float = 30.0
    min_confidence_for_strong: frozenset[str] = frozenset({"medium", "high"})
    blocked_risk_for_strong: frozenset[str] = frozenset({"high"})


class TrendSignalRepository:
    """Read-only first-party trend_signal repository for QA use."""

    def __init__(self, signals: list[TrendSignal], config: TrendRetrievalConfig | None = None) -> None:
        self._signals = signals
        self._config = config or TrendRetrievalConfig()

    @classmethod
    def from_contract_csv(
        cls,
        csv_path: str | Path,
        *,
        now: datetime | None = None,
        config: TrendRetrievalConfig | None = None,
    ) -> "TrendSignalRepository":
        rows = _read_csv_rows(csv_path)
        first_row = rows[0] if rows else {}
        if "signal_id" not in first_row:
            raise ValueError("Runtime ingestion requires first-party trend_signal contract schema (signal_id required).")

        inferred_now = now or datetime.now()
        active_config = config or TrendRetrievalConfig()
        signals = [_parse_contract_row(row, inferred_now, active_config) for row in rows]
        return cls(signals, config=config)

    @classmethod
    def from_contract_json(
        cls,
        json_path: str | Path,
        *,
        now: datetime | None = None,
        config: TrendRetrievalConfig | None = None,
    ) -> "TrendSignalRepository":
        payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        rows = payload.get("results", [])
        if rows:
            first_row = rows[0]
            if "signal_id" not in first_row:
                raise ValueError("Runtime ingestion requires first-party trend_signal contract schema (signal_id required).")
        inferred_now = now or datetime.now()
        active_config = config or TrendRetrievalConfig()
        signals = [_parse_contract_json_row(row, inferred_now, active_config) for row in rows]
        return cls(signals, config=config)

    @classmethod
    def from_legacy_csv_for_migration(
        cls,
        csv_path: str | Path,
        *,
        now: datetime | None = None,
        config: TrendRetrievalConfig | None = None,
    ) -> "TrendSignalRepository":
        rows = _read_csv_rows(csv_path)
        first_row = rows[0] if rows else {}
        if "trend_id" not in first_row:
            raise ValueError("Legacy migration loader expects legacy trend_id CSV schema.")

        inferred_now = now or datetime.now()
        active_config = config or TrendRetrievalConfig()
        signals = [_parse_legacy_row(row, inferred_now, active_config) for row in rows]
        return cls(signals, config=config)

    def retrieve_for_query(self, query: str, *, now: datetime | None = None, limit: int = 5) -> list[TrendEvidence]:
        now_dt = now or datetime.now()
        query_lower = query.strip().lower()
        terms = [t.strip().lower() for t in query.split() if t.strip()]
        if not terms and query_lower:
            terms = [query_lower]

        scored: list[tuple[float, TrendSignal]] = []
        for signal in self._signals:
            text = " ".join(
                [
                    signal.normalized_keyword,
                    signal.topic_cluster,
                    signal.trend_type,
                    signal.signal_summary,
                    signal.signal_evidence,
                ]
            ).lower()
            overlap = sum(1 for t in terms if t in text)
            if signal.normalized_keyword.lower() in query_lower:
                overlap += 2
            elif query_lower and query_lower in signal.normalized_keyword.lower():
                overlap += 1
            if overlap == 0:
                continue
            score = overlap * 100.0 + signal.trend_score
            scored.append((score, signal))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_signals = [s for _, s in scored[:limit]]
        return [self._to_evidence(signal, now_dt) for signal in top_signals]

    def _to_evidence(self, signal: TrendSignal, now_dt: datetime) -> TrendEvidence:
        is_stale = signal.fresh_until < now_dt
        confidence_ok = signal.confidence in self._config.min_confidence_for_strong
        score_ok = signal.trend_score >= self._config.min_trend_score
        blocked_by_safety = signal.risk_flag in self._config.blocked_risk_for_strong
        usable = (not is_stale) and confidence_ok and score_ok and (not blocked_by_safety)

        reason: str | None = None
        if not usable:
            bits: list[str] = []
            if is_stale:
                bits.append("stale")
            if not confidence_ok:
                bits.append("low_confidence")
            if not score_ok:
                bits.append("low_trend_score")
            if blocked_by_safety:
                bits.append("high_risk_blocked")
            reason = ",".join(bits)

        return TrendEvidence(
            signal=signal,
            is_stale=is_stale,
            usable_as_strong_evidence=usable,
            blocked_by_safety=blocked_by_safety,
            rejection_reason=reason,
        )


def _read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _parse_datetime(value: str) -> datetime:
    trimmed = value.strip()
    for fmt in _DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(trimmed, fmt)
            if parsed.tzinfo is not None:
                return parsed.replace(tzinfo=None)
            return parsed
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(trimmed)
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed
    except ValueError as exc:
        raise ValueError(f"Unsupported datetime format: {value}") from exc


def _parse_contract_row(row: dict[str, str], now_dt: datetime, config: TrendRetrievalConfig) -> TrendSignal:
    observed = _parse_datetime(row["observed_at"])
    fresh_until_raw = row.get("fresh_until", "").strip()
    fresh_until = _parse_datetime(fresh_until_raw) if fresh_until_raw else observed + timedelta(days=config.freshness_days)

    return TrendSignal(
        signal_id=row["signal_id"],
        keyword_id=row["keyword_id"],
        crawl_task_id=str(row["crawl_task_id"]),
        normalized_keyword=row["normalized_keyword"],
        topic_cluster=row["topic_cluster"],
        trend_type=row["trend_type"],
        signal_summary=row["signal_summary"],
        signal_evidence=row["signal_evidence"],
        source_platform=row["source_platform"],
        source_url=row["source_url"],
        trend_score=float(row["trend_score"]),
        confidence=row["confidence"].lower(),
        risk_flag=row["risk_flag"].lower(),
        observed_at=observed,
        fresh_until=fresh_until,
    )


def _parse_contract_json_row(row: dict[str, object], now_dt: datetime, config: TrendRetrievalConfig) -> TrendSignal:
    observed = _parse_datetime(str(row["observed_at"]))
    fresh_until_raw = str(row.get("fresh_until", "")).strip()
    fresh_until = _parse_datetime(fresh_until_raw) if fresh_until_raw else observed + timedelta(days=config.freshness_days)

    return TrendSignal(
        signal_id=str(row["signal_id"]),
        keyword_id=str(row["keyword_id"]),
        crawl_task_id=str(row["crawl_task_id"]),
        normalized_keyword=str(row["normalized_keyword"]),
        topic_cluster=str(row["topic_cluster"]),
        trend_type=str(row["trend_type"]),
        signal_summary=str(row["signal_summary"]),
        signal_evidence=str(row["signal_evidence"]),
        source_platform=str(row["source_platform"]),
        source_url=str(row["source_url"]),
        trend_score=float(row["trend_score"]),
        confidence=str(row["confidence"]).lower(),
        risk_flag=str(row["risk_flag"]).lower(),
        observed_at=observed,
        fresh_until=fresh_until,
    )


def _parse_legacy_row(row: dict[str, str], now_dt: datetime, config: TrendRetrievalConfig) -> TrendSignal:
    captured = _parse_datetime(row["captured_at"])
    growth = float(row.get("growth_monthly") or 0.0)
    heat = float(row.get("heat_index") or 0.0)
    trend_score = min(100.0, max(0.0, heat / 100.0 + growth / 20.0))
    confidence = "high" if heat >= 1000 else "medium" if heat >= 200 else "low"

    return TrendSignal(
        signal_id=row["trend_id"],
        keyword_id=f"legacy_kw_{row['keyword']}",
        crawl_task_id="legacy_p0",
        normalized_keyword=row["keyword"],
        topic_cluster=row.get("topic_cluster", "unknown"),
        trend_type="category",
        signal_summary=f"Legacy trend signal for {row['keyword']} from {row['platform']}",
        signal_evidence=f"captured heat_index={row['heat_index']}, growth_monthly={row['growth_monthly']}",
        source_platform=row["platform"],
        source_url="legacy://trend_signal.csv",
        trend_score=trend_score,
        confidence=confidence,
        risk_flag="medium",
        observed_at=captured,
        fresh_until=captured + timedelta(days=config.freshness_days),
    )
