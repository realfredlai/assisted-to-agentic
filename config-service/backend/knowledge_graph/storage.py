"""SQLite storage for the knowledge graph.

Deliberately independent of Django's ORM and Postgres: the knowledge graph is
domain *language*, not application data. A single SQLite file keeps it out of
the app's migration history, works with the database container down, and stays
trivially inspectable (`sqlite3 knowledge.db .schema`).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


class NodeNotFoundError(LookupError):
    """Raised when a node lookup returns no match (including alias matches)."""


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    area: str
    name: str
    definition: str
    aliases: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Edge:
    from_node: str
    to_node: str
    relationship: str


class Storage:
    """Owns the SQLite store and exposes the query primitives."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS nodes (
        id            TEXT PRIMARY KEY,
        type          TEXT NOT NULL,
        area          TEXT NOT NULL,
        name          TEXT NOT NULL,
        definition    TEXT NOT NULL,
        aliases       TEXT NOT NULL DEFAULT '[]',
        warnings      TEXT NOT NULL DEFAULT '[]',
        source_files  TEXT NOT NULL DEFAULT '[]',
        documentation TEXT NOT NULL DEFAULT '[]'
    );

    CREATE TABLE IF NOT EXISTS edges (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        from_node    TEXT NOT NULL,
        to_node      TEXT NOT NULL,
        relationship TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_node);
    CREATE INDEX IF NOT EXISTS idx_edges_to   ON edges(to_node);
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(self.SCHEMA)

    def insert_node(self, node: Node) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO nodes
                  (id, type, area, name, definition, aliases, warnings,
                   source_files, documentation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.id, node.type, node.area, node.name, node.definition,
                    json.dumps(node.aliases),
                    json.dumps(node.warnings),
                    json.dumps(node.source_files),
                    json.dumps(node.documentation),
                ),
            )

    def insert_edge(self, edge: Edge) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO edges (from_node, to_node, relationship) VALUES (?, ?, ?)",
                (edge.from_node, edge.to_node, edge.relationship),
            )

    def _row_to_node(self, row: sqlite3.Row) -> Node:
        return Node(
            id=row["id"],
            type=row["type"],
            area=row["area"],
            name=row["name"],
            definition=row["definition"],
            aliases=json.loads(row["aliases"]),
            warnings=json.loads(row["warnings"]),
            source_files=json.loads(row["source_files"]),
            documentation=json.loads(row["documentation"]),
        )

    def lookup(self, term: str) -> Node:
        """Find a node by id, name, or alias. Case-insensitive."""
        term_lower = term.strip().lower()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE lower(id) = ? OR lower(name) = ? LIMIT 1",
                (term_lower, term_lower),
            ).fetchone()
            if row:
                return self._row_to_node(row)
            # Alias scan (small N; fine to do in Python)
            for row in conn.execute("SELECT * FROM nodes").fetchall():
                aliases = {a.lower() for a in json.loads(row["aliases"])}
                if term_lower in aliases:
                    return self._row_to_node(row)
        raise NodeNotFoundError(term)

    def get_related(self, term: str) -> list[Edge]:
        node = self.lookup(term)
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT from_node, to_node, relationship FROM edges WHERE from_node = ?",
                (node.id,),
            ).fetchall()
        return [Edge(from_node=r["from_node"], to_node=r["to_node"],
                     relationship=r["relationship"]) for r in rows]

    def list_areas(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT area FROM nodes ORDER BY area"
            ).fetchall()
        return [r["area"] for r in rows]

    def validate_consistency(self) -> list[str]:
        issues: list[str] = []
        with self._conn() as conn:
            node_ids = {r["id"] for r in conn.execute("SELECT id FROM nodes").fetchall()}
            for row in conn.execute(
                "SELECT from_node, to_node, relationship FROM edges"
            ).fetchall():
                if row["from_node"] not in node_ids:
                    issues.append(
                        f"edge references missing from_node '{row['from_node']}' "
                        f"({row['relationship']} -> {row['to_node']})"
                    )
                if row["to_node"] not in node_ids:
                    issues.append(
                        f"edge references missing to_node '{row['to_node']}' "
                        f"(from {row['from_node']}, {row['relationship']})"
                    )
        return issues
