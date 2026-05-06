from fastapi import APIRouter

from app.schemas.claim import ClaimSchema
from app.schemas.constraints import AnswerConstraintsSchema
from app.schemas.evidence import EvidenceSchema
from app.schemas.source import SourceSchema
from app.schemas.trusted_search import (
    QuestionType,
    RiskLevel,
    TrustedSearchRequest,
    TrustedSearchResponse,
)

router = APIRouter(prefix="/api/v1", tags=["trusted-search"])


@router.post("/trusted-search", response_model=TrustedSearchResponse)
async def trusted_search(request: TrustedSearchRequest) -> TrustedSearchResponse:
    return build_mock_response(request)


def build_mock_response(request: TrustedSearchRequest) -> TrustedSearchResponse:
    question_type = (
        QuestionType.AI_MODEL_INFO
        if request.question_type == QuestionType.AUTO
        else request.question_type
    )

    evidence = EvidenceSchema(
        evidence_id="e1",
        claim_id="c1",
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
    claim = ClaimSchema(
        claim_id="c1",
        claim_text="MiroThinker 1.7 是否存在公开发布页面",
        claim_type="existence",
        status="uncertain",
        confidence=0.63,
        reason=(
            "This is a schema-only mock response; no live search or evidence "
            "verification has run."
        ),
        evidence=[evidence],
    )
    source = SourceSchema(
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
    constraints = AnswerConstraintsSchema(
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

    return TrustedSearchResponse(
        query=request.query,
        question_type=question_type,
        risk_level=RiskLevel.MEDIUM,
        overall_status="uncertain",
        overall_confidence=0.63,
        claims=[claim],
        sources=[source],
        conflicts=[],
        answer_constraints=constraints,
    )
