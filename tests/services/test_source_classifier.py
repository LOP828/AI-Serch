from app.schemas.search import SearchResultSchema
from app.schemas.source import SourceType
from app.services.source_classifier import (
    base_reliability_for,
    classify_source,
    search_result_to_source,
)


def test_huggingface_classifies_as_official_model_card() -> None:
    result = classify_source("https://huggingface.co/example/model")

    assert result.source_type == SourceType.OFFICIAL_MODEL_CARD
    assert result.base_reliability == 0.88
    assert result.is_primary_source is True


def test_github_classifies_as_source_code_repo() -> None:
    result = classify_source("https://github.com/example/repo")

    assert result.source_type == SourceType.SOURCE_CODE_REPO
    assert result.base_reliability == 0.88
    assert result.is_primary_source is True


def test_arxiv_classifies_as_academic_paper() -> None:
    result = classify_source("https://arxiv.org/abs/2501.12345")

    assert result.source_type == SourceType.ACADEMIC_PAPER
    assert result.base_reliability == 0.90
    assert result.is_primary_source is True


def test_sec_classifies_as_financial_filing() -> None:
    result = classify_source("https://www.sec.gov/ixviewer/doc/action")

    assert result.source_type == SourceType.FINANCIAL_FILING
    assert result.base_reliability == 0.95
    assert result.is_primary_source is True


def test_gov_domain_classifies_as_government_docs() -> None:
    result = classify_source("https://data.example.gov/report")

    assert result.source_type == SourceType.GOVERNMENT_DOCS
    assert result.base_reliability == 0.95
    assert result.is_primary_source is True


def test_community_domains_classify_as_community_forum() -> None:
    urls = [
        "https://www.reddit.com/r/models/comments/abc",
        "https://www.zhihu.com/question/123",
        "https://x.com/example/status/123",
        "https://twitter.com/example/status/123",
    ]

    for url in urls:
        result = classify_source(url)
        assert result.source_type == SourceType.COMMUNITY_FORUM
        assert result.base_reliability == 0.40
        assert result.is_primary_source is False


def test_unknown_domain_classifies_as_unknown() -> None:
    result = classify_source("https://unknown-example-site.com/article")

    assert result.source_type == SourceType.UNKNOWN
    assert result.base_reliability == 0.30
    assert result.is_primary_source is False


def test_docs_rules_classify_as_official_docs() -> None:
    docs_subdomain = classify_source("https://docs.example.com/guide")
    docs_path = classify_source("https://example.com/product/docs/start")

    assert docs_subdomain.source_type == SourceType.OFFICIAL_DOCS
    assert docs_path.source_type == SourceType.OFFICIAL_DOCS
    assert docs_subdomain.base_reliability == 0.95
    assert docs_subdomain.is_primary_source is True


def test_base_reliability_reads_policy_values() -> None:
    assert base_reliability_for(SourceType.PRODUCT_PAGE) == 0.80
    assert base_reliability_for(SourceType.SEO_CONTENT) == 0.20


def test_search_result_converts_to_source_schema() -> None:
    result = SearchResultSchema(
        title="MiroThinker-1.7 - Hugging Face",
        url="https://huggingface.co/example/mirothinker-1.7",
        snippet="Mock model card result.",
        published_at="2026-05-01T00:00:00Z",
    )

    source = search_result_to_source(result=result, source_id="s1")

    assert source.source_id == "s1"
    assert source.title == result.title
    assert source.url == result.url
    assert source.domain == "huggingface.co"
    assert source.snippet == result.snippet
    assert source.published_at == result.published_at
    assert source.source_type == SourceType.OFFICIAL_MODEL_CARD
    assert source.base_reliability == 0.88
    assert source.is_primary_source is True
    assert source.fetch_status == "not_fetched"
