from app.mcp.server import handle_mcp_message
from app.mcp.tools import TRUSTED_SEARCH_TOOL_NAME, trusted_search_tool
from app.schemas.trusted_search import TrustedSearchRequest
from app.services.trusted_search_service import TrustedSearchService


def test_trusted_search_tool_accepts_minimal_query() -> None:
    result = trusted_search_tool({"query": "MiroThinker 1.7 是不是开源模型？"})

    assert result["query"] == "MiroThinker 1.7 是不是开源模型？"
    assert result["question_type"] == "ai_model_info"
    assert result["claims"]
    assert result["sources"]
    assert result["conflicts"] == []
    assert result["answer_constraints"]


def test_trusted_search_tool_returns_complete_evidence_package_fields() -> None:
    result = trusted_search_tool({"query": "MiroThinker 1.7 是不是开源模型？"})

    assert {
        "query",
        "question_type",
        "claims",
        "search_plan",
        "sources",
        "page_fetches",
        "conflicts",
        "answer_constraints",
    }.issubset(result)
    evidence_items = [evidence for claim in result["claims"] for evidence in claim["evidence"]]
    assert evidence_items
    assert evidence_items[0]["final_score"] is not None


def test_trusted_search_tool_reuses_injected_service() -> None:
    service = RecordingService()

    result = trusted_search_tool({"query": "这个东西到底怎么样？"}, service=service)

    assert service.called is True
    assert service.request.query == "这个东西到底怎么样？"
    assert result["query"] == "这个东西到底怎么样？"


def test_trusted_search_tool_empty_query_returns_controlled_error() -> None:
    result = trusted_search_tool({"query": ""})

    assert result["error"]["code"] == "invalid_request"
    assert result["error"]["message"] == "Invalid trusted_search arguments."


def test_trusted_search_tool_service_exception_returns_controlled_error() -> None:
    result = trusted_search_tool({"query": "test"}, service=FailingService())

    assert result["error"]["code"] == "internal_error"
    assert "failed" in result["error"]["message"]


def test_mcp_tools_list_message_returns_tool_definition() -> None:
    response = handle_mcp_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    tool = response["result"]["tools"][0]
    assert tool["name"] == TRUSTED_SEARCH_TOOL_NAME
    assert tool["inputSchema"]["required"] == ["query"]


def test_mcp_tools_call_message_invokes_trusted_search() -> None:
    response = handle_mcp_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": TRUSTED_SEARCH_TOOL_NAME,
                "arguments": {"query": "MiroThinker 1.7 是不是开源模型？"},
            },
        }
    )

    result = response["result"]
    assert result["query"] == "MiroThinker 1.7 是不是开源模型？"
    assert result["claims"]


class RecordingService:
    def __init__(self) -> None:
        self.called = False
        self.request: TrustedSearchRequest | None = None

    def search(self, request: TrustedSearchRequest):
        self.called = True
        self.request = request
        return TrustedSearchService().search(request)


class FailingService:
    def search(self, request: TrustedSearchRequest):
        del request
        raise RuntimeError("boom")
