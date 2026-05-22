"""sf-mcp: Model Context Protocol server for Salesforce.

Wraps the `salesforce-py` library and exposes its capabilities as MCP tools
for Claude Code, Claude Desktop, Codex, Cursor, and any other MCP client.
"""

from sf_mcp._version import __version__
from sf_mcp.server import mcp

__all__ = ["__version__", "mcp"]
