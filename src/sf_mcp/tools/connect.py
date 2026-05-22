"""MCP tools for the Salesforce Connect REST API surface.

Exposes generic ``get`` / ``post`` / ``patch`` / ``delete`` against
``/services/data/vXX.X/connect/<subpath>``. Use these for Chatter feeds,
Communities, Files, Agentforce data libraries, named credentials, and any
other ``/connect/*`` endpoint not covered by a dedicated REST tool.

The Connect surface is huge (60+ namespaces) — exposing it as a generic
passthrough keeps the tool count tractable while letting callers reach any
endpoint by URL path. Refer to the REST/Connect Developer Guides for the
documented subpaths.
"""

from __future__ import annotations

from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def connect_get(
    path: str,
    params: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """GET ``/services/data/vXX.X/connect/<path>``.

    ``path`` is the portion after ``/connect/`` — e.g. ``"chatter/feeds/news/me/feed-elements"``,
    ``"communities"``, or ``"agentforce-data-libraries"``. Pass query string
    args via ``params``.
    """
    async with org_context.rest(target_org) as client:
        return await client.connect.get(path, params=params)


@mcp.tool
async def connect_post(
    path: str,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """POST a JSON body to ``/services/data/vXX.X/connect/<path>``."""
    async with org_context.rest(target_org) as client:
        return await client.connect.post(path, json=body, params=params)


@mcp.tool
async def connect_patch(
    path: str,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """PATCH ``/services/data/vXX.X/connect/<path>`` with a JSON body."""
    async with org_context.rest(target_org) as client:
        return await client.connect.patch(path, json=body, params=params)


@mcp.tool
async def connect_delete(
    path: str,
    params: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """DELETE ``/services/data/vXX.X/connect/<path>``."""
    async with org_context.rest(target_org) as client:
        return await client.connect.delete(path, params=params)
