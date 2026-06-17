import re
from dataclasses import dataclass
from typing import Protocol

from app.schemas.evidence import EvidenceSchema, SupportType
from app.schemas.page import PageFetchResultSchema
from app.services.claim_decomposer import ClaimDraft

MAX_EVIDENCE_SENTENCES = 3

# Claim types that are about a specific AI model and therefore version-sensitive.
# General-fact claims (tech_news / product_info / policy_legal) are intentionally
# excluded so the guard never touches non-model questions.
_VERSION_SENSITIVE_CLAIM_TYPES = frozenset(
    {
        "existence",
        "model_weights",
        "source_code",
        "training_data",
        "license",
        "interpretation",
    }
)

# Relevance multiplier applied to evidence that mentions a *different* version of
# the same model family than the one being asked about (e.g. "LLaMA-13B" evidence
# for a "Llama 3.1" claim). The mismatched evidence is downweighted before scoring
# rather than dropped, so it stays visible in the package but cannot dominate.
ENTITY_VERSION_MISMATCH_FACTOR = 0.4

# A version-ish token: dotted versions (3.1, 4.1, 2.5) or parameter sizes (7B, 13B).
_VERSION_TOKEN_PATTERN = re.compile(r"\d+\.\d+(?:\.\d+)*|\d+\s?b\b")
_CLAIM_MARKER_PATTERN = re.compile(r"是不是|是否|是|有没有|能不能|可以|属于|的")
_RTX_MODEL_PATTERN = re.compile(
    r"\brtx\s+\d{4}(?:\s+(?:ti|super|laptop))?\b",
    re.IGNORECASE,
)
_MEMORY_VALUE_PATTERN = re.compile(r"\b(\d{1,3})\s*(?:gb|g)\b", re.IGNORECASE)
_MEMORY_SPEC_TERMS = ("显存", "vram", "memory size", "graphics memory")

_NEGATION_TERMS = (
    " not ",
    " no ",
    "without",
    "not disclosed",
    "not released",
    "not available",
    "未",
    "没有",
    "不公开",
    "未公开",
    "未披露",
    "不能",
)

_CLAIM_KEYWORDS = {
    "existence": (
        "model card",
        "release",
        "released",
        "available",
        "发布",
        "模型卡",
        "页面",
    ),
    "model_weights": (
        "weights",
        "model files",
        "safetensors",
        "checkpoint",
        "权重",
        "模型文件",
    ),
    "source_code": (
        "github",
        "source code",
        "training code",
        "repository",
        "repo",
        "代码",
        "训练代码",
    ),
    "training_data": (
        "training data",
        "dataset",
        "data",
        "训练数据",
        "数据集",
    ),
    "license": (
        "license",
        "apache",
        "mit",
        "commercial use",
        "商用",
        "许可证",
    ),
    "interpretation": (
        "open source",
        "open-weight",
        "open weight",
        "开源",
        "开放权重",
    ),
}


@dataclass(frozen=True)
class EvidenceExtractionRequest:
    claim: ClaimDraft
    page_fetch_result: PageFetchResultSchema
    source_id: str


class EvidenceExtractorProtocol(Protocol):
    def extract(self, request: EvidenceExtractionRequest) -> list[EvidenceSchema]:
        """Extract evidence from provided page text only."""


class RuleBasedEvidenceExtractor:
    def extract(self, request: EvidenceExtractionRequest) -> list[EvidenceSchema]:
        product_spec_evidence = _extract_product_memory_spec_evidence(request)
        if product_spec_evidence is not None:
            return product_spec_evidence

        sentences = split_sentences(request.page_fetch_result.text)
        matched_sentences = self._match_sentences(request.claim, sentences)
        if not matched_sentences:
            return []

        evidence_text = " ".join(matched_sentences[:MAX_EVIDENCE_SENTENCES]).strip()
        if not evidence_text:
            return []

        support_type = infer_support_type(request.claim.claim_type, evidence_text)
        relevance_score = relevance_score_for(support_type, len(matched_sentences))
        relevance_score *= entity_version_relevance_factor(request.claim, evidence_text)
        return [
            EvidenceSchema(
                evidence_id=f"ev-{request.claim.claim_id}-{request.source_id}-1",
                claim_id=request.claim.claim_id,
                source_id=request.source_id,
                evidence_text=evidence_text,
                support_type=support_type,
                relevance_score=round(relevance_score, 4),
            )
        ]

    def _match_sentences(self, claim: ClaimDraft, sentences: list[str]) -> list[str]:
        keywords = _keywords_for_claim(claim)
        return [
            sentence
            for sentence in sentences
            if any(keyword in sentence.lower() for keyword in keywords)
        ]


