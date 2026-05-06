import re

from app.schemas.search import SearchPlanItemSchema
from app.schemas.source import SourceType
from app.schemas.trusted_search import QuestionType, Strictness
from app.services.claim_decomposer import ClaimDraft

_AI_MODEL_QUERY_SUFFIXES = (
    "Hugging Face",
    "GitHub",
    "paper",
    "arXiv",
    "license",
    "official",
)

_AI_MODEL_PREFERRED_SOURCE_TYPES = (
    SourceType.OFFICIAL_MODEL_CARD,
    SourceType.SOURCE_CODE_REPO,
    SourceType.ACADEMIC_PAPER,
    SourceType.OFFICIAL_DOCS,
    SourceType.OFFICIAL_BLOG,
)


def build_search_plan(
    query: str,
    question_type: QuestionType,
    claims: list[ClaimDraft],
    strictness: Strictness = Strictness.BALANCED,
) -> list[SearchPlanItemSchema]:
    if question_type == QuestionType.AI_MODEL_INFO:
        return _build_ai_model_search_plan(query, claims, strictness)

    return [
        SearchPlanItemSchema(
            claim_id=claim.claim_id,
            queries=[claim.claim_text],
            preferred_source_types=[],
        )
        for claim in claims
    ]


def _build_ai_model_search_plan(
    query: str,
    claims: list[ClaimDraft],
    strictness: Strictness,
) -> list[SearchPlanItemSchema]:
    entity = _extract_entity_from_claims(query, claims)
    preferred_source_types = list(_AI_MODEL_PREFERRED_SOURCE_TYPES)
    if strictness == Strictness.LOOSE:
        preferred_source_types.append(SourceType.MAINSTREAM_MEDIA)

    return [
        SearchPlanItemSchema(
            claim_id=claim.claim_id,
            queries=_queries_for_claim(entity, claim),
            preferred_source_types=preferred_source_types,
        )
        for claim in claims
    ]


def _queries_for_claim(entity: str, claim: ClaimDraft) -> list[str]:
    claim_specific_suffixes = {
        "existence": ("Hugging Face", "official"),
        "model_weights": ("Hugging Face", "GitHub", "official"),
        "source_code": ("GitHub", "official"),
        "training_data": ("paper", "arXiv", "official"),
        "license": ("license", "Hugging Face", "GitHub"),
        "interpretation": _AI_MODEL_QUERY_SUFFIXES,
    }
    suffixes = claim_specific_suffixes.get(claim.claim_type, _AI_MODEL_QUERY_SUFFIXES)
    queries = [f"{entity} {suffix}" for suffix in suffixes]
    return _deduplicate_strings(queries)


def _extract_entity_from_claims(query: str, claims: list[ClaimDraft]) -> str:
    if claims:
        match = re.match(r"(.+?)\s+是否", claims[0].claim_text)
        if match:
            return match.group(1).strip()

    normalized = query.strip().rstrip("？?。.")
    marker_match = re.search(r"(是不是|是否|是|有没有|能不能|可以|属于)", normalized)
    if marker_match:
        candidate = normalized[: marker_match.start()].strip(" ，,")
        if candidate:
            return candidate
    return normalized


def _deduplicate_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated
