# Evaluation Semantics and Result Algebra

## Inputs

Each evaluation case combines four independently validated records:

1. `PolicyView`: policy-visible contract and manifests.
2. `ScenarioMetadata`: evaluator-only family and comparison labels.
3. `OracleRecord`: reviewed state, admissible set, decisive clauses, and expected decision.
4. `ToolDecision`: one stored policy observation.

Duplicate rows, mixed-policy replay bundles, or mismatched scenario linkage are rejected before scoring.

## Oracle states

| State | Meaning | Schema-v1 contract-faithful response |
| --- | --- | --- |
| `UNIQUE_ADMISSIBLE` | Exactly one manifest satisfies every required clause. | `SELECT` that tool. |
| `MULTIPLE_ADMISSIBLE` | At least two manifests satisfy the contract and no typed tie-break exists. | `INDETERMINATE`. |
| `NO_ADMISSIBLE` | No available manifest satisfies the contract. | `NO_TOOL`. |
| `CONTRACT_INVALID` | The schema-valid contract is intentionally contradictory or incomplete. | `INVALID_CONTRACT`. |
| `EVALUATION_UNIT_INVALID` | The fixture, oracle, or benchmark relation is defective. | Not scored. |

## Invalidity layers

- `SCHEMA_INVALID`: structural validation failed; the record never reaches scoring.
- `CONTRACT_INVALID`: the policy-visible contract is intentionally defective and may be scoreable.
- `EVALUATION_UNIT_INVALID`: the evaluation materials disagree; the row stays visible but is excluded from policy metrics.

An invalid evaluation unit can retain the observed decision and policy-output status for inspection. Its selected-tool admissibility is always `NOT_APPLICABLE`, its strict outcome is always `NOT_SCORED`, and its invalid reasons remain separate from policy diagnostics.

## Policy-output status and provenance

Results copy the complete sorted `available_tool_ids` from policy-visible manifests. This lets the result model independently enforce:

- every admissible ID is available;
- a `VALID` selection names an available tool;
- an `UNKNOWN_TOOL` selection names an unavailable tool and cannot be admissible;
- `ADMISSIBLE` means membership in both the available and admissible sets;
- a scoreable valid `INADMISSIBLE` selection is available but outside the admissible set.

## Authoritative strict-outcome algebra

`derive_strict_contract_outcome()` in `models.py` is the single strict-outcome authority used by both the evaluator and `EvaluationResult` validation.

Precedence:

1. Any `INVALID` evaluation unit -> `NOT_SCORED`.
2. A scoreable `MALFORMED` or `UNKNOWN_TOOL` output -> `INCORRECT`.
3. A scoreable valid output follows the table below.

| Oracle state | Observed policy decision | Strict outcome |
| --- | --- | --- |
| `UNIQUE_ADMISSIBLE` | Select the admissible member. | `CORRECT` |
| `UNIQUE_ADMISSIBLE` | Anything else. | `INCORRECT` |
| `MULTIPLE_ADMISSIBLE` | `INDETERMINATE`. | `CORRECT` |
| `MULTIPLE_ADMISSIBLE` | Select an admissible member. | `ADMISSIBLE_BUT_UNJUSTIFIED` |
| `MULTIPLE_ADMISSIBLE` | Anything else. | `INCORRECT` |
| `NO_ADMISSIBLE` | `NO_TOOL`. | `CORRECT` |
| `NO_ADMISSIBLE` | Anything else. | `INCORRECT` |
| `CONTRACT_INVALID` | `INVALID_CONTRACT`. | `CORRECT` |
| `CONTRACT_INVALID` | Anything else. | `INCORRECT` |

The result model recomputes the outcome and rejects any supplied contradiction.

## Diagnostics

Incompatibilities produce typed `ClauseWitness` records with:

- stable clause ID;
- failure code;
- diagnostic scope;
- selected tool ID when applicable;
- expected and actual values.

All applicable failure codes remain in the result. `primary_failure_code` is a deterministic precedence winner for concise reporting, not a replacement for the full set. Cross-case findings such as order sensitivity or matched-pair inconsistency remain outside per-case failure codes.

## Incompatibility witnesses and frozen Milestone 1 semantics

The frozen Milestone 1 family varies only authority compatibility. Its `decisive_clause_ids` remain the union of observed incompatibility witnesses, a deliberately family-specific compatibility field. Those IDs explain which clauses make declared tools inadmissible within one scenario; they do not, by themselves, establish cross-scenario causality.

## Counterfactual findings

Milestone 2A adds separate `CounterfactualComparisonSpec` and `CounterfactualFinding` artifacts. The analyzer validates an evaluator-only contract intervention, holds non-owned semantic fields and canonical tool manifests constant, runs the existing relation checker independently at both endpoints, and marks the declared clause set decisive only when the admissible set or computed oracle state changes.

These findings are cross-scenario artifacts. They are not attached to `EvaluationResult`, do not become policy failure codes, and do not use stored oracle labels or policy decisions as their source of truth. See [Counterfactual clause semantics](counterfactual-semantics.md).
