"""MCP server exposing TCC workspace file tools (stdio transport)."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.config import WORKSPACE_DIR
from app.tools.file_tools import list_files, read_file

mcp = FastMCP(
    "TCC Workspace",
    instructions=(
        "Tools for listing and reading files inside the TCC project workspace folder. "
        "Paths are relative to workspace/ (e.g. notes/example.md, scripts/Hello.py)."
    ),
)


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def health() -> str:
    """Return MCP server and workspace health status."""
    return _json(
        {
            "status": "ok",
            "server": "tcc-workspace",
            "workspace": str(WORKSPACE_DIR),
            "workspace_exists": WORKSPACE_DIR.is_dir(),
        }
    )


@mcp.tool()
def list_workspace_files() -> str:
    """List all files under the workspace directory."""
    return _json(list_files())


@mcp.tool()
def read_workspace_file(path: str) -> str:
    """Read a workspace file by relative path (text, markdown, or PDF)."""
    return _json(read_file(path))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
