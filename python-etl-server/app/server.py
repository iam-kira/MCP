from __future__ import annotations

from typing import Any

import pandas as pd
from fastmcp import FastMCP


mcp = FastMCP("Python ETL MCP")

DATASETS: dict[str, pd.DataFrame] = {}


def _require_dataset(name: str) -> pd.DataFrame:
    if name not in DATASETS:
        raise ValueError(f"dataset '{name}' not found")
    return DATASETS[name]


@mcp.tool()
def extract_csv(path: str, dataset_name: str, delimiter: str = ",") -> dict[str, Any]:
    """Extracts a dataset from a CSV file."""
    if dataset_name in DATASETS:
        raise ValueError(f"dataset '{dataset_name}' already exists")
    frame = pd.read_csv(path, sep=delimiter)
    DATASETS[dataset_name] = frame
    return {"dataset": dataset_name, "shape": frame.shape}


@mcp.tool()
def extract_json(path: str, dataset_name: str, lines: bool = False) -> dict[str, Any]:
    """Extracts a dataset from a JSON file."""
    if dataset_name in DATASETS:
        raise ValueError(f"dataset '{dataset_name}' already exists")
    frame = pd.read_json(path, lines=lines)
    DATASETS[dataset_name] = frame
    return {"dataset": dataset_name, "shape": frame.shape}


@mcp.tool()
def select_columns(
    input_dataset: str, output_dataset: str, columns: list[str]
) -> dict[str, Any]:
    """Transforms a dataset by selecting columns."""
    frame = _require_dataset(input_dataset)
    DATASETS[output_dataset] = frame[columns].copy()
    result = DATASETS[output_dataset]
    return {
        "dataset": output_dataset,
        "shape": result.shape,
        "columns": list(result.columns),
    }


@mcp.tool()
def filter_rows(
    input_dataset: str,
    output_dataset: str,
    column: str,
    operator: str,
    value: str,
) -> dict[str, Any]:
    """Filters rows using a simple comparison operator."""
    frame = _require_dataset(input_dataset)
    if column not in frame.columns:
        raise ValueError(f"column '{column}' not present in dataset")

    if operator == "==":
        filtered = frame[frame[column] == value]
    elif operator == "!=":
        filtered = frame[frame[column] != value]
    elif operator == ">":
        filtered = frame[frame[column] > value]
    elif operator == "<":
        filtered = frame[frame[column] < value]
    else:
        raise ValueError("unsupported operator. use one of: ==, !=, >, <")

    DATASETS[output_dataset] = filtered.copy()
    return {"dataset": output_dataset, "shape": DATASETS[output_dataset].shape}


@mcp.tool()
def aggregate_sum(
    input_dataset: str,
    output_dataset: str,
    group_by: list[str],
    value_column: str,
) -> dict[str, Any]:
    """Groups and sums a numeric column."""
    frame = _require_dataset(input_dataset)
    grouped = frame.groupby(group_by, dropna=False)[value_column].sum().reset_index()
    DATASETS[output_dataset] = grouped
    return {"dataset": output_dataset, "shape": grouped.shape}


@mcp.tool()
def load_to_csv(input_dataset: str, output_path: str) -> dict[str, Any]:
    """Loads a dataset to a CSV file."""
    frame = _require_dataset(input_dataset)
    frame.to_csv(output_path, index=False)
    return {"dataset": input_dataset, "rows": len(frame), "output_path": output_path}


@mcp.tool()
def preview(input_dataset: str, rows: int = 5) -> dict[str, Any]:
    """Returns the first few rows of a dataset."""
    frame = _require_dataset(input_dataset)
    return {
        "dataset": input_dataset,
        "rows": rows,
        "preview": frame.head(max(1, rows)).to_dict(orient="records"),
    }


@mcp.tool()
def list_datasets() -> list[str]:
    """Lists in-memory datasets."""
    return sorted(DATASETS.keys())


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8103)
