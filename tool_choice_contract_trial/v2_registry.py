"""Explicit relation-clause registry for the isolated v2 contract layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .serialization import canonical_hash

CAPABILITY_REQUIREMENT_V2 = "capability.requirement"
AUTHORITY_REQUIREMENT_V2 = "authority.requirement"
INPUT_REQUIREMENT_V2 = "input.requirement"
OUTPUT_REQUIREMENT_V2 = "output.requirement"
OUTPUT_CITATIONS_V2 = "output.citations"
TOOL_PROHIBITION_V2 = "tool.prohibition"
TOOL_REQUIREMENT_V2 = "tool.requirement"


@dataclass(frozen=True)
class RelationClauseSpecV2:
    contract_fields: tuple[str, ...]
    manifest_fields: tuple[str, ...]
    expected_failure_code: str


V2_RELATION_CLAUSE_REGISTRY: Mapping[str, RelationClauseSpecV2] = MappingProxyType(
    {
        CAPABILITY_REQUIREMENT_V2: RelationClauseSpecV2(
            contract_fields=("contract.required_capabilities",),
            manifest_fields=("manifest.capabilities",),
            expected_failure_code="F_CAPABILITY_MISMATCH",
        ),
        AUTHORITY_REQUIREMENT_V2: RelationClauseSpecV2(
            contract_fields=("contract.accepted_authority_profiles",),
            manifest_fields=("manifest.authority_profiles",),
            expected_failure_code="F_AUTHORITY_MISMATCH",
        ),
        INPUT_REQUIREMENT_V2: RelationClauseSpecV2(
            contract_fields=("contract.required_input_profiles",),
            manifest_fields=("manifest.accepted_input_profiles",),
            expected_failure_code="F_INPUT_CONTRACT_MISMATCH",
        ),
        OUTPUT_REQUIREMENT_V2: RelationClauseSpecV2(
            contract_fields=("contract.required_output_profiles",),
            manifest_fields=("manifest.produced_output_profiles",),
            expected_failure_code="F_OUTPUT_CONTRACT_MISMATCH",
        ),
        OUTPUT_CITATIONS_V2: RelationClauseSpecV2(
            contract_fields=("contract.citations_required",),
            manifest_fields=("manifest.provides_citations",),
            expected_failure_code="F_OUTPUT_CONTRACT_MISMATCH",
        ),
        TOOL_PROHIBITION_V2: RelationClauseSpecV2(
            contract_fields=("contract.forbidden_tool_ids",),
            manifest_fields=("manifest.tool_id",),
            expected_failure_code="F_EXPLICIT_PROHIBITION",
        ),
        TOOL_REQUIREMENT_V2: RelationClauseSpecV2(
            contract_fields=("contract.required_tool_id",),
            manifest_fields=("manifest.tool_id",),
            expected_failure_code="F_REQUIRED_TOOL_MISMATCH",
        ),
    }
)


def v2_relation_registry_hash() -> str:
    """Hash the canonical v2 relation-clause registry."""

    return canonical_hash(
        {
            "relation_clause_registry_v2": {
                clause_id: {
                    "contract_fields": spec.contract_fields,
                    "expected_failure_code": spec.expected_failure_code,
                    "manifest_fields": spec.manifest_fields,
                }
                for clause_id, spec in sorted(V2_RELATION_CLAUSE_REGISTRY.items())
            }
        }
    )


V2_RELATION_REGISTRY_HASH = v2_relation_registry_hash()
