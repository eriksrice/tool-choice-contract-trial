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
uv run --frozen python -m tool_choice_contract_trial \
  check-schemas-v2 --directory schemas/v2
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

## Counterfactual two-run replay

```bash
comparison_dir=$(mktemp -d)
mkdir -p "$comparison_dir/run_1" "$comparison_dir/run_2"

uv run --frozen python -m tool_choice_contract_trial analyze-counterfactuals \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --comparisons fixtures/milestone_2a/authority_profiles/comparisons.jsonl \
  --findings "$comparison_dir/run_1/findings.jsonl" \
  --report "$comparison_dir/run_1/report.md"

uv run --frozen python -m tool_choice_contract_trial analyze-counterfactuals \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --comparisons fixtures/milestone_2a/authority_profiles/comparisons.jsonl \
  --findings "$comparison_dir/run_2/findings.jsonl" \
  --report "$comparison_dir/run_2/report.md"

cmp "$comparison_dir/run_1/findings.jsonl" "$comparison_dir/run_2/findings.jsonl"
cmp "$comparison_dir/run_1/report.md" "$comparison_dir/run_2/report.md"
cmp "$comparison_dir/run_1/findings.jsonl" tests/golden/counterfactual_findings.jsonl
cmp "$comparison_dir/run_1/report.md" tests/golden/counterfactual_report.md
```

## Milestone 2B two-run review-candidate replay

```bash
review_dir=$(mktemp -d)
mkdir -p "$review_dir/run_1" "$review_dir/run_2"

for run in run_1 run_2; do
  uv run --frozen python -m tool_choice_contract_trial \
    validate-oracle-candidates \
    --scenarios fixtures/milestone_2b/review_candidate/scenarios.jsonl \
    --expectations fixtures/milestone_2b/review_candidate/oracle_expectations.jsonl \
    --reviews fixtures/milestone_2b/review_candidate/oracle_reviews.jsonl \
    --findings "$review_dir/$run/oracle_validation_findings.jsonl" \
    --report "$review_dir/$run/oracle_review_packet.md" \
    --manifest "$review_dir/$run/provisional_bundle_manifest.json" \
    --invalid-unit-register "$review_dir/$run/invalid_unit_register.jsonl"
done

for artifact in \
  oracle_validation_findings.jsonl \
  oracle_review_packet.md \
  provisional_bundle_manifest.json \
  invalid_unit_register.jsonl; do
  cmp "$review_dir/run_1/$artifact" "$review_dir/run_2/$artifact"
  cmp "$review_dir/run_1/$artifact" "tests/golden/milestone_2b/$artifact"
done
```

The checked-in invalid-unit register is empty. Replacement `v2_scenario_012` has a matching proposed relation but remains honestly `PENDING_REVIEW`; focused tests also exercise mismatches, missing rows, contradictory completed reviews, incomplete adjudication, duplicate rows, and malformed linkage.

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

uv run --offline --frozen python -m tool_choice_contract_trial \
  analyze-counterfactuals \
  --scenarios fixtures/milestone_1/authority_profiles/scenarios.jsonl \
  --comparisons fixtures/milestone_2a/authority_profiles/comparisons.jsonl \
  --findings "$offline_dir/counterfactual_findings.jsonl" \
  --report "$offline_dir/counterfactual_report.md"

cmp "$offline_dir/counterfactual_findings.jsonl" \
  tests/golden/counterfactual_findings.jsonl
cmp "$offline_dir/counterfactual_report.md" \
  tests/golden/counterfactual_report.md

uv run --offline --frozen python -m tool_choice_contract_trial \
  validate-oracle-candidates \
  --scenarios fixtures/milestone_2b/review_candidate/scenarios.jsonl \
  --expectations fixtures/milestone_2b/review_candidate/oracle_expectations.jsonl \
  --reviews fixtures/milestone_2b/review_candidate/oracle_reviews.jsonl \
  --findings "$offline_dir/oracle_validation_findings.jsonl" \
  --report "$offline_dir/oracle_review_packet.md" \
  --manifest "$offline_dir/provisional_bundle_manifest.json" \
  --invalid-unit-register "$offline_dir/invalid_unit_register.jsonl"

cmp "$offline_dir/oracle_validation_findings.jsonl" \
  tests/golden/milestone_2b/oracle_validation_findings.jsonl
cmp "$offline_dir/oracle_review_packet.md" \
  tests/golden/milestone_2b/oracle_review_packet.md
cmp "$offline_dir/provisional_bundle_manifest.json" \
  tests/golden/milestone_2b/provisional_bundle_manifest.json
cmp "$offline_dir/invalid_unit_register.jsonl" \
  tests/golden/milestone_2b/invalid_unit_register.jsonl
```

## Canonical artifact hashes

For the frozen Milestone 1 replay and representative Milestone 2A comparisons:

| Artifact | SHA-256 |
| --- | --- |
| `tests/golden/results.jsonl` | `9744b7aa3ca2c1b538fbc2e78d918941542396fd00108229d7261ec0a9852d3d` |
| `tests/golden/report.md` | `ae9ef0d081c041edd2f1c3ff2b9714429da4ff5a12cd9036cba2761b664a5fdc` |
| `tests/golden/counterfactual_findings.jsonl` | `66904942d30c3bc413020304c29df76bf99e6c9ce912b31df0cc5a7b8d6c19bb` |
| `tests/golden/counterfactual_report.md` | `e050cf19b4f8e78235bdf6c0f8fce09e43a5dab464f2e06e2ec7e15be196e868` |
| `tests/golden/milestone_2b/oracle_validation_findings.jsonl` | `75a0945eee6f84a32362b0b24d9c261269a70db7a366e6e8c9493eb9adb9ec37` |
| `tests/golden/milestone_2b/oracle_review_packet.md` | `f40f2ebf8e17beb22cde325111341907d88a7ab8238308fd86a2203e11977e29` |
| `tests/golden/milestone_2b/provisional_bundle_manifest.json` | `08131c98e031f37e6daa0bd05099ac1755149f67774768dc45558e33ee0c58ed` |
| `tests/golden/milestone_2b/invalid_unit_register.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The result bundle contains hashes of each scenario, metadata row, oracle row, and decision row. It deliberately contains no timestamps or absolute paths.

## Why the output is stable

- input loaders reject duplicate or mismatched rows;
- Pydantic models normalize sorted tuple fields and reject duplicates;
- records are ordered by opaque scenario ID;
- JSON object keys are sorted with fixed separators;
- every JSONL record has exactly one trailing newline;
- the report renderer reads only the validated result bundle;
- the counterfactual report renderer reads only the validated finding bundle;
- the v2 review packet reads only validated scenarios, proposed expectations, reviews, findings, and the provisional manifest;
- comparison and scenario rows are ordered by opaque IDs, while tool catalogs are compared canonically by tool ID;
- the provisional manifest covers scenario, expectation, review, finding, bundle, and relation-registry hashes;
- persisted findings and manifests are source-verified against scenarios, expectations, reviews, and independently recomputed relations before report rendering;
- volatile run metadata is excluded from canonical artifacts.
