"""Pure Markdown projection of validated counterfactual findings."""

from __future__ import annotations

from pathlib import Path

from .models import CounterfactualFinding, CounterfactualValidationStatus


def _display_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_counterfactual_markdown(findings: tuple[CounterfactualFinding, ...]) -> str:
    """Render only values present in the finding bundle."""

    ordered = tuple(sorted(findings, key=lambda finding: finding.comparison_id))
    lines = [
        "# Tool Choice Contract Trial — Milestone 2A Counterfactual Findings",
        "",
        "> Scope: deterministic counterfactual mechanics over the existing synthetic "
        "authority family only; this does not validate a broader benchmark.",
        "",
        "## Comparisons",
        "",
    ]
    for finding in ordered:
        lines.extend(
            [
                f"### `{finding.comparison_id}`",
                "",
                f"- Validation status: `{finding.validation_status.value}`",
                f"- Endpoints: `{finding.source_scenario_id}` → `{finding.target_scenario_id}`",
                "- Declared clause intervention: "
                f"{_display_values(finding.declared_changed_clause_ids)}",
                "- Observed contract paths: "
                f"{_display_values(finding.observed_changed_contract_paths)}",
            ]
        )
        if finding.validation_status is CounterfactualValidationStatus.VALID:
            lines.append(
                "- Held constant: task summary, schema compatibility, tool availability, "
                "and canonical tool manifests."
            )
        else:
            lines.extend(
                [
                    "- Held constant: not established because structural validation failed.",
                    "- Invalid-comparison reasons: "
                    f"{_display_values(finding.invalid_comparison_reasons)}",
                ]
            )
        lines.extend(
            [
                "- Source relation: "
                f"`{finding.source_computed_oracle_state.value}` with "
                f"{_display_values(finding.source_computed_admissible_tool_ids)}",
                "- Target relation: "
                f"`{finding.target_computed_oracle_state.value}` with "
                f"{_display_values(finding.target_computed_admissible_tool_ids)}",
                f"- Admissible set changed: {_yes_no(finding.admissible_set_changed)}",
                f"- Oracle state changed: {_yes_no(finding.oracle_state_changed)}",
                "- Unique admissible tool flipped: "
                f"{_yes_no(finding.unique_admissible_tool_flipped)}",
                "- Declared clause set counterfactually decisive: "
                f"{_yes_no(finding.counterfactually_decisive)}",
                "- Individual decisiveness established: "
                f"{_yes_no(finding.individual_decisiveness_established)}",
                "",
            ]
        )

    lines.extend(
        [
            "## Why this is not an incompatibility witness",
            "",
            "An incompatibility witness explains why one declared tool manifest fails one "
            "contract clause in one scenario. A counterfactual finding instead validates a "
            "cross-scenario intervention, holds every other semantic input constant, and "
            "checks whether the independently computed admissible relation changes.",
            "",
            "## Interpretation boundary",
            "",
            "- Only singleton `authority.requirement` interventions are exercised here.",
            "- A future multi-clause intervention would establish set-level decisiveness only "
            "unless proper-subset interventions separately establish minimality.",
            "- The analyzer uses no stored policy decisions or oracle labels as its source of "
            "truth.",
            "- This remains one synthetic authority family; no broader benchmark, production, "
            "or cross-domain claim follows.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_counterfactual_markdown_report(
    path: Path,
    findings: tuple[CounterfactualFinding, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_counterfactual_markdown(findings),
        encoding="utf-8",
        newline="\n",
    )
