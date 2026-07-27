"""Deterministic counterfactual comparison semantics for Milestone 2A."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .errors import ArtifactIntegrityError
from .models import (
    CounterfactualComparisonSpec,
    CounterfactualFinding,
    CounterfactualValidationStatus,
    OracleState,
    PolicyView,
    TaskContract,
)
from .oracle import AUTHORITY_CLAUSE, assess_policy_view
from .serialization import canonical_hash

CLAUSE_FIELD_OWNERSHIP: dict[str, tuple[str, ...]] = {
    AUTHORITY_CLAUSE: ("contract.accepted_authority_profiles",),
}


def clause_ownership_hash(
    ownership: Mapping[str, tuple[str, ...]] = CLAUSE_FIELD_OWNERSHIP,
) -> str:
    """Hash the explicit clause-to-contract-field ownership registry."""

    return canonical_hash(
        {
            "clause_field_ownership": {
                clause_id: tuple(sorted(paths)) for clause_id, paths in sorted(ownership.items())
            }
        }
    )


def _semantic_policy_view_data(view: PolicyView) -> dict[str, Any]:
    """Normalize only fields whose schema semantics are explicitly order-insensitive."""

    return {
        "schema_version": view.schema_version,
        "scenario_id": view.scenario_id,
        "contract": view.contract.model_dump(mode="json"),
        "tools": [
            tool.model_dump(mode="json")
            for tool in sorted(view.tools, key=lambda item: item.tool_id)
        ],
    }


def semantic_policy_view_hash(view: PolicyView) -> str:
    """Hash a policy view with manifest record order normalized by opaque tool ID."""

    return canonical_hash(_semantic_policy_view_data(view))


def _observed_contract_paths(
    source_contract: TaskContract,
    target_contract: TaskContract,
) -> tuple[str, ...]:
    paths: list[str] = []
    for field_name in TaskContract.model_fields:
        if field_name == "contract_id":
            continue
        if getattr(source_contract, field_name) != getattr(target_contract, field_name):
            paths.append(f"contract.{field_name}")
    return tuple(sorted(paths))


def _canonical_tool_catalog(view: PolicyView) -> tuple[dict[str, Any], ...]:
    return tuple(
        tool.model_dump(mode="json") for tool in sorted(view.tools, key=lambda item: item.tool_id)
    )


def establishes_individual_decisiveness(
    *,
    comparison_valid: bool,
    relation_changed: bool,
    declared_changed_clause_ids: tuple[str, ...],
) -> bool:
    """Establish individual attribution only for a validated singleton intervention."""

    return comparison_valid and relation_changed and len(declared_changed_clause_ids) == 1


def analyze_comparison(
    spec: CounterfactualComparisonSpec,
    source: PolicyView,
    target: PolicyView,
    *,
    ownership: Mapping[str, tuple[str, ...]] = CLAUSE_FIELD_OWNERSHIP,
) -> CounterfactualFinding:
    """Validate one comparison and compute its endpoint relation independently."""

    if source.scenario_id != spec.source_scenario_id:
        raise ArtifactIntegrityError("source policy view does not match comparison linkage")
    if target.scenario_id != spec.target_scenario_id:
        raise ArtifactIntegrityError("target policy view does not match comparison linkage")
    if source.scenario_id == target.scenario_id:
        raise ArtifactIntegrityError("counterfactual comparison endpoints must be distinct")

    source_relation = assess_policy_view(source)
    target_relation = assess_policy_view(target)
    observed_paths = _observed_contract_paths(source.contract, target.contract)
    invalid_reasons: list[str] = []

    if (
        source.schema_version != target.schema_version
        or source.contract.schema_version != target.contract.schema_version
    ):
        invalid_reasons.append("schema versions are incompatible")
    if source.contract.task_summary != target.contract.task_summary:
        invalid_reasons.append("task summaries differ")
    if _canonical_tool_catalog(source) != _canonical_tool_catalog(target):
        invalid_reasons.append("tool manifests differ")

    declared_owned_paths: set[str] = set()
    for clause_id in spec.declared_changed_clause_ids:
        owned_paths = ownership.get(clause_id)
        if owned_paths is None:
            invalid_reasons.append(f"unknown clause ID: {clause_id}")
            continue
        declared_owned_paths.update(owned_paths)
        if not set(owned_paths).intersection(observed_paths):
            invalid_reasons.append(f"declared clause has no field change: {clause_id}")

    for path in observed_paths:
        if path not in declared_owned_paths:
            invalid_reasons.append(f"undeclared contract change: {path}")

    ordered_reasons = tuple(sorted(set(invalid_reasons)))
    comparison_valid = not ordered_reasons
    admissible_set_changed = (
        source_relation.admissible_tool_ids != target_relation.admissible_tool_ids
    )
    oracle_state_changed = source_relation.oracle_state is not target_relation.oracle_state
    relation_changed = admissible_set_changed or oracle_state_changed

    return CounterfactualFinding(
        comparison_id=spec.comparison_id,
        source_scenario_id=source.scenario_id,
        target_scenario_id=target.scenario_id,
        source_scenario_hash=semantic_policy_view_hash(source),
        target_scenario_hash=semantic_policy_view_hash(target),
        declared_changed_clause_ids=spec.declared_changed_clause_ids,
        observed_changed_contract_paths=observed_paths,
        validation_status=(
            CounterfactualValidationStatus.VALID
            if comparison_valid
            else CounterfactualValidationStatus.INVALID
        ),
        invalid_comparison_reasons=ordered_reasons,
        source_computed_oracle_state=source_relation.oracle_state,
        target_computed_oracle_state=target_relation.oracle_state,
        source_computed_admissible_tool_ids=source_relation.admissible_tool_ids,
        target_computed_admissible_tool_ids=target_relation.admissible_tool_ids,
        admissible_set_changed=admissible_set_changed,
        oracle_state_changed=oracle_state_changed,
        unique_admissible_tool_flipped=(
            source_relation.oracle_state is OracleState.UNIQUE_ADMISSIBLE
            and target_relation.oracle_state is OracleState.UNIQUE_ADMISSIBLE
            and admissible_set_changed
        ),
        counterfactually_decisive=comparison_valid and relation_changed,
        individual_decisiveness_established=establishes_individual_decisiveness(
            comparison_valid=comparison_valid,
            relation_changed=relation_changed,
            declared_changed_clause_ids=spec.declared_changed_clause_ids,
        ),
        comparison_spec_hash=canonical_hash(spec),
        clause_ownership_hash=clause_ownership_hash(ownership),
    )


def analyze_counterfactuals(
    policy_views: Iterable[PolicyView],
    specs: Iterable[CounterfactualComparisonSpec],
) -> tuple[CounterfactualFinding, ...]:
    """Analyze a linked bundle after rejecting duplicates and missing endpoints."""

    view_rows = tuple(policy_views)
    spec_rows = tuple(specs)
    views_by_id = {view.scenario_id: view for view in view_rows}
    if len(views_by_id) != len(view_rows):
        raise ArtifactIntegrityError("duplicate policy view scenario_id values")
    specs_by_id = {spec.comparison_id: spec for spec in spec_rows}
    if len(specs_by_id) != len(spec_rows):
        raise ArtifactIntegrityError("duplicate counterfactual comparison_id values")

    referenced_scenario_ids = {
        scenario_id
        for spec in spec_rows
        for scenario_id in (spec.source_scenario_id, spec.target_scenario_id)
    }
    missing_scenario_ids = sorted(referenced_scenario_ids - set(views_by_id))
    if missing_scenario_ids:
        raise ArtifactIntegrityError(
            f"counterfactual comparison linkage is missing scenarios: {missing_scenario_ids}"
        )

    return tuple(
        analyze_comparison(
            spec,
            views_by_id[spec.source_scenario_id],
            views_by_id[spec.target_scenario_id],
        )
        for spec in sorted(spec_rows, key=lambda item: item.comparison_id)
    )
