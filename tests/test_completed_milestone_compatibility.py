from __future__ import annotations

import hashlib
from pathlib import Path

from tool_choice_contract_trial.counterfactual_registry import ACTIVE_CLAUSE_OWNERSHIP_HASH

ROOT = Path(__file__).resolve().parents[1]

FROZEN_COMPLETED_MILESTONE_HASHES = {
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
    "fixtures/milestone_2a/authority_profiles/comparisons.jsonl": (
        "999468b7ba4fdc5a24b470979330acd58f18e684ca907b97e731bfd50d6bad6e"
    ),
    "schemas/v1/clause_witness.schema.json": (
        "3d681c841b6bc312063cb42f272ac9cc0433bea2d88610d70e59986243ca038b"
    ),
    "schemas/v1/counterfactual_comparison_spec.schema.json": (
        "73d1a77ba3d1b59edcc622a9235a755d620b63fcf8628055a66275cbafd2e137"
    ),
    "schemas/v1/counterfactual_finding.schema.json": (
        "63c0fdcd52d5cae659793c200ad3982e776033d4c1569be074df4ee7349edf5f"
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
    "tests/golden/results.jsonl": (
        "9744b7aa3ca2c1b538fbc2e78d918941542396fd00108229d7261ec0a9852d3d"
    ),
    "tests/golden/report.md": ("ae9ef0d081c041edd2f1c3ff2b9714429da4ff5a12cd9036cba2761b664a5fdc"),
    "tests/golden/counterfactual_findings.jsonl": (
        "66904942d30c3bc413020304c29df76bf99e6c9ce912b31df0cc5a7b8d6c19bb"
    ),
    "tests/golden/counterfactual_report.md": (
        "e050cf19b4f8e78235bdf6c0f8fce09e43a5dab464f2e06e2ec7e15be196e868"
    ),
}


def test_completed_milestone_artifacts_remain_byte_frozen() -> None:
    actual = {
        relative_path: hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        for relative_path in FROZEN_COMPLETED_MILESTONE_HASHES
    }
    assert actual == FROZEN_COMPLETED_MILESTONE_HASHES


def test_v1_counterfactual_registry_hash_remains_frozen() -> None:
    assert (
        ACTIVE_CLAUSE_OWNERSHIP_HASH
        == "571ac41f681570ea13ae3dd90df4035816e010687e804e352216a57371b3321d"
    )
