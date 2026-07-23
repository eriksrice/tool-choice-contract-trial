"""Deterministic Markdown projection of a validated result bundle."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from .errors import ArtifactIntegrityError, SchemaInvalidError
from .models import EvaluationResult, OracleState, StrictContractOutcome
from .serialization import read_jsonl_objects


def load_result_bundle(path: Path) -> tuple[EvaluationResult, ...]:
    try:
        objects = read_jsonl_objects(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SchemaInvalidError(f"SCHEMA_INVALID: {path}: {error}") from error
    results: list[EvaluationResult] = []
    for line_number, value in objects:
        try:
            results.append(EvaluationResult.model_validate(value))
        except ValidationError as error:
            raise SchemaInvalidError(f"SCHEMA_INVALID: {path}:{line_number}: {error}") from error
    result_keys = [(result.scenario_id, result.policy_id) for result in results]
    if len(result_keys) != len(set(result_keys)):
        raise ArtifactIntegrityError("duplicate scenario-policy result rows")
    return tuple(results)


def _display_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _decision(result: EvaluationResult) -> str:
    if result.policy_decision is None:
        return "MALFORMED"
    if result.selected_tool_id is not None:
        return f"{result.policy_decision.value} `{result.selected_tool_id}`"
    return result.policy_decision.value


def _minimal_pair_lines(ordered: tuple[EvaluationResult, ...]) -> list[str]:
    groups: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in ordered:
        if result.context.comparison_group_id:
            groups[result.context.comparison_group_id].append(result)

    lines: list[str] = []
    for comparison_group_id, group_results in sorted(groups.items()):
        unique_results = sorted(
            (
                result
                for result in group_results
                if result.oracle_state is OracleState.UNIQUE_ADMISSIBLE
            ),
            key=lambda result: result.scenario_id,
        )
        if len(unique_results) < 2:
            continue
        transitions = [
            (
                f"{result.context.variant_label}: "
                f"{_display_values(result.context.accepted_authority_profiles)} → "
                f"{_display_values(result.admissible_tool_ids)}"
            )
            for result in unique_results
        ]
        lines.append(
            f"- `{comparison_group_id}` changes the accepted authority condition and flips "
            "the unique admissible tool: " + "; ".join(transitions) + "."
        )
    if not lines:
        lines.append("- No complete unique-to-unique comparison group is present.")
    return lines


def _diagnostic_lines(ordered: tuple[EvaluationResult, ...]) -> list[str]:
    lines: list[str] = []
    for result in ordered:
        for witness in result.violation_witnesses:
            lines.extend(
                [
                    f"### {result.context.variant_label}",
                    "",
                    f"- Clause: `{witness.clause_id}`",
                    f"- Failure: `{witness.failure_code.value}`",
                    f"- Diagnostic scope: `{witness.scope.value}`",
                    f"- Tool: `{witness.tool_id}`" if witness.tool_id else "- Tool: not applicable",
                    f"- Expected: {_display_values(witness.expected_values)}",
                    f"- Actual: {_display_values(witness.actual_values)}",
                    "",
                ]
            )
    if not lines:
        return ["No clause-level policy failures were recorded.", ""]
    return lines


def render_markdown(results: tuple[EvaluationResult, ...]) -> str:
    """Render only values present in the result bundle; add no run metadata."""

    ordered = tuple(sorted(results, key=lambda result: (result.scenario_id, result.policy_id)))
    outcome_counts = Counter(result.strict_contract_outcome.value for result in ordered)
    status_counts = Counter(result.evaluation_unit_status.value for result in ordered)
    family_labels = tuple(sorted({result.context.family_label for result in ordered}))
    task_summaries = tuple(sorted({result.context.task_summary for result in ordered}))
    capabilities = tuple(
        sorted(
            {
                capability
                for result in ordered
                for capability in result.context.required_capabilities
            }
        )
    )
    citation_values = tuple(
        sorted({str(result.context.citations_required).lower() for result in ordered})
    )

    lines = [
        "# Tool Choice Contract Trial — Milestone 1 Results",
        "",
        "> Scope: one synthetic scenario family demonstrates deterministic evaluation "
        "mechanics only; it does not validate the benchmark thesis.",
        "",
        "## Experiment",
        "",
        f"- Family: {', '.join(family_labels)}",
        f"- Common synthetic task: {'; '.join(task_summaries)}",
        "- Contract condition under test: accepted evidence authority profile or set.",
        f"- Common required capability: {_display_values(capabilities)}",
        f"- Citations required: {', '.join(citation_values)}",
        "- Policy source: one trusted, schema-valid stored replay bundle.",
        "",
        "## Outcome counts",
        "",
        f"- Cases: {len(ordered)}",
        f"- Scoreable: {status_counts['SCOREABLE']}",
        f"- Invalid evaluation units: {status_counts['INVALID']}",
    ]
    for outcome in (
        "CORRECT",
        "INCORRECT",
        "ADMISSIBLE_BUT_UNJUSTIFIED",
        "NOT_SCORED",
    ):
        lines.append(f"- {outcome}: {outcome_counts[outcome]}")
    lines.extend(
        [
            "",
            "## Case evidence",
            "",
            "| Variant | Accepted authority | Computed admissible tools | Replayed decision | "
            "Selected-tool admissibility | Strict outcome | Decisive clause | Primary failure |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for result in ordered:
        lines.append(
            "| "
            + " | ".join(
                (
                    result.context.variant_label,
                    _display_values(result.context.accepted_authority_profiles),
                    _display_values(result.admissible_tool_ids),
                    _decision(result),
                    result.selected_tool_admissibility.value,
                    result.strict_contract_outcome.value,
                    _display_values(result.decisive_clause_ids),
                    result.primary_failure_code.value if result.primary_failure_code else "—",
                )
            )
            + " |"
        )
    lines.extend(["", "## Unique-to-unique minimal-pair flip", ""])
    lines.extend(_minimal_pair_lines(ordered))
    lines.extend(["", "## Clause-level diagnostics", ""])
    lines.extend(_diagnostic_lines(ordered))

    inadmissible = [
        result for result in ordered if result.selected_tool_admissibility.value == "INADMISSIBLE"
    ]
    admissible_unjustified = [
        result
        for result in ordered
        if result.strict_contract_outcome is StrictContractOutcome.ADMISSIBLE_BUT_UNJUSTIFIED
    ]
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "- Inadmissible selections: "
            + (
                ", ".join(result.context.variant_label for result in inadmissible)
                if inadmissible
                else "none"
            )
            + ".",
            "- Admissible-but-unjustified selections: "
            + (
                ", ".join(result.context.variant_label for result in admissible_unjustified)
                if admissible_unjustified
                else "none"
            )
            + ".",
            "- These categories remain separate: an admissible member chosen without a "
            "tie-break is not grouped with an inadmissible selection.",
            "- The harness evaluates declared manifest compatibility and does not execute "
            "tools or verify runtime truth.",
            "- This one synthetic family proves mechanics only, not benchmark validity or "
            "cross-domain performance.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_markdown_report(path: Path, results: tuple[EvaluationResult, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(results), encoding="utf-8", newline="\n")
