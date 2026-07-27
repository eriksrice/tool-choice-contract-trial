"""Authoritative Pydantic models for deterministic evaluation artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.0.0"
SchemaVersion = Literal["1.0.0"]


class ContractModel(BaseModel):
    """Strict immutable base model for deterministic contract artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _sorted_unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(values))


class DecisionKind(StrEnum):
    SELECT = "SELECT"
    NO_TOOL = "NO_TOOL"
    INDETERMINATE = "INDETERMINATE"
    INVALID_CONTRACT = "INVALID_CONTRACT"


class OracleState(StrEnum):
    UNIQUE_ADMISSIBLE = "UNIQUE_ADMISSIBLE"
    MULTIPLE_ADMISSIBLE = "MULTIPLE_ADMISSIBLE"
    NO_ADMISSIBLE = "NO_ADMISSIBLE"
    CONTRACT_INVALID = "CONTRACT_INVALID"
    EVALUATION_UNIT_INVALID = "EVALUATION_UNIT_INVALID"


class ReviewStatus(StrEnum):
    DRAFT = "DRAFT"
    OWNER_APPROVED = "OWNER_APPROVED"
    FROZEN = "FROZEN"


class EvaluationUnitStatus(StrEnum):
    SCOREABLE = "SCOREABLE"
    INVALID = "INVALID"


class PolicyOutputStatus(StrEnum):
    VALID = "VALID"
    MALFORMED = "MALFORMED"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"


class SelectedToolAdmissibility(StrEnum):
    ADMISSIBLE = "ADMISSIBLE"
    INADMISSIBLE = "INADMISSIBLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StrictContractOutcome(StrEnum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    ADMISSIBLE_BUT_UNJUSTIFIED = "ADMISSIBLE_BUT_UNJUSTIFIED"
    NOT_SCORED = "NOT_SCORED"


def derive_strict_contract_outcome(
    *,
    evaluation_unit_status: EvaluationUnitStatus,
    policy_output_status: PolicyOutputStatus,
    oracle_state: OracleState,
    policy_decision: DecisionKind | None,
    selected_tool_id: str | None,
    admissible_tool_ids: tuple[str, ...],
) -> StrictContractOutcome:
    """Derive the complete Milestone 1 strict outcome from result semantics."""

    if evaluation_unit_status is EvaluationUnitStatus.INVALID:
        return StrictContractOutcome.NOT_SCORED
    if oracle_state is OracleState.EVALUATION_UNIT_INVALID:
        raise ValueError("a scoreable result cannot derive from EVALUATION_UNIT_INVALID")
    if policy_output_status in {
        PolicyOutputStatus.MALFORMED,
        PolicyOutputStatus.UNKNOWN_TOOL,
    }:
        return StrictContractOutcome.INCORRECT

    selected_admissible_member = (
        policy_decision is DecisionKind.SELECT
        and selected_tool_id is not None
        and selected_tool_id in admissible_tool_ids
    )
    if oracle_state is OracleState.UNIQUE_ADMISSIBLE:
        return (
            StrictContractOutcome.CORRECT
            if selected_admissible_member
            else StrictContractOutcome.INCORRECT
        )
    if oracle_state is OracleState.MULTIPLE_ADMISSIBLE:
        if policy_decision is DecisionKind.INDETERMINATE:
            return StrictContractOutcome.CORRECT
        if selected_admissible_member:
            return StrictContractOutcome.ADMISSIBLE_BUT_UNJUSTIFIED
        return StrictContractOutcome.INCORRECT
    if oracle_state is OracleState.NO_ADMISSIBLE:
        return (
            StrictContractOutcome.CORRECT
            if policy_decision is DecisionKind.NO_TOOL
            else StrictContractOutcome.INCORRECT
        )
    if oracle_state is OracleState.CONTRACT_INVALID:
        return (
            StrictContractOutcome.CORRECT
            if policy_decision is DecisionKind.INVALID_CONTRACT
            else StrictContractOutcome.INCORRECT
        )
    raise ValueError(f"unsupported oracle state: {oracle_state}")


