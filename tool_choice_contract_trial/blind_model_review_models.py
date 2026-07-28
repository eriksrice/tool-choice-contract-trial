"""Strict models for the separate blind independent model-review evidence layer."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from .v2_models import (
    V2_SCHEMA_VERSION,
    DecisionKindV2,
    OracleStateV2,
    TaskContractV2,
    ToolManifestV2,
    V2ContractModel,
    V2SchemaVersion,
    validate_oracle_state_tool_ids_v2,
)

BLIND_MODEL_REVIEW_KIND = "BLIND_INDEPENDENT_MODEL_REVIEW"
BLIND_MODEL_REVIEW_PROTOCOL_ID = "blind_model_review_001"


class BlindModelReviewConfidenceV2(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BlindModelReviewComparisonStatusV2(StrEnum):
    FULL_AGREEMENT = "FULL_AGREEMENT"
    DISAGREEMENT = "DISAGREEMENT"
    INVALID_REVIEW_ARTIFACT = "INVALID_REVIEW_ARTIFACT"


def _sorted_unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(values))


def _validate_review_shape(
    *,
    state: OracleStateV2,
    tool_ids: tuple[str, ...],
    decision: DecisionKindV2,
    field_label: str,
) -> None:
    validate_oracle_state_tool_ids_v2(state, tool_ids, field_label=field_label)
    expected_decision = {
        OracleStateV2.UNIQUE_ADMISSIBLE: DecisionKindV2.SELECT,
        OracleStateV2.MULTIPLE_ADMISSIBLE: DecisionKindV2.INDETERMINATE,
        OracleStateV2.NO_ADMISSIBLE: DecisionKindV2.NO_TOOL,
        OracleStateV2.CONTRACT_INVALID: DecisionKindV2.INVALID_CONTRACT,
    }[state]
    if decision is not expected_decision:
        raise ValueError(f"{field_label}: {state.value} requires {expected_decision.value}")


class BlindModelReviewResponseV2(V2ContractModel):
    """Raw response row produced against blind, per-case tool aliases."""

    blind_case_id: str = Field(pattern=r"^blind_case_[0-9]{2}$")
    reviewed_oracle_state: OracleStateV2
    reviewed_admissible_tool_ids: tuple[str, ...] = ()
    reviewed_decision: DecisionKindV2
    confidence: BlindModelReviewConfidenceV2
    semantic_ambiguity: bool
    ecological_validity_concern: bool
    review_notes: str | None = None

    @field_validator("reviewed_admissible_tool_ids")
    @classmethod
    def validate_blind_tool_aliases(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = _sorted_unique(values, "reviewed_admissible_tool_ids")
        if any(re.fullmatch(r"candidate_tool_[a-z]", value) is None for value in values):
            raise ValueError("reviewed tool IDs must use candidate_tool aliases")
        return values

    @model_validator(mode="after")
    def response_shape_is_consistent(self) -> Self:
        _validate_review_shape(
            state=self.reviewed_oracle_state,
            tool_ids=self.reviewed_admissible_tool_ids,
            decision=self.reviewed_decision,
            field_label="blind model review state/set/decision",
        )
        return self


class BlindPacketCaseV2(V2ContractModel):
    """One policy-visible case after deterministic blind aliasing."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    blind_case_id: str = Field(pattern=r"^blind_case_[0-9]{2}$")
    contract: TaskContractV2
    tools: tuple[ToolManifestV2, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def packet_case_is_consistent(self) -> Self:
        tool_ids = [tool.tool_id for tool in self.tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise ValueError("blind packet tools must have unique tool IDs")
        if self.contract.schema_version != self.schema_version:
            raise ValueError("blind packet and contract schema versions must match")
        if any(tool.schema_version != self.schema_version for tool in self.tools):
            raise ValueError("blind packet and tool schema versions must match")
        return self


class BlindToolAliasMappingV2(V2ContractModel):
    blind_presentation_position: int = Field(ge=0)
    blind_tool_id: str = Field(pattern=r"^candidate_tool_[a-z]$")
    original_tool_id: str = Field(pattern=r"^[a-z0-9_]+$")
    original_tool_position: int = Field(ge=0)


class BlindCaseAliasMappingV2(V2ContractModel):
    blind_case_id: str = Field(pattern=r"^blind_case_[0-9]{2}$")
    blind_contract_id: str = Field(pattern=r"^blind_contract_[0-9]{2}$")
    original_contract_id: str = Field(pattern=r"^[a-z0-9_]+$")
    original_scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    original_scenario_position: int = Field(ge=0)
    tools: tuple[BlindToolAliasMappingV2, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def mapping_is_bijective(self) -> Self:
        blind_ids = [tool.blind_tool_id for tool in self.tools]
        original_ids = [tool.original_tool_id for tool in self.tools]
        blind_positions = [tool.blind_presentation_position for tool in self.tools]
        original_positions = [tool.original_tool_position for tool in self.tools]
        for label, values in (
            ("blind tool IDs", blind_ids),
            ("original tool IDs", original_ids),
            ("blind tool positions", blind_positions),
            ("original tool positions", original_positions),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique within a blind case")
        if tuple(sorted(blind_positions)) != tuple(range(len(self.tools))):
            raise ValueError("blind tool positions must be contiguous from zero")
        if tuple(sorted(original_positions)) != tuple(range(len(self.tools))):
            raise ValueError("original tool positions must be contiguous from zero")
        return self


class BlindAliasScopeV2(V2ContractModel):
    contract_aliases: Literal["global"]
    scenario_aliases: Literal["global"]
    tool_aliases: Literal["per blind case"]


class BlindPrivateCaseMapV2(V2ContractModel):
    warning: str = Field(alias="_warning", min_length=1)
    alias_scope: BlindAliasScopeV2
    blind_seed: str = Field(min_length=1)
    cases: tuple[BlindCaseAliasMappingV2, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def case_mapping_is_bijective(self) -> Self:
        if not self.warning.startswith("DO NOT SHARE WITH THE REVIEWER"):
            raise ValueError("private case map must carry the reviewer-sharing warning")
        for label, values in (
            ("blind case IDs", [case.blind_case_id for case in self.cases]),
            ("original scenario IDs", [case.original_scenario_id for case in self.cases]),
            ("blind contract IDs", [case.blind_contract_id for case in self.cases]),
            ("original contract IDs", [case.original_contract_id for case in self.cases]),
            (
                "original scenario positions",
                [case.original_scenario_position for case in self.cases],
            ),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self


class BlindSourceValidationV2(V2ContractModel):
    all_source_scenarios_appear_exactly_once: Literal[True]
    all_tool_references_map_consistently: Literal[True]
    exactly_twelve_cases: Literal[True]
    original_identifiers_absent_from_shared_files: Literal[True]
    prohibited_answer_terms_absent_from_shared_files: Literal[True]
    reverse_mapping_reproduces_complete_source_records: Literal[True]


class BlindPrivateSourceManifestV2(V2ContractModel):
    warning: str = Field(alias="_warning", min_length=1)
    aliases_are_bijective: Literal[True]
    blind_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    blind_seed: str = Field(min_length=1)
    confirmation_no_prohibited_answer_bearing_source_was_read: Literal[True]
    private_case_map_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response_template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scenario_count: int = Field(ge=1)
    semantic_fields_round_trip_exactly: Literal[True]
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_scenario_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transformation: str = Field(min_length=1)
    v2_schema_version: V2SchemaVersion
    validation: BlindSourceValidationV2

    @model_validator(mode="after")
    def private_manifest_has_warning(self) -> Self:
        if not self.warning.startswith("DO NOT SHARE WITH THE REVIEWER"):
            raise ValueError("private source manifest must carry the reviewer-sharing warning")
        return self


class BlindModelReviewRecordV2(V2ContractModel):
    """Canonical, unblinded evidence from one blind independent model review."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    review_protocol_id: str = Field(pattern=r"^[a-z0-9_]+$")
    review_kind: Literal["BLIND_INDEPENDENT_MODEL_REVIEW"] = BLIND_MODEL_REVIEW_KIND
    blind_case_id: str = Field(pattern=r"^blind_case_[0-9]{2}$")
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    reviewed_oracle_state: OracleStateV2
    reviewed_admissible_tool_ids: tuple[str, ...] = ()
    reviewed_decision: DecisionKindV2
    confidence: BlindModelReviewConfidenceV2
    semantic_ambiguity: bool
    ecological_validity_concern: bool
    review_notes: str | None = None
    source_packet_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    private_map_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")

    @field_validator("reviewed_admissible_tool_ids")
    @classmethod
    def sort_reviewed_tool_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(values, "reviewed_admissible_tool_ids")

    @model_validator(mode="after")
    def canonical_review_shape_is_consistent(self) -> Self:
        _validate_review_shape(
            state=self.reviewed_oracle_state,
            tool_ids=self.reviewed_admissible_tool_ids,
            decision=self.reviewed_decision,
            field_label="canonical blind model review state/set/decision",
        )
        return self


class BlindModelReviewComparisonV2(V2ContractModel):
    """Three-way comparison of owner, blind-model, and computed relations."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    review_protocol_id: str = Field(pattern=r"^[a-z0-9_]+$")
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    owner_reviewed_state: OracleStateV2
    owner_reviewed_admissible_tool_ids: tuple[str, ...]
    owner_reviewed_decision: DecisionKindV2
    blind_model_reviewed_state: OracleStateV2
    blind_model_reviewed_admissible_tool_ids: tuple[str, ...]
    blind_model_reviewed_decision: DecisionKindV2
    computed_state: OracleStateV2
    computed_admissible_tool_ids: tuple[str, ...]
    computed_decision: DecisionKindV2
    state_agreement: bool
    admissible_set_agreement: bool
    decision_agreement: bool
    semantic_ambiguity: bool
    ecological_validity_concern: bool
    comparison_status: BlindModelReviewComparisonStatusV2

    @field_validator(
        "owner_reviewed_admissible_tool_ids",
        "blind_model_reviewed_admissible_tool_ids",
        "computed_admissible_tool_ids",
    )
    @classmethod
    def sort_comparison_tool_ids(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _sorted_unique(values, getattr(info, "field_name", "comparison tool IDs"))

    @model_validator(mode="after")
    def comparison_is_derived_from_three_relations(self) -> Self:
        for label, state, tool_ids, decision in (
            (
                "owner-reviewed relation",
                self.owner_reviewed_state,
                self.owner_reviewed_admissible_tool_ids,
                self.owner_reviewed_decision,
            ),
            (
                "blind-model-reviewed relation",
                self.blind_model_reviewed_state,
                self.blind_model_reviewed_admissible_tool_ids,
                self.blind_model_reviewed_decision,
            ),
            (
                "computed relation",
                self.computed_state,
                self.computed_admissible_tool_ids,
                self.computed_decision,
            ),
        ):
            _validate_review_shape(
                state=state,
                tool_ids=tool_ids,
                decision=decision,
                field_label=label,
            )

        state_agreement = (
            self.owner_reviewed_state is self.blind_model_reviewed_state is self.computed_state
        )
        admissible_set_agreement = (
            self.owner_reviewed_admissible_tool_ids
            == self.blind_model_reviewed_admissible_tool_ids
            == self.computed_admissible_tool_ids
        )
        decision_agreement = (
            self.owner_reviewed_decision
            is self.blind_model_reviewed_decision
            is self.computed_decision
        )
        if self.state_agreement != state_agreement:
            raise ValueError("state_agreement differs from the three source relations")
        if self.admissible_set_agreement != admissible_set_agreement:
            raise ValueError("admissible_set_agreement differs from the three source relations")
        if self.decision_agreement != decision_agreement:
            raise ValueError("decision_agreement differs from the three source relations")
        expected_status = (
            BlindModelReviewComparisonStatusV2.FULL_AGREEMENT
            if state_agreement and admissible_set_agreement and decision_agreement
            else BlindModelReviewComparisonStatusV2.DISAGREEMENT
        )
        if self.comparison_status is not expected_status:
            raise ValueError("comparison_status differs from the agreement fields")
        return self


class BlindModelReviewProvenanceManifestV2(V2ContractModel):
    """Public-safe provenance for one canonical blind-model-review bundle."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    review_protocol_id: str = Field(pattern=r"^[a-z0-9_]+$")
    review_kind: Literal["BLIND_INDEPENDENT_MODEL_REVIEW"] = BLIND_MODEL_REVIEW_KIND
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_scenario_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    private_map_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    private_source_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response_template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    owner_findings_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    owner_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relation_registry_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_record_bundle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_bundle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_case_count: int = Field(ge=0)
    owner_agreement_count: int = Field(ge=0)
    full_agreement_count: int = Field(ge=0)
    disagreement_count: int = Field(ge=0)
    invalid_review_artifact_count: int = Field(ge=0)
    high_confidence_count: int = Field(ge=0)
    semantic_ambiguity_count: int = Field(ge=0)
    ecological_validity_concern_count: int = Field(ge=0)
    bundle_level_declared_manifest_concern_count: int = Field(ge=0)
    scenario_level_ecological_concern_ids: tuple[str, ...]
    reviewer_received_only_blind_policy_visible_packet: Literal[True]
    withheld_answer_bearing_sources: tuple[str, ...] = Field(min_length=1)
    shuffled_cases: Literal[True]
    per_case_aliased_tool_ids: Literal[True]
    response_format: Literal["JSONL"]
    private_map_published: Literal[False]
    raw_blind_packet_published: Literal[False]
    independent_human_review_performed: Literal[False]
    benchmark_frozen: Literal[False]
    policy_evaluation_performed: Literal[False]

    @field_validator("scenario_level_ecological_concern_ids", "withheld_answer_bearing_sources")
    @classmethod
    def sort_manifest_values(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        return _sorted_unique(values, getattr(info, "field_name", "manifest values"))

    @model_validator(mode="after")
    def manifest_counts_are_consistent(self) -> Self:
        if (
            self.full_agreement_count + self.disagreement_count + self.invalid_review_artifact_count
            != self.reviewed_case_count
        ):
            raise ValueError("comparison status counts must equal reviewed_case_count")
        if self.owner_agreement_count > self.reviewed_case_count:
            raise ValueError("owner_agreement_count cannot exceed reviewed_case_count")
        for field_name in (
            "high_confidence_count",
            "semantic_ambiguity_count",
            "ecological_validity_concern_count",
            "bundle_level_declared_manifest_concern_count",
        ):
            if getattr(self, field_name) > self.reviewed_case_count:
                raise ValueError(f"{field_name} cannot exceed reviewed_case_count")
        return self
