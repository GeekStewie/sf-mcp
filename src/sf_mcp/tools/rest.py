"""MCP tools wrapping the Salesforce REST API via salesforce-py.

Covers the most common ``/services/data/vXX.X/`` operations: SOQL/SOSL
queries, sObject CRUD (incl. external-ID upsert), describe, Tooling API,
and org limits. For anything not covered, drop down to ``connect_get`` /
``connect_post`` or extend this module with the relevant ``salesforce_py.rest.*``
namespace.
"""

from __future__ import annotations

from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def soql_query(
    soql: str,
    target_org: str | None = None,
    include_deleted: bool = False,
) -> dict[str, Any]:
    """Run a SOQL query via the REST API.

    Returns a single page of results — a dict with ``totalSize``,
    ``done``, ``records``, and (when paginated) ``nextRecordsUrl``. Set
    ``include_deleted=True`` to include soft-deleted records (uses the
    ``queryAll`` endpoint).
    """
    async with org_context.rest(target_org) as client:
        if include_deleted:
            return await client.query.query_all(soql)
        return await client.query.query(soql)


@mcp.tool
async def soql_query_all_pages(
    soql: str,
    target_org: str | None = None,
) -> list[dict[str, Any]]:
    """Run a SOQL query and follow ``nextRecordsUrl`` to return every record.

    Use sparingly — for large result sets prefer ``bulk_query``. Returns
    a flat list of record dicts.
    """
    async with org_context.rest(target_org) as client:
        return await client.query.query_all_records(soql)


@mcp.tool
async def sosl_search(
    sosl: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run a SOSL full-text search via the REST API.

    Example query: ``FIND {Acme} IN ALL FIELDS RETURNING Account(Id, Name)``.
    """
    async with org_context.rest(target_org) as client:
        return await client.search.search(sosl)


@mcp.tool
async def sobject_describe(
    object_name: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Return the full describe payload for an sObject.

    Lists every field, child relationship, record type, action override,
    layout, and supported flag. Useful before generating SOQL or building
    UI for a custom object.
    """
    async with org_context.rest(target_org) as client:
        return await client.sobjects.describe_object(object_name)


@mcp.tool
async def sobject_list(target_org: str | None = None) -> dict[str, Any]:
    """List every sObject available in the org along with its basic metadata."""
    async with org_context.rest(target_org) as client:
        return await client.sobjects.describe_global()


@mcp.tool
async def sobject_get(
    object_name: str,
    record_id: str,
    fields: list[str] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Retrieve a single record by ID, optionally filtering fields.

    When ``fields`` is omitted, Salesforce returns every accessible field
    (which can be expensive on wide objects).
    """
    async with org_context.rest(target_org) as client:
        return await client.sobjects.get(object_name, record_id, fields=fields)


@mcp.tool
async def sobject_create(
    object_name: str,
    record: dict[str, Any],
    target_org: str | None = None,
) -> dict[str, Any]:
    """Create a record. Returns ``{"id": ..., "success": true}`` on success."""
    async with org_context.rest(target_org) as client:
        return await client.sobjects.create(object_name, record)


@mcp.tool
async def sobject_update(
    object_name: str,
    record_id: str,
    record: dict[str, Any],
    target_org: str | None = None,
) -> dict[str, Any]:
    """Patch a record by ID. Returns ``{}`` on success (HTTP 204)."""
    async with org_context.rest(target_org) as client:
        return await client.sobjects.update(object_name, record_id, record)


@mcp.tool
async def sobject_delete(
    object_name: str,
    record_id: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Delete a record by ID. Returns ``{}`` on success (HTTP 204)."""
    async with org_context.rest(target_org) as client:
        return await client.sobjects.delete(object_name, record_id)


@mcp.tool
async def sobject_upsert(
    object_name: str,
    external_id_field: str,
    external_id: str,
    record: dict[str, Any],
    target_org: str | None = None,
) -> dict[str, Any]:
    """Upsert a record by external ID via PATCH ``/sobjects/<obj>/<field>/<value>``.

    Creates a new record when no match exists, updates the matched record
    otherwise. Idempotent on retry — safe for integration loops.
    """
    async with org_context.rest(target_org) as client:
        return await client.sobjects.upsert(object_name, external_id_field, external_id, record)


@mcp.tool
async def tooling_query(
    soql: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run a SOQL query against the Tooling API.

    Use this for metadata-style queries that the standard SOQL API can't
    answer — ``ApexClass``, ``CustomField``, ``ValidationRule``,
    ``Flow``, ``ApexLog``, etc.
    """
    async with org_context.rest(target_org) as client:
        return await client.tooling.query(soql)


@mcp.tool
async def limits_get(target_org: str | None = None) -> dict[str, Any]:
    """Return the org's current API / storage / governor limits."""
    async with org_context.rest(target_org) as client:
        return await client.limits.get_limits()
