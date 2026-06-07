from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP


load_dotenv()

mcp = FastMCP("TMC Talend MCP")

TMC_BASE_URL = os.getenv("TMC_BASE_URL", "").rstrip("/")
TMC_TOKEN = os.getenv("TMC_TOKEN", "")
TMC_WORKSPACE_ID = os.getenv("TMC_WORKSPACE_ID", "")
TMC_PROJECT_ID = os.getenv("TMC_PROJECT_ID", "")


def _headers() -> dict[str, str]:
    if not TMC_TOKEN:
        raise ValueError("TMC_TOKEN is not configured")
    return {
        "Authorization": f"Bearer {TMC_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, params: dict[str, Any] | None = None) -> Any:
    if not TMC_BASE_URL:
        raise ValueError("TMC_BASE_URL is not configured")
    url = f"{TMC_BASE_URL}{path}"
    response = requests.request(
        method=method,
        url=url,
        headers=_headers(),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    if not response.text.strip():
        return {}
    return response.json()


@mcp.tool()
def tmc_health() -> dict[str, Any]:
    """Checks Talend API connectivity using available workspace endpoint."""
    try:
        data = _request("GET", "/tmc/v2.6/workspaces")
        workspaces = data.get("items", data if isinstance(data, list) else [])
        return {
            "ok": True,
            "base_url": TMC_BASE_URL,
            "workspace_count": len(workspaces),
        }
    except Exception as error:
        return {"ok": False, "base_url": TMC_BASE_URL, "error": str(error)}


@mcp.tool()
def list_workspaces(limit: int = 50) -> dict[str, Any]:
    """Lists available TMC workspaces."""
    data = _request(
        "GET", "/tmc/v2.6/workspaces", params={"limit": max(1, min(limit, 200))}
    )
    values = data.get("items", data if isinstance(data, list) else [])
    items = [
        {
            "id": value.get("id"),
            "name": value.get("name"),
            "description": value.get("description"),
        }
        for value in values
    ]
    return {"count": len(items), "workspaces": items}


@mcp.tool()
def list_tasks(workspace_id: str = "", limit: int = 50) -> dict[str, Any]:
    """Lists tasks in a workspace."""
    current_workspace = workspace_id or TMC_WORKSPACE_ID
    if not current_workspace:
        raise ValueError(
            "workspace_id not provided and TMC_WORKSPACE_ID not configured"
        )

    data = _request(
        "GET",
        f"/tmc/v2.6/executables/tasks",
        params={"workspaceId": current_workspace, "limit": max(1, min(limit, 200))},
    )
    values = data.get("items", data if isinstance(data, list) else [])
    tasks = [
        {
            "id": value.get("id"),
            "name": value.get("name"),
            "status": value.get("status"),
            "workspace_id": current_workspace,
        }
        for value in values
    ]
    return {"count": len(tasks), "tasks": tasks}


@mcp.tool()
def list_task_runs(task_id: str, limit: int = 20) -> dict[str, Any]:
    """Lists recent runs for a specific task."""
    data = _request(
        "GET",
        f"/tmc/v2.6/executions/task-executions",
        params={"taskId": task_id, "limit": max(1, min(limit, 100))},
    )
    values = data.get("items", data if isinstance(data, list) else [])
    runs = [
        {
            "id": value.get("id"),
            "task_id": task_id,
            "status": value.get("status"),
            "start_time": value.get("startDate"),
            "end_time": value.get("endDate"),
        }
        for value in values
    ]
    return {"count": len(runs), "runs": runs}


@mcp.tool()
def get_project_summary(project_id: str = "") -> dict[str, Any]:
    """Returns lightweight project metadata if project id is available."""
    current_project = project_id or TMC_PROJECT_ID
    if not current_project:
        raise ValueError("project_id not provided and TMC_PROJECT_ID not configured")
    data = _request("GET", f"/tmc/v2.6/projects/{current_project}")
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "description": data.get("description"),
        "workspace_id": (
            data.get("workspace", {}).get("id")
            if isinstance(data.get("workspace"), dict)
            else None
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8104)
