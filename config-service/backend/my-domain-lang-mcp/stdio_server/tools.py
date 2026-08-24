"""Knowledge-graph tools for the MCP server.

The graph lives in `backend/knowledge_graph`, whose `storage` module is pure
stdlib (sqlite3 + json + pathlib) — no Django, no PyYAML. So this server reads
it by **importing it directly** rather than shelling out to `manage.py
knowledge` and parsing stdout: one failure mode instead of three, and typed
results instead of re-parsed JSON. That is why the MCP project lives inside
`backend/`.

Read-only by design. Rebuilding the graph stays a `make knowledge-import` job,
which needs PyYAML and Django; this venv has neither.

Two seams keep it testable and zero-config:
  * `sys.path` gains `backend/` so `knowledge_graph` is importable;
  * the database path defaults next to the shipped one, and `KNOWLEDGE_DB`
    overrides it — which is how the tests point at temporary graphs without
    touching the real file.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

from mcp.server.mcpserver.exceptions import ToolError

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Deliberately after the sys.path insert above: that ordering is the mechanism,
# not an oversight. `make typecheck` resolves this via MYPYPATH.
from knowledge_graph.storage import NodeNotFoundError, Storage  # noqa: E402

#: Where `make knowledge-import` writes the graph: config-service/knowledge.db.
DEFAULT_DB = _BACKEND.parent / "knowledge.db"

_REBUILD_HINT = "Build it from config-service/ with: make knowledge-import"


class TermRecord(TypedDict):
    """One domain term, as an agent sees it."""

    id: str
    name: str
    area: str
    type: str
    definition: str
    aliases: list[str]
    warnings: list[str]
    source_files: list[str]
    documentation: list[str]


#: Functional syntax because `from` is a Python keyword — the wire shape wins.
RelatedEdge = TypedDict(
    "RelatedEdge",
    {"from": str, "to": str, "to_name": str, "relationship": str},
)


class ValidationReport(TypedDict):
    valid: bool
    issues: list[str]


def db_path() -> Path:
    """The graph's location: `KNOWLEDGE_DB` if set, else the shipped default."""
    override = os.environ.get("KNOWLEDGE_DB")
    return Path(override) if override else DEFAULT_DB


@contextmanager
def _storage() -> Iterator[Storage]:
    """Open the graph, turning both 'not built yet' cases into actionable errors.

    Checking `exists()` first matters: `sqlite3.connect()` *creates* a file for a
    missing path, so going straight to a query would litter an empty database and
    then fail with a bare `no such table`.
    """
    path = db_path()
    if not path.exists():
        raise ToolError(
            f"The knowledge graph has not been built: no database at {path}. {_REBUILD_HINT}"
        )
    try:
        yield Storage(path)
    except sqlite3.OperationalError as exc:
        raise ToolError(
            f"The knowledge graph at {path} is unreadable ({exc}). {_REBUILD_HINT}"
        ) from exc


def _not_found(term: str) -> ToolError:
    return ToolError(
        f"No domain term matches '{term}'. Call list_domain_areas to see the areas "
        f"covered, or try the term's singular form or its name as used in the code."
    )


def lookup_term(term: str) -> TermRecord:
    with _storage() as store:
        try:
            node = store.lookup(term)
        except NodeNotFoundError:
            raise _not_found(term) from None
        return TermRecord(
            id=node.id,
            name=node.name,
            area=node.area,
            type=node.type,
            definition=node.definition,
            aliases=node.aliases,
            warnings=node.warnings,
            source_files=node.source_files,
            documentation=node.documentation,
        )


def get_related_terms(term: str) -> list[RelatedEdge]:
    with _storage() as store:
        try:
            edges = store.get_related(term)
        except NodeNotFoundError:
            raise _not_found(term) from None
        related: list[RelatedEdge] = []
        for edge in edges:
            try:
                to_name = store.lookup(edge.to_node).name
            except NodeNotFoundError:
                # An orphan edge; validate_knowledge_graph reports it properly.
                to_name = edge.to_node
            related.append(
                RelatedEdge(
                    {
                        "from": edge.from_node,
                        "to": edge.to_node,
                        "to_name": to_name,
                        "relationship": edge.relationship,
                    }
                )
            )
        return related


def list_domain_areas() -> list[str]:
    with _storage() as store:
        return store.list_areas()


def validate_knowledge_graph() -> ValidationReport:
    with _storage() as store:
        issues = store.validate_consistency()
        return ValidationReport(valid=not issues, issues=issues)
