# sf-mcp

[Model Context Protocol](https://modelcontextprotocol.io) server for Salesforce, built on [salesforce-py](https://github.com/geekstewie/salesforce-py) and [FastMCP](https://github.com/jlowin/fastmcp).

Exposes the Salesforce CLI, REST, Connect, Data 360, Models, and Bulk 2.0 APIs as MCP tools that any MCP-compatible client — Claude Code, Claude Desktop, Codex, Cursor — can call.

## Quick start

### 1. Authenticate at least one Salesforce org

`sf-mcp` reuses your local `sf` CLI session. Before running the server, log in to an org:

```bash
sf org login web --alias my-org
```

### 2. Install

```bash
uv tool install sf-mcp
# or:
pipx install sf-mcp
# or, in a project venv:
uv add sf-mcp
```

### 3. Add the server to your MCP client

#### Claude Code (CLI)

```bash
claude mcp add sf-mcp -- uvx sf-mcp
# Optional: pin a specific org alias for this MCP client. Otherwise sf-mcp
# uses SF_TARGET_ORG or the alias from `sf config get target-org`.
claude mcp add sf-mcp --env SF_MCP_ALIAS=my-org -- uvx sf-mcp
```

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "sf-mcp": {
      "command": "uvx",
      "args": ["sf-mcp"],
      "env": {
        "SF_MCP_ALIAS": "my-org"
      }
    }
  }
}
```

A copy of this config lives at [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json).

#### Cursor

Add to `~/.cursor/mcp.json` (or your workspace's `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sf-mcp": {
      "command": "uvx",
      "args": ["sf-mcp"],
      "env": {
        "SF_MCP_ALIAS": "my-org"
      }
    }
  }
}
```

A copy lives at [`examples/cursor_config.json`](examples/cursor_config.json).

#### Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.sf-mcp]
command = "uvx"
args = ["sf-mcp"]

[mcp_servers.sf-mcp.env]
SF_MCP_ALIAS = "my-org"
```

## Tools

Every tool accepts an optional `target_org` argument. Resolution order when it's omitted:

1. `SF_MCP_ALIAS` env var (explicit MCP-side override)
2. `SF_TARGET_ORG` env var (`sf` CLI's own standard)
3. `target-org` from the project-local `.sf/config.json` or the global `~/.sf/config.json` — i.e. whatever `sf config get target-org` would return

So if you've already run `sf config set target-org=my-org`, you don't need to set anything for sf-mcp.

### sf CLI (`sf_*`)

| Tool | Purpose |
| --- | --- |
| `sf_org_list` | List every authenticated org |
| `sf_org_display` | Show creds + metadata for the bound org |
| `sf_apex_run_anonymous` | Execute anonymous Apex |
| `sf_data_query` | SOQL via the CLI |
| `sf_apex_run_tests` | Run Apex tests |
| `sf_project_deploy` | Deploy a directory of metadata |
| `sf_project_retrieve` | Retrieve metadata into a local directory |

### REST API (`soql_*`, `sosl_*`, `sobject_*`, `tooling_*`, `limits_*`)

| Tool | Purpose |
| --- | --- |
| `soql_query` | Single-page SOQL via REST |
| `soql_query_all_pages` | Paginated SOQL — every record |
| `sosl_search` | Full-text SOSL search |
| `sobject_describe` | Field/relationship describe for one sObject |
| `sobject_list` | Describe-global — every sObject in the org |
| `sobject_get` | Get a record by ID |
| `sobject_create` | Create a record |
| `sobject_update` | Patch a record |
| `sobject_delete` | Delete a record |
| `sobject_upsert` | Upsert by external ID |
| `tooling_query` | SOQL against the Tooling API |
| `limits_get` | API/storage/governor limits |

### Connect REST (`connect_*`)

Generic passthroughs against `/services/data/vXX.X/connect/<path>`:

| Tool | Purpose |
| --- | --- |
| `connect_get` / `connect_post` / `connect_patch` / `connect_delete` | HTTP verb against any Connect subpath |

### Data 360 / CDP (`data360_*`)

| Tool | Purpose |
| --- | --- |
| `data360_query_v2` | Run a V2 (SAQL-style) query |
| `data360_sql_run` | Submit a SQL query, poll, and return rows |
| `data360_sql_rows` | Fetch additional row pages |

### Bulk API 2.0 (`bulk_*`)

| Tool | Purpose |
| --- | --- |
| `bulk_query` | End-to-end Bulk SOQL → CSV |
| `bulk_upsert` | End-to-end CSV upsert with polling |

### Einstein Models (`models_*`)

Requires `SF_MODELS_CLIENT_ID` and `SF_MODELS_CLIENT_SECRET` in the environment (Connected App with the `sfap_api einstein_gpt_api api` scopes).

| Tool | Purpose |
| --- | --- |
| `models_chat` | Chat completion |
| `models_embed` | Text embeddings |

## Configuration

| Env var | Purpose |
| --- | --- |
| `SF_MCP_ALIAS` | Optional. Highest-priority default org alias; overrides `SF_TARGET_ORG` and the sf CLI's own configured `target-org`. |
| `SF_TARGET_ORG` | Optional. Standard sf CLI env var; honoured when `SF_MCP_ALIAS` is unset. |
| `SF_MODELS_CLIENT_ID` / `SF_MODELS_CLIENT_SECRET` | Required for Einstein Models tools |
| `SF_MODELS_INSTANCE_URL` | Override the My Domain used for Models OAuth (defaults to the alias's instance URL) |

When neither env var is set and no `target_org` is passed, sf-mcp defers to `sf config get target-org` (project-local `.sf/config.json` first, then global `~/.sf/config.json`).

## Local development

```bash
git clone https://github.com/geekstewie/sf-mcp
cd sf-mcp
uv sync --extra dev

# Run the server in stdio mode
uv run python -m sf_mcp

# Run tests
uv run pytest

# Lint + format
uv run ruff check src/
uv run ruff format src/
```

## License
This project is a personal open-source project, released under the Apache License, Version 2.0.

You are free to use, modify, and distribute this software in accordance with the terms of the license. It is provided as-is, without warranty of any kind — express or implied — including but not limited to warranties of merchantability or fitness for a particular purpose. Use it at your own risk.

This project is not an official Salesforce product and is not affiliated with or endorsed by Salesforce, Inc. in any way.

See the LICENSE file for the full license text.
