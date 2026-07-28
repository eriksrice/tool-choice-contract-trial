"""Pure Markdown projection for validated blind model-review evidence."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .blind_model_review import verify_blind_model_review_evidence_v2
from .blind_model_review_models import (
    BlindModelReviewComparisonV2,
    BlindModelReviewProvenanceManifestV2,
    BlindModelReviewRecordV2,
)


def _values(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_blind_model_review_report_v2(
    records: Iterable[BlindModelReviewRecordV2],
    comparisons: Iterable[BlindModelReviewComparisonV2],
    provenance: BlindModelReviewProvenanceManifestV2,
) -> str:
    record_rows = tuple(sorted(records, key=lambda row: row.scenario_id))
    comparison_rows = tuple(sorted(comparisons, key=lambda row: row.scenario_id))
    verify_blind_model_review_evidence_v2(record_rows, comparison_rows, provenance)
    records_by_id = {record.scenario_id: record for record in record_rows}

    lines = [
        "# Tool Choice Contract Trial — Blind Independent Model Review",
        "",
        "> Evidence kind: `BLIND_INDEPENDENT_MODEL_REVIEW`. This is a blinded independent "
        "model review, not independent human review, owner review, adjudication, benchmark "
        "freeze, or policy evaluation.",
        "",
        f"> Owner review: {provenance.owner_agreement_count}/"
        f"{provenance.reviewed_case_count} agreement. Blind independent model review: "
        f"{provenance.full_agreement_count}/{provenance.reviewed_case_count} full agreement. "
        "The candidate remains provisional and unfrozen.",
        "",
        "## Provenance",
        "",
        f"- Review protocol: `{provenance.review_protocol_id}`",
        f"- Review protocol SHA-256: `{provenance.review_protocol_sha256}`",
        f"- Reviewer platform: `{provenance.reviewer_platform}`",
        f"- Review session type: `{provenance.review_session_type.value}`",
        f"- Exact model identifier: `{provenance.reviewer_model_identifier}`",
        "- Human reviewer: no",
        f"- Source commit: `{provenance.source_commit_sha}`",
        f"- Blind packet SHA-256: `{provenance.source_packet_sha256}`",
        f"- Private map SHA-256: `{provenance.private_map_sha256}`",
        f"- Raw response SHA-256: `{provenance.raw_review_sha256}`",
        "- Reviewer input: shuffled policy-visible cases with per-case aliased tool IDs.",
        f"- Withheld from reviewer: {_values(provenance.withheld_answer_bearing_sources)}.",
        "- Responses: one JSONL record per blind case.",
        "- Packet identity check passed: yes",
        "- Blind packet published: yes",
        "- Raw model-review response published: yes",
        "- Private case map published: no",
        "- Private source manifest published: no",
        "- Independent human review performed: no",
        "- Policy decisions used: no",
        "",
        "## Agreement summary",
        "",
        f"- Reviewed cases: {provenance.reviewed_case_count}",
        f"- `FULL_AGREEMENT`: {provenance.full_agreement_count}",
        f"- `DISAGREEMENT`: {provenance.disagreement_count}",
        f"- `INVALID_REVIEW_ARTIFACT`: {provenance.invalid_review_artifact_count}",
        f"- State disagreements: {sum(not row.state_agreement for row in comparison_rows)}",
        "- Admissible-set disagreements: "
        f"{sum(not row.admissible_set_agreement for row in comparison_rows)}",
        f"- Decision disagreements: {sum(not row.decision_agreement for row in comparison_rows)}",
        f"- High confidence: {provenance.high_confidence_count}",
        f"- Semantic ambiguity flags: {provenance.semantic_ambiguity_count}",
        f"- Ecological-validity flags: {provenance.ecological_validity_concern_count}",
        "",
        "## Case comparisons",
        "",
        "| Scenario | Owner state / set | Blind-model state / set | Computed state / set | "
        "Decision agreement | Confidence | Ambiguity | Ecological concern | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for comparison in comparison_rows:
        record = records_by_id[comparison.scenario_id]
        lines.append(
            f"| `{comparison.scenario_id}` | `{comparison.owner_reviewed_state.value}` / "
            f"{_values(comparison.owner_reviewed_admissible_tool_ids)} | "
            f"`{comparison.blind_model_reviewed_state.value}` / "
            f"{_values(comparison.blind_model_reviewed_admissible_tool_ids)} | "
            f"`{comparison.computed_state.value}` / "
            f"{_values(comparison.computed_admissible_tool_ids)} | "
            f"{_yes_no(comparison.decision_agreement)} | `{record.confidence.value}` | "
            f"{_yes_no(comparison.semantic_ambiguity)} | "
            f"{_yes_no(comparison.ecological_validity_concern)} | "
            f"`{comparison.comparison_status.value}` |"
        )

    lines.extend(
        [
            "",
            "## Ecological-validity interpretation",
            "",
            "### Bundle-level concern",
            "",
            f"{provenance.bundle_level_declared_manifest_concern_count} cases note the general "
            "limitation that synthetic, self-declared manifests are not runtime-verified. This "
            "is one bundle-level declared-manifest realism limitation, not "
            f"{provenance.bundle_level_declared_manifest_concern_count} distinct scenario "
            "defects.",
            "",
            "### Scenario-level concerns",
            "",
        ]
    )
    interpretations = {
        "v2_scenario_007": (
            "The `verified_transcript` requirement is somewhat artificial for the stated "
            "knowledge-packet task."
        ),
        "v2_scenario_012": (
            "The deliberately contradictory required-and-forbidden contract is "
            "diagnostically useful but intentionally artificial."
        ),
    }
    for scenario_id in provenance.scenario_level_ecological_concern_ids:
        note = records_by_id[scenario_id].review_notes
        interpretation = interpretations.get(scenario_id)
        if interpretation is None:
            lines.append(f"- `{scenario_id}`: {note}")
        else:
            lines.append(f"- `{scenario_id}`: {interpretation} Reviewer note: {note}")

    lines.extend(
        [
            "",
            "Ecological-validity flags do not change oracle agreement, evaluation-unit status, "
            "or row-level readiness.",
            "",
            "## Reproducibility boundary",
            "",
            "A clean public clone can verify the exact blind packet, raw model-review response, "
            "review protocol, canonical records, three-way comparisons, provenance counts and "
            "hashes, deterministic report, and consistency with owner and computed repository "
            "evidence.",
            "",
            "A clean public clone cannot repeat the original alias reversal because the "
            "reversible private case map and private source manifest remain unpublished. The "
            "provenance manifest provides cryptographic commitments to those retained private "
            "files, not public access to them.",
            "",
            "## Interpretation boundary",
            "",
            "- The owner-review artifacts remain separate and unchanged.",
            "- Independent human review has not been performed.",
            "- Row-level agreement does not freeze the provisional candidate.",
            "- No live-model policy evaluation or runtime model invocation is part of the "
            "repository. The evidence records a completed external blind model-review session.",
            "- No policy decisions, policy metrics, or runtime tool execution are included.",
            "- No benchmark-validity, production, or cross-domain claim follows.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_blind_model_review_report_v2(
    path: Path,
    records: Iterable[BlindModelReviewRecordV2],
    comparisons: Iterable[BlindModelReviewComparisonV2],
    provenance: BlindModelReviewProvenanceManifestV2,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_blind_model_review_report_v2(records, comparisons, provenance),
        encoding="utf-8",
        newline="\n",
    )
