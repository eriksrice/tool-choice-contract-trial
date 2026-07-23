"""Policy-visible fixture loading kept separate from oracle-only loading."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .errors import ArtifactIntegrityError, SchemaInvalidError
from .models import PolicyView, ToolDecision
from .serialization import read_jsonl_objects


def _load_policy_artifacts[PolicyArtifact: BaseModel](
    path: Path, model: type[PolicyArtifact]
) -> tuple[PolicyArtifact, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    artifacts: list[PolicyArtifact] = []
    for line_number, value in objects:
        try:
            artifacts.append(model.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    return tuple(artifacts)


def load_policy_views(path: Path) -> tuple[PolicyView, ...]:
    """Load the complete data surface a supported policy may receive."""

    views = _load_policy_artifacts(path, PolicyView)
    _require_unique_scenario_ids(views, "policy view")
    return views


def load_replay_decisions(path: Path) -> tuple[ToolDecision, ...]:
    decisions = _load_policy_artifacts(path, ToolDecision)
    _require_unique_scenario_ids(decisions, "replay decision")
    policy_ids = {decision.policy_id for decision in decisions}
    if len(policy_ids) != 1:
        raise ArtifactIntegrityError("Milestone 1 replay bundle must contain exactly one policy_id")
    return decisions


def _require_unique_scenario_ids(
    artifacts: tuple[PolicyView, ...] | tuple[ToolDecision, ...], artifact_name: str
) -> None:
    scenario_ids = [artifact.scenario_id for artifact in artifacts]
    duplicates = sorted(
        scenario_id for scenario_id in set(scenario_ids) if scenario_ids.count(scenario_id) > 1
    )
    if duplicates:
        raise ArtifactIntegrityError(f"duplicate {artifact_name} scenario_id values: {duplicates}")