class FailureCode(StrEnum):
    MALFORMED_DECISION = "F_MALFORMED_DECISION"
    UNKNOWN_TOOL = "F_UNKNOWN_TOOL"
    CONTRACT_DEFECT_IGNORED = "F_CONTRACT_DEFECT_IGNORED"
    INVALID_CONTRACT_MISCLASSIFICATION = "F_INVALID_CONTRACT_MISCLASSIFICATION"
    EXPLICIT_PROHIBITION = "F_EXPLICIT_PROHIBITION"
    FORCED_SELECTION = "F_FORCED_SELECTION"
    CAPABILITY_MISMATCH = "F_CAPABILITY_MISMATCH"
    INPUT_CONTRACT_MISMATCH = "F_INPUT_CONTRACT_MISMATCH"
    OUTPUT_CONTRACT_MISMATCH = "F_OUTPUT_CONTRACT_MISMATCH"
    AUTHORITY_MISMATCH = "F_AUTHORITY_MISMATCH"
    FRESHNESS_MISMATCH = "F_FRESHNESS_MISMATCH"
    DATA_BOUNDARY_MISMATCH = "F_DATA_BOUNDARY_MISMATCH"
    AMBIGUITY_FORCED_RESOLUTION = "F_AMBIGUITY_FORCED_RESOLUTION"
    UNSUPPORTED_ABSTENTION = "F_UNSUPPORTED_ABSTENTION"


PRIMARY_FAILURE_PRECEDENCE = (
    FailureCode.MALFORMED_DECISION,
    FailureCode.UNKNOWN_TOOL,
    FailureCode.CONTRACT_DEFECT_IGNORED,
    FailureCode.INVALID_CONTRACT_MISCLASSIFICATION,
    FailureCode.EXPLICIT_PROHIBITION,
    FailureCode.FORCED_SELECTION,
    FailureCode.CAPABILITY_MISMATCH,
    FailureCode.INPUT_CONTRACT_MISMATCH,
    FailureCode.OUTPUT_CONTRACT_MISMATCH,
    FailureCode.AUTHORITY_MISMATCH,
    FailureCode.FRESHNESS_MISMATCH,
    FailureCode.DATA_BOUNDARY_MISMATCH,
    FailureCode.AMBIGUITY_FORCED_RESOLUTION,
    FailureCode.UNSUPPORTED_ABSTENTION,
)
FAILURE_PRECEDENCE_INDEX = {
    failure_code: index for index, failure_code in enumerate(PRIMARY_FAILURE_PRECEDENCE)
}


class WitnessScope(StrEnum):
    SELECTED_TOOL = "SELECTED_TOOL"
    POLICY_OUTPUT = "POLICY_OUTPUT"
    CONTRACT = "CONTRACT"


class CrossEvaluationFindingType(StrEnum):
    ORDER_SENSITIVITY = "ORDER_SENSITIVITY"
    NAME_SENSITIVITY = "NAME_SENSITIVITY"
    MATCHED_PAIR_INCONSISTENCY = "MATCHED_PAIR_INCONSISTENCY"
    REPEATED_RUN_INSTABILITY = "REPEATED_RUN_INSTABILITY"


class TaskContract(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    contract_id: str = Field(pattern=r"^[a-z0-9_]+$")
    task_summary: str = Field(min_length=1)
    required_capabilities: tuple[str, ...] = Field(min_length=1)
    accepted_authority_profiles: tuple[str, ...] = Field(min_length=1)
    prohibited_authority_profiles: tuple[str, ...] = ()
    citations_required: bool = True

    @field_validator(
        "required_capabilities",
        "accepted_authority_profiles",
        "prohibited_authority_profiles",
    )
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)


class ToolManifest(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    tool_id: str = Field(pattern=r"^[a-z0-9_]+$")
    display_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    capabilities: tuple[str, ...] = Field(min_length=1)
    authority_profiles: tuple[str, ...] = Field(min_length=1)
    provides_citations: bool

    @field_validator("capabilities", "authority_profiles")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)


class PolicyView(ContractModel):
    """The complete and only supported input to a trusted policy adapter."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    contract: TaskContract
    tools: tuple[ToolManifest, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_tool_ids(self) -> Self:
        tool_ids = [tool.tool_id for tool in self.tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise ValueError("tools must have unique tool_id values")
        return self


class ScenarioMetadata(ContractModel):
    """Evaluator-only labels that never enter the policy adapter input."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    family_id: str = Field(pattern=r"^[a-z0-9_]+$")
    family_label: str = Field(min_length=1)
    variant_label: str = Field(min_length=1)
    comparison_group_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")


