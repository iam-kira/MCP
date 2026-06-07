# Personal MCP Servers Monorepo

This repository hosts four independently runnable MCP servers, each focused on a narrow integration domain. The goal is to keep every server small, composable, and easy to evolve without coupling runtime state across domains.

## Server matrix

| Server | Domain | Default Port | Primary Data Source |
| --- | --- | ---: | --- |
| `github-lineage-server` | SQL lineage discovery | `8101` | GitHub REST API + repository SQL files |
| `jira-server` | Issue search/inspection | `8102` | Jira REST API |
| `python-etl-server` | In-memory ETL pipelines | `8103` | CSV/JSON files + pandas |
| `tmc-talend-server` | Talend runtime visibility | `8104` | Talend API / TMC endpoints |

## Monorepo layout

```text
.
├── github-lineage-server/
│   ├── app/server.py
│   ├── .env.example
│   ├── requirements.txt
│   ├── README.md
│   └── ARCHITECTURE.md
├── jira-server/
├── python-etl-server/
├── tmc-talend-server/
├── README.md
└── ARCHITECTURE.md
```

## Runtime model

- Each folder starts its own `FastMCP` instance and exposes tools over `streamable-http`.
- Each server has its own environment configuration boundary (`.env` file local to that folder).
- No shared persistence layer is required; this keeps local setup friction low.
- Servers are intentionally stateless except `python-etl-server`, which keeps process-local DataFrame state.

## Prerequisites

- Python 3.10+
- Network access to the corresponding external APIs where relevant
- Valid access tokens/credentials in each server's `.env`

## Quick start

Run servers independently (recommended for development and debugging):

```bash
cd github-lineage-server
pip install -r requirements.txt
python app/server.py
```

```bash
cd jira-server
pip install -r requirements.txt
python app/server.py
```

```bash
cd python-etl-server
pip install -r requirements.txt
python app/server.py
```

```bash
cd tmc-talend-server
pip install -r requirements.txt
python app/server.py
```

## Configuration strategy

- Keep `.env.example` as the source of truth for required keys.
- Copy `.env.example` to `.env` per folder.
- Never commit real secrets.
- Use least-privilege tokens (read-only where possible).

## API and tool design principles

- **Small tool surface**: each server exports a focused set of MCP tools.
- **Structured output**: every tool returns JSON-serializable dictionaries/lists.
- **Bounded pagination/limits**: user-facing `limit`/`max_results` arguments are clamped.
- **Graceful failure**: API/network errors are surfaced in a debuggable payload.

## Validation checklist

- Start each server and call its health tool:
  - GitHub: `github_health`
  - Jira: `jira_health`
  - Talend: `tmc_health`
- For ETL, run an end-to-end smoke flow: `extract_*` → `transform` → `load_to_csv`.
- Confirm ports `8101`–`8104` are reachable from your MCP client.

## Extension roadmap

- Add auth abstraction modules per server for token rotation.
- Introduce per-server structured logging and request IDs.
- Add contract tests for tool payload schema stability.
- Add optional containerization for single-command startup.

## Notes

- Keep each server independently deployable and versionable.
- Prefer backward-compatible tool argument changes to avoid client breakage.
