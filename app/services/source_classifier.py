from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from app.schemas.search import SearchResultSchema
from app.schemas.source import FetchStatus, SourceSchema, SourceType

POLICY_PATH = Path(__file__).resolve().parents[1] / "policies" / "source_policy.yml"

_PRIMARY_SOURCE_TYPES = {
    SourceType.OFFICIAL_DOCS,
    SourceType.OFFICIAL_BLOG,
    SourceType.OFFICIAL_MODEL_CARD,
    SourceType.SOURCE_CODE_REPO,
    SourceType.ACADEMIC_PAPER,
    SourceType.GOVERNMENT_DOCS,
    SourceType.FINANCIAL_FILING,
}


@dataclass(frozen=True)
class SourceClassification:
    source_type: SourceType
    base_reliability: float
    is_primary_source: bool
    domain: str


def classify_source(url: str) -> SourceClassification:
    domain = extract_domain(url)
    source_type = classify_source_type(url, domain)
    return SourceClassification(
        source_type=source_type,
        base_reliability=base_reliability_for(source_type),
        is_primary_source=source_type in _PRIMARY_SOURCE_TYPES,
        domain=domain,
    )


def classify_source_type(url: str, domain: str | None = None) -> SourceType:
    normalized_url = url.lower()
    normalized_domain = domain or extract_domain(url)

    if _domain_matches(normalized_domain, "huggingface.co"):
        return SourceType.OFFICIAL_MODEL_CARD
    if _domain_matches(normalized_domain, "modelscope.cn"):
        return SourceType.OFFICIAL_MODEL_CARD
    if _domain_matches(normalized_domain, "github.com"):
        return SourceType.SOURCE_CODE_REPO
    if _domain_matches(normalized_domain, "gitlab.com"):
        return SourceType.SOURCE_CODE_REPO
    if _domain_matches(normalized_domain, "arxiv.org"):
        return SourceType.ACADEMIC_PAPER
    if _domain_matches(normalized_domain, "openreview.net"):
        return SourceType.ACADEMIC_PAPER
    if _domain_matches(normalized_domain, "sec.gov"):
        return SourceType.FINANCIAL_FILING
    if normalized_domain.endswith(".gov") or normalized_domain == "gov":
        return SourceType.GOVERNMENT_DOCS
    if normalized_domain.startswith("docs.") or "/docs/" in normalized_url:
        return SourceType.OFFICIAL_DOCS
    if any(
        _domain_matches(normalized_domain, community_domain)
        for community_domain in ("reddit.com", "zhihu.com", "x.com", "twitter.com")
    ):
        return SourceType.COMMUNITY_FORUM

    return SourceType.UNKNOWN


def search_result_to_source(result: SearchResultSchema, source_id: str) -> SourceSchema:
    classification = classify_source(str(result.url))
    return SourceSchema(
        source_id=source_id,
        title=result.title,
        url=result.url,
        domain=classification.domain,
        snippet=result.snippet,
        source_type=classification.source_type,
        base_reliability=classification.base_reliability,
        is_primary_source=classification.is_primary_source,
        published_at=result.published_at,
        author=None,
        fetched_at=None,
        fetch_status=FetchStatus.NOT_FETCHED,
    )


def search_results_to_sources(results: list[SearchResultSchema]) -> list[SourceSchema]:
    return [
        search_result_to_source(result=result, source_id=f"s{index}")
        for index, result in enumerate(results, start=1)
    ]


def extract_domain(url: str) -> str:
    netloc = urlsplit(url).netloc.lower()
    if "@" in netloc:
        netloc = netloc.rsplit("@", maxsplit=1)[1]
    domain = netloc.split(":", maxsplit=1)[0]
    if domain.startswith("www."):
        return domain[4:]
    return domain


def base_reliability_for(source_type: SourceType) -> float:
    policy = load_source_policy()
    return policy.get(source_type, policy[SourceType.UNKNOWN])


@lru_cache
def load_source_policy() -> dict[SourceType, float]:
    return _parse_source_policy(POLICY_PATH.read_text(encoding="utf-8"))


def _parse_source_policy(text: str) -> dict[SourceType, float]:
    policy: dict[SourceType, float] = {}
    current_source_type: SourceType | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "source_types:":
            continue

        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            key = stripped[:-1]
            current_source_type = SourceType(key)
            continue

        if current_source_type and stripped.startswith("base_score:"):
            _, raw_value = stripped.split(":", maxsplit=1)
            policy[current_source_type] = float(raw_value.strip())

    missing = set(SourceType) - set(policy)
    if missing:
        missing_values = ", ".join(sorted(source_type.value for source_type in missing))
        raise ValueError(f"source_policy.yml missing base_score for: {missing_values}")

    return policy


def _domain_matches(domain: str, expected_domain: str) -> bool:
    return domain == expected_domain or domain.endswith(f".{expected_domain}")
