# MCP Server

Conventions for every Model Context Protocol (MCP) server shipped under TMHSDigital. Covers tool naming, runtime choice, transport, error shape, destructive operations, auth, and the `mcp-tools.json` schema.

## Runtime choice

| Runtime | Use when |
| --- | --- |
| Python | Data-heavy processing, existing Python SDK (e.g. Plaid), scientific workloads, the ecosystem already has more Python repos |
| TypeScript | npm-publishable MCP server, Node-native APIs, the tool will be consumed by JavaScript tooling |

The runtime is chosen once, at repo creation, and recorded in `registry.json` `language`. Do not mix runtimes inside a single MCP server.

## Transport

- Default: `stdio`. Every tool repo publishes an MCP server that speaks stdio.
- `SSE` or `HTTP`: only when the server must run remotely (e.g. hosted behind an API gateway). Document the reason in the tool's README.
- `WebSocket`: not permitted without an amendment to this standard.

## Tool naming

Every MCP tool name follows this shape:

```
<tool-prefix>_<verbNoun>
```

| Part | Rule |
| --- | --- |
| `tool-prefix` | Short slug matching the repo, lowercase, no hyphens. `docker`, `plaid`, `homelab`, `monday`, `steam`, `mobile`. |
| `_` | Single underscore separator |
| `verbNoun` | camelCase, verb first. `listContainers`, `getAccount`, `searchItems`, `piStatus` |

Examples:

| Good | Bad |
| --- | --- |
| `docker_listContainers` | `dockerListContainers` (no underscore) |
| `plaid_getItem` | `plaid.getItem` (dot separator) |
| `homelab_piStatus` | `home_lab_pi_status` (snake_case verbNoun) |
| `steam_getAppDetails` | `Steam_GetAppDetails` (Pascal) |

The prefix acts as a namespace guard so tools from different servers never collide in an agent's tool list.

## Tool descriptions

Every tool has a `description` field in `mcp-tools.json`:

- One sentence, under 200 characters.
- Starts with an imperative verb: "List all running containers", not "Lists containers" or "A tool that lists containers".
- Mentions the primary input and output nouns.
- No marketing language.

## Destructive operations

A tool is **destructive** if it can modify or delete data, start or stop processes, move money, or otherwise produce effects the user cannot trivially undo.

Every destructive tool must:

| Requirement | Detail |
| --- | --- |
| Accept `confirm: boolean` | Required parameter. Tool returns an error message if `confirm` is missing or false. |
| Accept `dry_run: boolean` | Optional. When true, the tool simulates and returns what it would do without doing it. |
| Document effects | The `description` explicitly states the destructive action. |
| Require auth | The tool refuses to run if auth env vars are missing. |

Read-only tools do not need `confirm` or `dry_run`.

## Error shape

Every tool returns errors in the MCP standard shape:

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "<human-readable error>"
    }
  ]
}
```

- Never throw uncaught exceptions that propagate as protocol errors.
- Redact secrets and tokens from error messages before returning.
- Include a short error code in the text when helpful: `[AUTH_MISSING] PLAID_CLIENT_ID is not set.`.

## Auth patterns

| Pattern | Use |
| --- | --- |
| Environment variables | Default for all API keys, tokens, and secrets |
| `.env.example` | Required. Documents every variable the server reads |
| OAuth device flow | When the service supports it and tokens must be interactive (e.g. Monday, Steam) |
| Baked-in config | Never |

The server validates required env vars on startup and returns a clear error if any are missing, including the variable name and a link to the tool's README.

## `mcp-tools.json` schema

Every tool repo ships a `mcp-tools.json` file at the repo root. It drives the docs site and the `sync-check` validations.

```json
{
  "server": "docker-mcp",
  "prefix": "docker",
  "tools": [
    {
      "name": "docker_listContainers",
      "description": "List all running containers with status and ports.",
      "category": "containers",
      "destructive": false,
      "requiresConfirm": false
    },
    {
      "name": "docker_removeContainer",
      "description": "Remove a container by ID. Requires confirm=true.",
      "category": "containers",
      "destructive": true,
      "requiresConfirm": true
    }
  ]
}
```

Required fields per tool entry:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Full tool name with prefix |
| `description` | string | One sentence |
| `category` | string | Grouping for the docs site |
| `destructive` | bool | Whether the tool modifies external state |
| `requiresConfirm` | bool | Matches `destructive` for most tools |

## Testing

See [testing.md](testing.md) for the full matrix. Summary:

- Every tool in `mcp-tools.json` has one happy-path test.
- Every `destructive: true` tool has a test that asserts rejection when `confirm: false` or missing.
- Every tool description is validated for length and imperative-verb start by a schema test.

## Naming the server package

| Type | Example |
| --- | --- |
| npm package | `@tmhs/<tool>-mcp` |
| Python package | `<tool>_mcp` (PyPI not currently published) |
| Server folder in repo | `mcp-server/` |

## Migration

Existing tools that deviate from this standard (e.g. mixed camelCase/snake_case) should correct on their next minor version bump. Breaking tool renames require a major bump and a deprecation shim (keep the old name, log a warning, remove one minor version later).
