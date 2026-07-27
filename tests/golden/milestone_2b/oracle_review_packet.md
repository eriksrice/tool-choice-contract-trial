# Tool Choice Contract Trial — Milestone 2B Oracle Review Packet

> Status: provisional review candidate. Proposed expectations are deterministically cross-checked but not independently reviewed, adjudicated, or frozen.

## Bundle summary

- Bundle status: `PROVISIONAL_REVIEW_CANDIDATE`
- Scenario count: 12
- Pending-review count: 12
- Evaluation-unit-invalid count: 0
- Computed contract-invalid count: 1
- Relation-registry hash: `6ef1da326d4c58fcb57e4fe676c66ed40f89a3862b74d43a56dc8425fa7e8157`

## Scenario review entries

### `v2_scenario_001` — Structured JSON input required

- Family: Fictional enterprise knowledge packet — input profiles
- Task: Prepare an internal knowledge packet from the supplied source material.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `structured_json`; outputs `narrative_summary`; citations required; forbidden none.
- Available manifests:
  - `v2_tool_001`: inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_001`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_001`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_002` — Tabular CSV input required

- Family: Fictional enterprise knowledge packet — input profiles
- Task: Prepare an internal knowledge packet from the supplied source material.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `tabular_csv`; outputs `narrative_summary`; citations required; forbidden none.
- Available manifests:
  - `v2_tool_001`: inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_002`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_002`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_003` — Unsupported image archive input

- Family: Fictional enterprise knowledge packet — input profiles
- Task: Prepare an internal knowledge packet from the supplied source material.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `image_archive`; outputs `narrative_summary`; citations required; forbidden none.
- Available manifests:
  - `v2_tool_001`: inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_004` — Shared plain-text input

- Family: Fictional enterprise knowledge packet — input profiles
- Task: Prepare an internal knowledge packet from the supplied source material.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations required; forbidden none.
- Available manifests:
  - `v2_tool_001`: inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Computed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_001`, `v2_tool_002`; decision `INDETERMINATE`.
- Proposed expectation: `MULTIPLE_ADMISSIBLE` with `v2_tool_001`, `v2_tool_002`; decision `INDETERMINATE`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `MULTIPLE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_005` — Structured extracts output required

- Family: Fictional enterprise knowledge packet — output and evidence profiles
- Task: Prepare an internal knowledge packet in the required evidence format.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `structured_extracts`; citations not required; forbidden none.
- Available manifests:
  - `v2_tool_003`: inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_003`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_003`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_006` — Audit table output required

- Family: Fictional enterprise knowledge packet — output and evidence profiles
- Task: Prepare an internal knowledge packet in the required evidence format.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `audit_table`; citations not required; forbidden none.
- Available manifests:
  - `v2_tool_003`: inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_004`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_004`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_007` — Unsupported verified transcript output

- Family: Fictional enterprise knowledge packet — output and evidence profiles
- Task: Prepare an internal knowledge packet in the required evidence format.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `verified_transcript`; citations not required; forbidden none.
- Available manifests:
  - `v2_tool_003`: inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_008` — Shared narrative summary output

- Family: Fictional enterprise knowledge packet — output and evidence profiles
- Task: Prepare an internal knowledge packet in the required evidence format.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations not required; forbidden none.
- Available manifests:
  - `v2_tool_003`: inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Computed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_003`, `v2_tool_004`; decision `INDETERMINATE`.
- Proposed expectation: `MULTIPLE_ADMISSIBLE` with `v2_tool_003`, `v2_tool_004`; decision `INDETERMINATE`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `MULTIPLE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_009` — First available tool prohibited

- Family: Fictional enterprise knowledge packet — explicit prohibition
- Task: Prepare an internal knowledge packet using an allowed service.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations required; forbidden `v2_tool_005`.
- Available manifests:
  - `v2_tool_005`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_006`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_006`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_010` — Second available tool prohibited

- Family: Fictional enterprise knowledge packet — explicit prohibition
- Task: Prepare an internal knowledge packet using an allowed service.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations required; forbidden `v2_tool_006`.
- Available manifests:
  - `v2_tool_005`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_005`; decision `SELECT`.
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_005`; decision `SELECT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_011` — All available tools prohibited

- Family: Fictional enterprise knowledge packet — explicit prohibition
- Task: Prepare an internal knowledge packet using an allowed service.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations required; forbidden `v2_tool_005`, `v2_tool_006`.
- Available manifests:
  - `v2_tool_005`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

### `v2_scenario_012` — Unavailable forbidden tool reference

- Family: Fictional enterprise knowledge packet — explicit prohibition
- Task: Prepare an internal knowledge packet using an allowed service.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations required; forbidden `v2_tool_099`.
- Available manifests:
  - `v2_tool_005`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Computed relation: `CONTRACT_INVALID` with none; decision `INVALID_CONTRACT`.
- Proposed expectation: `CONTRACT_INVALID` with none; decision `INVALID_CONTRACT`.
- Proposal matches computed relation: yes
- Review: `PENDING`; readiness `PENDING_REVIEW`.
- Classification: computed contract state `CONTRACT_INVALID`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: no
- Ready for freeze: no

## Human review instructions

Review the proposed state, admissible set, and rationale without policy outputs. Record agreement or disagreement in the separate review artifact; disagreements require adjudication before an evaluation unit can become coherent.

## Interpretation boundary

- These twelve cases are proposed review candidates, not a frozen benchmark.
- A computed `CONTRACT_INVALID` state comes only from the policy-visible contract; `EVALUATION_UNIT_INVALID` identifies defective authoring or review relationships.
- No policy decisions, live models, tool execution, runtime outputs, or policy metrics are used here.
- The controlled v2 pairs have not been processed by the v1 authority-only counterfactual analyzer.
- No benchmark-performance, production, or cross-domain claim follows.
