"""Canonical serialization shared by all deterministic artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def canonical_data(value: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-compatible data without changing model field semantics."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return dict(value)


def canonical_json(value: BaseModel | Mapping[str, Any]) -> str:
    """Serialize with the project's fixed UTF-8 JSON representation."""

    return json.dumps(
        canonical_data(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_json_bytes(value: BaseModel | Mapping[str, Any]) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonical_hash(value: BaseModel | Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def write_jsonl(path: Path, records: Iterable[BaseModel]) -> None:
    """Write canonical JSONL with exactly one newline after every record."""

    payload = "".join(f"{canonical_json(record)}\n" for record in records)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def read_jsonl_objects(path: Path) -> list[tuple[int, dict[str, Any]]]:
    """Parse JSONL objects while retaining line numbers for structural errors."""

    objects: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8", newline="") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} must contain a JSON object")
            objects.append((line_number, value))
    return objects
