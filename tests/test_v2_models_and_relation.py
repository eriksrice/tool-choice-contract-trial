from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tool_choice_contract_trial.errors import ArtifactIntegrityError, SchemaInvalidError
from tool_choice_contract_trial.v2_io import (
    load_oracle_expectations_v2,
    load_oracle_reviews_v2,
    load_policy_views_v2,
)
from tool_choice_contract_trial.v2_models import (
    OracleStateV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    TaskContractV2,
    ToolManifestV2,
)
from tool_choice_contract_trial.v2_registry import (
    OUTPUT_CITATIONS_V2,
    TOOL_PROHIBITION_V2,
    V2_RELATION_CLAUSE_REGISTRY,
)
from tool_choice_contract_trial.v2_relation import assess_policy_view_v2
from tool_choice_contract_trial.v2_validation import validate_oracle_candidates_v2

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "fixtures" / "milestone_2b" / "review_candidate" / "scenarios.jsonl"
EXPECTATIONS = ROOT / "fixtures" / "milestone_2b" / "review_candidate" / "oracle_expectations.jsonl"
REVIEWS = ROOT / "fixtures" / "milestone_2b" / "review_candidate" / "oracle_reviews.jsonl"


@pytest.fixture
def v2_views() -> dict[str, PolicyViewV2]:
    return {view.scenario_id: view for view in load_policy_views_v2(SCENARIOS)}


@pytest.fixture
def v2_findings() -> dict[str, OracleValidationFindingV2]:
    findings = validate_oracle_candidates_v2(
        load_policy_views_v2(SCENARIOS),
        load_oracle_expectations_v2(EXPECTATIONS),
        load_oracle_reviews_v2(REVIEWS),
    )
    return {finding.scenario_id: finding for finding in findings}


def test_input_profile_family_relations(v2_views: dict[str, PolicyViewV2]) -> None:
    relations = {
        scenario_id: assess_policy_view_v2(v2_views[scenario_id])
        for scenario_id in (
            "v2_scenario_001",
            "v2_scenario_002",
            "v2_scenario_003",
            "v2_scenario_004",
        )
    }

    assert relations["v2_scenario_001"].admissible_tool_ids == ("v2_tool_001",)
    assert relations["v2_scenario_002"].admissible_tool_ids == ("v2_tool_002",)
    assert relations["v2_scenario_003"].oracle_state is OracleStateV2.NO_ADMISSIBLE
    assert relations["v2_scenario_004"].oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE
    assert relations["v2_scenario_004"].admissible_tool_ids == (
        "v2_tool_001",
        "v2_tool_002",
    )


def test_output_evidence_family_relations(v2_views: dict[str, PolicyViewV2]) -> None:
    relations = {
        scenario_id: assess_policy_view_v2(v2_views[scenario_id])
        for scenario_id in (
            "v2_scenario_005",
            "v2_scenario_006",
            "v2_scenario_007",
            "v2_scenario_008",
        )
    }

    assert relations["v2_scenario_005"].admissible_tool_ids == ("v2_tool_003",)
    assert relations["v2_scenario_006"].admissible_tool_ids == ("v2_tool_004",)
    assert relations["v2_scenario_007"].oracle_state is OracleStateV2.NO_ADMISSIBLE
    assert relations["v2_scenario_008"].oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE
    assert relations["v2_scenario_008"].admissible_tool_ids == (
        "v2_tool_003",
        "v2_tool_004",
    )


def test_explicit_prohibition_family_relations(v2_views: dict[str, PolicyViewV2]) -> None:
    first = assess_policy_view_v2(v2_views["v2_scenario_009"])
    second = assess_policy_view_v2(v2_views["v2_scenario_010"])
    prohibit_all = assess_policy_view_v2(v2_views["v2_scenario_011"])
    unavailable = assess_policy_view_v2(v2_views["v2_scenario_012"])

    assert first.admissible_tool_ids == ("v2_tool_006",)
    assert second.admissible_tool_ids == ("v2_tool_005",)
    assert prohibit_all.oracle_state is OracleStateV2.NO_ADMISSIBLE
    assert unavailable.oracle_state is OracleStateV2.CONTRACT_INVALID
    assert unavailable.admissible_tool_ids == ()
    assert unavailable.contract_invalid_reasons == (
        "forbidden tool ID is unavailable: v2_tool_099",
    )


