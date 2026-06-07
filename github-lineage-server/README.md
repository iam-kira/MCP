# GitHub Lineage MCP Server

This server provides lightweight lineage extraction from SQL assets stored in GitHub repositories. It uses GitHub REST APIs for discovery/retrieval and a deterministic regex-based parser to infer table dependency edges.

## Scope and non-goals

### In scope

- Repository-aware SQL search.
- File content retrieval from a specific branch/ref.
- Snapshot lineage graph generation from `.sql` blobs.

### Out of scope (current version)

- Full SQL AST parsing.
- Cross-file procedural lineage resolution.
- Dialect-specific SQL semantics.

## Tool contracts

| Tool | Purpose | Key Inputs | Output Shape |
| --- | --- | --- | --- |
| `github_health` | Validate GitHub connectivity/auth | none | `{ ok, authenticated, login, base_url }` |
| `search_sql_files` | Search SQL files via GitHub code search | `query, owner, repo, branch, limit` | `{ query, repo, count, items[] }` |
| `get_file_text` | Retrieve and decode repository file content | `path, owner, repo, branch` | `{ path, repo, branch, size, text }` |
| `build_sql_lineage_snapshot` | Build table-edge graph from SQL files | `owner, repo, branch, max_files` | `{ repo, nodes[], edges[], edge_count_by_file }` |

## Lineage extraction logic

The parser scans SQL text with pattern matching over clauses such as `FROM`, `JOIN`, `INTO`, `UPDATE`, and `TABLE`. For each file:

1. Extract candidate table tokens.
2. Normalize and de-duplicate table names.
3. Use the first table as target and remaining tables as sources.
4. Emit `depends_on` edges with file context.

This model is intentionally conservative and optimized for fast discovery over precision.

## Configuration

Copy `.env.example` to `.env` and define:

| Variable | Required | Description |
| --- | --- | --- |
| `GITHUB_TOKEN` | Recommended | Personal token for authenticated API calls |
| `GITHUB_BASE_URL` | Optional | Defaults to `https://api.github.com` |
| `GITHUB_API_VERSION` | Optional | API version header value |
| `DEFAULT_OWNER` | Optional | Default repository owner when omitted |
| `DEFAULT_REPO` | Optional | Default repository name when omitted |
| `DEFAULT_BRANCH` | Optional | Fallback branch (default `main`) |

## Setup and run

```bash
pip install -r requirements.txt
python app/server.py
```

Server endpoint starts on port `8101` using `streamable-http` transport.

## Operational notes

- Limits are clamped to avoid large unbounded scans.
- `build_sql_lineage_snapshot` scans up to `max_files` SQL blobs and skips unreadable files.
- Unauthorized or missing token scenarios return health failures or HTTP errors from GitHub.

## Example progression

1. `github_health` to validate credentials.
2. `search_sql_files("customer", owner, repo)` to identify candidate scripts.
3. `build_sql_lineage_snapshot(owner, repo, branch, max_files=30)` for graph generation.
4. Persist `nodes/edges` output in your downstream lineage store or graph DB.

## Extension points

- Replace regex parser with SQL AST parser for better lineage fidelity.
- Add per-file diagnostics (`parse_warnings`, `skipped_reason`).
- Add branch diff lineage (`base` vs `head`) for change impact analysis.
