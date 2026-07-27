from __future__ import annotations

from pathlib import Path

import pytest

import tool_choice_contract_trial.cli as cli_module
from tool_choice_contract_trial.counterfactual_io import (
    load_counterfactual_findings,
    load_counterfactual_specs,
)
from tool_choice_contract_trial.counterfactual_reporting import (
    render_counterfactual_markdown,
)
from tool_choice_contract_trial.errors import ArtifactIntegrityError
from tool_choice_contract_trial.models import CounterfactualFinding

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "fixtures" / "milestone_1" / "authority_profiles" / "scenarios.jsonl"
COMPARISONS = ROOT / "fixtures" / "milestone_2a" / "authority_profiles" / "comparisons.jsonl"
GOLDEN = ROOT / "tests" / "golden"


def _run_cli(output_directory: Path) -> tuple[Path, Path]:
    findings = output_directory / "counterfactual_findings.jsonl"
    report = output_directory / "counterfactual_report.md"
    exit_code = cli_module.main(
        [
            "analyze-counterfactuals",
            "--scenarios",
            str(SCENARIOS),
            "--comparisons",
            str(COMPARISONS),
            "--findings",
            str(findings),
            "--report",
            str(report),
        ]
    )
    assert exit_code == 0
    return findings, report


def test_counterfactual_cli_is_deterministic_and_matches_golden(tmp_path: Path) -> None:
    first_findings, first_report = _run_cli(tmp_path / "first")
    second_findings, second_report = _run_cli(tmp_path / "second")

    assert first_findings.read_bytes() == second_findings.read_bytes()
    assert first_report.read_bytes() == second_report.read_bytes()
    assert first_findings.read_bytes() == (GOLDEN / "counterfactual_findings.jsonl").read_bytes()
    assert first_report.read_bytes() == (GOLDEN / "counterfactual_report.md").read_bytes()


def test_counterfactual_report_is_a_pure_finding_projection(tmp_path: Path) -> None:
    findings_path, report_path = _run_cli(tmp_path)
    findings = load_counterfactual_findings(findings_path)
    assert all(isinstance(finding, CounterfactualFinding) for finding in findings)
    assert report_path.read_text() == render_counterfactual_markdown(findings)
    assert str(tmp_path) not in report_path.read_text()


def test_counterfactual_report_explains_required_semantics(tmp_path: Path) -> None:
    _, report_path = _run_cli(tmp_path)
    report = report_path.read_text()
    assert "contract.accepted_authority_profiles" in report
    assert "UNIQUE_ADMISSIBLE" in report
    assert "MULTIPLE_ADMISSIBLE" in report
    assert "counterfactually decisive for the admissibility relation: yes" in report
    assert "Individual relation decisiveness established: yes" in report
    assert "not an incompatibility witness" in report
    assert "existing synthetic authority family only" in report


def test_counterfactual_command_is_independent_of_oracles_and_policy_decisions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden_loader(*args: object, **kwargs: object) -> None:
        raise AssertionError("counterfactual analysis must not load this artifact")

    monkeypatch.setattr(cli_module, "load_oracle_records", forbidden_loader)
    monkeypatch.setattr(cli_module, "load_replay_decisions", forbidden_loader)
    _run_cli(tmp_path)


def test_duplicate_comparison_rows_fail_loudly(tmp_path: Path) -> None:
    rows = COMPARISONS.read_text().splitlines()
    duplicate_path = tmp_path / "duplicates.jsonl"
    duplicate_path.write_text("\n".join([*rows, rows[0]]) + "\n")

    with pytest.raises(ArtifactIntegrityError, match="duplicate counterfactual comparison"):
        load_counterfactual_specs(duplicate_path)