class LLMEvidenceExtractor:
    def extract(self, request: EvidenceExtractionRequest) -> list[EvidenceSchema]:
        del request
        raise NotImplementedError("LLM evidence extraction is reserved for a later stage.")


def extract_evidence_for_claims(
    claims: list[ClaimDraft],
    page_fetches: list[PageFetchResultSchema],
    source_ids: list[str],
    extractor: EvidenceExtractorProtocol | None = None,
) -> dict[str, list[EvidenceSchema]]:
    active_extractor = extractor or RuleBasedEvidenceExtractor()
    evidence_by_claim_id: dict[str, list[EvidenceSchema]] = {claim.claim_id: [] for claim in claims}
    for claim in claims:
        for source_id, page_fetch in zip(source_ids, page_fetches, strict=False):
            request = EvidenceExtractionRequest(
                claim=claim,
                page_fetch_result=page_fetch,
                source_id=source_id,
            )
            evidence_by_claim_id[claim.claim_id].extend(active_extractor.extract(request))
    return evidence_by_claim_id


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def infer_support_type(claim_type: str, evidence_text: str) -> SupportType:
    normalized = f" {evidence_text.lower()} "
    has_negation = any(term in normalized for term in _NEGATION_TERMS)
    if has_negation:
        return SupportType.OPPOSE
    if claim_type == "interpretation" and (
        "open-weight" in normalized or "open weight" in normalized or "开放权重" in normalized
    ):
        return SupportType.PARTIAL
    return SupportType.SUPPORT


def _extract_product_memory_spec_evidence(
    request: EvidenceExtractionRequest,
) -> list[EvidenceSchema] | None:
    spec = _product_memory_spec_from_claim(request.claim.claim_text)
    if spec is None:
        return None

    matched: list[tuple[str, SupportType]] = []
    for sentence in split_sentences(request.page_fetch_result.text):
        support_type = _product_memory_sentence_support_type(sentence, spec)
        if support_type is not None:
            matched.append((sentence, support_type))

    if not matched:
        return []

    support_type = (
        SupportType.SUPPORT
        if any(item_support_type == SupportType.SUPPORT for _, item_support_type in matched)
        else SupportType.OPPOSE
    )
    evidence_text = " ".join(sentence for sentence, _ in matched[:MAX_EVIDENCE_SENTENCES]).strip()
    relevance_score = relevance_score_for(support_type, len(matched))
    return [
        EvidenceSchema(
            evidence_id=f"ev-{request.claim.claim_id}-{request.source_id}-1",
            claim_id=request.claim.claim_id,
            source_id=request.source_id,
            evidence_text=evidence_text,
            support_type=support_type,
            relevance_score=round(relevance_score, 4),
        )
    ]


@dataclass(frozen=True)
class _ProductMemorySpec:
    model: str
    memory_gb: int


def _product_memory_spec_from_claim(claim_text: str) -> _ProductMemorySpec | None:
    normalized = _normalize_product_spec_text(claim_text)
    if not any(term in normalized for term in _MEMORY_SPEC_TERMS):
        return None

    model = _first_rtx_model(normalized)
    memory_gb = _first_memory_value_gb(normalized)
    if model is None or memory_gb is None:
        return None
    return _ProductMemorySpec(model=model, memory_gb=memory_gb)


