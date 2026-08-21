"""`manage.py knowledge` — query the config-service domain knowledge graph.

Subcommands mirror the Module 5 knowledge-graph reference CLI:
import / validate / lookup / related / list-areas.

Output is JSON by default so the CLI can be wrapped by a subprocess consumer
(e.g. an MCP server); pass --format table for human-readable output.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from knowledge_graph.importer import KnowledgeImportError, import_yaml_tree
from knowledge_graph.storage import NodeNotFoundError, Storage

# Defaults live at the config-service root (one level above backend/BASE_DIR),
# so the command behaves the same regardless of the caller's cwd.
DEFAULT_DB = Path(settings.BASE_DIR).parent / "knowledge.db"
DEFAULT_KNOWLEDGE_DIR = Path(settings.BASE_DIR).parent / "knowledge"


class Command(BaseCommand):
    help = "Query the domain knowledge graph (YAML -> SQLite -> CLI)."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        def common(sub):
            sub.add_argument(
                "--db", type=Path, default=DEFAULT_DB,
                help=f"SQLite path (default: {DEFAULT_DB})",
            )

        sub = subparsers.add_parser("import", help="Import YAML knowledge files into SQLite.")
        common(sub)
        sub.add_argument(
            "--knowledge-dir", type=Path, default=DEFAULT_KNOWLEDGE_DIR,
            help=f"Directory containing nodes/ and edges/ (default: {DEFAULT_KNOWLEDGE_DIR})",
        )

        sub = subparsers.add_parser("validate", help="Check for missing references.")
        common(sub)

        sub = subparsers.add_parser("lookup", help="Look up a term by id, name, or alias.")
        common(sub)
        sub.add_argument("term")
        sub.add_argument("--format", choices=["json", "table"], default="json")

        sub = subparsers.add_parser("related", help="List edges from this term.")
        common(sub)
        sub.add_argument("term")
        sub.add_argument("--format", choices=["json", "table"], default="json")

        sub = subparsers.add_parser("list-areas", help="List distinct domain areas.")
        common(sub)
        sub.add_argument("--format", choices=["json", "table"], default="json")

    def handle(self, *args, **options):
        handler = {
            "import": self._import,
            "validate": self._validate,
            "lookup": self._lookup,
            "related": self._related,
            "list-areas": self._list_areas,
        }[options["subcommand"]]
        handler(options)

    def _storage(self, options) -> Storage:
        storage = Storage(options["db"])
        storage.initialize_schema()
        return storage

    def _import(self, options):
        db: Path = options["db"]
        if db.exists():
            db.unlink()
        storage = self._storage(options)
        try:
            result = import_yaml_tree(options["knowledge_dir"], storage)
        except KnowledgeImportError as exc:
            raise CommandError(f"import failed: {exc}")
        self.stdout.write(f"imported {result.nodes_imported} nodes")
        self.stdout.write(f"imported {result.edges_imported} edge(s)")

    def _validate(self, options):
        issues = self._storage(options).validate_consistency()
        if not issues:
            self.stdout.write("knowledge graph is valid")
            return
        for issue in issues:
            self.stdout.write(issue)
        raise CommandError(f"knowledge graph has {len(issues)} issue(s)")

    def _lookup(self, options):
        storage = self._storage(options)
        term = options["term"]
        try:
            node = storage.lookup(term)
        except NodeNotFoundError:
            self.stdout.write(json.dumps({"error": "not_found", "term": term}))
            raise CommandError(f"term not found: {term}")
        if options["format"] == "json":
            self.stdout.write(json.dumps(asdict(node), ensure_ascii=False))
        else:
            self.stdout.write(f"{node.name} ({node.area})")
            self.stdout.write(f"  {node.definition.strip()}")
            if node.aliases:
                self.stdout.write(f"  aliases: {', '.join(node.aliases)}")
            for w in node.warnings:
                self.stdout.write(f"  warning: {w}")
            if node.source_files:
                self.stdout.write(f"  source: {', '.join(node.source_files)}")
            if node.documentation:
                self.stdout.write(f"  docs: {', '.join(node.documentation)}")

    def _related(self, options):
        storage = self._storage(options)
        term = options["term"]
        try:
            edges = storage.get_related(term)
        except NodeNotFoundError:
            self.stdout.write(json.dumps({"error": "not_found", "term": term}))
            raise CommandError(f"term not found: {term}")
        payload = [
            {"from": e.from_node, "to": e.to_node, "relationship": e.relationship}
            for e in edges
        ]
        if options["format"] == "json":
            self.stdout.write(json.dumps(payload, ensure_ascii=False))
        elif not payload:
            self.stdout.write("no relationships")
        else:
            for item in payload:
                self.stdout.write(
                    f"  {item['from']} --{item['relationship']}--> {item['to']}"
                )

    def _list_areas(self, options):
        areas = self._storage(options).list_areas()
        if options["format"] == "json":
            self.stdout.write(json.dumps(areas, ensure_ascii=False))
        else:
            for area in areas:
                self.stdout.write(f"  {area}")
