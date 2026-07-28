"""Source-aware integration of one blind independent model-review protocol."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from .blind_model_review_io import (
    load_blind_model_review_responses_v2,
    load_blind_packet_cases_v2,
    load_blind_private_case_map_v2,
    load_blind_private_source_manifest_v2,
)
from .blind_model_review_models import (
    BLIND_MODEL_REVIEW_PROTOCOL_ID,
    BlindCaseAliasMappingV2,
    BlindModelReviewComparisonStatusV2,
    BlindModelReviewComparisonV2,
    BlindModelReviewConfidenceV2,
    BlindModelReviewProvenanceManifestV2,
    BlindModelReviewRecordV2,
    BlindModelReviewResponseV2,
    BlindPacketCaseV2,
)
from .errors import ArtifactIntegrityError
from .serialization import canonical_hash
from .v2_models import (
    DecisionKindV2,
    OracleExpectationV2,
    OracleReviewDispositionV2,
    OracleReviewRecordV2,
    OracleStateV2,
    OracleValidationFindingV2,
    PolicyViewV2,
    ProvisionalBundleManifestV2,
    TaskContractV2,
    ToolManifestV2,
)
from .v2_registry import V2_RELATION_REGISTRY_HASH
from .v2_validation import verify_provisional_manifest_v2

EXPECTED_BLIND_PACKET_SHA256 = "a3a10982ada95885b8d74b55e4b9c36ee51282161cd831614a46fa54d3275ab7"
EXPECTED_PRIVATE_MAP_SHA256 = "afe4b4dccdbc050c0283a29593c2b3bdfe4602c11b31f3d408a68d933ab0a8a3"
EXPECTED_RAW_MODEL_REVIEW_SHA256 = (
    "668b643ea126c746ed0f35d1f3859992e4a1c11ec0df24a74f2c121411f33da1"
)
EXPECTED_REVIEW_PROTOCOL_SHA256 = "4193e72ea938bdf4a1629b5807c1295f31511b7ea4e773568e684f5ab269f8d3"
EXPECTED_SOURCE_COMMIT_SHA = "c11741b5e628354ed0fdcae46e1e8c7908fe109a"
EXPECTED_BLIND_SEED = "tool-choice-contract-trial-v2.1-independent-review-001"
EXPECTED_UNBLINDING = {
    f"blind_case_{index:02d}": f"v2_scenario_{scenario:03d}"
    for index, scenario in enumerate((8, 11, 1, 4, 9, 2, 3, 6, 12, 7, 10, 5), start=1)
}
WITHHELD_ANSWER_BEARING_SOURCES = (
    "computed_findings",
    "oracle_expectations",
    "owner_review_records",
    "owner_provisional_manifest",
    "policy_outputs",
    "private_case_map",
    "repository_history",
)
BUNDLE_REALISM_PHRASE = "abstract, self-declared manifest profiles"


@dataclass(frozen=True)
class BlindModelReviewEvidenceBundleV2:
    records: tuple[BlindModelReviewRecordV2, ...]
    comparisons: tuple[BlindModelReviewComparisonV2, ...]
    provenance: BlindModelReviewProvenanceManifestV2


def file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ArtifactIntegrityError(f"cannot hash evidence source: {path}: {error}") from error


def _unique_by[Artifact: BaseModel](
    rows: Iterable[Artifact], field_name: str, artifact_name: str
) -> dict[str, Artifact]:
    materialized = tuple(rows)
    result = {str(getattr(row, field_name)): row for row in materialized}
    if len(result) != len(materialized):
        raise ArtifactIntegrityError(f"duplicate {artifact_name} {field_name} values")
    return result


def _bundle_hash(label: str, rows: Iterable[BaseModel]) -> str:
    ordered = sorted(rows, key=lambda row: str(row.scenario_id))  # type: ignore[attr-defined]
    return canonical_hash({label: [row.model_dump(mode="json") for row in ordered]})


def _decision_for_state(state: OracleStateV2) -> DecisionKindV2:
    return {
        OracleStateV2.UNIQUE_ADMISSIBLE: DecisionKindV2.SELECT,
        OracleStateV2.MULTIPLE_ADMISSIBLE: DecisionKindV2.INDETERMINATE,
        OracleStateV2.NO_ADMISSIBLE: DecisionKindV2.NO_TOOL,
        OracleStateV2.CONTRACT_INVALID: DecisionKindV2.INVALID_CONTRACT,
    }[state]


def _comparison_from_sources(
    *,
    scenario_id: str,
    owner_review: OracleReviewRecordV2,
    model_review: BlindModelReviewRecordV2,
    finding: OracleValidationFindingV2,
) -> BlindModelReviewComparisonV2:
    owner_state = owner_review.reviewed_expected_state
    owner_set = owner_review.reviewed_admissible_tool_ids
    if owner_state is None or owner_set is None:
        raise ArtifactIntegrityError("completed owner review lacks state or admissible set")
    owner_decision = _decision_for_state(owner_state)
    state_agreement = (
        owner_state is model_review.reviewed_oracle_state is finding.computed_oracle_state
    )
    admissible_set_agreement = (
        owner_set
        == model_review.reviewed_admissible_tool_ids
        == finding.computed_admissible_tool_ids
    )
    decision_agreement = (
        owner_decision is model_review.reviewed_decision is finding.computed_expected_decision
    )
    return BlindModelReviewComparisonV2(
        review_protocol_id=BLIND_MODEL_REVIEW_PROTOCOL_ID,
        scenario_id=scenario_id,
        owner_reviewed_state=owner_state,
        owner_reviewed_admissible_tool_ids=owner_set,
        owner_reviewed_decision=owner_decision,
        blind_model_reviewed_state=model_review.reviewed_oracle_state,
        blind_model_reviewed_admissible_tool_ids=model_review.reviewed_admissible_tool_ids,
        blind_model_reviewed_decision=model_review.reviewed_decision,
        computed_state=finding.computed_oracle_state,
        computed_admissible_tool_ids=finding.computed_admissible_tool_ids,
        computed_decision=finding.computed_expected_decision,
        state_agreement=state_agreement,
        admissible_set_agreement=admissible_set_agreement,
        decision_agreement=decision_agreement,
        semantic_ambiguity=model_review.semantic_ambiguity,
        ecological_validity_concern=model_review.ecological_validity_concern,
        comparison_status=(
            BlindModelReviewComparisonStatusV2.FULL_AGREEMENT
            if state_agreement and admissible_set_agreement and decision_agreement
            else BlindModelReviewComparisonStatusV2.DISAGREEMENT
        ),
    )


def _verify_packet_case_round_trip(
    packet_case: BlindPacketCaseV2,
    mapping: BlindCaseAliasMappingV2,
    source_view: PolicyViewV2,
) -> dict[str, str]:
    if packet_case.blind_case_id != mapping.blind_case_id:
        raise ArtifactIntegrityError("blind packet case does not match private case mapping")
    if mapping.original_scenario_id != source_view.scenario_id:
        raise ArtifactIntegrityError("private case mapping does not match source scenario")
    if mapping.original_contract_id != source_view.contract.contract_id:
        raise ArtifactIntegrityError("private contract mapping does not match source contract")
    if packet_case.contract.contract_id != mapping.blind_contract_id:
        raise ArtifactIntegrityError("blind contract alias does not match private case mapping")

    mappings_by_blind_id = {row.blind_tool_id: row for row in mapping.tools}
    packet_tool_ids = tuple(tool.tool_id for tool in packet_case.tools)
    if set(mappings_by_blind_id) != set(packet_tool_ids):
        raise ArtifactIntegrityError("blind packet tool aliases do not match private case mapping")
    for position, tool in enumerate(packet_case.tools):
        tool_mapping = mappings_by_blind_id[tool.tool_id]
        if tool_mapping.blind_presentation_position != position:
            raise ArtifactIntegrityError("blind packet tool presentation order does not match map")
        if tool_mapping.original_tool_position >= len(source_view.tools):
            raise ArtifactIntegrityError("private map original tool position is out of range")
        source_tool = source_view.tools[tool_mapping.original_tool_position]
        if source_tool.tool_id != tool_mapping.original_tool_id:
            raise ArtifactIntegrityError("private tool mapping does not match source tool position")
        unblinded_tool = ToolManifestV2.model_validate(
            {**tool.model_dump(mode="json"), "tool_id": tool_mapping.original_tool_id}
        )
        if unblinded_tool != source_tool:
            raise ArtifactIntegrityError("blind tool manifest does not round-trip to source")

    original_tool_ids = {row.blind_tool_id: row.original_tool_id for row in mapping.tools}
    try:
        unblinded_contract_data = packet_case.contract.model_dump(mode="json")
        unblinded_contract_data["contract_id"] = mapping.original_contract_id
        unblinded_contract_data["forbidden_tool_ids"] = [
            original_tool_ids[tool_id] for tool_id in packet_case.contract.forbidden_tool_ids
        ]
        if packet_case.contract.required_tool_id is not None:
            unblinded_contract_data["required_tool_id"] = original_tool_ids[
                packet_case.contract.required_tool_id
            ]
    except KeyError as error:
        raise ArtifactIntegrityError(
            f"blind contract references an unmapped tool alias: {error.args[0]}"
        ) from error
    if TaskContractV2.model_validate(unblinded_contract_data) != source_view.contract:
        raise ArtifactIntegrityError("blind contract does not round-trip to source")
    return original_tool_ids


def _unblind_note(note: str | None, tool_ids: dict[str, str]) -> str | None:
    if note is None:
        return None
    unblinded = note
    for blind_tool_id, original_tool_id in sorted(
        tool_ids.items(), key=lambda item: len(item[0]), reverse=True
    ):
        unblinded = re.sub(rf"\b{re.escape(blind_tool_id)}\b", original_tool_id, unblinded)
    if re.search(r"\bcandidate_tool_[a-z]+\b", unblinded):
        raise ArtifactIntegrityError("review note contains an unmapped blind tool alias")
    return unblinded


def verify_blind_model_review_evidence_v2(
    records: Iterable[BlindModelReviewRecordV2],
    comparisons: Iterable[BlindModelReviewComparisonV2],
    provenance: BlindModelReviewProvenanceManifestV2,
) -> None:
    record_rows = tuple(sorted(records, key=lambda row: row.scenario_id))
    comparison_rows = tuple(sorted(comparisons, key=lambda row: row.scenario_id))
    records_by_id = _unique_by(record_rows, "scenario_id", "blind model review record")
    comparisons_by_id = _unique_by(comparison_rows, "scenario_id", "blind model review comparison")
    if set(records_by_id) != set(comparisons_by_id):
        raise ArtifactIntegrityError("blind review record and comparison scenario sets differ")
    if provenance.reviewed_case_count != len(record_rows):
        raise ArtifactIntegrityError("reviewed_case_count differs from canonical records")
    if provenance.review_record_bundle_hash != _bundle_hash(
        "blind_model_review_records_v2", record_rows
    ):
        raise ArtifactIntegrityError("review_record_bundle_hash differs from canonical records")
    if provenance.comparison_bundle_hash != _bundle_hash(
        "blind_model_review_comparisons_v2", comparison_rows
    ):
        raise ArtifactIntegrityError("comparison_bundle_hash differs from comparisons")
    if provenance.withheld_answer_bearing_sources != tuple(sorted(WITHHELD_ANSWER_BEARING_SOURCES)):
        raise ArtifactIntegrityError(
            "withheld_answer_bearing_sources differs from the registered protocol"
        )

    for scenario_id, record in records_by_id.items():
        comparison = comparisons_by_id[scenario_id]
        if (
            comparison.blind_model_reviewed_state is not record.reviewed_oracle_state
            or comparison.blind_model_reviewed_admissible_tool_ids
            != record.reviewed_admissible_tool_ids
            or comparison.blind_model_reviewed_decision is not record.reviewed_decision
            or comparison.semantic_ambiguity != record.semantic_ambiguity
            or comparison.ecological_validity_concern != record.ecological_validity_concern
        ):
            raise ArtifactIntegrityError(
                f"comparison differs from blind model review record: {scenario_id}"
            )
        if (
            record.review_protocol_id != provenance.review_protocol_id
            or record.source_packet_hash != provenance.source_packet_sha256
            or record.private_map_hash != provenance.private_map_sha256
            or record.source_commit_sha != provenance.source_commit_sha
        ):
            raise ArtifactIntegrityError(
                f"record provenance differs from public manifest: {scenario_id}"
            )

    expected_counts = {
        BlindModelReviewComparisonStatusV2.FULL_AGREEMENT: provenance.full_agreement_count,
        BlindModelReviewComparisonStatusV2.DISAGREEMENT: provenance.disagreement_count,
        BlindModelReviewComparisonStatusV2.INVALID_REVIEW_ARTIFACT: (
            provenance.invalid_review_artifact_count
        ),
    }
    for status, expected_count in expected_counts.items():
        if sum(row.comparison_status is status for row in comparison_rows) != expected_count:
            raise ArtifactIntegrityError(f"{status.value} count differs from comparisons")
    if (
        sum(record.confidence is BlindModelReviewConfidenceV2.HIGH for record in record_rows)
        != provenance.high_confidence_count
    ):
        raise ArtifactIntegrityError("high_confidence_count differs from review records")
    if sum(record.semantic_ambiguity for record in record_rows) != (
        provenance.semantic_ambiguity_count
    ):
        raise ArtifactIntegrityError("semantic_ambiguity_count differs from review records")
    if sum(record.ecological_validity_concern for record in record_rows) != (
        provenance.ecological_validity_concern_count
    ):
        raise ArtifactIntegrityError(
            "ecological_validity_concern_count differs from review records"
        )
    bundle_concern_count = sum(
        record.review_notes is not None and BUNDLE_REALISM_PHRASE in record.review_notes
        for record in record_rows
    )
    if bundle_concern_count != provenance.bundle_level_declared_manifest_concern_count:
        raise ArtifactIntegrityError(
            "bundle_level_declared_manifest_concern_count differs from review notes"
        )


def verify_published_blind_model_review_sources_v2(
    provenance: BlindModelReviewProvenanceManifestV2,
    *,
    blind_packet_path: Path,
    raw_review_path: Path,
    review_protocol_path: Path,
) -> None:
    """Verify the exact public review inputs, output, and protocol commitments."""

    if provenance.source_packet_sha256 != EXPECTED_BLIND_PACKET_SHA256:
        raise ArtifactIntegrityError("provenance blind packet hash is not registered")
    if provenance.raw_review_sha256 != EXPECTED_RAW_MODEL_REVIEW_SHA256:
        raise ArtifactIntegrityError("provenance raw review hash is not registered")
    if provenance.review_protocol_sha256 != EXPECTED_REVIEW_PROTOCOL_SHA256:
        raise ArtifactIntegrityError("provenance review protocol hash is not registered")
    if file_sha256(blind_packet_path) != provenance.source_packet_sha256:
        raise ArtifactIntegrityError("published blind packet hash differs from provenance")
    if file_sha256(raw_review_path) != provenance.raw_review_sha256:
        raise ArtifactIntegrityError("published raw review hash differs from provenance")
    if file_sha256(review_protocol_path) != provenance.review_protocol_sha256:
        raise ArtifactIntegrityError("published review protocol hash differs from provenance")


def verify_blind_model_review_comparisons_against_sources_v2(
    records: Iterable[BlindModelReviewRecordV2],
    comparisons: Iterable[BlindModelReviewComparisonV2],
    policy_views: Iterable[PolicyViewV2],
    owner_reviews: Iterable[OracleReviewRecordV2],
    owner_findings: Iterable[OracleValidationFindingV2],
) -> None:
    """Rebuild every public comparison from its separate repository sources."""

    records_by_id = _unique_by(records, "scenario_id", "blind model review record")
    comparisons_by_id = _unique_by(comparisons, "scenario_id", "blind model comparison")
    views_by_id = _unique_by(policy_views, "scenario_id", "v2 policy view")
    reviews_by_id = _unique_by(owner_reviews, "scenario_id", "owner review")
    findings_by_id = _unique_by(owner_findings, "scenario_id", "owner finding")
    scenario_ids = set(views_by_id)
    if not (
        set(records_by_id)
        == set(comparisons_by_id)
        == set(reviews_by_id)
        == set(findings_by_id)
        == scenario_ids
    ):
        raise ArtifactIntegrityError(
            "blind-review and owner-evidence scenario sets do not match source policy views"
        )
    for scenario_id in sorted(scenario_ids):
        available_tool_ids = {tool.tool_id for tool in views_by_id[scenario_id].tools}
        if not set(records_by_id[scenario_id].reviewed_admissible_tool_ids).issubset(
            available_tool_ids
        ):
            raise ArtifactIntegrityError(
                f"blind review references an unavailable source tool: {scenario_id}"
            )
        expected = _comparison_from_sources(
            scenario_id=scenario_id,
            owner_review=reviews_by_id[scenario_id],
            model_review=records_by_id[scenario_id],
            finding=findings_by_id[scenario_id],
        )
        if comparisons_by_id[scenario_id] != expected:
            raise ArtifactIntegrityError(
                f"comparison does not match its owner, model, and computed sources: {scenario_id}"
            )


def build_blind_model_review_evidence_v2(
    *,
    scenarios_path: Path,
    policy_views: Iterable[PolicyViewV2],
    expectations: Iterable[OracleExpectationV2],
    owner_reviews: Iterable[OracleReviewRecordV2],
    owner_findings: Iterable[OracleValidationFindingV2],
    owner_findings_path: Path,
    owner_manifest: ProvisionalBundleManifestV2,
    owner_manifest_path: Path,
    blind_packet_path: Path,
    raw_review_path: Path,
    review_protocol_path: Path,
    private_case_map_path: Path,
    private_source_manifest_path: Path,
) -> BlindModelReviewEvidenceBundleV2:
    view_rows = tuple(policy_views)
    expectation_rows = tuple(expectations)
    owner_review_rows = tuple(owner_reviews)
    owner_finding_rows = tuple(owner_findings)
    verify_provisional_manifest_v2(
        owner_manifest,
        view_rows,
        expectation_rows,
        owner_review_rows,
        owner_finding_rows,
    )

    views_by_id = _unique_by(view_rows, "scenario_id", "v2 policy view")
    reviews_by_id = _unique_by(owner_review_rows, "scenario_id", "owner review")
    findings_by_id = _unique_by(owner_finding_rows, "scenario_id", "owner finding")
    if set(views_by_id) != set(reviews_by_id) or set(views_by_id) != set(findings_by_id):
        raise ArtifactIntegrityError("owner evidence does not cover the policy-view scenario set")
    for scenario_id, review in reviews_by_id.items():
        if (
            review.reviewer_role != "owner_reviewer"
            or review.disposition is not OracleReviewDispositionV2.AGREE
            or review.reviewed_expected_state is None
            or review.reviewed_admissible_tool_ids is None
            or review.review_performed_without_policy_outputs is not True
        ):
            raise ArtifactIntegrityError(
                "owner review is not a completed policy-output-independent agreement: "
                f"{scenario_id}"
            )

    packet_hash = file_sha256(blind_packet_path)
    map_hash = file_sha256(private_case_map_path)
    raw_review_hash = file_sha256(raw_review_path)
    review_protocol_hash = file_sha256(review_protocol_path)
    private_manifest_hash = file_sha256(private_source_manifest_path)
    source_scenario_hash = file_sha256(scenarios_path)
    if packet_hash != EXPECTED_BLIND_PACKET_SHA256:
        raise ArtifactIntegrityError("blind packet hash does not match the registered protocol")
    if map_hash != EXPECTED_PRIVATE_MAP_SHA256:
        raise ArtifactIntegrityError("private case-map hash does not match the registered protocol")
    if raw_review_hash != EXPECTED_RAW_MODEL_REVIEW_SHA256:
        raise ArtifactIntegrityError("raw review hash does not match the registered protocol")
    if review_protocol_hash != EXPECTED_REVIEW_PROTOCOL_SHA256:
        raise ArtifactIntegrityError("review protocol hash does not match the registered protocol")

    packet_cases = load_blind_packet_cases_v2(blind_packet_path)
    raw_reviews = load_blind_model_review_responses_v2(raw_review_path)
    private_map = load_blind_private_case_map_v2(private_case_map_path)
    private_manifest = load_blind_private_source_manifest_v2(private_source_manifest_path)
    if (
        private_manifest.blind_packet_sha256 != packet_hash
        or private_manifest.private_case_map_sha256 != map_hash
        or private_manifest.source_commit_sha != EXPECTED_SOURCE_COMMIT_SHA
        or private_manifest.source_scenario_sha256 != source_scenario_hash
        or private_manifest.blind_seed != EXPECTED_BLIND_SEED
        or private_map.blind_seed != EXPECTED_BLIND_SEED
        or private_manifest.scenario_count != len(view_rows)
    ):
        raise ArtifactIntegrityError("private blind-source provenance does not match repository")

    packet_by_id = _unique_by(packet_cases, "blind_case_id", "blind packet case")
    raw_reviews_by_id = _unique_by(raw_reviews, "blind_case_id", "blind model review response")
    mappings_by_id = _unique_by(private_map.cases, "blind_case_id", "private case map")
    expected_case_ids = set(EXPECTED_UNBLINDING)
    if (
        set(packet_by_id) != expected_case_ids
        or set(raw_reviews_by_id) != expected_case_ids
        or set(mappings_by_id) != expected_case_ids
    ):
        raise ArtifactIntegrityError("blind packet, responses, or map has an incomplete case set")
    actual_unblinding = {
        blind_case_id: mapping.original_scenario_id
        for blind_case_id, mapping in mappings_by_id.items()
    }
    if actual_unblinding != EXPECTED_UNBLINDING:
        raise ArtifactIntegrityError("private map differs from the registered unblinding")

    source_view_order = tuple(view_rows)
    alias_maps: dict[str, dict[str, str]] = {}
    for blind_case_id in sorted(expected_case_ids):
        mapping = mappings_by_id[blind_case_id]
        if mapping.original_scenario_position >= len(source_view_order):
            raise ArtifactIntegrityError("mapped source scenario position is out of range")
        source_view = source_view_order[mapping.original_scenario_position]
        alias_maps[blind_case_id] = _verify_packet_case_round_trip(
            packet_by_id[blind_case_id], mapping, source_view
        )

    records: list[BlindModelReviewRecordV2] = []
    for blind_case_id in sorted(expected_case_ids):
        response: BlindModelReviewResponseV2 = raw_reviews_by_id[blind_case_id]
        mapping = mappings_by_id[blind_case_id]
        source_view = views_by_id[mapping.original_scenario_id]
        alias_map = alias_maps[blind_case_id]
        unknown_aliases = sorted(set(response.reviewed_admissible_tool_ids) - set(alias_map))
        if unknown_aliases:
            raise ArtifactIntegrityError(
                f"reviewed admissible set contains unknown tool aliases: {unknown_aliases}"
            )
        original_tool_ids = tuple(
            sorted(alias_map[tool_id] for tool_id in response.reviewed_admissible_tool_ids)
        )
        if not set(original_tool_ids).issubset(tool.tool_id for tool in source_view.tools):
            raise ArtifactIntegrityError("unblinded review references an unavailable source tool")
        records.append(
            BlindModelReviewRecordV2(
                review_protocol_id=BLIND_MODEL_REVIEW_PROTOCOL_ID,
                blind_case_id=blind_case_id,
                scenario_id=mapping.original_scenario_id,
                reviewed_oracle_state=response.reviewed_oracle_state,
                reviewed_admissible_tool_ids=original_tool_ids,
                reviewed_decision=response.reviewed_decision,
                confidence=response.confidence,
                semantic_ambiguity=response.semantic_ambiguity,
                ecological_validity_concern=response.ecological_validity_concern,
                review_notes=_unblind_note(response.review_notes, alias_map),
                source_packet_hash=packet_hash,
                private_map_hash=map_hash,
                source_commit_sha=private_manifest.source_commit_sha,
            )
        )
    record_rows = tuple(sorted(records, key=lambda row: row.scenario_id))
    records_by_id = _unique_by(record_rows, "scenario_id", "canonical model review")

    comparison_rows = tuple(
        _comparison_from_sources(
            scenario_id=scenario_id,
            owner_review=reviews_by_id[scenario_id],
            model_review=records_by_id[scenario_id],
            finding=findings_by_id[scenario_id],
        )
        for scenario_id in sorted(views_by_id)
    )

    scenario_specific_concerns = tuple(
        sorted(
            record.scenario_id
            for record in record_rows
            if record.review_notes is not None
            and (
                "verified_transcript" in record.review_notes
                or "deliberately contradictory contract" in record.review_notes
            )
        )
    )
    provenance = BlindModelReviewProvenanceManifestV2(
        review_protocol_id=BLIND_MODEL_REVIEW_PROTOCOL_ID,
        source_commit_sha=private_manifest.source_commit_sha,
        source_scenario_sha256=source_scenario_hash,
        source_packet_sha256=packet_hash,
        review_protocol_sha256=review_protocol_hash,
        private_map_sha256=map_hash,
        private_source_manifest_sha256=private_manifest_hash,
        response_template_sha256=private_manifest.response_template_sha256,
        raw_review_sha256=raw_review_hash,
        owner_findings_sha256=file_sha256(owner_findings_path),
        owner_manifest_sha256=file_sha256(owner_manifest_path),
        relation_registry_hash=V2_RELATION_REGISTRY_HASH,
        review_record_bundle_hash=_bundle_hash("blind_model_review_records_v2", record_rows),
        comparison_bundle_hash=_bundle_hash("blind_model_review_comparisons_v2", comparison_rows),
        reviewed_case_count=len(record_rows),
        owner_agreement_count=sum(
            review.disposition is OracleReviewDispositionV2.AGREE for review in owner_review_rows
        ),
        full_agreement_count=sum(
            row.comparison_status is BlindModelReviewComparisonStatusV2.FULL_AGREEMENT
            for row in comparison_rows
        ),
        disagreement_count=sum(
            row.comparison_status is BlindModelReviewComparisonStatusV2.DISAGREEMENT
            for row in comparison_rows
        ),
        invalid_review_artifact_count=sum(
            row.comparison_status is BlindModelReviewComparisonStatusV2.INVALID_REVIEW_ARTIFACT
            for row in comparison_rows
        ),
        high_confidence_count=sum(
            record.confidence is BlindModelReviewConfidenceV2.HIGH for record in record_rows
        ),
        semantic_ambiguity_count=sum(record.semantic_ambiguity for record in record_rows),
        ecological_validity_concern_count=sum(
            record.ecological_validity_concern for record in record_rows
        ),
        bundle_level_declared_manifest_concern_count=sum(
            record.review_notes is not None and BUNDLE_REALISM_PHRASE in record.review_notes
            for record in record_rows
        ),
        scenario_level_ecological_concern_ids=scenario_specific_concerns,
        reviewer_received_only_blind_policy_visible_packet=True,
        withheld_answer_bearing_sources=WITHHELD_ANSWER_BEARING_SOURCES,
        shuffled_cases=True,
        per_case_aliased_tool_ids=True,
        response_format="JSONL",
        reviewer_platform="ChatGPT",
        review_session_type="TEMPORARY_CHAT",
        reviewer_model_identifier="NOT_RECORDED",
        human_reviewer=False,
        packet_identity_check_passed=True,
        blind_packet_published=True,
        raw_review_published=True,
        private_map_published=False,
        private_source_manifest_published=False,
        public_clone_can_verify_source_packet=True,
        public_clone_can_verify_raw_response=True,
        public_clone_can_repeat_unblinding=False,
        independent_human_review_performed=False,
        benchmark_frozen=False,
        policy_evaluation_performed=False,
    )
    verify_blind_model_review_comparisons_against_sources_v2(
        record_rows,
        comparison_rows,
        view_rows,
        owner_review_rows,
        owner_finding_rows,
    )
    verify_published_blind_model_review_sources_v2(
        provenance,
        blind_packet_path=blind_packet_path,
        raw_review_path=raw_review_path,
        review_protocol_path=review_protocol_path,
    )
    verify_blind_model_review_evidence_v2(record_rows, comparison_rows, provenance)
    return BlindModelReviewEvidenceBundleV2(
        records=record_rows,
        comparisons=comparison_rows,
        provenance=provenance,
    )
