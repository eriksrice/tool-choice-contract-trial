"""Strict loading and canonical writing for blind model-review evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .blind_model_review_models import (
    BlindModelReviewComparisonV2,
    BlindModelReviewProvenanceManifestV2,
    BlindModelReviewRecordV2,
    BlindModelReviewResponseV2,
    BlindPacketCaseV2,
    BlindPrivateCaseMapV2,
    BlindPrivateSourceManifestV2,
)
from .errors import ArtifactIntegrityError, SchemaInvalidError
from .serialization import canonical_json, read_jsonl_objects


def _load_jsonl[Artifact: BaseModel](path: Path, model: type[Artifact]) -> tuple[Artifact, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error

    rows: list[Artifact] = []
    for line_number, value in objects:
        try:
            rows.append(model.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    return tuple(rows)


def _load_json[Artifact: BaseModel](path: Path, model: type[Artifact]) -> Artifact:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("artifact must contain one JSON object")
        return model.model_validate(value)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error


def _require_unique(rows: tuple[BaseModel, ...], field_name: str, artifact_name: str) -> None:
    values = [str(getattr(row, field_name)) for row in rows]
    duplicates = sorted(value for value in set(values) if values.count(value) > 1)
    if duplicates:
        raise ArtifactIntegrityError(f"duplicate {artifact_name} {field_name} values: {duplicates}")


def load_blind_model_review_responses_v2(
    path: Path,
) -> tuple[BlindModelReviewResponseV2, ...]:
    rows = _load_jsonl(path, BlindModelReviewResponseV2)
    _require_unique(rows, "blind_case_id", "blind model review response")
    return rows


def load_blind_packet_cases_v2(path: Path) -> tuple[BlindPacketCaseV2, ...]:
    try:
        text = path.read_text(encoding="utf-8")
        blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
        rows = tuple(BlindPacketCaseV2.model_validate(json.loads(block)) for block in blocks)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error
    if not rows:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: no blind case JSON blocks")
    _require_unique(rows, "blind_case_id", "blind packet case")
    return rows


def load_blind_private_case_map_v2(path: Path) -> BlindPrivateCaseMapV2:
    return _load_json(path, BlindPrivateCaseMapV2)


def load_blind_private_source_manifest_v2(path: Path) -> BlindPrivateSourceManifestV2:
    return _load_json(path, BlindPrivateSourceManifestV2)


def load_blind_model_review_records_v2(
    path: Path,
) -> tuple[BlindModelReviewRecordV2, ...]:
    rows = _load_jsonl(path, BlindModelReviewRecordV2)
    _require_unique(rows, "scenario_id", "canonical blind model review")
    _require_unique(rows, "blind_case_id", "canonical blind model review")
    return rows


def load_blind_model_review_comparisons_v2(
    path: Path,
) -> tuple[BlindModelReviewComparisonV2, ...]:
    rows = _load_jsonl(path, BlindModelReviewComparisonV2)
    _require_unique(rows, "scenario_id", "blind model review comparison")
    return rows


def load_blind_model_review_provenance_manifest_v2(
    path: Path,
) -> BlindModelReviewProvenanceManifestV2:
    return _load_json(path, BlindModelReviewProvenanceManifestV2)


def write_blind_model_review_provenance_manifest_v2(
    path: Path, manifest: BlindModelReviewProvenanceManifestV2
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(manifest) + "\n", encoding="utf-8", newline="\n")
