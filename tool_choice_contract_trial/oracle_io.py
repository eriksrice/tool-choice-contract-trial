"""Oracle-only fixture loading, intentionally isolated from policy loading."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .errors import ArtifactIntegrityError, SchemaInvalidError
from .models import OracleRecord
from .serialization import read_jsonl_objects


def load_oracle_records(path: Path) -> tuple[OracleRecord, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    records: list[OracleRecord] = []
    for line_number, value in objects:
        try:
            records.append(OracleRecord.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    scenario_ids = [record.scenario_id for record in records]
    duplicates = sorted(
        scenario_id for scenario_id in set(scenario_ids) if scenario_ids.count(scenario_id) > 1
    )
    if duplicates:
        raise ArtifactIntegrityError(f"duplicate oracle record scenario_id values: {duplicates}")
    return tuple(records)
