The reviewer is evaluating whether each available tool is admissible under a typed task contract. The packet does not contain intended answers, computed results, policy outputs, or prior reviews.

# Tool Choice Contract Trial v2.1 — Blind Independent Review

Review each case independently using only the contract, manifests, and semantics below. Record answers with the provided JSONL response template and use only the blind case and tool aliases shown here.

## Tool admissibility

A tool is admissible only when all applicable conditions hold:

- it declares every required capability;
- at least one authority profile intersects the contract’s accepted authority profiles;
- it accepts every required input profile;
- it produces every required output profile;
- when citations are required, it provides citations;
- its ID is not forbidden;
- when a particular tool ID is required, its ID matches that required ID.

## Contract invalidity

The contract is internally invalid when a non-null required tool ID is also explicitly forbidden.

A required tool ID that is unavailable is not automatically contract-invalid; it ordinarily leaves no available matching tool.

An unavailable forbidden ID is redundant and not automatically contract-invalid.

## Oracle states and decisions

- `UNIQUE_ADMISSIBLE`: exactly one tool is admissible → `SELECT`
- `MULTIPLE_ADMISSIBLE`: two or more tools are admissible → `INDETERMINATE`
- `NO_ADMISSIBLE`: no tool is admissible under a valid contract → `NO_TOOL`
- `CONTRACT_INVALID`: the contract is internally contradictory → `INVALID_CONTRACT`

## Response fields

- `reviewed_oracle_state`: `UNIQUE_ADMISSIBLE`, `MULTIPLE_ADMISSIBLE`, `NO_ADMISSIBLE`, or `CONTRACT_INVALID`
- `reviewed_decision`: `SELECT`, `INDETERMINATE`, `NO_TOOL`, or `INVALID_CONTRACT`
- `confidence`: `HIGH`, `MEDIUM`, or `LOW`
- `semantic_ambiguity`: boolean
- `ecological_validity_concern`: boolean
- `review_notes`: reviewer-supplied text or null

## Blind cases

### `blind_case_01`

```json
{
  "blind_case_id": "blind_case_01",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": false,
    "contract_id": "blind_contract_01",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet in the required evidence format."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 03",
      "produced_output_profiles": [
        "narrative_summary",
        "structured_extracts"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 04",
      "produced_output_profiles": [
        "audit_table",
        "narrative_summary"
      ],
      "provides_citations": false,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_02`

```json
{
  "blind_case_id": "blind_case_02",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_02",
    "forbidden_tool_ids": [
      "candidate_tool_b",
      "candidate_tool_a"
    ],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet using an allowed service."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 06",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 05",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_03`

```json
{
  "blind_case_id": "blind_case_03",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_03",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "structured_json"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet from the supplied source material."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text",
        "structured_json"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 01",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text",
        "tabular_csv"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 02",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_04`

```json
{
  "blind_case_id": "blind_case_04",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_04",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet from the supplied source material."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text",
        "structured_json"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 01",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text",
        "tabular_csv"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 02",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_05`

```json
{
  "blind_case_id": "blind_case_05",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_05",
    "forbidden_tool_ids": [
      "candidate_tool_a"
    ],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet using an allowed service."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 05",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 06",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_06`

```json
{
  "blind_case_id": "blind_case_06",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_06",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "tabular_csv"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet from the supplied source material."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text",
        "structured_json"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 01",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text",
        "tabular_csv"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 02",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_07`

```json
{
  "blind_case_id": "blind_case_07",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_07",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "image_archive"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet from the supplied source material."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text",
        "tabular_csv"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 02",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text",
        "structured_json"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets from declared input formats.",
      "display_name": "Knowledge Service 01",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_08`

```json
{
  "blind_case_id": "blind_case_08",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": false,
    "contract_id": "blind_contract_08",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "audit_table"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet in the required evidence format."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 04",
      "produced_output_profiles": [
        "audit_table",
        "narrative_summary"
      ],
      "provides_citations": false,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 03",
      "produced_output_profiles": [
        "narrative_summary",
        "structured_extracts"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_09`

```json
{
  "blind_case_id": "blind_case_09",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_09",
    "forbidden_tool_ids": [
      "candidate_tool_b"
    ],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": "candidate_tool_b",
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet using an allowed service."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 06",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 05",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_10`

```json
{
  "blind_case_id": "blind_case_10",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": false,
    "contract_id": "blind_contract_10",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "verified_transcript"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet in the required evidence format."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 04",
      "produced_output_profiles": [
        "audit_table",
        "narrative_summary"
      ],
      "provides_citations": false,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 03",
      "produced_output_profiles": [
        "narrative_summary",
        "structured_extracts"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_11`

```json
{
  "blind_case_id": "blind_case_11",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": true,
    "contract_id": "blind_contract_11",
    "forbidden_tool_ids": [
      "candidate_tool_a"
    ],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "narrative_summary"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet using an allowed service."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 06",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets under explicit tool constraints.",
      "display_name": "Knowledge Service 05",
      "produced_output_profiles": [
        "narrative_summary"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```

### `blind_case_12`

```json
{
  "blind_case_id": "blind_case_12",
  "contract": {
    "accepted_authority_profiles": [
      "approved_enterprise"
    ],
    "citations_required": false,
    "contract_id": "blind_contract_12",
    "forbidden_tool_ids": [],
    "required_capabilities": [
      "knowledge_packet_preparation"
    ],
    "required_input_profiles": [
      "plain_text"
    ],
    "required_output_profiles": [
      "structured_extracts"
    ],
    "required_tool_id": null,
    "schema_version": "2.1.0",
    "task_summary": "Prepare an internal knowledge packet in the required evidence format."
  },
  "schema_version": "2.1.0",
  "tools": [
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 04",
      "produced_output_profiles": [
        "audit_table",
        "narrative_summary"
      ],
      "provides_citations": false,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_a"
    },
    {
      "accepted_input_profiles": [
        "plain_text"
      ],
      "authority_profiles": [
        "approved_enterprise"
      ],
      "capabilities": [
        "knowledge_packet_preparation"
      ],
      "description": "Prepares knowledge packets in declared evidence formats.",
      "display_name": "Knowledge Service 03",
      "produced_output_profiles": [
        "narrative_summary",
        "structured_extracts"
      ],
      "provides_citations": true,
      "schema_version": "2.1.0",
      "tool_id": "candidate_tool_b"
    }
  ]
}
```
