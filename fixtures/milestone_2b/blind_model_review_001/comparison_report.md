# Tool Choice Contract Trial — Blind Independent Model Review

> Evidence kind: `BLIND_INDEPENDENT_MODEL_REVIEW`. This is a blinded independent model review, not independent human review, owner review, adjudication, benchmark freeze, or policy evaluation.

> Owner review: 12/12 agreement. Blind independent model review: 12/12 full agreement. The candidate remains provisional and unfrozen.

## Provenance

- Review protocol: `blind_model_review_001`
- Source commit: `c11741b5e628354ed0fdcae46e1e8c7908fe109a`
- Blind packet SHA-256: `a3a10982ada95885b8d74b55e4b9c36ee51282161cd831614a46fa54d3275ab7`
- Private map SHA-256: `afe4b4dccdbc050c0283a29593c2b3bdfe4602c11b31f3d408a68d933ab0a8a3`
- Raw response SHA-256: `668b643ea126c746ed0f35d1f3859992e4a1c11ec0df24a74f2c121411f33da1`
- Reviewer input: shuffled policy-visible cases with per-case aliased tool IDs.
- Withheld from reviewer: `computed_findings`, `expectations`, `manifests`, `owner_reviews`, `policy_outputs`, `repository_history`.
- Responses: one JSONL record per blind case.
- Independent human review performed: no
- Policy decisions used: no

## Agreement summary

- Reviewed cases: 12
- `FULL_AGREEMENT`: 12
- `DISAGREEMENT`: 0
- `INVALID_REVIEW_ARTIFACT`: 0
- State disagreements: 0
- Admissible-set disagreements: 0
- Decision disagreements: 0
- High confidence: 12
- Semantic ambiguity flags: 0
- Ecological-validity flags: 12

## Case comparisons

| Scenario | Owner state / set | Blind-model state / set | Computed state / set | Decision agreement | Confidence | Ambiguity | Ecological concern | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `v2_scenario_001` | `UNIQUE_ADMISSIBLE` / `v2_tool_001` | `UNIQUE_ADMISSIBLE` / `v2_tool_001` | `UNIQUE_ADMISSIBLE` / `v2_tool_001` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_002` | `UNIQUE_ADMISSIBLE` / `v2_tool_002` | `UNIQUE_ADMISSIBLE` / `v2_tool_002` | `UNIQUE_ADMISSIBLE` / `v2_tool_002` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_003` | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_004` | `MULTIPLE_ADMISSIBLE` / `v2_tool_001`, `v2_tool_002` | `MULTIPLE_ADMISSIBLE` / `v2_tool_001`, `v2_tool_002` | `MULTIPLE_ADMISSIBLE` / `v2_tool_001`, `v2_tool_002` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_005` | `UNIQUE_ADMISSIBLE` / `v2_tool_003` | `UNIQUE_ADMISSIBLE` / `v2_tool_003` | `UNIQUE_ADMISSIBLE` / `v2_tool_003` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_006` | `UNIQUE_ADMISSIBLE` / `v2_tool_004` | `UNIQUE_ADMISSIBLE` / `v2_tool_004` | `UNIQUE_ADMISSIBLE` / `v2_tool_004` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_007` | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_008` | `MULTIPLE_ADMISSIBLE` / `v2_tool_003`, `v2_tool_004` | `MULTIPLE_ADMISSIBLE` / `v2_tool_003`, `v2_tool_004` | `MULTIPLE_ADMISSIBLE` / `v2_tool_003`, `v2_tool_004` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_009` | `UNIQUE_ADMISSIBLE` / `v2_tool_006` | `UNIQUE_ADMISSIBLE` / `v2_tool_006` | `UNIQUE_ADMISSIBLE` / `v2_tool_006` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_010` | `UNIQUE_ADMISSIBLE` / `v2_tool_005` | `UNIQUE_ADMISSIBLE` / `v2_tool_005` | `UNIQUE_ADMISSIBLE` / `v2_tool_005` | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_011` | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | `NO_ADMISSIBLE` / none | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |
| `v2_scenario_012` | `CONTRACT_INVALID` / none | `CONTRACT_INVALID` / none | `CONTRACT_INVALID` / none | yes | `HIGH` | no | yes | `FULL_AGREEMENT` |

## Ecological-validity interpretation

### Bundle-level concern

11 cases note the general limitation that synthetic, self-declared manifests are not runtime-verified. This is one bundle-level declared-manifest realism limitation, not 11 distinct scenario defects.

### Scenario-level concerns

- `v2_scenario_007`: The `verified_transcript` requirement is somewhat artificial for the stated knowledge-packet task. Reviewer note: Both tools meet the capability, authority, and plain-text input requirements, but neither produces verified_transcript; citations are optional and no ID restriction applies. Realism is limited by abstract, self-declared manifest profiles.
- `v2_scenario_012`: The deliberately contradictory required-and-forbidden contract is diagnostically useful but intentionally artificial. Reviewer note: The contract simultaneously requires and forbids v2_tool_005, which the packet explicitly defines as contract invalidity; the conflict is resolved by that rule rather than left semantically ambiguous. The deliberately contradictory contract raises a realism concern.

Ecological-validity flags do not change oracle agreement, evaluation-unit status, or row-level readiness.

## Interpretation boundary

- The owner-review artifacts remain separate and unchanged.
- Independent human review has not been performed.
- Row-level agreement does not freeze the provisional candidate.
- No policy decisions, policy metrics, live models, or tool execution are included.
- No benchmark-validity, production, or cross-domain claim follows.
