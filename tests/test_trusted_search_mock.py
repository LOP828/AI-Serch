from fastapi.testclient import TestClient

from app.api.routes import trusted_search as trusted_search_route
from app.core.config import get_settings
from app.main import app
from app.schemas.search import SearchResultSchema
from app.schemas.trusted_search import OverallStatus, TrustedSearchResponse
from app.services.search_adapter import StaticSearchAdapter

client = TestClient(app)


def test_trusted_search_accepts_request() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={
            "query": "MiroThinker 1.7 是不是开源模型？",
            "question_type": "auto",
            "strictness": "balanced",
            "max_sources": 8,
            "require_primary_source": False,
            "return_raw_evidence": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "MiroThinker 1.7 是不是开源模型？"
    assert body["question_type"] == "ai_model_info"


def test_trusted_search_response_matches_schema() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    assert response.status_code == 200
    parsed = TrustedSearchResponse.model_validate(response.json())
    assert parsed.claims
    assert parsed.sources
    assert parsed.conflicts == []
    assert len(parsed.claims) == 6


def test_trusted_search_route_uses_search_provider_factory(monkeypatch) -> None:
    calls = []

    def build_test_adapter() -> StaticSearchAdapter:
        calls.append("factory_called")
        return StaticSearchAdapter(
            results=[
                SearchResultSchema(
                    title="Factory injected model card",
                    url="https://huggingface.co/example/factory-injected",
                    snippet=(
                        "MiroThinker 1.7 model files and weights are available. "
                        "License Apache-2.0 allows commercial use."
                    ),
                    published_at=None,
                )
            ]
        )

    monkeypatch.setattr(trusted_search_route, "build_search_adapter", build_test_adapter)

    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？", "max_sources": 1},
    )

    assert response.status_code == 200
    assert calls == ["factory_called"]
    body = response.json()
    assert [source["title"] for source in body["sources"]] == ["Factory injected model card"]


