"""Strict Pydantic models for the isolated Milestone 2B artifact layer."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .v2_registry import V2_RELATION_CLAUSE_REGISTRY, V2_RELATION_REGISTRY_HASH

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


def validate_oracle_state_tool_ids_v2(
    state: OracleStateV2,
    tool_ids: tuple[str, ...],
    *,
    field_label: str,
) -> None:
    """Validate the one authoritative state/admissible-set shape relation."""

    if state is OracleStateV2.UNIQUE_ADMISSIBLE and len(tool_ids) != 1:
        raise ValueError(f"{field_label}: UNIQUE_ADMISSIBLE requires exactly one tool")
    if state is OracleStateV2.MULTIPLE_ADMISSIBLE and len(tool_ids) < 2:
        raise ValueError(f"{field_label}: MULTIPLE_ADMISSIBLE requires at least two tools")
    if state in {OracleStateV2.NO_ADMISSIBLE, OracleStateV2.CONTRACT_INVALID} and tool_ids:
        raise ValueError(f"{field_label}: {state.value} requires an empty tool set")


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

    @model_validator(mode="after")
    def witness_matches_relation_registry(self) -> Self:
        clause = V2_RELATION_CLAUSE_REGISTRY.get(self.clause_id)
        if clause is None:
            raise ValueError(f"unsupported v2 relation clause: {self.clause_id}")
        if self.failure_code.value != clause.expected_failure_code:
            raise ValueError("failure_code does not match the v2 relation clause registry")
        if self.contract_fields != clause.contract_fields:
            raise ValueError("contract_fields do not match the v2 relation clause registry")
        if self.manifest_fields != clause.manifest_fields:
            raise ValueError("manifest_fields do not match the v2 relation clause registry")
        return self


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
        validate_oracle_state_tool_ids_v2(
            self.expected_oracle_state,
            self.expected_admissible_tool_ids,
            field_label="expected oracle state/set",
        )
        if self.expected_oracle_state is OracleStateV2.UNIQUE_ADMISSIBLE:
            if self.expected_decision is not DecisionKindV2.SELECT:
                raise ValueError("UNIQUE_ADMISSIBLE requires expected_decision=SELECT")
            if self.expected_selected_tool_id != self.expected_admissible_tool_ids[0]:
                raise ValueError("SELECT must name the unique expected admissible tool")
        elif self.expected_oracle_state is OracleStateV2.MULTIPLE_ADMISSIBLE:
            if self.expected_decision is not DecisionKindV2.INDETERMINATE:
                raise ValueError("MULTIPLE_ADMISSIBLE requires expected_decision=INDETERMINATE")
            if self.expected_selected_tool_id is not None:
                raise ValueError("INDETERMINATE cannot name a selected tool")
        elif self.expected_oracle_state is OracleStateV2.NO_ADMISSIBLE:
            if self.expected_decision is not DecisionKindV2.NO_TOOL:
                raise ValueError("NO_ADMISSIBLE requires expected_decision=NO_TOOL")
            if self.expected_selected_tool_id is not None:
                raise ValueError("NO_TOOL cannot name a selected tool")
        elif self.expected_oracle_state is OracleStateV2.CONTRACT_INVALID:
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
        validate_oracle_state_tool_ids_v2(
            self.reviewed_expected_state,
            self.reviewed_admissible_tool_ids,
            field_label="reviewed oracle state/set",
        )
        if self.review_performed_without_policy_outputs is None:
            raise ValueError("completed review must record policy-output independence")
        if self.disposition is not OracleReviewDispositionV2.ADJUDICATED and (
            self.adjudicated_state is not None or self.adjudicated_admissible_tool_ids is not None
        ):
            raise ValueError("only ADJUDICATED review may contain adjudicated values")
        if self.adjudicated_state is not None and self.adjudicated_admissible_tool_ids is not None:
            validate_oracle_state_tool_ids_v2(
                self.adjudicated_state,
                self.adjudicated_admissible_tool_ids,
                field_label="adjudicated oracle state/set",
            )
        return self


class OracleValidationFindingV2(V2ContractModel):
    schema_version: V2SchemaVersion = V2_SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expectation_present: bool
    review_present: bool
    expectation_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    relation_registry_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    available_tool_ids: tuple[str, ...] = Field(min_length=1)
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
    reviewed_expected_state: OracleStateV2 | None
    reviewed_admissible_tool_ids: tuple[str, ...] | None
    review_performed_without_policy_outputs: bool | None
    adjudicated_state: OracleStateV2 | None
    adjudicated_admissible_tool_ids: tuple[str, ...] | None
    review_readiness: ReviewReadinessV2
    evaluation_unit_status: EvaluationUnitStatusV2
    invalid_unit_reasons: tuple[str, ...]
    ready_for_scoring: bool
    ready_for_freeze: bool

    @field_validator(
        "available_tool_ids",
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

    @field_validator("reviewed_admissible_tool_ids", "adjudicated_admissible_tool_ids")
    @classmethod
    def sort_and_reject_duplicate_optional_values(
        cls,
        values: tuple[str, ...] | None,
        info: object,
    ) -> tuple[str, ...] | None:
        if values is None:
            return None
        field_name = getattr(info, "field_name", "optional tuple field")
        return _sorted_unique_v2(values, field_name)

    @model_validator(mode="after")
    def finding_status_is_consistent(self) -> Self:
        if self.relation_registry_hash != V2_RELATION_REGISTRY_HASH:
            raise ValueError("relation_registry_hash does not match the active v2 registry")
        validate_oracle_state_tool_ids_v2(
            self.computed_oracle_state,
            self.computed_admissible_tool_ids,
            field_label="computed oracle state/set",
        )
        expected_decision = {
            OracleStateV2.UNIQUE_ADMISSIBLE: DecisionKindV2.SELECT,
            OracleStateV2.MULTIPLE_ADMISSIBLE: DecisionKindV2.INDETERMINATE,
            OracleStateV2.NO_ADMISSIBLE: DecisionKindV2.NO_TOOL,
            OracleStateV2.CONTRACT_INVALID: DecisionKindV2.INVALID_CONTRACT,
        }[self.computed_oracle_state]
        if self.computed_expected_decision is not expected_decision:
            raise ValueError(
                f"{self.computed_oracle_state} requires computed decision {expected_decision}"
            )

        available_tool_ids = set(self.available_tool_ids)
        computed_admissible_tool_ids = set(self.computed_admissible_tool_ids)
        if not computed_admissible_tool_ids.issubset(available_tool_ids):
            raise ValueError("computed admissible tools must be a subset of available tools")
        witness_pairs = [
            (witness.tool_id, witness.clause_id) for witness in self.relation_witnesses
        ]
        if len(witness_pairs) != len(set(witness_pairs)):
            raise ValueError("relation witnesses must not duplicate a tool/clause pair")
        for witness in self.relation_witnesses:
            if witness.tool_id not in available_tool_ids:
                raise ValueError("relation witness references an unavailable tool")
            if witness.tool_id in computed_admissible_tool_ids:
                raise ValueError("computed-admissible tool cannot have a relation witness")

        if self.computed_oracle_state is OracleStateV2.CONTRACT_INVALID:
            if not self.contract_invalid_reasons:
                raise ValueError("CONTRACT_INVALID requires a semantic contract-invalid reason")
            if self.relation_witnesses:
                raise ValueError("CONTRACT_INVALID cannot contain ordinary tool witnesses")
        elif self.contract_invalid_reasons:
            raise ValueError("non-CONTRACT_INVALID finding cannot have contract-invalid reasons")
        else:
            witnessed_tool_ids = {witness.tool_id for witness in self.relation_witnesses}
            missing_witness_tool_ids = sorted(
                available_tool_ids - computed_admissible_tool_ids - witnessed_tool_ids
            )
            if missing_witness_tool_ids:
                raise ValueError(
                    "available inadmissible tools require relation witnesses: "
                    f"{missing_witness_tool_ids}"
                )

        if self.expectation_present:
            if self.expectation_hash is None:
                raise ValueError("present expectation requires expectation_hash")
            if self.proposed_oracle_state is None or self.proposed_expected_decision is None:
                raise ValueError("present expectation requires proposed state and decision")
            validate_oracle_state_tool_ids_v2(
                self.proposed_oracle_state,
                self.proposed_admissible_tool_ids,
                field_label="proposed oracle state/set",
            )
            proposed_decision = {
                OracleStateV2.UNIQUE_ADMISSIBLE: DecisionKindV2.SELECT,
                OracleStateV2.MULTIPLE_ADMISSIBLE: DecisionKindV2.INDETERMINATE,
                OracleStateV2.NO_ADMISSIBLE: DecisionKindV2.NO_TOOL,
                OracleStateV2.CONTRACT_INVALID: DecisionKindV2.INVALID_CONTRACT,
            }[self.proposed_oracle_state]
            if self.proposed_expected_decision is not proposed_decision:
                raise ValueError("proposed decision does not match the proposed oracle state")
            expected_selected_tool_id = (
                self.proposed_admissible_tool_ids[0]
                if proposed_decision is DecisionKindV2.SELECT
                else None
            )
            if self.proposed_selected_tool_id != expected_selected_tool_id:
                raise ValueError("proposed selected tool does not match the proposed state/set")
        elif (
            any(
                value is not None
                for value in (
                    self.expectation_hash,
                    self.proposed_oracle_state,
                    self.proposed_expected_decision,
                    self.proposed_selected_tool_id,
                )
            )
            or self.proposed_admissible_tool_ids
        ):
            raise ValueError("missing expectation cannot contain expectation evidence")

        completed_review_values = (
            self.reviewed_expected_state,
            self.reviewed_admissible_tool_ids,
            self.review_performed_without_policy_outputs,
            self.adjudicated_state,
            self.adjudicated_admissible_tool_ids,
        )
        if self.review_present:
            if self.review_hash is None or self.review_disposition is None:
                raise ValueError("present review requires review hash and disposition")
            if self.review_disposition is OracleReviewDispositionV2.PENDING:
                if any(value is not None for value in completed_review_values):
                    raise ValueError("PENDING finding cannot contain completed-review evidence")
            else:
                if (
                    self.reviewed_expected_state is None
                    or self.reviewed_admissible_tool_ids is None
                    or self.review_performed_without_policy_outputs is None
                ):
                    raise ValueError("completed finding requires complete reviewed evidence")
                validate_oracle_state_tool_ids_v2(
                    self.reviewed_expected_state,
                    self.reviewed_admissible_tool_ids,
                    field_label="finding reviewed oracle state/set",
                )
                if self.review_disposition is not OracleReviewDispositionV2.ADJUDICATED and (
                    self.adjudicated_state is not None
                    or self.adjudicated_admissible_tool_ids is not None
                ):
                    raise ValueError("only ADJUDICATED finding may contain adjudicated evidence")
                if (
                    self.adjudicated_state is not None
                    and self.adjudicated_admissible_tool_ids is not None
                ):
                    validate_oracle_state_tool_ids_v2(
                        self.adjudicated_state,
                        self.adjudicated_admissible_tool_ids,
                        field_label="finding adjudicated oracle state/set",
                    )
        elif (
            self.review_hash is not None
            or self.review_disposition is not None
            or any(value is not None for value in completed_review_values)
        ):
            raise ValueError("missing review cannot contain review evidence")

        from .v2_semantics import (  # Avoid a module-initialization cycle.
            OracleValidationEvidenceV2,
            derive_oracle_validation_state_v2,
        )

        derived = derive_oracle_validation_state_v2(
            OracleValidationEvidenceV2(
                expectation_present=self.expectation_present,
                review_present=self.review_present,
                computed_oracle_state=self.computed_oracle_state,
                computed_admissible_tool_ids=self.computed_admissible_tool_ids,
                computed_expected_decision=self.computed_expected_decision,
                proposed_oracle_state=self.proposed_oracle_state,
                proposed_admissible_tool_ids=self.proposed_admissible_tool_ids,
                proposed_expected_decision=self.proposed_expected_decision,
                proposed_selected_tool_id=self.proposed_selected_tool_id,
                review_disposition=self.review_disposition,
                reviewed_expected_state=self.reviewed_expected_state,
                reviewed_admissible_tool_ids=self.reviewed_admissible_tool_ids,
                review_performed_without_policy_outputs=(
                    self.review_performed_without_policy_outputs
                ),
                adjudicated_state=self.adjudicated_state,
                adjudicated_admissible_tool_ids=self.adjudicated_admissible_tool_ids,
            )
        )
        for field_name in (
            "state_matches_expectation",
            "admissible_set_matches_expectation",
            "decision_matches_expectation",
            "expectation_matches_relation",
            "review_readiness",
            "evaluation_unit_status",
            "invalid_unit_reasons",
            "ready_for_scoring",
            "ready_for_freeze",
        ):
            if getattr(self, field_name) != getattr(derived, field_name):
                raise ValueError(f"{field_name} differs from authoritative v2 derivation")
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
