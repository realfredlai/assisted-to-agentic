"""Import YAML knowledge files into SQLite storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from knowledge_graph.storage import Edge, Node, Storage


class KnowledgeImportError(Exception):
    """Raised when YAML import fails."""


@dataclass
class ImportResult:
    nodes_imported: int
    edges_imported: int


def _load_yaml(path: Path) -> dict:
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise KnowledgeImportError(f"malformed YAML in {path}: {exc}") from exc


def import_yaml_tree(knowledge_dir: Path, storage: Storage) -> ImportResult:
    nodes_dir = knowledge_dir / "nodes"
    edges_dir = knowledge_dir / "edges"

    seen_ids: set[str] = set()
    nodes_count = 0

    for path in sorted(nodes_dir.glob("*.yaml")):
        data = _load_yaml(path)
        for raw in data.get("nodes", []):
            node_id = raw.get("id")
            if not node_id:
                raise KnowledgeImportError(f"node missing id in {path}: {raw!r}")
            if node_id in seen_ids:
                raise KnowledgeImportError(
                    f"duplicate node id '{node_id}' (second occurrence in {path})"
                )
            seen_ids.add(node_id)
            storage.insert_node(Node(
                id=node_id,
                type=raw.get("type", "domain_term"),
                area=raw.get("area", "general"),
                name=raw.get("name", node_id),
                definition=raw.get("definition", ""),
                aliases=raw.get("aliases", []) or [],
                warnings=raw.get("warnings", []) or [],
                source_files=raw.get("source_files", []) or [],
                documentation=raw.get("documentation", []) or [],
            ))
            nodes_count += 1

    edges_count = 0
    for path in sorted(edges_dir.glob("*.yaml")):
        data = _load_yaml(path)
        for raw in data.get("edges", []):
            from_node = raw.get("from")
            to_node = raw.get("to")
            relationship = raw.get("relationship")
            if not (from_node and to_node and relationship):
                raise KnowledgeImportError(f"edge missing field in {path}: {raw!r}")
            storage.insert_edge(Edge(
                from_node=from_node, to_node=to_node, relationship=relationship,
            ))
            edges_count += 1

    return ImportResult(nodes_imported=nodes_count, edges_imported=edges_count)
