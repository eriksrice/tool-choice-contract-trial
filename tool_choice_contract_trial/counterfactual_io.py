"""Evaluator-only loading for counterfactual specifications and findings."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .counterfactual_registry import validate_counterfactual_finding_integrity
from .errors import ArtifactIntegrityError, SchemaInvalidError
from .models import CounterfactualComparisonSpec, CounterfactualFinding
from .serialization import read_jsonl_objects


def _load_counterfactual_artifacts[CounterfactualArtifact: BaseModel](
    path: Path,
    model: type[CounterfactualArtifact],
) -> tuple[CounterfactualArtifact, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    artifacts: list[CounterfactualArtifact] = []
    for line_number, value in objects:
        try:
            artifacts.append(model.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    return tuple(artifacts)


def _require_unique_comparison_ids(
    artifacts: tuple[CounterfactualComparisonSpec, ...] | tuple[CounterfactualFinding, ...],
    artifact_name: str,
) -> None:
    comparison_ids = [artifact.comparison_id for artifact in artifacts]
    duplicates = sorted(
        comparison_id
        for comparison_id in set(comparison_ids)
        if comparison_ids.count(comparison_id) > 1
    )
    if duplicates:
        raise ArtifactIntegrityError(
            f"duplicate {artifact_name} comparison_id values: {duplicates}"
        )


def load_counterfactual_specs(path: Path) -> tuple[CounterfactualComparisonSpec, ...]:
    specs = _load_counterfactual_artifacts(path, CounterfactualComparisonSpec)
    _require_unique_comparison_ids(specs, "counterfactual comparison")
    return specs


def load_counterfactual_findings(path: Path) -> tuple[CounterfactualFinding, ...]:
    findings = _load_counterfactual_artifacts(path, CounterfactualFinding)
    for finding in findings:
        validate_counterfactual_finding_integrity(
            validation_status=finding.validation_status.value,
            declared_clause_ids=finding.declared_changed_clause_ids,
            observed_contract_paths=finding.observed_changed_contract_paths,
            ownership_hash=finding.clause_ownership_hash,
        )
    _require_unique_comparison_ids(findings, "counterfactual finding")
    return findings
