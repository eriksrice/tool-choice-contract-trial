# Tool Choice Contract Trial — Milestone 2B Oracle Review Packet

> Status: provisional review candidate. Proposed expectations are deterministically cross-checked but not independently reviewed, adjudicated, or frozen.

> Review state: all 12 checked-in reviews are pending. No independently reviewed oracle truth or frozen benchmark is claimed, and no policy decisions are used.

## Bundle summary

- Bundle status: `PROVISIONAL_REVIEW_CANDIDATE`
- Scenario count: 12
- Pending-review count: 12
- Evaluation-unit-invalid count: 0
- Computed contract-invalid count: 1
- Relation-registry hash: `f761822f7fec61ecb68cdcfaae419800a1523fb91022b0dd23e31e8533023d3a`

## Scenario review entries

### `v2_scenario_001` — Structured JSON input required

- Family: Fictional enterprise knowledge packet — input profiles
- Task: Prepare an internal knowledge packet from the supplied source material.
- Requirements: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `structured_json`; outputs `narrative_summary`; citations required; forbidden none.
- Available manifests:
  - `v2_tool_001`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_002` / `input.requirement` (`F_INPUT_CONTRACT_MISMATCH`): expected `structured_json`; actual `plain_text`, `tabular_csv`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_001`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_001`; decision `SELECT`.
- Authoring rationale: Only v2_tool_001 declares the required structured_json input profile.
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
  - `v2_tool_001`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_001` / `input.requirement` (`F_INPUT_CONTRACT_MISMATCH`): expected `tabular_csv`; actual `plain_text`, `structured_json`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_002`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_002`; decision `SELECT`.
- Authoring rationale: Only v2_tool_002 declares the required tabular_csv input profile.
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
  - `v2_tool_001`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_001` / `input.requirement` (`F_INPUT_CONTRACT_MISMATCH`): expected `image_archive`; actual `plain_text`, `structured_json`.
  - `v2_tool_002` / `input.requirement` (`F_INPUT_CONTRACT_MISMATCH`): expected `image_archive`; actual `plain_text`, `tabular_csv`.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Contract-invalid reasons: none
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Authoring rationale: No available manifest declares the image_archive input profile.
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
  - `v2_tool_001`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `structured_json`; outputs `narrative_summary`; citations yes.
  - `v2_tool_002`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`, `tabular_csv`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - none
- Computed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_001`, `v2_tool_002`; decision `INDETERMINATE`.
- Contract-invalid reasons: none
- Proposed expectation: `MULTIPLE_ADMISSIBLE` with `v2_tool_001`, `v2_tool_002`; decision `INDETERMINATE`.
- Authoring rationale: Both available manifests declare the shared plain_text input profile.
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
  - `v2_tool_003`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Relation witnesses:
  - `v2_tool_004` / `output.requirement` (`F_OUTPUT_CONTRACT_MISMATCH`): expected `structured_extracts`; actual `audit_table`, `narrative_summary`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_003`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_003`; decision `SELECT`.
- Authoring rationale: Only v2_tool_003 declares the required structured_extracts output profile.
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
  - `v2_tool_003`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Relation witnesses:
  - `v2_tool_003` / `output.requirement` (`F_OUTPUT_CONTRACT_MISMATCH`): expected `audit_table`; actual `narrative_summary`, `structured_extracts`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_004`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_004`; decision `SELECT`.
- Authoring rationale: Only v2_tool_004 declares the required audit_table output profile.
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
  - `v2_tool_003`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Relation witnesses:
  - `v2_tool_003` / `output.requirement` (`F_OUTPUT_CONTRACT_MISMATCH`): expected `verified_transcript`; actual `narrative_summary`, `structured_extracts`.
  - `v2_tool_004` / `output.requirement` (`F_OUTPUT_CONTRACT_MISMATCH`): expected `verified_transcript`; actual `audit_table`, `narrative_summary`.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Contract-invalid reasons: none
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Authoring rationale: No available manifest declares the verified_transcript output profile.
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
  - `v2_tool_003`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`, `structured_extracts`; citations yes.
  - `v2_tool_004`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `audit_table`, `narrative_summary`; citations no.
- Relation witnesses:
  - none
- Computed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_003`, `v2_tool_004`; decision `INDETERMINATE`.
- Contract-invalid reasons: none
- Proposed expectation: `MULTIPLE_ADMISSIBLE` with `v2_tool_003`, `v2_tool_004`; decision `INDETERMINATE`.
- Authoring rationale: Both available manifests declare the shared narrative_summary output profile.
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
  - `v2_tool_005`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_005` / `tool.prohibition` (`F_EXPLICIT_PROHIBITION`): expected `tool_not_forbidden`; actual `v2_tool_005`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_006`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_006`; decision `SELECT`.
- Authoring rationale: v2_tool_005 is explicitly forbidden, leaving v2_tool_006 as the unique admissible tool.
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
  - `v2_tool_005`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_006` / `tool.prohibition` (`F_EXPLICIT_PROHIBITION`): expected `tool_not_forbidden`; actual `v2_tool_006`.
- Computed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_005`; decision `SELECT`.
- Contract-invalid reasons: none
- Proposed expectation: `UNIQUE_ADMISSIBLE` with `v2_tool_005`; decision `SELECT`.
- Authoring rationale: v2_tool_006 is explicitly forbidden, leaving v2_tool_005 as the unique admissible tool.
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
  - `v2_tool_005`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - `v2_tool_005` / `tool.prohibition` (`F_EXPLICIT_PROHIBITION`): expected `tool_not_forbidden`; actual `v2_tool_005`.
  - `v2_tool_006` / `tool.prohibition` (`F_EXPLICIT_PROHIBITION`): expected `tool_not_forbidden`; actual `v2_tool_006`.
- Computed relation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Contract-invalid reasons: none
- Proposed expectation: `NO_ADMISSIBLE` with none; decision `NO_TOOL`.
- Authoring rationale: Both otherwise compatible available tools are explicitly forbidden.
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
  - `v2_tool_005`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
  - `v2_tool_006`: capabilities `knowledge_packet_preparation`; authority `approved_enterprise`; inputs `plain_text`; outputs `narrative_summary`; citations yes.
- Relation witnesses:
  - none
- Computed relation: `CONTRACT_INVALID` with none; decision `INVALID_CONTRACT`.
- Contract-invalid reasons: `forbidden tool ID is unavailable: v2_tool_099`
- Proposed expectation: `CONTRACT_INVALID` with none; decision `INVALID_CONTRACT`.
- Authoring rationale: The contract forbids an unavailable opaque tool ID and is intentionally contract-invalid.
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
