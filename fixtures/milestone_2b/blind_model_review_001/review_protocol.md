# Blind Independent Model Review Protocol

## Evidence kind

`BLIND_INDEPENDENT_MODEL_REVIEW`

## Session provenance

- Reviewer platform: `ChatGPT`
- Session type: `Temporary Chat`
- Exact model identifier: `NOT_RECORDED`
- Human reviewer: `false`
- Web browsing requested: `false`
- Repository access provided: `false`
- Owner-review evidence provided: `false`
- Computed evidence provided: `false`
- Private mapping provided: `false`

No reviewer name or model name or version is inferred beyond this recorded provenance.

## Packet identity-check prompt

The following exact prompt was used before review:

```text
Do not evaluate or solve any cases yet.

Confirm that you can read the attached packet by returning exactly these five fields and nothing else:

schema_version:
blind_case_01_required_output_and_citations:
blind_case_02_forbidden_tool_ids:
blind_case_09_required_and_forbidden_tool_ids:
blind_case_12_required_output:

Copy the values directly from the attachment. Do not infer them from prior conversations or memory.
```

The identity check returned the equivalent of:

```text
schema_version: 2.1.0
blind_case_01_required_output_and_citations: narrative_summary; false
blind_case_02_forbidden_tool_ids: candidate_tool_b, candidate_tool_a
blind_case_09_required_and_forbidden_tool_ids: required candidate_tool_b; forbidden candidate_tool_b
blind_case_12_required_output: structured_extracts
```

This established packet availability and identity before review.

## Exact review prompt

The following complete prompt was used:

```text
Now perform the blind independent review using only the attached packet.

Do not use saved memory, previous chats, account history, external files, web browsing, or prior knowledge of this project. Do not infer an intended answer from recurring case structure.

For every blind case:

1. Evaluate every available tool against every contract requirement.
2. Determine the complete admissible tool set.
3. Select exactly one oracle state:
   - UNIQUE_ADMISSIBLE
   - MULTIPLE_ADMISSIBLE
   - NO_ADMISSIBLE
   - CONTRACT_INVALID
4. Select the corresponding decision:
   - SELECT
   - INDETERMINATE
   - NO_TOOL
   - INVALID_CONTRACT
5. Explain the decisive reasoning briefly.
6. Mark whether the case has semantic ambiguity.
7. Mark whether the case has an ecological-validity or realism concern.
8. Give HIGH, MEDIUM, or LOW confidence.

Do not accept the supplied ontology uncritically. Flag cases where rules conflict, are underspecified, or permit a reasonable competing interpretation.

Return exactly one JSON object per line, in the packet’s order:

{"blind_case_id":"blind_case_01","reviewed_oracle_state":"UNIQUE_ADMISSIBLE","reviewed_admissible_tool_ids":["candidate_tool_a"],"reviewed_decision":"SELECT","confidence":"HIGH","semantic_ambiguity":false,"ecological_validity_concern":false,"review_notes":"Brief decisive reasoning."}

Return JSONL only. Do not add an introduction, conclusion, Markdown fence, aggregate score, or mapping to original cases.
```
