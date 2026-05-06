import re
from dataclasses import dataclass

from app.schemas.trusted_search import QuestionType


@dataclass(frozen=True)
class ClaimDraft:
    claim_id: str
    claim_text: str
    claim_type: str


def decompose_claims(query: str, question_type: QuestionType) -> list[ClaimDraft]:
    if question_type == QuestionType.AI_MODEL_INFO:
        return _decompose_ai_model_info(query)

    normalized_query = query.strip()
    return [
        ClaimDraft(
            claim_id="c1",
            claim_text=f"{normalized_query} 这一问题可以被外部来源验证",
            claim_type="general_fact",
        )
    ]


def _decompose_ai_model_info(query: str) -> list[ClaimDraft]:
    entity = _extract_model_entity(query)
    templates = (
        ("existence", "{entity} 是否存在公开发布页面"),
        ("model_weights", "{entity} 是否公开模型权重"),
        ("source_code", "{entity} 是否公开训练代码"),
        ("training_data", "{entity} 是否公开训练数据"),
        ("license", "{entity} 的许可证是否允许商用"),
        ("interpretation", "{entity} 是否能严格称为开源模型"),
    )
    return [
        ClaimDraft(
            claim_id=f"c{index}",
            claim_text=template.format(entity=entity),
            claim_type=claim_type,
        )
        for index, (claim_type, template) in enumerate(templates, start=1)
    ]


def _extract_model_entity(query: str) -> str:
    normalized = query.strip().rstrip("？?。.")
    marker_pattern = re.compile(r"(是不是|是否|是|有没有|能不能|可以|属于)")
    marker_match = marker_pattern.search(normalized)
    if marker_match:
        candidate = normalized[: marker_match.start()].strip(" ，,")
        if candidate:
            return candidate

    cleanup_pattern = re.compile(r"(开源模型|开源|模型|权重|许可证|license)", re.IGNORECASE)
    candidate = cleanup_pattern.sub("", normalized).strip(" ，,")
    return candidate or normalized
