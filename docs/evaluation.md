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

Milestone 2A adds separate `CounterfactualComparisonSpec` and `CounterfactualFinding` artifacts. The analyzer validates an evaluator-only contract intervention, holds non-owned semantic fields and canonical tool manifests constant, runs the existing relation checker independently at both endpoints, and marks the declared clause set decisive for the admissibility relation only when the admissible set or computed oracle state changes.

These findings are cross-scenario relation artifacts. They are not attached to `EvaluationResult`, do not become policy failure codes, and do not use stored oracle labels or policy decisions as their source of truth. Policy matched-pair sensitivity would require separate endpoint policy decisions and is not evaluated in Milestone 2A. See [Counterfactual clause semantics](counterfactual-semantics.md).

## V2 relation semantics

Milestone 2B is an isolated review-candidate layer. Its relation checker consumes only `PolicyViewV2` and applies six registered clauses:

| Clause | Requirement |
| --- | --- |
| `capability.requirement` | Every required capability appears in the manifest. |
| `authority.requirement` | At least one accepted authority profile appears in the manifest, consistent with v1. |
| `input.requirement` | Every required input profile appears in the manifest's accepted profiles. |
| `output.requirement` | Every required output profile appears in the manifest's produced profiles. |
| `output.citations` | A citations-required contract admits only a citation-capable tool. |
| `tool.prohibition` | A forbidden tool is inadmissible even if every other clause matches. |
| `tool.requirement` | When a required tool ID is present, every differently identified tool is inadmissible. |

`required_tool_id` is optional. A matching available tool must still satisfy every other clause; nonmatching available tools receive `F_REQUIRED_TOOL_MISMATCH`. An unavailable required ID produces `NO_ADMISSIBLE`, not `CONTRACT_INVALID`. An unavailable forbidden ID may be redundant and is not inherently invalid. The deliberate contradiction is a contract that requires and forbids the same tool: the checker returns `CONTRACT_INVALID`, an empty set, `INVALID_CONTRACT`, a stable reason, and no ordinary tool witnesses before evaluating manifests. Otherwise it derives `UNIQUE_ADMISSIBLE`, `MULTIPLE_ADMISSIBLE`, or `NO_ADMISSIBLE` from the per-tool relation.

## Proposed expectations and review state

`OracleExpectationV2` is a human-authored `PROPOSED` artifact. It records an expected state, admissible set, contract-faithful response, and public rationale, but it is never an input to relation computation. `OracleReviewRecordV2` separately supports `PENDING`, `AGREE`, `DISAGREE`, and `ADJUDICATED` dispositions.

The validator computes every relation first, then compares it with the proposal and review:

- a matching proposal with `PENDING` review is scoreable as an artifact relationship but remains `PENDING_REVIEW`, `ready_for_scoring=false`, and `ready_for_freeze=false`;
- a completed agreement is coherent only when the proposal, reviewed values, and independently computed relation agree and policy-output independence was recorded;
- a completed disagreement without adjudication is `EVALUATION_UNIT_INVALID`;
- an adjudication is coherent only when both adjudicated values are present and match the independent relation;
- missing, contradictory, or malformed linkage is either a visible invalid-unit finding or a hard artifact-integrity failure.

One pure lifecycle derivation is authoritative for match flags, review readiness, evaluation-unit status, invalid reasons, and row-level scoring/freeze readiness. Persisted findings carry the review evidence and available-tool provenance needed to reject contradictory serialized states. Before a finding or provisional manifest is used as evidence, source-aware verification recomputes the relation, witnesses, hashes, lifecycle, and manifest contents from the original scenario, expectation, and review artifacts.

`CONTRACT_INVALID` describes the policy-visible task contract and can become ready once coherently reviewed. `EVALUATION_UNIT_INVALID` describes a defective expectation, review, adjudication, or artifact relationship and must not enter policy metrics. The checked-in v2.1 bundle records 12 owner agreements; replacement `v2_scenario_012` is `REVIEW_COMPLETE`, scoreable, and row-level ready for freeze. No current unit is evaluation-unit invalid. A separate blind independent model review reports 12/12 agreement with both the owner-reviewed and computed relations, but independent human review has not occurred. Row-level readiness and model-review agreement do not make the provisional bundle frozen. The bundle evaluates no policy and contains no policy decisions. See [Oracle review candidates](oracle-review-candidates.md).
