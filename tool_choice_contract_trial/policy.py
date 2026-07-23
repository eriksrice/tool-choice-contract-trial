"""Trusted policy adapter boundary for stored replay decisions."""

from __future__ import annotations

from typing import Protocol

from .models import PolicyView, ToolDecision


class PolicyAdapter(Protocol):
    """A supported adapter receives only the typed policy-visible view."""

    def decide(self, policy_view: PolicyView) -> ToolDecision: ...


class ReplayPolicyAdapter:
    """Return previously stored decisions without executing tools or providers."""

    def __init__(self, decisions: tuple[ToolDecision, ...]) -> None:
        by_scenario = {decision.scenario_id: decision for decision in decisions}
        if len(by_scenario) != len(decisions):
            raise ValueError("replay decisions must have unique scenario_id values")
        if len({decision.policy_id for decision in decisions}) != 1:
            raise ValueError("Milestone 1 replay requires exactly one policy_id")
        self._decisions = by_scenario

    def decide(self, policy_view: PolicyView) -> ToolDecision:
        try:
            return self._decisions[policy_view.scenario_id]
        except KeyError as error:
            raise ValueError(f"missing replay decision for {policy_view.scenario_id}") from error
