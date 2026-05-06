from fastapi import APIRouter

from app.schemas.claim import ClaimSchema
from app.schemas.constraints import AnswerConstraintsSchema
from app.schemas.evidence import EvidenceSchema
from app.schemas.source import SourceSchema
from app.schemas.trusted_search import (
    QuestionType,
    TrustedSearchRequest,
    TrustedSearchResponse,
)
from app.services.claim_decomposer import ClaimDraft, decompose_claims
from app.services.question_classifier import classify_question, risk_for_question_type
from app.services.search_planner import build_search_plan

router = APIRouter(prefix="/api/v1", tags=["trusted-search"])


@router.post("/trusted-search", response_model=TrustedSearchResponse)
async def trusted_search(request: TrustedSearchRequest) -> TrustedSearchResponse:
    return build_mock_response(request)


def build_mock_response(request: TrustedSearchRequest) -> TrustedSearchResponse:
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
    source = _build_mock_source()
    constraints = _build_mock_constraints()

    return TrustedSearchResponse(
        query=request.query,
        question_type=question_type,
        risk_level=risk_level,
        overall_status="uncertain",
        overall_confidence=0.63,
        claims=[_build_mock_claim(claim) for claim in claim_drafts],
        search_plan=search_plan,
        sources=[source],
        conflicts=[],
        answer_constraints=constraints,
    )


def _build_mock_claim(claim: ClaimDraft) -> ClaimSchema:
    evidence = _build_mock_evidence(claim.claim_id)
    return ClaimSchema(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        status="uncertain",
        confidence=0.63,
        reason=(
            "This is a schema-only mock response; no live search or evidence "
            "verification has run."
        ),
        evidence=[evidence],
    )


def _build_mock_evidence(claim_id: str) -> EvidenceSchema:
    return EvidenceSchema(
        evidence_id="e1",
        claim_id=claim_id,
        source_id="s1",
        evidence_text=(
            "Mock evidence: a model card page is available, but this stage does not "
            "verify real sources."
        ),
        support_type="partial",
        relevance_score=0.72,
        source_score=0.88,
        primary_source_factor=1.0,
        recency_factor=1.0,
        cross_check_factor=1.0,
        conflict_penalty=1.0,
        interest_conflict_penalty=1.0,
        final_score=0.63,
        score_breakdown={
            "relevance_score": 0.72,
            "source_base_score": 0.88,
            "primary_source_factor": 1.0,
            "recency_factor": 1.0,
            "final_score": 0.63,
        },
    )


def _build_mock_source() -> SourceSchema:
    return SourceSchema(
        source_id="s1",
        title="Mock MiroThinker-1.7 model card",
        url="https://huggingface.co/example/mirothinker-1.7",
        domain="huggingface.co",
        snippet="Mock source snippet for schema validation only.",
        source_type="official_model_card",
        base_reliability=0.88,
        is_primary_source=True,
        published_at=None,
        author=None,
        fetched_at=None,
        fetch_status="not_fetched",
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
