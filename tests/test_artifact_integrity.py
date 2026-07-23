from __future__ import annotations

import json
from pathlib import Path

import pytest

from tool_choice_contract_trial.errors import ArtifactIntegrityError
from tool_choice_contract_trial.evaluation import evaluate_case
from tool_choice_contract_trial.evaluation_io import load_scenario_metadata
from tool_choice_contract_trial.models import (
    OracleRecord,
    PolicyView,
    ScenarioMetadata,
    ToolDecision,
)
from tool_choice_contract_trial.oracle_io import load_oracle_records
from tool_choice_contract_trial.policy_io import load_policy_views, load_replay_decisions

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "milestone_1" / "authority_profiles"


def _duplicate_first_row(source: Path, destination: Path) -> None:
    rows = source.read_text().splitlines()
    destination.write_text("\n".join([*rows, rows[0]]) + "\n")


@pytest.mark.parametrize(
    ("filename", "loader", "message"),
    (
        ("scenarios.jsonl", load_policy_views, "duplicate policy view"),
        ("oracles.jsonl", load_oracle_records, "duplicate oracle record"),
        ("replay_decisions.jsonl", load_replay_decisions, "duplicate replay decision"),
        (
            "evaluation_metadata.jsonl",
            load_scenario_metadata,
            "duplicate scenario metadata",
        ),
    ),
)
def test_duplicate_scenario_rows_fail_loudly(
    filename: str,
    loader: object,
    message: str,
    tmp_path: Path,
) -> None:
    duplicate_path = tmp_path / filename
    _duplicate_first_row(FIXTURES / filename, duplicate_path)
    with pytest.raises(ArtifactIntegrityError, match=message):
        loader(duplicate_path)  # type: ignore[operator]


def test_mixed_policy_ids_are_rejected(tmp_path: Path) -> None:
    rows = [
        json.loads(line) for line in (FIXTURES / "replay_decisions.jsonl").read_text().splitlines()
    ]
    rows[1]["policy_id"] = "another_policy"
    mixed_path = tmp_path / "mixed.jsonl"
    mixed_path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    )
    with pytest.raises(ArtifactIntegrityError, match="exactly one policy_id"):
        load_replay_decisions(mixed_path)


def test_mismatched_oracle_is_rejected_before_scoring(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    with pytest.raises(ArtifactIntegrityError, match="oracle scenario_id"):
        evaluate_case(
            policy_views["scenario_001"],
            scenario_metadata["scenario_001"],
            oracle_records["scenario_002"],
            replay_decisions["scenario_001"],
        )