def test_minimal_pair_catalogs_are_equal_and_only_typed_requirement_changes(
    v2_views: dict[str, PolicyViewV2],
) -> None:
    for source_id, target_id, changed_field in (
        ("v2_scenario_001", "v2_scenario_002", "required_input_profiles"),
        ("v2_scenario_005", "v2_scenario_006", "required_output_profiles"),
        ("v2_scenario_009", "v2_scenario_010", "forbidden_tool_ids"),
    ):
        source = v2_views[source_id]
        target = v2_views[target_id]
        assert source.tools == target.tools
        source_contract = source.contract.model_dump(mode="json")
        target_contract = target.contract.model_dump(mode="json")
        source_contract.pop("contract_id")
        target_contract.pop("contract_id")
        source_value = source_contract.pop(changed_field)
        target_value = target_contract.pop(changed_field)
        assert source_contract == target_contract
        assert source_value != target_value


def test_clause_witnesses_identify_input_output_and_prohibition(
    v2_views: dict[str, PolicyViewV2],
) -> None:
    input_relation = assess_policy_view_v2(v2_views["v2_scenario_001"])
    output_relation = assess_policy_view_v2(v2_views["v2_scenario_005"])
    prohibition_relation = assess_policy_view_v2(v2_views["v2_scenario_009"])

    assert [(witness.tool_id, witness.clause_id) for witness in input_relation.witnesses] == [
        ("v2_tool_002", "input.requirement"),
    ]
    assert [(witness.tool_id, witness.clause_id) for witness in output_relation.witnesses] == [
        ("v2_tool_004", "output.requirement"),
    ]
    assert [(witness.tool_id, witness.clause_id) for witness in prohibition_relation.witnesses] == [
        ("v2_tool_005", TOOL_PROHIBITION_V2)
    ]


def test_citation_requirement_has_its_own_clause_witness(
    v2_views: dict[str, PolicyViewV2],
) -> None:
    view = v2_views["v2_scenario_001"]
    changed_tool = view.tools[0].model_copy(update={"provides_citations": False})
    changed_view = PolicyViewV2.model_validate(
        view.model_copy(update={"tools": (changed_tool, view.tools[1])}).model_dump(mode="json")
    )

    relation = assess_policy_view_v2(changed_view)

    assert any(
        witness.tool_id == "v2_tool_001" and witness.clause_id == OUTPUT_CITATIONS_V2
        for witness in relation.witnesses
    )


def test_v2_registry_is_explicit_and_milestone_bounded() -> None:
    assert set(V2_RELATION_CLAUSE_REGISTRY) == {
        "authority.requirement",
        "capability.requirement",
        "input.requirement",
        "output.citations",
        "output.requirement",
        "tool.prohibition",
    }
    assert {
        clause_id: clause.expected_failure_code
        for clause_id, clause in V2_RELATION_CLAUSE_REGISTRY.items()
    } == {
        "authority.requirement": "F_AUTHORITY_MISMATCH",
        "capability.requirement": "F_CAPABILITY_MISMATCH",
        "input.requirement": "F_INPUT_CONTRACT_MISMATCH",
        "output.citations": "F_OUTPUT_CONTRACT_MISMATCH",
        "output.requirement": "F_OUTPUT_CONTRACT_MISMATCH",
        "tool.prohibition": "F_EXPLICIT_PROHIBITION",
    }


def test_policy_visible_v2_boundary_contains_no_evaluator_fields(
    v2_views: dict[str, PolicyViewV2],
) -> None:
    assert set(PolicyViewV2.model_fields) == {
        "schema_version",
        "scenario_id",
        "contract",
        "tools",
    }
    serialized = "".join(view.model_dump_json() for view in v2_views.values())
    for forbidden in (
        "family_id",
        "variant_label",
        "expected_oracle_state",
        "admissible_tool_ids",
        "reviewer_role",
        "disposition",
        "construction_notes",
    ):
        assert forbidden not in serialized


def test_v2_identifiers_are_opaque(v2_views: dict[str, PolicyViewV2]) -> None:
    for view in v2_views.values():
        assert view.scenario_id.startswith("v2_scenario_")
        assert view.contract.contract_id.startswith("v2_contract_")
        assert all(tool.tool_id.startswith("v2_tool_") for tool in view.tools)
        identifiers = " ".join(
            [view.scenario_id, view.contract.contract_id, *(tool.tool_id for tool in view.tools)]
        )
        for semantic_label in ("input", "output", "prohibition", "unique", "multiple", "none"):
            assert semantic_label not in identifiers


