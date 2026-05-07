from app.schemas.conflict import ConflictSeverity
from app.schemas.evidence import EvidenceSchema, SupportType
from app.services.claim_decomposer import ClaimDraft
from app.services.conflict_detector import ConflictDetector


def test_high_support_and_oppose_generates_conflict() -> None:
    conflicts = ConflictDetector().detect(
        [_claim("c1")],
        [
            _evidence("e1", "c1", SupportType.SUPPORT, 0.75),
            _evidence("e2", "c1", SupportType.OPPOSE, 0.72),
        ],
    )

    assert len(conflicts) == 1
    assert conflicts[0].claim_id == "c1"
    assert conflicts[0].supporting_evidence_ids == ["e1"]
    assert conflicts[0].opposing_evidence_ids == ["e2"]
    assert conflicts[0].severity == ConflictSeverity.MINOR
    assert conflicts[0].summary


def test_low_oppose_does_not_generate_conflict() -> None:
    conflicts = ConflictDetector().detect(
        [_claim("c1")],
        [
            _evidence("e1", "c1", SupportType.SUPPORT, 0.82),
            _evidence("e2", "c1", SupportType.OPPOSE, 0.40),
        ],
    )

    assert conflicts == []


def test_only_conflicting_claim_generates_conflict() -> None:
    conflicts = ConflictDetector().detect(
        [_claim("c1"), _claim("c2")],
        [
            _evidence("e1", "c1", SupportType.SUPPORT, 0.82),
            _evidence("e2", "c1", SupportType.OPPOSE, 0.81),
            _evidence("e3", "c2", SupportType.SUPPORT, 0.90),
        ],
    )

    assert len(conflicts) == 1
    assert conflicts[0].claim_id == "c1"


def test_major_severity_requires_both_sides_at_least_point_eight() -> None:
    major = ConflictDetector().detect(
        [_claim("c1")],
        [
            _evidence("e1", "c1", SupportType.SUPPORT, 0.82),
            _evidence("e2", "c1", SupportType.OPPOSE, 0.81),
        ],
    )
    minor = ConflictDetector().detect(
        [_claim("c1")],
        [
            _evidence("e1", "c1", SupportType.SUPPORT, 0.82),
            _evidence("e2", "c1", SupportType.OPPOSE, 0.71),
        ],
    )

    assert major[0].severity == ConflictSeverity.MAJOR
    assert minor[0].severity == ConflictSeverity.MINOR


def _claim(claim_id: str) -> ClaimDraft:
    return ClaimDraft(claim_id=claim_id, claim_text="Claim text", claim_type="general_fact")


def _evidence(
    evidence_id: str,
    claim_id: str,
    support_type: SupportType,
    final_score: float,
) -> EvidenceSchema:
    return EvidenceSchema(
        evidence_id=evidence_id,
        claim_id=claim_id,
        source_id="s1",
        evidence_text="Evidence text.",
        support_type=support_type,
        relevance_score=0.8,
        final_score=final_score,
    )
