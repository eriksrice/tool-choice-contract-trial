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
    ScenarioArtifactRecordV2,
)
from .v2_registry import V2_RELATION_REGISTRY_HASH
from .v2_relation import RelationAssessmentV2, assess_policy_view_v2
from .v2_semantics import OracleValidationEvidenceV2, derive_oracle_validation_state_v2


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
    if expectation is not None and expectation.scenario_id != view.scenario_id:
        raise ArtifactIntegrityError("v2 expectation linkage does not match the policy view")
    if review is not None and review.scenario_id != view.scenario_id:
        raise ArtifactIntegrityError("v2 review linkage does not match the policy view")

    proposed_state = expectation.expected_oracle_state if expectation else None
    proposed_set = expectation.expected_admissible_tool_ids if expectation else ()
    proposed_decision = expectation.expected_decision if expectation else None
    proposed_selected_tool_id = expectation.expected_selected_tool_id if expectation else None
    lifecycle = derive_oracle_validation_state_v2(
        OracleValidationEvidenceV2(
            expectation_present=expectation is not None,
            review_present=review is not None,
            computed_oracle_state=relation.oracle_state,
            computed_admissible_tool_ids=relation.admissible_tool_ids,
            computed_expected_decision=relation.expected_decision,
            proposed_oracle_state=proposed_state,
            proposed_admissible_tool_ids=proposed_set,
            proposed_expected_decision=proposed_decision,
            proposed_selected_tool_id=proposed_selected_tool_id,
            review_disposition=review.disposition if review else None,
            reviewed_expected_state=review.reviewed_expected_state if review else None,
            reviewed_admissible_tool_ids=(review.reviewed_admissible_tool_ids if review else None),
            review_performed_without_policy_outputs=(
                review.review_performed_without_policy_outputs if review else None
            ),
            adjudicated_state=review.adjudicated_state if review else None,
            adjudicated_admissible_tool_ids=(
                review.adjudicated_admissible_tool_ids if review else None
            ),
        )
    )

    return OracleValidationFindingV2(
        scenario_id=view.scenario_id,
        scenario_hash=policy_view_v2_artifact_hash(view),
        expectation_present=expectation is not None,
        review_present=review is not None,
        expectation_hash=canonical_hash(expectation) if expectation else None,
        review_hash=canonical_hash(review) if review else None,
        relation_registry_hash=V2_RELATION_REGISTRY_HASH,
        available_tool_ids=tuple(sorted(tool.tool_id for tool in view.tools)),
        computed_oracle_state=relation.oracle_state,
        computed_admissible_tool_ids=relation.admissible_tool_ids,
        computed_expected_decision=relation.expected_decision,
        relation_witnesses=relation.witnesses,
        contract_invalid_reasons=relation.contract_invalid_reasons,
        proposed_oracle_state=proposed_state,
        proposed_admissible_tool_ids=proposed_set,
        proposed_expected_decision=proposed_decision,
        proposed_selected_tool_id=proposed_selected_tool_id,
        state_matches_expectation=lifecycle.state_matches_expectation,
        admissible_set_matches_expectation=(lifecycle.admissible_set_matches_expectation),
        decision_matches_expectation=lifecycle.decision_matches_expectation,
        expectation_matches_relation=lifecycle.expectation_matches_relation,
        review_disposition=review.disposition if review else None,
        reviewed_expected_state=review.reviewed_expected_state if review else None,
        reviewed_admissible_tool_ids=(review.reviewed_admissible_tool_ids if review else None),
        review_performed_without_policy_outputs=(
            review.review_performed_without_policy_outputs if review else None
        ),
        adjudicated_state=review.adjudicated_state if review else None,
        adjudicated_admissible_tool_ids=(
            review.adjudicated_admissible_tool_ids if review else None
        ),
        review_readiness=lifecycle.review_readiness,
        evaluation_unit_status=lifecycle.evaluation_unit_status,
        invalid_unit_reasons=lifecycle.invalid_unit_reasons,
        ready_for_scoring=lifecycle.ready_for_scoring,
        ready_for_freeze=lifecycle.ready_for_freeze,
    )