class EvaluationContext(ContractModel):
    """Evaluator context copied into results for pure report projection."""

    family_id: str = Field(pattern=r"^[a-z0-9_]+$")
    family_label: str = Field(min_length=1)
    variant_label: str = Field(min_length=1)
    comparison_group_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    available_tool_ids: tuple[str, ...] = Field(min_length=1)
    task_summary: str = Field(min_length=1)
    required_capabilities: tuple[str, ...] = Field(min_length=1)
    accepted_authority_profiles: tuple[str, ...] = Field(min_length=1)
    citations_required: bool

    @field_validator("available_tool_ids", "required_capabilities", "accepted_authority_profiles")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)


class ToolDecision(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    policy_id: str = Field(pattern=r"^[a-z0-9_]+$")
    decision: DecisionKind
    selected_tool_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    cited_clause_ids: tuple[str, ...] = ()

    @field_validator("cited_clause_ids")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(values, "cited_clause_ids")

    @model_validator(mode="after")
    def selected_tool_matches_decision(self) -> Self:
        if self.decision is DecisionKind.SELECT and self.selected_tool_id is None:
            raise ValueError("SELECT requires selected_tool_id")
        if self.decision is not DecisionKind.SELECT and self.selected_tool_id is not None:
            raise ValueError("non-SELECT decisions must not set selected_tool_id")
        return self


class OracleRecord(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    oracle_state: OracleState
    admissible_tool_ids: tuple[str, ...] = ()
    decisive_clause_ids: tuple[str, ...] = ()
    expected_decision: DecisionKind | None
    review_status: ReviewStatus
    construction_notes: dict[str, str] = Field(default_factory=dict)

    @field_validator("admissible_tool_ids", "decisive_clause_ids")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)

    @model_validator(mode="after")
    def state_shape_is_consistent(self) -> Self:
        expected_shapes = {
            OracleState.UNIQUE_ADMISSIBLE: (1, DecisionKind.SELECT),
            OracleState.MULTIPLE_ADMISSIBLE: (None, DecisionKind.INDETERMINATE),
            OracleState.NO_ADMISSIBLE: (0, DecisionKind.NO_TOOL),
            OracleState.CONTRACT_INVALID: (0, DecisionKind.INVALID_CONTRACT),
            OracleState.EVALUATION_UNIT_INVALID: (0, None),
        }
        expected_count, expected_decision = expected_shapes[self.oracle_state]
        if expected_count is not None and len(self.admissible_tool_ids) != expected_count:
            raise ValueError(f"{self.oracle_state} requires {expected_count} admissible tools")
        if (
            self.oracle_state is OracleState.MULTIPLE_ADMISSIBLE
            and len(self.admissible_tool_ids) < 2
        ):
            raise ValueError("MULTIPLE_ADMISSIBLE requires at least two admissible tools")
        if self.expected_decision is not expected_decision:
            raise ValueError(f"{self.oracle_state} requires expected_decision={expected_decision}")
        return self


class ClauseWitness(ContractModel):
    clause_id: str = Field(min_length=1)
    failure_code: FailureCode
    scope: WitnessScope
    tool_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    expected_values: tuple[str, ...] = ()
    actual_values: tuple[str, ...] = ()

    @field_validator("expected_values", "actual_values")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)

    @model_validator(mode="after")
    def tool_id_matches_scope(self) -> Self:
        if self.scope is WitnessScope.SELECTED_TOOL and self.tool_id is None:
            raise ValueError("SELECTED_TOOL witness requires tool_id")
        if self.scope is not WitnessScope.SELECTED_TOOL and self.tool_id is not None:
            raise ValueError("non-tool witness must not set tool_id")
        return self


