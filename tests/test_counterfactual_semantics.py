from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tool_choice_contract_trial.counterfactual import (
    CLAUSE_FIELD_OWNERSHIP,
    analyze_comparison,
    analyze_counterfactuals,
    establishes_individual_decisiveness,
)
from tool_choice_contract_trial.counterfactual_io import load_counterfactual_specs
from tool_choice_contract_trial.errors import ArtifactIntegrityError
from tool_choice_contract_trial.models import (
    CounterfactualComparisonSpec,
    CounterfactualFinding,
    CounterfactualValidationStatus,
    OracleState,
    PolicyView,
    ToolManifest,
)

ROOT = Path(__file__).resolve().parents[1]
COMPARISONS = ROOT / "fixtures" / "milestone_2a" / "authority_profiles" / "comparisons.jsonl"


def _spec(
    source_scenario_id: str,
    target_scenario_id: str,
    *,
    comparison_id: str = "test_comparison",
    clause_ids: tuple[str, ...] = ("authority.requirement",),
) -> CounterfactualComparisonSpec:
    return CounterfactualComparisonSpec(
        comparison_id=comparison_id,
        source_scenario_id=source_scenario_id,
        target_scenario_id=target_scenario_id,
        declared_changed_clause_ids=clause_ids,
    )


def _copy_view(
    source: PolicyView,
    *,
    scenario_id: str,
    contract_updates: dict[str, object] | None = None,
    tools: tuple[ToolManifest, ...] | None = None,
) -> PolicyView:
    contract = source.contract.model_copy(
        update={
            "contract_id": f"contract_{scenario_id}",
            **(contract_updates or {}),
        }
    )
    updates: dict[str, object] = {"scenario_id": scenario_id, "contract": contract}
    if tools is not None:
        updates["tools"] = tools
    return PolicyView.model_validate(source.model_copy(update=updates).model_dump(mode="json"))


def test_valid_singleton_authority_comparison_flips_unique_tool(
    policy_views: dict[str, PolicyView],
) -> None:
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_002"),
        policy_views["scenario_001"],
        policy_views["scenario_002"],
    )

    assert finding.validation_status is CounterfactualValidationStatus.VALID
    assert finding.observed_changed_contract_paths == ("contract.accepted_authority_profiles",)
    assert finding.source_computed_oracle_state is OracleState.UNIQUE_ADMISSIBLE
    assert finding.target_computed_oracle_state is OracleState.UNIQUE_ADMISSIBLE
    assert finding.source_computed_admissible_tool_ids == ("evidence_tool_01",)
    assert finding.target_computed_admissible_tool_ids == ("evidence_tool_02",)
    assert finding.unique_admissible_tool_flipped
    assert finding.counterfactually_decisive
    assert finding.individual_decisiveness_established


def test_clause_ownership_registry_is_explicit_and_milestone_bounded() -> None:
    assert CLAUSE_FIELD_OWNERSHIP == {
        "authority.requirement": ("contract.accepted_authority_profiles",),
    }


def test_valid_authority_comparison_changes_unique_to_multiple(
    policy_views: dict[str, PolicyView],
) -> None:
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_004"),
        policy_views["scenario_001"],
        policy_views["scenario_004"],
    )

    assert finding.validation_status is CounterfactualValidationStatus.VALID
    assert finding.source_computed_oracle_state is OracleState.UNIQUE_ADMISSIBLE
    assert finding.target_computed_oracle_state is OracleState.MULTIPLE_ADMISSIBLE
    assert finding.target_computed_admissible_tool_ids == (
        "evidence_tool_01",
        "evidence_tool_02",
    )
    assert finding.admissible_set_changed
    assert finding.oracle_state_changed
    assert not finding.unique_admissible_tool_flipped
    assert finding.counterfactually_decisive


def test_declared_clause_without_actual_field_change_is_invalid(
    policy_views: dict[str, PolicyView],
) -> None:
    target = _copy_view(policy_views["scenario_001"], scenario_id="scenario_099")
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_099"),
        policy_views["scenario_001"],
        target,
    )

    assert finding.validation_status is CounterfactualValidationStatus.INVALID
    assert finding.invalid_comparison_reasons == (
        "declared clause has no field change: authority.requirement",
    )
    assert not finding.counterfactually_decisive


def test_actual_field_difference_outside_declared_clause_is_invalid(
    policy_views: dict[str, PolicyView],
) -> None:
    target = _copy_view(
        policy_views["scenario_002"],
        scenario_id="scenario_099",
        contract_updates={"task_summary": "A different task summary."},
    )
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_099"),
        policy_views["scenario_001"],
        target,
    )

    assert finding.validation_status is CounterfactualValidationStatus.INVALID
    assert "task summaries differ" in finding.invalid_comparison_reasons
    assert "undeclared contract change: contract.task_summary" in finding.invalid_comparison_reasons