def verify_oracle_validation_finding_v2(
    finding: OracleValidationFindingV2,
    policy_view: PolicyViewV2,
    expectation: OracleExpectationV2 | None,
    review: OracleReviewRecordV2 | None,
) -> None:
    """Verify a persisted finding by recomputing it from all source artifacts."""

    expected = _finding_for_scenario(
        view=policy_view,
        relation=assess_policy_view_v2(policy_view),
        expectation=expectation,
        review=review,
    )
    if finding != expected:
        supplied = finding.model_dump(mode="json")
        recomputed = expected.model_dump(mode="json")
        changed_fields = sorted(
            field_name
            for field_name in set(supplied) | set(recomputed)
            if supplied.get(field_name) != recomputed.get(field_name)
        )
        raise ArtifactIntegrityError(
            "v2 oracle validation finding differs from source-aware recomputation: "
            f"scenario={policy_view.scenario_id}, fields={changed_fields}"
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


def _assemble_provisional_manifest_v2(
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
    if not set(expectations_by_id).issubset(views_by_id):
        raise ArtifactIntegrityError("v2 expectation scenario set exceeds policy views")
    if not set(reviews_by_id).issubset(views_by_id):
        raise ArtifactIntegrityError("v2 review scenario set exceeds policy views")

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


def verify_provisional_manifest_v2(
    manifest: ProvisionalBundleManifestV2,
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
    findings: Iterable[OracleValidationFindingV2],
) -> None:
    """Verify a provisional manifest and every finding against source artifacts."""

    view_rows = tuple(policy_views)
    expectation_rows = tuple(expectations)
    review_rows = tuple(reviews)
    finding_rows = tuple(findings)
    views_by_id = _unique_by_scenario(view_rows, "v2 policy view")
    expectations_by_id = _unique_by_scenario(expectation_rows, "v2 oracle expectation")
    reviews_by_id = _unique_by_scenario(review_rows, "v2 oracle review")
    findings_by_id = _unique_by_scenario(finding_rows, "v2 oracle validation finding")
    if set(findings_by_id) != set(views_by_id):
        raise ArtifactIntegrityError("v2 finding scenario set does not match policy views")
    if not set(expectations_by_id).issubset(views_by_id):
        raise ArtifactIntegrityError("v2 expectation scenario set exceeds policy views")
    if not set(reviews_by_id).issubset(views_by_id):
        raise ArtifactIntegrityError("v2 review scenario set exceeds policy views")

    for scenario_id, view in sorted(views_by_id.items()):
        verify_oracle_validation_finding_v2(
            findings_by_id[scenario_id],
            view,
            expectations_by_id.get(scenario_id),
            reviews_by_id.get(scenario_id),
        )

    expected = _assemble_provisional_manifest_v2(
        view_rows,
        expectation_rows,
        review_rows,
        finding_rows,
    )
    if manifest != expected:
        supplied = manifest.model_dump(mode="json")
        recomputed = expected.model_dump(mode="json")
        changed_fields = sorted(
            field_name
            for field_name in set(supplied) | set(recomputed)
            if supplied.get(field_name) != recomputed.get(field_name)
        )
        raise ArtifactIntegrityError(
            "v2 provisional manifest differs from source-aware recomputation: "
            f"fields={changed_fields}"
        )


def build_provisional_manifest_v2(
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
    findings: Iterable[OracleValidationFindingV2],
) -> ProvisionalBundleManifestV2:
    """Construct and immediately source-verify the provisional v2 manifest."""

    view_rows = tuple(policy_views)
    expectation_rows = tuple(expectations)
    review_rows = tuple(reviews)
    finding_rows = tuple(findings)
    manifest = _assemble_provisional_manifest_v2(
        view_rows,
        expectation_rows,
        review_rows,
        finding_rows,
    )
    verify_provisional_manifest_v2(
        manifest,
        view_rows,
        expectation_rows,
        review_rows,
        finding_rows,
    )
    return manifest


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
