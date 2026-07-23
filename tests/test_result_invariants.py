from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from tool_choice_contract_trial.evaluation import evaluate_case
from tool_choice_contract_trial.models import (
    DecisionKind,
    EvaluationResult,
    EvaluationUnitStatus,
    FailureCode,
    OracleRecord,
    OracleState,
    PolicyOutputStatus,
    PolicyView,
    ReviewStatus,
    ScenarioMetadata,
    SelectedToolAdmissibility,
    StrictContractOutcome,
    ToolDecision,
    WitnessScope,
)


def _evaluate(
    scenario_id: str,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    decision: ToolDecision | None,
) -> EvaluationResult:
    return evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        decision,
    )


def _payload(result: EvaluationResult, **updates: object) -> dict[str, object]:
    data = deepcopy(result.model_dump(mode="json"))
    data.update(updates)
    return data


def _oracle_disagreement_result(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    replay_decisions: dict[str, ToolDecision],
) -> EvaluationResult:
    scenario_id = "scenario_001"
    defective_oracle = OracleRecord(
        scenario_id=scenario_id,
        oracle_state=OracleState.UNIQUE_ADMISSIBLE,
        admissible_tool_ids=("evidence_tool_02",),
        decisive_clause_ids=("authority.requirement",),
        expected_decision=DecisionKind.SELECT,
        review_status=ReviewStatus.OWNER_APPROVED,
    )
    return evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        defective_oracle,
        replay_decisions[scenario_id],
    )


