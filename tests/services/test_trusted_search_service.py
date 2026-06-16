from app.schemas.claim import ClaimSchema
from app.schemas.search import SearchPlanItemSchema, SearchResultSchema
from app.schemas.trusted_search import (
    OverallStatus,
    QuestionType,
    Strictness,
    TrustedSearchRequest,
)
from app.services.search_adapter import SearchAdapterResponse
from app.services.trusted_search_service import (
    TrustedSearchService,
    derive_overall_confidence,
    derive_overall_status,
    provider_candidate_limit,
    rank_search_results,
    select_candidate_queries,
)


def test_overall_status_confirmed_when_all_confirmed() -> None:
    assert derive_overall_status([_claim("confirmed", 0.9)]) == OverallStatus.CONFIRMED


def test_overall_status_mostly_confirmed_for_confirmed_and_likely() -> None:
    claims = [_claim("confirmed", 0.85), _claim("likely", 0.70)]

    assert derive_overall_status(claims) == OverallStatus.MOSTLY_CONFIRMED


def test_overall_status_partially_confirmed_for_mixed_evidence() -> None:
    claims = [_claim("likely", 0.70), _claim("uncertain", 0.40)]

    assert derive_overall_status(claims) == OverallStatus.PARTIALLY_CONFIRMED


def test_overall_status_prioritizes_conflicting_and_false_likely() -> None:
    assert derive_overall_status([_claim("conflicting", 0.8)]) == OverallStatus.CONFLICTING
    assert derive_overall_status([_claim("false_likely", 0.8)]) == OverallStatus.LIKELY_FALSE


def test_overall_status_unsupported_when_no_supporting_claims() -> None:
    assert derive_overall_status([_claim("unsupported", 0.0)]) == OverallStatus.UNSUPPORTED
    assert derive_overall_status([]) == OverallStatus.UNSUPPORTED


def test_overall_confidence_averages_claim_confidence_and_clamps_conflicts() -> None:
    claims = [_claim("likely", 0.7), _claim("uncertain", 0.3)]
    conflicting = [_claim("conflicting", 0.9), _claim("likely", 0.8)]

    assert derive_overall_confidence(claims) == 0.5
    assert derive_overall_confidence(conflicting) == 0.60
    assert derive_overall_confidence([]) == 0.0


def test_ai_model_open_source_mixed_subclaims_are_partially_confirmed() -> None:
    claims = [
        _claim("likely", 0.70, claim_type="existence"),
        _claim("likely", 0.70, claim_type="model_weights"),
        _claim("likely", 0.70, claim_type="source_code"),
        _claim("likely", 0.70, claim_type="license"),
        _claim("false_likely", 0.78, claim_type="training_data"),
        _claim("uncertain", 0.60, claim_type="interpretation"),
    ]

    assert (
        derive_overall_status(claims, QuestionType.AI_MODEL_INFO)
        == OverallStatus.PARTIALLY_CONFIRMED
    )


def test_core_false_likely_interpretation_remains_likely_false() -> None:
    claims = [
        _claim("likely", 0.70, claim_type="model_weights"),
        _claim("false_likely", 0.78, claim_type="interpretation"),
    ]

    assert (
        derive_overall_status(claims, QuestionType.AI_MODEL_INFO)
        == OverallStatus.LIKELY_FALSE
    )


def test_candidate_query_budget_varies_by_strictness() -> None:
    search_plan = [
        SearchPlanItemSchema(
            claim_id="c1",
            queries=[f"query {index}" for index in range(1, 10)],
        )
    ]

    assert (
        len(select_candidate_queries(search_plan, Strictness.STRICT, "fallback query"))
        == 3
    )
    assert (
        len(select_candidate_queries(search_plan, Strictness.BALANCED, "fallback query"))
        == 5
    )
    assert (
        len(select_candidate_queries(search_plan, Strictness.LOOSE, "fallback query"))
        == 7
    )


def test_candidate_query_selection_deduplicates_with_stable_order() -> None:
    search_plan = [
        SearchPlanItemSchema(claim_id="c1", queries=["official", "github", "official"]),
        SearchPlanItemSchema(claim_id="c2", queries=["github", "paper", "license"]),
    ]

    selected = select_candidate_queries(
        search_plan,
        Strictness.BALANCED,
        "fallback query",
    )

    assert selected == ["official", "github", "paper", "license"]


def test_candidate_query_selection_falls_back_to_original_query_when_plan_empty() -> None:
    selected = select_candidate_queries([], Strictness.BALANCED, "original query")

    assert selected == ["original query"]


