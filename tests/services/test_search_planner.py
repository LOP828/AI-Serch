from app.schemas.search import SearchPlanItemSchema
from app.schemas.source import SourceType
from app.schemas.trusted_search import QuestionType, Strictness
from app.services.claim_decomposer import decompose_claims
from app.services.search_planner import build_search_plan


def _queries_for(query: str, strictness: Strictness = Strictness.BALANCED) -> list[str]:
    claims = decompose_claims(query, QuestionType.AI_MODEL_INFO)
    search_plan = build_search_plan(
        query=query,
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
        strictness=strictness,
    )
    return [query for item in search_plan for query in item.queries]


def _queries_for_type(
    query: str,
    question_type: QuestionType,
    strictness: Strictness = Strictness.BALANCED,
) -> list[str]:
    claims = decompose_claims(query, question_type)
    search_plan = build_search_plan(
        query=query,
        question_type=question_type,
        claims=claims,
        strictness=strictness,
    )
    return [query for item in search_plan for query in item.queries]


def test_ai_model_search_plan_contains_expected_query_templates() -> None:
    claims = decompose_claims("MiroThinker 1.7 是不是开源模型？", QuestionType.AI_MODEL_INFO)

    search_plan = build_search_plan(
        query="MiroThinker 1.7 是不是开源模型？",
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
    )

    all_queries = {query for item in search_plan for query in item.queries}
    assert "MiroThinker 1.7 Hugging Face" in all_queries
    assert "MiroThinker 1.7 GitHub" in all_queries
    assert "MiroThinker 1.7 paper" in all_queries
    assert "MiroThinker 1.7 arXiv" in all_queries
    assert "MiroThinker 1.7 license" in all_queries
    assert "MiroThinker 1.7 official" in all_queries
    assert '"MiroThinker 1.7"' in all_queries
    assert "MiroThinker 1.7 model card" in all_queries
    assert '"MiroThinker 1.7" model card' in all_queries


def test_each_claim_has_at_least_one_bound_query() -> None:
    claims = decompose_claims("MiroThinker 1.7 是不是开源模型？", QuestionType.AI_MODEL_INFO)

    search_plan = build_search_plan(
        query="MiroThinker 1.7 是不是开源模型？",
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
    )

    assert {item.claim_id for item in search_plan} == {claim.claim_id for claim in claims}
    assert all(item.queries for item in search_plan)


def test_search_plan_item_schema_fields_are_complete() -> None:
    item = SearchPlanItemSchema(
        claim_id="c1",
        queries=["MiroThinker 1.7 Hugging Face"],
        preferred_source_types=[SourceType.OFFICIAL_MODEL_CARD],
    )

    dumped = item.model_dump()
    assert set(dumped) == {"claim_id", "queries", "preferred_source_types"}


def test_ai_model_search_plan_contains_quoted_exact_entity_query() -> None:
    queries = _queries_for("MiroThinker 1.7 是不是开源模型？")

    assert '"MiroThinker 1.7"' in queries


def test_ai_model_search_plan_preserves_gpt_version_string() -> None:
    queries = _queries_for("GPT-4.1 是否是 OpenAI 发布的模型？")

    assert "GPT-4.1" in queries
    assert '"GPT-4.1"' in queries
    assert "GPT-4.1 official" in queries
    assert "site:openai.com GPT-4.1" in queries
    assert "site:platform.openai.com GPT-4.1 models" in queries
    assert '"GPT-4.1" model card' in queries
    assert all("GPT-4 " not in query for query in queries)


def test_ai_model_search_plan_preserves_llama_version_string() -> None:
    queries = _queries_for("Llama 3.1 是否公开模型权重并允许商用？")

    assert "Llama 3.1" in queries
    assert '"Llama 3.1"' in queries
    assert "Llama 3.1 Hugging Face" in queries
    assert '"Llama 3.1" license' in queries
    assert "Llama 3.1 GitHub" in queries
    assert "Llama 3.1 arXiv" in queries
    assert "Llama 3.1 model card" in queries


def test_ai_model_search_plan_preserves_mirothinker_version_string() -> None:
    queries = _queries_for("MiroThinker 1.7 是不是开源模型？")

    assert "MiroThinker 1.7" in queries
    assert '"MiroThinker 1.7"' in queries
    assert "MiroThinker 1.7 GitHub" in queries
    assert "MiroThinker 1.7 license" in queries


