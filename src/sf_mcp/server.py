"""FastMCP server registering all sf-mcp tools."""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP(
    name="sf-mcp",
    instructions=(
        "Salesforce MCP server. Tools are grouped by API surface: "
        "`sf_*` (sf CLI), `soql_*`/`sobject_*`/`tooling_*`/`limits_*` (REST), "
        "`connect_*` (Connect REST), `data360_*` (CDP), "
        "`bulk_*` (Bulk API 2.0), `models_*` (Einstein Models). "
        "Every tool accepts an optional `target_org` alias; when omitted, the "
        "server falls back to the SF_MCP_ALIAS environment variable."
    ),
)

# Importing the tool modules registers their @mcp.tool functions on the server.
from sf_mcp.tools import bulk, connect, data360, models, rest, sf_cli  # noqa: E402,F401

__all__ = ["mcp"]
