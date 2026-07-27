"""Authoritative pure lifecycle semantics for v2 oracle-validation findings."""

from __future__ import annotations

from dataclasses import dataclass

from .v2_models import (
    DecisionKindV2,
    EvaluationUnitStatusV2,
    OracleReviewDispositionV2,
    OracleStateV2,
    ReviewReadinessV2,
)


@dataclass(frozen=True)
class OracleValidationEvidenceV2:
    expectation_present: bool
    review_present: bool
    computed_oracle_state: OracleStateV2
    computed_admissible_tool_ids: tuple[str, ...]
    computed_expected_decision: DecisionKindV2
    proposed_oracle_state: OracleStateV2 | None
    proposed_admissible_tool_ids: tuple[str, ...]
    proposed_expected_decision: DecisionKindV2 | None
    proposed_selected_tool_id: str | None
    review_disposition: OracleReviewDispositionV2 | None
    reviewed_expected_state: OracleStateV2 | None
    reviewed_admissible_tool_ids: tuple[str, ...] | None
    review_performed_without_policy_outputs: bool | None
    adjudicated_state: OracleStateV2 | None
    adjudicated_admissible_tool_ids: tuple[str, ...] | None


@dataclass(frozen=True)
class DerivedOracleValidationStateV2:
    state_matches_expectation: bool
    admissible_set_matches_expectation: bool
    decision_matches_expectation: bool
    expectation_matches_relation: bool
    review_readiness: ReviewReadinessV2
    evaluation_unit_status: EvaluationUnitStatusV2
    invalid_unit_reasons: tuple[str, ...]
    ready_for_scoring: bool
    ready_for_freeze: bool


def derive_oracle_validation_state_v2(
    evidence: OracleValidationEvidenceV2,
) -> DerivedOracleValidationStateV2:
    """Derive every lifecycle flag and status from source evidence exactly once."""

    state_matches = (
        evidence.expectation_present
        and evidence.proposed_oracle_state is evidence.computed_oracle_state
    )
    set_matches = (
        evidence.expectation_present
        and evidence.proposed_admissible_tool_ids == evidence.computed_admissible_tool_ids
    )
    computed_selected_tool_id = (
        evidence.computed_admissible_tool_ids[0]
        if evidence.computed_expected_decision is DecisionKindV2.SELECT
        else None
    )
    decision_matches = (
        evidence.expectation_present
        and evidence.proposed_expected_decision is evidence.computed_expected_decision
        and evidence.proposed_selected_tool_id == computed_selected_tool_id
    )
    expectation_matches = state_matches and set_matches and decision_matches

    invalid_reasons: list[str] = []
    if not evidence.expectation_present:
        invalid_reasons.append("missing oracle expectation")
    if not evidence.review_present:
        invalid_reasons.append("missing oracle review record")

    if not evidence.expectation_present or not evidence.review_present:
        review_readiness = ReviewReadinessV2.INVALID_UNIT
    elif evidence.review_disposition is OracleReviewDispositionV2.PENDING:
        review_readiness = ReviewReadinessV2.PENDING_REVIEW
    elif evidence.review_disposition is OracleReviewDispositionV2.AGREE:
        review_readiness = ReviewReadinessV2.REVIEW_COMPLETE
        if evidence.review_performed_without_policy_outputs is not True:
            invalid_reasons.append("completed review did not establish policy-output independence")
        if (
            evidence.reviewed_expected_state is None
            or evidence.reviewed_admissible_tool_ids is None
        ):
            invalid_reasons.append("completed review is missing reviewed state or admissible set")
        else:
            if (
                evidence.reviewed_expected_state is not evidence.proposed_oracle_state
                or evidence.reviewed_admissible_tool_ids != evidence.proposed_admissible_tool_ids
            ):
                invalid_reasons.append(
                    "review claims agreement but reviewed values differ from the proposal"
                )
            if (
                evidence.reviewed_expected_state is not evidence.computed_oracle_state
                or evidence.reviewed_admissible_tool_ids != evidence.computed_admissible_tool_ids
            ):
                invalid_reasons.append(
                    "review agreement differs from the independently computed relation"
                )
        if not expectation_matches:
            invalid_reasons.append(
                "proposed expectation differs from the independently computed relation"
            )
    elif evidence.review_disposition is OracleReviewDispositionV2.DISAGREE:
        review_readiness = ReviewReadinessV2.ADJUDICATION_REQUIRED
        if evidence.review_performed_without_policy_outputs is not True:
            invalid_reasons.append("completed review did not establish policy-output independence")
        if (
            evidence.reviewed_expected_state is None
            or evidence.reviewed_admissible_tool_ids is None
        ):
            invalid_reasons.append("completed review is missing reviewed state or admissible set")
        invalid_reasons.append("completed disagreement lacks adjudication")
    elif evidence.review_disposition is OracleReviewDispositionV2.ADJUDICATED:
        review_readiness = ReviewReadinessV2.ADJUDICATED
        if evidence.review_performed_without_policy_outputs is not True:
            invalid_reasons.append("completed review did not establish policy-output independence")
        if (
            evidence.reviewed_expected_state is None
            or evidence.reviewed_admissible_tool_ids is None
        ):
            invalid_reasons.append("completed review is missing reviewed state or admissible set")
        if evidence.adjudicated_state is None or evidence.adjudicated_admissible_tool_ids is None:
            invalid_reasons.append("adjudication is incomplete")
        elif (
            evidence.adjudicated_state is not evidence.computed_oracle_state
            or evidence.adjudicated_admissible_tool_ids != evidence.computed_admissible_tool_ids
        ):
            invalid_reasons.append(
                "adjudicated values differ from the independently computed relation"
            )
    else:
        review_readiness = ReviewReadinessV2.INVALID_UNIT
        invalid_reasons.append("review disposition is missing")

    ordered_reasons = tuple(sorted(set(invalid_reasons)))
    evaluation_status = (
        EvaluationUnitStatusV2.INVALID if ordered_reasons else EvaluationUnitStatusV2.SCOREABLE
    )
    ready = (
        evaluation_status is EvaluationUnitStatusV2.SCOREABLE
        and evidence.review_disposition
        in {
            OracleReviewDispositionV2.AGREE,
            OracleReviewDispositionV2.ADJUDICATED,
        }
    )
    return DerivedOracleValidationStateV2(
        state_matches_expectation=state_matches,
        admissible_set_matches_expectation=set_matches,
        decision_matches_expectation=decision_matches,
        expectation_matches_relation=expectation_matches,
        review_readiness=review_readiness,
        evaluation_unit_status=evaluation_status,
        invalid_unit_reasons=ordered_reasons,
        ready_for_scoring=ready,
        ready_for_freeze=ready,
    )
