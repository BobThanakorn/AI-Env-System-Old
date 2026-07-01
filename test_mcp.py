"""Smoke tests for the TCC workspace MCP server."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from app.mcp.workspace_server import mcp

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


def _text(result) -> str:
    if not result.content:
        return ""
    block = result.content[0]
    return block.text if hasattr(block, "text") else str(block)


async def test_in_memory() -> None:
    async with create_connected_server_and_client_session(mcp) as session:
        tools = await session.list_tools()
        names = sorted(tool.name for tool in tools.tools)
        assert names == ["health", "list_workspace_files", "read_workspace_file"], names

        health = json.loads(_text(await session.call_tool("health", {})))
        assert health["status"] == "ok"
        assert health["server"] == "tcc-workspace"

        listing = json.loads(_text(await session.call_tool("list_workspace_files", {})))
        assert listing["tool"] == "list_files"
        assert isinstance(listing["files"], list)

        missing = json.loads(
            _text(await session.call_tool("read_workspace_file", {"path": "__missing_mcp_test__.txt"}))
        )
        assert "error" in missing

    print("in-memory MCP: OK")


async def test_stdio_subprocess() -> None:
    if not PYTHON.exists():
        print("stdio MCP: SKIP (venv python not found)")
        return

    params = StdioServerParameters(
        command=str(PYTHON),
        args=["run_mcp_server.py"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert "health" in names

            health = json.loads(_text(await session.call_tool("health", {})))
            assert health["status"] == "ok"

    print("stdio MCP: OK")


async def main() -> None:
    await test_in_memory()
    await test_stdio_subprocess()
    print("All MCP tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
