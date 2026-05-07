from app.schemas.conflict import ConflictSchema, ConflictSeverity
from app.schemas.evidence import EvidenceSchema, SupportType
from app.services.claim_decomposer import ClaimDraft

CONFLICT_SCORE_THRESHOLD = 0.70
MAJOR_CONFLICT_SCORE_THRESHOLD = 0.80


class ConflictDetector:
    def detect(
        self,
        claims: list[ClaimDraft],
        evidence_items: list[EvidenceSchema],
    ) -> list[ConflictSchema]:
        evidence_by_claim_id = _group_evidence_by_claim_id(evidence_items)
        conflicts: list[ConflictSchema] = []
        for claim in claims:
            evidence_for_claim = evidence_by_claim_id.get(claim.claim_id, [])
            support = _high_scoring_evidence(evidence_for_claim, SupportType.SUPPORT)
            oppose = _high_scoring_evidence(evidence_for_claim, SupportType.OPPOSE)
            if not support or not oppose:
                continue

            conflicts.append(
                ConflictSchema(
                    conflict_id=f"conflict-{len(conflicts) + 1}",
                    claim_id=claim.claim_id,
                    supporting_evidence_ids=[evidence.evidence_id for evidence in support],
                    opposing_evidence_ids=[evidence.evidence_id for evidence in oppose],
                    severity=_severity_for(support, oppose),
                    summary=(
                        "High-confidence supporting and opposing evidence were found "
                        "for the same claim."
                    ),
                )
            )
        return conflicts


def _group_evidence_by_claim_id(
    evidence_items: list[EvidenceSchema],
) -> dict[str, list[EvidenceSchema]]:
    grouped: dict[str, list[EvidenceSchema]] = {}
    for evidence in evidence_items:
        grouped.setdefault(evidence.claim_id, []).append(evidence)
    return grouped


def _high_scoring_evidence(
    evidence_items: list[EvidenceSchema],
    support_type: SupportType,
) -> list[EvidenceSchema]:
    return [
        evidence
        for evidence in evidence_items
        if evidence.support_type == support_type
        and (evidence.final_score or 0.0) >= CONFLICT_SCORE_THRESHOLD
    ]


def _severity_for(
    support: list[EvidenceSchema],
    oppose: list[EvidenceSchema],
) -> ConflictSeverity:
    top_support = max(evidence.final_score or 0.0 for evidence in support)
    top_oppose = max(evidence.final_score or 0.0 for evidence in oppose)
    if (
        top_support >= MAJOR_CONFLICT_SCORE_THRESHOLD
        and top_oppose >= MAJOR_CONFLICT_SCORE_THRESHOLD
    ):
        return ConflictSeverity.MAJOR
    return ConflictSeverity.MINOR
