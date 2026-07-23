from __future__ import annotations

from pathlib import Path

import pytest

from tool_choice_contract_trial.evaluation_io import load_scenario_metadata
from tool_choice_contract_trial.models import (
    OracleRecord,
    PolicyView,
    ScenarioMetadata,
    ToolDecision,
)
from tool_choice_contract_trial.oracle_io import load_oracle_records
from tool_choice_contract_trial.policy_io import load_policy_views, load_replay_decisions

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRECTORY = ROOT / "fixtures" / "milestone_1" / "authority_profiles"


@pytest.fixture
def policy_views() -> dict[str, PolicyView]:
    return {
        view.scenario_id: view for view in load_policy_views(FIXTURE_DIRECTORY / "scenarios.jsonl")
    }


@pytest.fixture
def oracle_records() -> dict[str, OracleRecord]:
    return {
        oracle.scenario_id: oracle
        for oracle in load_oracle_records(FIXTURE_DIRECTORY / "oracles.jsonl")
    }


@pytest.fixture
def scenario_metadata() -> dict[str, ScenarioMetadata]:
    return {
        metadata.scenario_id: metadata
        for metadata in load_scenario_metadata(FIXTURE_DIRECTORY / "evaluation_metadata.jsonl")
    }


@pytest.fixture
def replay_decisions() -> dict[str, ToolDecision]:
    return {
        decision.scenario_id: decision
        for decision in load_replay_decisions(FIXTURE_DIRECTORY / "replay_decisions.jsonl")
    }
