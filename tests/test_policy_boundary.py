from __future__ import annotations

import inspect
from pathlib import Path
from typing import get_type_hints

from tool_choice_contract_trial.models import PolicyView, ToolDecision
from tool_choice_contract_trial.policy import PolicyAdapter, ReplayPolicyAdapter

ORACLE_ONLY_FIELDS = {
    "admissible_tool_ids",
    "construction_notes",
    "decisive_clause_ids",
    "expected_decision",
    "family_id",
    "family_label",
    "oracle_state",
    "review_status",
    "variant_label",
    "comparison_group_id",
}
SEMANTIC_IDENTIFIER_TOKENS = {
    "approved_internal",
    "authority",
    "multiple",
    "no_tool",
    "public_primary",
    "unique",
    "unsupported",
}


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_policy_view_contains_no_oracle_only_fields(
    policy_views: dict[str, PolicyView],
) -> None:
    for view in policy_views.values():
        visible_keys = _all_keys(view.model_dump(mode="json"))
        assert visible_keys.isdisjoint(ORACLE_ONLY_FIELDS)


def test_policy_visible_identifiers_are_opaque(
    policy_views: dict[str, PolicyView],
) -> None:
    for view in policy_views.values():
        identifiers = (
            view.scenario_id,
            view.contract.contract_id,
            *(tool.tool_id for tool in view.tools),
        )
        for identifier in identifiers:
            assert all(token not in identifier for token in SEMANTIC_IDENTIFIER_TOKENS)


def test_supported_adapter_argument_is_only_typed_policy_view() -> None:
    hints = get_type_hints(PolicyAdapter.decide)
    parameters = tuple(inspect.signature(PolicyAdapter.decide).parameters)
    assert parameters == ("self", "policy_view")
    assert hints["policy_view"] is PolicyView
    assert hints["return"] is ToolDecision


def test_replay_adapter_receives_policy_view_only(
    policy_views: dict[str, PolicyView], replay_decisions: dict[str, ToolDecision]
) -> None:
    adapter = ReplayPolicyAdapter(tuple(replay_decisions.values()))
    view = policy_views["scenario_001"]
    assert adapter.decide(view) == replay_decisions[view.scenario_id]


def test_runtime_package_has_no_network_or_provider_imports() -> None:
    package_directory = Path(__file__).resolve().parents[1] / "tool_choice_contract_trial"
    source = "\n".join(path.read_text() for path in package_directory.glob("*.py"))
    forbidden_imports = (
        "import httpx",
        "import openai",
        "import requests",
        "import socket",
        "import urllib",
    )
    assert all(forbidden not in source for forbidden in forbidden_imports)
