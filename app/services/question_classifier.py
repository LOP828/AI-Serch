from dataclasses import dataclass

from app.schemas.trusted_search import QuestionType, RiskLevel


@dataclass(frozen=True)
class ClassifiedQuestion:
    question_type: QuestionType
    risk_level: RiskLevel


_CLASSIFICATION_RULES: tuple[tuple[QuestionType, tuple[str, ...]], ...] = (
    (
        QuestionType.POLICY_LEGAL,
        (
            "政策",
            "法规",
            "法律",
            "监管",
            "政府",
            "是否有效",
            "条例",
            "办法",
        ),
    ),
    (
        QuestionType.TECH_NEWS,
        (
            "发布",
            "爆料",
            "传言",
            "最新",
            "下周",
            "消息",
            "官宣",
            "泄露",
            "新闻",
        ),
    ),
    (
        QuestionType.PRODUCT_INFO,
        (
            "价格",
            "显存",
            "配置",
            "商品",
            "京东",
            "天猫",
            "型号",
            "评测",
            "参数",
            "gb",
            "rtx",
        ),
    ),
    (
        QuestionType.AI_MODEL_INFO,
        (
            "模型",
            "llm",
            "hugging face",
            "开源",
            "权重",
            "license",
            "github",
            "模型卡",
            "参数量",
            "safetensors",
        ),
    ),
    (
        QuestionType.TECHNICAL_DOC,
        (
            "python",
            "api",
            "报错",
            "函数",
            "库",
            "文档",
            "sdk",
            "框架",
            "fastapi",
            "depends",
        ),
    ),
)

_GENERAL_FACT_MARKERS = (
    "是什么",
    "是谁",
    "什么时候",
    "在哪里",
    "哪一年",
    "哪个国家",
    "多少",
    "有多",
)

_RISK_BY_QUESTION_TYPE = {
    QuestionType.AI_MODEL_INFO: RiskLevel.MEDIUM,
    QuestionType.TECH_NEWS: RiskLevel.MEDIUM,
    QuestionType.PRODUCT_INFO: RiskLevel.MEDIUM,
    QuestionType.POLICY_LEGAL: RiskLevel.HIGH,
    QuestionType.TECHNICAL_DOC: RiskLevel.LOW,
    QuestionType.GENERAL_FACT: RiskLevel.LOW,
    QuestionType.UNKNOWN: RiskLevel.MEDIUM,
    QuestionType.AUTO: RiskLevel.MEDIUM,
}


def classify_question(query: str) -> ClassifiedQuestion:
    normalized = query.strip().lower()
    if not normalized:
        return ClassifiedQuestion(QuestionType.UNKNOWN, RiskLevel.MEDIUM)

    for question_type, keywords in _CLASSIFICATION_RULES:
        if any(keyword in normalized for keyword in keywords):
            return ClassifiedQuestion(question_type, risk_for_question_type(question_type))

    if any(marker in normalized for marker in _GENERAL_FACT_MARKERS):
        return ClassifiedQuestion(QuestionType.GENERAL_FACT, RiskLevel.LOW)

    return ClassifiedQuestion(QuestionType.UNKNOWN, RiskLevel.MEDIUM)


def risk_for_question_type(question_type: QuestionType) -> RiskLevel:
    return _RISK_BY_QUESTION_TYPE.get(question_type, RiskLevel.MEDIUM)
