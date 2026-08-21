"""Tests for the knowledge graph CLI (manage.py knowledge).

SimpleTestCase throughout: these tests touch a temp SQLite file, never the
Postgres database.
"""

from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from knowledge_graph.management.commands.knowledge import DEFAULT_KNOWLEDGE_DIR

MINIMAL_NODES = """
nodes:
  - id: application
    name: Application
    area: config_storage
    type: domain_term
    definition: An application owned by the organization.
    aliases:
      - app
  - id: configuration
    name: Configuration
    area: config_storage
    type: domain_term
    definition: A named set of environment settings.
  - id: user
    name: User
    area: user_directory
    type: domain_term
    definition: A directory entry for a person.
    warnings:
      - Not an auth account.
"""

MINIMAL_EDGES = """
edges:
  - from: application
    to: configuration
    relationship: owns
"""


class KnowledgeCommandTestCase(SimpleTestCase):
    """Shared scaffolding: a temp knowledge tree and db path per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.knowledge_dir = root / "knowledge"
        (self.knowledge_dir / "nodes").mkdir(parents=True)
        (self.knowledge_dir / "edges").mkdir(parents=True)
        (self.knowledge_dir / "nodes" / "core.yaml").write_text(MINIMAL_NODES)
        (self.knowledge_dir / "edges" / "core.yaml").write_text(MINIMAL_EDGES)
        self.db = root / "knowledge.db"

    def knowledge(self, *args) -> str:
        out = StringIO()
        call_command("knowledge", *args, "--db", str(self.db), stdout=out)
        return out.getvalue()

    def do_import(self) -> str:
        return self.knowledge("import", "--knowledge-dir", str(self.knowledge_dir))


class ImportCommandTest(KnowledgeCommandTestCase):
    def test_import_reports_counts(self):
        output = self.do_import()
        self.assertIn("imported 3 nodes", output)
        self.assertIn("imported 1 edge(s)", output)
        self.assertTrue(self.db.exists())

    def test_duplicate_id_fails(self):
        (self.knowledge_dir / "nodes" / "dupe.yaml").write_text("""
nodes:
  - id: application
    name: Application Again
    area: config_storage
    type: domain_term
    definition: duplicate
""")
        with self.assertRaises(CommandError) as ctx:
            self.do_import()
        self.assertIn("duplicate node id 'application'", str(ctx.exception))


class LookupCommandTest(KnowledgeCommandTestCase):
    def test_resolves_by_id_name_and_alias(self):
        self.do_import()
        for term in ("application", "Application", "APPLICATION", "app"):
            with self.subTest(term=term):
                node = json.loads(self.knowledge("lookup", term))
                self.assertEqual(node["id"], "application")
                self.assertEqual(node["name"], "Application")
                self.assertEqual(node["aliases"], ["app"])
                self.assertIn("definition", node)
                self.assertIn("warnings", node)
                self.assertIn("source_files", node)

    def test_unknown_term_exits_nonzero(self):
        self.do_import()
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("knowledge", "lookup", "nonsense", "--db", str(self.db),
                         stdout=out)
        self.assertEqual(json.loads(out.getvalue()),
                         {"error": "not_found", "term": "nonsense"})

    def test_table_format(self):
        self.do_import()
        output = self.knowledge("lookup", "user", "--format", "table")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(output)
        self.assertIn("User (user_directory)", output)
        self.assertIn("A directory entry for a person.", output)
        self.assertIn("warning: Not an auth account.", output)


class RelatedCommandTest(KnowledgeCommandTestCase):
    def test_returns_outgoing_edges(self):
        self.do_import()
        edges = json.loads(self.knowledge("related", "application"))
        self.assertEqual(edges, [
            {"from": "application", "to": "configuration", "relationship": "owns"},
        ])
        # Edges are directed: configuration has no outgoing edges.
        self.assertEqual(json.loads(self.knowledge("related", "configuration")), [])


class ListAreasCommandTest(KnowledgeCommandTestCase):
    def test_distinct_sorted(self):
        self.do_import()
        areas = json.loads(self.knowledge("list-areas"))
        self.assertEqual(areas, ["config_storage", "user_directory"])


class ValidateCommandTest(KnowledgeCommandTestCase):
    def test_clean_graph_passes(self):
        self.do_import()
        self.assertIn("knowledge graph is valid", self.knowledge("validate"))

    def test_orphan_edge_detected(self):
        (self.knowledge_dir / "edges" / "core.yaml").write_text("""
edges:
  - from: application
    to: missing_term
    relationship: owns
""")
        self.do_import()
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("knowledge", "validate", "--db", str(self.db), stdout=out)
        self.assertIn("missing to_node 'missing_term'", out.getvalue())


class RealKnowledgeTest(KnowledgeCommandTestCase):
    """The shipped knowledge/ tree must import and validate cleanly."""

    def test_shipped_knowledge_imports_and_validates(self):
        output = self.knowledge("import", "--knowledge-dir", str(DEFAULT_KNOWLEDGE_DIR))
        self.assertIn("imported 5 nodes", output)
        self.assertIn("imported 6 edge(s)", output)
        self.assertIn("knowledge graph is valid", self.knowledge("validate"))
