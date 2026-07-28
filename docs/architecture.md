# Architecture and System Boundary

## Purpose

Tool Choice Contract Trial evaluates whether a recorded policy decision is admissible under an explicit task contract and a set of declared tool manifests. Milestone 2A also validates evaluator-only counterfactual comparisons between existing v1 scenarios. Milestone 2B adds a separate v2 path that computes admissibility before comparing it with proposed expectations and review records. Every path is local and deterministic: typed files enter, validated artifacts leave, and no tool is executed.

## Components

| Component | Responsibility | Must not receive or do |
| --- | --- | --- |
| `PolicyView` | Carry an opaque scenario ID, task contract, and available manifests. | Oracle labels, expected decisions, admissible IDs, evaluator metadata. |
| `ReplayPolicyAdapter` | Return one trusted, schema-valid stored `ToolDecision` for the matching scenario. | Load oracle files or evaluate compatibility. |
| Relation checker | Compare contract requirements with declared manifests and collect incompatibility witnesses. | Execute tools or infer undeclared runtime behavior. |
| Evaluator | Cross-check the oracle, normalize status dimensions, derive strict outcome, and assemble diagnostics. | Hide fixture/oracle disagreement as a policy error. |
| `CounterfactualComparisonSpec` | Declare evaluator-only source, target, and changed clause IDs. | Carry policy output, oracle answers, or result labels. |
| Counterfactual analyzer | Validate clause-owned contract changes and compare independently computed endpoint relations. | Read policy decisions or use stored oracle labels as truth. |
| `PolicyViewV2` | Carry only an opaque scenario ID, v2 contract, and v2 manifests. | Family labels, proposed answers, reviews, decisions, or evaluation labels. |
| V2 relation checker | Derive state, admissible set, witnesses, and semantic contract defects solely from `PolicyViewV2`. | Read proposals, reviews, adjudications, or policy decisions. |
| `OracleExpectationV2` | Store an evaluator-only proposed state, set, response, rationale, family, and variant. | Become computed truth or claim independent review. |
| `OracleReviewRecordV2` | Record pending, agreeing, disagreeing, or adjudicated review state and policy-output independence. | Invent a reviewer, imply a pending review is complete, or alter the computed relation. |
| V2 validation layer | Compare the already-computed relation with the proposal and review; classify readiness and evaluation-unit defects. | Score a policy, freeze a pending candidate, or convert contract invalidity into fixture invalidity. |
| Serializer | Write stable UTF-8 canonical JSONL. | Add timestamps or environment-specific paths. |
| Report renderers | Produce Markdown solely from validated result or finding bundles. | Add volatile run context or infer missing evidence. |

## Data paths

```text
Policy-visible path
  scenarios.jsonl -> PolicyView -> ReplayPolicyAdapter -> ToolDecision

Evaluator-only path
  evaluation_metadata.jsonl -----+
  oracles.jsonl ------------------+-> deterministic evaluator
  PolicyView + ToolDecision ------+
                                      |
                                      +-> results.jsonl -> report.md

Counterfactual evaluator-only path
  scenarios.jsonl -> PolicyView --------+
  comparisons.jsonl --------------------+-> structural validator
                                            + relation checker at each endpoint
                                            -> counterfactual_findings.jsonl
                                            -> counterfactual_report.md

Milestone 2B review-candidate path
  scenarios.jsonl -> PolicyViewV2 -> v2 relation checker ----+
  oracle_expectations.jsonl ----------------------------------+-> validation findings
  oracle_reviews.jsonl ---------------------------------------+   + provisional manifest
                                                               +-> review packet
                                                               +-> invalid-unit register
```

The loading paths are separate in code. `policy_io.py` handles v1 policy-visible scenarios and stored decisions; `oracle_io.py`, `evaluation_io.py`, and `counterfactual_io.py` handle v1 evaluator-only material. `v2_io.py` validates the separately stored v2 policy views, proposals, and reviews. The v2 relation checker receives only `PolicyViewV2`, and the validation command has no policy-decision input. Boundary tests confirm that policy-visible identifiers and inputs do not expose answer labels, review state, family labels, or comparison metadata.

## Version boundary

The v1 models, schemas, fixtures, registry, commands, and canonical outputs remain frozen for Milestones 1 and 2A. The current v2.1 candidate uses explicit `*V2` models, its own relation registry, `schemas/v2/`, and `fixtures/milestone_2b/`. Git history preserves the earlier v2.0 candidate. This is an intentionally narrow parallel layer, not a migration framework: v2 does not rewrite, upgrade, or reinterpret v1 artifacts, and mixed v2 candidate versions are not supported in one bundle.

## Declared-manifest boundary

Compatibility is computed only from fields present in `TaskContract` and `ToolManifest`. The repository does not:

- invoke any declared tool;
- evaluate tool arguments or outputs;
- verify side effects or runtime truth;
- add live model calls;
- require a service, database, queue, frontend, or network provider.

This is an architectural guarantee against accidental leakage for trusted adapters. It is not a sandbox for arbitrary hostile adapter code.

## Deterministic boundary

The deterministic bundle excludes volatile metadata. Serialization uses UTF-8, sorted JSON object keys, stable record ordering, fixed separators, and exactly one newline per JSONL record. Markdown is a pure function of the validated result bundle. See [Reproducibility](reproducibility.md).

## Repository map

- `tool_choice_contract_trial/models.py`: authoritative types and cross-field invariants.
- `tool_choice_contract_trial/oracle.py`: declared-manifest relation assessment.
- `tool_choice_contract_trial/evaluation.py`: per-case evaluation and diagnostics.
- `tool_choice_contract_trial/counterfactual_registry.py`: supported clauses, owned paths, and finding-integrity authority.
- `tool_choice_contract_trial/counterfactual.py`: comparison validation and admissibility-relation decisiveness.
- `tool_choice_contract_trial/counterfactual_reporting.py`: pure finding projection.
- `tool_choice_contract_trial/v2_models.py`: strict v2 policy, proposal, review, finding, and manifest types.
- `tool_choice_contract_trial/v2_registry.py`: v2 relation clauses and canonical field ownership.
- `tool_choice_contract_trial/v2_relation.py`: independent v2 declared-manifest relation assessment.
- `tool_choice_contract_trial/v2_validation.py`: proposal/review comparison and provisional manifest assembly.
- `tool_choice_contract_trial/v2_reporting.py`: pure v2 review-packet projection.
- `tool_choice_contract_trial/policy.py`: replay adapter.
- `tool_choice_contract_trial/serialization.py`: canonical JSON and hashing.
- `tool_choice_contract_trial/reporting.py`: pure Markdown projection.
- `tool_choice_contract_trial/cli.py`: `argparse` command surface.

Formal comparison validity and attribution rules are documented in [Counterfactual clause semantics](counterfactual-semantics.md). The v2 proposal and review lifecycle is documented in [Oracle review candidates](oracle-review-candidates.md).
