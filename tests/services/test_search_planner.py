from app.schemas.search import SearchPlanItemSchema
from app.schemas.source import SourceType
from app.schemas.trusted_search import QuestionType
from app.services.claim_decomposer import decompose_claims
from app.services.search_planner import build_search_plan


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
