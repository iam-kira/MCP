# Jira MCP Server

This server exposes a compact Jira integration surface for issue discovery, detail retrieval, and project enumeration through MCP tools.

## Integration model

- Transport: `streamable-http`
- API dependency: Jira REST API (`/rest/api/{version}`)
- Auth modes:
  - PAT via `JIRA_PAT` (Bearer)
  - Basic auth via `JIRA_EMAIL` + `JIRA_API_TOKEN`

## Tool contracts

| Tool | Purpose | Key Inputs | Output Shape |
| --- | --- | --- | --- |
| `jira_health` | Verify Jira auth/connectivity | none | `{ ok, base_url, display_name, account_id }` |
| `search_issues` | Execute JQL issue search | `jql, max_results` | `{ jql, count, total, issues[] }` |
| `get_issue` | Fetch one issue with comments | `issue_key` | `{ key, summary, status, assignee, comments[]... }` |
| `list_projects` | List available projects | `limit` | `{ count, projects[] }` |

## Returned issue shape (search)

`search_issues` returns a normalized subset optimized for dashboards and triage:

- `key`
- `summary`
- `status`
- `assignee`
- `priority`
- `issue_type`
- `updated`

Use `get_issue` for fuller context and comments.

## Configuration

Copy `.env.example` to `.env`:

| Variable | Required | Description |
| --- | --- | --- |
| `JIRA_BASE_URL` | Yes | Jira base URL (cloud or self-managed) |
| `JIRA_EMAIL` | Conditional | Required only for basic auth |
| `JIRA_API_TOKEN` | Conditional | Required only for basic auth |
| `JIRA_PAT` | Conditional | Alternative bearer token auth |
| `JIRA_API_VERSION` | Optional | Defaults to `3` |

Auth precedence in implementation:

1. If `JIRA_PAT` is set, bearer header is sent.
2. If `JIRA_EMAIL` + `JIRA_API_TOKEN` are set, basic auth is used.

## Setup and run

```bash
pip install -r requirements.txt
python app/server.py
```

Server listens on port `8102`.

## Query patterns

Example JQL patterns commonly used by clients:

- `project = ABC AND statusCategory != Done ORDER BY updated DESC`
- `assignee = currentUser() AND priority in (High, Highest)`
- `project = ABC AND labels = lineage`

## Failure semantics

- Invalid auth/base URL: surfaced by `jira_health` and tool-level request errors.
- Overly broad JQL with high cardinality: bounded by `max_results` clamping.
- Missing issue key: `get_issue` returns an upstream Jira HTTP error.

## Extension points

- Add pagination cursor handling (`startAt`) for full project exports.
- Add field selection controls to reduce payload size.
- Add derived analytics tools (SLA breach risk, cycle-time snapshots).
