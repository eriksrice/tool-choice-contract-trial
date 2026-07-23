from __future__ import annotations

import pytest

from tool_choice_contract_trial.errors import ArtifactIntegrityError
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
)
from tool_choice_contract_trial.oracle import CONTRACT_CONSISTENCY_CLAUSE


def test_plausible_negative_has_authority_mismatch_witness(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    scenario_id = "scenario_001"
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        replay_decisions[scenario_id],
    )
    assert result.strict_contract_outcome is StrictContractOutcome.INCORRECT
    assert result.selected_tool_admissibility is SelectedToolAdmissibility.INADMISSIBLE
    assert result.failure_codes == (FailureCode.AUTHORITY_MISMATCH,)
    assert result.primary_failure_code is FailureCode.AUTHORITY_MISMATCH
    assert result.violated_clause_ids == ("authority.requirement",)
    assert result.violation_witnesses[0].expected_values == ("public_primary",)
    assert result.violation_witnesses[0].actual_values == ("approved_internal",)


def test_multiple_member_selection_is_not_inadmissible(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    scenario_id = "scenario_004"
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        replay_decisions[scenario_id],
    )
    assert result.oracle_state is OracleState.MULTIPLE_ADMISSIBLE
    assert result.selected_tool_admissibility is SelectedToolAdmissibility.ADMISSIBLE
    assert result.strict_contract_outcome is StrictContractOutcome.ADMISSIBLE_BUT_UNJUSTIFIED
    assert result.failure_codes == (FailureCode.AMBIGUITY_FORCED_RESOLUTION,)


def test_indeterminate_is_contract_faithful_for_multiple(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    scenario_id = "scenario_004"
    decision = ToolDecision(
        scenario_id=scenario_id,
        policy_id="test_policy",
        decision=DecisionKind.INDETERMINATE,
    )
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        decision,
    )
    assert result.strict_contract_outcome is StrictContractOutcome.CORRECT
    assert result.selected_tool_admissibility is SelectedToolAdmissibility.NOT_APPLICABLE


def test_primary_failure_precedence_retains_every_failure(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    scenario_id = "scenario_003"
    decision = ToolDecision(
        scenario_id=scenario_id,
        policy_id="test_policy",
        decision=DecisionKind.SELECT,
        selected_tool_id="evidence_tool_01",
    )
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        decision,
    )
    assert result.failure_codes == (
        FailureCode.FORCED_SELECTION,
        FailureCode.AUTHORITY_MISMATCH,
    )
    assert result.primary_failure_code is FailureCode.FORCED_SELECTION
    assert len(result.violation_witnesses) == 2


def test_contract_invalid_is_schema_valid_and_scoreable(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
) -> None:
    base = policy_views["scenario_001"]
    view = base.model_copy(
        update={
            "scenario_id": "scenario_099",
            "contract": base.contract.model_copy(
                update={"prohibited_authority_profiles": ("public_primary",)}
            ),
        }
    )
    metadata = scenario_metadata["scenario_001"].model_copy(
        update={"scenario_id": view.scenario_id}
    )
    oracle = OracleRecord(
        scenario_id=view.scenario_id,
        oracle_state=OracleState.CONTRACT_INVALID,
        admissible_tool_ids=(),
        decisive_clause_ids=(CONTRACT_CONSISTENCY_CLAUSE,),
        expected_decision=DecisionKind.INVALID_CONTRACT,
        review_status=ReviewStatus.OWNER_APPROVED,
    )
    decision = ToolDecision(
        scenario_id=view.scenario_id,
        policy_id="test_policy",
        decision=DecisionKind.INVALID_CONTRACT,
    )
    result = evaluate_case(view, metadata, oracle, decision)
    assert result.evaluation_unit_status is EvaluationUnitStatus.SCOREABLE
    assert result.oracle_state is OracleState.CONTRACT_INVALID
    assert result.strict_contract_outcome is StrictContractOutcome.CORRECT
    contradictory_payload = result.model_dump(mode="json")
    contradictory_payload["strict_contract_outcome"] = StrictContractOutcome.INCORRECT
    with pytest.raises(ValueError, match="does not match the derived Milestone 1 outcome"):
        EvaluationResult.model_validate(contradictory_payload)


