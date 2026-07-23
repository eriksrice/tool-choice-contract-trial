"""Per-case scoring and clause-level diagnostics."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import ArtifactIntegrityError
from .models import (
    FAILURE_PRECEDENCE_INDEX,
    ClauseWitness,
    DecisionKind,
    EvaluationContext,
    EvaluationResult,
    EvaluationUnitStatus,
    FailureCode,
    OracleRecord,
    OracleState,
    PolicyOutputStatus,
    PolicyView,
    ScenarioMetadata,
    SelectedToolAdmissibility,
    ToolDecision,
    WitnessScope,
    derive_strict_contract_outcome,
)
from .oracle import (
    CONTRACT_CONSISTENCY_CLAUSE,
    RelationAssessment,
    assess_policy_view,
    evaluation_unit_invalid_reasons,
)
from .serialization import canonical_hash


def _ordered_failures(failures: Iterable[FailureCode]) -> tuple[FailureCode, ...]:
    return tuple(sorted(set(failures), key=FAILURE_PRECEDENCE_INDEX.__getitem__))


def _ordered_witnesses(
    witnesses: Iterable[ClauseWitness],
) -> tuple[ClauseWitness, ...]:
    return tuple(
        sorted(
            witnesses,
            key=lambda witness: (
                witness.clause_id,
                FAILURE_PRECEDENCE_INDEX[witness.failure_code],
                witness.tool_id or "",
            ),
        )
    )


def _policy_witness(
    clause_id: str,
    failure_code: FailureCode,
    expected_values: tuple[str, ...],
    actual_values: tuple[str, ...],
) -> ClauseWitness:
    return ClauseWitness(
        clause_id=clause_id,
        failure_code=failure_code,
        scope=WitnessScope.POLICY_OUTPUT,
        expected_values=expected_values,
        actual_values=actual_values,
    )


def _contract_witness(
    decision: ToolDecision,
    expected: DecisionKind,
) -> ClauseWitness:
    return ClauseWitness(
        clause_id=CONTRACT_CONSISTENCY_CLAUSE,
        failure_code=FailureCode.CONTRACT_DEFECT_IGNORED,
        scope=WitnessScope.CONTRACT,
        expected_values=(expected.value,),
        actual_values=(decision.decision.value,),
    )


def _unknown_tool_witness(decision: ToolDecision, known_tool_ids: set[str]) -> ClauseWitness:
    return ClauseWitness(
        clause_id="decision.known_tool",
        failure_code=FailureCode.UNKNOWN_TOOL,
        scope=WitnessScope.SELECTED_TOOL,
        tool_id=decision.selected_tool_id,
        expected_values=tuple(sorted(known_tool_ids)),
        actual_values=(decision.selected_tool_id or "missing",),
    )


def _context(view: PolicyView, metadata: ScenarioMetadata) -> EvaluationContext:
    return EvaluationContext(
        family_id=metadata.family_id,
        family_label=metadata.family_label,
        variant_label=metadata.variant_label,
        comparison_group_id=metadata.comparison_group_id,
        available_tool_ids=tuple(sorted(tool.tool_id for tool in view.tools)),
        task_summary=view.contract.task_summary,
        required_capabilities=view.contract.required_capabilities,
        accepted_authority_profiles=view.contract.accepted_authority_profiles,
        citations_required=view.contract.citations_required,
    )


def _selected_admissibility(
    decision: ToolDecision | None,
    relation: RelationAssessment,
) -> SelectedToolAdmissibility:
    if decision is None or decision.decision is not DecisionKind.SELECT:
        return SelectedToolAdmissibility.NOT_APPLICABLE
    if decision.selected_tool_id in relation.admissible_tool_ids:
        return SelectedToolAdmissibility.ADMISSIBLE
    return SelectedToolAdmissibility.INADMISSIBLE


def _result(
    *,
    view: PolicyView,
    metadata: ScenarioMetadata,
    oracle: OracleRecord,
    decision: ToolDecision | None,
    malformed_policy_id: str,
    evaluation_unit_status: EvaluationUnitStatus,
    policy_output_status: PolicyOutputStatus,
    oracle_state: OracleState,
    admissible_tool_ids: tuple[str, ...],
    decisive_clause_ids: tuple[str, ...],
    selected_tool_admissibility: SelectedToolAdmissibility,
    witnesses: list[ClauseWitness],
    evaluation_invalid_reasons: tuple[str, ...],
) -> EvaluationResult:
    ordered_witnesses = _ordered_witnesses(witnesses)
    failure_codes = _ordered_failures(witness.failure_code for witness in ordered_witnesses)
    decision_payload = decision or {
        "scenario_id": view.scenario_id,
        "policy_id": malformed_policy_id,
        "policy_output_status": PolicyOutputStatus.MALFORMED,
    }
    policy_decision = decision.decision if decision is not None else None
    selected_tool_id = decision.selected_tool_id if decision is not None else None
    strict_contract_outcome = derive_strict_contract_outcome(
        evaluation_unit_status=evaluation_unit_status,
        policy_output_status=policy_output_status,
        oracle_state=oracle_state,
        policy_decision=policy_decision,
        selected_tool_id=selected_tool_id,
        admissible_tool_ids=admissible_tool_ids,
    )
    return EvaluationResult(
        scenario_id=view.scenario_id,
        context=_context(view, metadata),
        policy_id=decision.policy_id if decision is not None else malformed_policy_id,
        evaluation_unit_status=evaluation_unit_status,
        policy_output_status=policy_output_status,
        oracle_state=oracle_state,
        admissible_tool_ids=admissible_tool_ids,
        decisive_clause_ids=decisive_clause_ids,
        policy_decision=policy_decision,
        selected_tool_id=selected_tool_id,
        selected_tool_admissibility=selected_tool_admissibility,
        strict_contract_outcome=strict_contract_outcome,
        violated_clause_ids=tuple(sorted({witness.clause_id for witness in ordered_witnesses})),
        violation_witnesses=ordered_witnesses,
        failure_codes=failure_codes,
        primary_failure_code=failure_codes[0] if failure_codes else None,
        evaluation_invalid_reasons=evaluation_invalid_reasons,
        scenario_hash=canonical_hash(view),
        metadata_hash=canonical_hash(metadata),
        oracle_hash=canonical_hash(oracle),
        decision_hash=canonical_hash(decision_payload),
    )


def evaluate_case(
    view: PolicyView,
    metadata: ScenarioMetadata,
    oracle: OracleRecord,
    decision: ToolDecision | None,
    *,
    malformed_policy_id: str = "normalized_malformed_policy",
) -> EvaluationResult:
    """Evaluate one normalized policy observation without executing a tool.

    Stored replay rows are schema-valid before this function is called. ``None``
    represents a normalized malformed observation that a future adapter could
    produce; the Milestone 1 replay loader does not recover malformed rows.
    """

    if metadata.scenario_id != view.scenario_id:
        raise ArtifactIntegrityError("scenario metadata scenario_id does not match policy view")
    if oracle.scenario_id != view.scenario_id:
        raise ArtifactIntegrityError("oracle scenario_id does not match policy view")
    if decision is not None and decision.scenario_id != view.scenario_id:
        raise ArtifactIntegrityError("decision scenario_id does not match policy view")

    relation = assess_policy_view(view)
    invalid_reasons = evaluation_unit_invalid_reasons(view, oracle, relation)
    known_tool_ids = {tool.tool_id for tool in view.tools}
    policy_output_status = (
        PolicyOutputStatus.MALFORMED
        if decision is None
        else PolicyOutputStatus.UNKNOWN_TOOL
        if (
            decision.decision is DecisionKind.SELECT
            and decision.selected_tool_id not in known_tool_ids
        )
        else PolicyOutputStatus.VALID
    )
    witnesses: list[ClauseWitness] = []
    if decision is None:
        witnesses.append(
            _policy_witness(
                "decision.schema",
                FailureCode.MALFORMED_DECISION,
                ("normalized_schema_valid_decision",),
                ("malformed_provider_output",),
            )
        )
    elif policy_output_status is PolicyOutputStatus.UNKNOWN_TOOL:
        witnesses.append(_unknown_tool_witness(decision, known_tool_ids))

    if invalid_reasons:
        return _result(
            view=view,
            metadata=metadata,
            oracle=oracle,
            decision=decision,
            malformed_policy_id=malformed_policy_id,
            evaluation_unit_status=EvaluationUnitStatus.INVALID,
            policy_output_status=policy_output_status,
            oracle_state=OracleState.EVALUATION_UNIT_INVALID,
            admissible_tool_ids=(),
            decisive_clause_ids=relation.decisive_clause_ids,
            selected_tool_admissibility=SelectedToolAdmissibility.NOT_APPLICABLE,
            witnesses=witnesses,
            evaluation_invalid_reasons=invalid_reasons,
        )

    selected_admissibility = _selected_admissibility(decision, relation)

    if decision is None:
        pass
    elif relation.oracle_state is OracleState.CONTRACT_INVALID:
        if decision.decision is not DecisionKind.INVALID_CONTRACT:
            witnesses.append(_contract_witness(decision, DecisionKind.INVALID_CONTRACT))
    elif relation.oracle_state is OracleState.UNIQUE_ADMISSIBLE:
        if decision.decision is DecisionKind.SELECT:
            if (
                decision.selected_tool_id != relation.admissible_tool_ids[0]
                and decision.selected_tool_id in known_tool_ids
            ):
                witnesses.extend(relation.witnesses_by_tool[decision.selected_tool_id or ""])
        elif decision.decision is DecisionKind.INVALID_CONTRACT:
            witnesses.append(
                _policy_witness(
                    "decision.contract_valid",
                    FailureCode.INVALID_CONTRACT_MISCLASSIFICATION,
                    (DecisionKind.SELECT.value,),
                    (DecisionKind.INVALID_CONTRACT.value,),
                )
            )
        else:
            witnesses.append(
                _policy_witness(
                    "decision.selection_required",
                    FailureCode.UNSUPPORTED_ABSTENTION,
                    (DecisionKind.SELECT.value,),
                    (decision.decision.value,),
                )
            )
    elif relation.oracle_state is OracleState.NO_ADMISSIBLE:
        if decision.decision is DecisionKind.NO_TOOL:
            pass
        elif decision.decision is DecisionKind.SELECT:
            witnesses.append(
                _policy_witness(
                    "decision.no_admissible_tool",
                    FailureCode.FORCED_SELECTION,
                    (DecisionKind.NO_TOOL.value,),
                    (DecisionKind.SELECT.value,),
                )
            )
            if decision.selected_tool_id in known_tool_ids:
                witnesses.extend(relation.witnesses_by_tool[decision.selected_tool_id or ""])
        elif decision.decision is DecisionKind.INVALID_CONTRACT:
            witnesses.append(
                _policy_witness(
                    "decision.contract_valid",
                    FailureCode.INVALID_CONTRACT_MISCLASSIFICATION,
                    (DecisionKind.NO_TOOL.value,),
                    (DecisionKind.INVALID_CONTRACT.value,),
                )
            )
        else:
            witnesses.append(
                _policy_witness(
                    "decision.no_tool_required",
                    FailureCode.UNSUPPORTED_ABSTENTION,
                    (DecisionKind.NO_TOOL.value,),
                    (decision.decision.value,),
                )
            )
    elif relation.oracle_state is OracleState.MULTIPLE_ADMISSIBLE:
        if decision.decision is DecisionKind.INDETERMINATE:
            pass
        elif decision.decision is DecisionKind.SELECT:
            witnesses.append(
                _policy_witness(
                    "decision.ambiguity_unresolved",
                    FailureCode.AMBIGUITY_FORCED_RESOLUTION,
                    (DecisionKind.INDETERMINATE.value,),
                    (DecisionKind.SELECT.value,),
                )
            )
            if (
                decision.selected_tool_id not in relation.admissible_tool_ids
                and decision.selected_tool_id in known_tool_ids
            ):
                witnesses.extend(relation.witnesses_by_tool[decision.selected_tool_id or ""])
        elif decision.decision is DecisionKind.INVALID_CONTRACT:
            witnesses.append(
                _policy_witness(
                    "decision.contract_valid",
                    FailureCode.INVALID_CONTRACT_MISCLASSIFICATION,
                    (DecisionKind.INDETERMINATE.value,),
                    (DecisionKind.INVALID_CONTRACT.value,),
                )
            )
        else:
            witnesses.append(
                _policy_witness(
                    "decision.indeterminate_required",
                    FailureCode.UNSUPPORTED_ABSTENTION,
                    (DecisionKind.INDETERMINATE.value,),
                    (decision.decision.value,),
                )
            )

    return _result(
        view=view,
        metadata=metadata,
        oracle=oracle,
        decision=decision,
        malformed_policy_id=malformed_policy_id,
        evaluation_unit_status=EvaluationUnitStatus.SCOREABLE,
        policy_output_status=policy_output_status,
        oracle_state=relation.oracle_state,
        admissible_tool_ids=relation.admissible_tool_ids,
        decisive_clause_ids=relation.decisive_clause_ids,
        selected_tool_admissibility=selected_admissibility,
        witnesses=witnesses,
        evaluation_invalid_reasons=(),
    )
