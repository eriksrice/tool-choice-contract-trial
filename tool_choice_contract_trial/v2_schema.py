"""Deterministic JSON Schema projections for isolated v2 models."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .errors import SchemaDriftError
from .v2_models import (
    ClauseWitnessV2,
    OracleExpectationV2,
    OracleReviewRecordV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
    TaskContractV2,
    ToolManifestV2,
)

V2_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "clause_witness_v2.schema.json": ClauseWitnessV2,
    "oracle_expectation_v2.schema.json": OracleExpectationV2,
    "oracle_review_record_v2.schema.json": OracleReviewRecordV2,
    "oracle_validation_finding_v2.schema.json": OracleValidationFindingV2,
    "policy_view_v2.schema.json": PolicyViewV2,
    "provisional_bundle_manifest_v2.schema.json": ProvisionalBundleManifestV2,
    "task_contract_v2.schema.json": TaskContractV2,
    "tool_manifest_v2.schema.json": ToolManifestV2,
}


def generated_v2_schema_bytes() -> dict[str, bytes]:
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
        for filename, model in V2_SCHEMA_MODELS.items()
    }


def generate_v2_schemas(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, payload in generated_v2_schema_bytes().items():
        (directory / filename).write_bytes(payload)


def check_v2_schema_drift(directory: Path) -> None:
    expected = generated_v2_schema_bytes()
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
        raise SchemaDriftError("v2 schema drift: " + ", ".join(differences))
