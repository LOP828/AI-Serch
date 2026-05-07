from app.schemas.claim import ClaimSchema, ClaimStatus
from app.schemas.conflict import ConflictSchema
from app.schemas.evidence import EvidenceSchema
from app.schemas.page import PageFetchResultSchema
from app.schemas.trusted_search import (
    OverallStatus,
    QuestionType,
    TrustedSearchRequest,
    TrustedSearchResponse,
)
from app.services.answer_constraint_builder import AnswerConstraintBuilder
from app.services.claim_aggregator import ClaimAggregation, ClaimAggregator
from app.services.claim_decomposer import ClaimDraft, decompose_claims
from app.services.conflict_detector import ConflictDetector
from app.services.evidence_extractor import (
    EvidenceExtractorProtocol,
    RuleBasedEvidenceExtractor,
    extract_evidence_for_claims,
)
from app.services.page_fetcher import PageFetcher, build_fallback_http_client
from app.services.question_classifier import classify_question, risk_for_question_type
from app.services.reliability_scorer import ReliabilityScorer
from app.services.search_adapter import SearchAdapter, StaticSearchAdapter
from app.services.search_planner import build_search_plan
from app.services.source_classifier import search_results_to_sources


class TrustedSearchService:
    def __init__(
        self,
        search_adapter: SearchAdapter | None = None,
        page_fetcher: PageFetcher | None = None,
        evidence_extractor: EvidenceExtractorProtocol | None = None,
        reliability_scorer: ReliabilityScorer | None = None,
        claim_aggregator: ClaimAggregator | None = None,
        conflict_detector: ConflictDetector | None = None,
        answer_constraint_builder: AnswerConstraintBuilder | None = None,
    ) -> None:
        self._search_adapter = search_adapter or StaticSearchAdapter()
        self._page_fetcher = page_fetcher or _build_stage_fetcher()
        self._evidence_extractor = evidence_extractor or RuleBasedEvidenceExtractor()
        self._reliability_scorer = reliability_scorer or ReliabilityScorer()
        self._claim_aggregator = claim_aggregator or ClaimAggregator()
        self._conflict_detector = conflict_detector or ConflictDetector()
        self._answer_constraint_builder = answer_constraint_builder or AnswerConstraintBuilder()

    def search(self, request: TrustedSearchRequest) -> TrustedSearchResponse:
        classified = classify_question(request.query)
        question_type = classified.question_type
        risk_level = classified.risk_level
        if request.question_type != QuestionType.AUTO:
            question_type = request.question_type
            risk_level = risk_for_question_type(question_type)

        claim_drafts = decompose_claims(request.query, question_type)
        search_plan = build_search_plan(
            query=request.query,
            question_type=question_type,
            claims=claim_drafts,
            strictness=request.strictness,
        )
        adapter_response = self._search_adapter.search(
            request.query,
            max_results=request.max_sources,
        )
        sources = search_results_to_sources(adapter_response.results)
        page_fetches = [self._safe_fetch_source(source) for source in sources]
        evidence_by_claim_id = extract_evidence_for_claims(
            claims=claim_drafts,
            page_fetches=page_fetches,
            source_ids=[source.source_id for source in sources],
            extractor=self._evidence_extractor,
        )
        sources_by_id = {source.source_id: source for source in sources}
        scored_evidence_by_claim_id = {
            claim_id: self._reliability_scorer.score_evidence_items(
                evidence_items,
                sources_by_id,
            )
            for claim_id, evidence_items in evidence_by_claim_id.items()
        }
        scored_evidence = [
            evidence
            for evidence_items in scored_evidence_by_claim_id.values()
            for evidence in evidence_items
        ]
        conflicts = self._conflict_detector.detect(claim_drafts, scored_evidence)
        aggregations = self._claim_aggregator.aggregate(claim_drafts, scored_evidence)
        claims = [
            _apply_conflict_to_claim(
                claim=_build_claim(
                    claim=claim,
                    evidence=scored_evidence_by_claim_id[claim.claim_id],
                    aggregation=aggregations[claim.claim_id],
                ),
                conflicts=conflicts,
            )
            for claim in claim_drafts
        ]
        constraints = self._answer_constraint_builder.build(
            query=request.query,
            question_type=question_type,
            claims=claims,
        )
        return TrustedSearchResponse(
            query=request.query,
            question_type=question_type,
            risk_level=risk_level,
            overall_status=derive_overall_status(claims, question_type),
            overall_confidence=derive_overall_confidence(claims),
            claims=claims,
            search_plan=search_plan,
            sources=sources,
            page_fetches=page_fetches,
            conflicts=conflicts,
            answer_constraints=constraints,
        )

    def _safe_fetch_source(self, source) -> PageFetchResultSchema:
        try:
            return self._page_fetcher.fetch_source(source)
        except Exception as exc:
            return PageFetchResultSchema(
                url=source.url,
                title=source.title,
                text=source.snippet or "",
                fetch_status="fallback" if source.snippet else "failed",
                error_message=f"unexpected fetch error: {exc}",
            )


