import argparse
import json
from pathlib import Path

from cuad_risk.dataset import build_dataset
from cuad_risk.validation import validate_dataset_dir


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cuad-risk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build the silver risk dataset")
    build.add_argument("--train-json", type=Path, required=True)
    build.add_argument("--test-json", type=Path, required=True)
    build.add_argument("--split-map", type=Path, required=True)
    build.add_argument("--rule-cards", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)

    validate = subparsers.add_parser(
        "validate", help="Validate a published silver risk dataset"
    )
    validate.add_argument("--dataset-dir", type=Path, required=True)
    validate.add_argument("--rule-cards", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        build_dataset(
            train_json=args.train_json,
            test_json=args.test_json,
            split_map=args.split_map,
            rule_cards=args.rule_cards,
            output_dir=args.output_dir,
        )
    elif args.command == "validate":
        report = validate_dataset_dir(args.dataset_dir, args.rule_cards)
        print(
            json.dumps(
                {
                    "status": "valid",
                    "contracts": report.contract_count,
                    "category_assessments": report.category_assessment_count,
                    "split_counts": report.split_counts,
                },
                sort_keys=True,
            )
        )
    return 0
