"""Pure Markdown review-packet projection for v2 oracle candidates."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .errors import ArtifactIntegrityError
from .v2_models import (
    OracleExpectationV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
)


def _values(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_oracle_review_packet_v2(
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    findings: Iterable[OracleValidationFindingV2],
    manifest: ProvisionalBundleManifestV2,
) -> str:
    """Render only validated v2 policy views, expectations, findings, and manifest values."""

    view_rows = tuple(policy_views)
    expectation_rows = tuple(expectations)
    finding_rows = tuple(sorted(findings, key=lambda row: row.scenario_id))
    views_by_id = {view.scenario_id: view for view in view_rows}
    expectations_by_id = {expectation.scenario_id: expectation for expectation in expectation_rows}
    if len(views_by_id) != len(view_rows):
        raise ArtifactIntegrityError("duplicate policy view in review packet")
    if len(expectations_by_id) != len(expectation_rows):
        raise ArtifactIntegrityError("duplicate expectation in review packet")
    if {finding.scenario_id for finding in finding_rows} != set(views_by_id):
        raise ArtifactIntegrityError("review packet finding scenario set is incomplete")

    lines = [
        "# Tool Choice Contract Trial — Milestone 2B Oracle Review Packet",
        "",
        "> Status: provisional review candidate. Proposed expectations are deterministically "
        "cross-checked but not independently reviewed, adjudicated, or frozen.",
        "",
        "## Bundle summary",
        "",
        f"- Bundle status: `{manifest.bundle_status.value}`",
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
        family_label = expectation.family_label if expectation else "Missing expectation"
        variant_label = expectation.variant_label if expectation else "Missing expectation"
        review_disposition = (
            finding.review_disposition.value if finding.review_disposition else "MISSING"
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
                f"{'required' if contract.citations_required else 'not required'}; forbidden "
                f"{_values(contract.forbidden_tool_ids)}.",
                "- Available manifests:",
            ]
        )
        for tool in sorted(view.tools, key=lambda item: item.tool_id):
            lines.append(
                f"  - `{tool.tool_id}`: inputs {_values(tool.accepted_input_profiles)}; "
                f"outputs {_values(tool.produced_output_profiles)}; citations "
                f"{'yes' if tool.provides_citations else 'no'}."
            )
        lines.extend(
            [
                "- Computed relation: "
                f"`{finding.computed_oracle_state.value}` with "
                f"{_values(finding.computed_admissible_tool_ids)}; decision "
                f"`{finding.computed_expected_decision.value}`.",
                "- Proposed expectation: "
                + (
                    f"`{finding.proposed_oracle_state.value}` with "
                    f"{_values(finding.proposed_admissible_tool_ids)}; decision "
                    f"`{finding.proposed_expected_decision.value}`."
                    if finding.proposed_oracle_state and finding.proposed_expected_decision
                    else "missing."
                ),
                "- Proposal matches computed relation: "
                f"{_yes_no(finding.expectation_matches_relation)}",
                f"- Review: `{review_disposition}`; readiness `{finding.review_readiness.value}`.",
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
            "Review the proposed state, admissible set, and rationale without policy outputs. "
            "Record agreement or disagreement in the separate review artifact; disagreements "
            "require adjudication before an evaluation unit can become coherent.",
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
    findings: Iterable[OracleValidationFindingV2],
    manifest: ProvisionalBundleManifestV2,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_oracle_review_packet_v2(policy_views, expectations, findings, manifest),
        encoding="utf-8",
        newline="\n",
    )
