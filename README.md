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
# bind a default org alias so tools don't have to be told each time:
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

Every tool accepts an optional `target_org` argument; when omitted the server falls back to the `SF_MCP_ALIAS` environment variable, then errors out if neither is set.

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
| `SF_MCP_ALIAS` | Default org alias when a tool call doesn't specify one |
| `SF_MODELS_CLIENT_ID` / `SF_MODELS_CLIENT_SECRET` | Required for Einstein Models tools |
| `SF_MODELS_INSTANCE_URL` | Override the My Domain used for Models OAuth (defaults to the alias's instance URL) |

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

Apache 2.0. See [LICENSE](LICENSE).
