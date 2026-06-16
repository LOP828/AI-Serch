from app.schemas.trusted_search import QuestionType
from app.services.claim_decomposer import decompose_claims


def test_decomposes_ai_model_open_source_question() -> None:
    claims = decompose_claims("MiroThinker 1.7 是不是开源模型？", QuestionType.AI_MODEL_INFO)

    assert [claim.claim_id for claim in claims] == ["c1", "c2", "c3", "c4", "c5", "c6"]
    assert [claim.claim_type for claim in claims] == [
        "existence",
        "model_weights",
        "source_code",
        "training_data",
        "license",
        "interpretation",
    ]
    assert [claim.claim_text for claim in claims] == [
        "MiroThinker 1.7 是否存在公开发布页面",
        "MiroThinker 1.7 是否公开模型权重",
        "MiroThinker 1.7 是否公开训练代码",
        "MiroThinker 1.7 是否公开训练数据",
        "MiroThinker 1.7 的许可证是否允许商用",
        "MiroThinker 1.7 是否能严格称为开源模型",
    ]


def test_decomposes_ai_model_release_origin_question() -> None:
    claims = decompose_claims("GPT-4.1 是否是 OpenAI 发布的模型？", QuestionType.AI_MODEL_INFO)

    assert [claim.claim_id for claim in claims] == ["c1", "c2", "c3"]
    assert [claim.claim_type for claim in claims] == [
        "official_release_page",
        "model_provider",
        "model_access",
    ]
    assert [claim.claim_text for claim in claims] == [
        "GPT-4.1 是否存在 OpenAI 官方发布或文档页面",
        "GPT-4.1 是否由 OpenAI 提供或发布",
        "GPT-4.1 是否可通过 OpenAI API / platform 使用",
    ]
    assert "source_code" not in {claim.claim_type for claim in claims}
    assert "training_data" not in {claim.claim_type for claim in claims}
    assert "license" not in {claim.claim_type for claim in claims}
    assert "interpretation" not in {claim.claim_type for claim in claims}


def test_gpt_open_source_question_still_uses_open_source_template() -> None:
    claims = decompose_claims("GPT-4.1 是否开源？", QuestionType.AI_MODEL_INFO)

    assert [claim.claim_type for claim in claims] == [
        "existence",
        "model_weights",
        "source_code",
        "training_data",
        "license",
        "interpretation",
    ]
    assert [claim.claim_text for claim in claims] == [
        "GPT-4.1 是否存在公开发布页面",
        "GPT-4.1 是否公开模型权重",
        "GPT-4.1 是否公开训练代码",
        "GPT-4.1 是否公开训练数据",
        "GPT-4.1 的许可证是否允许商用",
        "GPT-4.1 是否能严格称为开源模型",
    ]


def test_llama_weights_and_commercial_query_still_uses_open_source_template() -> None:
    claims = decompose_claims(
        "Llama 3.1 是否公开模型权重并允许商用？",
        QuestionType.AI_MODEL_INFO,
    )

    assert "model_weights" in {claim.claim_type for claim in claims}
    assert "license" in {claim.claim_type for claim in claims}
    assert "interpretation" in {claim.claim_type for claim in claims}
    assert "official_release_page" not in {claim.claim_type for claim in claims}
    assert "Llama 3.1 是否公开模型权重" in [claim.claim_text for claim in claims]
    assert "Llama 3.1 的许可证是否允许商用" in [claim.claim_text for claim in claims]


def test_non_ai_model_question_uses_general_fallback_claim() -> None:
    claims = decompose_claims("法国的首都是什么？", QuestionType.GENERAL_FACT)

    assert len(claims) == 1
    assert claims[0].claim_id == "c1"
    assert claims[0].claim_type == "general_fact"
    assert claims[0].claim_text == "法国的首都是什么？ 这一问题可以被外部来源验证"
