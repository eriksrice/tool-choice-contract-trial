"""Deterministic v2 declared-manifest relation checker."""

from __future__ import annotations

from dataclasses import dataclass

from .v2_models import (
    ClauseWitnessV2,
    DecisionKindV2,
    FailureCodeV2,
    OracleStateV2,
    PolicyViewV2,
    ToolManifestV2,
)
from .v2_registry import (
    AUTHORITY_REQUIREMENT_V2,
    CAPABILITY_REQUIREMENT_V2,
    INPUT_REQUIREMENT_V2,
    OUTPUT_CITATIONS_V2,
    OUTPUT_REQUIREMENT_V2,
    TOOL_PROHIBITION_V2,
    V2_RELATION_CLAUSE_REGISTRY,
)


@dataclass(frozen=True)
class RelationAssessmentV2:
    oracle_state: OracleStateV2
    admissible_tool_ids: tuple[str, ...]
    expected_decision: DecisionKindV2
    witnesses: tuple[ClauseWitnessV2, ...]
    contract_invalid_reasons: tuple[str, ...]


def _witness(
    *,
    clause_id: str,
    failure_code: FailureCodeV2,
    tool_id: str,
    expected_values: tuple[str, ...],
    actual_values: tuple[str, ...],
) -> ClauseWitnessV2:
    clause = V2_RELATION_CLAUSE_REGISTRY[clause_id]
    return ClauseWitnessV2(
        clause_id=clause_id,
        failure_code=failure_code,
        tool_id=tool_id,
        contract_fields=clause.contract_fields,
        manifest_fields=clause.manifest_fields,
        expected_values=expected_values,
        actual_values=actual_values,
    )


def _tool_witnesses_v2(view: PolicyViewV2, tool: ToolManifestV2) -> tuple[ClauseWitnessV2, ...]:
    contract = view.contract
    witnesses: list[ClauseWitnessV2] = []

    missing_capabilities = tuple(
        capability
        for capability in contract.required_capabilities
        if capability not in tool.capabilities
    )
    if missing_capabilities:
        witnesses.append(
            _witness(
                clause_id=CAPABILITY_REQUIREMENT_V2,
                failure_code=FailureCodeV2.CAPABILITY_MISMATCH,
                tool_id=tool.tool_id,
                expected_values=missing_capabilities,
                actual_values=tool.capabilities,
            )
        )

    if not set(contract.accepted_authority_profiles).intersection(tool.authority_profiles):
        witnesses.append(
            _witness(
                clause_id=AUTHORITY_REQUIREMENT_V2,
                failure_code=FailureCodeV2.AUTHORITY_MISMATCH,
                tool_id=tool.tool_id,
                expected_values=contract.accepted_authority_profiles,
                actual_values=tool.authority_profiles,
            )
        )

    missing_input_profiles = tuple(
        profile
        for profile in contract.required_input_profiles
        if profile not in tool.accepted_input_profiles
    )
    if missing_input_profiles:
        witnesses.append(
            _witness(
                clause_id=INPUT_REQUIREMENT_V2,
                failure_code=FailureCodeV2.INPUT_CONTRACT_MISMATCH,
                tool_id=tool.tool_id,
                expected_values=missing_input_profiles,
                actual_values=tool.accepted_input_profiles,
            )
        )

    missing_output_profiles = tuple(
        profile
        for profile in contract.required_output_profiles
        if profile not in tool.produced_output_profiles
    )
    if missing_output_profiles:
        witnesses.append(
            _witness(
                clause_id=OUTPUT_REQUIREMENT_V2,
                failure_code=FailureCodeV2.OUTPUT_CONTRACT_MISMATCH,
                tool_id=tool.tool_id,
                expected_values=missing_output_profiles,
                actual_values=tool.produced_output_profiles,
            )
        )

    if contract.citations_required and not tool.provides_citations:
        witnesses.append(
            _witness(
                clause_id=OUTPUT_CITATIONS_V2,
                failure_code=FailureCodeV2.OUTPUT_CONTRACT_MISMATCH,
                tool_id=tool.tool_id,
                expected_values=("citations_provided",),
                actual_values=("citations_unavailable",),
            )
        )

    if tool.tool_id in contract.forbidden_tool_ids:
        witnesses.append(
            _witness(
                clause_id=TOOL_PROHIBITION_V2,
                failure_code=FailureCodeV2.EXPLICIT_PROHIBITION,
                tool_id=tool.tool_id,
                expected_values=("tool_not_forbidden",),
                actual_values=(tool.tool_id,),
            )
        )

    return tuple(sorted(witnesses, key=lambda item: item.clause_id))


def assess_policy_view_v2(view: PolicyViewV2) -> RelationAssessmentV2:
    """Compute the v2 relation using policy-visible contract and manifest fields only."""

    available_tool_ids = {tool.tool_id for tool in view.tools}
    unavailable_forbidden_ids = tuple(
        sorted(set(view.contract.forbidden_tool_ids) - available_tool_ids)
    )
    if unavailable_forbidden_ids:
        return RelationAssessmentV2(
            oracle_state=OracleStateV2.CONTRACT_INVALID,
            admissible_tool_ids=(),
            expected_decision=DecisionKindV2.INVALID_CONTRACT,
            witnesses=(),
            contract_invalid_reasons=tuple(
                f"forbidden tool ID is unavailable: {tool_id}"
                for tool_id in unavailable_forbidden_ids
            ),
        )

    witnesses_by_tool = {
        tool.tool_id: _tool_witnesses_v2(view, tool)
        for tool in sorted(view.tools, key=lambda item: item.tool_id)
    }
    admissible_tool_ids = tuple(
        tool_id for tool_id, witnesses in witnesses_by_tool.items() if not witnesses
    )
    witnesses = tuple(
        witness for tool_id in sorted(witnesses_by_tool) for witness in witnesses_by_tool[tool_id]
    )

    if len(admissible_tool_ids) == 1:
        oracle_state = OracleStateV2.UNIQUE_ADMISSIBLE
        expected_decision = DecisionKindV2.SELECT
    elif len(admissible_tool_ids) > 1:
        oracle_state = OracleStateV2.MULTIPLE_ADMISSIBLE
        expected_decision = DecisionKindV2.INDETERMINATE
    else:
        oracle_state = OracleStateV2.NO_ADMISSIBLE
        expected_decision = DecisionKindV2.NO_TOOL

    return RelationAssessmentV2(
        oracle_state=oracle_state,
        admissible_tool_ids=admissible_tool_ids,
        expected_decision=expected_decision,
        witnesses=witnesses,
        contract_invalid_reasons=(),
    )
