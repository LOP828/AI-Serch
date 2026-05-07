from app.schemas.claim import ClaimSchema, ClaimStatus
from app.schemas.constraints import AllowedTone, AnswerConstraintsSchema
from app.schemas.trusted_search import QuestionType

BASE_FORBIDDEN_PHRASES = [
    "毫无疑问",
    "完全确定",
    "已经完全确认",
    "官方已经确认",
    "一定是",
]


class AnswerConstraintBuilder:
    def build(
        self,
        query: str,
        question_type: QuestionType,
        claims: list[ClaimSchema],
    ) -> AnswerConstraintsSchema:
        del query
        statuses = {claim.status for claim in claims}
        required_phrases: list[str] = []
        forbidden_phrases = list(BASE_FORBIDDEN_PHRASES)

        interpretation_status = _core_interpretation_status(claims)
        mixed_ai_model_open_source = _has_mixed_ai_model_open_source_claims(
            question_type,
            claims,
        )

        if ClaimStatus.CONFLICTING in statuses:
            allowed_tone = AllowedTone.CONFLICT_AWARE
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.extend(
                [
                    "不同来源之间存在冲突",
                    "不能直接下确定结论",
                ]
            )
        elif (
            ClaimStatus.FALSE_LIKELY in statuses
            and not mixed_ai_model_open_source
            and (
                interpretation_status in {None, ClaimStatus.FALSE_LIKELY}
                or statuses <= {ClaimStatus.FALSE_LIKELY}
            )
        ):
            allowed_tone = AllowedTone.CORRECTIVE
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.append("现有证据更倾向于反驳该说法")
        elif ClaimStatus.FALSE_LIKELY in statuses:
            allowed_tone = AllowedTone.CAUTIOUS
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.extend(
                [
                    "部分信息仍无法确认",
                    "目前证据不足以完全确认",
                ]
            )
        elif ClaimStatus.UNSUPPORTED in statuses:
            allowed_tone = AllowedTone.CAUTIOUS
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.extend(
                [
                    "部分信息仍无法确认",
                    "目前证据不足以完全确认",
                ]
            )
            forbidden_phrases.extend(["已经确认", "官方确认"])
        elif ClaimStatus.UNCERTAIN in statuses:
            allowed_tone = AllowedTone.CAUTIOUS
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.extend(
                [
                    "部分信息仍无法确认",
                    "目前证据不足以完全确认",
                ]
            )
        elif statuses and statuses <= {ClaimStatus.CONFIRMED, ClaimStatus.LIKELY}:
            allowed_tone = AllowedTone.CONFIDENT
            can_answer_confidently = True
            must_disclose_uncertainty = False
        else:
            allowed_tone = AllowedTone.CAUTIOUS
            can_answer_confidently = False
            must_disclose_uncertainty = True
            required_phrases.append("目前证据不足以完全确认")

        if _needs_ai_model_open_source_disclosure(question_type, claims):
            required_phrases.append(
                "需要区分权重开放、代码开放、训练数据开放、许可证和严格开源定义"
            )

        return AnswerConstraintsSchema(
            can_answer_confidently=can_answer_confidently,
            must_disclose_uncertainty=must_disclose_uncertainty,
            must_cite_sources=True,
            allowed_tone=allowed_tone,
            required_phrases=_deduplicate(required_phrases),
            forbidden_phrases=_deduplicate(forbidden_phrases),
        )


def _needs_ai_model_open_source_disclosure(
    question_type: QuestionType,
    claims: list[ClaimSchema],
) -> bool:
    if question_type != QuestionType.AI_MODEL_INFO:
        return False

    uncertain_statuses = {
        ClaimStatus.UNCERTAIN,
        ClaimStatus.UNSUPPORTED,
        ClaimStatus.CONFLICTING,
        ClaimStatus.FALSE_LIKELY,
    }
    return any(
        claim.claim_type == "interpretation" and claim.status in uncertain_statuses
        for claim in claims
    )


def _has_mixed_ai_model_open_source_claims(
    question_type: QuestionType,
    claims: list[ClaimSchema],
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


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated
