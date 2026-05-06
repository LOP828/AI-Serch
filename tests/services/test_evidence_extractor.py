from app.schemas.evidence import SupportType
from app.schemas.page import PageFetchResultSchema
from app.schemas.source import FetchStatus
from app.services.claim_decomposer import ClaimDraft
from app.services.evidence_extractor import (
    EvidenceExtractionRequest,
    RuleBasedEvidenceExtractor,
    split_sentences,
)


def test_extracts_support_evidence_from_weight_text() -> None:
    evidence = _extract(
        claim=ClaimDraft("c2", "MiroThinker 1.7 是否公开模型权重", "model_weights"),
        text="The model files and weights are available in safetensors format.",
    )

    assert len(evidence) == 1
    assert evidence[0].claim_id == "c2"
    assert evidence[0].source_id == "s1"
    assert evidence[0].support_type == SupportType.SUPPORT
    assert evidence[0].evidence_text == (
        "The model files and weights are available in safetensors format."
    )


def test_extracts_license_evidence() -> None:
    evidence = _extract(
        claim=ClaimDraft("c5", "MiroThinker 1.7 的许可证是否允许商用", "license"),
        text="License Apache-2.0 allows commercial use.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.SUPPORT
    assert "commercial use" in evidence[0].evidence_text


def test_extracts_code_evidence_from_github_text() -> None:
    evidence = _extract(
        claim=ClaimDraft("c3", "MiroThinker 1.7 是否公开训练代码", "source_code"),
        text="The GitHub repository provides source code for MiroThinker.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.SUPPORT
    assert "source code" in evidence[0].evidence_text


def test_extracts_oppose_evidence_from_negated_training_data_text() -> None:
    evidence = _extract(
        claim=ClaimDraft("c4", "MiroThinker 1.7 是否公开训练数据", "training_data"),
        text="The training data is not disclosed.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.OPPOSE


def test_returns_empty_list_when_no_relevant_sentence_exists() -> None:
    evidence = _extract(
        claim=ClaimDraft("c4", "MiroThinker 1.7 是否公开训练数据", "training_data"),
        text="This page only discusses benchmark results.",
    )

    assert evidence == []


def test_evidence_text_is_limited_to_three_sentences() -> None:
    evidence = _extract(
        claim=ClaimDraft("c2", "MiroThinker 1.7 是否公开模型权重", "model_weights"),
        text=(
            "Weights are available. Model files are downloadable. "
            "The checkpoint is listed. Safetensors files are included."
        ),
    )

    assert len(split_sentences(evidence[0].evidence_text)) == 3


def test_support_type_and_relevance_score_are_valid() -> None:
    evidence = _extract(
        claim=ClaimDraft("c6", "MiroThinker 1.7 是否能严格称为开源模型", "interpretation"),
        text="It is described as an open-weight model.",
    )

    assert evidence[0].support_type in set(SupportType)
    assert evidence[0].support_type == SupportType.PARTIAL
    assert 0.0 <= evidence[0].relevance_score <= 1.0
    assert evidence[0].final_score is None


def _extract(claim: ClaimDraft, text: str):
    page = PageFetchResultSchema(
        url="https://example.com/page",
        title="Example",
        text=text,
        fetch_status=FetchStatus.SUCCESS,
    )
    request = EvidenceExtractionRequest(
        claim=claim,
        page_fetch_result=page,
        source_id="s1",
    )
    return RuleBasedEvidenceExtractor().extract(request)
