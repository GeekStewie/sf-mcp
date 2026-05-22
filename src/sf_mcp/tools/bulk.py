"""MCP tools for Bulk API 2.0 (large reads + writes via CSV).

Two end-to-end helpers covering the most common patterns:

- ``bulk_query`` — submit a SOQL query, poll, and return the full CSV
  payload as text. Handles ``ORDER BY`` reapply via DuckDB internally.
- ``bulk_upsert`` — create + upload + complete an upsert job from CSV
  text keyed on an external ID, then poll until terminal.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def bulk_query(
    soql: str,
    include_deleted: bool = False,
    poll_interval: float = 3.0,
    poll_timeout: float = 1800.0,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run a Bulk 2.0 SOQL query end-to-end and return CSV results.

    Strips ``ORDER BY`` for the API submit, polls until ``JobComplete``,
    downloads every page, then reapplies ``ORDER BY`` client-side via
    DuckDB. Returns the full CSV payload as a UTF-8 string under
    ``"csv"``. Use this for result sets too large for ``soql_query``.
    """
    operation = "queryAll" if include_deleted else "query"
    async with org_context.bulk(target_org) as client:
        csv_bytes = await client.query.run_query(
            soql,
            operation=operation,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
            auto_delete=True,
        )
        return {"csv": csv_bytes.decode("utf-8")}


@mcp.tool
async def bulk_upsert(
    object_name: str,
    external_id_field: str,
    csv_data: str,
    poll_interval: float = 3.0,
    poll_timeout: float = 1800.0,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run a Bulk 2.0 upsert from CSV text and wait for completion.

    The first line of ``csv_data`` must be a header row. ``external_id_field``
    is the API name of the field used to match existing records. Returns
    the final job state plus tallies of successful / failed / unprocessed
    records (without payloads — fetch results separately if needed).
    """
    async with org_context.bulk(target_org) as client:
        job = await client.ingest.upsert(
            object_name=object_name,
            external_id_field=external_id_field,
            csv_data=csv_data.encode("utf-8"),
        )
        job_id = job["id"]

        elapsed = 0.0
        state = job
        while elapsed < poll_timeout:
            state = await client.ingest.get_job(job_id)
            status = state.get("state", "")
            if status in {"JobComplete", "Failed", "Aborted"}:
                break
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            return {"jobId": job_id, "state": "TIMEOUT", "raw": state}

        return {
            "jobId": job_id,
            "state": state.get("state"),
            "numberRecordsProcessed": state.get("numberRecordsProcessed"),
            "numberRecordsFailed": state.get("numberRecordsFailed"),
            "errorMessage": state.get("errorMessage"),
            "raw": state,
        }
