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
    intent = _classify_ai_model_query_intent(query)
    if intent == "release_or_origin":
        return _decompose_ai_model_release_or_origin(query, entity)
    if intent == "model_access":
        return _decompose_ai_model_access(query, entity)
    if intent == "model_capability_or_spec":
        return _decompose_ai_model_capability_or_spec(entity)
    return _decompose_ai_model_open_source(entity)


def _decompose_ai_model_open_source(entity: str) -> list[ClaimDraft]:
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


def _decompose_ai_model_release_or_origin(query: str, entity: str) -> list[ClaimDraft]:
    provider = _extract_provider(query)
    if provider:
        templates = (
            ("official_release_page", "{entity} 是否存在 {provider} 官方发布或文档页面"),
            ("model_provider", "{entity} 是否由 {provider} 提供或发布"),
            ("model_access", "{entity} 是否可通过 {provider} API / platform 使用"),
        )
        return [
            ClaimDraft(
                claim_id=f"c{index}",
                claim_text=template.format(entity=entity, provider=provider),
                claim_type=claim_type,
            )
            for index, (claim_type, template) in enumerate(templates, start=1)
        ]

    templates = (
        ("official_release_page", "{entity} 是否存在官方发布或文档页面"),
        ("model_provider", "{entity} 是否有明确发布或提供方"),
        ("model_access", "{entity} 是否可通过官方 API / platform 使用"),
    )
    return [
        ClaimDraft(
            claim_id=f"c{index}",
            claim_text=template.format(entity=entity),
            claim_type=claim_type,
        )
        for index, (claim_type, template) in enumerate(templates, start=1)
    ]


def _decompose_ai_model_access(query: str, entity: str) -> list[ClaimDraft]:
    provider = _extract_provider(query)
    provider_text = f"{provider} " if provider else "官方 "
    templates = (
        ("model_access", "{entity} 是否可通过 {provider_text}API / platform 使用"),
        ("official_release_page", "{entity} 是否存在 {provider_text}官方文档页面"),
    )
    return [
        ClaimDraft(
            claim_id=f"c{index}",
            claim_text=template.format(entity=entity, provider_text=provider_text),
            claim_type=claim_type,
        )
        for index, (claim_type, template) in enumerate(templates, start=1)
    ]


def _decompose_ai_model_capability_or_spec(entity: str) -> list[ClaimDraft]:
    templates = (
        ("model_capability_or_spec", "{entity} 的相关能力或规格是否有官方说明"),
        ("official_release_page", "{entity} 是否存在官方文档页面"),
    )
    return [
        ClaimDraft(
            claim_id=f"c{index}",
            claim_text=template.format(entity=entity),
            claim_type=claim_type,
        )
        for index, (claim_type, template) in enumerate(templates, start=1)
    ]


def _classify_ai_model_query_intent(query: str) -> str:
    normalized = query.lower()
    if _contains_any(
        normalized,
        (
            "开源",
            "公开权重",
            "权重",
            "license",
            "许可证",
            "商用",
            "commercial",
            "training code",
            "训练代码",
            "训练数据",
        ),
    ):
        return "open_source_status"
    if _is_release_or_origin_query(normalized):
        return "release_or_origin"
    if _contains_any(
        normalized,
        ("api", "platform", "可用", "能用", "访问", "chatgpt", "azure", "openrouter"),
    ):
        return "model_access"
    if _contains_any(normalized, ("上下文", "context", "多模态", "价格", "版本", "参数")):
        return "model_capability_or_spec"
    return "open_source_status"


def _is_release_or_origin_query(normalized_query: str) -> bool:
    return (
        bool(re.search(r"(是否是|是不是).+发布", normalized_query))
        or "由" in normalized_query
        and "发布" in normalized_query
        or "谁发布" in normalized_query
        or "发布的模型" in normalized_query
        or "官方发布" in normalized_query
        or "官方文档" in normalized_query
        or "official release" in normalized_query
        or "released by" in normalized_query
    )


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _extract_provider(query: str) -> str | None:
    if re.search(r"\bopenai\b", query, flags=re.IGNORECASE):
        return "OpenAI"
    return None


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
