from app.schemas.claim import ClaimSchema
from app.schemas.constraints import AllowedTone
from app.schemas.trusted_search import QuestionType
from app.services.answer_constraint_builder import AnswerConstraintBuilder


def test_all_confirmed_or_likely_allows_confident_answer() -> None:
    constraints = _build([_claim("confirmed"), _claim("likely")])

    assert constraints.can_answer_confidently is True
    assert constraints.must_disclose_uncertainty is False
    assert constraints.allowed_tone == AllowedTone.CONFIDENT


def test_uncertain_requires_cautious_uncertainty_disclosure() -> None:
    constraints = _build([_claim("confirmed"), _claim("uncertain")])

    assert constraints.can_answer_confidently is False
    assert constraints.must_disclose_uncertainty is True
    assert constraints.allowed_tone == AllowedTone.CAUTIOUS
    assert "部分信息仍无法确认" in constraints.required_phrases


def test_unsupported_forbids_confident_phrases() -> None:
    constraints = _build([_claim("unsupported")])

    assert constraints.can_answer_confidently is False
    assert constraints.allowed_tone == AllowedTone.CAUTIOUS
    assert "已经确认" in constraints.forbidden_phrases
    assert "毫无疑问" in constraints.forbidden_phrases
    assert "官方确认" in constraints.forbidden_phrases


def test_conflicting_requires_conflict_aware_tone() -> None:
    constraints = _build([_claim("conflicting")])

    assert constraints.can_answer_confidently is False
    assert constraints.must_disclose_uncertainty is True
    assert constraints.allowed_tone == AllowedTone.CONFLICT_AWARE
    assert "不同来源之间存在冲突" in constraints.required_phrases
    assert "不能直接下确定结论" in constraints.required_phrases


def test_false_likely_requires_corrective_tone() -> None:
    constraints = _build([_claim("false_likely")])

    assert constraints.can_answer_confidently is False
    assert constraints.must_disclose_uncertainty is True
    assert constraints.allowed_tone == AllowedTone.CORRECTIVE
    assert "现有证据更倾向于反驳该说法" in constraints.required_phrases


def test_ai_model_open_source_mixed_subclaims_use_cautious_tone() -> None:
    constraints = _build(
        [
            _claim("likely", claim_type="existence"),
            _claim("likely", claim_type="model_weights"),
            _claim("likely", claim_type="source_code"),
            _claim("likely", claim_type="license"),
            _claim("false_likely", claim_type="training_data"),
            _claim("uncertain", claim_type="interpretation"),
        ],
        question_type=QuestionType.AI_MODEL_INFO,
    )

    required_text = " ".join(constraints.required_phrases)
    assert constraints.can_answer_confidently is False
    assert constraints.must_disclose_uncertainty is True
    assert constraints.allowed_tone == AllowedTone.CAUTIOUS
    assert "权重开放" in required_text
    assert "代码开放" in required_text
    assert "训练数据开放" in required_text
    assert "许可证" in required_text
    assert "严格开源定义" in required_text


def test_ai_model_false_likely_interpretation_can_use_corrective_tone() -> None:
    constraints = _build(
        [
            _claim("likely", claim_type="model_weights"),
            _claim("false_likely", claim_type="interpretation"),
        ],
        question_type=QuestionType.AI_MODEL_INFO,
    )

    assert constraints.allowed_tone == AllowedTone.CORRECTIVE


def test_forbidden_phrases_are_non_empty() -> None:
    constraints = _build([_claim("likely")])

    assert constraints.forbidden_phrases
    assert "完全确定" in constraints.forbidden_phrases


def test_ai_model_uncertain_open_source_interpretation_requires_domain_disclosure() -> None:
    constraints = _build(
        [_claim("uncertain", claim_type="interpretation")],
        question_type=QuestionType.AI_MODEL_INFO,
    )

    required_text = " ".join(constraints.required_phrases)
    assert "权重开放" in required_text
    assert "代码开放" in required_text
    assert "训练数据开放" in required_text
    assert "许可证" in required_text
    assert "严格开源定义" in required_text


def _build(
    claims: list[ClaimSchema],
    question_type: QuestionType = QuestionType.GENERAL_FACT,
):
    return AnswerConstraintBuilder().build(
        query="test query",
        question_type=question_type,
        claims=claims,
    )


def _claim(status: str, claim_type: str = "general_fact") -> ClaimSchema:
    return ClaimSchema(
        claim_id=f"c-{status}-{claim_type}",
        claim_text="Claim text",
        claim_type=claim_type,
        status=status,
        confidence=0.8,
        reason="Reason.",
        evidence=[],
    )
