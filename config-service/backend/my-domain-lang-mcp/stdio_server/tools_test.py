"""Tests for the knowledge-graph tools, exercised through an MCP client.

Fixtures build their graphs **in-process** with `Storage`, never by shelling out
to `manage.py knowledge import`: that would drag Django, PyYAML, and the backend
venv into this suite and destroy the standalone property. Nothing here touches
the real `knowledge.db`, which is generated and gitignored — so the suite passes
with Docker stopped and the graph never built.
"""

from __future__ import annotations

import json

import pytest
from knowledge_graph.storage import Edge, Node, Storage
from mcp import Client
from mcp.shared.exceptions import MCPError

from stdio_server import tools
from stdio_server.main import build_server

NODES = [
    Node(
        id="application",
        type="domain_term",
        area="config_storage",
        name="Application",
        definition="A registered application whose configuration this service stores.",
        aliases=["app"],
        warnings=["Not a Django app; unrelated to INSTALLED_APPS."],
        source_files=["backend/api/models.py"],
        documentation=["context/DOMAIN.md"],
    ),
    Node(
        id="configuration",
        type="domain_term",
        area="config_storage",
        name="Configuration",
        definition="A named set of environment settings belonging to one application.",
    ),
    Node(
        id="user",
        type="domain_term",
        area="user_directory",
        name="User",
        definition="A person in the directory.",
        aliases=["person"],
        warnings=["Not django.contrib.auth's User; this one cannot log in."],
    ),
]

EDGES = [
    Edge(from_node="application", to_node="configuration", relationship="owns"),
    Edge(from_node="application", to_node="user", relationship="associated_with"),
    # Incoming edge — must NOT appear in application's related terms.
    Edge(from_node="user", to_node="application", relationship="associated_with"),
]


def _build(db_path, nodes=NODES, edges=EDGES) -> None:
    store = Storage(db_path)
    store.initialize_schema()
    for node in nodes:
        store.insert_node(node)
    for edge in edges:
        store.insert_edge(edge)


@pytest.fixture
def graph(tmp_path, monkeypatch):
    """A temporary knowledge graph, wired in via the KNOWLEDGE_DB seam."""
    db = tmp_path / "knowledge.db"
    _build(db)
    monkeypatch.setenv("KNOWLEDGE_DB", str(db))
    return db


def _payload(result):
    return result.structured_content


async def test_tool_surface_is_the_four_knowledge_tools(graph):
    async with Client(build_server()) as client:
        listed = (await client.list_tools()).tools
        assert {t.name for t in listed} == {
            "lookup_term",
            "get_related_terms",
            "list_domain_areas",
            "validate_knowledge_graph",
        }
        for tool in listed:
            assert tool.description and len(tool.description) > 40
            assert tool.output_schema, f"{tool.name} has no output schema"
        # Phase 1's promise still holds for the other two surfaces.
        assert (await client.list_resources()).resources == []
        assert (await client.list_prompts()).prompts == []


async def test_lookup_term_resolves_id_name_and_alias_case_insensitively(graph):
    async with Client(build_server()) as client:
        for term in ("application", "Application", "APP", "app"):
            result = await client.call_tool("lookup_term", {"term": term})
            assert result.is_error is False, term
            payload = _payload(result)
            assert payload["id"] == "application", term
            assert payload["name"] == "Application"
            assert payload["area"] == "config_storage"
            assert "configuration this service stores" in payload["definition"]
            assert payload["aliases"] == ["app"]
            assert payload["warnings"] == ["Not a Django app; unrelated to INSTALLED_APPS."]
            assert payload["source_files"] == ["backend/api/models.py"]


async def test_unknown_term_is_an_actionable_tool_error(graph):
    async with Client(build_server()) as client:
        result = await client.call_tool("lookup_term", {"term": "nonsense_term"})
        assert result.is_error is True
        message = result.content[0].text
        assert "nonsense_term" in message
        assert "list_domain_areas" in message
        # The session survives a tool-execution error.
        assert (await client.call_tool("list_domain_areas", {})).is_error is False


