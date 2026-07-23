# Architecture and System Boundary

## Purpose

Tool Choice Contract Trial evaluates whether a recorded policy decision is admissible under an explicit task contract and a set of declared tool manifests. The Milestone 1 implementation is a local deterministic pipeline: typed files enter, validated result artifacts leave, and no tool is executed.

## Components

| Component | Responsibility | Must not receive or do |
| --- | --- | --- |
| `PolicyView` | Carry an opaque scenario ID, task contract, and available manifests. | Oracle labels, expected decisions, admissible IDs, evaluator metadata. |
| `ReplayPolicyAdapter` | Return one trusted, schema-valid stored `ToolDecision` for the matching scenario. | Load oracle files or evaluate compatibility. |
| Relation checker | Compare contract requirements with declared manifests and collect incompatibility witnesses. | Execute tools or infer undeclared runtime behavior. |
| Evaluator | Cross-check the oracle, normalize status dimensions, derive strict outcome, and assemble diagnostics. | Hide fixture/oracle disagreement as a policy error. |
| Serializer | Write stable UTF-8 canonical JSONL. | Add timestamps or environment-specific paths. |
| Report renderer | Produce Markdown solely from validated results. | Re-read fixtures, decisions, or oracle files. |

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
```

The two loading paths are separate in code. `policy_io.py` handles policy-visible scenarios and stored decisions; `oracle_io.py` and `evaluation_io.py` handle evaluator-only material. Boundary tests confirm that policy identifiers and inputs do not expose answer labels.

## Declared-manifest boundary

Compatibility is computed only from fields present in `TaskContract` and `ToolManifest`. Milestone 1 does not:

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
- `tool_choice_contract_trial/policy.py`: replay adapter.
- `tool_choice_contract_trial/serialization.py`: canonical JSON and hashing.
- `tool_choice_contract_trial/reporting.py`: pure Markdown projection.
- `tool_choice_contract_trial/cli.py`: `argparse` command surface.
