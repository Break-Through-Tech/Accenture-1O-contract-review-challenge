import csv
import hashlib
import json
from pathlib import Path
import re
import unittest

from cuad_risk.dataset import PACKAGE_CONTENT_FILES


FELLOW_DOCUMENTS = (
    "README.md",
    "METHODOLOGY.md",
    "SCHEMA.md",
    "CATEGORY_DEFINITIONS.md",
    "review/README.md",
)


class FellowPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.package_dir = cls.project_root / "data" / "risk"

    def test_package_is_flat_and_contains_all_fellow_documentation(self) -> None:
        self.assertFalse((self.package_dir / "v1").exists())
        required_files = set(PACKAGE_CONTENT_FILES) | {"manifest.json"}
        actual_files = {
            str(path.relative_to(self.package_dir))
            for path in self.package_dir.rglob("*")
            if path.is_file()
        }
        self.assertEqual(required_files, actual_files)

    def test_fellow_documents_only_use_resolvable_local_links(self) -> None:
        link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
        forbidden_references = (
            "docs/",
            "config/",
            "src/",
            "notebooks/",
            "pyproject.toml",
        )
        for name in FELLOW_DOCUMENTS:
            path = self.package_dir / name
            text = path.read_text(encoding="utf-8")
            with self.subTest(document=name):
                for forbidden in forbidden_references:
                    self.assertNotIn(forbidden, text)
                for target in link_pattern.findall(text):
                    if target.startswith(("https://", "http://", "#")):
                        continue
                    resolved = (path.parent / target).resolve()
                    self.assertTrue(resolved.is_relative_to(self.package_dir.resolve()))
                    self.assertTrue(resolved.exists(), target)

    def test_fellow_metadata_does_not_expose_internal_release_versions(self) -> None:
        forbidden_version = re.compile(r"v1(?:\.1(?:\.0)?)?", re.I)

        rule_config = json.loads(
            (self.package_dir / "rule_cards.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("dataset_version", rule_config)
        self.assertIsNone(forbidden_version.search(json.dumps(rule_config)))

        source_registry = json.loads(
            (self.package_dir / "source_registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("dataset_version", source_registry)
        self.assertIsNone(forbidden_version.search(json.dumps(source_registry)))

        manifest = json.loads(
            (self.package_dir / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("dataset_version", manifest)
        self.assertIsNone(
            forbidden_version.search(str(manifest.get("generator", {}).get("id", "")))
        )
        implementation_hash = manifest.get("generator", {}).get(
            "implementation_sha256", ""
        )
        self.assertRegex(implementation_hash, r"^[0-9a-f]{64}$")
        package_hashes = manifest.get("package_sha256", {})
        expected_package_files = {
            str(path.relative_to(self.package_dir))
            for path in self.package_dir.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(set(package_hashes), expected_package_files)
        for relative_path, expected_hash in package_hashes.items():
            self.assertEqual(
                hashlib.sha256(
                    (self.package_dir / relative_path).read_bytes()
                ).hexdigest(),
                expected_hash,
            )

        for name in FELLOW_DOCUMENTS:
            with self.subTest(document=name):
                self.assertIsNone(
                    forbidden_version.search(
                        (self.package_dir / name).read_text(encoding="utf-8")
                    )
                )

    def test_published_rows_use_stable_unversioned_provenance_ids(self) -> None:
        forbidden_version = re.compile(r"v1(?:\.1)?", re.I)

        with (self.package_dir / "contract_assessments.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            contract_rows = list(csv.DictReader(handle))
        self.assertIn("rollup_policy_id", contract_rows[0])
        self.assertNotIn("rollup_rule_version", contract_rows[0])
        self.assertTrue(
            all(row["rollup_policy_id"] == "buyer_risk_rollup" for row in contract_rows)
        )

        with (self.package_dir / "category_assessments.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            category_rows = list(csv.DictReader(handle))
        for row in category_rows:
            self.assertIsNone(forbidden_version.search(row["rule_card_id"]))
            self.assertIsNone(forbidden_version.search(row["source_ids"]))
            self.assertIsNone(forbidden_version.search(row["rationale"]))

        for line in (self.package_dir / "clause_findings.jsonl").read_text(
            encoding="utf-8"
        ).splitlines():
            finding = json.loads(line)
            self.assertIsNone(forbidden_version.search(finding["rule_card_id"]))
            self.assertIsNone(
                forbidden_version.search(json.dumps(finding["source_ids"]))
            )
            self.assertIsNone(forbidden_version.search(finding["rationale"]))

        for line in (self.package_dir / "risk_training_examples.jsonl").read_text(
            encoding="utf-8"
        ).splitlines():
            example = json.loads(line)
            self.assertEqual(
                example["target_provenance"],
                "research_derived_weak_rule",
            )

    def test_package_contains_joinable_complete_contract_text(self) -> None:
        with (self.package_dir / "contracts.jsonl").open(
            encoding="utf-8"
        ) as handle:
            contract_rows = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(contract_rows), 510)
        self.assertEqual(
            len({row["contract_id"] for row in contract_rows}),
            len(contract_rows),
        )
        for row in contract_rows:
            contract_text = "\n\n".join(row["paragraphs"])
            self.assertEqual(row["contract_text"], contract_text)
            self.assertEqual(
                row["contract_text_sha256"],
                hashlib.sha256(contract_text.encode("utf-8")).hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
