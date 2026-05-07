from app.schemas.claim import ClaimSchema
from app.schemas.trusted_search import OverallStatus
from app.services.trusted_search_service import (
    derive_overall_confidence,
    derive_overall_status,
)


def test_overall_status_confirmed_when_all_confirmed() -> None:
    assert derive_overall_status([_claim("confirmed", 0.9)]) == OverallStatus.CONFIRMED


def test_overall_status_mostly_confirmed_for_confirmed_and_likely() -> None:
    claims = [_claim("confirmed", 0.85), _claim("likely", 0.70)]

    assert derive_overall_status(claims) == OverallStatus.MOSTLY_CONFIRMED


def test_overall_status_partially_confirmed_for_mixed_evidence() -> None:
    claims = [_claim("likely", 0.70), _claim("uncertain", 0.40)]

    assert derive_overall_status(claims) == OverallStatus.PARTIALLY_CONFIRMED


def test_overall_status_prioritizes_conflicting_and_false_likely() -> None:
    assert derive_overall_status([_claim("conflicting", 0.8)]) == OverallStatus.CONFLICTING
    assert derive_overall_status([_claim("false_likely", 0.8)]) == OverallStatus.LIKELY_FALSE


def test_overall_status_unsupported_when_no_supporting_claims() -> None:
    assert derive_overall_status([_claim("unsupported", 0.0)]) == OverallStatus.UNSUPPORTED
    assert derive_overall_status([]) == OverallStatus.UNSUPPORTED


def test_overall_confidence_averages_claim_confidence_and_clamps_conflicts() -> None:
    claims = [_claim("likely", 0.7), _claim("uncertain", 0.3)]
    conflicting = [_claim("conflicting", 0.9), _claim("likely", 0.8)]

    assert derive_overall_confidence(claims) == 0.5
    assert derive_overall_confidence(conflicting) == 0.60
    assert derive_overall_confidence([]) == 0.0


def _claim(status: str, confidence: float) -> ClaimSchema:
    return ClaimSchema(
        claim_id=f"c-{status}",
        claim_text="Claim text",
        claim_type="general_fact",
        status=status,
        confidence=confidence,
        reason="Reason.",
        evidence=[],
    )