def test_balanced_ai_model_plan_contains_official_source_biased_queries() -> None:
    queries = _queries_for("MiroThinker 1.7 是不是开源模型？", Strictness.BALANCED)

    assert "MiroThinker 1.7 official" in queries
    assert "MiroThinker 1.7 Hugging Face" in queries
    assert "MiroThinker 1.7 GitHub" in queries
    assert "MiroThinker 1.7 paper" in queries
    assert "MiroThinker 1.7 arXiv" in queries
    assert "MiroThinker 1.7 license" in queries
    assert "MiroThinker 1.7 model card" in queries


def test_strict_ai_model_plan_contains_site_biased_queries() -> None:
    queries = _queries_for("MiroThinker 1.7 是不是开源模型？", Strictness.STRICT)

    assert "MiroThinker 1.7 site:huggingface.co" in queries
    assert '"MiroThinker 1.7" site:huggingface.co' in queries
    assert "MiroThinker 1.7 site:github.com" in queries
    assert '"MiroThinker 1.7" site:github.com' in queries
    assert "MiroThinker 1.7 official release" in queries


def test_loose_ai_model_plan_keeps_official_queries_and_adds_broader_queries() -> None:
    queries = _queries_for("MiroThinker 1.7 是不是开源模型？", Strictness.LOOSE)

    assert "MiroThinker 1.7 official" in queries
    assert "MiroThinker 1.7 Hugging Face" in queries
    assert "MiroThinker 1.7 GitHub" in queries
    assert "MiroThinker 1.7 release" in queries
    assert "MiroThinker 1.7 announcement" in queries
    assert "MiroThinker 1.7 technical report" in queries


def test_openai_gpt_queries_include_official_openai_site_queries_for_all_strictness() -> None:
    for strictness in (Strictness.STRICT, Strictness.BALANCED, Strictness.LOOSE):
        queries = _queries_for("GPT-4.1 是否是 OpenAI 发布的模型？", strictness)

        assert "site:openai.com GPT-4.1" in queries
        assert "site:platform.openai.com GPT-4.1 models" in queries
        assert "GPT-4.1 site:huggingface.co" in queries
        assert "GPT-4.1 site:github.com" in queries


def test_policy_legal_sec_bitcoin_spot_etf_query_includes_sec_official_queries() -> None:
    queries = _queries_for_type(
        "美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？",
        QuestionType.POLICY_LEGAL,
    )

    assert "site:sec.gov spot bitcoin ETF approval" in queries
    assert "site:sec.gov spot bitcoin ETP approval order" in queries
    assert "SEC spot bitcoin ETP approval order Jan 10 2024" in queries


def test_product_info_rtx_query_includes_nvidia_official_spec_queries() -> None:
    queries = _queries_for_type(
        "RTX 5070 Ti 是否是 16GB 显存？",
        QuestionType.PRODUCT_INFO,
    )

    assert "site:nvidia.com RTX 5070 Ti specifications" in queries
    assert "site:nvidia.com GeForce RTX 5070 Ti 16GB" in queries
    assert "RTX 5070 Ti specifications NVIDIA" in queries


def test_ai_model_preferred_source_types_prioritize_primary_sources() -> None:
    claims = decompose_claims("MiroThinker 1.7 是不是开源模型？", QuestionType.AI_MODEL_INFO)

    search_plan = build_search_plan(
        query="MiroThinker 1.7 是不是开源模型？",
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
    )

    for item in search_plan:
        assert SourceType.OFFICIAL_MODEL_CARD in item.preferred_source_types
        assert SourceType.SOURCE_CODE_REPO in item.preferred_source_types
        assert SourceType.ACADEMIC_PAPER in item.preferred_source_types
        assert SourceType.OFFICIAL_DOCS in item.preferred_source_types
        assert SourceType.OFFICIAL_BLOG in item.preferred_source_types


def test_ai_model_queries_are_deduplicated_with_stable_order() -> None:
    claims = decompose_claims("MiroThinker 1.7 是不是开源模型？", QuestionType.AI_MODEL_INFO)

    first_plan = build_search_plan(
        query="MiroThinker 1.7 是不是开源模型？",
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
        strictness=Strictness.BALANCED,
    )
    second_plan = build_search_plan(
        query="MiroThinker 1.7 是不是开源模型？",
        question_type=QuestionType.AI_MODEL_INFO,
        claims=claims,
        strictness=Strictness.BALANCED,
    )

    assert first_plan == second_plan
    for item in first_plan:
        assert item.queries == list(dict.fromkeys(item.queries))
