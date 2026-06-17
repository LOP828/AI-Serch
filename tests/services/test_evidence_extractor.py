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


def test_mismatched_model_version_is_downweighted() -> None:
    matched = _extract(
        claim=ClaimDraft("c2", "Llama 3.1 是否公开模型权重", "model_weights"),
        text="Llama 3.1 weights are available in safetensors format.",
    )
    mismatched = _extract(
        claim=ClaimDraft("c2", "Llama 3.1 是否公开模型权重", "model_weights"),
        text="The LLaMA-13B weights are available in safetensors format.",
    )

    assert matched and mismatched
    assert mismatched[0].relevance_score < matched[0].relevance_score
    assert mismatched[0].relevance_score == round(matched[0].relevance_score * 0.4, 4)


def test_version_absent_without_conflict_is_not_penalized() -> None:
    with_version = _extract(
        claim=ClaimDraft("c2", "Llama 3.1 是否公开模型权重", "model_weights"),
        text="Llama 3.1 weights are available in safetensors format.",
    )
    version_omitted = _extract(
        claim=ClaimDraft("c2", "Llama 3.1 是否公开模型权重", "model_weights"),
        text="The model files and weights are available in safetensors format.",
    )

    assert with_version and version_omitted
    assert version_omitted[0].relevance_score == with_version[0].relevance_score


def test_product_memory_spec_general_fact_claim_returns_relevant_evidence() -> None:
    claim_text = "RTX 5070 Ti 是不是 16GB 显存 这一问题可以被外部来源验证"
    evidence = _extract(
        claim=ClaimDraft("c1", claim_text, "general_fact"),
        text="The RTX 5070 Ti 12GB variant uses GDDR7 memory.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.OPPOSE


def test_rtx_5070_ti_16g_supports_16gb_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text="PC Specifications GPU: MSI GeForce RTX 5070 Ti 16G Ventus 3X OC.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.SUPPORT


def test_rtx_5070_ti_16gb_supports_16gb_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text="My system specs: GPU: MSI GeForce RTX 5070 Ti 16GB.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.SUPPORT


def test_rtx_5070_16gb_does_not_support_rtx_5070_ti_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text="The GeForce RTX 5070 16GB card is listed with GDDR7 memory.",
    )

    assert evidence == []


def test_rtx_5080_16gb_does_not_support_rtx_5070_ti_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text="The GeForce RTX 5080 16GB card is listed with GDDR7 memory.",
    )

    assert evidence == []


def test_rtx_5070_ti_12gb_opposes_16gb_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text="The GeForce RTX 5070 Ti 12GB variant uses GDDR7 memory.",
    )

    assert len(evidence) == 1
    assert evidence[0].support_type == SupportType.OPPOSE


def test_other_model_memory_values_do_not_oppose_rtx_5070_ti_memory_claim() -> None:
    evidence = _extract(
        claim=ClaimDraft("c1", "RTX 5070 Ti 是否是 16GB 显存？", "general_fact"),
        text=(
            "The GeForce RTX 5070 12GB card is listed with GDDR7 memory. "
            "The GeForce RTX 5080 24GB card is listed with GDDR7 memory."
        ),
    )

    assert evidence == []


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
