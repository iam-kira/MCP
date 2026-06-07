# TMC Talend MCP Server

This server offers a focused Talend API integration layer to inspect workspace/task/run metadata and project-level details from Talend Management Console (TMC).

## Current tool surface

| Tool | Purpose | Key Inputs | Output Shape |
| --- | --- | --- | --- |
| `tmc_health` | Validate API connectivity | none | `{ ok, base_url, workspace_count }` |
| `list_workspaces` | Enumerate workspaces | `limit` | `{ count, workspaces[] }` |
| `list_tasks` | Enumerate executable tasks | `workspace_id, limit` | `{ count, tasks[] }` |
| `list_task_runs` | List task execution history | `task_id, limit` | `{ count, runs[] }` |
| `get_project_summary` | Fetch project metadata | `project_id` | `{ id, name, description, workspace_id }` |

## API integration behavior

- Base path currently targets `v2.6` endpoints.
- Authentication uses bearer token (`Authorization: Bearer ...`).
- Empty HTTP response bodies are normalized to `{}`.
- `limit` values are clamped to safe bounded ranges.

## Configuration

Copy `.env.example` to `.env` and populate:

| Variable | Required | Description |
| --- | --- | --- |
| `TMC_BASE_URL` | Yes | Base URL for Talend API host |
| `TMC_TOKEN` | Yes | Bearer access token |
| `TMC_WORKSPACE_ID` | Optional | Default workspace fallback for task queries |
| `TMC_PROJECT_ID` | Optional | Default project fallback |

If `workspace_id` / `project_id` are omitted in tool calls, defaults are resolved from environment.

## Setup and run

```bash
pip install -r requirements.txt
python app/server.py
```

Server listens on port `8104`.

## Recommended call sequence

1. `tmc_health` to verify token and base URL.
2. `list_workspaces` to identify target workspace.
3. `list_tasks(workspace_id=...)` for operational inventory.
4. `list_task_runs(task_id=...)` to inspect runtime behavior.
5. `get_project_summary(project_id=...)` for project metadata context.

## Error handling model

- Missing `TMC_BASE_URL` or `TMC_TOKEN` raises explicit configuration errors.
- Upstream API failures propagate as request exceptions with status context.
- Invalid IDs return endpoint-specific error responses from Talend API.

## Extension points

- Add create/update operations for task orchestration.
- Add run-level log and metrics retrieval.
- Add normalized status taxonomy across Talend execution states.
