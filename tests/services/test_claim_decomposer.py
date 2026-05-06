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


def test_non_ai_model_question_uses_general_fallback_claim() -> None:
    claims = decompose_claims("法国的首都是什么？", QuestionType.GENERAL_FACT)

    assert len(claims) == 1
    assert claims[0].claim_id == "c1"
    assert claims[0].claim_type == "general_fact"
    assert claims[0].claim_text == "法国的首都是什么？ 这一问题可以被外部来源验证"
