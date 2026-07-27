"""Deterministic manifest-compatibility relation checker."""

from __future__ import annotations

from dataclasses import dataclass

from .counterfactual_registry import AUTHORITY_CLAUSE
from .models import (
    ClauseWitness,
    DecisionKind,
    FailureCode,
    OracleRecord,
    OracleState,
    PolicyView,
    ToolManifest,
    WitnessScope,
)

CAPABILITY_CLAUSE = "capability.requirement"
CITATION_CLAUSE = "citation.requirement"
PROHIBITION_CLAUSE = "authority.prohibition"
CONTRACT_CONSISTENCY_CLAUSE = "contract.semantic_consistency"


@dataclass(frozen=True)
class RelationAssessment:
    oracle_state: OracleState
    admissible_tool_ids: tuple[str, ...]
    decisive_clause_ids: tuple[str, ...]
    expected_decision: DecisionKind
    witnesses_by_tool: dict[str, tuple[ClauseWitness, ...]]


def _tool_witnesses(view: PolicyView, tool: ToolManifest) -> tuple[ClauseWitness, ...]:
    contract = view.contract
    witnesses: list[ClauseWitness] = []
    missing_capabilities = tuple(
        capability
        for capability in contract.required_capabilities
        if capability not in tool.capabilities
    )
    if missing_capabilities:
        witnesses.append(
            ClauseWitness(
                clause_id=CAPABILITY_CLAUSE,
                failure_code=FailureCode.CAPABILITY_MISMATCH,
                scope=WitnessScope.SELECTED_TOOL,
                tool_id=tool.tool_id,
                expected_values=missing_capabilities,
                actual_values=tool.capabilities,
            )
        )
    if contract.citations_required and not tool.provides_citations:
        witnesses.append(
            ClauseWitness(
                clause_id=CITATION_CLAUSE,
                failure_code=FailureCode.OUTPUT_CONTRACT_MISMATCH,
                scope=WitnessScope.SELECTED_TOOL,
                tool_id=tool.tool_id,
                expected_values=("citations_provided",),
                actual_values=("citations_unavailable",),
            )
        )
    if not set(contract.accepted_authority_profiles).intersection(tool.authority_profiles):
        witnesses.append(
            ClauseWitness(
                clause_id=AUTHORITY_CLAUSE,
                failure_code=FailureCode.AUTHORITY_MISMATCH,
                scope=WitnessScope.SELECTED_TOOL,
                tool_id=tool.tool_id,
                expected_values=contract.accepted_authority_profiles,
                actual_values=tool.authority_profiles,
            )
        )
    prohibited = tuple(
        sorted(set(contract.prohibited_authority_profiles).intersection(tool.authority_profiles))
    )
    if prohibited:
        witnesses.append(
            ClauseWitness(
                clause_id=PROHIBITION_CLAUSE,
                failure_code=FailureCode.EXPLICIT_PROHIBITION,
                scope=WitnessScope.SELECTED_TOOL,
                tool_id=tool.tool_id,
                expected_values=contract.prohibited_authority_profiles,
                actual_values=prohibited,
            )
        )
    return tuple(sorted(witnesses, key=lambda witness: witness.clause_id))


def assess_policy_view(view: PolicyView) -> RelationAssessment:
    """Compute the admissible set using only declared contract/manifest fields.

    In Milestone 1, decisive clauses are the union of observed incompatibility
    witnesses. General decisiveness for the admissibility relation is deliberately deferred.
    """

    contradictory_authorities = set(view.contract.accepted_authority_profiles).intersection(
        view.contract.prohibited_authority_profiles
    )
    if contradictory_authorities:
        return RelationAssessment(
            oracle_state=OracleState.CONTRACT_INVALID,
            admissible_tool_ids=(),
            decisive_clause_ids=(CONTRACT_CONSISTENCY_CLAUSE,),
            expected_decision=DecisionKind.INVALID_CONTRACT,
            witnesses_by_tool={},
        )

    witnesses_by_tool = {tool.tool_id: _tool_witnesses(view, tool) for tool in view.tools}
    admissible_tool_ids = tuple(
        sorted(tool_id for tool_id, witnesses in witnesses_by_tool.items() if not witnesses)
    )
    decisive_clause_ids = tuple(
        sorted(
            {witness.clause_id for witnesses in witnesses_by_tool.values() for witness in witnesses}
        )
    )
    if len(admissible_tool_ids) == 1:
        oracle_state = OracleState.UNIQUE_ADMISSIBLE
        expected_decision = DecisionKind.SELECT
    elif len(admissible_tool_ids) > 1:
        oracle_state = OracleState.MULTIPLE_ADMISSIBLE
        expected_decision = DecisionKind.INDETERMINATE
    else:
        oracle_state = OracleState.NO_ADMISSIBLE
        expected_decision = DecisionKind.NO_TOOL
    return RelationAssessment(
        oracle_state=oracle_state,
        admissible_tool_ids=admissible_tool_ids,
        decisive_clause_ids=decisive_clause_ids,
        expected_decision=expected_decision,
        witnesses_by_tool=witnesses_by_tool,
    )


def evaluation_unit_invalid_reasons(
    view: PolicyView, oracle: OracleRecord, relation: RelationAssessment
) -> tuple[str, ...]:
    """Expose fixture/oracle disagreements without converting them to policy errors."""

    reasons: list[str] = []
    if view.scenario_id != oracle.scenario_id:
        reasons.append("scenario_id mismatch between policy view and oracle")
    if oracle.oracle_state is OracleState.EVALUATION_UNIT_INVALID:
        reasons.append("oracle record declares the evaluation unit invalid")
    elif oracle.oracle_state is not relation.oracle_state:
        reasons.append(
            f"oracle_state mismatch: stored={oracle.oracle_state} computed={relation.oracle_state}"
        )
    if oracle.admissible_tool_ids != relation.admissible_tool_ids:
        reasons.append("admissible_tool_ids mismatch between oracle and relation checker")
    if oracle.decisive_clause_ids != relation.decisive_clause_ids:
        reasons.append("decisive_clause_ids mismatch between oracle and relation checker")
    if oracle.expected_decision is not relation.expected_decision:
        reasons.append("expected_decision mismatch between oracle and relation checker")
    return tuple(reasons)
