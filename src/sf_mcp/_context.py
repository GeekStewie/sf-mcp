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


class OrgContext:
    """Resolve and cache Salesforce credentials for one or more org aliases."""

    def __init__(self) -> None:
        self._creds: dict[str, tuple[str, str, str]] = {}
        self._lock = asyncio.Lock()

    def resolve_alias(self, target_org: str | None) -> str:
        """Pick the alias from the call argument or the ``SF_MCP_ALIAS`` env var."""
        alias = target_org or os.environ.get(DEFAULT_ALIAS_ENV)
        if not alias:
            raise SalesforcePyError(
                "No Salesforce org alias provided. Pass `target_org` to the tool "
                f"or set the {DEFAULT_ALIAS_ENV} environment variable."
            )
        return alias

    async def creds(self, alias: str) -> tuple[str, str, str]:
        """Return cached ``(instance_url, access_token, username)`` for ``alias``."""
        if alias in self._creds:
            return self._creds[alias]
        async with self._lock:
            if alias in self._creds:
                return self._creds[alias]
            from salesforce_py.sf import SFOrg

            org = SFOrg(target_org=alias)
            await asyncio.to_thread(org._ensure_connected)
            self._creds[alias] = (org.instance_url, org.access_token, org.username)
            return self._creds[alias]

    def invalidate(self, alias: str) -> None:
        """Drop cached creds for ``alias`` (called automatically after a 401)."""
        self._creds.pop(alias, None)

    def task(self, target_org: str | None) -> SFOrgTask:
        """Return a fresh :class:`SFOrgTask` bound to the resolved alias."""
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
