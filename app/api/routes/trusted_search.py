from fastapi import APIRouter

from app.schemas.claim import ClaimSchema
from app.schemas.constraints import AnswerConstraintsSchema
from app.schemas.evidence import EvidenceSchema
from app.schemas.trusted_search import (
    QuestionType,
    TrustedSearchRequest,
    TrustedSearchResponse,
)
from app.services.claim_decomposer import ClaimDraft, decompose_claims
from app.services.evidence_extractor import extract_evidence_for_claims
from app.services.page_fetcher import PageFetcher, build_fallback_http_client
from app.services.question_classifier import classify_question, risk_for_question_type
from app.services.search_adapter import SearchAdapter, StaticSearchAdapter
from app.services.search_planner import build_search_plan
from app.services.source_classifier import search_results_to_sources

router = APIRouter(prefix="/api/v1", tags=["trusted-search"])


@router.post("/trusted-search", response_model=TrustedSearchResponse)
async def trusted_search(request: TrustedSearchRequest) -> TrustedSearchResponse:
    return build_mock_response(request)


def build_mock_response(
    request: TrustedSearchRequest,
    search_adapter: SearchAdapter | None = None,
    page_fetcher: PageFetcher | None = None,
) -> TrustedSearchResponse:
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
    adapter = search_adapter or StaticSearchAdapter()
    adapter_response = adapter.search(request.query, max_results=request.max_sources)
    sources = search_results_to_sources(adapter_response.results)
    fetcher = page_fetcher or _build_stage_fetcher()
    page_fetches = [fetcher.fetch_source(source) for source in sources]
    evidence_by_claim_id = extract_evidence_for_claims(
        claims=claim_drafts,
        page_fetches=page_fetches,
        source_ids=[source.source_id for source in sources],
    )
    constraints = _build_mock_constraints()

    return TrustedSearchResponse(
        query=request.query,
        question_type=question_type,
        risk_level=risk_level,
        overall_status="uncertain",
        overall_confidence=0.63,
        claims=[
            _build_claim(claim, evidence_by_claim_id[claim.claim_id])
            for claim in claim_drafts
        ],
        search_plan=search_plan,
        sources=sources,
        page_fetches=page_fetches,
        conflicts=[],
        answer_constraints=constraints,
    )


def _build_stage_fetcher() -> PageFetcher:
    return PageFetcher(http_client=build_fallback_http_client(), timeout_seconds=0.1)


def _build_claim(claim: ClaimDraft, evidence: list[EvidenceSchema]) -> ClaimSchema:
    return ClaimSchema(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        status="uncertain",
        confidence=0.63,
        reason=(
            "Rule-based evidence extraction has run, but reliability scoring and "
            "claim aggregation have not run yet."
        ),
        evidence=evidence,
    )


def _build_mock_constraints() -> AnswerConstraintsSchema:
    return AnswerConstraintsSchema(
        can_answer_confidently=False,
        must_disclose_uncertainty=True,
        must_cite_sources=True,
        allowed_tone="cautious",
        required_phrases=[
            "目前只能确认这是 mock evidence package",
            "真实搜索和证据验证尚未运行",
        ],
        forbidden_phrases=[
            "毫无疑问",
            "已经完全开源",
            "官方已经确认",
        ],
    )
