# Limitations and Interpretation Boundary

## What Milestone 1 demonstrates

- Typed task contracts and declared tool manifests can be evaluated deterministically.
- A policy-visible input can remain structurally separate from oracle-only metadata.
- A one-clause minimal pair can flip the unique admissible tool.
- Plausible but inadmissible selection can produce a clause-level witness.
- Multiple-admissible selection can remain distinct from inadmissible selection.
- Frozen inputs can reproduce byte-identical JSONL and Markdown artifacts offline.

## What Milestone 1 does not demonstrate

- benchmark validity, representativeness, or useful statistical power;
- cross-domain performance or general policy quality;
- production readiness, adoption, deployment, or operational reliability;
- runtime truth of a declared manifest;
- tool argument correctness, output conformance, or side-effect behavior;
- live-model quality, model stability, or provider integration;
- adversarial isolation of untrusted adapter code;
- a general ontology of task or tool requirements.

## Coverage limits

The current fixture bundle is exactly one fictional evidence-retrieval family with four authority-profile variants. Capability and citation fields are intentionally held constant so authority is decisive. That makes the minimal pair legible, but it cannot support claims about other clauses, combinations, or domains.

The checked-in decisions are a trusted replay chosen to exercise mechanics. They are not evidence that one policy outperforms another.

## Semantic limits

- Schema v1 has no typed tie-break rule. A selected member of a multiple-admissible set is `ADMISSIBLE_BUT_UNJUSTIFIED`; `INDETERMINATE` is the strictly contract-faithful response.
- Milestone 1 decisive-clause IDs reflect observed incompatibility witnesses in an authority-only family. General counterfactual decisiveness remains undefined.
- `CONTRACT_INVALID` is an intentional policy-visible defect. `EVALUATION_UNIT_INVALID` is a defective fixture/oracle relationship. They cannot be relabeled interchangeably after observing output.
- A malformed stored replay row is structurally invalid before scoring; per-case `MALFORMED` represents a normalized observation at an adapter boundary.

## System boundary

The harness compares data. It does not execute a selected tool, inspect external state, verify effects, retry work, or test runtime behavior. No result should be read as evidence that a tool is trustworthy or correct in operation.

## Roadmap gate

Any broader evaluation should first define and test general decisive-clause semantics, preserve the policy/oracle separation, and state new claims before adding scenarios. That work is outside the current repository state.
