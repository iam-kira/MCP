# Python ETL MCP Server

This server provides a minimal but practical ETL runtime over in-memory pandas DataFrames. It is designed for small personal workflows, rapid prototyping, and file-based transformations.

## Processing model

- Data is stored in a process-local dictionary: `dataset_name -> DataFrame`.
- Transform tools read one dataset and materialize a new output dataset.
- State is ephemeral and resets when the server process restarts.

## Tool contracts

| Tool | Pipeline Stage | Inputs | Output |
| --- | --- | --- | --- |
| `extract_csv` | Extract | `path, dataset_name, delimiter` | dataset registration metadata |
| `extract_json` | Extract | `path, dataset_name, lines` | dataset registration metadata |
| `select_columns` | Transform | `input_dataset, output_dataset, columns[]` | output dataset metadata |
| `filter_rows` | Transform | `input_dataset, output_dataset, column, operator, value` | output dataset metadata |
| `aggregate_sum` | Transform | `input_dataset, output_dataset, group_by[], value_column` | grouped output metadata |
| `load_to_csv` | Load | `input_dataset, output_path` | persisted rows/path |
| `preview` | Inspect | `input_dataset, rows` | first N records |
| `list_datasets` | Inspect | none | sorted dataset names |

## Supported filter operators

- `==`
- `!=`
- `>`
- `<`

Current implementation compares values directly as provided; type coercion behavior follows pandas semantics for the column dtype.

## Setup and run

```bash
pip install -r requirements.txt
python app/server.py
```

Server listens on port `8103`.

## End-to-end example flow

1. Extract: `extract_csv("input/orders.csv", "orders")`
2. Transform: `filter_rows("orders", "orders_open", "status", "==", "OPEN")`
3. Transform: `aggregate_sum("orders_open", "amount_by_customer", ["customer_id"], "amount")`
4. Load: `load_to_csv("amount_by_customer", "output/customer_totals.csv")`
5. Inspect: `preview("amount_by_customer", 10)`

## Reliability and safety notes

- Duplicate dataset names are rejected by extract tools.
- Missing dataset references fail fast with explicit validation errors.
- No automatic checkpointing is performed; persist important outputs with `load_to_csv`.

## Extension points

- Add `join_datasets` for multi-source pipelines.
- Add `cast_columns` and schema validation tools.
- Add `load_to_json`/database sinks for broader output targets.
