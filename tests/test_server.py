"""Smoke tests — server boots and registers every expected tool."""

from __future__ import annotations

import pytest


def test_server_imports():
    """The package must import without side effects requiring an org."""
    import sf_mcp

    assert sf_mcp.__version__


@pytest.mark.asyncio
async def test_tools_are_registered():
    """Every documented tool must be present on the FastMCP instance."""
    from sf_mcp import mcp

    expected = {
        # sf CLI
        "sf_org_list",
        "sf_org_display",
        "sf_apex_run_anonymous",
        "sf_data_query",
        "sf_apex_run_tests",
        "sf_project_deploy",
        "sf_project_retrieve",
        # REST
        "soql_query",
        "soql_query_all_pages",
        "sosl_search",
        "sobject_describe",
        "sobject_list",
        "sobject_get",
        "sobject_create",
        "sobject_update",
        "sobject_delete",
        "sobject_upsert",
        "tooling_query",
        "limits_get",
        # Connect
        "connect_get",
        "connect_post",
        "connect_patch",
        "connect_delete",
        # Data 360
        "data360_query_v2",
        "data360_sql_run",
        "data360_sql_rows",
        # Bulk
        "bulk_query",
        "bulk_upsert",
        # Models
        "models_chat",
        "models_embed",
    }
    tools = await mcp.list_tools()
    registered = {t.name for t in tools}
    missing = expected - registered
    assert not missing, f"Missing tools: {missing}"


def test_resolve_alias_requires_alias_or_env(monkeypatch):
    """resolve_alias raises if neither argument nor env var is set."""
    from salesforce_py.exceptions import SalesforcePyError

    from sf_mcp._context import org_context

    monkeypatch.delenv("SF_MCP_ALIAS", raising=False)
    with pytest.raises(SalesforcePyError):
        org_context.resolve_alias(None)


def test_resolve_alias_prefers_argument_over_env(monkeypatch):
    from sf_mcp._context import org_context

    monkeypatch.setenv("SF_MCP_ALIAS", "from-env")
    assert org_context.resolve_alias("from-arg") == "from-arg"
    assert org_context.resolve_alias(None) == "from-env"
