import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from cuad_risk.validation import DatasetValidationError, validate_dataset_dir
from cuad_risk.cli import main
from cuad_risk.provenance import generator_fingerprint


CATEGORY_IDS = tuple(f"category_{index}" for index in range(10))


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ValidateDatasetDirectoryTest(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        dataset_dir = root / "dataset"
        dataset_dir.mkdir()
        rule_cards = root / "rules.json"
        rule_cards.write_text(
            json.dumps(
                {
                    "categories": [
                        {"category_id": category_id}
                        for category_id in CATEGORY_IDS
                    ]
                }
            ),
            encoding="utf-8",
        )
        (root / "source_registry.json").write_text(
            json.dumps({"sources": []}), encoding="utf-8"
        )

        fixture_contracts = (
            {
                "contract_id": "train-1",
                "source_contract_id": "contract_0001",
                "source_partition": "train",
                "source_index": 1,
                "split": "train",
                "context_group_id": "context-a",
                "contract_title": "Training contract",
                "contract_type": "unknown",
                "contract_type_confidence": "low",
                "paragraphs": ["Example training contract text."],
            },
            {
                "contract_id": "test-1",
                "source_contract_id": "contract_0001",
                "source_partition": "test",
                "source_index": 1,
                "split": "official_test",
                "context_group_id": "context-b",
                "contract_title": "Test contract",
                "contract_type": "unknown",
                "contract_type_confidence": "low",
                "paragraphs": ["Example test contract text."],
            },
        )
        category_rows = []
        for contract in fixture_contracts:
            contract_text = "\n\n".join(contract["paragraphs"])
            text_hash = hashlib.sha256(contract_text.encode("utf-8")).hexdigest()
            for category_id in CATEGORY_IDS:
                category_rows.append(
                    {
                        "contract_id": contract["contract_id"],
                        "source_contract_id": contract["source_contract_id"],
                        "source_partition": contract["source_partition"],
                        "source_index": contract["source_index"],
                        "context_group_id": contract["context_group_id"],
                        "contract_title": contract["contract_title"],
                        "contract_type": contract["contract_type"],
                        "contract_type_confidence": contract[
                            "contract_type_confidence"
                        ],
                        "contract_text_sha256": text_hash,
                        "split": contract["split"],
                        "category_id": category_id,
                        "assessment_id": (
                            f"{contract['contract_id']}:{category_id}"
                        ),
                        "risk_domain": category_id,
                        "issue_family_id": category_id,
                        "unresolved_material": "False",
                        "severity_ordinal": "1",
                        "risk_band": "low",
                        "label_status": "weak_automatic",
                        "evidence_text": "Example clause text.",
                        "evidence_count": "1",
                        "confidence": "medium",
                    }
                )
        _write_csv(dataset_dir / "category_assessments.csv", category_rows)
        _write_csv(
            dataset_dir / "contract_assessments.csv",
            [
                {
                    "contract_id": "train-1",
                    "rule_contract_risk_band": "low",
                    "rule_contract_review_priority_band": "low",
                    "rule_contract_review_priority_ordinal": "1",
                    "triggering_assessment_ids": json.dumps(
                        [f"train-1:{category_id}" for category_id in CATEGORY_IDS]
                    ),
                },
                {
                    "contract_id": "test-1",
                    "rule_contract_risk_band": "low",
                    "rule_contract_review_priority_band": "low",
                    "rule_contract_review_priority_ordinal": "1",
                    "triggering_assessment_ids": json.dumps(
                        [f"test-1:{category_id}" for category_id in CATEGORY_IDS]
                    ),
                },
            ],
        )
        contracts_path = dataset_dir / "contracts.jsonl"
        with contracts_path.open("w", encoding="utf-8") as handle:
            for contract in fixture_contracts:
                row = dict(contract)
                row["contract_text"] = "\n\n".join(row["paragraphs"])
                row["contract_text_sha256"] = hashlib.sha256(
                    row["contract_text"].encode("utf-8")
                ).hexdigest()
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        (dataset_dir / "clause_findings.jsonl").write_text("", encoding="utf-8")
        (dataset_dir / "risk_training_examples.jsonl").write_text(
            "", encoding="utf-8"
        )
        _write_csv(
            dataset_dir / "category_training_examples.csv",
            [
                {
                    "contract_id": "train-1",
                    "category_id": "category_0",
                    "split": "train",
                    "severity_ordinal": "1",
                    "target_risk_band": "low",
                    "model_input_text": "Example clause text.",
                    "label_confidence": "medium",
                    "exact_text_seen_in_train": "False",
                }
            ],
        )
        _write_csv(
            dataset_dir / "review" / "official_test_reference_template.csv",
            [
                {
                    "contract_id": "test-1",
                    "reviewer_slot": "1",
                    "human_contract_risk_band": "",
                },
                {
                    "contract_id": "test-1",
                    "reviewer_slot": "2",
                    "human_contract_risk_band": "",
                },
            ],
        )
        package_hashes = {
            str(path.relative_to(dataset_dir)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in dataset_dir.rglob("*")
            if path.is_file()
        }
        (dataset_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "category_ids": sorted(CATEGORY_IDS),
                    "generator": generator_fingerprint(),
                    "input_sha256": {
                        "rule_cards": hashlib.sha256(
                            rule_cards.read_bytes()
                        ).hexdigest(),
                        "source_registry": hashlib.sha256(
                            (root / "source_registry.json").read_bytes()
                        ).hexdigest(),
                    },
                    "package_sha256": package_hashes,
                    "counts": {
                        "contracts": 2,
                        "contract_texts": 2,
                        "category_assessments": 20,
                        "clause_findings": 0,
                        "source_answer_spans": 20,
                        "contract_assessments": 2,
                        "risk_training_examples": 0,
                        "category_training_examples": 1,
                        "reference_template_rows": 2,
                    },
                }
            ),
            encoding="utf-8",
        )
        return dataset_dir, rule_cards

    def test_directory_validation_checks_all_published_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))

            report = validate_dataset_dir(dataset_dir, rule_cards)

            self.assertEqual(report.contract_count, 2)
            self.assertEqual(report.category_assessment_count, 20)

    def test_directory_validation_rejects_stale_auxiliary_counts(self) -> None:
        for count_name in (
            "source_answer_spans",
            "contract_assessments",
            "reference_template_rows",
        ):
            with self.subTest(count_name=count_name), tempfile.TemporaryDirectory() as tmp:
                dataset_dir, rule_cards = self._fixture(Path(tmp))
                manifest_path = dataset_dir / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["counts"][count_name] += 1
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                with self.assertRaisesRegex(
                    DatasetValidationError,
                    f"manifest count mismatch for {count_name}",
                ):
                    validate_dataset_dir(dataset_dir, rule_cards)

    def test_directory_validation_requires_complete_package_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))
            manifest_path = dataset_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["package_sha256"].pop("category_assessments.csv")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(
                DatasetValidationError,
                "manifest package file inventory mismatch",
            ):
                validate_dataset_dir(dataset_dir, rule_cards)

    def test_directory_validation_rejects_unlisted_package_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))
            (dataset_dir / "unexpected.txt").write_text(
                "not part of the release", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                DatasetValidationError,
                "manifest package file inventory mismatch",
            ):
                validate_dataset_dir(dataset_dir, rule_cards)

    def test_validate_cli_returns_success_for_a_valid_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))

            exit_code = main(
                [
                    "validate",
                    "--dataset-dir",
                    str(dataset_dir),
                    "--rule-cards",
                    str(rule_cards),
                ]
            )

            self.assertEqual(exit_code, 0)

    def test_directory_validation_rejects_wrong_contract_table_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))
            _write_csv(
                dataset_dir / "contract_assessments.csv",
                [{"contract_id": "train-1", "rule_contract_risk_band": "low"}],
            )

            with self.assertRaisesRegex(
                DatasetValidationError, "contract assessment count"
            ):
                validate_dataset_dir(dataset_dir, rule_cards)

    def test_directory_validation_rejects_stale_contract_rollup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))
            _write_csv(
                dataset_dir / "contract_assessments.csv",
                [
                    {
                        "contract_id": "train-1",
                        "rule_contract_risk_band": "medium",
                        "rule_contract_review_priority_band": "medium",
                        "rule_contract_review_priority_ordinal": "2",
                    },
                    {
                        "contract_id": "test-1",
                        "rule_contract_risk_band": "low",
                        "rule_contract_review_priority_band": "low",
                        "rule_contract_review_priority_ordinal": "1",
                    },
                ],
            )

            with self.assertRaisesRegex(
                DatasetValidationError, "contract rollup mismatch"
            ):
                validate_dataset_dir(dataset_dir, rule_cards)

    def test_directory_validation_enforces_configured_release_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir, rule_cards = self._fixture(Path(tmp))
            config = json.loads(rule_cards.read_text(encoding="utf-8"))
            config["release_invariants"] = {
                "contracts": 3,
                "category_assessments": 30,
                "contracts_by_split": {
                    "train": 1,
                    "validation": 1,
                    "official_test": 1,
                },
            }
            rule_cards.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(
                DatasetValidationError, "release contract count mismatch"
            ):
                validate_dataset_dir(dataset_dir, rule_cards)


if __name__ == "__main__":
    unittest.main()
