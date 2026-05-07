from datetime import UTC, datetime

from app.schemas.evidence import EvidenceSchema
from app.schemas.source import SourceSchema

PRIMARY_SOURCE_FACTOR = 1.10
SECONDARY_SOURCE_FACTOR = 1.00
UNKNOWN_SOURCE_FACTOR = 0.90


class ReliabilityScorer:
    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime.now(UTC)

    def score_evidence(
        self,
        evidence: EvidenceSchema,
        source: SourceSchema | None,
    ) -> EvidenceSchema:
        source_base_score = source.base_reliability if source else 0.30
        primary_source_factor = primary_factor_for(source)
        recency_factor = self.recency_factor_for(source.published_at if source else None)
        final_score = clamp_score(
            evidence.relevance_score
            * source_base_score
            * primary_source_factor
            * recency_factor
        )

        return evidence.model_copy(
            update={
                "source_score": source_base_score,
                "primary_source_factor": primary_source_factor,
                "recency_factor": recency_factor,
                "final_score": final_score,
                "score_breakdown": {
                    "relevance_score": evidence.relevance_score,
                    "source_base_score": source_base_score,
                    "primary_source_factor": primary_source_factor,
                    "recency_factor": recency_factor,
                    "final_score": final_score,
                },
            }
        )

    def score_evidence_items(
        self,
        evidence_items: list[EvidenceSchema],
        sources_by_id: dict[str, SourceSchema],
    ) -> list[EvidenceSchema]:
        return [
            self.score_evidence(evidence, sources_by_id.get(evidence.source_id))
            for evidence in evidence_items
        ]

    def recency_factor_for(self, published_at: str | None) -> float:
        if not published_at:
            return 1.00

        published_datetime = parse_datetime(published_at)
        if not published_datetime:
            return 1.00

        age_days = (self._now - published_datetime).days
        if age_days <= 365:
            return 1.05
        if age_days <= 365 * 3:
            return 1.00
        if age_days <= 365 * 8:
            return 0.80
        return 0.60


def primary_factor_for(source: SourceSchema | None) -> float:
    if source is None:
        return UNKNOWN_SOURCE_FACTOR
    if source.is_primary_source:
        return PRIMARY_SOURCE_FACTOR
    return SECONDARY_SOURCE_FACTOR


def parse_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def clamp_score(value: float) -> float:
    return max(0.0, min(round(value, 4), 1.0))
