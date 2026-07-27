# Limitations and Interpretation Boundary

## What the current milestones demonstrate

- Typed task contracts and declared tool manifests can be evaluated deterministically.
- A policy-visible input can remain structurally separate from oracle-only metadata.
- A one-clause minimal pair can flip the unique admissible tool.
- Plausible but inadmissible selection can produce a clause-level witness.
- Multiple-admissible selection can remain distinct from inadmissible selection.
- Frozen inputs can reproduce byte-identical JSONL and Markdown artifacts offline.
- Two evaluator-only comparisons can validate singleton authority interventions and identify a unique-tool flip or unique-to-multiple state change.
- Counterfactual decisiveness can remain separate from per-tool incompatibility witnesses.

## What the current milestones do not demonstrate

- benchmark validity, representativeness, or useful statistical power;
- cross-domain performance or general policy quality;
- production readiness, adoption, deployment, or operational reliability;
- runtime truth of a declared manifest;
- tool argument correctness, output conformance, or side-effect behavior;
- live-model quality, model stability, or provider integration;
- adversarial isolation of untrusted adapter code;
- a general ontology of task or tool requirements;
- minimality or individual causality for multi-clause interventions;
- counterfactual semantics for any clause other than `authority.requirement`.

## Coverage limits

The policy-visible fixture bundle remains exactly one fictional evidence-retrieval family with four authority-profile variants. Capability and citation fields are intentionally held constant so authority is decisive. Milestone 2A reuses those scenarios and adds only two evaluator-only comparison specifications. This cannot support claims about other clauses, combinations, or domains.

The checked-in decisions are a trusted replay chosen to exercise mechanics. They are not evidence that one policy outperforms another.

## Semantic limits

- Schema v1 has no typed tie-break rule. A selected member of a multiple-admissible set is `ADMISSIBLE_BUT_UNJUSTIFIED`; `INDETERMINATE` is the strictly contract-faithful response.
- Milestone 1 decisive-clause IDs remain observed incompatibility-witness unions for compatibility. Milestone 2A counterfactual findings use separate validated comparison semantics.
- Only singleton authority interventions are exercised. A future multi-clause comparison is set-level unless proper-subset interventions establish minimality.
- `CONTRACT_INVALID` is an intentional policy-visible defect. `EVALUATION_UNIT_INVALID` is a defective fixture/oracle relationship. They cannot be relabeled interchangeably after observing output.
- A malformed stored replay row is structurally invalid before scoring; per-case `MALFORMED` represents a normalized observation at an adapter boundary.

## System boundary

The harness compares data. It does not execute a selected tool, inspect external state, verify effects, retry work, or test runtime behavior. No result should be read as evidence that a tool is trustworthy or correct in operation.

## Roadmap gate

Any broader evaluation must preserve the policy/evaluator separation, define explicit ownership for each added clause, establish claims before adding scenarios, and separately review multi-clause minimality, new families, or policy evaluation. Those decisions are deferred beyond Milestone 2A.
