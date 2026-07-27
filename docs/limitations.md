# Limitations and Interpretation Boundary

## What the current milestones demonstrate

- Typed task contracts and declared tool manifests can be evaluated deterministically.
- A policy-visible input can remain structurally separate from oracle-only metadata.
- A one-clause minimal pair can flip the unique admissible tool.
- Plausible but inadmissible selection can produce a clause-level witness.
- Multiple-admissible selection can remain distinct from inadmissible selection.
- Frozen inputs can reproduce byte-identical JSONL and Markdown artifacts offline.
- Two evaluator-only comparisons can validate singleton authority interventions and identify a unique-tool flip or unique-to-multiple state change.
- Decisiveness for the admissibility relation can remain separate from per-tool incompatibility witnesses.
- An isolated v2 layer can cross-check proposed input, output/evidence, and explicit-prohibition expectations without exposing them to the relation checker.
- Review, adjudication, contract invalidity, evaluation-unit invalidity, and freeze readiness can remain distinct deterministic fields.

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
- v2 counterfactual semantics for any clause other than the frozen v1 `authority.requirement` analyzer;
- independent human review or adjudication of the 12 v2 candidates;
- a frozen v2 benchmark or policy-comparison result.

## Coverage limits

The frozen v1 policy-visible bundle remains exactly one fictional evidence-retrieval family with four authority-profile variants. Capability and citation fields are intentionally held constant so authority is decisive. Milestone 2A reuses those scenarios and adds only two evaluator-only comparison specifications.

The separate v2 review candidate contains exactly three fictional enterprise knowledge-work families and 12 cases: four input-profile cases, four output/evidence-profile cases, and four explicit-prohibition cases. Their proposed expectations match the independent computation, but every review record is still `PENDING`. This is authoring and validation coverage, not benchmark evidence.

The checked-in decisions are a trusted replay chosen to exercise mechanics. They are not evidence that one policy outperforms another.

## Semantic limits

- Schema v1 has no typed tie-break rule. A selected member of a multiple-admissible set is `ADMISSIBLE_BUT_UNJUSTIFIED`; `INDETERMINATE` is the strictly contract-faithful response.
- Milestone 1 decisive-clause IDs remain observed incompatibility-witness unions for compatibility. Milestone 2A counterfactual findings use separate validated comparison semantics.
- Only singleton authority interventions are exercised. A future multi-clause comparison is set-level unless proper-subset interventions establish minimality.
- Policy matched-pair sensitivity is a separate future concept requiring policy decisions at both endpoints; Milestone 2A does not evaluate it.
- `CONTRACT_INVALID` is an intentional policy-visible defect. `EVALUATION_UNIT_INVALID` is a defective fixture/oracle relationship. They cannot be relabeled interchangeably after observing output.
- A malformed stored replay row is structurally invalid before scoring; per-case `MALFORMED` represents a normalized observation at an adapter boundary.
- The v2 input and output pairs are controlled in their authoring design, but the v1 counterfactual analyzer cannot validate them and no v2 counterfactual finding is claimed.
- A matching v2 proposal with pending review is neither independently reviewed nor ready for scoring or freeze.

## System boundary

The harness compares data. It does not execute a selected tool, inspect external state, verify effects, retry work, or test runtime behavior. No result should be read as evidence that a tool is trustworthy or correct in operation.

## Roadmap gate

Any broader evaluation must preserve the policy/evaluator separation, define explicit ownership for each added clause, and establish claims before adding scenarios or policies. Independent review and any required adjudication must precede a v2 freeze decision. V2 counterfactual analysis, policy comparison, benchmark scaling, live-model evaluation, and Milestone 3 remain separate later gates.