class EvaluationResult(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    context: EvaluationContext
    policy_id: str = Field(pattern=r"^[a-z0-9_]+$")
    evaluation_unit_status: EvaluationUnitStatus
    policy_output_status: PolicyOutputStatus
    oracle_state: OracleState
    admissible_tool_ids: tuple[str, ...]
    decisive_clause_ids: tuple[str, ...]
    policy_decision: DecisionKind | None
    selected_tool_id: str | None = Field(pattern=r"^[a-z0-9_]+$")
    selected_tool_admissibility: SelectedToolAdmissibility
    strict_contract_outcome: StrictContractOutcome
    violated_clause_ids: tuple[str, ...]
    violation_witnesses: tuple[ClauseWitness, ...]
    failure_codes: tuple[FailureCode, ...]
    primary_failure_code: FailureCode | None
    evaluation_invalid_reasons: tuple[str, ...]
    scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    metadata_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    oracle_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator(
        "admissible_tool_ids",
        "decisive_clause_ids",
        "violated_clause_ids",
        "evaluation_invalid_reasons",
    )
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)

    @field_validator("failure_codes")
    @classmethod
    def reject_duplicate_failures(cls, values: tuple[FailureCode, ...]) -> tuple[FailureCode, ...]:
        if len(values) != len(set(values)):
            raise ValueError("failure_codes must not contain duplicates")
        return values

    @model_validator(mode="after")
    def evaluation_unit_semantics_are_consistent(self) -> Self:
        if self.evaluation_unit_status is EvaluationUnitStatus.SCOREABLE:
            if self.evaluation_invalid_reasons:
                raise ValueError("SCOREABLE result cannot have evaluation-invalid reasons")
            if self.oracle_state is OracleState.EVALUATION_UNIT_INVALID:
                raise ValueError("EVALUATION_UNIT_INVALID cannot be scoreable")
        else:
            if not self.evaluation_invalid_reasons:
                raise ValueError("INVALID result requires an evaluation-invalid reason")
            if self.oracle_state is not OracleState.EVALUATION_UNIT_INVALID:
                raise ValueError("INVALID result must use EVALUATION_UNIT_INVALID")
            if self.selected_tool_admissibility is not SelectedToolAdmissibility.NOT_APPLICABLE:
                raise ValueError("INVALID result must use NOT_APPLICABLE tool admissibility")
        return self

    @model_validator(mode="after")
    def policy_output_semantics_are_consistent(self) -> Self:
        available_tool_ids = set(self.context.available_tool_ids)
        if not set(self.admissible_tool_ids).issubset(available_tool_ids):
            raise ValueError("admissible_tool_ids must be a subset of available_tool_ids")

        if self.policy_output_status is PolicyOutputStatus.MALFORMED:
            if self.policy_decision is not None or self.selected_tool_id is not None:
                raise ValueError("MALFORMED output cannot contain a normalized decision")
            if self.selected_tool_admissibility is not SelectedToolAdmissibility.NOT_APPLICABLE:
                raise ValueError("MALFORMED output must have NOT_APPLICABLE admissibility")
            if FailureCode.MALFORMED_DECISION not in self.failure_codes:
                raise ValueError("MALFORMED output requires F_MALFORMED_DECISION")
            if set(self.failure_codes) != {FailureCode.MALFORMED_DECISION}:
                raise ValueError("MALFORMED output can contain only F_MALFORMED_DECISION")
        elif self.policy_decision is None:
            raise ValueError("non-malformed output requires policy_decision")

        if self.policy_output_status is PolicyOutputStatus.UNKNOWN_TOOL:
            if (
                self.policy_decision is not DecisionKind.SELECT
                or self.selected_tool_id is None
                or FailureCode.UNKNOWN_TOOL not in self.failure_codes
            ):
                raise ValueError("UNKNOWN_TOOL requires SELECT, tool ID, and F_UNKNOWN_TOOL")
            if self.selected_tool_id in available_tool_ids:
                raise ValueError("UNKNOWN_TOOL selected ID must be absent from available_tool_ids")
            if self.selected_tool_admissibility is SelectedToolAdmissibility.ADMISSIBLE:
                raise ValueError("UNKNOWN_TOOL selection cannot be ADMISSIBLE")
        if self.policy_output_status is PolicyOutputStatus.VALID and (
            FailureCode.MALFORMED_DECISION in self.failure_codes
            or FailureCode.UNKNOWN_TOOL in self.failure_codes
        ):
            raise ValueError("VALID output cannot contain malformed or unknown-tool failures")
        if (
            self.policy_output_status is PolicyOutputStatus.VALID
            and self.policy_decision is DecisionKind.SELECT
            and self.selected_tool_id not in available_tool_ids
        ):
            raise ValueError("VALID SELECT requires an ID in available_tool_ids")

        if self.policy_decision is DecisionKind.SELECT:
            if self.selected_tool_id is None:
                raise ValueError("SELECT requires selected_tool_id")
            if (
                self.evaluation_unit_status is EvaluationUnitStatus.SCOREABLE
                and self.selected_tool_admissibility is SelectedToolAdmissibility.NOT_APPLICABLE
            ):
                raise ValueError("SELECT requires an admissibility classification")
        elif self.selected_tool_id is not None:
            raise ValueError("non-SELECT result cannot contain selected_tool_id")

        if self.selected_tool_admissibility in {
            SelectedToolAdmissibility.ADMISSIBLE,
            SelectedToolAdmissibility.INADMISSIBLE,
        } and (self.policy_decision is not DecisionKind.SELECT or self.selected_tool_id is None):
            raise ValueError("tool admissibility requires SELECT and selected_tool_id")
        if (
            self.selected_tool_admissibility is SelectedToolAdmissibility.NOT_APPLICABLE
            and self.selected_tool_id is not None
            and self.evaluation_unit_status is EvaluationUnitStatus.SCOREABLE
        ):
            raise ValueError("NOT_APPLICABLE can accompany a selected tool only on INVALID units")
        return self

    @model_validator(mode="after")
    def oracle_and_outcome_semantics_are_consistent(self) -> Self:
        admissible_count = len(self.admissible_tool_ids)
        if self.oracle_state is OracleState.UNIQUE_ADMISSIBLE and admissible_count != 1:
            raise ValueError("UNIQUE_ADMISSIBLE requires exactly one admissible tool")
        if self.oracle_state is OracleState.MULTIPLE_ADMISSIBLE and admissible_count < 2:
            raise ValueError("MULTIPLE_ADMISSIBLE requires at least two admissible tools")
        if (
            self.oracle_state
            in {
                OracleState.NO_ADMISSIBLE,
                OracleState.CONTRACT_INVALID,
                OracleState.EVALUATION_UNIT_INVALID,
            }
            and admissible_count
        ):
            raise ValueError(f"{self.oracle_state} requires an empty admissible set")

        if self.selected_tool_admissibility is SelectedToolAdmissibility.ADMISSIBLE and (
            self.selected_tool_id not in self.context.available_tool_ids
            or self.selected_tool_id not in self.admissible_tool_ids
        ):
            raise ValueError(
                "ADMISSIBLE selected tool must appear in available_tool_ids and admissible_tool_ids"
            )
        if (
            self.evaluation_unit_status is EvaluationUnitStatus.SCOREABLE
            and self.policy_output_status is PolicyOutputStatus.VALID
            and self.selected_tool_admissibility is SelectedToolAdmissibility.INADMISSIBLE
            and (
                self.selected_tool_id not in self.context.available_tool_ids
                or self.selected_tool_id in self.admissible_tool_ids
            )
        ):
            raise ValueError(
                "INADMISSIBLE valid selected tool must appear in available_tool_ids and "
                "outside admissible_tool_ids"
            )

        derived_outcome = derive_strict_contract_outcome(
            evaluation_unit_status=self.evaluation_unit_status,
            policy_output_status=self.policy_output_status,
            oracle_state=self.oracle_state,
            policy_decision=self.policy_decision,
            selected_tool_id=self.selected_tool_id,
            admissible_tool_ids=self.admissible_tool_ids,
        )
        if self.strict_contract_outcome is not derived_outcome:
            raise ValueError(
                "strict_contract_outcome does not match the derived Milestone 1 outcome: "
                f"expected {derived_outcome}"
            )
        if (
            self.strict_contract_outcome is StrictContractOutcome.ADMISSIBLE_BUT_UNJUSTIFIED
            and FailureCode.AMBIGUITY_FORCED_RESOLUTION not in self.failure_codes
        ):
            raise ValueError("ADMISSIBLE_BUT_UNJUSTIFIED requires F_AMBIGUITY_FORCED_RESOLUTION")

        if self.strict_contract_outcome is StrictContractOutcome.CORRECT and (
            self.failure_codes or self.violation_witnesses or self.violated_clause_ids
        ):
            raise ValueError("CORRECT result cannot contain policy failures or witnesses")
        if (
            self.strict_contract_outcome is StrictContractOutcome.INCORRECT
            and not self.failure_codes
        ):
            raise ValueError("INCORRECT result requires a policy failure diagnostic")
        return self

    @model_validator(mode="after")
    def diagnostic_semantics_are_consistent(self) -> Self:
        witness_clause_ids = {witness.clause_id for witness in self.violation_witnesses}
        if witness_clause_ids != set(self.violated_clause_ids):
            raise ValueError("violated_clause_ids must exactly match witness clause IDs")
        witness_failure_codes = {witness.failure_code for witness in self.violation_witnesses}
        if witness_failure_codes != set(self.failure_codes):
            raise ValueError("every failure code must have a witness and vice versa")

        expected_primary = (
            min(self.failure_codes, key=FAILURE_PRECEDENCE_INDEX.__getitem__)
            if self.failure_codes
            else None
        )
        if self.primary_failure_code is not expected_primary:
            raise ValueError("primary_failure_code is not the precedence winner")

        selected_tool_failures = {
            FailureCode.UNKNOWN_TOOL,
            FailureCode.EXPLICIT_PROHIBITION,
            FailureCode.CAPABILITY_MISMATCH,
            FailureCode.INPUT_CONTRACT_MISMATCH,
            FailureCode.OUTPUT_CONTRACT_MISMATCH,
            FailureCode.AUTHORITY_MISMATCH,
            FailureCode.FRESHNESS_MISMATCH,
            FailureCode.DATA_BOUNDARY_MISMATCH,
        }
        contract_failures = {FailureCode.CONTRACT_DEFECT_IGNORED}
        for witness in self.violation_witnesses:
            expected_scope = (
                WitnessScope.SELECTED_TOOL
                if witness.failure_code in selected_tool_failures
                else WitnessScope.CONTRACT
                if witness.failure_code in contract_failures
                else WitnessScope.POLICY_OUTPUT
            )
            if witness.scope is not expected_scope:
                raise ValueError("witness scope is inconsistent with its failure code")
            if (
                witness.scope is WitnessScope.SELECTED_TOOL
                and witness.tool_id != self.selected_tool_id
            ):
                raise ValueError("selected-tool witness must reference the selected tool")
        return self


