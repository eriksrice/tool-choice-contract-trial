from __future__ import annotations

from pathlib import Path

import pytest

from tool_choice_contract_trial.errors import SchemaDriftError
from tool_choice_contract_trial.schema import check_schema_drift, generate_schemas

ROOT = Path(__file__).resolve().parents[1]
COMMITTED_SCHEMAS = ROOT / "schemas" / "v1"


def test_committed_schemas_have_no_drift() -> None:
    check_schema_drift(COMMITTED_SCHEMAS)


def test_schema_generation_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_schemas(first)
    generate_schemas(second)
    assert {path.name: path.read_bytes() for path in first.glob("*.schema.json")} == {
        path.name: path.read_bytes() for path in second.glob("*.schema.json")
    }


def test_changed_schema_is_rejected(tmp_path: Path) -> None:
    generate_schemas(tmp_path)
    target = tmp_path / "policy_view.schema.json"
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(SchemaDriftError, match=r"changed policy_view\.schema\.json"):
        check_schema_drift(tmp_path)
