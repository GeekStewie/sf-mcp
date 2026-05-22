"""MCP tools for the Salesforce Einstein Models REST API.

Wraps the chat-generations and embeddings capabilities. The Models API
uses a separate client-credentials OAuth flow against the org's My
Domain — set ``SF_MODELS_CLIENT_ID`` and ``SF_MODELS_CLIENT_SECRET``
in the environment to enable. The instance URL is taken from the
linked sf CLI alias automatically.
"""

from __future__ import annotations

from typing import Any

from sf_mcp._context import org_context
from sf_mcp.server import mcp


@mcp.tool
async def models_chat(
    model_name: str,
    messages: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Generate a chat completion via Einstein Models.

    ``model_name`` is the API name (e.g.
    ``"sfdc_ai__DefaultOpenAIGPT4OmniMini"``,
    ``"sfdc_ai__DefaultBedrockAnthropicClaude46Sonnet"``). ``messages`` is
    the OpenAI-style list of role/content dicts. Pass model-specific
    parameters (``temperature``, ``max_tokens``, ``localization``, etc.)
    via ``extra``.
    """
    async with org_context.models(target_org) as client:
        return await client.chat_generations.generate(model_name, messages, extra=extra)


@mcp.tool
async def models_embed(
    model_name: str,
    inputs: list[str],
    extra: dict[str, Any] | None = None,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Create embeddings for one or more strings via Einstein Models.

    Even when embedding a single string, pass it as a one-element list —
    the underlying API requires the ``input`` field to be an array.
    """
    async with org_context.models(target_org) as client:
        return await client.embeddings.embed(model_name, inputs, extra=extra)
