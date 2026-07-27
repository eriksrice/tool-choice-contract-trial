from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tool_choice_contract_trial.counterfactual import analyze_comparison
from tool_choice_contract_trial.counterfactual_io import load_counterfactual_findings
from tool_choice_contract_trial.counterfactual_registry import (
    ACTIVE_CLAUSE_OWNERSHIP_HASH,
    CLAUSE_FIELD_OWNERSHIP,
    SUPPORTED_COUNTERFACTUAL_CLAUSE_IDS,
)
from tool_choice_contract_trial.counterfactual_reporting import render_counterfactual_markdown
from tool_choice_contract_trial.errors import SchemaInvalidError
from tool_choice_contract_trial.models import (
    CounterfactualComparisonSpec,
    CounterfactualFinding,
    PolicyView,
)


def _valid_finding_payload(policy_views: dict[str, PolicyView]) -> dict[str, object]:
    finding = analyze_comparison(
        CounterfactualComparisonSpec(
            comparison_id="integrity_comparison",
            source_scenario_id="scenario_001",
            target_scenario_id="scenario_002",
            declared_changed_clause_ids=("authority.requirement",),
        ),
        policy_views["scenario_001"],
        policy_views["scenario_002"],
    )
    return finding.model_dump(mode="json")


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _make_invalid(payload: dict[str, object], reason: str) -> None:
    payload["validation_status"] = "INVALID"
    payload["invalid_comparison_reasons"] = [reason]
    payload["counterfactually_decisive_for_relation"] = False
    payload["individual_relation_decisiveness_established"] = False


def test_registry_is_the_explicit_supported_clause_and_path_authority() -> None:
    assert SUPPORTED_COUNTERFACTUAL_CLAUSE_IDS == ("authority.requirement",)
    assert CLAUSE_FIELD_OWNERSHIP == {
        "authority.requirement": ("contract.accepted_authority_profiles",),
    }
    assert len(ACTIVE_CLAUSE_OWNERSHIP_HASH) == 64


def test_valid_finding_without_observed_path_is_rejected(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = []

    with pytest.raises(ValidationError, match="no observed contract path"):
        CounterfactualFinding.model_validate(payload)


def test_valid_finding_with_authority_and_task_summary_paths_is_rejected(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = [
        "contract.accepted_authority_profiles",
        "contract.task_summary",
    ]

    with pytest.raises(
        ValidationError,
        match=r"undeclared contract change: contract\.task_summary",
    ):
        CounterfactualFinding.model_validate(payload)


def test_valid_finding_with_unknown_clause_is_rejected(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["declared_changed_clause_ids"] = ["unknown.requirement"]

    with pytest.raises(ValidationError, match=r"unknown clause ID: unknown\.requirement"):
        CounterfactualFinding.model_validate(payload)


def test_valid_finding_with_undeclared_path_is_rejected(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = ["contract.citations_required"]

    with pytest.raises(
        ValidationError,
        match=r"undeclared contract change: contract\.citations_required",
    ):
        CounterfactualFinding.model_validate(payload)


def test_valid_finding_with_clause_accounting_for_no_path_is_rejected(
    policy_views: dict[str, PolicyView],
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = ["contract.task_summary"]

    with pytest.raises(
        ValidationError,
        match=r"declared clause has no field change: authority\.requirement",
    ):
        CounterfactualFinding.model_validate(payload)


def test_finding_with_stale_registry_hash_is_rejected(
    policy_views: dict[str, PolicyView],
    tmp_path: Path,
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["clause_ownership_hash"] = "0" * 64

    with pytest.raises(ValidationError, match="does not match the active registry"):
        CounterfactualFinding.model_validate(payload)

    path = tmp_path / "stale.jsonl"
    _write_payload(path, payload)
    with pytest.raises(SchemaInvalidError, match="does not match the active registry"):
        load_counterfactual_findings(path)


def test_invalid_unknown_clause_finding_is_representable_and_loadable(
    policy_views: dict[str, PolicyView],
    tmp_path: Path,
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["declared_changed_clause_ids"] = ["unknown.requirement"]
    _make_invalid(payload, "unknown clause ID: unknown.requirement")
    path = tmp_path / "unknown.jsonl"
    _write_payload(path, payload)

    finding = load_counterfactual_findings(path)[0]

    assert finding.declared_changed_clause_ids == ("unknown.requirement",)
    assert finding.validation_status.value == "INVALID"


def test_invalid_undeclared_path_finding_is_representable_and_loadable(
    policy_views: dict[str, PolicyView],
    tmp_path: Path,
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = ["contract.task_summary"]
    _make_invalid(payload, "undeclared contract change: contract.task_summary")
    path = tmp_path / "undeclared.jsonl"
    _write_payload(path, payload)

    finding = load_counterfactual_findings(path)[0]

    assert finding.observed_changed_contract_paths == ("contract.task_summary",)
    assert finding.validation_status.value == "INVALID"


def test_invalid_no_change_finding_is_representable_and_loadable(
    policy_views: dict[str, PolicyView],
    tmp_path: Path,
) -> None:
    payload = _valid_finding_payload(policy_views)
    payload["observed_changed_contract_paths"] = []
    _make_invalid(payload, "no observed contract path")
    path = tmp_path / "no-change.jsonl"
    _write_payload(path, payload)

    finding = load_counterfactual_findings(path)[0]

    assert finding.observed_changed_contract_paths == ()
    assert finding.validation_status.value == "INVALID"


def test_analyzer_valid_finding_round_trips_through_loader(
    policy_views: dict[str, PolicyView],
    tmp_path: Path,
) -> None:
    payload = _valid_finding_payload(policy_views)
    path = tmp_path / "valid.jsonl"
    _write_payload(path, payload)

    loaded = load_counterfactual_findings(path)

    assert loaded == (CounterfactualFinding.model_validate(payload),)
    assert loaded[0].clause_ownership_hash == ACTIVE_CLAUSE_OWNERSHIP_HASH


def test_report_rechecks_finding_registry_integrity(
    policy_views: dict[str, PolicyView],
) -> None:
    finding = CounterfactualFinding.model_validate(_valid_finding_payload(policy_views))
    stale = finding.model_copy(update={"clause_ownership_hash": "0" * 64})

    with pytest.raises(ValueError, match="does not match the active registry"):
        render_counterfactual_markdown((stale,))