@pytest.mark.parametrize("model", (TaskContractV2, ToolManifestV2, PolicyViewV2))
def test_v2_policy_models_reject_empty_or_extra_fields(model: type[object]) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({})  # type: ignore[attr-defined]

    with pytest.raises(ValidationError, match="unexpected"):
        model.model_validate({"unexpected": True})  # type: ignore[attr-defined]


def test_duplicate_v2_tool_ids_are_rejected(v2_views: dict[str, PolicyViewV2]) -> None:
    view = v2_views["v2_scenario_001"]
    with pytest.raises(ValidationError, match="unique tool_id"):
        PolicyViewV2.model_validate(
            view.model_copy(update={"tools": (view.tools[0], view.tools[0])}).model_dump(
                mode="json"
            )
        )


def test_duplicate_v2_policy_view_rows_fail_loudly(tmp_path: Path) -> None:
    rows = SCENARIOS.read_text().splitlines()
    path = tmp_path / "duplicate-scenarios.jsonl"
    path.write_text("\n".join([*rows, rows[0]]) + "\n")

    with pytest.raises(ArtifactIntegrityError, match="duplicate v2 policy view"):
        load_policy_views_v2(path)


def test_malformed_v2_policy_view_fails_schema_validation(tmp_path: Path) -> None:
    payload = json.loads(SCENARIOS.read_text().splitlines()[0])
    payload["family_label"] = "Evaluator-only leakage"
    path = tmp_path / "malformed-scenario.jsonl"
    path.write_text(json.dumps(payload) + "\n")

    with pytest.raises(SchemaInvalidError, match="SCHEMA_INVALID"):
        load_policy_views_v2(path)


def test_finding_rejects_admissible_tool_absent_from_available_provenance(
    v2_findings: dict[str, OracleValidationFindingV2],
) -> None:
    payload = v2_findings["v2_scenario_001"].model_dump(mode="json")
    payload["available_tool_ids"] = ["v2_tool_002"]

    with pytest.raises(ValidationError, match="subset of available tools"):
        OracleValidationFindingV2.model_validate(payload)


def test_finding_rejects_witness_for_unknown_or_admissible_tool(
    v2_findings: dict[str, OracleValidationFindingV2],
) -> None:
    baseline = v2_findings["v2_scenario_001"]
    for tool_id, message in (
        ("v2_tool_099", "unavailable tool"),
        ("v2_tool_001", "computed-admissible tool"),
    ):
        payload = baseline.model_dump(mode="json")
        payload["relation_witnesses"][0]["tool_id"] = tool_id
        with pytest.raises(ValidationError, match=message):
            OracleValidationFindingV2.model_validate(payload)


def test_clause_witness_rejects_wrong_failure_code_or_registry_fields(
    v2_findings: dict[str, OracleValidationFindingV2],
) -> None:
    baseline = v2_findings["v2_scenario_001"]
    changes = (
        ("failure_code", "F_AUTHORITY_MISMATCH", "failure_code"),
        ("contract_fields", ["contract.required_output_profiles"], "contract_fields"),
        ("manifest_fields", ["manifest.produced_output_profiles"], "manifest_fields"),
    )
    for field_name, value, message in changes:
        payload = baseline.model_dump(mode="json")
        payload["relation_witnesses"][0][field_name] = value
        with pytest.raises(ValidationError, match=message):
            OracleValidationFindingV2.model_validate(payload)


def test_finding_rejects_missing_or_duplicate_inadmissibility_witness(
    v2_findings: dict[str, OracleValidationFindingV2],
) -> None:
    baseline = v2_findings["v2_scenario_001"]
    missing = baseline.model_dump(mode="json")
    missing["relation_witnesses"] = []
    duplicate = baseline.model_dump(mode="json")
    duplicate["relation_witnesses"].append(duplicate["relation_witnesses"][0].copy())

    with pytest.raises(ValidationError, match="require relation witnesses"):
        OracleValidationFindingV2.model_validate(missing)
    with pytest.raises(ValidationError, match="duplicate a tool/clause pair"):
        OracleValidationFindingV2.model_validate(duplicate)


def test_contract_invalid_finding_rejects_ordinary_tool_witnesses(
    v2_findings: dict[str, OracleValidationFindingV2],
) -> None:
    payload = v2_findings["v2_scenario_012"].model_dump(mode="json")
    prohibition_witness = v2_findings["v2_scenario_009"].model_dump(mode="json")[
        "relation_witnesses"
    ][0]
    payload["relation_witnesses"] = [prohibition_witness]

    with pytest.raises(ValidationError, match="CONTRACT_INVALID cannot contain"):
        OracleValidationFindingV2.model_validate(payload)
