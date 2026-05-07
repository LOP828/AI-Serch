from app.schemas.claim import ClaimStatus
from app.schemas.evidence import EvidenceSchema, SupportType
from app.services.claim_aggregator import ClaimAggregator
from app.services.claim_decomposer import ClaimDraft


def test_high_support_evidence_confirms_claim() -> None:
    result = _aggregate([_evidence(SupportType.SUPPORT, 0.85)])

    assert result.status == ClaimStatus.CONFIRMED
    assert result.confidence == 0.85
    assert result.reason


def test_medium_support_evidence_makes_claim_likely() -> None:
    result = _aggregate([_evidence(SupportType.SUPPORT, 0.70)])

    assert result.status == ClaimStatus.LIKELY
    assert result.confidence == 0.70
    assert result.reason


def test_partial_or_low_support_evidence_makes_claim_uncertain() -> None:
    partial = _aggregate([_evidence(SupportType.PARTIAL, 0.62)])
    low_support = _aggregate([_evidence(SupportType.SUPPORT, 0.40)])

    assert partial.status == ClaimStatus.UNCERTAIN
    assert low_support.status == ClaimStatus.UNCERTAIN
    assert partial.confidence == 0.62
    assert low_support.confidence == 0.40


def test_no_evidence_makes_claim_unsupported() -> None:
    result = _aggregate([])

    assert result.status == ClaimStatus.UNSUPPORTED
    assert result.confidence == 0.0
    assert result.reason == "No relevant supporting evidence was found."


def test_high_support_and_oppose_evidence_makes_claim_conflicting() -> None:
    result = _aggregate(
        [
            _evidence(SupportType.SUPPORT, 0.74),
            _evidence(SupportType.OPPOSE, 0.72),
        ]
    )

    assert result.status == ClaimStatus.CONFLICTING
    assert result.confidence == 0.74
    assert "supporting and opposing" in result.reason


def test_high_oppose_without_same_level_support_makes_claim_false_likely() -> None:
    result = _aggregate(
        [
            _evidence(SupportType.OPPOSE, 0.78),
            _evidence(SupportType.SUPPORT, 0.50),
        ]
    )

    assert result.status == ClaimStatus.FALSE_LIKELY
    assert result.confidence == 0.78
    assert result.reason


def test_missing_final_score_is_safe() -> None:
    result = _aggregate([_evidence(SupportType.SUPPORT, None)])

    assert result.status == ClaimStatus.UNCERTAIN
    assert result.confidence == 0.0
    assert result.reason


def test_aggregate_groups_evidence_by_claim_id() -> None:
    claims = [
        ClaimDraft("c1", "Claim 1", "general_fact"),
        ClaimDraft("c2", "Claim 2", "general_fact"),
    ]
    evidence = [
        _evidence(SupportType.SUPPORT, 0.82, claim_id="c1"),
        _evidence(SupportType.OPPOSE, 0.80, claim_id="c2"),
    ]

    results = ClaimAggregator().aggregate(claims, evidence)

    assert results["c1"].status == ClaimStatus.CONFIRMED
    assert results["c2"].status == ClaimStatus.FALSE_LIKELY


def _aggregate(evidence: list[EvidenceSchema]):
    claim = ClaimDraft("c1", "Claim text", "general_fact")
    return ClaimAggregator().aggregate_claim(claim, evidence)


def _evidence(
    support_type: SupportType,
    final_score: float | None,
    claim_id: str = "c1",
) -> EvidenceSchema:
    return EvidenceSchema(
        evidence_id=f"e-{claim_id}-{support_type}",
        claim_id=claim_id,
        source_id="s1",
        evidence_text="Evidence text.",
        support_type=support_type,
        relevance_score=0.8,
        final_score=final_score,
    )
