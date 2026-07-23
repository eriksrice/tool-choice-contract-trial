"""Single argparse CLI for the authorized deterministic Milestone 1 path."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .evaluation import evaluate_case
from .evaluation_io import load_scenario_metadata
from .oracle_io import load_oracle_records
from .policy import ReplayPolicyAdapter
from .policy_io import load_policy_views, load_replay_decisions
from .reporting import load_result_bundle, write_markdown_report
from .schema import check_schema_drift, generate_schemas
from .serialization import write_jsonl


def _path(value: str) -> Path:
    return Path(value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool-choice-contract-trial")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate-schemas")
    generate.add_argument("--output", type=_path, required=True)

    check = subparsers.add_parser("check-schemas")
    check.add_argument("--directory", type=_path, required=True)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--scenarios", type=_path, required=True)
    evaluate.add_argument("--metadata", type=_path, required=True)
    evaluate.add_argument("--oracles", type=_path, required=True)
    evaluate.add_argument("--decisions", type=_path, required=True)
    evaluate.add_argument("--results", type=_path, required=True)
    evaluate.add_argument("--report", type=_path, required=True)

    render = subparsers.add_parser("render-report")
    render.add_argument("--results", type=_path, required=True)
    render.add_argument("--report", type=_path, required=True)
    return parser


def _require_same_scenarios(
    policy_scenarios: set[str], named_scenarios: set[str], artifact_name: str
) -> None:
    if policy_scenarios != named_scenarios:
        missing = sorted(policy_scenarios - named_scenarios)
        extra = sorted(named_scenarios - policy_scenarios)
        raise ValueError(f"{artifact_name} scenario set mismatch; missing={missing}, extra={extra}")


def _evaluate(args: argparse.Namespace) -> None:
    policy_views = load_policy_views(args.scenarios)
    metadata_records = load_scenario_metadata(args.metadata)
    oracles = load_oracle_records(args.oracles)
    decisions = load_replay_decisions(args.decisions)
    policy_scenarios = {view.scenario_id for view in policy_views}
    if len(policy_scenarios) != len(policy_views):
        raise ValueError("policy views must have unique scenario_id values")
    _require_same_scenarios(
        policy_scenarios,
        {metadata.scenario_id for metadata in metadata_records},
        "scenario metadata",
    )
    _require_same_scenarios(
        policy_scenarios,
        {oracle.scenario_id for oracle in oracles},
        "oracle",
    )
    _require_same_scenarios(
        policy_scenarios,
        {decision.scenario_id for decision in decisions},
        "decision",
    )
    metadata_by_scenario = {metadata.scenario_id: metadata for metadata in metadata_records}
    oracle_by_scenario = {oracle.scenario_id: oracle for oracle in oracles}
    adapter = ReplayPolicyAdapter(decisions)
    results = tuple(
        evaluate_case(
            view,
            metadata_by_scenario[view.scenario_id],
            oracle_by_scenario[view.scenario_id],
            adapter.decide(view),
        )
        for view in sorted(policy_views, key=lambda item: item.scenario_id)
    )
    write_jsonl(args.results, results)
    write_markdown_report(args.report, results)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "generate-schemas":
        generate_schemas(args.output)
    elif args.command == "check-schemas":
        check_schema_drift(args.directory)
    elif args.command == "evaluate":
        _evaluate(args)
    elif args.command == "render-report":
        write_markdown_report(args.report, load_result_bundle(args.results))
    return 0
