"""Strict loading for policy-visible and evaluator-only v2 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .errors import ArtifactIntegrityError, SchemaInvalidError
from .serialization import read_jsonl_objects
from .v2_models import (
    OracleExpectationV2,
    OracleReviewRecordV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
)


def _load_v2_artifacts[V2Artifact: BaseModel](
    path: Path,
    model: type[V2Artifact],
) -> tuple[V2Artifact, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    artifacts: list[V2Artifact] = []
    for line_number, value in objects:
        try:
            artifacts.append(model.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    return tuple(artifacts)


def _require_unique_scenario_ids(artifacts: tuple[BaseModel, ...], artifact_name: str) -> None:
    scenario_ids = [str(artifact.scenario_id) for artifact in artifacts]  # type: ignore[attr-defined]
    duplicates = sorted(
        scenario_id for scenario_id in set(scenario_ids) if scenario_ids.count(scenario_id) > 1
    )
    if duplicates:
        raise ArtifactIntegrityError(f"duplicate {artifact_name} scenario_id values: {duplicates}")


def load_policy_views_v2(path: Path) -> tuple[PolicyViewV2, ...]:
    views = _load_v2_artifacts(path, PolicyViewV2)
    _require_unique_scenario_ids(views, "v2 policy view")
    return views


def load_oracle_expectations_v2(path: Path) -> tuple[OracleExpectationV2, ...]:
    expectations = _load_v2_artifacts(path, OracleExpectationV2)
    _require_unique_scenario_ids(expectations, "v2 oracle expectation")
    return expectations


def load_oracle_reviews_v2(path: Path) -> tuple[OracleReviewRecordV2, ...]:
    reviews = _load_v2_artifacts(path, OracleReviewRecordV2)
    _require_unique_scenario_ids(reviews, "v2 oracle review")
    return reviews


def load_oracle_validation_findings_v2(path: Path) -> tuple[OracleValidationFindingV2, ...]:
    """Load internally coherent findings; source verification remains required for trust."""

    findings = _load_v2_artifacts(path, OracleValidationFindingV2)
    _require_unique_scenario_ids(findings, "v2 oracle validation finding")
    return findings


def load_provisional_manifest_v2(path: Path) -> ProvisionalBundleManifestV2:
    """Load schema-valid manifest data; source verification is a separate required step."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("manifest must contain one JSON object")
        return ProvisionalBundleManifestV2.model_validate(value)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error
