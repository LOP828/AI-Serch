from typing import Protocol

from pydantic import ValidationError

from app.schemas.trusted_search import TrustedSearchRequest, TrustedSearchResponse
from app.services.trusted_search_service import TrustedSearchService

TRUSTED_SEARCH_TOOL_NAME = "trusted_search"
TRUSTED_SEARCH_TOOL_DESCRIPTION = (
    "对用户问题进行批判性搜索分析，返回结构化 evidence package，包括 "
    "question_type、claims、search_plan、sources、page_fetches、evidence、"
    "conflicts 和 answer_constraints。"
)

TRUSTED_SEARCH_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "question_type": {
            "type": "string",
            "default": "auto",
            "enum": [
                "auto",
                "ai_model_info",
                "tech_news",
                "product_info",
                "policy_legal",
                "technical_doc",
                "general_fact",
                "unknown",
            ],
        },
        "strictness": {
            "type": "string",
            "default": "balanced",
            "enum": ["loose", "balanced", "strict"],
        },
        "max_sources": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
        "require_primary_source": {"type": "boolean", "default": False},
        "return_raw_evidence": {"type": "boolean", "default": True},
    },
    "required": ["query"],
    "additionalProperties": False,
}

TRUSTED_SEARCH_TOOL_DEFINITION = {
    "name": TRUSTED_SEARCH_TOOL_NAME,
    "description": TRUSTED_SEARCH_TOOL_DESCRIPTION,
    "inputSchema": TRUSTED_SEARCH_INPUT_SCHEMA,
}


class TrustedSearchServiceProtocol(Protocol):
    def search(self, request: TrustedSearchRequest) -> TrustedSearchResponse:
        """Run trusted search and return a structured response."""


def trusted_search_tool(
    arguments: dict,
    service: TrustedSearchServiceProtocol | None = None,
) -> dict:
    try:
        request = TrustedSearchRequest.model_validate(arguments)
    except ValidationError as exc:
        return _error_response(
            code="invalid_request",
            message="Invalid trusted_search arguments.",
            details={"errors": exc.errors()},
        )

    active_service = service or TrustedSearchService()
    try:
        response = active_service.search(request)
    except Exception:
        return _error_response(
            code="internal_error",
            message="trusted_search failed unexpectedly.",
        )

    return response.model_dump(mode="json")


def _error_response(
    code: str,
    message: str,
    details: dict | None = None,
) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }
