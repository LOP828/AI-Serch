from dataclasses import dataclass

from app.schemas.claim import ClaimStatus
from app.schemas.evidence import EvidenceSchema, SupportType
from app.services.claim_decomposer import ClaimDraft

CONFIRMED_SUPPORT_THRESHOLD = 0.80
LIKELY_SUPPORT_THRESHOLD = 0.65
CONFLICT_THRESHOLD = 0.70
FALSE_LIKELY_OPPOSE_THRESHOLD = 0.75


@dataclass(frozen=True)
class ClaimAggregation:
    claim_id: str
    status: ClaimStatus
    confidence: float
    reason: str


class ClaimAggregator:
    def aggregate(
        self,
        claims: list[ClaimDraft],
        evidence_items: list[EvidenceSchema],
    ) -> dict[str, ClaimAggregation]:
        evidence_by_claim_id = group_evidence_by_claim_id(evidence_items)
        return {
            claim.claim_id: self.aggregate_claim(
                claim=claim,
                evidence_items=evidence_by_claim_id.get(claim.claim_id, []),
            )
            for claim in claims
        }

    def aggregate_claim(
        self,
        claim: ClaimDraft,
        evidence_items: list[EvidenceSchema],
    ) -> ClaimAggregation:
        support_scores = _scores_for(evidence_items, SupportType.SUPPORT)
        oppose_scores = _scores_for(evidence_items, SupportType.OPPOSE)
        partial_scores = _scores_for(evidence_items, SupportType.PARTIAL)
        has_support = any(
            evidence.support_type == SupportType.SUPPORT for evidence in evidence_items
        )
        has_partial = any(
            evidence.support_type == SupportType.PARTIAL for evidence in evidence_items
        )
        top_support = max(support_scores, default=0.0)
        top_oppose = max(oppose_scores, default=0.0)
        top_partial = max(partial_scores, default=0.0)
        top_any = max((_score(evidence) for evidence in evidence_items), default=0.0)

        if top_support >= CONFLICT_THRESHOLD and top_oppose >= CONFLICT_THRESHOLD:
            return ClaimAggregation(
                claim_id=claim.claim_id,
                status=ClaimStatus.CONFLICTING,
                confidence=max(top_support, top_oppose),
                reason="High-confidence supporting and opposing evidence both exist.",
            )

        if top_oppose >= FALSE_LIKELY_OPPOSE_THRESHOLD and top_support < CONFLICT_THRESHOLD:
            return ClaimAggregation(
                claim_id=claim.claim_id,
                status=ClaimStatus.FALSE_LIKELY,
                confidence=top_oppose,
                reason="Strong opposing evidence was found without comparable support.",
            )

        if top_support >= CONFIRMED_SUPPORT_THRESHOLD and top_oppose < CONFLICT_THRESHOLD:
            return ClaimAggregation(
                claim_id=claim.claim_id,
                status=ClaimStatus.CONFIRMED,
                confidence=top_support,
                reason="Found high-confidence supporting evidence from a strong source.",
            )

        if top_support >= LIKELY_SUPPORT_THRESHOLD:
            return ClaimAggregation(
                claim_id=claim.claim_id,
                status=ClaimStatus.LIKELY,
                confidence=top_support,
                reason="Found supporting evidence, but not enough for confirmed status.",
            )

        if has_partial or has_support:
            return ClaimAggregation(
                claim_id=claim.claim_id,
                status=ClaimStatus.UNCERTAIN,
                confidence=max(top_partial, top_support, top_any),
                reason="Only partial or low-confidence evidence was found.",
            )

        return ClaimAggregation(
            claim_id=claim.claim_id,
            status=ClaimStatus.UNSUPPORTED,
            confidence=0.0,
            reason="No relevant supporting evidence was found.",
        )


def group_evidence_by_claim_id(
    evidence_items: list[EvidenceSchema],
) -> dict[str, list[EvidenceSchema]]:
    grouped: dict[str, list[EvidenceSchema]] = {}
    for evidence in evidence_items:
        grouped.setdefault(evidence.claim_id, []).append(evidence)
    return grouped


def _scores_for(evidence_items: list[EvidenceSchema], support_type: SupportType) -> list[float]:
    return [
        _score(evidence)
        for evidence in evidence_items
        if evidence.support_type == support_type
    ]


def _score(evidence: EvidenceSchema) -> float:
    return evidence.final_score or 0.0
