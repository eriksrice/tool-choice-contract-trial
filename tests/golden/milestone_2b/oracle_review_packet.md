# Tool Choice Contract Trial — Milestone 2B Oracle Review Packet

> Owner review: complete for all 12 cases; 11 proposals accepted and 1 disputed. 1 dispute remains unadjudicated.

> Independent review has not been performed. The bundle is not frozen, and no policy decisions were used.

## Bundle summary

- Bundle status: `PROVISIONAL_REVIEW_CANDIDATE`
- Scenario count: 12
- Pending-review count: 0
- Evaluation-unit-invalid count: 1
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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_001`.
- Review performed without policy outputs: yes
- Review note: Only v2_tool_001 accepts the required structured_json input profile; the other declared requirements are held constant and satisfied.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_002`.
- Review performed without policy outputs: yes
- Review note: Only v2_tool_002 accepts the required tabular_csv input profile; the other declared requirements are held constant and satisfied.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `NO_ADMISSIBLE` with none.
- Review performed without policy outputs: yes
- Review note: Neither available tool accepts the required image_archive input profile, so NO_TOOL is the contract-faithful response.
- Adjudication: none.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_001`, `v2_tool_002`.
- Review performed without policy outputs: yes
- Review note: Both available tools accept plain_text and satisfy the remaining requirements; without a typed tie-break, INDETERMINATE is the contract-faithful response.
- Adjudication: none.
- Classification: computed contract state `MULTIPLE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_003`.
- Review performed without policy outputs: yes
- Review note: Only v2_tool_003 produces the required structured_extracts output profile; citations are not required and do not affect admissibility.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_004`.
- Review performed without policy outputs: yes
- Review note: Only v2_tool_004 produces the required audit_table output profile; citations are not required and do not affect admissibility.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `NO_ADMISSIBLE` with none.
- Review performed without policy outputs: yes
- Review note: Neither available tool produces the required verified_transcript output profile. The relation is logically correct, although this output profile is somewhat artificial for the stated knowledge-packet task and should be reconsidered before a claim-grade freeze.
- Adjudication: none.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_003`, `v2_tool_004`.
- Review performed without policy outputs: yes
- Review note: Both tools produce narrative_summary and satisfy the remaining requirements; without a typed tie-break, INDETERMINATE is the contract-faithful response.
- Adjudication: none.
- Classification: computed contract state `MULTIPLE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_006`.
- Review performed without policy outputs: yes
- Review note: Both tools otherwise satisfy the contract, but v2_tool_005 is explicitly prohibited, leaving v2_tool_006 uniquely admissible.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `UNIQUE_ADMISSIBLE` with `v2_tool_005`.
- Review performed without policy outputs: yes
- Review note: Both tools otherwise satisfy the contract, but v2_tool_006 is explicitly prohibited, leaving v2_tool_005 uniquely admissible.
- Adjudication: none.
- Classification: computed contract state `UNIQUE_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `AGREE`; readiness `REVIEW_COMPLETE`.
- Reviewed relation: `NO_ADMISSIBLE` with none.
- Review performed without policy outputs: yes
- Review note: Both otherwise compatible available tools are explicitly prohibited, so no available tool is admissible.
- Adjudication: none.
- Classification: computed contract state `NO_ADMISSIBLE`; evaluation-unit status `SCOREABLE`.
- Invalid-unit reasons: none
- Ready for scoring: yes
- Ready for freeze: yes

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
- Reviewer role: `owner_reviewer`
- Review: `DISAGREE`; readiness `ADJUDICATION_REQUIRED`.
- Reviewed relation: `MULTIPLE_ADMISSIBLE` with `v2_tool_005`, `v2_tool_006`.
- Review performed without policy outputs: yes
- Review note: An unavailable ID in a prohibition list is not inherently contract-invalid. Unless forbidden_tool_ids is explicitly defined as a scenario-local subset of the currently available tool IDs, the prohibition of v2_tool_099 is redundant and both available tools remain admissible. The scenario or ontology rule requires revision before approval.
- Adjudication: none.
- Classification: computed contract state `CONTRACT_INVALID`; evaluation-unit status `EVALUATION_UNIT_INVALID`.
- Invalid-unit reasons: `completed disagreement lacks adjudication`
- Ready for scoring: no
- Ready for freeze: no

## Human review instructions

Independent review remains outstanding. It should assess the proposed state, admissible set, and rationale without policy outputs and must remain distinct from the recorded owner review. The unresolved disagreement requires adjudication before that evaluation unit can become coherent.

## Interpretation boundary

- These twelve cases are proposed review candidates, not a frozen benchmark.
- A computed `CONTRACT_INVALID` state comes only from the policy-visible contract; `EVALUATION_UNIT_INVALID` identifies defective authoring or review relationships.
- No policy decisions, live models, tool execution, runtime outputs, or policy metrics are used here.
- The controlled v2 pairs have not been processed by the v1 authority-only counterfactual analyzer.
- No benchmark-performance, production, or cross-domain claim follows.
