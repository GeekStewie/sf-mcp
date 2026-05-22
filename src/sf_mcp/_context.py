"""Org credential resolution and lazy client construction.

The MCP server reuses the user's `sf` CLI session: every tool call resolves
an org alias to ``(instance_url, access_token, username)`` by invoking
``sf org display --json`` once per alias, then caches the credentials so
subsequent calls reuse them. Cached creds are dropped on 401 so the next
call re-runs ``sf org display`` to pick up a refreshed token.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from salesforce_py.exceptions import AuthError, SalesforcePyError

if TYPE_CHECKING:
    from salesforce_py.bulk import BulkClient
    from salesforce_py.connect import ConnectClient
    from salesforce_py.data360 import Data360Client
    from salesforce_py.models import ModelsClient
    from salesforce_py.rest import RestClient
    from salesforce_py.sf import SFOrgTask


DEFAULT_ALIAS_ENV = "SF_MCP_ALIAS"
SF_CLI_TARGET_ORG_ENV = "SF_TARGET_ORG"
DEFAULT_CACHE_KEY = "__default__"


class OrgContext:
    """Resolve and cache Salesforce credentials for one or more org aliases."""

    def __init__(self) -> None:
        self._creds: dict[str, tuple[str, str, str]] = {}
        self._lock = asyncio.Lock()

    def resolve_alias(self, target_org: str | None) -> str | None:
        """Resolve the org alias for a tool call.

        Priority:
          1. ``target_org`` argument
          2. ``SF_MCP_ALIAS`` env var (explicit MCP-side override)
          3. ``SF_TARGET_ORG`` env var (sf CLI's own standard)
          4. ``None`` — defer to whatever ``sf`` itself is configured to use
             (``target-org`` in the project-local ``.sf/config.json`` or the
             global ``~/.sf/config.json``).
        """
        return (
            target_org
            or os.environ.get(DEFAULT_ALIAS_ENV)
            or os.environ.get(SF_CLI_TARGET_ORG_ENV)
            or None
        )

    async def creds(self, alias: str | None) -> tuple[str, str, str]:
        """Return cached ``(instance_url, access_token, username)`` for ``alias``.

        Pass ``None`` to use the sf CLI's configured default org. The result is
        cached twice — once under the sentinel ``__default__`` key so the next
        ``None`` lookup is a hit, and once under the actual resolved alias so an
        explicit call for the same org also hits.
        """
        cache_key = alias or DEFAULT_CACHE_KEY
        if cache_key in self._creds:
            return self._creds[cache_key]
        async with self._lock:
            if cache_key in self._creds:
                return self._creds[cache_key]
            from salesforce_py.sf import SFOrg

            org = SFOrg(target_org=alias)
            await asyncio.to_thread(org._ensure_connected)
            if not org.instance_url or not org.access_token:
                raise SalesforcePyError(
                    "Could not resolve a Salesforce org from the sf CLI. Pass "
                    "`target_org` to the tool, set SF_MCP_ALIAS or "
                    "SF_TARGET_ORG, or run `sf config set "
                    "target-org=<alias>`."
                )
            creds = (org.instance_url, org.access_token, org.username)
            self._creds[cache_key] = creds
            if alias is None and org.alias:
                self._creds[org.alias] = creds
            return creds

    def invalidate(self, alias: str | None) -> None:
        """Drop cached creds for ``alias`` (called automatically after a 401)."""
        self._creds.pop(alias or DEFAULT_CACHE_KEY, None)

    def task(self, target_org: str | None) -> SFOrgTask:
        """Return a fresh :class:`SFOrgTask` bound to the resolved alias.

        Passes ``None`` straight through to ``SFOrgTask`` when no alias is
        configured, so the underlying ``sf`` CLI applies its own default.
        """
        from salesforce_py.sf import SFOrgTask

        return SFOrgTask(target_org=self.resolve_alias(target_org))

    @asynccontextmanager
    async def rest(self, target_org: str | None) -> AsyncGenerator[RestClient, None]:
        """Yield an open :class:`RestClient`. Drops cached creds on AuthError."""
        from salesforce_py.rest import RestClient

        alias = self.resolve_alias(target_org)
        instance_url, access_token, _ = await self.creds(alias)
        try:
            async with RestClient(instance_url, access_token) as client:
                yield client
        except AuthError:
            self.invalidate(alias)
            raise

    @asynccontextmanager
    async def connect(self, target_org: str | None) -> AsyncGenerator[ConnectClient, None]:
        """Yield an open :class:`ConnectClient`. Drops cached creds on AuthError."""
        from salesforce_py.connect import ConnectClient

        alias = self.resolve_alias(target_org)
        instance_url, access_token, _ = await self.creds(alias)
        try:
            async with ConnectClient(instance_url, access_token) as client:
                yield client
        except AuthError:
            self.invalidate(alias)
            raise

    @asynccontextmanager
    async def data360(self, target_org: str | None) -> AsyncGenerator[Data360Client, None]:
        """Yield an open :class:`Data360Client`. Drops cached creds on AuthError."""
        from salesforce_py.data360 import Data360Client

        alias = self.resolve_alias(target_org)
        instance_url, access_token, _ = await self.creds(alias)
        try:
            async with Data360Client(instance_url, access_token) as client:
                yield client
        except AuthError:
            self.invalidate(alias)
            raise

    @asynccontextmanager
    async def bulk(self, target_org: str | None) -> AsyncGenerator[BulkClient, None]:
        """Yield an open :class:`BulkClient`. Drops cached creds on AuthError."""
        from salesforce_py.bulk import BulkClient

        alias = self.resolve_alias(target_org)
        instance_url, access_token, _ = await self.creds(alias)
        try:
            async with BulkClient(instance_url, access_token) as client:
                yield client
        except AuthError:
            self.invalidate(alias)
            raise

    @asynccontextmanager
    async def models(self, target_org: str | None) -> AsyncGenerator[ModelsClient, None]:
        """Yield an open :class:`ModelsClient`.

        Models uses its own client-credentials OAuth flow against the org's
        My Domain. Required env vars: ``SF_MODELS_CLIENT_ID``,
        ``SF_MODELS_CLIENT_SECRET``. The instance URL is taken from
        ``SF_MODELS_INSTANCE_URL`` / ``SF_INSTANCE_URL``, falling back to
        the alias's ``instance_url`` from the cached sf CLI session.
        """
        from salesforce_py.models import ModelsClient

        if not os.environ.get("SF_MODELS_INSTANCE_URL") and not os.environ.get("SF_INSTANCE_URL"):
            try:
                alias = self.resolve_alias(target_org)
                instance_url, _, _ = await self.creds(alias)
                os.environ["SF_INSTANCE_URL"] = instance_url
            except SalesforcePyError:
                pass

        client = await ModelsClient.from_env()
        async with client:
            yield client


org_context = OrgContext()
