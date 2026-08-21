"""Phase-1 stdio MCP server: completes the MCP handshake, exposes nothing yet.

Protocol discipline for stdio transport: stdout belongs to JSON-RPC frames
alone — every diagnostic goes to stderr. Exit is clean (0) when the client
closes the stream; anything unexpected is logged to stderr and exits nonzero.
Phase 2 will register tools backed by the sibling `knowledge_graph` package.
"""

from __future__ import annotations

import logging
import sys

import mcp.types as types
from mcp.server.mcpserver import MCPServer
from mcp.shared.exceptions import MCPError

SERVER_NAME = "my-domain-lang-mcp"
SERVER_VERSION = "0.1.0"

logger = logging.getLogger(SERVER_NAME)


def build_server() -> MCPServer:
    """Return the bare Phase-1 server: handshake only, zero tools/resources/prompts."""
    server = MCPServer(
        SERVER_NAME,
        version=SERVER_VERSION,
        instructions=(
            "Phase 1 skeleton: no tools, resources, or prompts are exposed yet. "
            "Phase 2 will surface the config-service domain knowledge graph."
        ),
    )

    async def unknown_tool_guard(ctx, call_next):
        # Spec alignment (Tools § Error Handling): a tools/call naming an
        # unregistered tool is a *protocol* error (-32602), not a tool-execution
        # error — mcp 2.0.0 would otherwise answer CallToolResult(is_error=True).
        if ctx.method == "tools/call":
            name = (ctx.params or {}).get("name")
            if name not in {tool.name for tool in await server.list_tools()}:
                raise MCPError(types.INVALID_PARAMS, f"Unknown tool: {name}")
        return await call_next(ctx)

    server.middleware.append(unknown_tool_guard)
    return server


def main() -> int:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger.info("starting %s %s (stdio)", SERVER_NAME, SERVER_VERSION)
    try:
        build_server().run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("interrupted; shutting down")
        return 0
    except Exception:
        logger.exception("fatal protocol-layer error")
        return 1
    logger.info("client disconnected; shutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
