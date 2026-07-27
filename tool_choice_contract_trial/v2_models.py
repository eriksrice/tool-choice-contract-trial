"""Strict Pydantic models for the isolated Milestone 2B artifact layer."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .v2_registry import V2_RELATION_REGISTRY_HASH

V2_SCHEMA_VERSION = "2.0.0"
V2SchemaVersion = Literal["2.0.0"]


class V2ContractModel(BaseModel):
    """Strict immutable base model for deterministic v2 artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _sorted_unique_v2(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(values))


class OracleStateV2(StrEnum):
    UNIQUE_ADMISSIBLE = "UNIQUE_ADMISSIBLE"
    MULTIPLE_ADMISSIBLE = "MULTIPLE_ADMISSIBLE"
    NO_ADMISSIBLE = "NO_ADMISSIBLE"
    CONTRACT_INVALID = "CONTRACT_INVALID"


class DecisionKindV2(StrEnum):
    SELECT = "SELECT"
    NO_TOOL = "NO_TOOL"
    INDETERMINATE = "INDETERMINATE"
    INVALID_CONTRACT = "INVALID_CONTRACT"


class FailureCodeV2(StrEnum):
    CAPABILITY_MISMATCH = "F_CAPABILITY_MISMATCH"
    AUTHORITY_MISMATCH = "F_AUTHORITY_MISMATCH"
    INPUT_CONTRACT_MISMATCH = "F_INPUT_CONTRACT_MISMATCH"
    OUTPUT_CONTRACT_MISMATCH = "F_OUTPUT_CONTRACT_MISMATCH"
    EXPLICIT_PROHIBITION = "F_EXPLICIT_PROHIBITION"


class AuthoringStatusV2(StrEnum):
    PROPOSED = "PROPOSED"


class OracleReviewDispositionV2(StrEnum):
    PENDING = "PENDING"
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    ADJUDICATED = "ADJUDICATED"


