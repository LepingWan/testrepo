#!/usr/bin/env python3
"""Static checks for the Panini Colab notebook.

This intentionally avoids importing the project package or running expensive
model/data cells. It checks notebook JSON, code-cell syntax, saved-output
presence, stage-label consistency, and the STATUS helper's ability to run
before setup cells initialize notebook globals.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
from pathlib import Path


NOTEBOOK = Path(__file__).resolve().parents[1] / "Panini_Course_Project.ipynb"

EXPECTED_LABELS = [
    "STATUS: Run Context Helper",
    "FOUNDATION 1: Run Controls",
    "FOUNDATION 2: Colab/Repo Setup And Paths",
    "FOUNDATION 3: Shared Checkpoint Helpers",
    "FOUNDATION 4: Imports And CoursePackage Loading",
    "Q1: Package Audit",
    "Q2: GSW Graph Construction And Reconciliation",
    "Q3: Network Analysis And Plots",
    "Q4A: Parser And Dependency Validation",
    "Q4B / STAGE A: GPU Decomposition Run",
    "Q5: Sparse Retrieval Baselines",
    "Q6: Dense, Hybrid, And Dual Retrieval",
    "Q7: Reranker Helpers And Scoring",
    "Q8A: RICR Tests And Toy Trace",
    "Q8B / STAGE B: GPU Rerank + RICR Run",
    "Q9: Controlled RICR Ablations",
    "Q10A: Answer Formatting And GPU Answer Run",
    "Q10C: 2Wiki Scoring Tables And Trace Selection",
    "Q11: MuSiQue Transfer And Scaling",
    "Q12A: Submission Materialization And Validation",
    "Q12B: Environment And RUNME",
]


def load_notebook() -> dict:
    try:
        return json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssertionError(f"Notebook is not valid JSON: {error}") from error


def code_cells(nb: dict) -> list[tuple[int, dict]]:
    return [
        (index, cell)
        for index, cell in enumerate(nb.get("cells", []))
        if cell.get("cell_type") == "code"
    ]


def cell_source(cell: dict) -> str:
    return "".join(cell.get("source", []))


def check_code_syntax(nb: dict) -> None:
    errors = []
    for index, cell in code_cells(nb):
        try:
            ast.parse(cell_source(cell))
        except SyntaxError as error:
            errors.append(f"cell {index}:{error.lineno}: {error.msg}")
    assert not errors, "Code-cell syntax errors:\n" + "\n".join(errors)


def check_labels(nb: dict) -> None:
    all_code = "\n".join(cell_source(cell) for _, cell in code_cells(nb))
    missing = [label for label in EXPECTED_LABELS if label not in all_code]
    assert not missing, "Missing expected run-map labels: " + ", ".join(missing)


def check_status_helper_runs_before_setup(nb: dict) -> None:
    status_cells = [
        cell_source(cell)
        for _, cell in code_cells(nb)
        if "STATUS: Run Context Helper" in cell_source(cell)
    ]
    assert len(status_cells) == 1, f"Expected one STATUS helper, found {len(status_cells)}"

    namespace: dict[str, object] = {}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(status_cells[0], "STATUS helper", "exec"), namespace)
    except Exception as error:
        raise AssertionError(
            "STATUS helper must run before setup/import cells initialize globals; "
            f"got {type(error).__name__}: {error}"
        ) from error


def check_outputs_preserved(nb: dict) -> None:
    output_count = sum(len(cell.get("outputs", [])) for _, cell in code_cells(nb))
    assert output_count > 0, "Notebook has no saved outputs; did a cleanup script clear them?"


def main() -> None:
    nb = load_notebook()
    check_code_syntax(nb)
    check_labels(nb)
    check_status_helper_runs_before_setup(nb)
    check_outputs_preserved(nb)
    output_count = sum(len(cell.get("outputs", [])) for _, cell in code_cells(nb))
    print(f"Static notebook check passed: {len(nb.get('cells', []))} cells, {output_count} outputs.")


if __name__ == "__main__":
    main()
