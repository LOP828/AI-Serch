import json
import sys
from typing import Any, TextIO

from app.mcp.tools import (
    TRUSTED_SEARCH_TOOL_DEFINITION,
    TRUSTED_SEARCH_TOOL_NAME,
    TrustedSearchServiceProtocol,
    trusted_search_tool,
)


def handle_mcp_message(
    message: dict[str, Any],
    service: TrustedSearchServiceProtocol | None = None,
) -> dict[str, Any]:
    request_id = message.get("id")
    method = message.get("method")

    if method == "tools/list":
        return _jsonrpc_response(request_id, {"tools": [TRUSTED_SEARCH_TOOL_DEFINITION]})

    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != TRUSTED_SEARCH_TOOL_NAME:
            return _jsonrpc_error(request_id, "unknown_tool", "Unknown MCP tool.")
        result = trusted_search_tool(params.get("arguments") or {}, service=service)
        return _jsonrpc_response(request_id, result)

    if message.get("tool") == TRUSTED_SEARCH_TOOL_NAME:
        return trusted_search_tool(message.get("arguments") or {}, service=service)

    return _jsonrpc_error(request_id, "unsupported_method", "Unsupported MCP message.")


def run_stdio_server(
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = handle_mcp_message(message)
        except json.JSONDecodeError as exc:
            response = _jsonrpc_error(None, "invalid_json", str(exc))
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
        output_stream.flush()


def _jsonrpc_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    if request_id is None:
        return result
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: str, message: str) -> dict[str, Any]:
    error = {"code": code, "message": message}
    if request_id is None:
        return {"error": error}
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


if __name__ == "__main__":
    run_stdio_server()
