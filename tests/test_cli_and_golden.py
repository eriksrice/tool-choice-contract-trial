from __future__ import annotations

from pathlib import Path

from tool_choice_contract_trial.cli import main
from tool_choice_contract_trial.models import EvaluationResult
from tool_choice_contract_trial.reporting import load_result_bundle, render_markdown

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "milestone_1" / "authority_profiles"
GOLDEN = ROOT / "tests" / "golden"


def _run_cli(output_directory: Path) -> tuple[Path, Path]:
    results = output_directory / "results.jsonl"
    report = output_directory / "report.md"
    exit_code = main(
        [
            "evaluate",
            "--scenarios",
            str(FIXTURES / "scenarios.jsonl"),
            "--metadata",
            str(FIXTURES / "evaluation_metadata.jsonl"),
            "--oracles",
            str(FIXTURES / "oracles.jsonl"),
            "--decisions",
            str(FIXTURES / "replay_decisions.jsonl"),
            "--results",
            str(results),
            "--report",
            str(report),
        ]
    )
    assert exit_code == 0
    return results, report


def test_cli_is_byte_deterministic_and_matches_golden(tmp_path: Path) -> None:
    first_results, first_report = _run_cli(tmp_path / "first")
    second_results, second_report = _run_cli(tmp_path / "second")

    assert first_results.read_bytes() == second_results.read_bytes()
    assert first_report.read_bytes() == second_report.read_bytes()
    assert first_results.read_bytes() == (GOLDEN / "results.jsonl").read_bytes()
    assert first_report.read_bytes() == (GOLDEN / "report.md").read_bytes()


def test_markdown_is_a_pure_result_bundle_projection(tmp_path: Path) -> None:
    results_path, report_path = _run_cli(tmp_path)
    results = load_result_bundle(results_path)
    assert all(isinstance(result, EvaluationResult) for result in results)
    assert report_path.read_text() == render_markdown(results)
    assert str(tmp_path) not in report_path.read_text()


def test_markdown_explains_the_milestone_1_evidence(tmp_path: Path) -> None:
    _, report_path = _run_cli(tmp_path)
    report = report_path.read_text()
    assert "Retrieve cited evidence for the fictional Meridian documentation review." in report
    assert "Unique-to-unique minimal-pair flip" in report
    assert "Public-primary evidence required" in report
    assert "Approved-internal evidence required" in report
    assert "`public_primary`" in report
    assert "`approved_internal`" in report
    assert "`authority.requirement`" in report
    assert "`F_AUTHORITY_MISMATCH`" in report
    assert "ADMISSIBLE_BUT_UNJUSTIFIED" in report
    assert "proves mechanics only" in report