def test_unknown_clause_id_fails_comparison_validation(
    policy_views: dict[str, PolicyView],
) -> None:
    finding = analyze_comparison(
        _spec(
            "scenario_001",
            "scenario_002",
            clause_ids=("unknown.requirement",),
        ),
        policy_views["scenario_001"],
        policy_views["scenario_002"],
    )

    assert finding.validation_status is CounterfactualValidationStatus.INVALID
    assert "unknown clause ID: unknown.requirement" in finding.invalid_comparison_reasons
    assert not finding.counterfactually_decisive


def test_tool_manifest_drift_is_invalid(policy_views: dict[str, PolicyView]) -> None:
    base_target = policy_views["scenario_002"]
    changed_tool = base_target.tools[0].model_copy(update={"display_name": "Changed name"})
    target = _copy_view(
        base_target,
        scenario_id="scenario_099",
        tools=(changed_tool, *base_target.tools[1:]),
    )
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_099"),
        policy_views["scenario_001"],
        target,
    )

    assert finding.validation_status is CounterfactualValidationStatus.INVALID
    assert "tool manifests differ" in finding.invalid_comparison_reasons


def test_task_summary_drift_is_invalid(policy_views: dict[str, PolicyView]) -> None:
    target = _copy_view(
        policy_views["scenario_002"],
        scenario_id="scenario_099",
        contract_updates={"task_summary": "Different semantic task."},
    )
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_099"),
        policy_views["scenario_001"],
        target,
    )

    assert finding.validation_status is CounterfactualValidationStatus.INVALID
    assert "task summaries differ" in finding.invalid_comparison_reasons


@pytest.mark.parametrize(
    ("source_scenario_id", "target_scenario_id"),
    (
        ("scenario_099", "scenario_001"),
        ("scenario_001", "scenario_099"),
    ),
)
def test_missing_source_or_target_is_rejected(
    source_scenario_id: str,
    target_scenario_id: str,
    policy_views: dict[str, PolicyView],
) -> None:
    with pytest.raises(ArtifactIntegrityError, match="missing scenarios"):
        analyze_counterfactuals(
            (policy_views["scenario_001"],),
            (_spec(source_scenario_id, target_scenario_id),),
        )


def test_duplicate_comparison_id_is_rejected(policy_views: dict[str, PolicyView]) -> None:
    with pytest.raises(ArtifactIntegrityError, match="duplicate counterfactual comparison_id"):
        analyze_counterfactuals(
            tuple(policy_views.values()),
            (
                _spec("scenario_001", "scenario_002"),
                _spec("scenario_001", "scenario_004"),
            ),
        )


def test_source_equal_to_target_is_schema_invalid() -> None:
    with pytest.raises(ValidationError, match="must be distinct"):
        _spec("scenario_001", "scenario_001")


def test_valid_intervention_can_leave_relation_unchanged(
    policy_views: dict[str, PolicyView],
) -> None:
    target = _copy_view(
        policy_views["scenario_001"],
        scenario_id="scenario_099",
        contract_updates={
            "accepted_authority_profiles": (
                "independent_certified",
                "public_primary",
            )
        },
    )
    finding = analyze_comparison(
        _spec("scenario_001", "scenario_099"),
        policy_views["scenario_001"],
        target,
    )

    assert finding.validation_status is CounterfactualValidationStatus.VALID
    assert not finding.admissible_set_changed
    assert not finding.oracle_state_changed
    assert not finding.counterfactually_decisive
    assert not finding.individual_decisiveness_established


def test_multi_clause_intervention_does_not_establish_individual_decisiveness(
    policy_views: dict[str, PolicyView],
) -> None:
    assert not establishes_individual_decisiveness(
        comparison_valid=True,
        relation_changed=True,
        declared_changed_clause_ids=("clause.a", "clause.b"),
    )
    singleton = analyze_comparison(
        _spec("scenario_001", "scenario_002"),
        policy_views["scenario_001"],
        policy_views["scenario_002"],
    )
    payload = singleton.model_dump(mode="json")
    payload["declared_changed_clause_ids"] = ["clause.a", "clause.b"]
    payload["individual_decisiveness_established"] = False
    set_level = CounterfactualFinding.model_validate(payload)
    assert set_level.counterfactually_decisive
    assert not set_level.individual_decisiveness_established

    payload["individual_decisiveness_established"] = True
    with pytest.raises(ValidationError, match="decisive singleton intervention"):
        CounterfactualFinding.model_validate(payload)


def test_semantically_irrelevant_record_and_tool_order_are_canonical(
    policy_views: dict[str, PolicyView],
) -> None:
    specs = load_counterfactual_specs(COMPARISONS)
    baseline = analyze_counterfactuals(tuple(policy_views.values()), specs)
    reordered_views = tuple(
        view.model_copy(update={"tools": tuple(reversed(view.tools))})
        for view in reversed(tuple(policy_views.values()))
    )
    reordered = analyze_counterfactuals(reordered_views, tuple(reversed(specs)))

    assert reordered == baseline
