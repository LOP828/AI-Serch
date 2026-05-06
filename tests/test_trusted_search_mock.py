from fastapi.testclient import TestClient

from app.main import app
from app.schemas.trusted_search import TrustedSearchResponse

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
        "sources",
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
        "evidence_text",
        "support_type",
        "relevance_score",
        "final_score",
        "score_breakdown",
    }.issubset(evidence)
    assert 0.0 <= evidence["final_score"] <= 1.0


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


def test_trusted_search_rejects_empty_query() -> None:
    response = client.post("/api/v1/trusted-search", json={"query": ""})

    assert response.status_code == 422
