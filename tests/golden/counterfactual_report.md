# Tool Choice Contract Trial — Milestone 2A Counterfactual Findings

> Scope: deterministic counterfactual mechanics over the existing synthetic authority family only; this does not validate a broader benchmark.

## Comparisons

### `counterfactual_001`

- Validation status: `VALID`
- Endpoints: `scenario_001` → `scenario_002`
- Declared clause intervention: `authority.requirement`
- Observed contract paths: `contract.accepted_authority_profiles`
- Held constant: task summary, schema compatibility, tool availability, and canonical tool manifests.
- Source relation: `UNIQUE_ADMISSIBLE` with `evidence_tool_01`
- Target relation: `UNIQUE_ADMISSIBLE` with `evidence_tool_02`
- Admissible set changed: yes
- Oracle state changed: no
- Unique admissible tool flipped: yes
- Declared clause set counterfactually decisive: yes
- Individual decisiveness established: yes

### `counterfactual_002`

- Validation status: `VALID`
- Endpoints: `scenario_001` → `scenario_004`
- Declared clause intervention: `authority.requirement`
- Observed contract paths: `contract.accepted_authority_profiles`
- Held constant: task summary, schema compatibility, tool availability, and canonical tool manifests.
- Source relation: `UNIQUE_ADMISSIBLE` with `evidence_tool_01`
- Target relation: `MULTIPLE_ADMISSIBLE` with `evidence_tool_01`, `evidence_tool_02`
- Admissible set changed: yes
- Oracle state changed: yes
- Unique admissible tool flipped: no
- Declared clause set counterfactually decisive: yes
- Individual decisiveness established: yes

## Why this is not an incompatibility witness

An incompatibility witness explains why one declared tool manifest fails one contract clause in one scenario. A counterfactual finding instead validates a cross-scenario intervention, holds every other semantic input constant, and checks whether the independently computed admissible relation changes.

## Interpretation boundary

- Only singleton `authority.requirement` interventions are exercised here.
- A future multi-clause intervention would establish set-level decisiveness only unless proper-subset interventions separately establish minimality.
- The analyzer uses no stored policy decisions or oracle labels as its source of truth.
- This remains one synthetic authority family; no broader benchmark, production, or cross-domain claim follows.
