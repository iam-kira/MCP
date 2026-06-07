# Jira Server Architecture

```mermaid
flowchart LR
    Client[MCP Client] --> Server[Jira MCP Server]
    Server --> Jira[Jira REST API]
    Jira --> Server
    Server --> Client
```

## Notes

- Supports PAT (`JIRA_PAT`) or basic auth (`JIRA_EMAIL` + `JIRA_API_TOKEN`).
- Uses JQL for flexible ticket filtering.
- Keeps response payloads small and readable.
