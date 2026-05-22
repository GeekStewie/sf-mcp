"""MCP tools wrapping the Salesforce ``sf`` CLI via salesforce-py.

These tools cover org introspection, anonymous Apex, SOQL via the CLI
(useful when the REST extra isn't available), Apex test runs, and
deploy / retrieve. The CLI is sync-only inside salesforce-py, so each
call dispatches to a worker thread via :func:`asyncio.to_thread`.
"""

from __future__ import annotations

import asyncio
import contextlib
import tempfile
from pathlib import Path
from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def sf_org_list(target_org: str | None = None) -> dict[str, Any]:
    """List every Salesforce org authenticated with the local ``sf`` CLI.

    Equivalent to ``sf org list --json``. ``target_org`` is unused by the
    underlying command but is accepted for API consistency across tools.
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(task.org.list_orgs)


@mcp.tool
async def sf_org_display(target_org: str | None = None) -> dict[str, Any]:
    """Display credentials and metadata for one authenticated org.

    Equivalent to ``sf org display --target-org <alias> --json``. Returns
    instance URL, username, access token, expiration, and connection status.
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(task.org.display, True)


@mcp.tool
async def sf_apex_run_anonymous(
    apex_code: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Execute anonymous Apex against the org and return the result.

    The body is written to a temp file and passed to ``sf apex run --file``.
    Use this for ad-hoc queries, fix-ups, and one-off scripts that don't
    warrant a deploy.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".apex", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(apex_code)
        tmp_path = Path(fh.name)
    try:
        task = org_context.task(target_org)
        return await asyncio.to_thread(task.apex.run, tmp_path)
    finally:
        with contextlib.suppress(OSError):
            tmp_path.unlink()


@mcp.tool
async def sf_data_query(
    soql: str,
    target_org: str | None = None,
    use_tooling_api: bool = False,
    all_rows: bool = False,
) -> list[dict[str, Any]]:
    """Run a SOQL query via ``sf data query``.

    For most queries prefer ``soql_query`` (REST). Use this when the REST
    extra isn't available, or when CLI-style output is specifically needed.
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(
        lambda: task.data.query(soql=soql, use_tooling_api=use_tooling_api, all_rows=all_rows)
    )


@mcp.tool
async def sf_apex_run_tests(
    class_names: list[str] | None = None,
    tests: list[str] | None = None,
    test_level: str | None = None,
    code_coverage: bool = False,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Run Apex tests and return the result summary.

    ``test_level`` may be ``RunSpecifiedTests``, ``RunLocalTests``, or
    ``RunAllTestsInOrg``. ``class_names`` runs every method on the listed
    classes; ``tests`` accepts ``Class.method`` strings.
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(
        lambda: task.apex.run_tests(
            class_names=class_names,
            tests=tests,
            test_level=test_level,
            code_coverage=code_coverage,
        )
    )


@mcp.tool
async def sf_project_deploy(
    source_dir: str,
    test_level: str | None = None,
    dry_run: bool = False,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Deploy local metadata to the target org.

    Equivalent to ``sf project deploy start --source-dir <dir>``. Set
    ``dry_run=True`` for validation-only. ``test_level`` controls Apex
    test execution during deploy
    (``NoTestRun`` / ``RunLocalTests`` / ``RunAllTestsInOrg`` /
    ``RunSpecifiedTests`` / ``RunRelevantTests``).
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(
        lambda: task.project.deploy_start(
            source_dir=[source_dir],
            test_level=test_level,
            dry_run=dry_run,
        )
    )


@mcp.tool
async def sf_project_retrieve(
    output_dir: str,
    metadata: list[str] | None = None,
    package_name: list[str] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Retrieve metadata from the org into a local directory.

    Equivalent to ``sf project retrieve start --output-dir <dir>``.
    ``metadata`` accepts entries like ``ApexClass:MyClass`` or
    ``CustomObject:Account``.
    """
    task = org_context.task(target_org)
    return await asyncio.to_thread(
        lambda: task.project.retrieve_start(
            output_dir=Path(output_dir),
            metadata=metadata,
            package_name=package_name,
        )
    )
