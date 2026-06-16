from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ENDPOINT = "/api/v1/trusted-search"
MAX_EXCERPT_CHARS = 180

EVAL_CASES = [
    {
        "eval_id": "eval_001",
        "query": "GPT-4.1 是否是 OpenAI 发布的模型？",
        "question_type": "ai_model_info",
        "strictness": "balanced",
        "max_sources": 2,
    },
    {
        "eval_id": "eval_002",
        "query": "Llama 3.1 是否公开模型权重并允许商用？",
        "question_type": "ai_model_info",
        "strictness": "balanced",
        "max_sources": 2,
    },
    {
        "eval_id": "eval_003",
        "query": "OpenAI 最近是否发布了新的语音模型？",
        "question_type": "tech_news",
        "strictness": "balanced",
        "max_sources": 2,
    },
    {
        "eval_id": "eval_004",
        "query": "RTX 5070 Ti 是否是 16GB 显存？",
        "question_type": "product_info",
        "strictness": "balanced",
        "max_sources": 2,
    },
    {
        "eval_id": "eval_005",
        "query": "美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？",
        "question_type": "policy_legal",
        "strictness": "balanced",
        "max_sources": 2,
    },
]


def main() -> int:
    _configure_utf8_stdio()
    run_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    preflight_error = _preflight_error()
    if preflight_error is not None:
        print(json.dumps(_blocked_payload(run_time, preflight_error), ensure_ascii=False, indent=2))
        return 2

    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    client = TestClient(app)
    results = [_run_case(client, eval_case, run_time) for eval_case in EVAL_CASES]
    get_settings.cache_clear()

    print(
        json.dumps(
            {
                "run_time": run_time,
                "provider": "tavily",
                "endpoint_or_entrypoint": ENDPOINT,
                "opt_in_env_used": "yes",
                "tavily_network_enabled": "yes",
                "api_key_present": "yes",
                "evals": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _preflight_error() -> str | None:
    if os.environ.get("CSL_SEARCH_PROVIDER", "").strip().lower() != "tavily":
        return "CSL_SEARCH_PROVIDER=tavily is required."
    if os.environ.get("CSL_SEARCH_ALLOW_NETWORK", "").strip().lower() != "true":
        return "CSL_SEARCH_ALLOW_NETWORK=true is required."
    if "CSL_SEARCH_API_KEY" not in os.environ:
        return "CSL_SEARCH_API_KEY must be present in the environment."
    return None


def _blocked_payload(run_time: str, reason: str) -> dict[str, Any]:
    return {
        "run_time": run_time,
        "provider": "tavily",
        "endpoint_or_entrypoint": ENDPOINT,
        "opt_in_env_used": "no",
        "tavily_network_enabled": "no",
        "api_key_present": "yes" if "CSL_SEARCH_API_KEY" in os.environ else "no",
        "status": "blocked",
        "blocked_reason": reason,
    }


def _run_case(client: Any, eval_case: dict[str, Any], run_time: str) -> dict[str, Any]:
    response = client.post(
        ENDPOINT,
        json={
            "query": eval_case["query"],
            "question_type": eval_case["question_type"],
            "strictness": eval_case["strictness"],
            "max_sources": eval_case["max_sources"],
            "return_raw_evidence": True,
        },
    )
    if response.status_code != 200:
        return {
            **_case_header(eval_case, run_time),
            "status": "failed",
            "http_status_code": response.status_code,
            "error": _short_text(response.text),
        }

    body = response.json()
    claims = body.get("claims", [])
    sources = body.get("sources", [])
    conflicts = body.get("conflicts", [])
    page_fetches = body.get("page_fetches", [])
    evidence_items = [evidence for claim in claims for evidence in claim.get("evidence", [])]
    answer_constraints = body.get("answer_constraints", {})

    return {
        **_case_header(eval_case, run_time),
        "status": "completed",
        "overall_status": body.get("overall_status"),
        "overall_confidence": body.get("overall_confidence"),
        "claims_count": len(claims),
        "sources_count": len(sources),
        "evidence_count": len(evidence_items),
        "conflicts_count": len(conflicts),
        "answer_allowed_tone": answer_constraints.get("allowed_tone"),
        "must_disclose_uncertainty": answer_constraints.get("must_disclose_uncertainty"),
        "can_answer_confidently": answer_constraints.get("can_answer_confidently"),
        "page_fetch_status_counts": _page_fetch_status_counts(page_fetches),
        "sources": [_summarize_source(source) for source in sources],
        "claims": [_summarize_claim(claim) for claim in claims],
        "evidence": [_summarize_evidence(evidence) for evidence in evidence_items],
        "conflicts": [_summarize_conflict(conflict) for conflict in conflicts],
    }


def _case_header(eval_case: dict[str, Any], run_time: str) -> dict[str, Any]:
    return {
        "eval_id": eval_case["eval_id"],
        "run_time": run_time,
        "query": eval_case["query"],
        "question_type": eval_case["question_type"],
        "strictness": eval_case["strictness"],
        "max_sources": eval_case["max_sources"],
        "provider": "tavily",
        "endpoint_or_entrypoint": ENDPOINT,
        "opt_in_env_used": "yes",
        "tavily_network_enabled": "yes",
    }


def _summarize_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "title": _short_text(source.get("title")),
        "domain": source.get("domain"),
        "source_type": source.get("source_type"),
        "base_reliability": source.get("base_reliability"),
        "is_primary_source": source.get("is_primary_source"),
        "published_at": source.get("published_at"),
        "human_source_type_judgment": "not_reviewed",
        "suspected_issue": None,
    }


def _summarize_claim(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": claim.get("claim_id"),
        "claim_text": claim.get("claim_text"),
        "claim_type": claim.get("claim_type"),
        "status": claim.get("status"),
        "confidence": claim.get("confidence"),
        "evidence_count": len(claim.get("evidence", [])),
        "reason": _short_text(claim.get("reason")),
        "human_judgment": "not_reviewed",
        "suspected_issue": None,
    }


def _summarize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": evidence.get("evidence_id"),
        "claim_id": evidence.get("claim_id"),
        "source_id": evidence.get("source_id"),
        "support_type": evidence.get("support_type"),
        "relevance_score": evidence.get("relevance_score"),
        "final_score": evidence.get("final_score"),
        "short_excerpt": _short_text(evidence.get("evidence_text")),
        "human_support_judgment": "not_reviewed",
        "suspected_issue": None,
    }


def _summarize_conflict(conflict: dict[str, Any]) -> dict[str, Any]:
    return {
        "conflict_id": conflict.get("conflict_id"),
        "claim_id": conflict.get("claim_id"),
        "severity": conflict.get("severity"),
        "summary": _short_text(conflict.get("summary")),
    }


def _page_fetch_status_counts(page_fetches: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(fetch.get("fetch_status", "unknown") for fetch in page_fetches))


def _short_text(value: object, max_chars: int = MAX_EXCERPT_CHARS) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


if __name__ == "__main__":
    raise SystemExit(main())
