"""MCP tools for Salesforce Data 360 (Customer Data Platform).

Wraps ``/services/data/vXX.X/ssot/`` — the Data 360 Connect REST API.
Includes the SQL query lifecycle (submit / poll / fetch rows) and a small
catalog of GETs for inspecting data spaces, data streams, calculated
insights, and segments. For anything else, reach into ``Data360Client``
directly via a future tool addition.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def data360_query_v2(
    query: dict[str, Any],
    dataspace: str | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run a Data 360 V2 (SAQL-style) query against ``/ssot/queryv2``.

    ``query`` is the document-form payload — refer to the Data 360 query
    reference for shape. ``dataspace`` defaults to the org's default
    dataspace when omitted.
    """
    async with org_context.data360(target_org) as client:
        return await client.query.query_v2(query, dataspace=dataspace)


@mcp.tool
async def data360_sql_run(
    sql: str,
    dataspace: str | None = None,
    workload_name: str | None = None,
    poll_interval: float = 1.5,
    poll_timeout: float = 300.0,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Submit a Data 360 SQL query, poll until done, return rows.

    Lifecycle: ``POST /ssot/query-sql`` → poll ``GET /ssot/query-sql/{id}``
    until ``status == "COMPLETED"`` → fetch first page via
    ``/ssot/query-sql/{id}/rows``. The result includes ``queryId``,
    ``status``, and ``rows``. Use ``data360_sql_rows`` to fetch additional
    pages for large result sets.
    """
    async with org_context.data360(target_org) as client:
        submit = await client.query.submit_sql_query(
            {"sql": sql}, dataspace=dataspace, workload_name=workload_name
        )
        query_id = submit.get("queryId") or submit.get("id")
        if not query_id:
            return {"error": "Data 360 SQL submit returned no queryId", "raw": submit}

        deadline = poll_timeout
        elapsed = 0.0
        status_payload: dict[str, Any] = {}
        while elapsed < deadline:
            status_payload = await client.query.get_sql_query_status(
                query_id, dataspace=dataspace, workload_name=workload_name
            )
            status = (status_payload.get("status") or "").upper()
            if status in {"COMPLETED", "SUCCEEDED"}:
                break
            if status in {"FAILED", "CANCELED", "CANCELLED"}:
                return {"queryId": query_id, "status": status, "raw": status_payload}
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            return {
                "queryId": query_id,
                "status": "TIMEOUT",
                "raw": status_payload,
            }

        if dataspace is None:
            return {
                "queryId": query_id,
                "status": status_payload.get("status"),
                "note": "Pass `dataspace` to fetch rows; omitted here.",
                "metadata": status_payload,
            }

        rows = await client.query.get_sql_query_rows(
            query_id,
            dataspace=dataspace,
            offset=0,
            workload_name=workload_name,
        )
        return {
            "queryId": query_id,
            "status": status_payload.get("status"),
            "metadata": status_payload,
            "rows": rows,
        }


@mcp.tool
async def data360_sql_rows(
    query_id: str,
    dataspace: str,
    offset: int = 0,
    row_limit: int | None = None,
    workload_name: str | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Fetch a page of rows from a completed Data 360 SQL query."""
    async with org_context.data360(target_org) as client:
        return await client.query.get_sql_query_rows(
            query_id,
            dataspace=dataspace,
            offset=offset,
            row_limit=row_limit,
            workload_name=workload_name,
        )
