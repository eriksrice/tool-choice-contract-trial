from __future__ import annotations

import json
from pathlib import Path

import pytest

from tool_choice_contract_trial.errors import ArtifactIntegrityError, SchemaInvalidError
from tool_choice_contract_trial.v2_io import (
    load_oracle_expectations_v2,
    load_oracle_reviews_v2,
    load_policy_views_v2,
)
from tool_choice_contract_trial.v2_models import (
    DecisionKindV2,
    EvaluationUnitStatusV2,
    OracleExpectationV2,
    OracleReviewDispositionV2,
    OracleReviewRecordV2,
    OracleStateV2,
    PolicyViewV2,
    ReviewReadinessV2,
)
from tool_choice_contract_trial.v2_relation import assess_policy_view_v2
from tool_choice_contract_trial.v2_validation import validate_oracle_candidates_v2

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "milestone_2b" / "review_candidate"


@pytest.fixture
def v2_bundle() -> tuple[
    tuple[PolicyViewV2, ...],
    tuple[OracleExpectationV2, ...],
    tuple[OracleReviewRecordV2, ...],
]:
    return (
        load_policy_views_v2(FIXTURES / "scenarios.jsonl"),
        load_oracle_expectations_v2(FIXTURES / "oracle_expectations.jsonl"),
        load_oracle_reviews_v2(FIXTURES / "oracle_reviews.jsonl"),
    )


def _replace_expectation(
    expectations: tuple[OracleExpectationV2, ...],
    replacement: OracleExpectationV2,
) -> tuple[OracleExpectationV2, ...]:
    return tuple(
        replacement if row.scenario_id == replacement.scenario_id else row for row in expectations
    )


def _replace_review(
    reviews: tuple[OracleReviewRecordV2, ...],
    replacement: OracleReviewRecordV2,
) -> tuple[OracleReviewRecordV2, ...]:
    return tuple(
        replacement if row.scenario_id == replacement.scenario_id else row for row in reviews
    )


def _unique_mismatch(expectation: OracleExpectationV2) -> OracleExpectationV2:
    return OracleExpectationV2.model_validate(
        expectation.model_copy(
            update={
                "expected_admissible_tool_ids": ("v2_tool_002",),
                "expected_selected_tool_id": "v2_tool_002",
            }
        ).model_dump(mode="json")
    )


