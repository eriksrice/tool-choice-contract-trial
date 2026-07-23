# Tool Choice Contract Trial — Milestone 1 Results

> Scope: one synthetic scenario family demonstrates deterministic evaluation mechanics only; it does not validate the benchmark thesis.

## Experiment

- Family: Fictional enterprise evidence retrieval
- Common synthetic task: Retrieve cited evidence for the fictional Meridian documentation review.
- Contract condition under test: accepted evidence authority profile or set.
- Common required capability: `evidence_retrieval`
- Citations required: true
- Policy source: one trusted, schema-valid stored replay bundle.

## Outcome counts

- Cases: 4
- Scoreable: 4
- Invalid evaluation units: 0
- CORRECT: 2
- INCORRECT: 1
- ADMISSIBLE_BUT_UNJUSTIFIED: 1
- NOT_SCORED: 0

## Case evidence

| Variant | Accepted authority | Computed admissible tools | Replayed decision | Selected-tool admissibility | Strict outcome | Decisive clause | Primary failure |
|---|---|---|---|---|---|---|---|
| Public-primary evidence required | `public_primary` | `evidence_tool_01` | SELECT `evidence_tool_02` | INADMISSIBLE | INCORRECT | `authority.requirement` | F_AUTHORITY_MISMATCH |
| Approved-internal evidence required | `approved_internal` | `evidence_tool_02` | SELECT `evidence_tool_02` | ADMISSIBLE | CORRECT | `authority.requirement` | — |
| Unsupported authority required | `independent_certified` | none | NO_TOOL | NOT_APPLICABLE | CORRECT | `authority.requirement` | — |
| Public-primary or approved-internal evidence accepted | `approved_internal`, `public_primary` | `evidence_tool_01`, `evidence_tool_02` | SELECT `evidence_tool_01` | ADMISSIBLE | ADMISSIBLE_BUT_UNJUSTIFIED | `authority.requirement` | F_AMBIGUITY_FORCED_RESOLUTION |

## Unique-to-unique minimal-pair flip

- `comparison_001` changes the accepted authority condition and flips the unique admissible tool: Public-primary evidence required: `public_primary` → `evidence_tool_01`; Approved-internal evidence required: `approved_internal` → `evidence_tool_02`.

## Clause-level diagnostics

### Public-primary evidence required

- Clause: `authority.requirement`
- Failure: `F_AUTHORITY_MISMATCH`
- Diagnostic scope: `SELECTED_TOOL`
- Tool: `evidence_tool_02`
- Expected: `public_primary`
- Actual: `approved_internal`

### Public-primary or approved-internal evidence accepted

- Clause: `decision.ambiguity_unresolved`
- Failure: `F_AMBIGUITY_FORCED_RESOLUTION`
- Diagnostic scope: `POLICY_OUTPUT`
- Tool: not applicable
- Expected: `INDETERMINATE`
- Actual: `SELECT`

## Interpretation boundary

- Inadmissible selections: Public-primary evidence required.
- Admissible-but-unjustified selections: Public-primary or approved-internal evidence accepted.
- These categories remain separate: an admissible member chosen without a tie-break is not grouped with an inadmissible selection.
- The harness evaluates declared manifest compatibility and does not execute tools or verify runtime truth.
- This one synthetic family proves mechanics only, not benchmark validity or cross-domain performance.
