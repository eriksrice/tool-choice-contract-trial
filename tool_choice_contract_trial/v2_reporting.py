"""Pure Markdown review-packet projection for v2 oracle candidates."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .errors import ArtifactIntegrityError
from .v2_models import (
    OracleExpectationV2,
    OracleReviewDispositionV2,
    OracleReviewRecordV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
)
from .v2_validation import verify_provisional_manifest_v2


def _values(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "not recorded"
    return "yes" if value else "no"


def render_oracle_review_packet_v2(
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
    findings: Iterable[OracleValidationFindingV2],
    manifest: ProvisionalBundleManifestV2,
) -> str:
    """Render only validated v2 policy views, expectations, findings, and manifest values."""

    view_rows = tuple(policy_views)
    expectation_rows = tuple(expectations)
    review_rows = tuple(reviews)
    finding_rows = tuple(sorted(findings, key=lambda row: row.scenario_id))
    verify_provisional_manifest_v2(
        manifest,
        view_rows,
        expectation_rows,
        review_rows,
        finding_rows,
    )
    views_by_id = {view.scenario_id: view for view in view_rows}
    expectations_by_id = {expectation.scenario_id: expectation for expectation in expectation_rows}
    reviews_by_id = {review.scenario_id: review for review in review_rows}
    if len(views_by_id) != len(view_rows):
        raise ArtifactIntegrityError("duplicate policy view in review packet")
    if len(expectations_by_id) != len(expectation_rows):
        raise ArtifactIntegrityError("duplicate expectation in review packet")
    if len(reviews_by_id) != len(review_rows):
        raise ArtifactIntegrityError("duplicate review in review packet")
    if {finding.scenario_id for finding in finding_rows} != set(views_by_id):
        raise ArtifactIntegrityError("review packet finding scenario set is incomplete")
    agree_count = sum(
        review.disposition is OracleReviewDispositionV2.AGREE for review in review_rows
    )
    owner_review_count = sum(
        review.reviewer_role == "owner_reviewer"
        and review.disposition is not OracleReviewDispositionV2.PENDING
        for review in review_rows
    )
    independent_review_count = sum(
        review.reviewer_role == "independent_reviewer"
        and review.disposition is not OracleReviewDispositionV2.PENDING
        for review in review_rows
    )
    pending_scenario_ids = tuple(
        sorted(
            review.scenario_id
            for review in review_rows
            if review.disposition is OracleReviewDispositionV2.PENDING
        )
    )
    owner_review_statement = (
        f"complete for all {len(review_rows)} current candidates"
        if owner_review_count == len(review_rows)
        else f"complete for {owner_review_count} of {len(review_rows)} current candidates"
    )
    replacement_review = reviews_by_id.get("v2_scenario_012")
    if (
        not pending_scenario_ids
        and replacement_review is not None
        and replacement_review.disposition is OracleReviewDispositionV2.AGREE
    ):
        pending_review_statement = (
            "The replacement `v2_scenario_012` contradiction was approved during owner re-review."
        )
    elif not pending_scenario_ids:
        pending_review_statement = "No owner-review candidates are pending."
    elif pending_scenario_ids == ("v2_scenario_012",):
        pending_review_statement = "The replacement `v2_scenario_012` awaits owner re-review."
    else:
        pending_review_statement = (
            f"Pending owner-review candidates: {_values(pending_scenario_ids)}."
        )
    independent_review_statement = (
        "Independent review has not been performed."
        if independent_review_count == 0
        else f"Independent review is recorded for {independent_review_count} cases."
    )
    owner_review_instruction = (
        "Owner review is complete for all 12 current candidates, including replacement "
        "`v2_scenario_012`."
        if owner_review_count == len(review_rows)
        else "Owner review is not complete for all current candidates."
    )

    lines = [
        "# Tool Choice Contract Trial — Milestone 2B Oracle Review Packet",
        "",
        f"> Owner review: {owner_review_statement}; {agree_count} proposals accepted. "
        f"{pending_review_statement}",
        "",
        f"> {independent_review_statement} The bundle is not frozen, and no policy decisions "
        "were used.",
        "",
        "## Bundle summary",
        "",
        f"- Bundle status: `{manifest.bundle_status.value}`",
        f"- Artifact schema versions: {_values(manifest.artifact_schema_versions)}",
        f"- Scenario count: {len(manifest.scenario_artifacts)}",
        f"- Pending-review count: {manifest.pending_review_count}",
        f"- Evaluation-unit-invalid count: {manifest.invalid_unit_count}",
        f"- Computed contract-invalid count: {manifest.contract_invalid_count}",
        f"- Relation-registry hash: `{manifest.relation_registry_hash}`",
        "",
        "## Scenario review entries",
        "",
    ]

    for finding in finding_rows:
        view = views_by_id[finding.scenario_id]
        expectation = expectations_by_id.get(finding.scenario_id)
        review = reviews_by_id.get(finding.scenario_id)
        family_label = expectation.family_label if expectation else "Missing expectation"
        variant_label = expectation.variant_label if expectation else "Missing expectation"
        review_disposition = (
            finding.review_disposition.value if finding.review_disposition else "MISSING"
        )
        reviewed_relation = (
            f"`{review.reviewed_expected_state.value}` with "
            f"{_values(review.reviewed_admissible_tool_ids)}"
            if review
            and review.reviewed_expected_state is not None
            and review.reviewed_admissible_tool_ids is not None
            else "not recorded"
        )
        adjudication = (
            f"`{review.adjudicated_state.value}` with "
            f"{_values(review.adjudicated_admissible_tool_ids)}"
            if review
            and review.adjudicated_state is not None
            and review.adjudicated_admissible_tool_ids is not None
            else "none"
        )
        contract = view.contract
        lines.extend(
            [
                f"### `{finding.scenario_id}` — {variant_label}",
                "",
                f"- Family: {family_label}",
                f"- Task: {contract.task_summary}",
                "- Requirements: capabilities "
                f"{_values(contract.required_capabilities)}; authority "
                f"{_values(contract.accepted_authority_profiles)}; inputs "
                f"{_values(contract.required_input_profiles)}; outputs "
                f"{_values(contract.required_output_profiles)}; citations "
                f"{'required' if contract.citations_required else 'not required'}; required tool "
                f"{f'`{contract.required_tool_id}`' if contract.required_tool_id else 'none'}; "
                "forbidden "
                f"{_values(contract.forbidden_tool_ids)}.",
                "- Available manifests:",
            ]
        )
        for tool in sorted(view.tools, key=lambda item: item.tool_id):
            lines.append(
                f"  - `{tool.tool_id}`: capabilities {_values(tool.capabilities)}; "
                f"authority {_values(tool.authority_profiles)}; inputs "
                f"{_values(tool.accepted_input_profiles)}; "
                f"outputs {_values(tool.produced_output_profiles)}; citations "
                f"{'yes' if tool.provides_citations else 'no'}."
            )
        lines.append("- Relation witnesses:")
        if finding.relation_witnesses:
            for witness in finding.relation_witnesses:
                lines.append(
                    f"  - `{witness.tool_id}` / `{witness.clause_id}` "
                    f"(`{witness.failure_code.value}`): expected "
                    f"{_values(witness.expected_values)}; actual "
                    f"{_values(witness.actual_values)}."
                )
        else:
            lines.append("  - none")
        lines.extend(
            [
                "- Computed relation: "
                f"`{finding.computed_oracle_state.value}` with "
                f"{_values(finding.computed_admissible_tool_ids)}; decision "
                f"`{finding.computed_expected_decision.value}`.",
                f"- Contract-invalid reasons: {_values(finding.contract_invalid_reasons)}",
                "- Proposed expectation: "
                + (
                    f"`{finding.proposed_oracle_state.value}` with "
                    f"{_values(finding.proposed_admissible_tool_ids)}; decision "
                    f"`{finding.proposed_expected_decision.value}`."
                    if finding.proposed_oracle_state and finding.proposed_expected_decision
                    else "missing."
                ),
                "- Authoring rationale: "
                + (expectation.authoring_rationale if expectation else "missing."),
                "- Proposal matches computed relation: "
                f"{_yes_no(finding.expectation_matches_relation)}",
                f"- Reviewer role: `{review.reviewer_role if review else 'MISSING'}`",
                f"- Review: `{review_disposition}`; readiness `{finding.review_readiness.value}`.",
                f"- Reviewed relation: {reviewed_relation}.",
                "- Review performed without policy outputs: "
                f"{_yes_no(review.review_performed_without_policy_outputs if review else None)}",
                "- Review note: " + (review.review_notes if review else "missing."),
                f"- Adjudication: {adjudication}.",
                "- Classification: computed contract state "
                f"`{finding.computed_oracle_state.value}`; evaluation-unit status "
                f"`{finding.evaluation_unit_status.value}`.",
                f"- Invalid-unit reasons: {_values(finding.invalid_unit_reasons)}",
                f"- Ready for scoring: {_yes_no(finding.ready_for_scoring)}",
                f"- Ready for freeze: {_yes_no(finding.ready_for_freeze)}",
                "",
            ]
        )

    lines.extend(
        [
            "## Human review instructions",
            "",
            f"{owner_review_instruction} Independent review remains outstanding and must assess "
            "the proposed state, admissible set, and rationale without policy outputs. Any future "
            "disagreement would require separate adjudication.",
            "",
            "## Interpretation boundary",
            "",
            "- These twelve cases are proposed review candidates, not a frozen benchmark.",
            "- A computed `CONTRACT_INVALID` state comes only from the policy-visible contract; "
            "`EVALUATION_UNIT_INVALID` identifies defective authoring or review relationships.",
            "- No policy decisions, live models, tool execution, runtime outputs, or policy "
            "metrics are used here.",
            "- The controlled v2 pairs have not been processed by the v1 authority-only "
            "counterfactual analyzer.",
            "- No benchmark-performance, production, or cross-domain claim follows.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_oracle_review_packet_v2(
    path: Path,
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    reviews: Iterable[OracleReviewRecordV2],
    findings: Iterable[OracleValidationFindingV2],
    manifest: ProvisionalBundleManifestV2,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_oracle_review_packet_v2(
            policy_views,
            expectations,
            reviews,
            findings,
            manifest,
        ),
        encoding="utf-8",
        newline="\n",
    )
