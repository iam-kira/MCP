from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP


load_dotenv()

mcp = FastMCP("Jira MCP Server")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PAT = os.getenv("JIRA_PAT", "")
JIRA_API_VERSION = os.getenv("JIRA_API_VERSION", "3")


def _auth() -> tuple[str, str] | None:
    if JIRA_EMAIL and JIRA_API_TOKEN:
        return JIRA_EMAIL, JIRA_API_TOKEN
    return None


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if JIRA_PAT:
        headers["Authorization"] = f"Bearer {JIRA_PAT}"
    return headers


def _request(method: str, path: str, params: dict[str, Any] | None = None) -> Any:
    if not JIRA_BASE_URL:
        raise ValueError("JIRA_BASE_URL is not configured")

    url = f"{JIRA_BASE_URL}{path}"
    auth = _auth()
    response = requests.request(
        method=method,
        url=url,
        headers=_headers(),
        params=params,
        auth=auth,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def jira_health() -> dict[str, Any]:
    """Checks Jira API connectivity."""
    try:
        data = _request("GET", f"/rest/api/{JIRA_API_VERSION}/myself")
        return {
            "ok": True,
            "base_url": JIRA_BASE_URL,
            "display_name": data.get("displayName"),
            "account_id": data.get("accountId") or data.get("name"),
        }
    except Exception as error:
        return {"ok": False, "base_url": JIRA_BASE_URL, "error": str(error)}


@mcp.tool()
def search_issues(jql: str, max_results: int = 50) -> dict[str, Any]:
    """Searches Jira issues by JQL."""
    data = _request(
        "GET",
        f"/rest/api/{JIRA_API_VERSION}/search",
        params={
            "jql": jql,
            "maxResults": max(1, min(max_results, 200)),
            "fields": "summary,status,assignee,reporter,issuetype,priority,updated,created",
        },
    )

    issues = []
    for item in data.get("issues", []):
        fields = item.get("fields", {})
        issues.append(
            {
                "key": item.get("key"),
                "summary": fields.get("summary"),
                "status": (fields.get("status") or {}).get("name"),
                "assignee": ((fields.get("assignee") or {}).get("displayName")),
                "priority": ((fields.get("priority") or {}).get("name")),
                "issue_type": ((fields.get("issuetype") or {}).get("name")),
                "updated": fields.get("updated"),
            }
        )

    return {
        "jql": jql,
        "count": len(issues),
        "total": data.get("total", len(issues)),
        "issues": issues,
    }


@mcp.tool()
def get_issue(issue_key: str) -> dict[str, Any]:
    """Fetches a single Jira issue with comments."""
    data = _request(
        "GET",
        f"/rest/api/{JIRA_API_VERSION}/issue/{issue_key}",
        params={"expand": "renderedFields", "fields": "*all"},
    )
    fields = data.get("fields", {})
    comments = ((fields.get("comment") or {}).get("comments")) or []
    return {
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "status": (fields.get("status") or {}).get("name"),
        "assignee": ((fields.get("assignee") or {}).get("displayName")),
        "reporter": ((fields.get("reporter") or {}).get("displayName")),
        "labels": fields.get("labels") or [],
        "comment_count": len(comments),
        "comments": [
            {
                "author": ((comment.get("author") or {}).get("displayName")),
                "created": comment.get("created"),
                "body": comment.get("body"),
            }
            for comment in comments
        ],
    }


@mcp.tool()
def list_projects(limit: int = 100) -> dict[str, Any]:
    """Lists Jira projects."""
    data = _request(
        "GET",
        f"/rest/api/{JIRA_API_VERSION}/project/search",
        params={"maxResults": max(1, min(limit, 200))},
    )
    values = data.get("values", []) if isinstance(data, dict) else data
    projects = [
        {
            "id": value.get("id"),
            "key": value.get("key"),
            "name": value.get("name"),
            "project_type": value.get("projectTypeKey"),
        }
        for value in values
    ]
    return {"count": len(projects), "projects": projects}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8102)
