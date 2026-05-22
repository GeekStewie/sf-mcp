"""Entry point: ``python -m sf_mcp`` and the ``sf-mcp`` console script."""

from __future__ import annotations

from sf_mcp.server import mcp


def main() -> None:
    """Run the FastMCP server over stdio (the default MCP transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
