import unittest

from cuad_risk.validation import DatasetValidationError, validate_category_rows


CATEGORY_IDS = tuple(f"category_{index}" for index in range(10))


def _rows() -> list[dict]:
    return [
        {
            "contract_id": "cuad_train_0001",
            "context_group_id": "context_0001",
            "contract_text_sha256": "hash-one",
            "split": "train",
            "category_id": category_id,
            "severity_ordinal": "1",
            "risk_band": "low",
            "label_status": "weak_automatic",
        }
        for category_id in CATEGORY_IDS
    ]


class ValidateDatasetTest(unittest.TestCase):
    def test_valid_rows_report_complete_contract_category_coverage(self) -> None:
        report = validate_category_rows(_rows(), expected_category_ids=CATEGORY_IDS)

        self.assertEqual(report.contract_count, 1)
        self.assertEqual(report.category_assessment_count, 10)
        self.assertEqual(report.split_counts, {"train": 1})

    def test_duplicate_contract_category_is_rejected(self) -> None:
        rows = _rows()
        rows.append(rows[0].copy())

        with self.assertRaisesRegex(
            DatasetValidationError, "duplicate contract-category"
        ):
            validate_category_rows(rows, expected_category_ids=CATEGORY_IDS)

    def test_severity_band_mismatch_is_rejected(self) -> None:
        rows = _rows()
        rows[0]["severity_ordinal"] = "3"

        with self.assertRaisesRegex(DatasetValidationError, "severity-band"):
            validate_category_rows(rows, expected_category_ids=CATEGORY_IDS)

    def test_context_group_cannot_cross_train_and_validation(self) -> None:
        rows = _rows()
        duplicate_contract = []
        for row in rows:
            cloned = row.copy()
            cloned["contract_id"] = "cuad_train_0002"
            cloned["split"] = "validation"
            cloned["contract_text_sha256"] = "hash-two"
            duplicate_contract.append(cloned)

        with self.assertRaisesRegex(DatasetValidationError, "context group"):
            validate_category_rows(
                rows + duplicate_contract,
                expected_category_ids=CATEGORY_IDS,
            )

    def test_exact_contract_text_cannot_cross_development_and_test(self) -> None:
        rows = _rows()
        test_contract = []
        for row in rows:
            cloned = row.copy()
            cloned["contract_id"] = "cuad_test_0001"
            cloned["context_group_id"] = "official_test_0001"
            cloned["split"] = "official_test"
            test_contract.append(cloned)

        with self.assertRaisesRegex(DatasetValidationError, "text hash"):
            validate_category_rows(
                rows + test_contract,
                expected_category_ids=CATEGORY_IDS,
            )

    def test_unresolved_label_must_not_have_numeric_severity(self) -> None:
        rows = _rows()
        rows[0]["label_status"] = "weak_abstain"
        rows[0]["risk_band"] = "unresolved"

        with self.assertRaisesRegex(DatasetValidationError, "abstain"):
            validate_category_rows(rows, expected_category_ids=CATEGORY_IDS)


if __name__ == "__main__":
    unittest.main()