def test_relation_computation_is_independent_of_expectation_and_review_mutations(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    baseline_relations = tuple(assess_policy_view_v2(view) for view in views)
    changed_expectation = _unique_mismatch(expectations[0])
    changed_review = OracleReviewRecordV2(
        scenario_id="v2_scenario_001",
        reviewer_role="independent_reviewer",
        disposition=OracleReviewDispositionV2.DISAGREE,
        reviewed_expected_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        reviewed_admissible_tool_ids=("v2_tool_002",),
        review_notes="Test-only disagreement.",
        review_performed_without_policy_outputs=True,
    )

    validate_oracle_candidates_v2(
        views,
        _replace_expectation(expectations, changed_expectation),
        _replace_review(reviews, changed_review),
    )

    assert tuple(assess_policy_view_v2(view) for view in views) == baseline_relations


def test_pending_matching_proposals_remain_pending_and_not_freeze_ready(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    findings = validate_oracle_candidates_v2(*v2_bundle)

    assert len(findings) == 12
    assert all(finding.expectation_matches_relation for finding in findings)
    assert all(finding.review_readiness is ReviewReadinessV2.PENDING_REVIEW for finding in findings)
    assert all(
        finding.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE for finding in findings
    )
    assert not any(finding.ready_for_scoring or finding.ready_for_freeze for finding in findings)


def test_proposed_admissible_set_mismatch_is_visible_but_pending_review_remains_pending(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    changed = _unique_mismatch(expectations[0])
    finding = validate_oracle_candidates_v2(
        views,
        _replace_expectation(expectations, changed),
        reviews,
    )[0]

    assert finding.state_matches_expectation
    assert not finding.admissible_set_matches_expectation
    assert not finding.expectation_matches_relation
    assert finding.review_readiness is ReviewReadinessV2.PENDING_REVIEW
    assert not finding.ready_for_scoring


def test_proposed_oracle_state_mismatch_is_visible(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    changed = OracleExpectationV2.model_validate(
        expectations[0]
        .model_copy(
            update={
                "expected_oracle_state": OracleStateV2.NO_ADMISSIBLE,
                "expected_admissible_tool_ids": (),
                "expected_decision": DecisionKindV2.NO_TOOL,
                "expected_selected_tool_id": None,
            }
        )
        .model_dump(mode="json")
    )
    finding = validate_oracle_candidates_v2(
        views,
        _replace_expectation(expectations, changed),
        reviews,
    )[0]

    assert not finding.state_matches_expectation
    assert not finding.expectation_matches_relation
    assert not finding.ready_for_scoring


def test_completed_disagreement_without_adjudication_is_invalid(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    review = OracleReviewRecordV2(
        scenario_id="v2_scenario_001",
        reviewer_role="independent_reviewer",
        disposition=OracleReviewDispositionV2.DISAGREE,
        reviewed_expected_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        reviewed_admissible_tool_ids=("v2_tool_002",),
        review_notes="Test-only completed disagreement.",
        review_performed_without_policy_outputs=True,
    )
    finding = validate_oracle_candidates_v2(
        views,
        expectations,
        _replace_review(reviews, review),
    )[0]

    assert finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
    assert finding.review_readiness is ReviewReadinessV2.ADJUDICATION_REQUIRED
    assert "completed disagreement lacks adjudication" in finding.invalid_unit_reasons


def test_review_claiming_agreement_with_different_values_is_invalid(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    review = OracleReviewRecordV2(
        scenario_id="v2_scenario_001",
        reviewer_role="independent_reviewer",
        disposition=OracleReviewDispositionV2.AGREE,
        reviewed_expected_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        reviewed_admissible_tool_ids=("v2_tool_002",),
        review_notes="Test-only inconsistent agreement.",
        review_performed_without_policy_outputs=True,
    )
    finding = validate_oracle_candidates_v2(
        views,
        expectations,
        _replace_review(reviews, review),
    )[0]

    assert finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
    assert any("claims agreement" in reason for reason in finding.invalid_unit_reasons)


def test_incomplete_adjudication_is_invalid(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    review = OracleReviewRecordV2(
        scenario_id="v2_scenario_001",
        reviewer_role="adjudicator",
        disposition=OracleReviewDispositionV2.ADJUDICATED,
        reviewed_expected_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        reviewed_admissible_tool_ids=("v2_tool_002",),
        review_notes="Test-only incomplete adjudication.",
        review_performed_without_policy_outputs=True,
    )
    finding = validate_oracle_candidates_v2(
        views,
        expectations,
        _replace_review(reviews, review),
    )[0]

    assert finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
    assert "adjudication is incomplete" in finding.invalid_unit_reasons


def test_completed_adjudication_can_restore_a_coherent_unit(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    changed_expectation = _unique_mismatch(expectations[0])
    review = OracleReviewRecordV2(
        scenario_id="v2_scenario_001",
        reviewer_role="adjudicator",
        disposition=OracleReviewDispositionV2.ADJUDICATED,
        reviewed_expected_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        reviewed_admissible_tool_ids=("v2_tool_002",),
        review_notes="Test-only complete adjudication.",
        review_performed_without_policy_outputs=True,
        adjudicated_state=OracleStateV2.UNIQUE_ADMISSIBLE,
        adjudicated_admissible_tool_ids=("v2_tool_001",),
    )
    finding = validate_oracle_candidates_v2(
        views,
        _replace_expectation(expectations, changed_expectation),
        _replace_review(reviews, review),
    )[0]

    assert finding.review_readiness is ReviewReadinessV2.ADJUDICATED
    assert finding.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE
    assert finding.ready_for_scoring
    assert finding.ready_for_freeze


def test_contract_invalid_remains_distinct_from_invalid_evaluation_unit(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    pending = validate_oracle_candidates_v2(views, expectations, reviews)[-1]
    review = OracleReviewRecordV2(
        scenario_id="v2_scenario_012",
        reviewer_role="independent_reviewer",
        disposition=OracleReviewDispositionV2.AGREE,
        reviewed_expected_state=OracleStateV2.CONTRACT_INVALID,
        reviewed_admissible_tool_ids=(),
        review_notes="Test-only agreement with the intentional contract defect.",
        review_performed_without_policy_outputs=True,
    )
    reviewed = validate_oracle_candidates_v2(
        views,
        expectations,
        _replace_review(reviews, review),
    )[-1]

    assert pending.computed_oracle_state is OracleStateV2.CONTRACT_INVALID
    assert pending.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE
    assert reviewed.computed_oracle_state is OracleStateV2.CONTRACT_INVALID
    assert reviewed.evaluation_unit_status is EvaluationUnitStatusV2.SCOREABLE
    assert reviewed.ready_for_scoring


@pytest.mark.parametrize(
    ("drop_expectation", "drop_review", "reason"),
    (
        (True, False, "missing oracle expectation"),
        (False, True, "missing oracle review record"),
    ),
)
def test_missing_authoring_artifact_produces_visible_invalid_unit(
    drop_expectation: bool,
    drop_review: bool,
    reason: str,
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    if drop_expectation:
        expectations = expectations[1:]
    if drop_review:
        reviews = reviews[1:]

    finding = validate_oracle_candidates_v2(views, expectations, reviews)[0]

    assert finding.evaluation_unit_status is EvaluationUnitStatusV2.INVALID
    assert reason in finding.invalid_unit_reasons


def test_wrong_scenario_review_linkage_is_a_hard_integrity_error(
    v2_bundle: tuple[
        tuple[PolicyViewV2, ...],
        tuple[OracleExpectationV2, ...],
        tuple[OracleReviewRecordV2, ...],
    ],
) -> None:
    views, expectations, reviews = v2_bundle
    wrong = reviews[0].model_copy(update={"scenario_id": "v2_scenario_099"})

    with pytest.raises(ArtifactIntegrityError, match="unknown v2 scenarios"):
        validate_oracle_candidates_v2(views, expectations, (wrong, *reviews[1:]))


@pytest.mark.parametrize(
    ("filename", "loader", "message"),
    (
        (
            "oracle_expectations.jsonl",
            load_oracle_expectations_v2,
            "duplicate v2 oracle expectation",
        ),
        ("oracle_reviews.jsonl", load_oracle_reviews_v2, "duplicate v2 oracle review"),
    ),
)
def test_duplicate_v2_authoring_rows_fail_loudly(
    filename: str,
    loader: object,
    message: str,
    tmp_path: Path,
) -> None:
    rows = (FIXTURES / filename).read_text().splitlines()
    path = tmp_path / filename
    path.write_text("\n".join([*rows, rows[0]]) + "\n")

    with pytest.raises(ArtifactIntegrityError, match=message):
        loader(path)  # type: ignore[operator]


def test_malformed_review_artifact_fails_schema_validation(tmp_path: Path) -> None:
    payload = json.loads((FIXTURES / "oracle_reviews.jsonl").read_text().splitlines()[0])
    payload["policy_decision"] = "SELECT"
    path = tmp_path / "malformed.jsonl"
    path.write_text(json.dumps(payload) + "\n")

    with pytest.raises(SchemaInvalidError, match="SCHEMA_INVALID"):
        load_oracle_reviews_v2(path)
