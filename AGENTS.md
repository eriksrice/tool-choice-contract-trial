# Repository Contributor Contract

## Product boundary

This repository evaluates whether declared tool manifests satisfy typed task contracts. It does not execute tools or verify runtime truth, arguments, outputs, side effects, retries, idempotency, rollback, or sandbox behavior. Do not add live model calls, provider integrations, retrieval, orchestration, services, databases, queues, or frontends.

## Evaluation integrity

- A policy adapter receives only `PolicyView`: an opaque scenario ID, the task contract, and available tool manifests.
- Oracle records, comparison specifications, evaluator metadata, expected decisions, and findings remain evaluator-only.
- The deterministic relation checker, not stored oracle labels or policy decisions, computes admissibility.
- The v2 relation checker must receive only `PolicyViewV2`; proposed expectations, reviews, family labels, and adjudications remain evaluator-only and are compared only after relation computation.
- Incompatibility witnesses are per-scenario tool facts; counterfactual findings are cross-scenario evaluator artifacts. Do not turn either into post-hoc policy labels.
- Keep intentional policy-visible `CONTRACT_INVALID` relations distinct from defective `EVALUATION_UNIT_INVALID` authoring or review relationships.
- Treat loaded v2 findings and manifests as schema-valid but untrusted until source-aware verification recomputes their relation, lifecycle, witnesses, hashes, and counts.
- Never mutate fixtures, oracle records, or expected semantics after observing policy output.

## Types and determinism

- Pydantic v2 models are the schema authority. Checked-in JSON Schemas are deterministic projections.
- Preserve UTF-8, stable record ordering, sorted JSON keys, fixed separators, and exactly one newline per JSONL record.
- Reports must be pure projections of validated canonical bundles and must contain no volatile timestamps or environment-specific paths.
- Add no dependency without a demonstrated need and explicit scope review.

## Compatibility and scope

- Preserve the frozen Milestone 1 fixtures, commands, schemas, goldens, and hashes.
- Preserve the frozen Milestone 2A comparison fixtures, schemas, counterfactual registry and hash, commands, goldens, and hashes.
- Keep the v2 `2.1.0` models, schemas, fixtures, registry, and review artifacts explicitly separate from v1; do not build an implicit migration path.
- Keep new evaluator-only artifacts separate from policy-visible inputs.
- Do not add a scenario family, contract clause class, execution behavior, or broader claim unless the current task explicitly authorizes it.
- Stop at the milestone boundary named by the task.

## Required checks

```bash
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m tool_choice_contract_trial \
  check-schemas --directory schemas/v1
uv run --frozen python -m tool_choice_contract_trial \
  check-schemas-v2 --directory schemas/v2
```

For deterministic replay and exact artifact comparisons, follow [docs/reproducibility.md](docs/reproducibility.md).