def _product_memory_sentence_support_type(
    sentence: str,
    spec: _ProductMemorySpec,
) -> SupportType | None:
    normalized = _normalize_product_spec_text(sentence)
    if not _contains_exact_product_model(normalized, spec.model):
        return None

    memory_values = _memory_values_gb(normalized)
    if not memory_values:
        return None
    if spec.memory_gb in memory_values:
        return SupportType.SUPPORT
    return SupportType.OPPOSE


def _normalize_product_spec_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("-", " ")).strip()


def _first_rtx_model(text: str) -> str | None:
    models = _rtx_models(text)
    return models[0] if models else None


def _first_memory_value_gb(text: str) -> int | None:
    values = _memory_values_gb(text)
    return values[0] if values else None


def _memory_values_gb(text: str) -> list[int]:
    return [int(match.group(1)) for match in _MEMORY_VALUE_PATTERN.finditer(text)]


def _contains_exact_product_model(text: str, model: str) -> bool:
    return model in _rtx_models(text)


def _rtx_models(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", match.group(0).lower()).strip()
        for match in _RTX_MODEL_PATTERN.finditer(text)
    ]


def relevance_score_for(support_type: SupportType, matched_sentence_count: int) -> float:
    base_scores = {
        SupportType.SUPPORT: 0.82,
        SupportType.OPPOSE: 0.78,
        SupportType.PARTIAL: 0.68,
        SupportType.NEUTRAL: 0.40,
    }
    bonus = min(max(matched_sentence_count - 1, 0) * 0.03, 0.08)
    return min(base_scores[support_type] + bonus, 1.0)


def entity_version_relevance_factor(claim: ClaimDraft, evidence_text: str) -> float:
    """Downweight evidence that talks about a different version of the same model.

    Returns ``1.0`` (no change) unless the claim targets a specific versioned model
    (e.g. "Llama 3.1") and the evidence both mentions the model family and a
    *different* version token, without mentioning the target version. This catches
    the eval_002 failure mode where "LLaMA-13B" / older-LLaMA evidence was scored
    as if it were about Llama 3.1. Evidence that simply omits the version number is
    left untouched, so mock fixtures and version-agnostic sentences are unaffected.
    """
    if claim.claim_type not in _VERSION_SENSITIVE_CLAIM_TYPES:
        return 1.0

    target_version = _target_version(claim.claim_text)
    if not target_version:
        return 1.0

    text = evidence_text.lower()
    if _contains_version_token(text, target_version):
        return 1.0

    family = _family_name(claim.claim_text)
    if not family or family not in text:
        return 1.0

    other_versions = _version_tokens(text) - {target_version}
    if other_versions:
        return ENTITY_VERSION_MISMATCH_FACTOR
    return 1.0


def _claim_entity(claim_text: str) -> str:
    normalized = claim_text.strip().rstrip("？?。.")
    marker_match = _CLAIM_MARKER_PATTERN.search(normalized)
    if marker_match:
        candidate = normalized[: marker_match.start()].strip(" ，,")
        if candidate:
            return candidate
    return normalized


def _target_version(claim_text: str) -> str | None:
    entity = _claim_entity(claim_text)
    match = re.search(r"\d+\.\d+(?:\.\d+)*", entity)
    return match.group(0) if match else None


def _family_name(claim_text: str) -> str | None:
    entity = _claim_entity(claim_text)
    match = re.search(r"[A-Za-z][A-Za-z-]{1,}", entity)
    return match.group(0).lower() if match else None


def _contains_version_token(text: str, version: str) -> bool:
    return re.search(rf"(?<!\d){re.escape(version)}(?!\d)", text) is not None


def _version_tokens(text: str) -> set[str]:
    return {match.group(0).replace(" ", "") for match in _VERSION_TOKEN_PATTERN.finditer(text)}


def _keywords_for_claim(claim: ClaimDraft) -> tuple[str, ...]:
    configured = _CLAIM_KEYWORDS.get(claim.claim_type)
    if configured:
        return tuple(keyword.lower() for keyword in configured)

    claim_terms = re.findall(r"[\w.-]+|[\u4e00-\u9fff]{2,}", claim.claim_text.lower())
    return tuple(claim_terms)
