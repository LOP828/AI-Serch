from app.schemas.search import SearchResultSchema
from app.schemas.trusted_search import OverallStatus, TrustedSearchRequest
from app.services.search_adapter import StaticSearchAdapter
from app.services.trusted_search_service import TrustedSearchService


def test_e2e_ai_model_open_source_question() -> None:
    response = TrustedSearchService().search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    _assert_complete_response(response)
    assert response.question_type == "ai_model_info"
    assert response.overall_status == OverallStatus.PARTIALLY_CONFIRMED
    assert response.answer_constraints.allowed_tone == "cautious"
    assert response.answer_constraints.must_disclose_uncertainty is True
    required_text = " ".join(response.answer_constraints.required_phrases)
    assert "权重开放" in required_text
    assert "代码开放" in required_text
    assert "训练数据开放" in required_text
    assert "许可证" in required_text
    assert "严格开源定义" in required_text
    assert response.overall_confidence > 0.0


def test_e2e_tech_news_question() -> None:
    response = _service_with_snippet(
        "OpenAI 下周会发布某个代号模型吗？ 有传言称发布消息，但没有官方确认。"
    ).search(TrustedSearchRequest(query="OpenAI 下周会发布某个代号模型吗？"))

    _assert_complete_response(response)
    assert response.question_type == "tech_news"
    assert response.risk_level == "medium"


def test_e2e_product_info_question() -> None:
    response = _service_with_snippet(
        "某款笔记本 RTX 5070 Ti 是不是 12GB 显存？ 商品参数页面显示显存为 12GB。"
    ).search(TrustedSearchRequest(query="某款笔记本 RTX 5070 Ti 是不是 12GB 显存？"))

    _assert_complete_response(response)
    assert response.question_type == "product_info"


def test_e2e_policy_legal_question() -> None:
    response = _service_with_snippet(
        "某项政策现在是否还有效？ 政府文件显示该政策仍然有效。"
    ).search(TrustedSearchRequest(query="某项政策现在是否还有效？"))

    _assert_complete_response(response)
    assert response.question_type == "policy_legal"
    assert response.risk_level == "high"


def test_e2e_empty_search_results_return_legal_response() -> None:
    response = TrustedSearchService(search_adapter=StaticSearchAdapter(results=[])).search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    assert response.sources == []
    assert response.page_fetches == []
    assert response.overall_status == OverallStatus.UNSUPPORTED
    assert response.overall_confidence == 0.0
    assert all(claim.status == "unsupported" for claim in response.claims)


def test_e2e_search_adapter_failure_return_legal_response() -> None:
    response = TrustedSearchService(search_adapter=StaticSearchAdapter(should_fail=True)).search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    assert response.sources == []
    assert response.overall_status == OverallStatus.UNSUPPORTED
    assert response.answer_constraints.must_disclose_uncertainty is True


def test_e2e_all_page_fetches_can_fallback() -> None:
    response = TrustedSearchService().search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    assert response.page_fetches
    assert {page.fetch_status for page in response.page_fetches} == {"fallback"}
    _assert_complete_response(response)


def test_e2e_empty_evidence_still_returns_legal_response() -> None:
    response = _service_with_snippet("This page only contains unrelated text.").search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    assert response.overall_status == OverallStatus.UNSUPPORTED
    assert all(claim.status == "unsupported" for claim in response.claims)
    assert response.answer_constraints.must_disclose_uncertainty is True


def test_e2e_conflict_is_exposed_in_response() -> None:
    response = _service_with_results(
        [
            SearchResultSchema(
                title="Supporting model card",
                url="https://huggingface.co/example/conflict-model",
                snippet="The model card says model files and weights are available.",
                published_at=None,
            ),
            SearchResultSchema(
                title="Opposing repository",
                url="https://github.com/example/conflict-model",
                snippet="The model weights are not publicly released.",
                published_at=None,
            ),
        ]
    ).search(TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？"))

    assert response.conflicts
    assert response.overall_status == OverallStatus.CONFLICTING
    assert response.answer_constraints.allowed_tone == "conflict_aware"
    conflict = response.conflicts[0]
    assert conflict.claim_id
    assert conflict.supporting_evidence_ids
    assert conflict.opposing_evidence_ids
    assert conflict.summary
    assert any(claim.status == "conflicting" for claim in response.claims)


def _service_with_snippet(snippet: str) -> TrustedSearchService:
    return _service_with_results(
        [
            SearchResultSchema(
                title="Mock source",
                url="https://example.com/mock-source",
                snippet=snippet,
                published_at=None,
            )
        ]
    )


def _service_with_results(results: list[SearchResultSchema]) -> TrustedSearchService:
    adapter = StaticSearchAdapter(results=results)
    return TrustedSearchService(search_adapter=adapter)


def _assert_complete_response(response) -> None:
    assert response.query
    assert response.question_type
    assert response.risk_level
    assert response.claims
    assert response.search_plan
    assert response.sources
    assert response.page_fetches
    assert response.overall_status
    assert 0.0 <= response.overall_confidence <= 1.0
    assert response.answer_constraints.forbidden_phrases
    assert "真实搜索和证据验证尚未运行" not in response.answer_constraints.required_phrases

    evidence_items = [evidence for claim in response.claims for evidence in claim.evidence]
    assert evidence_items
    for evidence in evidence_items:
        assert evidence.final_score is not None
        assert evidence.score_breakdown
    for claim in response.claims:
        assert claim.status
        assert 0.0 <= claim.confidence <= 1.0
        assert claim.reason