def test_provider_candidate_limit_expands_beyond_response_max_sources() -> None:
    assert provider_candidate_limit(2) == 6
    assert provider_candidate_limit(8) == 10


def test_trusted_search_uses_expanded_candidate_pool_but_truncates_response_sources() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title=f"Candidate {index}",
                url=f"https://example.com/candidate-{index}",
                snippet="candidate snippet",
            )
            for index in range(1, 5)
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="MiroThinker 1.7 是不是开源模型？",
            max_sources=2,
        )
    )

    assert adapter.max_total_results_values == [6]
    assert adapter.max_results_per_query_values == [2]
    assert len(adapter.queries_values[0]) == 5
    assert len(response.sources) == 2
    assert [source.title for source in response.sources] == ["Candidate 1", "Candidate 2"]


def test_source_ranking_keeps_official_source_when_provider_returns_it_late() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Community first",
                url="https://www.zhihu.com/question/123",
                snippet="community discussion",
            ),
            SearchResultSchema(
                title="Unknown second",
                url="https://example.com/model-writeup",
                snippet="unknown source",
            ),
            SearchResultSchema(
                title="Official model card late",
                url="https://huggingface.co/example/model",
                snippet="official model card",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="MiroThinker 1.7 是不是开源模型？",
            question_type=QuestionType.AI_MODEL_INFO,
            max_sources=2,
        )
    )

    assert adapter.max_total_results_values == [6]
    assert len(response.sources) == 2
    assert [source.title for source in response.sources] == [
        "Official model card late",
        "Community first",
    ]


def test_source_ranking_keeps_final_sources_capped_after_candidate_expansion() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Community first",
                url="https://www.reddit.com/r/models/comments/1",
                snippet="community discussion",
            ),
            SearchResultSchema(
                title="Unknown second",
                url="https://example.com/model",
                snippet="unknown source",
            ),
            SearchResultSchema(
                title="Official model card third",
                url="https://huggingface.co/example/model",
                snippet="official model card",
            ),
            SearchResultSchema(
                title="Source repo fourth",
                url="https://github.com/example/model",
                snippet="source repository",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="MiroThinker 1.7 是不是开源模型？",
            question_type=QuestionType.AI_MODEL_INFO,
            max_sources=2,
        )
    )

    assert adapter.max_total_results_values == [6]
    assert len(response.sources) == 2
    assert [source.title for source in response.sources] == [
        "Official model card third",
        "Source repo fourth",
    ]


def test_openai_scope_prefers_openai_domain_over_non_openai_huggingface() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Third-party GPT-4.1 Hugging Face page",
                url="https://huggingface.co/some-user/gpt-4.1",
                snippet="third-party model card",
            ),
            SearchResultSchema(
                title="OpenAI GPT-4.1 release notes",
                url="https://openai.com/index/gpt-4-1/",
                snippet="OpenAI release notes",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="GPT-4.1 是否是 OpenAI 发布的模型？",
            question_type=QuestionType.AI_MODEL_INFO,
            max_sources=2,
        )
    )

    assert [source.title for source in response.sources] == [
        "OpenAI GPT-4.1 release notes",
        "Third-party GPT-4.1 Hugging Face page",
    ]


def test_openai_scope_prefers_openai_domain_over_non_openai_github_repo() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Third-party GPT-4.1 GitHub repo",
                url="https://github.com/some-user/gpt-4.1-notes",
                snippet="third-party source repo",
            ),
            SearchResultSchema(
                title="OpenAI API docs",
                url="https://platform.openai.com/docs/models/gpt-4.1",
                snippet="OpenAI API documentation",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="GPT-4.1 是否是 OpenAI 发布的模型？",
            question_type=QuestionType.AI_MODEL_INFO,
            max_sources=2,
        )
    )

    assert [source.title for source in response.sources] == [
        "OpenAI API docs",
        "Third-party GPT-4.1 GitHub repo",
    ]


def test_openai_scope_entity_alignment_runs_before_max_sources_truncation() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Third-party Hugging Face page",
                url="https://huggingface.co/some-user/gpt-4.1",
                snippet="third-party model card",
            ),
            SearchResultSchema(
                title="Third-party GitHub repo",
                url="https://github.com/some-user/gpt-4.1-notes",
                snippet="third-party repo",
            ),
            SearchResultSchema(
                title="Unknown article",
                url="https://example.com/gpt-4.1",
                snippet="unknown article",
            ),
            SearchResultSchema(
                title="OpenAI official help article",
                url="https://help.openai.com/en/articles/gpt-4-1",
                snippet="OpenAI help article",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="GPT-4.1 是否是 OpenAI 发布的模型？",
            question_type=QuestionType.AI_MODEL_INFO,
            max_sources=2,
        )
    )

    assert adapter.max_total_results_values == [6]
    assert len(response.sources) == 2
    assert [source.title for source in response.sources] == [
        "OpenAI official help article",
        "Third-party Hugging Face page",
    ]


