"""Evaluator-only metadata loading, isolated from the policy adapter path."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .errors import ArtifactIntegrityError, SchemaInvalidError
from .models import ScenarioMetadata
from .serialization import read_jsonl_objects


def load_scenario_metadata(path: Path) -> tuple[ScenarioMetadata, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    records: list[ScenarioMetadata] = []
    for line_number, value in objects:
        try:
            records.append(ScenarioMetadata.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error

    scenario_ids = [record.scenario_id for record in records]
    duplicates = sorted(
        scenario_id for scenario_id in set(scenario_ids) if scenario_ids.count(scenario_id) > 1
    )
    if duplicates:
        raise ArtifactIntegrityError(
            f"duplicate scenario metadata scenario_id values: {duplicates}"
        )
    return tuple(records)