class ReviewReadinessV2(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"
    ADJUDICATION_REQUIRED = "ADJUDICATION_REQUIRED"
    ADJUDICATED = "ADJUDICATED"
    INVALID_UNIT = "INVALID_UNIT"


class EvaluationUnitStatusV2(StrEnum):
    SCOREABLE = "SCOREABLE"
    INVALID = "EVALUATION_UNIT_INVALID"


class BundleStatusV2(StrEnum):
    PROVISIONAL_REVIEW_CANDIDATE = "PROVISIONAL_REVIEW_CANDIDATE"


class TaskContractV2(V2ContractModel):
    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    contract_id: str = Field(pattern=r"^[a-z0-9_]+$")
    task_summary: str = Field(min_length=1)
    required_capabilities: tuple[str, ...] = Field(min_length=1)
    accepted_authority_profiles: tuple[str, ...] = Field(min_length=1)
    required_input_profiles: tuple[str, ...] = Field(min_length=1)
    required_output_profiles: tuple[str, ...] = Field(min_length=1)
    citations_required: bool = True
    forbidden_tool_ids: tuple[str, ...] = ()

    @field_validator(
        "required_capabilities",
        "accepted_authority_profiles",
        "required_input_profiles",
        "required_output_profiles",
        "forbidden_tool_ids",
    )
    @classmethod
    def sort_and_reject_duplicates(
        cls,
        values: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique_v2(values, field_name)


class ToolManifestV2(V2ContractModel):
    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    tool_id: str = Field(pattern=r"^[a-z0-9_]+$")
    display_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    capabilities: tuple[str, ...] = Field(min_length=1)
    authority_profiles: tuple[str, ...] = Field(min_length=1)
    accepted_input_profiles: tuple[str, ...] = Field(min_length=1)
    produced_output_profiles: tuple[str, ...] = Field(min_length=1)
    provides_citations: bool

    @field_validator(
        "capabilities",
        "authority_profiles",
        "accepted_input_profiles",
        "produced_output_profiles",
    )
    @classmethod
    def sort_and_reject_duplicates(
        cls,
        values: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique_v2(values, field_name)


class PolicyViewV2(V2ContractModel):
    """The complete policy-visible input for v2 relation checking."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    contract: TaskContractV2
    tools: tuple[ToolManifestV2, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_tool_ids_and_versions(self) -> Self:
        tool_ids = [tool.tool_id for tool in self.tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise ValueError("tools must have unique tool_id values")
        if self.contract.schema_version != self.schema_version:
            raise ValueError("policy view and contract schema versions must match")
        if any(tool.schema_version != self.schema_version for tool in self.tools):
            raise ValueError("policy view and tool schema versions must match")
        return self


class ClauseWitnessV2(V2ContractModel):
    clause_id: str = Field(min_length=1)
    failure_code: FailureCodeV2
    tool_id: str = Field(pattern=r"^[a-z0-9_]+$")
    contract_fields: tuple[str, ...] = Field(min_length=1)
    manifest_fields: tuple[str, ...] = Field(min_length=1)
    expected_values: tuple[str, ...] = ()
    actual_values: tuple[str, ...] = ()

    @field_validator(
        "contract_fields",
        "manifest_fields",
        "expected_values",
        "actual_values",
    )
    @classmethod
    def sort_and_reject_duplicates(
        cls,
        values: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique_v2(values, field_name)


class OracleExpectationV2(V2ContractModel):
    """Evaluator-only human-authored proposal, never relation-checker input."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    family_id: str = Field(pattern=r"^[a-z0-9_]+$")
    family_label: str = Field(min_length=1)
    variant_label: str = Field(min_length=1)
    expected_oracle_state: OracleStateV2
    expected_admissible_tool_ids: tuple[str, ...] = ()
    expected_decision: DecisionKindV2
    expected_selected_tool_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    authoring_rationale: str = Field(min_length=1)
    authoring_status: AuthoringStatusV2 = AuthoringStatusV2.PROPOSED

    @field_validator("expected_admissible_tool_ids")
    @classmethod
    def sort_and_reject_duplicate_tools(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_v2(values, "expected_admissible_tool_ids")

    @model_validator(mode="after")
    def expected_state_shape_is_consistent(self) -> Self:
        if self.expected_oracle_state is OracleStateV2.UNIQUE_ADMISSIBLE:
            if len(self.expected_admissible_tool_ids) != 1:
                raise ValueError("UNIQUE_ADMISSIBLE requires exactly one expected tool")
            if self.expected_decision is not DecisionKindV2.SELECT:
                raise ValueError("UNIQUE_ADMISSIBLE requires expected_decision=SELECT")
            if self.expected_selected_tool_id != self.expected_admissible_tool_ids[0]:
                raise ValueError("SELECT must name the unique expected admissible tool")
        elif self.expected_oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE:
            if len(self.expected_admissible_tool_ids) < 2:
                raise ValueError("MULTIPLE_ADMISSIBLE requires at least two expected tools")
            if self.expected_decision is not DecisionKindV2.INDETERMINATE:
                raise ValueError("MULTIPLE_ADMISSIBLE requires expected_decision=INDETERMINATE")
            if self.expected_selected_tool_id is not None:
                raise ValueError("INDETERMINATE cannot name a selected tool")
        elif self.expected_oracle_state is OracleStateV2.NO_ADMISSIBLE:
            if self.expected_admissible_tool_ids:
                raise ValueError("NO_ADMISSIBLE requires an empty expected set")
            if self.expected_decision is not DecisionKindV2.NO_TOOL:
                raise ValueError("NO_ADMISSIBLE requires expected_decision=NO_TOOL")
            if self.expected_selected_tool_id is not None:
                raise ValueError("NO_TOOL cannot name a selected tool")
        elif self.expected_oracle_state is OracleStateV2.CONTRACT_INVALID:
            if self.expected_admissible_tool_ids:
                raise ValueError("CONTRACT_INVALID requires an empty expected set")
            if self.expected_decision is not DecisionKindV2.INVALID_CONTRACT:
                raise ValueError("CONTRACT_INVALID requires expected_decision=INVALID_CONTRACT")
            if self.expected_selected_tool_id is not None:
                raise ValueError("INVALID_CONTRACT cannot name a selected tool")
        return self


class OracleReviewRecordV2(V2ContractModel):
    """Evaluator-only independent-review or adjudication record."""

    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    reviewer_role: str = Field(pattern=r"^[a-z0-9_]+$")
    disposition: OracleReviewDispositionV2
    reviewed_expected_state: OracleStateV2 | None = None
    reviewed_admissible_tool_ids: tuple[str, ...] | None = None
    review_notes: str = Field(min_length=1)
    review_performed_without_policy_outputs: bool | None = None
    adjudicated_state: OracleStateV2 | None = None
    adjudicated_admissible_tool_ids: tuple[str, ...] | None = None

    @field_validator("reviewed_admissible_tool_ids", "adjudicated_admissible_tool_ids")
    @classmethod
    def sort_and_reject_duplicate_tools(
        cls,
        values: tuple[str, ...] | None,
        info: object,
    ) -> tuple[str, ...] | None:
        if values is None:
            return None
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique_v2(values, field_name)

    @model_validator(mode="after")
    def review_record_shape_is_consistent(self) -> Self:
        if self.disposition is OracleReviewDispositionV2.PENDING:
            if any(
                value is not None
                for value in (
                    self.reviewed_expected_state,
                    self.reviewed_admissible_tool_ids,
                    self.review_performed_without_policy_outputs,
                    self.adjudicated_state,
                    self.adjudicated_admissible_tool_ids,
                )
            ):
                raise ValueError("PENDING review cannot contain completed-review fields")
            return self

        if self.reviewed_expected_state is None or self.reviewed_admissible_tool_ids is None:
            raise ValueError("completed review requires reviewed state and admissible set")
        if self.review_performed_without_policy_outputs is None:
            raise ValueError("completed review must record policy-output independence")
        if self.disposition is not OracleReviewDispositionV2.ADJUDICATED and (
            self.adjudicated_state is not None or self.adjudicated_admissible_tool_ids is not None
        ):
            raise ValueError("only ADJUDICATED review may contain adjudicated values")
        return self


class OracleValidationFindingV2(V2ContractModel):
    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expectation_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    relation_registry_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    computed_oracle_state: OracleStateV2
    computed_admissible_tool_ids: tuple[str, ...]
    computed_expected_decision: DecisionKindV2
    relation_witnesses: tuple[ClauseWitnessV2, ...]
    contract_invalid_reasons: tuple[str, ...]
    proposed_oracle_state: OracleStateV2 | None
    proposed_admissible_tool_ids: tuple[str, ...]
    proposed_expected_decision: DecisionKindV2 | None
    proposed_selected_tool_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    state_matches_expectation: bool
    admissible_set_matches_expectation: bool
    decision_matches_expectation: bool
    expectation_matches_relation: bool
    review_disposition: OracleReviewDispositionV2 | None
    review_readiness: ReviewReadinessV2
    evaluation_unit_status: EvaluationUnitStatusV2
    invalid_unit_reasons: tuple[str, ...]
    ready_for_scoring: bool
    ready_for_freeze: bool

    @field_validator(
        "computed_admissible_tool_ids",
        "contract_invalid_reasons",
        "proposed_admissible_tool_ids",
        "invalid_unit_reasons",
    )
    @classmethod
    def sort_and_reject_duplicate_values(
        cls,
        values: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique_v2(values, field_name)

    @model_validator(mode="after")
    def finding_status_is_consistent(self) -> Self:
        if self.relation_registry_hash != V2_RELATION_REGISTRY_HASH:
            raise ValueError("relation_registry_hash does not match the active v2 registry")
        expected_shapes = {
            OracleStateV2.UNIQUE_ADMISSIBLE: (1, DecisionKindV2.SELECT),
            OracleStateV2.MULTIPLE_ADMISSIBLE: (None, DecisionKindV2.INDETERMINATE),
            OracleStateV2.NO_ADMISSIBLE: (0, DecisionKindV2.NO_TOOL),
            OracleStateV2.CONTRACT_INVALID: (0, DecisionKindV2.INVALID_CONTRACT),
        }
        expected_count, expected_decision = expected_shapes[self.computed_oracle_state]
        if expected_count is not None and len(self.computed_admissible_tool_ids) != expected_count:
            raise ValueError(
                f"{self.computed_oracle_state} requires {expected_count} computed tools"
            )
        if (
            self.computed_oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE
            and len(self.computed_admissible_tool_ids) < 2
        ):
            raise ValueError("MULTIPLE_ADMISSIBLE requires at least two computed tools")
        if self.computed_expected_decision is not expected_decision:
            raise ValueError(
                f"{self.computed_oracle_state} requires computed decision {expected_decision}"
            )
        if self.computed_oracle_state is OracleStateV2.CONTRACT_INVALID:
            if not self.contract_invalid_reasons:
                raise ValueError("CONTRACT_INVALID requires a semantic contract-invalid reason")
        elif self.contract_invalid_reasons:
            raise ValueError("non-CONTRACT_INVALID finding cannot have contract-invalid reasons")

        expected_match = (
            self.state_matches_expectation
            and self.admissible_set_matches_expectation
            and self.decision_matches_expectation
        )
        if self.expectation_matches_relation is not expected_match:
            raise ValueError("expectation_matches_relation does not match component flags")
        if self.evaluation_unit_status is EvaluationUnitStatusV2.INVALID:
            if not self.invalid_unit_reasons:
                raise ValueError("invalid evaluation unit requires invalid-unit reasons")
            if self.ready_for_scoring or self.ready_for_freeze:
                raise ValueError("invalid evaluation unit cannot be ready")
        elif self.invalid_unit_reasons:
            raise ValueError("scoreable evaluation unit cannot have invalid-unit reasons")
        if self.ready_for_freeze and not self.ready_for_scoring:
            raise ValueError("freeze readiness requires scoring readiness")
        if self.review_disposition is OracleReviewDispositionV2.PENDING and (
            self.ready_for_scoring or self.ready_for_freeze
        ):
            raise ValueError("pending review cannot be ready for scoring or freeze")
        return self


class ScenarioArtifactRecordV2(V2ContractModel):
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expectation_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    finding_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ComputedStateCountsV2(V2ContractModel):
    unique_admissible: int = Field(ge=0)
    multiple_admissible: int = Field(ge=0)
    no_admissible: int = Field(ge=0)
    contract_invalid: int = Field(ge=0)

    @property
    def total(self) -> int:
        return (
            self.unique_admissible
            + self.multiple_admissible
            + self.no_admissible
            + self.contract_invalid
        )


class ProvisionalBundleManifestV2(V2ContractModel):
    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    artifact_schema_versions: tuple[str, ...] = Field(min_length=1)
    scenario_artifacts: tuple[ScenarioArtifactRecordV2, ...] = Field(min_length=1)
    scenario_bundle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expectation_bundle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_bundle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    relation_registry_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    computed_state_counts: ComputedStateCountsV2
    pending_review_count: int = Field(ge=0)
    invalid_unit_count: int = Field(ge=0)
    contract_invalid_count: int = Field(ge=0)
    bundle_status: BundleStatusV2 = BundleStatusV2.PROVISIONAL_REVIEW_CANDIDATE

    @field_validator("artifact_schema_versions")
    @classmethod
    def sort_and_reject_duplicate_versions(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique_v2(values, "artifact_schema_versions")

    @model_validator(mode="after")
    def manifest_counts_are_consistent(self) -> Self:
        if self.relation_registry_hash != V2_RELATION_REGISTRY_HASH:
            raise ValueError("relation_registry_hash does not match the active v2 registry")
        scenario_ids = [artifact.scenario_id for artifact in self.scenario_artifacts]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("scenario_artifacts must have unique scenario IDs")
        if tuple(sorted(scenario_ids)) != tuple(scenario_ids):
            raise ValueError("scenario_artifacts must be sorted by scenario ID")
        if self.computed_state_counts.total != len(self.scenario_artifacts):
            raise ValueError("computed state counts must equal the scenario count")
        if self.contract_invalid_count != self.computed_state_counts.contract_invalid:
            raise ValueError("contract-invalid count must match computed state counts")
        return self
