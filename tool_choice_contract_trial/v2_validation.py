"""Independent v2 oracle-candidate comparison and provisional manifest assembly."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .errors import ArtifactIntegrityError
from .serialization import canonical_hash, canonical_json, write_jsonl
from .v2_models import (
    V2_SCHEMA_VERSION,
    BundleStatusV2,
    ComputedStateCountsV2,
    EvaluationUnitStatusV2,
    OracleExpectationV2,
    OracleReviewDispositionV2,
    OracleReviewRecordV2,
    OracleStateV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
    ReviewReadinessV2,
    ScenarioArtifactRecordV2,
)
from .v2_registry import V2_RELATION_REGISTRY_HASH
from .v2_relation import RelationAssessmentV2, assess_policy_view_v2


def _unique_by_scenario[V2Artifact: BaseModel](
    artifacts: Iterable[V2Artifact],
    artifact_name: str,
) -> dict[str, V2Artifact]:
    rows = tuple(artifacts)
    result = {str(row.scenario_id): row for row in rows}  # type: ignore[attr-defined]
    if len(result) != len(rows):
        raise ArtifactIntegrityError(f"duplicate {artifact_name} scenario_id values")
    return result


def _policy_view_v2_artifact_data(view: PolicyViewV2) -> dict[str, Any]:
    return {
        "schema_version": view.schema_version,
        "scenario_id": view.scenario_id,
        "contract": view.contract.model_dump(mode="json"),
        "tools": [
            tool.model_dump(mode="json")
            for tool in sorted(view.tools, key=lambda item: item.tool_id)
        ],
    }


def policy_view_v2_artifact_hash(view: PolicyViewV2) -> str:
    return canonical_hash(_policy_view_v2_artifact_data(view))


def _bundle_hash(label: str, rows: Iterable[BaseModel]) -> str:
    ordered = sorted(
        rows,
        key=lambda row: str(row.scenario_id),  # type: ignore[attr-defined]
    )
    return canonical_hash({label: [row.model_dump(mode="json") for row in ordered]})


def _finding_for_scenario(
    *,
    view: PolicyViewV2,
    relation: RelationAssessmentV2,
    expectation: OracleExpectationV2 | None,
    review: OracleReviewRecordV2 | None,
) -> OracleValidationFindingV2:
    proposed_state = expectation.expected_oracle_state if expectation else None
    proposed_set = expectation.expected_admissible_tool_ids if expectation else ()
    proposed_decision = expectation.expected_decision if expectation else None
    proposed_selected_tool_id = expectation.expected_selected_tool_id if expectation else None
    state_matches = expectation is not None and proposed_state is relation.oracle_state
    set_matches = expectation is not None and proposed_set == relation.admissible_tool_ids
    decision_matches = expectation is not None and proposed_decision is relation.expected_decision

    invalid_reasons: list[str] = []
    if expectation is None:
        invalid_reasons.append("missing oracle expectation")
    if review is None:
        invalid_reasons.append("missing oracle review record")

    review_readiness = ReviewReadinessV2.INVALID_UNIT
    if review is not None:
        if review.disposition is OracleReviewDispositionV2.PENDING:
            review_readiness = ReviewReadinessV2.PENDING_REVIEW
        else:
            if review.review_performed_without_policy_outputs is not True:
                invalid_reasons.append(
                    "completed review did not establish policy-output independence"
                )

            if review.disposition is OracleReviewDispositionV2.AGREE:
                review_readiness = ReviewReadinessV2.REVIEW_COMPLETE
                if expectation is None:
                    invalid_reasons.append("review agreement has no linked expectation")
                else:
                    if (
                        review.reviewed_expected_state is not expectation.expected_oracle_state
                        or review.reviewed_admissible_tool_ids
                        != expectation.expected_admissible_tool_ids
                    ):
                        invalid_reasons.append(
                            "review claims agreement but reviewed values differ from the proposal"
                        )
                if (
                    review.reviewed_expected_state is not relation.oracle_state
                    or review.reviewed_admissible_tool_ids != relation.admissible_tool_ids
                ):
                    invalid_reasons.append(
                        "review agreement differs from the independently computed relation"
                    )
                if not (state_matches and set_matches and decision_matches):
                    invalid_reasons.append(
                        "proposed expectation differs from the independently computed relation"
                    )
            elif review.disposition is OracleReviewDispositionV2.DISAGREE:
                review_readiness = ReviewReadinessV2.ADJUDICATION_REQUIRED
                invalid_reasons.append("completed disagreement lacks adjudication")
            elif review.disposition is OracleReviewDispositionV2.ADJUDICATED:
                review_readiness = ReviewReadinessV2.ADJUDICATED
                if (
                    review.adjudicated_state is None
                    or review.adjudicated_admissible_tool_ids is None
                ):
                    invalid_reasons.append("adjudication is incomplete")
                elif (
                    review.adjudicated_state is not relation.oracle_state
                    or review.adjudicated_admissible_tool_ids != relation.admissible_tool_ids
                ):
                    invalid_reasons.append(
                        "adjudicated values differ from the independently computed relation"
                    )

    ordered_invalid_reasons = tuple(sorted(set(invalid_reasons)))
    evaluation_status = (
        EvaluationUnitStatusV2.INVALID
        if ordered_invalid_reasons
        else EvaluationUnitStatusV2.SCOREABLE
    )
    completed_and_coherent = (
        evaluation_status is EvaluationUnitStatusV2.SCOREABLE
        and review is not None
        and review.disposition
        in {
            OracleReviewDispositionV2.AGREE,
            OracleReviewDispositionV2.ADJUDICATED,
        }
    )

    return OracleValidationFindingV2(
        scenario_id=view.scenario_id,
        scenario_hash=policy_view_v2_artifact_hash(view),
        expectation_hash=canonical_hash(expectation) if expectation else None,
        review_hash=canonical_hash(review) if review else None,
        relation_registry_hash=V2_RELATION_REGISTRY_HASH,
        computed_oracle_state=relation.oracle_state,
        computed_admissible_tool_ids=relation.admissible_tool_ids,
        computed_expected_decision=relation.expected_decision,
        relation_witnesses=relation.witnesses,
        contract_invalid_reasons=relation.contract_invalid_reasons,
        proposed_oracle_state=proposed_state,
        proposed_admissible_tool_ids=proposed_set,
        proposed_expected_decision=proposed_decision,
        proposed_selected_tool_id=proposed_selected_tool_id,
        state_matches_expectation=state_matches,
        admissible_set_matches_expectation=set_matches,
        decision_matches_expectation=decision_matches,
        expectation_matches_relation=state_matches and set_matches and decision_matches,
        review_disposition=review.disposition if review else None,
        review_readiness=review_readiness,
        evaluation_unit_status=evaluation_status,
        invalid_unit_reasons=ordered_invalid_reasons,
        ready_for_scoring=completed_and_coherent,
        ready_for_freeze=completed_and_coherent,
    )


def validate_oracle_candidates_v2(
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
) -> tuple[OracleValidationFindingV2, ...]:
    """Compute relations first, then compare them with evaluator-only authoring artifacts."""

    views_by_id = _unique_by_scenario(policy_views, "v2 policy view")

    relations_by_id = {
        scenario_id: assess_policy_view_v2(view)
        for scenario_id, view in sorted(views_by_id.items())
    }

    expectations_by_id = _unique_by_scenario(expectations, "v2 oracle expectation")
    reviews_by_id = _unique_by_scenario(reviews, "v2 oracle review")
    scenario_ids = set(views_by_id)
    extra_expectations = sorted(set(expectations_by_id) - scenario_ids)
    extra_reviews = sorted(set(reviews_by_id) - scenario_ids)
    if extra_expectations:
        raise ArtifactIntegrityError(
            f"oracle expectations reference unknown v2 scenarios: {extra_expectations}"
        )
    if extra_reviews:
        raise ArtifactIntegrityError(
            f"oracle reviews reference unknown v2 scenarios: {extra_reviews}"
        )

    return tuple(
        _finding_for_scenario(
            view=views_by_id[scenario_id],
            relation=relations_by_id[scenario_id],
            expectation=expectations_by_id.get(scenario_id),
            review=reviews_by_id.get(scenario_id),
        )
        for scenario_id in sorted(views_by_id)
    )


def build_provisional_manifest_v2(
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
    findings: Iterable[OracleValidationFindingV2],
) -> ProvisionalBundleManifestV2:
    view_rows = tuple(sorted(policy_views, key=lambda row: row.scenario_id))
    expectation_rows = tuple(sorted(expectations, key=lambda row: row.scenario_id))
    review_rows = tuple(sorted(reviews, key=lambda row: row.scenario_id))
    finding_rows = tuple(sorted(findings, key=lambda row: row.scenario_id))
    views_by_id = _unique_by_scenario(view_rows, "v2 policy view")
    expectations_by_id = _unique_by_scenario(expectation_rows, "v2 oracle expectation")
    reviews_by_id = _unique_by_scenario(review_rows, "v2 oracle review")
    findings_by_id = _unique_by_scenario(finding_rows, "v2 oracle validation finding")
    if set(findings_by_id) != set(views_by_id):
        raise ArtifactIntegrityError("v2 finding scenario set does not match policy views")

    scenario_artifacts = tuple(
        ScenarioArtifactRecordV2(
            scenario_id=scenario_id,
            scenario_hash=policy_view_v2_artifact_hash(views_by_id[scenario_id]),
            expectation_hash=(
                canonical_hash(expectations_by_id[scenario_id])
                if scenario_id in expectations_by_id
                else None
            ),
            review_hash=(
                canonical_hash(reviews_by_id[scenario_id]) if scenario_id in reviews_by_id else None
            ),
            finding_hash=canonical_hash(findings_by_id[scenario_id]),
        )
        for scenario_id in sorted(views_by_id)
    )
    state_counts = ComputedStateCountsV2(
        unique_admissible=sum(
            finding.computed_oracle_state is OracleStateV2.UNIQUE_ADMISSIBLE
            for finding in finding_rows
        ),
        multiple_admissible=sum(
            finding.computed_oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE
            for finding in finding_rows
        ),
        no_admissible=sum(
            finding.computed_oracle_state is OracleStateV2.NO_ADMISSIBLE for finding in finding_rows
        ),
        contract_invalid=sum(
            finding.computed_oracle_state is OracleStateV2.CONTRACT_INVALID
            for finding in finding_rows
        ),
    )

    return ProvisionalBundleManifestV2(
        artifact_schema_versions=(V2_SCHEMA_VERSION,),
        scenario_artifacts=scenario_artifacts,
        scenario_bundle_hash=canonical_hash(
            {"policy_views_v2": [_policy_view_v2_artifact_data(view) for view in view_rows]}
        ),
        expectation_bundle_hash=_bundle_hash("oracle_expectations_v2", expectation_rows),
        review_bundle_hash=_bundle_hash("oracle_reviews_v2", review_rows),
        relation_registry_hash=V2_RELATION_REGISTRY_HASH,
        computed_state_counts=state_counts,
        pending_review_count=sum(
            finding.review_disposition is OracleReviewDispositionV2.PENDING
            for finding in finding_rows
        ),
        invalid_unit_count=sum(
            finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
            for finding in finding_rows
        ),
        contract_invalid_count=state_counts.contract_invalid,
        bundle_status=BundleStatusV2.PROVISIONAL_REVIEW_CANDIDATE,
    )


def write_provisional_manifest_v2(path: Path, manifest: ProvisionalBundleManifestV2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(manifest) + "\n", encoding="utf-8", newline="\n")


def write_invalid_unit_register_v2(
    path: Path,
    findings: Iterable[OracleValidationFindingV2],
) -> None:
    write_jsonl(
        path,
        (
            finding
            for finding in sorted(findings, key=lambda row: row.scenario_id)
            if finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
        ),
    )
