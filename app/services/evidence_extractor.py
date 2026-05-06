import re
from dataclasses import dataclass
from typing import Protocol

from app.schemas.evidence import EvidenceSchema, SupportType
from app.schemas.page import PageFetchResultSchema
from app.services.claim_decomposer import ClaimDraft

MAX_EVIDENCE_SENTENCES = 3

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
        sentences = split_sentences(request.page_fetch_result.text)
        matched_sentences = self._match_sentences(request.claim, sentences)
        if not matched_sentences:
            return []

        evidence_text = " ".join(matched_sentences[:MAX_EVIDENCE_SENTENCES]).strip()
        if not evidence_text:
            return []

        support_type = infer_support_type(request.claim.claim_type, evidence_text)
        return [
            EvidenceSchema(
                evidence_id=f"ev-{request.claim.claim_id}-{request.source_id}-1",
                claim_id=request.claim.claim_id,
                source_id=request.source_id,
                evidence_text=evidence_text,
                support_type=support_type,
                relevance_score=relevance_score_for(support_type, len(matched_sentences)),
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


def relevance_score_for(support_type: SupportType, matched_sentence_count: int) -> float:
    base_scores = {
        SupportType.SUPPORT: 0.82,
        SupportType.OPPOSE: 0.78,
        SupportType.PARTIAL: 0.68,
        SupportType.NEUTRAL: 0.40,
    }
    bonus = min(max(matched_sentence_count - 1, 0) * 0.03, 0.08)
    return min(base_scores[support_type] + bonus, 1.0)


def _keywords_for_claim(claim: ClaimDraft) -> tuple[str, ...]:
    configured = _CLAIM_KEYWORDS.get(claim.claim_type)
    if configured:
        return tuple(keyword.lower() for keyword in configured)

    claim_terms = re.findall(r"[\w.-]+|[\u4e00-\u9fff]{2,}", claim.claim_text.lower())
    return tuple(claim_terms)
