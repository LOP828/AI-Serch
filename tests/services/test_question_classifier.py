from app.schemas.trusted_search import QuestionType, RiskLevel
from app.services.question_classifier import classify_question


def test_classifies_ai_model_info() -> None:
    result = classify_question("MiroThinker 1.7 是不是开源模型？")

    assert result.question_type == QuestionType.AI_MODEL_INFO
    assert result.risk_level == RiskLevel.MEDIUM


def test_classifies_tech_news() -> None:
    result = classify_question("OpenAI 下周会发布某个代号模型吗？")

    assert result.question_type == QuestionType.TECH_NEWS
    assert result.risk_level == RiskLevel.MEDIUM


def test_classifies_product_info() -> None:
    result = classify_question("某款笔记本的 RTX 5070 Ti 是不是 12GB 显存？")

    assert result.question_type == QuestionType.PRODUCT_INFO
    assert result.risk_level == RiskLevel.MEDIUM


def test_classifies_policy_legal() -> None:
    result = classify_question("某项政策现在是否还有效？")

    assert result.question_type == QuestionType.POLICY_LEGAL
    assert result.risk_level == RiskLevel.HIGH


def test_classifies_technical_doc() -> None:
    result = classify_question("FastAPI 的 Depends 怎么使用？")

    assert result.question_type == QuestionType.TECHNICAL_DOC
    assert result.risk_level == RiskLevel.LOW


def test_classifies_general_fact() -> None:
    result = classify_question("法国的首都是什么？")

    assert result.question_type == QuestionType.GENERAL_FACT
    assert result.risk_level == RiskLevel.LOW


def test_classifies_unknown() -> None:
    result = classify_question("这个东西到底怎么样？")

    assert result.question_type == QuestionType.UNKNOWN
    assert result.risk_level == RiskLevel.MEDIUM
