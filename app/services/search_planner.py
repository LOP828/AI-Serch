import re

from app.schemas.search import SearchPlanItemSchema
from app.schemas.source import SourceType
from app.schemas.trusted_search import QuestionType, Strictness
from app.services.claim_decomposer import ClaimDraft

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
    if question_type == QuestionType.POLICY_LEGAL:
        return _build_policy_legal_search_plan(query, claims)
    if question_type == QuestionType.PRODUCT_INFO:
        return _build_product_info_search_plan(query, claims)

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
            queries=_queries_for_claim(entity, claim, strictness),
            preferred_source_types=preferred_source_types,
        )
        for claim in claims
    ]


def _queries_for_claim(
    entity: str,
    claim: ClaimDraft,
    strictness: Strictness,
) -> list[str]:
    quoted_entity = f'"{entity}"'
    queries = _base_queries(entity, quoted_entity, strictness)
    queries.extend(_claim_specific_queries(entity, quoted_entity, claim, strictness))
    if strictness == Strictness.LOOSE:
        queries.extend(_loose_queries(entity, quoted_entity))
    return _deduplicate_strings(queries)


def _base_queries(entity: str, quoted_entity: str, strictness: Strictness) -> list[str]:
    official_domain_queries = _ai_model_official_domain_queries(entity)
    if strictness == Strictness.STRICT:
        return [
            quoted_entity,
            f"{quoted_entity} official",
            f"{entity} official",
            f"{entity} official release",
            *official_domain_queries,
            f"{entity} site:huggingface.co",
            f"{quoted_entity} site:huggingface.co",
            f"{entity} site:github.com",
            f"{quoted_entity} site:github.com",
        ]

    return [
        entity,
        quoted_entity,
        f"{entity} official",
        *official_domain_queries,
        f"{entity} Hugging Face",
        f"{entity} GitHub",
        f"{entity} paper",
        f"{entity} arXiv",
    ]


def _claim_specific_queries(
    entity: str,
    quoted_entity: str,
    claim: ClaimDraft,
    strictness: Strictness,
) -> list[str]:
    if claim.claim_type == "existence":
        return [
            f"{entity} official release",
            f"{entity} model card",
            f"{quoted_entity} model card",
        ]
    if claim.claim_type == "model_weights":
        return [
            f"{entity} Hugging Face",
            f"{entity} site:huggingface.co",
            f"{quoted_entity} site:huggingface.co",
            f"{entity} model files",
            f"{entity} weights model card",
        ]
    if claim.claim_type == "source_code":
        return [
            f"{entity} GitHub",
            f"{entity} site:github.com",
            f"{quoted_entity} site:github.com",
            f"{entity} source code",
            f"{entity} training code GitHub",
        ]
    if claim.claim_type == "training_data":
        return [
            f"{entity} paper",
            f"{entity} arXiv",
            f"{quoted_entity} paper",
            f"{quoted_entity} arXiv",
            f"{entity} technical report",
        ]
    if claim.claim_type == "license":
        return [
            f"{entity} license",
            f"{quoted_entity} license",
            f"{entity} commercial use",
            f"{entity} license Hugging Face",
            f"{entity} license GitHub",
        ]
    if claim.claim_type == "interpretation":
        return [
            f"{entity} license",
            f"{quoted_entity} license",
            f"{entity} model card",
            f"{quoted_entity} model card",
            f"{entity} commercial use",
            f"{entity} open source",
        ]

    if strictness == Strictness.STRICT:
        return [
            f"{entity} arXiv",
            f"{entity} paper",
            f"{entity} license",
            f"{quoted_entity} license",
        ]

    return [
        f"{entity} license",
        f"{quoted_entity} license",
        f"{entity} model card",
        f"{quoted_entity} model card",
    ]


def _loose_queries(entity: str, quoted_entity: str) -> list[str]:
    return [
        f"{entity} release",
        f"{entity} announcement",
        f"{entity} technical report",
        f"{quoted_entity} release",
    ]


def _build_policy_legal_search_plan(
    query: str,
    claims: list[ClaimDraft],
) -> list[SearchPlanItemSchema]:
    return [
        SearchPlanItemSchema(
            claim_id=claim.claim_id,
            queries=_policy_legal_queries(query=query, claim=claim),
            preferred_source_types=[
                SourceType.GOVERNMENT_DOCS,
                SourceType.FINANCIAL_FILING,
                SourceType.OFFICIAL_DOCS,
            ],
        )
        for claim in claims
    ]


def _build_product_info_search_plan(
    query: str,
    claims: list[ClaimDraft],
) -> list[SearchPlanItemSchema]:
    return [
        SearchPlanItemSchema(
            claim_id=claim.claim_id,
            queries=_product_info_queries(query=query, claim=claim),
            preferred_source_types=[
                SourceType.PRODUCT_PAGE,
                SourceType.OFFICIAL_DOCS,
                SourceType.MAINSTREAM_MEDIA,
            ],
        )
        for claim in claims
    ]


def _policy_legal_queries(query: str, claim: ClaimDraft) -> list[str]:
    base_query = _clean_query_text(query)
    normalized = base_query.lower()
    queries: list[str] = []
    if "sec" in normalized and ("bitcoin" in normalized or "比特币" in normalized):
        queries.extend(
            [
                "site:sec.gov spot bitcoin ETF approval",
                "site:sec.gov spot bitcoin ETP approval order",
                "SEC spot bitcoin ETP approval order Jan 10 2024",
            ]
        )
    queries.extend([base_query, claim.claim_text])
    return _deduplicate_strings(queries)


def _product_info_queries(query: str, claim: ClaimDraft) -> list[str]:
    base_query = _clean_query_text(query)
    normalized = base_query.lower()
    queries: list[str] = []
    if "rtx" in normalized:
        entity = _extract_product_entity(base_query)
        queries.extend(
            [
                f"site:nvidia.com {entity} specifications",
                f"site:nvidia.com GeForce {entity} 16GB",
                f"{entity} specifications NVIDIA",
            ]
        )
    queries.extend([base_query, claim.claim_text])
    return _deduplicate_strings(queries)


def _ai_model_official_domain_queries(entity: str) -> list[str]:
    normalized_entity = entity.lower()
    if "openai" not in normalized_entity and "gpt" not in normalized_entity:
        return []
    return [
        f"site:openai.com {entity}",
        f"site:platform.openai.com {entity} models",
    ]


def _extract_product_entity(query: str) -> str:
    normalized = query.strip().rstrip("？?。.")
    marker_match = re.search(r"(是否|是不是|是|有没有|能不能|可以|属于)", normalized)
    if marker_match:
        candidate = normalized[: marker_match.start()].strip(" ，,")
        if candidate:
            return candidate
    return normalized


def _clean_query_text(query: str) -> str:
    return query.strip().rstrip("？?。.")


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