class CrossEvaluationFinding(ContractModel):
    """A multi-run finding kept separate from per-case evaluation failures."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    finding_type: CrossEvaluationFindingType
    scenario_ids: tuple[str, ...] = Field(min_length=2)
    policy_ids: tuple[str, ...] = Field(min_length=1)
    details: dict[str, str]

    @field_validator("scenario_ids", "policy_ids")
    @classmethod
    def sort_and_reject_duplicates(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)


class CounterfactualValidationStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


class CounterfactualComparisonSpec(ContractModel):
    """Evaluator-only declaration of one intended contract intervention."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    comparison_id: str = Field(pattern=r"^[a-z0-9_]+$")
    source_scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    target_scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    declared_changed_clause_ids: tuple[str, ...] = Field(min_length=1)
    evaluator_notes: str | None = Field(
        default=None,
        min_length=1,
        description="Optional public-safe evaluator notes.",
    )

    @field_validator("declared_changed_clause_ids")
    @classmethod
    def sort_and_reject_duplicate_clauses(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(values, "declared_changed_clause_ids")

    @model_validator(mode="after")
    def endpoints_are_distinct(self) -> Self:
        if self.source_scenario_id == self.target_scenario_id:
            raise ValueError("source_scenario_id and target_scenario_id must be distinct")
        return self


class CounterfactualFinding(ContractModel):
    """Validated cross-scenario relation finding, separate from policy failures."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    comparison_id: str = Field(pattern=r"^[a-z0-9_]+$")
    source_scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    target_scenario_id: str = Field(pattern=r"^[a-z0-9_]+$")
    source_scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_scenario_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    declared_changed_clause_ids: tuple[str, ...] = Field(min_length=1)
    observed_changed_contract_paths: tuple[str, ...]
    validation_status: CounterfactualValidationStatus
    invalid_comparison_reasons: tuple[str, ...]
    source_computed_oracle_state: OracleState
    target_computed_oracle_state: OracleState
    source_computed_admissible_tool_ids: tuple[str, ...]
    target_computed_admissible_tool_ids: tuple[str, ...]
    admissible_set_changed: bool
    oracle_state_changed: bool
    unique_admissible_tool_flipped: bool
    counterfactually_decisive: bool
    individual_decisiveness_established: bool
    comparison_spec_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    clause_ownership_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator(
        "declared_changed_clause_ids",
        "observed_changed_contract_paths",
        "invalid_comparison_reasons",
        "source_computed_admissible_tool_ids",
        "target_computed_admissible_tool_ids",
    )
    @classmethod
    def sort_and_reject_duplicate_values(
        cls, values: tuple[str, ...], info: object
    ) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "tuple field")
        return _sorted_unique(values, field_name)

    @model_validator(mode="after")
    def finding_semantics_are_consistent(self) -> Self:
        if self.source_scenario_id == self.target_scenario_id:
            raise ValueError("source_scenario_id and target_scenario_id must be distinct")
        if self.validation_status is CounterfactualValidationStatus.VALID:
            if self.invalid_comparison_reasons:
                raise ValueError("VALID comparison cannot have invalid-comparison reasons")
        elif not self.invalid_comparison_reasons:
            raise ValueError("INVALID comparison requires an invalid-comparison reason")

        set_changed = (
            self.source_computed_admissible_tool_ids != self.target_computed_admissible_tool_ids
        )
        state_changed = self.source_computed_oracle_state is not self.target_computed_oracle_state
        if self.admissible_set_changed is not set_changed:
            raise ValueError("admissible_set_changed does not match the computed sets")
        if self.oracle_state_changed is not state_changed:
            raise ValueError("oracle_state_changed does not match the computed states")

        for endpoint, state, admissible_tool_ids in (
            (
                "source",
                self.source_computed_oracle_state,
                self.source_computed_admissible_tool_ids,
            ),
            (
                "target",
                self.target_computed_oracle_state,
                self.target_computed_admissible_tool_ids,
            ),
        ):
            if state is OracleState.UNIQUE_ADMISSIBLE and len(admissible_tool_ids) != 1:
                raise ValueError(f"{endpoint} UNIQUE_ADMISSIBLE requires exactly one tool")
            if state is OracleState.MULTIPLE_ADMISSIBLE and len(admissible_tool_ids) < 2:
                raise ValueError(f"{endpoint} MULTIPLE_ADMISSIBLE requires at least two tools")
            if state in {OracleState.NO_ADMISSIBLE, OracleState.CONTRACT_INVALID} and (
                admissible_tool_ids
            ):
                raise ValueError(f"{endpoint} {state} requires an empty admissible set")
            if state is OracleState.EVALUATION_UNIT_INVALID:
                raise ValueError("counterfactual endpoints must come from the relation checker")

        unique_flip = (
            self.source_computed_oracle_state is OracleState.UNIQUE_ADMISSIBLE
            and self.target_computed_oracle_state is OracleState.UNIQUE_ADMISSIBLE
            and len(self.source_computed_admissible_tool_ids) == 1
            and len(self.target_computed_admissible_tool_ids) == 1
            and set_changed
        )
        if self.unique_admissible_tool_flipped is not unique_flip:
            raise ValueError("unique_admissible_tool_flipped does not match the computed relation")

        decisive = self.validation_status is CounterfactualValidationStatus.VALID and (
            set_changed or state_changed
        )
        if self.counterfactually_decisive is not decisive:
            raise ValueError("counterfactually_decisive does not match comparison semantics")
        individually_decisive = decisive and len(self.declared_changed_clause_ids) == 1
        if self.individual_decisiveness_established is not individually_decisive:
            raise ValueError(
                "individual_decisiveness_established requires a decisive singleton intervention"
            )
        return self
