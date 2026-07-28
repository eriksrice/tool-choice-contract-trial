from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import tool_choice_contract_trial.blind_model_review as integration_module
from tool_choice_contract_trial.blind_model_review import (
    EXPECTED_BLIND_PACKET_SHA256,
    EXPECTED_PRIVATE_MAP_SHA256,
    EXPECTED_RAW_MODEL_REVIEW_SHA256,
    EXPECTED_REVIEW_PROTOCOL_SHA256,
    EXPECTED_SOURCE_COMMIT_SHA,
    EXPECTED_UNBLINDING,
    BlindModelReviewEvidenceBundleV2,
    build_blind_model_review_evidence_v2,
    file_sha256,
    verify_blind_model_review_comparisons_against_sources_v2,
    verify_blind_model_review_evidence_v2,
    verify_published_blind_model_review_sources_v2,
)
from tool_choice_contract_trial.blind_model_review_io import (
    load_blind_model_review_comparisons_v2,
    load_blind_model_review_provenance_manifest_v2,
    load_blind_model_review_records_v2,
    load_blind_model_review_responses_v2,
    write_blind_model_review_provenance_manifest_v2,
)
from tool_choice_contract_trial.blind_model_review_models import (
    BLIND_MODEL_REVIEW_KIND,
    BlindCaseAliasMappingV2,
    BlindModelReviewComparisonStatusV2,
    BlindModelReviewConfidenceV2,
    BlindModelReviewResponseV2,
    BlindPacketCaseV2,
    BlindPrivateCaseMapV2,
    BlindPrivateSourceManifestV2,
    BlindToolAliasMappingV2,
)
from tool_choice_contract_trial.blind_model_review_reporting import (
    render_blind_model_review_report_v2,
)
from tool_choice_contract_trial.errors import ArtifactIntegrityError, SchemaInvalidError
from tool_choice_contract_trial.serialization import canonical_json, write_jsonl
from tool_choice_contract_trial.v2_io import (
    load_oracle_expectations_v2,
    load_oracle_reviews_v2,
    load_oracle_validation_findings_v2,
    load_policy_views_v2,
    load_provisional_manifest_v2,
)
from tool_choice_contract_trial.v2_models import DecisionKindV2, OracleStateV2
from tool_choice_contract_trial.v2_validation import verify_provisional_manifest_v2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "milestone_2b" / "review_candidate"
OWNER_GOLDEN = ROOT / "tests" / "golden" / "milestone_2b"
PUBLIC_EVIDENCE = ROOT / "fixtures" / "milestone_2b" / "blind_model_review_001"
SOURCE_EVIDENCE = PUBLIC_EVIDENCE / "source_evidence"
REVIEW_PROTOCOL = PUBLIC_EVIDENCE / "review_protocol.md"

EXPECTED_OWNER_HASHES = {
    "oracle_validation_findings.jsonl": (
        "60b60f1df3e830cefcc3d1831e7dd96e14ce373f506fc9d6f21ab8394fa2f539"
    ),
    "provisional_bundle_manifest.json": (
        "09834c0cc013dfc27538f570773b36a17a3a3a51d0681657c3c91b2c16e785d8"
    ),
}


def _load_public_evidence() -> BlindModelReviewEvidenceBundleV2:
    records = load_blind_model_review_records_v2(PUBLIC_EVIDENCE / "model_review_records.jsonl")
    comparisons = load_blind_model_review_comparisons_v2(
        PUBLIC_EVIDENCE / "comparison_records.jsonl"
    )
    provenance = load_blind_model_review_provenance_manifest_v2(
        PUBLIC_EVIDENCE / "review_provenance_manifest.json"
    )
    return BlindModelReviewEvidenceBundleV2(
        records=records,
        comparisons=comparisons,
        provenance=provenance,
    )


