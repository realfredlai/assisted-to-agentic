"""Stdio MCP server exposing the config-service domain knowledge graph.

Protocol discipline for stdio transport: stdout belongs to JSON-RPC frames
alone — every diagnostic goes to stderr. Exit is clean (0) when the client
closes the stream; anything unexpected is logged to stderr and exits nonzero.

Error channels follow the MCP spec's split (Tools § Error Handling), which
mcp 2.0.0 does not implement in full:

  * **Protocol errors** — unknown tool, invalid arguments — are JSON-RPC
    errors (`-32602`). The SDK answers both with `isError` results instead,
    so `spec_conformance_guard` below restores the spec behaviour.
  * **Tool execution errors** — an unknown domain term, a graph that has not
    been built — stay `isError` results carrying text the model can act on.
"""

from __future__ import annotations

import logging
import sys

import jsonschema
import mcp.types as types
from mcp.server.mcpserver import MCPServer
from mcp.shared.exceptions import MCPError

from stdio_server import tools

SERVER_NAME = "my-domain-lang-mcp"
SERVER_VERSION = "0.2.0"

logger = logging.getLogger(SERVER_NAME)


def build_server() -> MCPServer:
    """Return the server with the four knowledge-graph tools registered."""
    server = MCPServer(
        SERVER_NAME,
        version=SERVER_VERSION,
        instructions=(
            "Authoritative domain language for the config-service codebase — what "
            "User, Application, Configuration and friends actually mean here. "
            "Look a term up before assuming its ordinary meaning: several carry "
            "warnings about exactly that (this User is not Django's auth user). "
            "The graph is read-only; it is rebuilt from YAML by `make knowledge-import`."
        ),
    )

    @server.tool(
        name="lookup_term",
        description=(
            "Look up one domain term of the config-service codebase and get its "
            "definition, aliases, warnings, source files, and documentation links. "
            "Accepts the term's id, its display name, or any alias, case-insensitively "
            "('application', 'Application', and 'app' all work). Use this whenever a "
            "domain word appears and you need its meaning *in this codebase* rather "
            "than its general one — the 'warnings' field records the traps."
        ),
    )
    def lookup_term(term: str) -> tools.TermRecord:
        return tools.lookup_term(term)

    @server.tool(
        name="get_related_terms",
        description=(
            "List the relationships pointing *out* of a domain term — what it owns, "
            "contains, is classified by, or is associated with. Each record carries "
            "the relationship, the target's id, and the target's display name. Use it "
            "after lookup_term to see how a concept connects to the rest of the domain. "
            "Edges are directed: this returns only the ones originating at the term."
        ),
    )
    def get_related_terms(term: str) -> list[tools.RelatedEdge]:
        return tools.get_related_terms(term)

    @server.tool(
        name="list_domain_areas",
        description=(
            "List the distinct areas the domain is partitioned into. Cheap orientation "
            "when you do not yet know what the knowledge graph covers, and the natural "
            "first call before guessing at term names."
        ),
    )
    def list_domain_areas() -> list[str]:
        return tools.list_domain_areas()

    @server.tool(
        name="validate_knowledge_graph",
        description=(
            "Check the knowledge graph for internal inconsistencies — edges pointing at "
            "nodes that do not exist. Returns {valid, issues}. Useful after the YAML in "
            "knowledge/ has been edited and re-imported."
        ),
    )
    def validate_knowledge_graph() -> tools.ValidationReport:
        return tools.validate_knowledge_graph()

    async def spec_conformance_guard(ctx, call_next):
        """Answer unknown tools and invalid arguments as JSON-RPC protocol errors.

        The MCP spec puts both in the protocol-error category (`-32602`), distinct
        from tool-execution errors. mcp 2.0.0 returns `isError` results for them
        instead, which blurs 'you called this wrong' into 'the tool ran and
        failed'. Validating here — before the SDK's own argument parsing — keeps
        the two channels apart. The SDK does not coerce arguments, so this
        rejects exactly what it would have rejected anyway; only the channel
        changes.
        """
        if ctx.method == "tools/call":
            params = ctx.params or {}
            name = params.get("name")
            registered = {tool.name: tool for tool in await server.list_tools()}
            tool = registered.get(name)
            if tool is None:
                raise MCPError(types.INVALID_PARAMS, f"Unknown tool: {name}")
            try:
                jsonschema.validate(params.get("arguments") or {}, tool.input_schema)
            except jsonschema.ValidationError as exc:
                raise MCPError(
                    types.INVALID_PARAMS,
                    f"Invalid arguments for tool {name}: {exc.message}",
                ) from exc
        return await call_next(ctx)

    server.middleware.append(spec_conformance_guard)
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
