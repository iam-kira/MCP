from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import Any

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP


load_dotenv()

mcp = FastMCP("GitHub Data Lineage")

GITHUB_BASE_URL = os.getenv("GITHUB_BASE_URL", "https://api.github.com").rstrip("/")
GITHUB_API_VERSION = os.getenv("GITHUB_API_VERSION", "2022-11-28")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DEFAULT_OWNER = os.getenv("DEFAULT_OWNER", "")
DEFAULT_REPO = os.getenv("DEFAULT_REPO", "")
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")

TABLE_PATTERN = re.compile(
    r"(?:from|join|into|update|table)\s+([a-zA-Z_][a-zA-Z0-9_\.]{1,120})",
    re.IGNORECASE,
)


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _repo(owner: str | None, repo: str | None) -> tuple[str, str]:
    resolved_owner = owner or DEFAULT_OWNER
    resolved_repo = repo or DEFAULT_REPO
    if not resolved_owner or not resolved_repo:
        raise ValueError("owner/repo not provided and no defaults configured")
    return resolved_owner, resolved_repo


def _request(method: str, url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.request(
        method=method,
        url=url,
        headers=_headers(),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _extract_edges(sql_text: str, source_name: str) -> list[dict[str, str]]:
    tables = TABLE_PATTERN.findall(sql_text or "")
    normalized = [table.strip().strip("`").strip('"') for table in tables if table]
    unique_tables = []
    seen = set()
    for table in normalized:
        lower = table.lower()
        if lower not in seen:
            seen.add(lower)
            unique_tables.append(table)

    if len(unique_tables) < 2:
        return []

    target = unique_tables[0]
    edges = []
    for source in unique_tables[1:]:
        edges.append(
            {
                "source": source,
                "target": target,
                "relation": "depends_on",
                "file": source_name,
            }
        )
    return edges


@mcp.tool()
def github_health() -> dict[str, Any]:
    """Checks GitHub API connectivity with current token/config."""
    try:
        data = _request("GET", f"{GITHUB_BASE_URL}/user")
        return {
            "ok": True,
            "authenticated": True,
            "login": data.get("login"),
            "base_url": GITHUB_BASE_URL,
        }
    except requests.HTTPError as error:
        return {
            "ok": False,
            "authenticated": False,
            "error": str(error),
            "base_url": GITHUB_BASE_URL,
        }


@mcp.tool()
def search_sql_files(
    query: str,
    owner: str = "",
    repo: str = "",
    branch: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Searches SQL files in a repository using GitHub code search."""
    repo_owner, repo_name = _repo(owner, repo)
    ref = branch or DEFAULT_BRANCH
    final_query = f"{query} repo:{repo_owner}/{repo_name} extension:sql"

    data = _request(
        "GET",
        f"{GITHUB_BASE_URL}/search/code",
        params={"q": final_query, "per_page": max(1, min(limit, 100))},
    )

    items = []
    for item in data.get("items", []):
        items.append(
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "sha": item.get("sha"),
                "html_url": item.get("html_url"),
                "repository": item.get("repository", {}).get("full_name"),
                "branch": ref,
            }
        )

    return {
        "query": query,
        "repo": f"{repo_owner}/{repo_name}",
        "count": len(items),
        "items": items,
    }


@mcp.tool()
def get_file_text(
    path: str,
    owner: str = "",
    repo: str = "",
    branch: str = "",
) -> dict[str, Any]:
    """Returns decoded file text from a GitHub repository."""
    import base64

    repo_owner, repo_name = _repo(owner, repo)
    ref = branch or DEFAULT_BRANCH

    data = _request(
        "GET",
        f"{GITHUB_BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{path}",
        params={"ref": ref},
    )

    encoded = data.get("content", "")
    decoded = base64.b64decode(encoded).decode("utf-8", errors="replace")
    return {
        "path": path,
        "repo": f"{repo_owner}/{repo_name}",
        "branch": ref,
        "size": len(decoded),
        "text": decoded,
    }


@mcp.tool()
def build_sql_lineage_snapshot(
    owner: str = "",
    repo: str = "",
    branch: str = "",
    max_files: int = 30,
) -> dict[str, Any]:
    """Builds a simple table lineage graph from SQL files in a repository."""
    repo_owner, repo_name = _repo(owner, repo)
    ref = branch or DEFAULT_BRANCH

    tree = _request(
        "GET",
        f"{GITHUB_BASE_URL}/repos/{repo_owner}/{repo_name}/git/trees/{ref}",
        params={"recursive": 1},
    )
    sql_files = [
        node.get("path")
        for node in tree.get("tree", [])
        if node.get("type") == "blob" and str(node.get("path", "")).endswith(".sql")
    ]

    edges: list[dict[str, str]] = []
    per_file_edges: dict[str, int] = defaultdict(int)

    for path in sql_files[: max(1, min(max_files, 200))]:
        try:
            file_payload = get_file_text(
                path=path, owner=repo_owner, repo=repo_name, branch=ref
            )
            extracted = _extract_edges(file_payload.get("text", ""), path)
            edges.extend(extracted)
            per_file_edges[path] = len(extracted)
        except Exception:
            per_file_edges[path] = 0

    nodes = sorted(
        {edge["source"] for edge in edges} | {edge["target"] for edge in edges}
    )

    return {
        "repo": f"{repo_owner}/{repo_name}",
        "branch": ref,
        "scanned_sql_files": min(len(sql_files), max(1, min(max_files, 200))),
        "nodes": nodes,
        "edges": edges,
        "edge_count_by_file": dict(per_file_edges),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8101)