def _write_synthetic_blind_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[BlindModelReviewEvidenceBundleV2, dict[str, Path]]:
    """Exercise integration without publishing or depending on the private source map."""

    views = load_policy_views_v2(SOURCE / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(SOURCE / "oracle_expectations.jsonl")
    reviews = load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl")
    findings = load_oracle_validation_findings_v2(OWNER_GOLDEN / "oracle_validation_findings.jsonl")
    findings_by_id = {row.scenario_id: row for row in findings}
    expected_unblinding: dict[str, str] = {}
    packet_cases: list[BlindPacketCaseV2] = []
    map_cases: list[BlindCaseAliasMappingV2] = []
    responses: list[BlindModelReviewResponseV2] = []

    for index, view in enumerate(views, start=1):
        blind_case_id = f"blind_case_{index:02d}"
        blind_contract_id = f"blind_contract_{index:02d}"
        expected_unblinding[blind_case_id] = view.scenario_id
        tool_aliases = {
            tool.tool_id: f"candidate_tool_{chr(ord('a') + position)}"
            for position, tool in enumerate(view.tools)
        }
        blind_tools = tuple(
            tool.model_validate(
                {**tool.model_dump(mode="json"), "tool_id": tool_aliases[tool.tool_id]}
            )
            for tool in view.tools
        )
        contract_data = view.contract.model_dump(mode="json")
        contract_data["contract_id"] = blind_contract_id
        contract_data["forbidden_tool_ids"] = [
            tool_aliases[tool_id] for tool_id in view.contract.forbidden_tool_ids
        ]
        if view.contract.required_tool_id is not None:
            contract_data["required_tool_id"] = tool_aliases[view.contract.required_tool_id]
        packet_cases.append(
            BlindPacketCaseV2(
                blind_case_id=blind_case_id,
                contract=view.contract.model_validate(contract_data),
                tools=blind_tools,
            )
        )
        map_cases.append(
            BlindCaseAliasMappingV2(
                blind_case_id=blind_case_id,
                blind_contract_id=blind_contract_id,
                original_contract_id=view.contract.contract_id,
                original_scenario_id=view.scenario_id,
                original_scenario_position=index - 1,
                tools=tuple(
                    BlindToolAliasMappingV2(
                        blind_presentation_position=position,
                        blind_tool_id=tool_aliases[tool.tool_id],
                        original_tool_id=tool.tool_id,
                        original_tool_position=position,
                    )
                    for position, tool in enumerate(view.tools)
                ),
            )
        )
        finding = findings_by_id[view.scenario_id]
        note = "Realism is limited by abstract, self-declared manifest profiles."
        if view.scenario_id == "v2_scenario_007":
            note += " The verified_transcript requirement is artificial."
        if view.scenario_id == "v2_scenario_012":
            note = "The deliberately contradictory contract is intentionally artificial."
        responses.append(
            BlindModelReviewResponseV2(
                blind_case_id=blind_case_id,
                reviewed_oracle_state=finding.computed_oracle_state,
                reviewed_admissible_tool_ids=tuple(
                    tool_aliases[tool_id] for tool_id in finding.computed_admissible_tool_ids
                ),
                reviewed_decision=finding.computed_expected_decision,
                confidence=BlindModelReviewConfidenceV2.HIGH,
                semantic_ambiguity=False,
                ecological_validity_concern=True,
                review_notes=note,
            )
        )

    paths = {
        "packet": tmp_path / "blind_packet.md",
        "responses": tmp_path / "responses.jsonl",
        "protocol": tmp_path / "review_protocol.md",
        "map": tmp_path / "private_map.json",
        "manifest": tmp_path / "private_source_manifest.json",
    }
    packet_text = "# Synthetic blind packet\n\n" + "\n\n".join(
        f"```json\n{canonical_json(case)}\n```" for case in packet_cases
    )
    paths["packet"].write_text(packet_text + "\n", encoding="utf-8", newline="\n")
    write_jsonl(paths["responses"], responses)
    paths["protocol"].write_bytes(REVIEW_PROTOCOL.read_bytes())
    private_map = BlindPrivateCaseMapV2(
        _warning="DO NOT SHARE WITH THE REVIEWER — test-only synthetic map",
        alias_scope={
            "contract_aliases": "global",
            "scenario_aliases": "global",
            "tool_aliases": "per blind case",
        },
        blind_seed=integration_module.EXPECTED_BLIND_SEED,
        cases=tuple(map_cases),
    )
    paths["map"].write_text(
        json.dumps(
            private_map.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    packet_hash = file_sha256(paths["packet"])
    map_hash = file_sha256(paths["map"])
    raw_review_hash = file_sha256(paths["responses"])
    private_manifest = BlindPrivateSourceManifestV2(
        _warning="DO NOT SHARE WITH THE REVIEWER — test-only source manifest",
        aliases_are_bijective=True,
        blind_packet_sha256=packet_hash,
        blind_seed=integration_module.EXPECTED_BLIND_SEED,
        confirmation_no_prohibited_answer_bearing_source_was_read=True,
        private_case_map_sha256=map_hash,
        response_template_sha256="0" * 64,
        scenario_count=12,
        semantic_fields_round_trip_exactly=True,
        source_commit_sha=EXPECTED_SOURCE_COMMIT_SHA,
        source_scenario_sha256=file_sha256(SOURCE / "scenarios.jsonl"),
        transformation="Test-only deterministic aliasing.",
        v2_schema_version="2.1.0",
        validation={
            "all_source_scenarios_appear_exactly_once": True,
            "all_tool_references_map_consistently": True,
            "exactly_twelve_cases": True,
            "original_identifiers_absent_from_shared_files": True,
            "prohibited_answer_terms_absent_from_shared_files": True,
            "reverse_mapping_reproduces_complete_source_records": True,
        },
    )
    paths["manifest"].write_text(
        json.dumps(
            private_manifest.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(integration_module, "EXPECTED_BLIND_PACKET_SHA256", packet_hash)
    monkeypatch.setattr(integration_module, "EXPECTED_PRIVATE_MAP_SHA256", map_hash)
    monkeypatch.setattr(integration_module, "EXPECTED_RAW_MODEL_REVIEW_SHA256", raw_review_hash)
    monkeypatch.setattr(integration_module, "EXPECTED_UNBLINDING", expected_unblinding)

    evidence = build_blind_model_review_evidence_v2(
        scenarios_path=SOURCE / "scenarios.jsonl",
        policy_views=views,
        expectations=expectations,
        owner_reviews=reviews,
        owner_findings=findings,
        owner_findings_path=OWNER_GOLDEN / "oracle_validation_findings.jsonl",
        owner_manifest=load_provisional_manifest_v2(
            OWNER_GOLDEN / "provisional_bundle_manifest.json"
        ),
        owner_manifest_path=OWNER_GOLDEN / "provisional_bundle_manifest.json",
        blind_packet_path=paths["packet"],
        raw_review_path=paths["responses"],
        review_protocol_path=paths["protocol"],
        private_case_map_path=paths["map"],
        private_source_manifest_path=paths["manifest"],
    )
    return evidence, paths


def test_synthetic_source_integration_validates_and_reverses_all_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence, paths = _write_synthetic_blind_sources(tmp_path, monkeypatch)

    assert len(load_blind_model_review_responses_v2(paths["responses"])) == 12
    assert len(evidence.records) == 12
    assert len(evidence.comparisons) == 12
    assert all(
        "candidate_tool_" not in tool_id
        for record in evidence.records
        for tool_id in record.reviewed_admissible_tool_ids
    )
    assert all(
        row.comparison_status is BlindModelReviewComparisonStatusV2.FULL_AGREEMENT
        for row in evidence.comparisons
    )


def test_raw_review_rejects_duplicates_missing_cases_invalid_alias_and_bad_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, paths = _write_synthetic_blind_sources(tmp_path, monkeypatch)
    original = paths["responses"].read_text(encoding="utf-8")
    lines = original.splitlines()

    paths["responses"].write_text(original + lines[0] + "\n", encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="duplicate"):
        load_blind_model_review_responses_v2(paths["responses"])

    paths["responses"].write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        integration_module,
        "EXPECTED_RAW_MODEL_REVIEW_SHA256",
        file_sha256(paths["responses"]),
    )
    with pytest.raises(ArtifactIntegrityError, match="incomplete case set"):
        build_blind_model_review_evidence_v2(
            scenarios_path=SOURCE / "scenarios.jsonl",
            policy_views=load_policy_views_v2(SOURCE / "scenarios.jsonl"),
            expectations=load_oracle_expectations_v2(SOURCE / "oracle_expectations.jsonl"),
            owner_reviews=load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl"),
            owner_findings=load_oracle_validation_findings_v2(
                OWNER_GOLDEN / "oracle_validation_findings.jsonl"
            ),
            owner_findings_path=OWNER_GOLDEN / "oracle_validation_findings.jsonl",
            owner_manifest=load_provisional_manifest_v2(
                OWNER_GOLDEN / "provisional_bundle_manifest.json"
            ),
            owner_manifest_path=OWNER_GOLDEN / "provisional_bundle_manifest.json",
            blind_packet_path=paths["packet"],
            raw_review_path=paths["responses"],
            review_protocol_path=paths["protocol"],
            private_case_map_path=paths["map"],
            private_source_manifest_path=paths["manifest"],
        )

    bad_alias = json.loads(lines[0])
    bad_alias["reviewed_admissible_tool_ids"] = ["candidate_tool_z"]
    paths["responses"].write_text(
        "\n".join([json.dumps(bad_alias), *lines[1:]]) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        integration_module,
        "EXPECTED_RAW_MODEL_REVIEW_SHA256",
        file_sha256(paths["responses"]),
    )
    with pytest.raises(ArtifactIntegrityError, match="unknown tool aliases"):
        build_blind_model_review_evidence_v2(
            scenarios_path=SOURCE / "scenarios.jsonl",
            policy_views=load_policy_views_v2(SOURCE / "scenarios.jsonl"),
            expectations=load_oracle_expectations_v2(SOURCE / "oracle_expectations.jsonl"),
            owner_reviews=load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl"),
            owner_findings=load_oracle_validation_findings_v2(
                OWNER_GOLDEN / "oracle_validation_findings.jsonl"
            ),
            owner_findings_path=OWNER_GOLDEN / "oracle_validation_findings.jsonl",
            owner_manifest=load_provisional_manifest_v2(
                OWNER_GOLDEN / "provisional_bundle_manifest.json"
            ),
            owner_manifest_path=OWNER_GOLDEN / "provisional_bundle_manifest.json",
            blind_packet_path=paths["packet"],
            raw_review_path=paths["responses"],
            review_protocol_path=paths["protocol"],
            private_case_map_path=paths["map"],
            private_source_manifest_path=paths["manifest"],
        )

    bad_shape = json.loads(lines[0])
    bad_shape["reviewed_decision"] = DecisionKindV2.NO_TOOL.value
    paths["responses"].write_text(json.dumps(bad_shape) + "\n", encoding="utf-8")
    with pytest.raises(SchemaInvalidError, match="requires SELECT"):
        load_blind_model_review_responses_v2(paths["responses"])


def test_registered_public_provenance_hashes_and_unblinding_are_exact() -> None:
    evidence = _load_public_evidence()

    assert evidence.provenance.source_packet_sha256 == EXPECTED_BLIND_PACKET_SHA256
    assert evidence.provenance.review_protocol_sha256 == EXPECTED_REVIEW_PROTOCOL_SHA256
    assert evidence.provenance.private_map_sha256 == EXPECTED_PRIVATE_MAP_SHA256
    assert evidence.provenance.source_commit_sha == EXPECTED_SOURCE_COMMIT_SHA
    assert {
        record.blind_case_id: record.scenario_id for record in evidence.records
    } == EXPECTED_UNBLINDING
    assert evidence.provenance.raw_review_sha256 == (EXPECTED_RAW_MODEL_REVIEW_SHA256)
    verify_published_blind_model_review_sources_v2(
        evidence.provenance,
        blind_packet_path=SOURCE_EVIDENCE / "blind_review_packet.md",
        raw_review_path=SOURCE_EVIDENCE / "raw_model_review_response.jsonl",
        review_protocol_path=REVIEW_PROTOCOL,
    )


def test_review_protocol_records_exact_session_and_identity_check_evidence() -> None:
    evidence = _load_public_evidence()
    protocol = REVIEW_PROTOCOL.read_text(encoding="utf-8")

    assert evidence.provenance.reviewer_platform == "ChatGPT"
    assert evidence.provenance.review_session_type.value == "TEMPORARY_CHAT"
    assert evidence.provenance.reviewer_model_identifier == "NOT_RECORDED"
    assert evidence.provenance.human_reviewer is False
    assert evidence.provenance.packet_identity_check_passed is True
    assert "Do not evaluate or solve any cases yet." in protocol
    assert "schema_version: 2.1.0" in protocol
    assert "candidate_tool_b, candidate_tool_a" in protocol
    assert "This established packet availability and identity before review." in protocol
    assert "Now perform the blind independent review using only the attached packet." in protocol


def test_public_comparisons_are_source_aware_and_have_exact_expected_counts() -> None:
    evidence = _load_public_evidence()
    views = load_policy_views_v2(SOURCE / "scenarios.jsonl")
    expectations = load_oracle_expectations_v2(SOURCE / "oracle_expectations.jsonl")
    owner_reviews = load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl")
    owner_findings = load_oracle_validation_findings_v2(
        OWNER_GOLDEN / "oracle_validation_findings.jsonl"
    )
    owner_manifest = load_provisional_manifest_v2(OWNER_GOLDEN / "provisional_bundle_manifest.json")

    verify_provisional_manifest_v2(
        owner_manifest, views, expectations, owner_reviews, owner_findings
    )
    verify_blind_model_review_comparisons_against_sources_v2(
        evidence.records,
        evidence.comparisons,
        views,
        owner_reviews,
        owner_findings,
    )
    verify_blind_model_review_evidence_v2(
        evidence.records, evidence.comparisons, evidence.provenance
    )
    assert len(evidence.comparisons) == 12
    assert (
        sum(
            row.comparison_status is BlindModelReviewComparisonStatusV2.FULL_AGREEMENT
            for row in evidence.comparisons
        )
        == 12
    )
    assert not any(
        not row.state_agreement or not row.admissible_set_agreement or not row.decision_agreement
        for row in evidence.comparisons
    )


def test_confidence_ambiguity_and_ecological_notes_are_preserved() -> None:
    evidence = _load_public_evidence()
    records = {record.scenario_id: record for record in evidence.records}

    assert all(
        record.confidence is BlindModelReviewConfidenceV2.HIGH for record in records.values()
    )
    assert not any(record.semantic_ambiguity for record in records.values())
    assert all(record.ecological_validity_concern for record in records.values())
    assert "verified_transcript" in (records["v2_scenario_007"].review_notes or "")
    assert "deliberately contradictory contract" in (records["v2_scenario_012"].review_notes or "")


def test_model_review_stays_separate_from_owner_review_and_human_review() -> None:
    evidence = _load_public_evidence()
    owner_bytes = (SOURCE / "oracle_reviews.jsonl").read_bytes()

    assert all(record.review_kind == BLIND_MODEL_REVIEW_KIND for record in evidence.records)
    assert b"BLIND_INDEPENDENT_MODEL_REVIEW" not in owner_bytes
    assert evidence.provenance.independent_human_review_performed is False
    assert evidence.provenance.human_reviewer is False
    assert evidence.provenance.benchmark_frozen is False
    assert evidence.provenance.policy_evaluation_performed is False


def test_report_is_a_deterministic_projection_with_precise_claim_boundaries() -> None:
    evidence = _load_public_evidence()
    rendered = render_blind_model_review_report_v2(
        evidence.records, evidence.comparisons, evidence.provenance
    )

    assert rendered.encode() == (PUBLIC_EVIDENCE / "comparison_report.md").read_bytes()
    assert "Blind independent model review: 12/12 full agreement" in rendered
    assert "Independent human review has not been performed" in rendered
    assert "somewhat artificial for the stated knowledge-packet task" in rendered
    assert "diagnostically useful but intentionally artificial" in rendered
    assert "candidate remains provisional and unfrozen" in rendered
    assert "No policy decisions" in rendered
    assert "No live-model policy evaluation or runtime model invocation" in rendered
    assert "completed external blind model-review session" in rendered
    assert "No policy decisions, policy metrics, or runtime tool execution" in rendered
    assert "No policy decisions, policy metrics, live models" not in rendered
    assert "A clean public clone can verify" in rendered
    assert "cannot repeat the original alias reversal" in rendered


def test_provenance_distinguishes_policy_visible_manifests_from_withheld_evidence() -> None:
    provenance = _load_public_evidence().provenance

    assert "manifests" not in provenance.withheld_answer_bearing_sources
    assert "owner_provisional_manifest" in provenance.withheld_answer_bearing_sources
    assert "owner_review_records" in provenance.withheld_answer_bearing_sources
    assert "private_case_map" in provenance.withheld_answer_bearing_sources
    assert provenance.blind_packet_published is True
    assert provenance.raw_review_published is True
    assert provenance.private_map_published is False
    assert provenance.private_source_manifest_published is False
    assert provenance.public_clone_can_verify_source_packet is True
    assert provenance.public_clone_can_verify_raw_response is True
    assert provenance.public_clone_can_repeat_unblinding is False


def test_canonical_evidence_serialization_is_byte_deterministic(tmp_path: Path) -> None:
    evidence = _load_public_evidence()
    first = tmp_path / "first"
    second = tmp_path / "second"
    for directory in (first, second):
        write_jsonl(directory / "model_review_records.jsonl", evidence.records)
        write_jsonl(directory / "comparison_records.jsonl", evidence.comparisons)
        write_blind_model_review_provenance_manifest_v2(
            directory / "review_provenance_manifest.json", evidence.provenance
        )

    for name in (
        "model_review_records.jsonl",
        "comparison_records.jsonl",
        "review_provenance_manifest.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()
        assert (first / name).read_bytes() == (PUBLIC_EVIDENCE / name).read_bytes()


def test_owner_evidence_hashes_remain_unchanged() -> None:
    actual = {
        name: hashlib.sha256((OWNER_GOLDEN / name).read_bytes()).hexdigest()
        for name in EXPECTED_OWNER_HASHES
    }
    assert actual == EXPECTED_OWNER_HASHES


def test_canonical_records_and_comparisons_remain_byte_identical() -> None:
    assert file_sha256(PUBLIC_EVIDENCE / "model_review_records.jsonl") == (
        "4340c0d23a40f1d5c0505bb64ef78ed6834580e6aafd721eb66f4cdaa5d88db8"
    )
    assert file_sha256(PUBLIC_EVIDENCE / "comparison_records.jsonl") == (
        "b8713c9ea4e5776fa319ef0a7c31e2ed122cc83bf240fa5c5083719415b31b5b"
    )


def test_public_bundle_excludes_private_sources_and_paths() -> None:
    forbidden = (
        "/" + "Users/",
        "PRIVATE_" + "case_map",
        "PRIVATE_" + "source_manifest",
        "-".join(("tool", "choice", "contract", "trial", "independent", "review")),
    )
    files = tuple(path for path in PUBLIC_EVIDENCE.rglob("*") if path.is_file())

    assert {str(path.relative_to(PUBLIC_EVIDENCE)) for path in files} == {
        "comparison_records.jsonl",
        "comparison_report.md",
        "model_review_records.jsonl",
        "review_protocol.md",
        "review_provenance_manifest.json",
        "source_evidence/blind_review_packet.md",
        "source_evidence/raw_model_review_response.jsonl",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden), path

    canonical_files = (
        PUBLIC_EVIDENCE / "model_review_records.jsonl",
        PUBLIC_EVIDENCE / "comparison_records.jsonl",
        PUBLIC_EVIDENCE / "review_provenance_manifest.json",
        PUBLIC_EVIDENCE / "comparison_report.md",
    )
    assert all(
        "candidate_tool_" not in path.read_text(encoding="utf-8") for path in canonical_files
    )


def test_source_files_and_public_bundle_are_mutation_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, paths = _write_synthetic_blind_sources(tmp_path, monkeypatch)
    original_packet = paths["packet"].read_bytes()
    original_map = paths["map"].read_bytes()
    original_raw = paths["responses"].read_bytes()

    paths["packet"].write_bytes(original_packet + b"\n")
    with pytest.raises(ArtifactIntegrityError, match="packet hash"):
        _write_evidence_from_paths(paths)
    paths["packet"].write_bytes(original_packet)

    paths["map"].write_bytes(original_map + b"\n")
    with pytest.raises(ArtifactIntegrityError, match="case-map hash"):
        _write_evidence_from_paths(paths)
    paths["map"].write_bytes(original_map)

    raw_rows = original_raw.decode().splitlines()
    changed = json.loads(raw_rows[0])
    changed["review_notes"] = "A valid but mutated test-only review note."
    raw_rows[0] = json.dumps(changed, separators=(",", ":"), sort_keys=True)
    paths["responses"].write_text("\n".join(raw_rows) + "\n", encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="raw review hash"):
        _write_evidence_from_paths(paths)

    paths["responses"].write_bytes(original_raw)
    paths["protocol"].write_bytes(REVIEW_PROTOCOL.read_bytes() + b"\n")
    with pytest.raises(ArtifactIntegrityError, match="review protocol hash"):
        _write_evidence_from_paths(paths)


def _write_evidence_from_paths(paths: dict[str, Path]) -> BlindModelReviewEvidenceBundleV2:
    return build_blind_model_review_evidence_v2(
        scenarios_path=SOURCE / "scenarios.jsonl",
        policy_views=load_policy_views_v2(SOURCE / "scenarios.jsonl"),
        expectations=load_oracle_expectations_v2(SOURCE / "oracle_expectations.jsonl"),
        owner_reviews=load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl"),
        owner_findings=load_oracle_validation_findings_v2(
            OWNER_GOLDEN / "oracle_validation_findings.jsonl"
        ),
        owner_findings_path=OWNER_GOLDEN / "oracle_validation_findings.jsonl",
        owner_manifest=load_provisional_manifest_v2(
            OWNER_GOLDEN / "provisional_bundle_manifest.json"
        ),
        owner_manifest_path=OWNER_GOLDEN / "provisional_bundle_manifest.json",
        blind_packet_path=paths["packet"],
        raw_review_path=paths["responses"],
        review_protocol_path=paths["protocol"],
        private_case_map_path=paths["map"],
        private_source_manifest_path=paths["manifest"],
    )


def test_source_aware_comparison_rejects_a_semantic_record_mutation() -> None:
    evidence = _load_public_evidence()
    changed = evidence.records[0].model_copy(
        update={
            "reviewed_oracle_state": OracleStateV2.NO_ADMISSIBLE,
            "reviewed_admissible_tool_ids": (),
            "reviewed_decision": DecisionKindV2.NO_TOOL,
        }
    )

    with pytest.raises(ArtifactIntegrityError, match="comparison does not match"):
        verify_blind_model_review_comparisons_against_sources_v2(
            (changed, *evidence.records[1:]),
            evidence.comparisons,
            load_policy_views_v2(SOURCE / "scenarios.jsonl"),
            load_oracle_reviews_v2(SOURCE / "oracle_reviews.jsonl"),
            load_oracle_validation_findings_v2(OWNER_GOLDEN / "oracle_validation_findings.jsonl"),
        )