def test_trusted_search_tavily_disabled_route_path_does_not_network_or_crash(
    monkeypatch,
) -> None:
    def fail_if_network_is_called(*args, **kwargs):
        raise AssertionError("default Tavily disabled route path must not access network")

    monkeypatch.setenv("CSL_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("CSL_SEARCH_ALLOW_NETWORK", "false")
    monkeypatch.setenv("CSL_SEARCH_API_KEY", "")
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        fail_if_network_is_called,
    )
    get_settings.cache_clear()

    try:
        response = client.post(
            "/api/v1/trusted-search",
            json={"query": "OpenAI official blog", "max_sources": 1},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    parsed = TrustedSearchResponse.model_validate(response.json())
    assert parsed.sources == []
    assert parsed.overall_status == OverallStatus.UNSUPPORTED
    assert "api_key" not in response.text.lower()


def test_trusted_search_tavily_missing_api_key_route_path_does_not_crash_or_leak_key(
    monkeypatch,
) -> None:
    def fail_if_network_is_called(*args, **kwargs):
        raise AssertionError("Tavily without API key must not access network")

    monkeypatch.setenv("CSL_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("CSL_SEARCH_ALLOW_NETWORK", "true")
    monkeypatch.setenv("CSL_SEARCH_API_KEY", "")
    monkeypatch.setattr(
        "app.services.providers.tavily_provider.urllib_request.urlopen",
        fail_if_network_is_called,
    )
    get_settings.cache_clear()

    try:
        response = client.post(
            "/api/v1/trusted-search",
            json={"query": "OpenAI official blog", "max_sources": 1},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    parsed = TrustedSearchResponse.model_validate(response.json())
    assert parsed.sources == []
    assert parsed.overall_status == OverallStatus.UNSUPPORTED
    assert "api_key" not in response.text.lower()
    assert "authorization" not in response.text.lower()


def test_trusted_search_response_contains_required_fields() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    assert {
        "query",
        "question_type",
        "risk_level",
        "overall_status",
        "overall_confidence",
        "claims",
        "search_plan",
        "sources",
        "page_fetches",
        "conflicts",
        "answer_constraints",
    }.issubset(body)

    claim = body["claims"][0]
    assert {
        "claim_id",
        "claim_text",
        "claim_type",
        "status",
        "confidence",
        "reason",
        "evidence",
    }.issubset(claim)

    source = body["sources"][0]
    assert {
        "source_id",
        "title",
        "url",
        "source_type",
        "base_reliability",
        "is_primary_source",
    }.issubset(source)

    evidence = claim["evidence"][0]
    assert {
        "claim_id",
        "source_id",
        "evidence_text",
        "support_type",
        "relevance_score",
        "final_score",
        "score_breakdown",
    }.issubset(evidence)
    assert 0.0 <= evidence["final_score"] <= 1.0
    assert evidence["score_breakdown"]


def test_trusted_search_uses_classifier_and_decomposer() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    claim_texts = [claim["claim_text"] for claim in body["claims"]]
    assert body["question_type"] == "ai_model_info"
    assert body["risk_level"] == "medium"
    assert claim_texts == [
        "MiroThinker 1.7 是否存在公开发布页面",
        "MiroThinker 1.7 是否公开模型权重",
        "MiroThinker 1.7 是否公开训练代码",
        "MiroThinker 1.7 是否公开训练数据",
        "MiroThinker 1.7 的许可证是否允许商用",
        "MiroThinker 1.7 是否能严格称为开源模型",
    ]


def test_trusted_search_returns_claims_and_search_plan() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    assert len(body["claims"]) == 6
    assert len(body["search_plan"]) == 6
    assert {item["claim_id"] for item in body["search_plan"]} == {
        claim["claim_id"] for claim in body["claims"]
    }
    assert all(item["queries"] for item in body["search_plan"])


def test_trusted_search_returns_classified_sources() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    source_types = [source["source_type"] for source in body["sources"]]
    assert source_types == ["official_model_card", "source_code_repo"]
    assert body["sources"][0]["base_reliability"] == 0.88
    assert body["sources"][0]["is_primary_source"] is True


def test_trusted_search_returns_page_fetch_fallbacks_without_crashing() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["page_fetches"]) == len(body["sources"])
    assert {fetch["fetch_status"] for fetch in body["page_fetches"]} == {"fallback"}
    assert all(fetch["text"] for fetch in body["page_fetches"])


def test_trusted_search_returns_evidence_bound_to_claim_and_source() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    source_ids = {source["source_id"] for source in body["sources"]}
    claims_with_evidence = [claim for claim in body["claims"] if claim["evidence"]]
    assert claims_with_evidence
    for claim in claims_with_evidence:
        for evidence in claim["evidence"]:
            assert evidence["claim_id"] == claim["claim_id"]
            assert evidence["source_id"] in source_ids
            assert evidence["evidence_text"]
            assert evidence["support_type"] in {"support", "oppose", "partial", "neutral"}
            assert 0.0 <= evidence["relevance_score"] <= 1.0
            assert 0.0 <= evidence["final_score"] <= 1.0


def test_trusted_search_returns_scored_evidence() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    scored = [
        evidence
        for claim in body["claims"]
        for evidence in claim["evidence"]
        if evidence["final_score"] is not None
    ]
    assert scored
    for evidence in scored:
        assert evidence["source_score"] is not None
        assert evidence["primary_source_factor"] is not None
        assert evidence["recency_factor"] is not None
        assert {
            "relevance_score",
            "source_base_score",
            "primary_source_factor",
            "recency_factor",
            "final_score",
        }.issubset(evidence["score_breakdown"])


def test_trusted_search_returns_aggregated_claim_statuses() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    statuses = {claim["claim_id"]: claim["status"] for claim in body["claims"]}
    assert statuses["c1"] == "likely"
    assert statuses["c2"] == "likely"
    assert statuses["c3"] == "likely"
    assert statuses["c4"] == "false_likely"
    assert statuses["c6"] == "uncertain"
    assert all(claim["reason"] for claim in body["claims"])


def test_trusted_search_returns_real_answer_constraints() -> None:
    response = client.post(
        "/api/v1/trusted-search",
        json={"query": "MiroThinker 1.7 是不是开源模型？"},
    )

    body = response.json()
    constraints = body["answer_constraints"]
    assert constraints["can_answer_confidently"] is False
    assert constraints["must_disclose_uncertainty"] is True
    assert constraints["must_cite_sources"] is True
    assert constraints["allowed_tone"] == "cautious"
    required_text = " ".join(constraints["required_phrases"])
    assert "权重开放" in required_text
    assert "代码开放" in required_text
    assert "训练数据开放" in required_text
    assert "许可证" in required_text
    assert "严格开源定义" in required_text
    assert "真实搜索和证据验证尚未运行" not in constraints["required_phrases"]
    assert constraints["forbidden_phrases"]


def test_trusted_search_rejects_empty_query() -> None:
    response = client.post("/api/v1/trusted-search", json={"query": ""})

    assert response.status_code == 422