def test_scoreable_cannot_be_not_scored(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    with pytest.raises(ValidationError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(
            _payload(result, strict_contract_outcome=StrictContractOutcome.NOT_SCORED)
        )


@pytest.mark.parametrize(
    ("updates", "message"),
    (
        (
            {
                "evaluation_unit_status": EvaluationUnitStatus.INVALID,
                "oracle_state": OracleState.EVALUATION_UNIT_INVALID,
                "admissible_tool_ids": [],
                "strict_contract_outcome": StrictContractOutcome.NOT_SCORED,
                "evaluation_invalid_reasons": [],
            },
            "INVALID result requires an evaluation-invalid reason",
        ),
        (
            {"evaluation_invalid_reasons": ["fixture defect"]},
            "SCOREABLE result cannot have evaluation-invalid reasons",
        ),
        (
            {
                "oracle_state": OracleState.EVALUATION_UNIT_INVALID,
                "admissible_tool_ids": [],
            },
            "EVALUATION_UNIT_INVALID cannot be scoreable",
        ),
    ),
)
def test_evaluation_unit_status_invariants(
    updates: dict[str, object],
    message: str,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_001"],
    )
    with pytest.raises(ValidationError, match=message):
        EvaluationResult.model_validate(_payload(result, **updates))


def test_unique_contract_faithful_selection_cannot_be_incorrect(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    with pytest.raises(ValidationError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(
            _payload(
                result,
                strict_contract_outcome=StrictContractOutcome.INCORRECT,
            )
        )


def test_multiple_admissible_member_cannot_be_incorrect(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_004",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_004"],
    )
    with pytest.raises(ValidationError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(
            _payload(
                result,
                strict_contract_outcome=StrictContractOutcome.INCORRECT,
            )
        )


def test_no_admissible_no_tool_cannot_be_incorrect(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_003",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_003"],
    )
    with pytest.raises(ValidationError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(
            _payload(result, strict_contract_outcome=StrictContractOutcome.INCORRECT)
        )


@pytest.mark.parametrize(
    "admissibility",
    (SelectedToolAdmissibility.ADMISSIBLE, SelectedToolAdmissibility.INADMISSIBLE),
)
def test_tool_admissibility_requires_a_selection(
    admissibility: SelectedToolAdmissibility,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_003",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_003"],
    )
    with pytest.raises(ValidationError, match="tool admissibility requires SELECT"):
        EvaluationResult.model_validate(_payload(result, selected_tool_admissibility=admissibility))


def test_not_applicable_cannot_accompany_selected_tool(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    with pytest.raises(ValidationError, match="SELECT requires an admissibility"):
        EvaluationResult.model_validate(
            _payload(
                result,
                selected_tool_admissibility=SelectedToolAdmissibility.NOT_APPLICABLE,
            )
        )


def test_malformed_cannot_contain_normalized_decision(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = _evaluate("scenario_001", policy_views, scenario_metadata, oracle_records, None)
    with pytest.raises(ValidationError, match="MALFORMED output cannot contain"):
        EvaluationResult.model_validate(_payload(result, policy_decision=DecisionKind.NO_TOOL))


def test_unknown_tool_requires_select_id_and_failure(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        ToolDecision(
            scenario_id="scenario_001",
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_99",
        ),
    )
    with pytest.raises(ValidationError, match="UNKNOWN_TOOL requires"):
        EvaluationResult.model_validate(
            _payload(
                result,
                failure_codes=[],
                primary_failure_code=None,
                violated_clause_ids=[],
                violation_witnesses=[],
            )
        )


def test_known_admissible_selected_tool_cannot_be_marked_unknown(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    witness = {
        "clause_id": "decision.known_tool",
        "failure_code": FailureCode.UNKNOWN_TOOL,
        "scope": WitnessScope.SELECTED_TOOL,
        "tool_id": "evidence_tool_02",
        "expected_values": list(result.context.available_tool_ids),
        "actual_values": ["evidence_tool_02"],
    }
    with pytest.raises(ValidationError, match="must be absent from available_tool_ids"):
        EvaluationResult.model_validate(
            _payload(
                result,
                policy_output_status=PolicyOutputStatus.UNKNOWN_TOOL,
                strict_contract_outcome=StrictContractOutcome.INCORRECT,
                failure_codes=[FailureCode.UNKNOWN_TOOL],
                primary_failure_code=FailureCode.UNKNOWN_TOOL,
                violated_clause_ids=["decision.known_tool"],
                violation_witnesses=[witness],
            )
        )


def test_unknown_tool_id_cannot_appear_in_available_set(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        ToolDecision(
            scenario_id="scenario_001",
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_99",
        ),
    )
    payload = _payload(result)
    context = payload["context"]
    assert isinstance(context, dict)
    context["available_tool_ids"] = [*result.context.available_tool_ids, "evidence_tool_99"]
    with pytest.raises(ValidationError, match="must be absent from available_tool_ids"):
        EvaluationResult.model_validate(payload)


def test_valid_selected_tool_must_appear_in_available_set(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_001"],
    )
    payload = _payload(result)
    context = payload["context"]
    assert isinstance(context, dict)
    context["available_tool_ids"] = ["evidence_tool_01", "evidence_tool_03"]
    with pytest.raises(ValidationError, match="VALID SELECT requires an ID"):
        EvaluationResult.model_validate(payload)


def test_admissible_set_must_be_subset_of_available_set(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    with pytest.raises(ValidationError, match="must be a subset of available_tool_ids"):
        EvaluationResult.model_validate(_payload(result, admissible_tool_ids=["evidence_tool_99"]))


@pytest.mark.parametrize(
    "admissibility",
    (SelectedToolAdmissibility.ADMISSIBLE, SelectedToolAdmissibility.INADMISSIBLE),
)
def test_invalid_evaluation_unit_rejects_tool_admissibility_judgment(
    admissibility: SelectedToolAdmissibility,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _oracle_disagreement_result(policy_views, scenario_metadata, replay_decisions)
    with pytest.raises(ValidationError, match="must use NOT_APPLICABLE tool admissibility"):
        EvaluationResult.model_validate(_payload(result, selected_tool_admissibility=admissibility))


def test_invalid_evaluation_unit_rejects_scored_outcome(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _oracle_disagreement_result(policy_views, scenario_metadata, replay_decisions)
    with pytest.raises(ValidationError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(
            _payload(result, strict_contract_outcome=StrictContractOutcome.INCORRECT)
        )


@pytest.mark.parametrize(
    ("oracle_state", "admissible_tool_ids", "message"),
    (
        (OracleState.UNIQUE_ADMISSIBLE, [], "UNIQUE_ADMISSIBLE requires exactly one"),
        (
            OracleState.MULTIPLE_ADMISSIBLE,
            ["evidence_tool_02"],
            "MULTIPLE_ADMISSIBLE requires at least two",
        ),
        (
            OracleState.NO_ADMISSIBLE,
            ["evidence_tool_02"],
            "NO_ADMISSIBLE requires an empty",
        ),
    ),
)
def test_oracle_state_rejects_impossible_admissible_cardinality(
    oracle_state: OracleState,
    admissible_tool_ids: list[str],
    message: str,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    with pytest.raises(ValidationError, match=message):
        EvaluationResult.model_validate(
            _payload(
                result,
                oracle_state=oracle_state,
                admissible_tool_ids=admissible_tool_ids,
            )
        )


def test_correct_cannot_have_failures_or_witnesses(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_002",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_002"],
    )
    witness = {
        "clause_id": "decision.selection_required",
        "failure_code": FailureCode.UNSUPPORTED_ABSTENTION,
        "scope": WitnessScope.POLICY_OUTPUT,
        "tool_id": None,
        "expected_values": ["SELECT"],
        "actual_values": ["NO_TOOL"],
    }
    with pytest.raises(ValidationError, match="CORRECT result cannot contain"):
        EvaluationResult.model_validate(
            _payload(
                result,
                failure_codes=[FailureCode.UNSUPPORTED_ABSTENTION],
                primary_failure_code=FailureCode.UNSUPPORTED_ABSTENTION,
                violated_clause_ids=["decision.selection_required"],
                violation_witnesses=[witness],
            )
        )


def test_incorrect_requires_failure_diagnostic(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_001"],
    )
    with pytest.raises(ValidationError, match="INCORRECT result requires"):
        EvaluationResult.model_validate(
            _payload(
                result,
                failure_codes=[],
                primary_failure_code=None,
                violated_clause_ids=[],
                violation_witnesses=[],
            )
        )


def test_witness_failure_must_be_retained(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_001"],
    )
    with pytest.raises(ValidationError, match="every failure code must have a witness"):
        EvaluationResult.model_validate(
            _payload(
                result,
                failure_codes=[FailureCode.FORCED_SELECTION],
                primary_failure_code=FailureCode.FORCED_SELECTION,
            )
        )


def test_primary_failure_must_be_precedence_winner(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = _evaluate(
        "scenario_003",
        policy_views,
        scenario_metadata,
        oracle_records,
        ToolDecision(
            scenario_id="scenario_003",
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_01",
        ),
    )
    with pytest.raises(ValidationError, match="precedence winner"):
        EvaluationResult.model_validate(
            _payload(result, primary_failure_code=FailureCode.AUTHORITY_MISMATCH)
        )


def test_selected_tool_witness_must_reference_selected_tool(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    result = _evaluate(
        "scenario_001",
        policy_views,
        scenario_metadata,
        oracle_records,
        replay_decisions["scenario_001"],
    )
    payload = _payload(result)
    payload["violation_witnesses"][0]["tool_id"] = "evidence_tool_01"  # type: ignore[index]
    with pytest.raises(ValidationError, match="must reference the selected tool"):
        EvaluationResult.model_validate(payload)
