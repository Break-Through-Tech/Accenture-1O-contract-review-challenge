from collections import defaultdict
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from cuad_risk.provenance import generator_fingerprint
from cuad_risk.rollup import roll_up_contract


class DatasetValidationError(ValueError):
    """Raised when generated risk data violates a published invariant."""


@dataclass(frozen=True)
class ValidationReport:
    contract_count: int
    category_assessment_count: int
    split_counts: dict[str, int]


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_category_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    expected_category_ids: Sequence[str],
) -> ValidationReport:
    materialized = list(rows)
    expected = set(expected_category_ids)
    seen_pairs: set[tuple[str, str]] = set()
    categories_by_contract: dict[str, set[str]] = defaultdict(set)
    splits_by_contract: dict[str, set[str]] = defaultdict(set)
    splits_by_context_group: dict[str, set[str]] = defaultdict(set)
    splits_by_text_hash: dict[str, set[str]] = defaultdict(set)
    expected_bands = {"0": "none", "1": "low", "2": "medium", "3": "high"}
    allowed_splits = {"train", "validation", "official_test"}

    for row in materialized:
        contract_id = str(row["contract_id"])
        category_id = str(row["category_id"])
        pair = (contract_id, category_id)
        if pair in seen_pairs:
            raise DatasetValidationError(
                f"duplicate contract-category assessment: {contract_id}/{category_id}"
            )
        seen_pairs.add(pair)
        categories_by_contract[contract_id].add(category_id)
        split = str(row["split"])
        if split not in allowed_splits:
            raise DatasetValidationError(
                f"unknown split for {contract_id}/{category_id}: {split}"
            )
        splits_by_contract[contract_id].add(split)
        context_group_id = str(row.get("context_group_id", ""))
        if not context_group_id:
            raise DatasetValidationError(
                f"missing context group for {contract_id}/{category_id}"
            )
        splits_by_context_group[context_group_id].add(split)
        text_hash = str(row.get("contract_text_sha256", ""))
        if text_hash:
            splits_by_text_hash[text_hash].add(split)

        severity = row.get("severity_ordinal")
        band = row.get("risk_band")
        label_status = str(row.get("label_status", ""))
        if label_status == "weak_abstain" and severity not in {None, ""}:
            raise DatasetValidationError(
                f"abstain has numeric severity for {contract_id}/{category_id}"
            )
        if label_status == "weak_abstain" and str(band) != "unresolved":
            raise DatasetValidationError(
                f"abstain has non-unresolved band for {contract_id}/{category_id}"
            )
        if label_status == "weak_not_applicable":
            if severity not in {None, ""} or str(band) != "not_applicable":
                raise DatasetValidationError(
                    "not-applicable row has a numeric target or wrong band for "
                    f"{contract_id}/{category_id}"
                )
        if label_status == "weak_automatic" and severity in {None, ""}:
            raise DatasetValidationError(
                f"automatic label lacks numeric severity for {contract_id}/{category_id}"
            )
        if severity not in {None, ""}:
            expected_band = expected_bands.get(str(severity))
            if expected_band is None or str(band) != expected_band:
                raise DatasetValidationError(
                    f"severity-band mismatch for {contract_id}/{category_id}"
                )

    for contract_id, actual_categories in categories_by_contract.items():
        if actual_categories != expected:
            missing = sorted(expected - actual_categories)
            extra = sorted(actual_categories - expected)
            raise DatasetValidationError(
                f"category coverage mismatch for {contract_id}; "
                f"missing={missing}, extra={extra}"
            )
        if len(splits_by_contract[contract_id]) != 1:
            raise DatasetValidationError(
                f"contract appears in multiple splits: {contract_id}"
            )

    for context_group_id, splits in splits_by_context_group.items():
        if len(splits) != 1:
            raise DatasetValidationError(
                f"context group appears in multiple splits: "
                f"{context_group_id} -> {sorted(splits)}"
            )

    for text_hash, splits in splits_by_text_hash.items():
        if len(splits) != 1:
            raise DatasetValidationError(
                f"contract text hash appears in multiple splits: "
                f"{text_hash} -> {sorted(splits)}"
            )

    split_contracts: dict[str, set[str]] = defaultdict(set)
    for contract_id, splits in splits_by_contract.items():
        if splits:
            split_contracts[next(iter(splits))].add(contract_id)

    return ValidationReport(
        contract_count=len(categories_by_contract),
        category_assessment_count=len(materialized),
        split_counts={
            split: len(contract_ids)
            for split, contract_ids in sorted(split_contracts.items())
        },
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise DatasetValidationError(f"missing published table: {path.name}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_dataset_dir(
    dataset_dir: Path,
    rule_cards_path: Path,
) -> ValidationReport:
    """Validate the cross-file invariants of a published dataset release."""

    with rule_cards_path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    expected_category_ids = [
        str(category["category_id"]) for category in config["categories"]
    ]
    if len(expected_category_ids) != 10 or len(set(expected_category_ids)) != 10:
        raise DatasetValidationError(
            "risk rule cards must contain exactly ten unique category IDs"
        )

    source_registry_path = rule_cards_path.with_name("source_registry.json")
    if not source_registry_path.is_file():
        raise DatasetValidationError("missing source registry: source_registry.json")
    with source_registry_path.open(encoding="utf-8") as handle:
        source_registry = json.load(handle)
    registered_source_ids = {
        str(source["source_id"]) for source in source_registry.get("sources", [])
    }
    referenced_source_ids = set(config.get("methodology_source_ids", []))
    for category in config["categories"]:
        referenced_source_ids.update(category.get("source_ids", []))
        for rule_group in ("present_rules", "missing_rules"):
            for rule in category.get(rule_group, []):
                referenced_source_ids.update(rule.get("source_ids", []))
    missing_source_ids = sorted(referenced_source_ids - registered_source_ids)
    if missing_source_ids:
        raise DatasetValidationError(
            f"unregistered rule-card source IDs: {missing_source_ids}"
        )

    category_rows = _read_csv(dataset_dir / "category_assessments.csv")
    report = validate_category_rows(
        category_rows,
        expected_category_ids=expected_category_ids,
    )
    release_invariants = config.get("release_invariants", {})
    expected_contract_count = release_invariants.get("contracts")
    if (
        expected_contract_count is not None
        and report.contract_count != expected_contract_count
    ):
        raise DatasetValidationError(
            "release contract count mismatch: "
            f"expected {expected_contract_count}, found {report.contract_count}"
        )
    expected_category_count = release_invariants.get("category_assessments")
    if (
        expected_category_count is not None
        and report.category_assessment_count != expected_category_count
    ):
        raise DatasetValidationError(
            "release category assessment count mismatch: "
            f"expected {expected_category_count}, "
            f"found {report.category_assessment_count}"
        )
    expected_split_counts = release_invariants.get("contracts_by_split")
    if expected_split_counts and report.split_counts != expected_split_counts:
        raise DatasetValidationError(
            "release split counts mismatch: "
            f"expected {expected_split_counts}, found {report.split_counts}"
        )
    contract_ids = {row["contract_id"] for row in category_rows}
    assessment_ids = {row["assessment_id"] for row in category_rows}
    category_pairs = {
        (row["contract_id"], row["category_id"]) for row in category_rows
    }
    category_metadata_by_contract: dict[str, dict[str, str]] = {}
    for row in category_rows:
        category_metadata_by_contract.setdefault(row["contract_id"], row)

    contracts_path = dataset_dir / "contracts.jsonl"
    if not contracts_path.is_file():
        raise DatasetValidationError("missing published table: contracts.jsonl")
    contract_text_rows_by_id: dict[str, dict[str, object]] = {}
    with contracts_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            contract = json.loads(line)
            contract_id = str(contract.get("contract_id", ""))
            if not contract_id or contract_id in contract_text_rows_by_id:
                raise DatasetValidationError(
                    f"missing or duplicate contract text ID at line {line_number}"
                )
            source_row = category_metadata_by_contract.get(contract_id)
            if source_row is None:
                raise DatasetValidationError(
                    f"contract text references unknown contract at line {line_number}"
                )
            paragraphs = contract.get("paragraphs")
            if not isinstance(paragraphs, list) or not all(
                isinstance(paragraph, str) for paragraph in paragraphs
            ):
                raise DatasetValidationError(
                    f"contract text has invalid paragraphs at line {line_number}"
                )
            reconstructed_text = "\n\n".join(paragraphs)
            if contract.get("contract_text") != reconstructed_text:
                raise DatasetValidationError(
                    f"contract text does not match paragraphs for {contract_id}"
                )
            text_hash = hashlib.sha256(
                reconstructed_text.encode("utf-8")
            ).hexdigest()
            if contract.get("contract_text_sha256") != text_hash:
                raise DatasetValidationError(
                    f"contract text hash mismatch for {contract_id}"
                )
            metadata_fields = (
                "source_contract_id",
                "source_partition",
                "source_index",
                "split",
                "context_group_id",
                "contract_title",
                "contract_type",
                "contract_type_confidence",
                "contract_text_sha256",
            )
            for field in metadata_fields:
                if str(contract.get(field, "")) != str(source_row.get(field, "")):
                    raise DatasetValidationError(
                        f"contract text metadata mismatch for {contract_id}/{field}"
                    )
            contract_text_rows_by_id[contract_id] = contract
    if set(contract_text_rows_by_id) != contract_ids:
        raise DatasetValidationError(
            "contract text identifiers do not match category table"
        )

    contract_rows = _read_csv(dataset_dir / "contract_assessments.csv")
    assessed_contract_ids = {row["contract_id"] for row in contract_rows}
    if len(contract_rows) != report.contract_count or assessed_contract_ids != contract_ids:
        raise DatasetValidationError(
            "contract assessment count or identifiers do not match category table"
        )
    invalid_contract_bands = sorted(
        {
            row.get("rule_contract_risk_band", "")
            for row in contract_rows
            if row.get("rule_contract_risk_band", "")
            not in {"low", "medium", "high"}
        }
    )
    if invalid_contract_bands:
        raise DatasetValidationError(
            f"invalid contract risk bands: {invalid_contract_bands}"
        )
    required_contract_fields = {
        "rule_contract_review_priority_band",
        "rule_contract_review_priority_ordinal",
    }
    if contract_rows and not required_contract_fields.issubset(contract_rows[0]):
        raise DatasetValidationError(
            "contract assessments lack risk/review separation fields: "
            f"{sorted(required_contract_fields - set(contract_rows[0]))}"
        )
    contract_rows_by_id = {row["contract_id"]: row for row in contract_rows}
    category_rows_by_contract: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in category_rows:
        category_rows_by_contract[row["contract_id"]].append(row)
    for contract_id, rows in category_rows_by_contract.items():
        rollup = roll_up_contract(
            {
                "finding_id": row.get("assessment_id")
                or f"{contract_id}:{row['category_id']}",
                "severity_ordinal": (
                    None
                    if row.get("severity_ordinal") in {None, ""}
                    else int(row["severity_ordinal"])
                ),
                "risk_domain": row.get("risk_domain", row["category_id"]),
                "issue_family_id": row.get(
                    "issue_family_id", row["category_id"]
                ),
                "unresolved_material": _as_bool(
                    row.get("unresolved_material", False)
                ),
            }
            for row in rows
        )
        published = contract_rows_by_id[contract_id]
        if published.get("rule_contract_risk_band") != rollup.risk_band:
            raise DatasetValidationError(
                "contract rollup mismatch for "
                f"{contract_id}: expected {rollup.risk_band}, found "
                f"{published.get('rule_contract_risk_band')}"
            )
        if (
            published.get("rule_contract_review_priority_band")
            != rollup.review_priority_band
        ):
            raise DatasetValidationError(
                "contract review-priority mismatch for "
                f"{contract_id}: expected {rollup.review_priority_band}, found "
                f"{published.get('rule_contract_review_priority_band')}"
            )
        published_ordinal = published.get("rule_contract_risk_ordinal", "")
        if published_ordinal and int(published_ordinal) != rollup.risk_ordinal:
            raise DatasetValidationError(
                f"contract rollup ordinal mismatch for {contract_id}"
            )
        published_priority_ordinal = published.get(
            "rule_contract_review_priority_ordinal", ""
        )
        if (
            published_priority_ordinal
            and int(published_priority_ordinal)
            != rollup.review_priority_ordinal
        ):
            raise DatasetValidationError(
                f"contract review-priority ordinal mismatch for {contract_id}"
            )
        raw_trigger_ids = published.get("triggering_assessment_ids", "[]")
        try:
            published_trigger_ids = json.loads(raw_trigger_ids or "[]")
        except json.JSONDecodeError as error:
            raise DatasetValidationError(
                f"invalid triggering assessment IDs for {contract_id}"
            ) from error
        if not set(published_trigger_ids).issubset(assessment_ids):
            raise DatasetValidationError(
                f"unknown triggering assessment ID for {contract_id}"
            )
        if sorted(published_trigger_ids) != sorted(rollup.triggering_finding_ids):
            raise DatasetValidationError(
                f"contract trigger mismatch for {contract_id}"
            )
        if _as_bool(published.get("use_for_model_fit", False)) or _as_bool(
            published.get("use_for_model_validation", False)
        ):
            raise DatasetValidationError(
                "contract rule outputs must not be marked fit-ready: "
                f"{contract_id}"
            )

    findings_path = dataset_dir / "clause_findings.jsonl"
    if not findings_path.is_file():
        raise DatasetValidationError("missing published table: clause_findings.jsonl")
    finding_ids: set[str] = set()
    findings_by_id: dict[str, dict[str, object]] = {}
    finding_count = 0
    with findings_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            finding = json.loads(line)
            finding_id = str(finding["finding_id"])
            if finding_id in finding_ids:
                raise DatasetValidationError(f"duplicate finding id: {finding_id}")
            finding_ids.add(finding_id)
            findings_by_id[finding_id] = finding
            pair = (str(finding["contract_id"]), str(finding["category_id"]))
            if pair not in category_pairs:
                raise DatasetValidationError(
                    f"finding references unknown contract-category at line {line_number}"
                )
            contract_text_row = contract_text_rows_by_id[pair[0]]
            paragraph_index = int(finding["paragraph_index"])
            paragraphs = contract_text_row["paragraphs"]
            if paragraph_index < 0 or paragraph_index >= len(paragraphs):
                raise DatasetValidationError(
                    f"finding paragraph index is out of range: {finding_id}"
                )
            answer_start = int(finding["answer_start"])
            answer_end = int(finding["answer_end"])
            paragraph = paragraphs[paragraph_index]
            if (
                answer_start < 0
                or answer_end < answer_start
                or answer_end > len(paragraph)
                or paragraph[answer_start:answer_end] != finding["evidence_text"]
            ):
                raise DatasetValidationError(
                    f"finding offsets do not match contract text: {finding_id}"
                )
            severity = finding.get("severity_ordinal")
            if severity is not None:
                expected_band = {0: "none", 1: "low", 2: "medium", 3: "high"}.get(
                    int(severity)
                )
                if expected_band != finding.get("risk_band"):
                    raise DatasetValidationError(
                        f"finding severity-band mismatch: {finding_id}"
                    )
            finding_count += 1

    review_rows = _read_csv(
        dataset_dir / "review" / "official_test_reference_template.csv"
    )
    test_contract_ids = {
        row["contract_id"]
        for row in category_rows
        if row["split"] == "official_test"
    }
    slots_by_contract: dict[str, set[str]] = defaultdict(set)
    for row in review_rows:
        slots_by_contract[row["contract_id"]].add(row["reviewer_slot"])
    if set(slots_by_contract) != test_contract_ids or any(
        slots != {"1", "2"} for slots in slots_by_contract.values()
    ):
        raise DatasetValidationError(
            "official-test review template must contain reviewer slots 1 and 2 "
            "for every official-test contract"
        )

    training_path = dataset_dir / "risk_training_examples.jsonl"
    if not training_path.is_file():
        raise DatasetValidationError(
            "missing published table: risk_training_examples.jsonl"
        )
    required_training_fields = {
        "finding_id",
        "model_input_text",
        "severity_ordinal",
        "target_risk_band",
        "label_confidence",
        "target_name",
        "target_provenance",
    }
    leaked_annotation_fields = {
        "risk_band",
        "direction",
        "trigger_ids",
        "source_ids",
        "rationale",
        "label_status",
    }
    training_count = 0
    with training_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            example = json.loads(line)
            if example.get("split") not in {"train", "validation"}:
                raise DatasetValidationError(
                    "risk training examples may not contain official-test rows "
                    f"(line {line_number})"
                )
            if example.get("severity_ordinal") is None:
                raise DatasetValidationError(
                    f"risk training example lacks target at line {line_number}"
                )
            expected_three_class_band = (
                "low"
                if int(example["severity_ordinal"]) in {0, 1}
                else "medium"
                if int(example["severity_ordinal"]) == 2
                else "high"
            )
            if example.get("target_risk_band") != expected_three_class_band:
                raise DatasetValidationError(
                    "risk training example has invalid three-class target at "
                    f"line {line_number}"
                )
            missing_fields = required_training_fields - set(example)
            if missing_fields:
                raise DatasetValidationError(
                    "risk training example lacks model-ready fields at line "
                    f"{line_number}: {sorted(missing_fields)}"
                )
            leaked_fields = leaked_annotation_fields & set(example)
            if leaked_fields:
                raise DatasetValidationError(
                    "risk training example contains target-derived annotation "
                    f"fields at line {line_number}: {sorted(leaked_fields)}"
                )
            source_finding = findings_by_id.get(str(example["finding_id"]))
            if source_finding is None:
                raise DatasetValidationError(
                    f"risk training example has no source finding at line {line_number}"
                )
            if (
                example["severity_ordinal"]
                != source_finding.get("severity_ordinal")
                or example["model_input_text"]
                != source_finding.get("evidence_text")
            ):
                raise DatasetValidationError(
                    f"risk training/source mismatch at line {line_number}"
                )
            training_count += 1

    category_training_rows = _read_csv(
        dataset_dir / "category_training_examples.csv"
    )
    source_rows_by_pair = {
        (row["contract_id"], row["category_id"]): row
        for row in category_rows
    }
    if category_training_rows:
        leaked_fields = leaked_annotation_fields & set(category_training_rows[0])
        if leaked_fields:
            raise DatasetValidationError(
                "category training examples contain target-derived annotation "
                f"fields: {sorted(leaked_fields)}"
            )
        if "exact_text_seen_in_train" not in category_training_rows[0]:
            raise DatasetValidationError(
                "category training examples lack duplicate-text audit flag"
            )
        if "target_risk_band" not in category_training_rows[0]:
            raise DatasetValidationError(
                "category training examples lack three-class target"
            )
    for row in category_training_rows:
        pair = (row["contract_id"], row["category_id"])
        source_row = source_rows_by_pair.get(pair)
        if source_row is None or row.get("severity_ordinal") in {None, ""}:
            raise DatasetValidationError(
                "category training row lacks a source assessment or numeric target"
            )
        if row.get("split") not in {"train", "validation"}:
            raise DatasetValidationError(
                "category training examples may not contain official-test rows"
            )
        if row.get("severity_ordinal") != source_row.get("severity_ordinal"):
            raise DatasetValidationError(
                f"category training target mismatch for {pair[0]}/{pair[1]}"
            )
        expected_three_class_band = (
            "low"
            if int(row["severity_ordinal"]) in {0, 1}
            else "medium"
            if int(row["severity_ordinal"]) == 2
            else "high"
        )
        if row.get("target_risk_band") != expected_three_class_band:
            raise DatasetValidationError(
                "category training three-class target mismatch for "
                f"{pair[0]}/{pair[1]}"
            )
        if row.get("model_input_text") != source_row.get("evidence_text"):
            raise DatasetValidationError(
                f"category training/source text mismatch for {pair[0]}/{pair[1]}"
            )
        if row.get("label_confidence") != source_row.get("confidence"):
            raise DatasetValidationError(
                "category training/source confidence mismatch for "
                f"{pair[0]}/{pair[1]}"
            )

    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.is_file():
        raise DatasetValidationError("missing published table: manifest.json")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("generator") != generator_fingerprint():
        raise DatasetValidationError(
            "manifest generator fingerprint does not match the current builder code"
        )
    expected_config_hashes = {
        "rule_cards": _sha256(rule_cards_path),
        "source_registry": _sha256(source_registry_path),
    }
    for name, expected_hash in expected_config_hashes.items():
        if manifest.get("input_sha256", {}).get(name) != expected_hash:
            raise DatasetValidationError(
                f"manifest input hash mismatch for {name}"
            )
    package_hashes = manifest.get("package_sha256")
    if not isinstance(package_hashes, dict) or not package_hashes:
        raise DatasetValidationError("manifest lacks package hash coverage")
    actual_package_files = {
        str(path.relative_to(dataset_dir))
        for path in dataset_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if set(package_hashes) != actual_package_files:
        raise DatasetValidationError(
            "manifest package file inventory mismatch: "
            f"expected {sorted(actual_package_files)}, "
            f"found {sorted(package_hashes)}"
        )
    for relative_path, expected_hash in package_hashes.items():
        package_path = dataset_dir / relative_path
        if not package_path.is_file():
            raise DatasetValidationError(
                f"manifest package file is missing: {relative_path}"
            )
        if _sha256(package_path) != expected_hash:
            raise DatasetValidationError(
                f"manifest package hash mismatch for {relative_path}"
            )
    if set(manifest.get("category_ids", [])) != set(expected_category_ids):
        raise DatasetValidationError("manifest category IDs do not match rule cards")
    actual_counts = {
        "contracts": report.contract_count,
        "contract_texts": len(contract_text_rows_by_id),
        "category_assessments": report.category_assessment_count,
        "clause_findings": finding_count,
        "source_answer_spans": sum(
            int(row.get("evidence_count", 0)) for row in category_rows
        ),
        "contract_assessments": len(contract_rows),
        "risk_training_examples": training_count,
        "category_training_examples": len(category_training_rows),
        "reference_template_rows": len(review_rows),
    }
    for name, actual in actual_counts.items():
        if manifest.get("counts", {}).get(name) != actual:
            raise DatasetValidationError(
                f"manifest count mismatch for {name}: "
                f"expected {actual}, found {manifest.get('counts', {}).get(name)}"
            )

    return report
