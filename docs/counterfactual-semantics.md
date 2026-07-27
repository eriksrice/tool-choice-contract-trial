# Counterfactual Clause Semantics

## Purpose

Milestone 2A defines when a declared contract clause set may be called counterfactually decisive for the admissibility relation. It uses only the existing four-scenario authority family and does not change the frozen Milestone 1 evaluation or its family-specific `decisive_clause_ids` field.

## Three distinct concepts

An **incompatibility witness** is a per-scenario, per-tool fact. It records that a declared tool manifest fails a contract clause and explains why that tool is inadmissible in that scenario.

A **counterfactual comparison** is an evaluator-only relationship between two policy-visible scenarios. It declares an intended contract intervention and asks whether all other semantic inputs were held constant.

A **clause set that is counterfactually decisive for the admissibility relation** is established only when the comparison is structurally valid and the deterministic relation checker computes a different admissible set or oracle state across the endpoints. A witness alone does not establish decisiveness for the admissibility relation.

## Clause-field ownership

Milestone 2A uses one explicit registry:

| Clause ID | Owned canonical contract path |
| --- | --- |
| `authority.requirement` | `contract.accepted_authority_profiles` |

Unknown clause IDs invalidate a comparison. Adding a future clause requires an explicit registry entry and tests; there is no generic rules language or plugin framework.

Every finding carries the deterministic hash of this active registry. A `VALID` finding is accepted only when its declared clauses and observed paths have complete bidirectional ownership under that registry. An `INVALID` finding may preserve unknown clauses, undeclared paths, or no observed change together with its reasons so failed comparisons remain inspectable.

## Comparison validity

A comparison is valid only when:

- source and target scenario IDs exist and are distinct;
- scenario and contract identifiers are treated as opaque and may differ;
- policy-view and contract schema versions are compatible;
- task summaries are identical;
- tool manifests are canonically equivalent after ordering by opaque tool ID;
- tool availability, names, descriptions, capabilities, authority profiles, and citation behavior do not drift;
- every observed semantic contract change is owned by a declared clause;
- every declared clause owns at least one observed change.

The comparison uses validated model values rather than source-line order or JSON key order. It does not discard meaningful text or manifest differences.

## Decisiveness and attribution

For a valid comparison:

```text
counterfactually decisive for the admissibility relation
  = admissible set changed OR computed oracle state changed
```

A singleton clause intervention establishes individual relation decisiveness when the admissibility relation changes. A multi-clause intervention is only set-decisive for that relation unless proper-subset interventions independently establish minimality. The finding model therefore cannot label a decisive multi-clause set as individually decisive for the relation.

## Implemented comparisons

| Comparison | Contract intervention | Computed relation change |
| --- | --- | --- |
| `scenario_001` → `scenario_002` | accepted authority changes from `public_primary` to `approved_internal` | unique admissible tool flips from `evidence_tool_01` to `evidence_tool_02` |
| `scenario_001` → `scenario_004` | accepted authority expands from `public_primary` to `public_primary` or `approved_internal` | state changes from `UNIQUE_ADMISSIBLE` to `MULTIPLE_ADMISSIBLE` |

The specifications live in [the evaluator-only comparison bundle](../fixtures/milestone_2a/authority_profiles/comparisons.jsonl). The representative outputs are [canonical JSONL](../tests/golden/counterfactual_findings.jsonl) and a [Markdown report](../tests/golden/counterfactual_report.md).

## Independence and provenance

The analyzer accepts policy-visible scenarios and evaluator-only comparison specifications. It does not accept stored policy decisions or oracle records. Each finding records endpoint artifact (policy-view) hashes, the comparison-spec hash, and the clause-ownership registry hash.

## Limitations and future gates

Only singleton `authority.requirement` interventions in one synthetic family have been exercised. Milestone 2A does not establish minimality for multi-clause changes, support other clause classes, add scenario families, evaluate live policies, or validate benchmark, production, or cross-domain claims. Policy matched-pair sensitivity is a separate future concept that would require policy decisions at both endpoints; Milestone 2A does not evaluate it. Those questions require separate scope and evidence gates.
