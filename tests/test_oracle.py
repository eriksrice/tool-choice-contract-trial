from __future__ import annotations

from tool_choice_contract_trial.models import OracleState, PolicyView, ScenarioMetadata
from tool_choice_contract_trial.oracle import AUTHORITY_CLAUSE, assess_policy_view


def test_exactly_one_four_variant_family(
    policy_views: dict[str, PolicyView],
    scenario_metadata: dict[str, ScenarioMetadata],
) -> None:
    assert set(policy_views) == {
        "scenario_001",
        "scenario_002",
        "scenario_003",
        "scenario_004",
    }
    assert set(policy_views) == set(scenario_metadata)
    assert {metadata.family_id for metadata in scenario_metadata.values()} == {"authority_profiles"}


def test_four_intended_oracle_states_and_admissible_sets(
    policy_views: dict[str, PolicyView],
) -> None:
    expected = {
        "scenario_001": (
            OracleState.UNIQUE_ADMISSIBLE,
            ("evidence_tool_01",),
        ),
        "scenario_002": (
            OracleState.UNIQUE_ADMISSIBLE,
            ("evidence_tool_02",),
        ),
        "scenario_003": (OracleState.NO_ADMISSIBLE, ()),
        "scenario_004": (
            OracleState.MULTIPLE_ADMISSIBLE,
            ("evidence_tool_01", "evidence_tool_02"),
        ),
    }
    for scenario_id, (oracle_state, admissible_tool_ids) in expected.items():
        relation = assess_policy_view(policy_views[scenario_id])
        assert relation.oracle_state is oracle_state
        assert relation.admissible_tool_ids == admissible_tool_ids
        assert relation.decisive_clause_ids == (AUTHORITY_CLAUSE,)


def test_unique_cases_are_a_one_clause_minimal_pair_that_flips_the_tool(
    policy_views: dict[str, PolicyView],
) -> None:
    public = policy_views["scenario_001"]
    internal = policy_views["scenario_002"]
    public_data = public.model_dump(mode="json")
    internal_data = internal.model_dump(mode="json")
    public_data.pop("scenario_id")
    internal_data.pop("scenario_id")
    public_data["contract"].pop("contract_id")
    internal_data["contract"].pop("contract_id")
    public_authority = public_data["contract"].pop("accepted_authority_profiles")
    internal_authority = internal_data["contract"].pop("accepted_authority_profiles")

    assert public_data == internal_data
    assert public_authority == ["public_primary"]
    assert internal_authority == ["approved_internal"]
    assert assess_policy_view(public).admissible_tool_ids == ("evidence_tool_01",)
    assert assess_policy_view(internal).admissible_tool_ids == ("evidence_tool_02",)


def test_tools_are_neutral_and_differ_only_by_authority_profile(
    policy_views: dict[str, PolicyView],
) -> None:
    catalogs = [view.tools for view in policy_views.values()]
    assert all(catalog == catalogs[0] for catalog in catalogs)
    normalized_tools = []
    for tool in catalogs[0]:
        data = tool.model_dump(mode="json")
        data.pop("tool_id")
        data.pop("display_name")
        data.pop("authority_profiles")
        normalized_tools.append(data)
    assert normalized_tools[0] == normalized_tools[1] == normalized_tools[2]
    assert len({len(tool.description) for tool in catalogs[0]}) == 1
