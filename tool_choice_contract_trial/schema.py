"""Deterministic JSON Schema projections of authoritative Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .errors import SchemaDriftError
from .models import (
    ClauseWitness,
    CounterfactualComparisonSpec,
    CounterfactualFinding,
    CrossEvaluationFinding,
    EvaluationContext,
    EvaluationResult,
    OracleRecord,
    PolicyView,
    ScenarioMetadata,
    TaskContract,
    ToolDecision,
    ToolManifest,
)

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "clause_witness.schema.json": ClauseWitness,
    "counterfactual_comparison_spec.schema.json": CounterfactualComparisonSpec,
    "counterfactual_finding.schema.json": CounterfactualFinding,
    "cross_evaluation_finding.schema.json": CrossEvaluationFinding,
    "evaluation_context.schema.json": EvaluationContext,
    "evaluation_result.schema.json": EvaluationResult,
    "oracle_record.schema.json": OracleRecord,
    "policy_view.schema.json": PolicyView,
    "scenario_metadata.schema.json": ScenarioMetadata,
    "task_contract.schema.json": TaskContract,
    "tool_decision.schema.json": ToolDecision,
    "tool_manifest.schema.json": ToolManifest,
}


def generated_schema_bytes() -> dict[str, bytes]:
    return {
        filename: (
            json.dumps(
                model.model_json_schema(mode="validation"),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        for filename, model in SCHEMA_MODELS.items()
    }


def generate_schemas(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, payload in generated_schema_bytes().items():
        (directory / filename).write_bytes(payload)


def check_schema_drift(directory: Path) -> None:
    expected = generated_schema_bytes()
    actual_names = {path.name for path in directory.glob("*.schema.json")}
    expected_names = set(expected)
    differences = [
        *(f"missing {name}" for name in sorted(expected_names - actual_names)),
        *(f"unexpected {name}" for name in sorted(actual_names - expected_names)),
    ]
    for filename, payload in expected.items():
        path = directory / filename
        if path.exists() and path.read_bytes() != payload:
            differences.append(f"changed {filename}")
    if differences:
        raise SchemaDriftError("schema drift: " + ", ".join(differences))