def derive_overall_status(
    claims: list[ClaimSchema],
    question_type: QuestionType | None = None,
) -> OverallStatus:
    if not claims:
        return OverallStatus.UNSUPPORTED

    statuses = {claim.status for claim in claims}
    if ClaimStatus.CONFLICTING in statuses:
        return OverallStatus.CONFLICTING
    if ClaimStatus.FALSE_LIKELY in statuses:
        if _has_mixed_ai_model_open_source_claims(claims, question_type):
            return OverallStatus.PARTIALLY_CONFIRMED
        if _core_interpretation_status(claims) == ClaimStatus.FALSE_LIKELY:
            return OverallStatus.LIKELY_FALSE
        if statuses <= {ClaimStatus.FALSE_LIKELY}:
            return OverallStatus.LIKELY_FALSE
        if statuses & {ClaimStatus.CONFIRMED, ClaimStatus.LIKELY}:
            return OverallStatus.PARTIALLY_CONFIRMED
        return OverallStatus.LIKELY_FALSE
    if statuses <= {ClaimStatus.CONFIRMED}:
        return OverallStatus.CONFIRMED
    if statuses <= {ClaimStatus.CONFIRMED, ClaimStatus.LIKELY}:
        return OverallStatus.MOSTLY_CONFIRMED
    if statuses <= {ClaimStatus.UNSUPPORTED}:
        return OverallStatus.UNSUPPORTED
    if statuses & {ClaimStatus.CONFIRMED, ClaimStatus.LIKELY}:
        return OverallStatus.PARTIALLY_CONFIRMED
    return OverallStatus.UNCERTAIN


def derive_overall_confidence(claims: list[ClaimSchema]) -> float:
    if not claims:
        return 0.0
    status = derive_overall_status(claims)
    if status == OverallStatus.UNSUPPORTED:
        return 0.0

    confidence = sum(claim.confidence for claim in claims) / len(claims)
    if status == OverallStatus.CONFLICTING:
        confidence = min(confidence, 0.60)
    return max(0.0, min(round(confidence, 4), 1.0))


def _has_mixed_ai_model_open_source_claims(
    claims: list[ClaimSchema],
    question_type: QuestionType | None,
) -> bool:
    if question_type != QuestionType.AI_MODEL_INFO:
        return False
    if _core_interpretation_status(claims) != ClaimStatus.UNCERTAIN:
        return False

    statuses = {claim.status for claim in claims}
    return (
        ClaimStatus.FALSE_LIKELY in statuses
        and bool(statuses & {ClaimStatus.CONFIRMED, ClaimStatus.LIKELY})
    )


def _core_interpretation_status(claims: list[ClaimSchema]) -> ClaimStatus | None:
    for claim in claims:
        if claim.claim_type == "interpretation":
            return claim.status
    return None


def _build_stage_fetcher() -> PageFetcher:
    return PageFetcher(http_client=build_fallback_http_client(), timeout_seconds=0.1)


def _build_claim(
    claim: ClaimDraft,
    evidence: list[EvidenceSchema],
    aggregation: ClaimAggregation,
) -> ClaimSchema:
    return ClaimSchema(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        status=aggregation.status,
        confidence=aggregation.confidence,
        reason=aggregation.reason,
        evidence=evidence,
    )


def _apply_conflict_to_claim(
    claim: ClaimSchema,
    conflicts: list[ConflictSchema],
) -> ClaimSchema:
    claim_conflicts = [conflict for conflict in conflicts if conflict.claim_id == claim.claim_id]
    if not claim_conflicts:
        return claim
    top_conflict = claim_conflicts[0]
    return claim.model_copy(
        update={
            "status": ClaimStatus.CONFLICTING,
            "confidence": min(max(claim.confidence, 0.70), 1.0),
            "reason": top_conflict.summary,
        }
    )
