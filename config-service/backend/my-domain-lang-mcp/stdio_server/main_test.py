"""Black-box tests for the stdio server's protocol layer.

Tool *behaviour* lives in `tools_test.py`; this file covers the transport and
the error channels underneath it, at two levels:

- In-memory: ``Client(server)`` dispatches in-process (no JSON-RPC framing) —
  handshake semantics, the advertised surface, and error-then-survive
  behaviour, fast.
- Subprocess: spawn ``sys.executable -m stdio_server.main`` and speak real
  stdio — the SDK-client handshake, hand-rolled JSON-RPC exchanges asserting
  stdout carries only protocol frames, a real tools/call, and clean exit on
  client disconnect.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import mcp.types as types
import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import MCPError

from stdio_server.main import SERVER_NAME, SERVER_VERSION, build_server

PROJECT_DIR = Path(__file__).resolve().parents[1]
SERVER_CMD = [sys.executable, "-m", "stdio_server.main"]


async def test_handshake_completes_in_memory():
    async with Client(build_server()) as client:
        assert client.server_info is not None
        assert client.server_info.name == SERVER_NAME
        assert client.server_info.version == SERVER_VERSION
        assert isinstance(client.protocol_version, str) and client.protocol_version


async def test_exposes_knowledge_tools_but_no_resources_or_prompts():
    """Replaces work item 002's AC2 (`test_no_tools_resources_or_prompts`).

    Phase 1 asserted an empty tool list — that was its whole point. Phase 2 makes
    it false by design, so the criterion was changed deliberately rather than the
    test quietly weakened: resources and prompts are still asserted empty, and the
    tool list is now pinned to the four knowledge tools.
    """
    async with Client(build_server()) as client:
        assert {t.name for t in (await client.list_tools()).tools} == {
            "lookup_term",
            "get_related_terms",
            "list_domain_areas",
            "validate_knowledge_graph",
        }
        assert (await client.list_resources()).resources == []
        assert (await client.list_prompts()).prompts == []


async def test_unknown_tool_yields_protocol_error_not_crash():
    # Spec (Tools § Error Handling): unknown tool is a protocol error, -32602.
    async with Client(build_server()) as client:
        with pytest.raises(MCPError) as exc_info:
            await client.call_tool("does_not_exist", {})
        assert exc_info.value.code == types.INVALID_PARAMS
        assert "does_not_exist" in exc_info.value.message
        # the error did not poison the session
        assert (await client.list_tools()).tools


async def test_handshake_over_real_stdio():
    params = StdioServerParameters(
        command=SERVER_CMD[0],
        args=SERVER_CMD[1:],
        cwd=str(PROJECT_DIR),
    )
    async with Client(stdio_client(params)) as client:
        assert client.server_info is not None
        assert client.server_info.name == SERVER_NAME
        assert client.protocol_version


def _frame(payload: dict) -> str:
    return json.dumps(payload) + "\n"


def test_raw_initialize_and_stderr_discipline():
    # Incremental exchange: read each response before sending the next frame
    # (closing stdin early races the server's shutdown against its dispatch).
    proc = subprocess.Popen(
        SERVER_CMD,
        cwd=PROJECT_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    killer = threading.Timer(30, proc.kill)
    killer.start()
    try:
        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": types.LATEST_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "raw-test", "version": "0"},
                    },
                }
            )
        )
        proc.stdin.flush()
        init_response = json.loads(proc.stdout.readline())

        proc.stdin.write(_frame({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        proc.stdin.write(_frame({"jsonrpc": "2.0", "id": 2, "method": "no/such-method"}))
        proc.stdin.flush()
        error_response = json.loads(proc.stdout.readline())

        # the spec's own protocol-error example: tools/call with an unknown name
        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "invalid_tool_name", "arguments": {}},
                }
            )
        )
        proc.stdin.flush()
        unknown_tool_response = json.loads(proc.stdout.readline())

        proc.stdin.close()
        returncode = proc.wait(timeout=30)
        remaining_out = proc.stdout.read()
        err = proc.stderr.read()
    finally:
        killer.cancel()

    assert returncode == 0
    assert init_response["id"] == 1
    assert init_response["result"]["serverInfo"]["name"] == SERVER_NAME
    # unknown method after the handshake gets a JSON-RPC error, not a crash
    assert error_response["id"] == 2
    assert error_response["error"]["code"] == types.METHOD_NOT_FOUND
    # unknown tool is a protocol error (-32602), not a tool-execution result
    assert unknown_tool_response["id"] == 3
    assert unknown_tool_response["error"]["code"] == types.INVALID_PARAMS
    assert unknown_tool_response["error"]["message"] == "Unknown tool: invalid_tool_name"
    assert "result" not in unknown_tool_response
    # anything else stdout emitted must still be pure JSON-RPC frames
    for line in remaining_out.splitlines():
        if line.strip():
            json.loads(line)
    # the startup log line landed on stderr, and only there
    assert "starting" in err
    assert "starting" not in remaining_out


def test_clean_exit_on_client_disconnect():
    proc = subprocess.Popen(
        SERVER_CMD,
        cwd=PROJECT_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # close stdin immediately: the client vanished before saying hello
    out, err = proc.communicate("", timeout=30)
    assert proc.returncode == 0
    assert "Traceback" not in err
    assert out == ""


def test_raw_tools_call_over_stdio(tmp_path):
    """A real tools/call across the wire: structured result, stdout stays pure."""
    from knowledge_graph.storage import Node, Storage

    db = tmp_path / "knowledge.db"
    store = Storage(db)
    store.initialize_schema()
    store.insert_node(
        Node(
            id="configuration",
            type="domain_term",
            area="config_storage",
            name="Configuration",
            definition="A named set of environment settings.",
            aliases=["config"],
        )
    )

    proc = subprocess.Popen(
        SERVER_CMD,
        cwd=PROJECT_DIR,
        env={**os.environ, "KNOWLEDGE_DB": str(db)},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    killer = threading.Timer(30, proc.kill)
    killer.start()
    try:
        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": types.LATEST_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "raw-test", "version": "0"},
                    },
                }
            )
        )
        proc.stdin.flush()
        proc.stdout.readline()
        proc.stdin.write(_frame({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "lookup_term", "arguments": {"term": "config"}},
                }
            )
        )
        proc.stdin.flush()
        call_response = json.loads(proc.stdout.readline())
        proc.stdin.close()
        returncode = proc.wait(timeout=30)
        err = proc.stderr.read()
    finally:
        killer.cancel()

    assert returncode == 0
    assert call_response["id"] == 2
    result = call_response["result"]
    assert result.get("isError") in (None, False)
    assert result["structuredContent"]["id"] == "configuration"
    assert "Traceback" not in err
