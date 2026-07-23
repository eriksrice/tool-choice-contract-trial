# Reproducibility

## Environment

- Python `3.12`
- `uv` with the checked-in `uv.lock`
- no network provider or credentials required at runtime

Install the locked environment:

```bash
uv sync --frozen
```

## Quality and schema checks

```bash
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m tool_choice_contract_trial \
  check-schemas --directory schemas/v1
```

## Two-run deterministic replay

```bash
replay_dir=$(mktemp -d)
mkdir -p "$replay_dir/run_1" "$replay_dir/run_2"

uv run --frozen python -m tool_choice_contract_trial evaluate \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --metadata fixtures/milestone_1/authority_profiles/evaluation_metadata.jsonl \
  --oracles fixtures/milestone_1/authority_profiles/oracles.jsonl \
  --decisions fixtures/milestone_1/authority_profiles/replay_decisions.jsonl \
  --results "$replay_dir/run_1/results.jsonl" \
  --report "$replay_dir/run_1/report.md"

uv run --frozen python -m tool_choice_contract_trial evaluate \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --metadata fixtures/milestone_1/authority_profiles/evaluation_metadata.jsonl \
  --oracles fixtures/milestone_1/authority_profiles/oracles.jsonl \
  --decisions fixtures/milestone_1/authority_profiles/replay_decisions.jsonl \
  --results "$replay_dir/run_2/results.jsonl" \
  --report "$replay_dir/run_2/report.md"

cmp "$replay_dir/run_1/results.jsonl" "$replay_dir/run_2/results.jsonl"
cmp "$replay_dir/run_1/report.md" "$replay_dir/run_2/report.md"
cmp "$replay_dir/run_1/results.jsonl" tests/golden/results.jsonl
cmp "$replay_dir/run_1/report.md" tests/golden/report.md
```

Successful `cmp` commands produce no output.

## Offline frozen replay

After the locked environment is available locally:

```bash
offline_dir=$(mktemp -d)
uv run --offline --frozen python -m tool_choice_contract_trial evaluate \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --metadata fixtures/milestone_1/authority_profiles/evaluation_metadata.jsonl \
  --oracles fixtures/milestone_1/authority_profiles/oracles.jsonl \
  --decisions fixtures/milestone_1/authority_profiles/replay_decisions.jsonl \
  --results "$offline_dir/results.jsonl" \
  --report "$offline_dir/report.md"

cmp "$offline_dir/results.jsonl" tests/golden/results.jsonl
cmp "$offline_dir/report.md" tests/golden/report.md
```

## Canonical artifact hashes

For the accepted Milestone 1 fixtures and replay decisions:

| Artifact | SHA-256 |
| --- | --- |
| `tests/golden/results.jsonl` | `9744b7aa3ca2c1b538fbc2e78d918941542396fd00108229d7261ec0a9852d3d` |
| `tests/golden/report.md` | `ae9ef0d081c041edd2f1c3ff2b9714429da4ff5a12cd9036cba2761b664a5fdc` |

The result bundle contains hashes of each scenario, metadata row, oracle row, and decision row. It deliberately contains no timestamps or absolute paths.

## Why the output is stable

- input loaders reject duplicate or mismatched rows;
- Pydantic models normalize sorted tuple fields and reject duplicates;
- records are ordered by opaque scenario ID;
- JSON object keys are sorted with fixed separators;
- every JSONL record has exactly one trailing newline;
- the report renderer reads only the validated result bundle;
- volatile run metadata is excluded from canonical artifacts.
