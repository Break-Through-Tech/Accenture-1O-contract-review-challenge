import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cuad_risk.dataset import _infer_contract_type
from cuad_risk.provenance import GENERATOR_ID, TARGET_PROVENANCE


LOCKED_CATEGORY_IDS = {
    "governing_law",
    "renewal_term",
    "revenue_profit_sharing",
    "cap_on_liability",
    "uncapped_liability",
    "termination_for_convenience",
    "anti_assignment",
    "audit_rights",
    "license_grant",
    "exclusivity",
}


def _document(title: str, context: str, answer_text: str | None = None) -> dict:
    answers = []
    if answer_text is not None:
        answers.append(
            {
                "text": answer_text,
                "answer_start": context.index(answer_text),
            }
        )
    return {
        "title": title,
        "paragraphs": [
            {
                "context": context,
                "qas": [
                    {
                        "id": f"{title}__Governing Law_0",
                        "question": (
                            'Highlight the parts related to "Governing Law". '
                            "Which jurisdiction governs the contract?"
                        ),
                        "answers": answers,
                        "is_impossible": not answers,
                    }
                ],
            }
        ],
    }


class BuildDatasetCliTest(unittest.TestCase):
    def test_contract_type_inference_prioritizes_explicit_ma_titles(self) -> None:
        for title in (
            "ACME_ASSET_PURCHASE_AGREEMENT",
            "ACME_STOCK_PURCHASE_AGREEMENT",
            "ACME_SHARE_PURCHASE_AGREEMENT",
        ):
            with self.subTest(title=title):
                self.assertEqual(
                    _infer_contract_type(title),
                    "merger_acquisition",
                )

    def test_build_creates_split_safe_rows_for_every_locked_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_json = root / "train.json"
            test_json = root / "test.json"
            split_csv = root / "splits.csv"
            output_dir = root / "output"

            train_json.write_text(
                json.dumps(
                    {
                        "data": [
                            _document(
                                "TRAIN_ONE_MASTER_SERVICES_AGREEMENT",
                                "This Agreement is governed by the laws of California.",
                                "governed by the laws of California",
                            ),
                            _document(
                                "TRAIN_TWO_LICENSE_AGREEMENT",
                                "The parties agree to the terms written here.",
                            ),
                        ]
                    }
                ),
                encoding="utf-8",
            )
            test_json.write_text(
                json.dumps(
                    {
                        "data": [
                            _document(
                                "TEST_ONE_DISTRIBUTION_AGREEMENT",
                                "This Agreement is governed by the laws of New York.",
                                "governed by the laws of New York",
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with split_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["contract_id", "context_group_id", "split"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "contract_id": "contract_0001",
                        "context_group_id": "context_0001",
                        "split": "train",
                    }
                )
                writer.writerow(
                    {
                        "contract_id": "contract_0002",
                        "context_group_id": "context_0002",
                        "split": "validation",
                    }
                )

            project_root = Path(__file__).resolve().parents[1]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(project_root / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cuad_risk",
                    "build",
                    "--train-json",
                    str(train_json),
                    "--test-json",
                    str(test_json),
                    "--split-map",
                    str(split_csv),
                    "--rule-cards",
                    str(project_root / "data/risk/rule_cards.json"),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=project_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)

            with (output_dir / "category_assessments.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                category_rows = list(csv.DictReader(handle))
            self.assertEqual(len(category_rows), 30)
            self.assertEqual(
                {row["category_id"] for row in category_rows},
                LOCKED_CATEGORY_IDS,
            )
            self.assertEqual(
                {row["split"] for row in category_rows},
                {"train", "validation", "official_test"},
            )
            self.assertEqual(
                len({row["contract_id"] for row in category_rows}),
                3,
            )
            train_governing_law = next(
                row
                for row in category_rows
                if row["contract_id"] == "cuad_train_0001"
                and row["category_id"] == "governing_law"
            )
            self.assertEqual(train_governing_law["presence_status"], "present")
            self.assertEqual(train_governing_law["evidence_count"], "1")
            self.assertEqual(train_governing_law["finding_count"], "1")
            self.assertEqual(train_governing_law["contract_type"], "services")
            self.assertIn("risk_band", train_governing_law)
            self.assertIn("severity_ordinal", train_governing_law)
            self.assertIn("label_status", train_governing_law)
            self.assertEqual(train_governing_law["applicability"], "applicable")
            self.assertTrue(json.loads(train_governing_law["source_ids"]))
            self.assertEqual(
                train_governing_law["supervised_target_available"], "True"
            )
            self.assertEqual(train_governing_law["use_for_model_fit"], "True")

            train_exclusivity = next(
                row
                for row in category_rows
                if row["contract_id"] == "cuad_train_0001"
                and row["category_id"] == "exclusivity"
            )
            self.assertEqual(train_exclusivity["risk_band"], "not_applicable")
            self.assertEqual(train_exclusivity["unresolved_material"], "False")

            clause_findings = [
                json.loads(line)
                for line in (output_dir / "clause_findings.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(clause_findings), 2)
            train_finding = next(
                finding
                for finding in clause_findings
                if finding["contract_id"] == "cuad_train_0001"
            )
            self.assertEqual(train_finding["paragraph_index"], 0)
            self.assertEqual(
                train_finding["provenance"][0]["qa_id"],
                "TRAIN_ONE_MASTER_SERVICES_AGREEMENT__Governing Law_0",
            )
            self.assertEqual(
                train_finding["provenance"][0]["answer_start"],
                train_finding["answer_start"],
            )
            self.assertEqual(
                train_finding["provenance"][0]["answer_end"],
                train_finding["answer_end"],
            )

            with (output_dir / "contract_assessments.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                contract_rows = list(csv.DictReader(handle))
            self.assertEqual(len(contract_rows), 3)
            self.assertEqual(
                {row["contract_type"] for row in contract_rows},
                {"services", "license", "distribution"},
            )
            self.assertTrue(
                all(row["rule_contract_risk_band"] in {"low", "medium", "high"}
                    for row in contract_rows)
            )
            self.assertTrue(
                all(
                    row["rule_contract_review_priority_band"]
                    in {"low", "medium", "high"}
                    for row in contract_rows
                )
            )
            self.assertNotIn("reference_contract_risk_band", contract_rows[0])
            self.assertNotIn("model_contract_risk_band", contract_rows[0])
            category_assessment_ids = {
                row["assessment_id"] for row in category_rows
            }
            self.assertTrue(
                all(
                    set(json.loads(row["triggering_assessment_ids"]))
                    .issubset(category_assessment_ids)
                    for row in contract_rows
                )
            )

            training_examples = [
                json.loads(line)
                for line in (output_dir / "risk_training_examples.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(training_examples), 1)
            self.assertEqual(training_examples[0]["split"], "train")
            self.assertIsInstance(training_examples[0]["severity_ordinal"], int)
            self.assertIn("model_input_text", training_examples[0])
            self.assertIn("label_confidence", training_examples[0])
            self.assertIn(
                training_examples[0]["target_risk_band"],
                {"low", "medium", "high"},
            )
            self.assertNotIn("risk_band", training_examples[0])
            self.assertNotIn("trigger_ids", training_examples[0])
            self.assertNotIn("rationale", training_examples[0])
            self.assertEqual(
                training_examples[0]["target_provenance"],
                TARGET_PROVENANCE,
            )

            with (output_dir / "category_training_examples.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                category_training_rows = list(csv.DictReader(handle))
            self.assertTrue(category_training_rows)
            self.assertEqual(
                {row["split"] for row in category_training_rows},
                {"train", "validation"},
            )
            self.assertTrue(
                all(row["severity_ordinal"] for row in category_training_rows)
            )
            self.assertTrue(
                all("model_input_text" in row for row in category_training_rows)
            )
            self.assertTrue(
                all(
                    row["target_risk_band"] in {"low", "medium", "high"}
                    for row in category_training_rows
                )
            )
            self.assertNotIn("risk_band", category_training_rows[0])
            self.assertNotIn("trigger_ids", category_training_rows[0])
            self.assertIn("exact_text_seen_in_train", category_training_rows[0])
            self.assertTrue(
                all(
                    row["target_provenance"] == TARGET_PROVENANCE
                    for row in category_training_rows
                )
            )

            self.assertTrue(
                all(row["use_for_model_fit"] == "False" for row in contract_rows)
            )
            self.assertTrue(
                all(
                    row["use_for_model_validation"] == "False"
                    for row in contract_rows
                )
            )

            with (
                output_dir / "review" / "official_test_reference_template.csv"
            ).open(encoding="utf-8", newline="") as handle:
                review_rows = list(csv.DictReader(handle))
            self.assertEqual(len(review_rows), 2)
            self.assertEqual(
                {row["reviewer_slot"] for row in review_rows}, {"1", "2"}
            )
            for row in review_rows:
                self.assertEqual(row["human_risk_band"], "")
                self.assertEqual(row["human_risk_ordinal"], "")

            manifest = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["counts"]["contracts"], 3)
            self.assertEqual(manifest["counts"]["category_assessments"], 30)
            self.assertEqual(manifest["counts"]["clause_findings"], 2)
            self.assertEqual(manifest["counts"]["contract_assessments"], 3)
            self.assertEqual(manifest["counts"]["reference_template_rows"], 2)
            self.assertEqual(manifest["counts"]["risk_training_examples"], 1)
            self.assertEqual(
                manifest["counts"]["category_training_examples"],
                len(category_training_rows),
            )
            self.assertEqual(manifest["category_ids"], sorted(LOCKED_CATEGORY_IDS))
            self.assertEqual(manifest["generator"]["id"], GENERATOR_ID)
            self.assertEqual(
                manifest["input_sha256"]["train_json"],
                hashlib.sha256(train_json.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                manifest["distributions"]["contracts_by_split"],
                {"official_test": 1, "train": 1, "validation": 1},
            )

    def test_build_consolidates_same_clause_spans_but_keeps_distant_clauses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_json = root / "train.json"
            test_json = root / "test.json"
            split_csv = root / "splits.csv"
            rules_json = root / "rules.json"
            output_dir = root / "output"

            first = "Either party's liability shall not exceed fees."
            nearby = "Aggregate liability is limited to twelve months of fees."
            distant = "The operative limitation appears in another schedule."
            context = first + (" " * 40) + nearby + (" " * 300) + distant

            def qa(qa_id: str, answer_text: str) -> dict:
                return {
                    "id": qa_id,
                    "question": 'Highlight the parts related to "Cap On Liability".',
                    "answers": [
                        {
                            "text": answer_text,
                            "answer_start": context.index(answer_text),
                        }
                    ],
                    "is_impossible": False,
                }

            document = {
                "title": "ACME_MASTER_SERVICES_AGREEMENT",
                "paragraphs": [
                    {
                        "context": context,
                        "qas": [
                            qa("cap_duplicate_a", first),
                            qa("cap_duplicate_b", first),
                            qa("cap_nearby", nearby),
                            qa("cap_distant", distant),
                        ],
                    }
                ],
            }
            train_json.write_text(
                json.dumps({"data": [document]}), encoding="utf-8"
            )
            test_json.write_text(json.dumps({"data": []}), encoding="utf-8")
            context_group_id = (
                "context_"
                + hashlib.md5(context.encode("utf-8")).hexdigest()[:10]
            )
            with split_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["context_group_id", "split"]
                )
                writer.writeheader()
                writer.writerow(
                    {"context_group_id": context_group_id, "split": "train"}
                )
            rules_json.write_text(
                json.dumps(
                    {
                        "dataset_name": "test risk labels",
                        "dataset_version": "test",
                        "categories": [
                            {
                                "category_id": "cap_on_liability",
                                "category_name": "Cap On Liability",
                                "rule_card_id": "cap-v1",
                                "review_bundle_id": "liability",
                                "risk_domain": "liability",
                                "issue_family_template": "liability-allocation",
                                "material_if_unresolved": True,
                                "present_rules": [
                                    {
                                        "rule_id": "cap_present",
                                        "priority": 1,
                                        "when_any": ["liability"],
                                        "severity_ordinal": 2,
                                        "direction": "mixed",
                                        "confidence": "medium",
                                        "rationale": "A cap needs human review.",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            project_root = Path(__file__).resolve().parents[1]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(project_root / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cuad_risk",
                    "build",
                    "--train-json",
                    str(train_json),
                    "--test-json",
                    str(test_json),
                    "--split-map",
                    str(split_csv),
                    "--rule-cards",
                    str(rules_json),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=project_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            findings = [
                json.loads(line)
                for line in (output_dir / "clause_findings.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(findings), 2)
            self.assertEqual(
                [len(finding["provenance"]) for finding in findings], [3, 1]
            )
            self.assertEqual(
                {item["qa_id"] for item in findings[0]["provenance"]},
                {"cap_duplicate_a", "cap_duplicate_b", "cap_nearby"},
            )
            self.assertEqual(findings[0]["paragraph_index"], 0)
            self.assertEqual(findings[0]["answer_start"], context.index(first))
            self.assertEqual(
                findings[0]["answer_end"], context.index(nearby) + len(nearby)
            )
            self.assertEqual(findings[1]["evidence_text"], distant)
            self.assertEqual(findings[0]["risk_band"], "medium")
            self.assertEqual(findings[0]["contract_type"], "services")
            self.assertEqual(findings[1]["risk_band"], "unresolved")

            with (output_dir / "category_assessments.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                category_row = next(csv.DictReader(handle))
            self.assertEqual(category_row["severity_ordinal"], "2")
            self.assertEqual(category_row["unresolved_material"], "True")

            with (output_dir / "category_assessments.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                category_row = next(csv.DictReader(handle))
            self.assertEqual(category_row["context_group_id"], context_group_id)
            self.assertEqual(category_row["finding_count"], "2")
            self.assertEqual(category_row["evidence_count"], "4")
            self.assertEqual(category_row["risk_band"], "medium")

            with (output_dir / "contract_assessments.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                contract_row = next(csv.DictReader(handle))
            self.assertEqual(
                contract_row["rule_contract_risk_band"], "medium"
            )

            manifest = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["counts"]["clause_findings"], 2)
            self.assertEqual(manifest["counts"]["source_answer_spans"], 4)


if __name__ == "__main__":
    unittest.main()
