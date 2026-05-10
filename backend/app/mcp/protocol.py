import json
from typing import Any

class MCPProtocol:
    def __init__(self, server_name: str, server_version: str):
        self.server_name = server_name
        self.server_version = server_version
        self._tools: dict[str, dict] = {}
        self._tool_handlers: dict[str, callable] = {}

    def register_tool(self, name: str, description: str, parameters: dict, handler: callable):
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": parameters,
                "required": [k for k, v in parameters.items() if v.get("required", True)],
            },
        }
        self._tool_handlers[name] = handler

    async def handle_message(self, message: str) -> str | None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return self._error(None, -32700, "Parse error")
        method = data.get("method", "")
        params = data.get("params", {})
        msg_id = data.get("id")
        if method == "initialize":
            return self._response(msg_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": self.server_name, "version": self.server_version}})
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._response(msg_id, {})
        if method == "tools/list":
            return self._response(msg_id, {"tools": list(self._tools.values())})
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            if tool_name not in self._tool_handlers:
                return self._error(msg_id, -32601, f"Tool not found: {tool_name}")
            try:
                result = await self._tool_handlers[tool_name](**arguments)
                return self._response(msg_id, {"content": [{"type": "text", "text": json.dumps(result, default=str) if isinstance(result, dict) else str(result)}]})
            except Exception as e:
                return self._error(msg_id, -32603, f"Tool execution error: {str(e)}")
        return self._error(msg_id, -32601, f"Method not found: {method}")

    def _response(self, msg_id: Any, result: Any) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result})

    def _error(self, msg_id: Any, code: int, message: str) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})

    def get_tool_manifest(self) -> dict:
        return {"server": {"name": self.server_name, "version": self.server_version}, "tools": list(self._tools.values()), "tool_count": len(self._tools)}
