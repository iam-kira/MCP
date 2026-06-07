# GitHub Lineage Architecture

```mermaid
flowchart LR
    Client[MCP Client] --> Server[GitHub Lineage MCP Server]
    Server --> GH[GitHub REST API]
    Server --> Parser[SQL Pattern Parser]
    Parser --> Graph[Lineage Nodes and Edges]
    Graph --> Client
```

## Notes

- The lineage logic is intentionally simple and regex-based.
- Works best with SQL files that use clear `FROM`, `JOIN`, `INTO`, and `UPDATE` clauses.
- Designed to be extended later with parser-level lineage accuracy.