async def test_get_related_returns_outgoing_edges_with_target_names(graph):
    async with Client(build_server()) as client:
        result = await client.call_tool("get_related_terms", {"term": "application"})
        edges = _payload(result)["result"]
        assert {(e["relationship"], e["to"], e["to_name"]) for e in edges} == {
            ("owns", "configuration", "Configuration"),
            ("associated_with", "user", "User"),
        }
        assert all(e["from"] == "application" for e in edges)
        # the user -> application edge is incoming, so it is excluded
        assert not any(e["to"] == "application" for e in edges)


async def test_list_domain_areas(graph):
    async with Client(build_server()) as client:
        result = await client.call_tool("list_domain_areas", {})
        assert _payload(result)["result"] == ["config_storage", "user_directory"]


async def test_validate_reports_clean_and_broken_graphs(tmp_path, monkeypatch):
    clean = tmp_path / "clean.db"
    _build(clean)
    monkeypatch.setenv("KNOWLEDGE_DB", str(clean))
    async with Client(build_server()) as client:
        payload = _payload(await client.call_tool("validate_knowledge_graph", {}))
        assert payload == {"valid": True, "issues": []}

    broken = tmp_path / "broken.db"
    _build(broken, edges=[*EDGES, Edge("application", "ghost_node", "owns")])
    monkeypatch.setenv("KNOWLEDGE_DB", str(broken))
    async with Client(build_server()) as client:
        payload = _payload(await client.call_tool("validate_knowledge_graph", {}))
        assert payload["valid"] is False
        assert any("ghost_node" in issue for issue in payload["issues"])


async def test_missing_database_is_reported_and_creates_no_file(tmp_path, monkeypatch):
    missing = tmp_path / "never_built.db"
    monkeypatch.setenv("KNOWLEDGE_DB", str(missing))
    async with Client(build_server()) as client:
        result = await client.call_tool("lookup_term", {"term": "application"})
        assert result.is_error is True
        message = result.content[0].text
        assert str(missing) in message
        assert "make knowledge-import" in message
    # sqlite3.connect() would have created an empty file; the guard must not.
    assert not missing.exists()


def test_default_db_path_resolves_to_config_service_knowledge_db(monkeypatch):
    monkeypatch.delenv("KNOWLEDGE_DB", raising=False)
    path = tools.db_path()
    assert path == tools.DEFAULT_DB
    assert path.name == "knowledge.db"
    assert path.parent.name == "config-service"
    # Deliberately no existence assertion: the real graph is generated and
    # gitignored, so requiring it would make this suite environment-dependent.


async def test_invalid_arguments_are_protocol_errors(graph):
    """Spec: invalid arguments are protocol errors (-32602), not isError results."""
    async with Client(build_server()) as client:
        for bad_args in ({}, {"term": 123}, {"term": None}):
            with pytest.raises(MCPError) as exc_info:
                await client.call_tool("lookup_term", bad_args)
            assert exc_info.value.error.code == -32602
            assert "lookup_term" in exc_info.value.error.message
        # ...and the session still works afterwards
        assert (await client.call_tool("list_domain_areas", {})).is_error is False


async def test_valid_arguments_still_pass_the_guard(graph):
    """The guard must not reject anything the SDK would have accepted."""
    async with Client(build_server()) as client:
        # extra properties are permitted by the schema, so they must still work
        result = await client.call_tool("lookup_term", {"term": "app", "unexpected": 1})
        assert result.is_error is False
        assert _payload(result)["id"] == "application"


async def test_tool_results_are_json_serialisable(graph):
    """Structured content must survive a JSON round-trip for any client."""
    async with Client(build_server()) as client:
        for name, args in (
            ("lookup_term", {"term": "user"}),
            ("get_related_terms", {"term": "application"}),
            ("list_domain_areas", {}),
            ("validate_knowledge_graph", {}),
        ):
            payload = _payload(await client.call_tool(name, args))
            assert json.loads(json.dumps(payload)) == payload
