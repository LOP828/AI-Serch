from datetime import UTC, datetime

from app.schemas.evidence import EvidenceSchema, SupportType
from app.schemas.source import SourceSchema
from app.services.reliability_scorer import ReliabilityScorer


def test_official_model_card_high_relevance_gets_high_score() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=0.90, source_id="s1")
    source = _source(
        source_id="s1",
        source_type="official_model_card",
        base_reliability=0.88,
        is_primary_source=True,
    )

    scored = scorer.score_evidence(evidence, source)

    assert scored.final_score == 0.8712
    assert scored.source_score == 0.88


def test_community_forum_scores_lower_than_official_model_card() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=0.90, source_id="s1")
    official = _source("s1", "official_model_card", 0.88, True)
    community = _source("s1", "community_forum", 0.40, False)

    official_scored = scorer.score_evidence(evidence, official)
    community_scored = scorer.score_evidence(evidence, community)

    assert community_scored.final_score < official_scored.final_score
    assert community_scored.final_score == 0.36


def test_primary_source_factor_adds_boost() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=0.70, source_id="s1")
    source = _source("s1", "academic_paper", 0.90, True)

    scored = scorer.score_evidence(evidence, source)

    assert scored.primary_source_factor == 1.10
    assert scored.final_score == 0.693


def test_final_score_is_clamped_to_one() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=1.0, source_id="s1")
    source = _source(
        "s1",
        "government_docs",
        0.95,
        True,
        published_at="2026-05-01T00:00:00Z",
    )

    scored = scorer.score_evidence(evidence, source)

    assert scored.final_score == 1.0


def test_score_breakdown_contains_expected_fields() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=0.82, source_id="s1")
    source = _source("s1", "source_code_repo", 0.88, True)

    scored = scorer.score_evidence(evidence, source)

    assert scored.score_breakdown == {
        "relevance_score": 0.82,
        "source_base_score": 0.88,
        "primary_source_factor": 1.10,
        "recency_factor": 1.00,
        "final_score": 0.7938,
    }


def test_missing_source_is_scored_safely() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))
    evidence = _evidence(relevance_score=0.80, source_id="missing")

    scored = scorer.score_evidence(evidence, None)

    assert scored.source_score == 0.30
    assert scored.primary_source_factor == 0.90
    assert scored.recency_factor == 1.00
    assert scored.final_score == 0.216


def test_recency_factor_handles_new_and_old_dates() -> None:
    scorer = ReliabilityScorer(now=datetime(2026, 5, 6, tzinfo=UTC))

    assert scorer.recency_factor_for(None) == 1.00
    assert scorer.recency_factor_for("2026-05-01T00:00:00Z") == 1.05
    assert scorer.recency_factor_for("2020-01-01T00:00:00Z") == 0.80
    assert scorer.recency_factor_for("2010-01-01T00:00:00Z") == 0.60


def _evidence(relevance_score: float, source_id: str) -> EvidenceSchema:
    return EvidenceSchema(
        evidence_id="e1",
        claim_id="c1",
        source_id=source_id,
        evidence_text="Evidence text.",
        support_type=SupportType.SUPPORT,
        relevance_score=relevance_score,
    )


def _source(
    source_id: str,
    source_type: str,
    base_reliability: float,
    is_primary_source: bool,
    published_at: str | None = None,
) -> SourceSchema:
    return SourceSchema(
        source_id=source_id,
        title="Source",
        url="https://example.com/source",
        domain="example.com",
        source_type=source_type,
        base_reliability=base_reliability,
        is_primary_source=is_primary_source,
        published_at=published_at,
    )