def test_source_ranking_preserves_provider_order_for_equal_scores() -> None:
    results = [
        SearchResultSchema(
            title="First unknown",
            url="https://example.com/first",
            snippet="first",
        ),
        SearchResultSchema(
            title="Second unknown",
            url="https://example.net/second",
            snippet="second",
        ),
    ]

    ranked = rank_search_results(results, question_type=QuestionType.GENERAL_FACT)

    assert [result.title for result in ranked] == ["First unknown", "Second unknown"]


def test_non_openai_general_fact_query_preserves_equal_score_order() -> None:
    results = [
        SearchResultSchema(
            title="First same-score result",
            url="https://example.com/first",
            snippet="first",
        ),
        SearchResultSchema(
            title="Second same-score result",
            url="https://example.net/second",
            snippet="second",
        ),
    ]

    ranked = rank_search_results(
        results,
        question_type=QuestionType.GENERAL_FACT,
        query="普通事实问题",
    )

    assert [result.title for result in ranked] == [
        "First same-score result",
        "Second same-score result",
    ]


def test_policy_legal_ranking_prioritizes_sec_source_over_media() -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Media report first",
                url="https://finance.example.com/sec-bitcoin-etf",
                snippet="media report",
            ),
            SearchResultSchema(
                title="SEC approval order second",
                url="https://www.sec.gov/rules/sro/nysearca/2024/34-99306.pdf",
                snippet="SEC approval order",
            ),
            SearchResultSchema(
                title="Another media report third",
                url="https://news.example.com/bitcoin-etf",
                snippet="another media report",
            ),
        ]
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(
            query="美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？",
            question_type=QuestionType.POLICY_LEGAL,
            max_sources=2,
        )
    )

    assert [source.title for source in response.sources] == [
        "SEC approval order second",
        "Media report first",
    ]
    assert response.sources[0].domain == "sec.gov"


def test_default_static_trusted_search_sources_remain_stable() -> None:
    response = TrustedSearchService().search(
        TrustedSearchRequest(
            query="MiroThinker 1.7 是不是开源模型？",
            max_sources=2,
        )
    )

    assert [source.title for source in response.sources] == [
        "MiroThinker-1.7 - Hugging Face",
        "MiroThinker GitHub repository",
    ]


def test_trusted_search_falls_back_to_original_query_when_search_plan_empty(monkeypatch) -> None:
    adapter = RecordingCandidateAdapter(
        [
            SearchResultSchema(
                title="Fallback query result",
                url="https://example.com/fallback-query-result",
                snippet="fallback snippet",
            )
        ]
    )
    monkeypatch.setattr(
        "app.services.trusted_search_service.build_search_plan",
        lambda **kwargs: [],
    )

    response = TrustedSearchService(search_adapter=adapter).search(
        TrustedSearchRequest(query="MiroThinker 1.7 是不是开源模型？")
    )

    assert adapter.queries_values == [["MiroThinker 1.7 是不是开源模型？"]]
    assert response.search_plan == []
    assert [source.title for source in response.sources] == ["Fallback query result"]


def _claim(status: str, confidence: float, claim_type: str = "general_fact") -> ClaimSchema:
    return ClaimSchema(
        claim_id=f"c-{status}",
        claim_text="Claim text",
        claim_type=claim_type,
        status=status,
        confidence=confidence,
        reason="Reason.",
        evidence=[],
    )


class RecordingCandidateAdapter:
    def __init__(self, results: list[SearchResultSchema]) -> None:
        self._results = results
        self.queries_values: list[list[str]] = []
        self.max_results_per_query_values: list[int] = []
        self.max_total_results_values: list[int] = []

    def search_many(
        self,
        queries: list[str],
        max_results_per_query: int = 8,
        max_total_results: int = 8,
    ) -> SearchAdapterResponse:
        self.queries_values.append(queries)
        self.max_results_per_query_values.append(max_results_per_query)
        self.max_total_results_values.append(max_total_results)
        return SearchAdapterResponse(results=self._results[:max_total_results])
