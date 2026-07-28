from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import tool_choice_contract_trial.cli as cli_module
from tool_choice_contract_trial.errors import ArtifactIntegrityError
from tool_choice_contract_trial.serialization import canonical_hash
from tool_choice_contract_trial.v2_io import (
    load_oracle_expectations_v2,
    load_oracle_reviews_v2,
    load_oracle_validation_findings_v2,
    load_policy_views_v2,
    load_provisional_manifest_v2,
)
from tool_choice_contract_trial.v2_models import (
    BundleStatusV2,
    EvaluationUnitStatusV2,
    OracleReviewDispositionV2,
    OracleStateV2,
    PolicyViewV2,
    ReviewReadinessV2,
)
from tool_choice_contract_trial.v2_reporting import render_oracle_review_packet_v2
from tool_choice_contract_trial.v2_schema import (
    V2_SCHEMA_MODELS,
    check_v2_schema_drift,
    generate_v2_schemas,
)
from tool_choice_contract_trial.v2_validation import (
    build_provisional_manifest_v2,
    validate_oracle_candidates_v2,
    verify_oracle_validation_finding_v2,
    verify_provisional_manifest_v2,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "milestone_2b" / "review_candidate"
GOLDEN = ROOT / "tests" / "golden" / "milestone_2b"


def _run_cli(output_directory: Path) -> dict[str, Path]:
    outputs = {
        "findings": output_directory / "oracle_validation_findings.jsonl",
        "report": output_directory / "oracle_review_packet.md",
        "manifest": output_directory / "provisional_bundle_manifest.json",
        "invalid": output_directory / "invalid_unit_register.jsonl",
    }
    exit_code = cli_module.main(
        [
            "validate-oracle-candidates",
            "--scenarios",
            str(FIXTURES / "scenarios.jsonl"),
            "--expectations",
            str(FIXTURES / "oracle_expectations.jsonl"),
            "--reviews",
            str(FIXTURES / "oracle_reviews.jsonl"),
            "--findings",
            str(outputs["findings"]),
            "--report",
            str(outputs["report"]),
            "--manifest",
            str(outputs["manifest"]),
            "--invalid-unit-register",
            str(outputs["invalid"]),
        ]
    )
    assert exit_code == 0
    return outputs


def test_v2_cli_is_byte_deterministic_and_matches_goldens(tmp_path: Path) -> None:
    first = _run_cli(tmp_path / "first")
    second = _run_cli(tmp_path / "second")

    golden_names = {
        "findings": "oracle_validation_findings.jsonl",
        "report": "oracle_review_packet.md",
        "manifest": "provisional_bundle_manifest.json",
        "invalid": "invalid_unit_register.jsonl",
    }
    for output_name, golden_name in golden_names.items():
        assert first[output_name].read_bytes() == second[output_name].read_bytes()
        assert first[output_name].read_bytes() == (GOLDEN / golden_name).read_bytes()


def test_v2_review_packet_is_a_pure_validated_bundle_projection(tmp_path: Path) -> None:
    outputs = _run_cli(tmp_path)
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(outputs["findings"])
    manifest = load_provisional_manifest_v2(outputs["manifest"])

    assert outputs["report"].read_text() == render_oracle_review_packet_v2(
        views,
        expectations,
        reviews,
        findings,
        manifest,
    )
    assert str(tmp_path) not in outputs["report"].read_text()


def test_v2_review_packet_and_manifest_state_the_review_boundary(tmp_path: Path) -> None:
    outputs = _run_cli(tmp_path)
    report = outputs["report"].read_text()
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(outputs["findings"])
    manifest = load_provisional_manifest_v2(outputs["manifest"])
    invalid_rows = [json.loads(line) for line in outputs["invalid"].read_text().splitlines()]

    assert "Owner review: complete for 11 of 12 current candidates" in report
    assert "11 proposals accepted" in report
    assert "The replacement `v2_scenario_012` awaits owner re-review" in report
    assert "Independent review has not been performed" in report
    assert "The bundle is not frozen" in report
    assert "Artifact schema versions: `2.1.0`" in report
    assert "CONTRACT_INVALID" in report
    assert "no policy decisions were used" in report
    assert "have not been processed by the v1 authority-only counterfactual analyzer" in report
    assert "Authoring rationale" in report
    assert "capabilities" in report
    assert "authority" in report
    assert "Relation witnesses" in report
    assert "required tool `v2_tool_005`; forbidden `v2_tool_005`" in report
    assert "required tool is also explicitly forbidden: v2_tool_005" in report
    assert "Reviewer role: `owner_reviewer`" in report
    assert "Reviewed relation:" in report
    assert "Review performed without policy outputs: yes" in report
    assert "Adjudication: none" in report
    assert reviews[-1].review_notes in report

    assert sum(row.disposition is OracleReviewDispositionV2.AGREE for row in reviews) == 11
    assert sum(row.disposition is OracleReviewDispositionV2.PENDING for row in reviews) == 1
    assert not any(row.disposition is OracleReviewDispositionV2.DISAGREE for row in reviews)
    assert not any(row.disposition is OracleReviewDispositionV2.ADJUDICATED for row in reviews)
    assert all(row.reviewer_role == "owner_reviewer" for row in reviews)
    assert all(row.review_performed_without_policy_outputs is True for row in reviews[:-1])
    assert reviews[-1].review_performed_without_policy_outputs is None
    assert all(row.adjudicated_state is None for row in reviews)
    assert all(row.adjudicated_admissible_tool_ids is None for row in reviews)

    accepted = findings[:-1]
    disputed = findings[-1]
    assert all(row.review_readiness is ReviewReadinessV2.REVIEW_COMPLETE for row in accepted)
    assert all(row.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE for row in accepted)
    assert all(row.ready_for_scoring and row.ready_for_freeze for row in accepted)
    assert disputed.scenario_id == "v2_scenario_012"
    assert disputed.computed_oracle_state is OracleStateV2.CONTRACT_INVALID
    assert disputed.expectation_matches_relation
    assert disputed.reviewed_expected_state is None
    assert disputed.reviewed_admissible_tool_ids is None
    assert disputed.review_readiness is ReviewReadinessV2.PENDING_REVIEW
    assert disputed.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE
    assert not disputed.ready_for_scoring
    assert not disputed.ready_for_freeze

    assert manifest.bundle_status is BundleStatusV2.PROVISIONAL_REVIEW_CANDIDATE
    assert manifest.artifact_schema_versions == ("2.1.0",)
    assert manifest.pending_review_count == 1
    assert manifest.invalid_unit_count == 0
    assert manifest.contract_invalid_count == 1
    assert manifest.computed_state_counts.model_dump() == {
        "unique_admissible": 6,
        "multiple_admissible": 2,
        "no_admissible": 3,
        "contract_invalid": 1,
    }
    assert invalid_rows == []


def test_loaded_findings_round_trip_through_source_aware_verification(tmp_path: Path) -> None:
    outputs = _run_cli(tmp_path)
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(outputs["findings"])
    views_by_id = {row.scenario_id: row for row in views}
    expectations_by_id = {row.scenario_id: row for row in expectations}
    reviews_by_id = {row.scenario_id: row for row in reviews}

    for finding in findings:
        verify_oracle_validation_finding_v2(
            finding,
            views_by_id[finding.scenario_id],
            expectations_by_id[finding.scenario_id],
            reviews_by_id[finding.scenario_id],
        )


def test_loaded_manifest_round_trips_through_source_aware_verification(tmp_path: Path) -> None:
    outputs = _run_cli(tmp_path)
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(outputs["findings"])
    manifest = load_provisional_manifest_v2(outputs["manifest"])

    verify_provisional_manifest_v2(manifest, views, expectations, reviews, findings)


def test_review_packet_rejects_loaded_but_source_inconsistent_evidence(
    tmp_path: Path,
) -> None:
    outputs = _run_cli(tmp_path)
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(outputs["findings"])
    manifest = load_provisional_manifest_v2(outputs["manifest"])
    changed_finding = findings[0].model_copy(update={"scenario_hash": "0" * 64})

    with pytest.raises(ArtifactIntegrityError, match="scenario_hash"):
        render_oracle_review_packet_v2(
            views,
            expectations,
            reviews,
            (changed_finding, *findings[1:]),
            manifest,
        )


def test_v2_command_never_loads_oracles_or_policy_decisions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden_loader(*args: object, **kwargs: object) -> None:
        raise AssertionError("v2 oracle validation must not load v1 policy or oracle artifacts")

    monkeypatch.setattr(cli_module, "load_oracle_records", forbidden_loader)
    monkeypatch.setattr(cli_module, "load_replay_decisions", forbidden_loader)

    _run_cli(tmp_path)


def test_v2_schema_generation_is_deterministic_and_has_no_drift(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_v2_schemas(first)
    generate_v2_schemas(second)

    assert {path.name: path.read_bytes() for path in first.glob("*.schema.json")} == {
        path.name: path.read_bytes() for path in second.glob("*.schema.json")
    }
    check_v2_schema_drift(ROOT / "schemas" / "v2")


@pytest.mark.parametrize("model", V2_SCHEMA_MODELS.values(), ids=lambda model: model.__name__)
def test_each_v2_schema_authority_rejects_an_empty_object(model: type[object]) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({})  # type: ignore[attr-defined]


def test_v2_record_order_is_canonical() -> None:
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    baseline_findings = validate_oracle_candidates_v2(views, expectations, reviews)
    reordered_findings = validate_oracle_candidates_v2(
        tuple(reversed(views)),
        tuple(reversed(expectations)),
        tuple(reversed(reviews)),
    )

    assert reordered_findings == baseline_findings
    assert build_provisional_manifest_v2(
        views,
        expectations,
        reviews,
        baseline_findings,
    ) == build_provisional_manifest_v2(
        tuple(reversed(views)),
        tuple(reversed(expectations)),
        tuple(reversed(reviews)),
        tuple(reversed(reordered_findings)),
    )


def test_provisional_manifest_hash_changes_with_scenario_or_expectation_mutation() -> None:
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = validate_oracle_candidates_v2(views, expectations, reviews)
    baseline = build_provisional_manifest_v2(views, expectations, reviews, findings)

    changed_contract = views[0].contract.model_copy(
        update={"task_summary": "Prepare a changed test-only knowledge packet."}
    )
    changed_view = PolicyViewV2.model_validate(
        views[0].model_copy(update={"contract": changed_contract}).model_dump(mode="json")
    )
    changed_views = (changed_view, *views[1:])
    changed_findings = validate_oracle_candidates_v2(changed_views, expectations, reviews)
    scenario_mutation = build_provisional_manifest_v2(
        changed_views,
        expectations,
        reviews,
        changed_findings,
    )

    changed_expectation = expectations[0].model_copy(
        update={"authoring_rationale": "Changed test-only authoring rationale."}
    )
    changed_expectations = (changed_expectation, *expectations[1:])
    expectation_findings = validate_oracle_candidates_v2(
        views,
        changed_expectations,
        reviews,
    )
    expectation_mutation = build_provisional_manifest_v2(
        views,
        changed_expectations,
        reviews,
        expectation_findings,
    )

    changed_review = reviews[0].model_copy(
        update={"review_notes": "Changed test-only pending review note."}
    )
    changed_reviews = (changed_review, *reviews[1:])
    review_findings = validate_oracle_candidates_v2(
        views,
        expectations,
        changed_reviews,
    )
    review_mutation = build_provisional_manifest_v2(
        views,
        expectations,
        changed_reviews,
        review_findings,
    )

    assert canonical_hash(scenario_mutation) != canonical_hash(baseline)
    assert canonical_hash(expectation_mutation) != canonical_hash(baseline)
    assert canonical_hash(review_mutation) != canonical_hash(baseline)


@pytest.fixture
def source_verified_manifest_bundle() -> tuple[object, tuple[object, ...], ...]:
    views = load_policy_views_v2(FIXTURES / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl")
    findings = validate_oracle_candidates_v2(views, expectations, reviews)
    manifest = build_provisional_manifest_v2(views, expectations, reviews, findings)
    return manifest, views, expectations, reviews, findings


@pytest.mark.parametrize("count_field", ("pending_review_count", "invalid_unit_count"))
def test_source_aware_manifest_rejects_altered_review_counts(
    count_field: str,
    source_verified_manifest_bundle: tuple[object, tuple[object, ...], ...],
) -> None:
    manifest, views, expectations, reviews, findings = source_verified_manifest_bundle
    changed = manifest.model_copy(update={count_field: getattr(manifest, count_field) + 1})

    with pytest.raises(ArtifactIntegrityError, match=count_field):
        verify_provisional_manifest_v2(changed, views, expectations, reviews, findings)


def test_source_aware_manifest_rejects_altered_bundle_or_scenario_hash(
    source_verified_manifest_bundle: tuple[object, tuple[object, ...], ...],
) -> None:
    manifest, views, expectations, reviews, findings = source_verified_manifest_bundle
    changed_bundle = manifest.model_copy(update={"scenario_bundle_hash": "0" * 64})
    changed_artifact = manifest.scenario_artifacts[0].model_copy(update={"finding_hash": "0" * 64})
    changed_scenario = manifest.model_copy(
        update={"scenario_artifacts": (changed_artifact, *manifest.scenario_artifacts[1:])}
    )

    with pytest.raises(ArtifactIntegrityError, match="scenario_bundle_hash"):
        verify_provisional_manifest_v2(changed_bundle, views, expectations, reviews, findings)
    with pytest.raises(ArtifactIntegrityError, match="scenario_artifacts"):
        verify_provisional_manifest_v2(changed_scenario, views, expectations, reviews, findings)


@pytest.mark.parametrize("shape", ("missing", "extra", "mismatched"))
def test_source_aware_manifest_rejects_changed_scenario_artifact_set(
    shape: str,
    source_verified_manifest_bundle: tuple[object, tuple[object, ...], ...],
) -> None:
    manifest, views, expectations, reviews, findings = source_verified_manifest_bundle
    artifacts = manifest.scenario_artifacts
    if shape == "missing":
        changed_artifacts = artifacts[:-1]
    elif shape == "extra":
        changed_artifacts = (*artifacts, artifacts[-1])
    else:
        changed_artifacts = (
            artifacts[0].model_copy(update={"scenario_id": "v2_scenario_099"}),
            *artifacts[1:],
        )
    changed = manifest.model_copy(update={"scenario_artifacts": changed_artifacts})

    with pytest.raises(ArtifactIntegrityError, match="scenario_artifacts"):
        verify_provisional_manifest_v2(changed, views, expectations, reviews, findings)
