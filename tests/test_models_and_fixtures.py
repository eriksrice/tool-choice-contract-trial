from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tool_choice_contract_trial.errors import SchemaInvalidError
from tool_choice_contract_trial.evaluation import evaluate_case
from tool_choice_contract_trial.models import (
    ClauseWitness,
    CrossEvaluationFinding,
    EvaluationContext,
    EvaluationResult,
    OracleRecord,
    PolicyView,
    ScenarioMetadata,
    TaskContract,
    ToolDecision,
    ToolManifest,
)
from tool_choice_contract_trial.policy_io import load_policy_views


@pytest.mark.parametrize(
    "model",
    (
        TaskContract,
        ToolManifest,
        PolicyView,
        ScenarioMetadata,
        EvaluationContext,
        ToolDecision,
        OracleRecord,
        ClauseWitness,
        EvaluationResult,
        CrossEvaluationFinding,
    ),
)
def test_each_authoritative_artifact_rejects_an_empty_object(
    model: type[object],
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({})  # type: ignore[attr-defined]


def test_all_fixture_and_result_models_round_trip(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    assert (
        len(policy_views)
        == len(scenario_metadata)
        == len(oracle_records)
        == len(replay_decisions)
        == 4
    )
    for scenario_id, view in policy_views.items():
        PolicyView.model_validate_json(view.model_dump_json())
        OracleRecord.model_validate_json(oracle_records[scenario_id].model_dump_json())
        ToolDecision.model_validate_json(replay_decisions[scenario_id].model_dump_json())
        result = evaluate_case(
            view,
            scenario_metadata[scenario_id],
            oracle_records[scenario_id],
            replay_decisions[scenario_id],
        )
        EvaluationResult.model_validate_json(result.model_dump_json())


def test_stored_policy_view_loader_labels_structural_errors_schema_invalid(
    tmp_path: Path,
) -> None:
    invalid_path = tmp_path / "invalid.jsonl"
    invalid_path.write_text(json.dumps({"scenario_id": "missing_required_fields"}) + "\n")
    with pytest.raises(SchemaInvalidError, match="SCHEMA_INVALID"):
        load_policy_views(invalid_path)


def test_schema_v1_rejects_untyped_tie_break_rule(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = policy_views["scenario_004"].contract.model_dump(mode="json")
    payload["tie_break_rule"] = "pick the first tool"
    with pytest.raises(ValidationError, match="tie_break_rule"):
        TaskContract.model_validate(payload)