def test_oracle_disagreement_is_evaluation_unit_invalid_not_policy_failure(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    scenario_id = "scenario_001"
    defective_oracle = OracleRecord(
        scenario_id=scenario_id,
        oracle_state=OracleState.UNIQUE_ADMISSIBLE,
        admissible_tool_ids=("evidence_tool_02",),
        decisive_clause_ids=("authority.requirement",),
        expected_decision=DecisionKind.SELECT,
        review_status=ReviewStatus.OWNER_APPROVED,
    )
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        defective_oracle,
        replay_decisions[scenario_id],
    )
    assert result.evaluation_unit_status is EvaluationUnitStatus.INVALID
    assert result.oracle_state is OracleState.EVALUATION_UNIT_INVALID
    assert result.policy_output_status is PolicyOutputStatus.VALID
    assert result.policy_decision is DecisionKind.SELECT
    assert result.selected_tool_id == replay_decisions[scenario_id].selected_tool_id
    assert result.selected_tool_admissibility is SelectedToolAdmissibility.NOT_APPLICABLE
    assert result.strict_contract_outcome is StrictContractOutcome.NOT_SCORED
    assert result.failure_codes == ()
    assert result.evaluation_invalid_reasons


def test_normalized_malformed_observation_is_distinct_from_unknown_tool(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    scenario_id = "scenario_001"
    malformed = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        None,
    )
    unknown = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        ToolDecision(
            scenario_id=scenario_id,
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_99",
        ),
    )
    assert malformed.policy_output_status is PolicyOutputStatus.MALFORMED
    assert malformed.failure_codes == (FailureCode.MALFORMED_DECISION,)
    assert unknown.policy_output_status is PolicyOutputStatus.UNKNOWN_TOOL
    assert unknown.failure_codes == (FailureCode.UNKNOWN_TOOL,)


def test_decision_from_another_scenario_is_rejected_before_scoring(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
    replay_decisions: dict[str, ToolDecision],
) -> None:
    with pytest.raises(ArtifactIntegrityError, match="decision scenario_id"):
        evaluate_case(
            policy_views["scenario_001"],
            scenario_metadata["scenario_001"],
            oracle_records["scenario_001"],
            replay_decisions["scenario_002"],
        )


@pytest.mark.parametrize("scenario_id", ("scenario_001", "scenario_003", "scenario_004"))
def test_false_invalid_contract_response_has_its_own_failure_not_abstention(
    scenario_id: str,
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        ToolDecision(
            scenario_id=scenario_id,
            policy_id="test_policy",
            decision=DecisionKind.INVALID_CONTRACT,
        ),
    )
    assert result.failure_codes == (FailureCode.INVALID_CONTRACT_MISCLASSIFICATION,)
    assert FailureCode.UNSUPPORTED_ABSTENTION not in result.failure_codes


@pytest.mark.parametrize(
    ("scenario_id", "expected_failures"),
    (
        (
            "scenario_003",
            (FailureCode.UNKNOWN_TOOL, FailureCode.FORCED_SELECTION),
        ),
        (
            "scenario_004",
            (
                FailureCode.UNKNOWN_TOOL,
                FailureCode.AMBIGUITY_FORCED_RESOLUTION,
            ),
        ),
    ),
)
def test_unknown_tool_retains_state_specific_failures(
    scenario_id: str,
    expected_failures: tuple[FailureCode, ...],
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        ToolDecision(
            scenario_id=scenario_id,
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_99",
        ),
    )
    assert result.failure_codes == expected_failures


def test_multiple_nonmember_retains_ambiguity_and_authority_failures(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
    oracle_records: dict[str, OracleRecord],
) -> None:
    scenario_id = "scenario_004"
    result = evaluate_case(
        policy_views[scenario_id],
        scenario_metadata[scenario_id],
        oracle_records[scenario_id],
        ToolDecision(
            scenario_id=scenario_id,
            policy_id="test_policy",
            decision=DecisionKind.SELECT,
            selected_tool_id="evidence_tool_03",
        ),
    )
    assert result.failure_codes == (
        FailureCode.AUTHORITY_MISMATCH,
        FailureCode.AMBIGUITY_FORCED_RESOLUTION,
    )
    assert result.selected_tool_admissibility is SelectedToolAdmissibility.INADMISSIBLE
