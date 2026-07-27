from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FROZEN_MILESTONE_1_HASHES = {
    "fixtures/milestone_1/authority_profiles/evaluation_metadata.jsonl": (
        "72a4a4d2666955e1a73616b5023e7d11e1b7ab88d4a30f9ec1888322bd5890b8"
    ),
    "fixtures/milestone_1/authority_profiles/oracles.jsonl": (
        "e0d28001249384dff0653836d6efebf2b361b8dbbbaafd7eff64642e9cdb1741"
    ),
    "fixtures/milestone_1/authority_profiles/replay_decisions.jsonl": (
        "4ae5de0b544247cd718b600359135d4db7d7ab4d6317db5528e1e2cbdddc7bbc"
    ),
    "fixtures/milestone_1/authority_profiles/scenarios.jsonl": (
        "cad7acb0dc2cecf0c8812084df45063ed20a051434fac601ec091e73abdc9f53"
    ),
    "schemas/v1/clause_witness.schema.json": (
        "3d681c841b6bc312063cb42f272ac9cc0433bea2d88610d70e59986243ca038b"
    ),
    "schemas/v1/cross_evaluation_finding.schema.json": (
        "527912fd85be75865e0730956216a746f8aa405b14c5453d91a83be56af9ed22"
    ),
    "schemas/v1/evaluation_context.schema.json": (
        "47112205f28054a1d4e919f6146b6ed38af19488bc60f92602b0a9fd289be3b5"
    ),
    "schemas/v1/evaluation_result.schema.json": (
        "fbbd881de3829e6501db0d67c5cbca1781eccfb2aa47b3d72a593c264004c197"
    ),
    "schemas/v1/oracle_record.schema.json": (
        "4ed3a1009627144b73acb61c02c03b757e58a4f2f8929d58ad499e472ee0f789"
    ),
    "schemas/v1/policy_view.schema.json": (
        "322ded2ecfa1c42e68e74bf5069f09651a0b807c5ea0ea906d8524eedd535581"
    ),
    "schemas/v1/scenario_metadata.schema.json": (
        "3b319f606625d046a6c618a3373c041011e3e0b691d51bb456b21227c40facf7"
    ),
    "schemas/v1/task_contract.schema.json": (
        "f15475edfd460bca9f1d06b768cba82c7afee7829446488a15144ee38b089d25"
    ),
    "schemas/v1/tool_decision.schema.json": (
        "b9a00fbe8fb6511eb4e4810d49be611a4ca935a6e19dac058f3fb7584b8ab291"
    ),
    "schemas/v1/tool_manifest.schema.json": (
        "62ec63ad49a8cb19f171ba2835e45941666daf4565d9e601aef3fe4a61174898"
    ),
    "tests/golden/report.md": ("ae9ef0d081c041edd2f1c3ff2b9714429da4ff5a12cd9036cba2761b664a5fdc"),
    "tests/golden/results.jsonl": (
        "9744b7aa3ca2c1b538fbc2e78d918941542396fd00108229d7261ec0a9852d3d"
    ),
}


def test_frozen_milestone_1_artifact_hashes_are_preserved() -> None:
    actual = {
        relative_path: hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        for relative_path in FROZEN_MILESTONE_1_HASHES
    }
    assert actual == FROZEN_MILESTONE_1_HASHES
