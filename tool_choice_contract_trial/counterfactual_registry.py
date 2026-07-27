"""Shared clause/path authority for Milestone 2A counterfactual findings."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .serialization import canonical_hash

AUTHORITY_CLAUSE = "authority.requirement"

CLAUSE_FIELD_OWNERSHIP: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        AUTHORITY_CLAUSE: ("contract.accepted_authority_profiles",),
    }
)
SUPPORTED_COUNTERFACTUAL_CLAUSE_IDS = tuple(sorted(CLAUSE_FIELD_OWNERSHIP))


def clause_ownership_hash() -> str:
    """Hash the active clause-to-contract-path ownership registry."""

    return canonical_hash(
        {
            "clause_field_ownership": {
                clause_id: tuple(sorted(paths))
                for clause_id, paths in sorted(CLAUSE_FIELD_OWNERSHIP.items())
            }
        }
    )


ACTIVE_CLAUSE_OWNERSHIP_HASH = clause_ownership_hash()


@dataclass(frozen=True)
class ClausePathValidation:
    """Deterministic result of validating declared clauses against observed paths."""

    reasons: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.reasons


def validate_clause_path_relationship(
    declared_clause_ids: tuple[str, ...],
    observed_contract_paths: tuple[str, ...],
) -> ClausePathValidation:
    """Validate clause support and bidirectional clause/path ownership."""

    reasons: list[str] = []
    observed_paths = set(observed_contract_paths)
    if not observed_paths:
        reasons.append("no observed contract path")

    declared_owned_paths: set[str] = set()
    for clause_id in declared_clause_ids:
        owned_paths = CLAUSE_FIELD_OWNERSHIP.get(clause_id)
        if owned_paths is None:
            reasons.append(f"unknown clause ID: {clause_id}")
            continue
        declared_owned_paths.update(owned_paths)
        if not observed_paths.intersection(owned_paths):
            reasons.append(f"declared clause has no field change: {clause_id}")

    for path in observed_contract_paths:
        if path not in declared_owned_paths:
            reasons.append(f"undeclared contract change: {path}")

    return ClausePathValidation(reasons=tuple(sorted(set(reasons))))


def validate_counterfactual_finding_integrity(
    *,
    validation_status: str,
    declared_clause_ids: tuple[str, ...],
    observed_contract_paths: tuple[str, ...],
    ownership_hash: str,
) -> None:
    """Require active registry provenance and valid clause/path claims for VALID findings."""

    if ownership_hash != ACTIVE_CLAUSE_OWNERSHIP_HASH:
        raise ValueError("clause_ownership_hash does not match the active registry")
    if validation_status != "VALID":
        return

    validation = validate_clause_path_relationship(
        declared_clause_ids,
        observed_contract_paths,
    )
    if not validation.is_valid:
        raise ValueError(
            "VALID finding violates clause/path integrity: " + "; ".join(validation.reasons)
        )
