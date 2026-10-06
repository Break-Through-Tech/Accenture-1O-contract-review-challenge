from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from cuad_risk.provenance import TARGET_PROVENANCE, generator_fingerprint
from cuad_risk.rollup import roll_up_contract
from cuad_risk.scoring import FindingAssessment, score_finding


# CUAD often annotates one provision with several overlapping answer spans. A
# short gap can also separate two fragments of the same provision. This value is
# intentionally conservative so provisions in different sections remain separate.
MAX_SAME_FINDING_GAP_CHARS = 250

PACKAGE_CONTENT_FILES = (
    "CATEGORY_DEFINITIONS.md",
    "METHODOLOGY.md",
    "README.md",
    "SCHEMA.md",
    "category_assessments.csv",
    "category_training_examples.csv",
    "clause_findings.jsonl",
    "contract_assessments.csv",
    "contracts.jsonl",
    "review/README.md",
    "review/official_test_reference_template.csv",
    "risk_training_examples.jsonl",
    "rule_cards.json",
    "source_registry.json",
)

CATEGORY_FIELDS = [
    "assessment_id",
    "contract_id",
    "source_contract_id",
    "source_partition",
    "source_index",
    "split",
    "context_group_id",
    "contract_title",
    "contract_type",
    "contract_type_confidence",
    "category_id",
    "category_name",
    "rule_card_id",
    "review_bundle_id",
    "risk_domain",
    "issue_family_id",
    "presence_status",
    "finding_kind",
    "finding_count",
    "finding_ids",
    "evidence_count",
    "evidence_text",
    "severity_ordinal",
    "risk_band",
    "direction",
    "confidence",
    "label_status",
    "applicability",
    "trigger_ids",
    "source_ids",
    "rationale",
    "unresolved_material",
    "supervised_target_available",
    "use_for_model_fit",
    "use_for_model_validation",
    "contract_text_sha256",
]

CONTRACT_FIELDS = [
    "contract_id",
    "source_contract_id",
    "source_partition",
    "source_index",
    "split",
    "context_group_id",
    "contract_title",
    "contract_type",
    "contract_type_confidence",
    "rule_contract_risk_band",
    "rule_contract_risk_ordinal",
    "rule_contract_review_priority_band",
    "rule_contract_review_priority_ordinal",
    "rule_label_status",
    "rollup_policy_id",
    "triggering_assessment_ids",
    "triggering_domains",
    "unresolved_required_categories",
    "rationale",
    "use_for_model_fit",
    "use_for_model_validation",
    "contract_text_sha256",
]

REVIEW_TEMPLATE_FIELDS = [
    "contract_id",
    "source_contract_id",
    "source_partition",
    "source_index",
    "split",
    "context_group_id",
    "contract_title",
    "contract_type",
    "contract_type_confidence",
    "contract_text_sha256",
    "reviewer_slot",
    "reviewer_id",
    "human_risk_band",
    "human_risk_ordinal",
    "human_confidence",
    "human_rationale",
    "reviewed_at",
]

CLAUSE_TRAINING_FIELDS = [
    "example_id",
    "finding_id",
    "contract_id",
    "source_contract_id",
    "source_partition",
    "source_index",
    "split",
    "context_group_id",
    "contract_title",
    "contract_type",
    "contract_type_confidence",
    "category_id",
    "category_name",
    "paragraph_index",
    "answer_start",
    "answer_end",
    "model_input_text",
    "severity_ordinal",
    "target_risk_band",
    "label_confidence",
    "exact_text_seen_in_train",
    "use_for_model_fit",
    "use_for_model_validation",
    "target_name",
    "target_provenance",
]

CATEGORY_TRAINING_FIELDS = [
    "assessment_id",
    "contract_id",
    "source_contract_id",
    "source_partition",
    "source_index",
    "split",
    "context_group_id",
    "contract_title",
    "contract_type",
    "contract_type_confidence",
    "category_id",
    "category_name",
    "presence_status",
    "finding_kind",
    "finding_count",
    "evidence_count",
    "model_input_text",
    "severity_ordinal",
    "target_risk_band",
    "label_confidence",
    "exact_text_seen_in_train",
    "use_for_model_fit",
    "use_for_model_validation",
    "target_name",
    "target_provenance",
]

_CONTRACT_TYPE_PATTERNS = (
    (
        "employment",
        re.compile(r"\b(?:employment|employee|executive|severance)\b", re.I),
    ),
    (
        "confidentiality",
        re.compile(r"\b(?:confidentiality|non[- ]?disclosure|nda)\b", re.I),
    ),
    (
        "software_license",
        re.compile(r"\b(?:software|saas|cloud subscription)\b", re.I),
    ),
    ("license", re.compile(r"\b(?:licen[cs]e|licensing)\b", re.I)),
    (
        "services",
        re.compile(
            r"\b(?:master services?|professional services?|services? agreement|"
            r"consulting|outsourcing)\b",
            re.I,
        ),
    ),
    (
        "distribution",
        re.compile(r"\b(?:distribut(?:or|ion)|reseller|dealer)\b", re.I),
    ),
    (
        "merger_acquisition",
        re.compile(
            r"\b(?:merger|acquisition|asset purchase|stock purchase|share purchase)\b",
            re.I,
        ),
    ),
    (
        "supply",
        re.compile(r"\b(?:supply|supplier|purchase|procurement|vendor)\b", re.I),
    ),
    ("lease", re.compile(r"\b(?:lease|leasing|rental)\b", re.I)),
    ("franchise", re.compile(r"\bfranchis(?:e|ing)\b", re.I)),
    (
        "collaboration",
        re.compile(r"\b(?:joint venture|collaboration|strategic alliance)\b", re.I),
    ),
    (
        "marketing",
        re.compile(r"\b(?:marketing|advertising|endorsement|sponsorship)\b", re.I),
    ),
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_sha256(output_dir: Path) -> dict[str, str]:
    return {
        relative_path: _file_sha256(output_dir / relative_path)
        for relative_path in PACKAGE_CONTENT_FILES
        if (output_dir / relative_path).is_file()
    }


def _clean_split_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return "" if text.lower() == "nan" else text


def _read_split_rows(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [
                {key: _clean_split_value(value) for key, value in row.items()}
                for row in csv.DictReader(handle)
            ]
    if suffix in {".parquet", ".pq"}:
        try:
            import pandas as pd
        except ImportError as error:  # pragma: no cover - runtime dependency
            raise RuntimeError(
                "Reading a Parquet split map requires pandas and pyarrow"
            ) from error
        try:
            frame = pd.read_parquet(path)
        except ImportError as error:  # pragma: no cover - runtime dependency
            raise RuntimeError(
                "Reading a Parquet split map requires a Parquet engine such as pyarrow"
            ) from error
        return [
            {key: _clean_split_value(value) for key, value in row.items()}
            for row in frame.to_dict(orient="records")
        ]
    raise ValueError("Split map must be CSV or Parquet")


def _split_indexes(
    rows: Iterable[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_context_group: dict[str, dict[str, str]] = {}
    by_contract: dict[str, dict[str, str]] = {}
    for row in rows:
        split = row.get("split", "")
        if split not in {"train", "validation"}:
            raise ValueError(f"Unexpected frozen split value: {split!r}")
        context_group_id = row.get("context_group_id", "")
        contract_id = row.get("contract_id", "")
        if not context_group_id and not contract_id:
            raise ValueError(
                "Each split-map row needs context_group_id or contract_id"
            )
        if context_group_id:
            existing = by_context_group.get(context_group_id)
            if existing is not None and existing["split"] != split:
                raise ValueError(
                    f"Context group appears in multiple splits: {context_group_id}"
                )
            by_context_group[context_group_id] = row
        if contract_id:
            existing = by_contract.get(contract_id)
            if existing is not None and existing["split"] != split:
                raise ValueError(f"Contract appears in multiple splits: {contract_id}")
            by_contract[contract_id] = row
    return by_context_group, by_contract


def _contract_text(document: dict[str, Any]) -> str:
    return "\n\n".join(
        str(paragraph.get("context", ""))
        for paragraph in document.get("paragraphs", [])
    )


def _context_group_id(text: str) -> str:
    # This is the exact grouping key used by the repository's frozen split.
    return "context_" + hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def _category_name(qa: dict[str, Any]) -> str:
    question = str(qa.get("question", ""))
    if '"' in question:
        parts = question.split('"')
        if len(parts) >= 3:
            return parts[1]
    qa_id = str(qa.get("id", ""))
    if "__" in qa_id:
        remainder = qa_id.rsplit("__", 1)[1]
        return remainder.rsplit("_", 1)[0]
    return ""


def _normalize_category_id(value: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "_" for character in value
    )
    return "_".join(part for part in normalized.split("_") if part)


def _infer_contract_type(title: str) -> str:
    searchable_title = re.sub(r"[_-]+", " ", title)
    for contract_type, pattern in _CONTRACT_TYPE_PATTERNS:
        if pattern.search(searchable_title):
            return contract_type
    return "unknown"


def _answer_records_by_category(
    document: dict[str, Any],
    category_ids: set[str],
) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {
        category_id: [] for category_id in category_ids
    }
    for paragraph_index, paragraph in enumerate(document.get("paragraphs", [])):
        context = str(paragraph.get("context", ""))
        for qa_index, qa in enumerate(paragraph.get("qas", [])):
            category_id = _normalize_category_id(_category_name(qa))
            if category_id not in category_ids:
                continue
            for answer_index, answer in enumerate(qa.get("answers", [])):
                answer_text = str(answer.get("text", ""))
                if not answer_text.strip():
                    continue
                raw_start = answer.get("answer_start")
                try:
                    answer_start = int(raw_start)
                except (TypeError, ValueError):
                    answer_start = context.find(answer_text)
                if answer_start < 0:
                    raise ValueError(
                        f"Answer text for QA {qa.get('id', '')!r} has no valid offset"
                    )
                answer_end = answer_start + len(answer_text)
                records[category_id].append(
                    {
                        "qa_id": str(qa.get("id", "")),
                        "qa_index": qa_index,
                        "paragraph_index": paragraph_index,
                        "answer_index": answer_index,
                        "answer_start": answer_start,
                        "answer_end": answer_end,
                        "answer_text": answer_text,
                        "_context": context,
                    }
                )
    return records


def _consolidate_answer_records(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered = sorted(
        records,
        key=lambda row: (
            row["paragraph_index"],
            row["answer_start"],
            row["answer_end"],
            row["qa_id"],
            row["answer_index"],
        ),
    )
    clusters: list[list[dict[str, Any]]] = []
    cluster_end = -1
    cluster_paragraph = -1
    for record in ordered:
        same_paragraph = record["paragraph_index"] == cluster_paragraph
        is_nearby = record["answer_start"] <= (
            cluster_end + MAX_SAME_FINDING_GAP_CHARS
        )
        if clusters and same_paragraph and is_nearby:
            clusters[-1].append(record)
            cluster_end = max(cluster_end, record["answer_end"])
        else:
            clusters.append([record])
            cluster_paragraph = record["paragraph_index"]
            cluster_end = record["answer_end"]

    findings: list[dict[str, Any]] = []
    for cluster in clusters:
        answer_start = min(record["answer_start"] for record in cluster)
        answer_end = max(record["answer_end"] for record in cluster)
        context = cluster[0]["_context"]
        provenance = [
            {key: value for key, value in record.items() if key != "_context"}
            for record in cluster
        ]
        findings.append(
            {
                "paragraph_index": cluster[0]["paragraph_index"],
                "answer_start": answer_start,
                "answer_end": answer_end,
                "evidence_text": context[answer_start:answer_end],
                "provenance": provenance,
            }
        )
    return findings


def _issue_family_id(category: dict[str, Any], contract_id: str) -> str:
    template = str(category.get("issue_family_template") or category["category_id"])
    try:
        return template.format(
            contract_id=contract_id,
            category_id=category["category_id"],
        )
    except (KeyError, ValueError):
        return template


def _assessment_fields(assessment: FindingAssessment) -> dict[str, Any]:
    return {
        "severity_ordinal": assessment.severity_ordinal,
        "risk_band": assessment.risk_band,
        "direction": assessment.direction,
        "confidence": assessment.confidence,
        "label_status": assessment.label_status,
        "applicability": assessment.applicability,
        "trigger_ids": list(assessment.trigger_ids),
        "source_ids": list(assessment.source_ids),
        "rationale": assessment.rationale,
    }


def _choose_category_assessment(
    assessments: list[FindingAssessment],
) -> FindingAssessment:
    """Select the most urgent finding without mixing separate provisions."""

    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    status_rank = {
        "weak_not_applicable": 0,
        "weak_abstain": 1,
        "weak_automatic": 2,
    }
    return max(
        assessments,
        key=lambda assessment: (
            -1
            if assessment.severity_ordinal is None
            else assessment.severity_ordinal,
            status_rank.get(assessment.label_status, 0),
            confidence_rank.get(assessment.confidence, 0),
        ),
    )


def _finding_kind(
    presence_status: str,
    assessment: FindingAssessment,
) -> str:
    if assessment.label_status == "weak_not_applicable":
        return "not_applicable"
    if assessment.label_status == "weak_abstain":
        return "ambiguity"
    if presence_status == "absent":
        return "expected_but_missing"
    return "present_clause"


def _usage_fields(
    split: str,
    assessment: FindingAssessment,
) -> dict[str, bool]:
    target_available = assessment.severity_ordinal is not None
    return {
        "supervised_target_available": target_available,
        "use_for_model_fit": split == "train" and target_available,
        "use_for_model_validation": split == "validation" and target_available,
    }


def _three_class_risk_band(severity_ordinal: int) -> str:
    """Map the internal four-step scale to the challenge's three bands."""

    if severity_ordinal in {0, 1}:
        return "low"
    if severity_ordinal == 2:
        return "medium"
    if severity_ordinal == 3:
        return "high"
    raise ValueError(f"Unsupported severity ordinal: {severity_ordinal}")


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            serializable = dict(row)
            for field in (
                "finding_ids",
                "trigger_ids",
                "source_ids",
                "triggering_assessment_ids",
                "triggering_domains",
                "unresolved_required_categories",
            ):
                if field in serializable and isinstance(
                    serializable[field], (list, tuple)
                ):
                    serializable[field] = json.dumps(
                        serializable[field], ensure_ascii=False
                    )
            writer.writerow(serializable)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sorted_counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _normalized_evidence_key(category_id: str, text: str) -> tuple[str, str]:
    return category_id, " ".join(text.split()).casefold()


def build_dataset(
    *,
    train_json: Path,
    test_json: Path,
    split_map: Path,
    rule_cards: Path,
    output_dir: Path,
) -> None:
    config = _read_json(rule_cards)
    categories = list(config["categories"])
    category_ids = [str(category["category_id"]) for category in categories]
    if len(category_ids) != len(set(category_ids)):
        raise ValueError("Rule-card configuration contains duplicate category IDs")
    cards_by_id = {str(category["category_id"]): category for category in categories}

    splits_by_context, splits_by_contract = _split_indexes(
        _read_split_rows(split_map)
    )

    contracts: list[dict[str, Any]] = []
    raw_documents = (
        ("train", _read_json(train_json).get("data", [])),
        ("test", _read_json(test_json).get("data", [])),
    )
    for partition, documents in raw_documents:
        for source_index, document in enumerate(documents, start=1):
            source_contract_id = f"contract_{source_index:04d}"
            paragraphs = [
                str(paragraph.get("context", ""))
                for paragraph in document.get("paragraphs", [])
            ]
            text = _contract_text(document)
            derived_context_group_id = _context_group_id(text)
            if partition == "train":
                split_row = splits_by_context.get(derived_context_group_id)
                if split_row is None:
                    split_row = splits_by_contract.get(source_contract_id)
                if split_row is None:
                    raise ValueError(
                        "Missing frozen split for "
                        f"{source_contract_id}/{derived_context_group_id}"
                    )
                split = split_row["split"]
                context_group_id = (
                    split_row.get("context_group_id") or derived_context_group_id
                )
            else:
                split = "official_test"
                context_group_id = derived_context_group_id

            title = str(document.get("title", ""))
            contract_type = _infer_contract_type(title)
            contracts.append(
                {
                    "contract_id": f"cuad_{partition}_{source_index:04d}",
                    "source_contract_id": source_contract_id,
                    "source_partition": partition,
                    "source_index": source_index,
                    "split": split,
                    "context_group_id": context_group_id,
                    "title": title,
                    "contract_type": contract_type,
                    "contract_type_confidence": (
                        "low" if contract_type == "unknown" else "high"
                    ),
                    "paragraphs": paragraphs,
                    "text": text,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "answer_records": _answer_records_by_category(
                        document, set(category_ids)
                    ),
                }
            )

    clause_findings: list[dict[str, Any]] = []
    category_rows: list[dict[str, Any]] = []
    category_rows_by_contract: dict[str, list[dict[str, Any]]] = {}
    for contract in contracts:
        contract_category_rows: list[dict[str, Any]] = []
        consolidated_by_category = {
            category_id: _consolidate_answer_records(
                contract["answer_records"].get(category_id, [])
            )
            for category_id in category_ids
        }
        revenue_evidence = "\n\n".join(
            finding["evidence_text"]
            for finding in consolidated_by_category.get(
                "revenue_profit_sharing", []
            )
        )
        for category in categories:
            category_id = str(category["category_id"])
            issue_family_id = _issue_family_id(category, contract["contract_id"])
            if category_id == "audit_rights" and revenue_evidence:
                issue_family_id = "revenue_verification"
            risk_domain = str(category.get("risk_domain") or category_id)
            consolidated = consolidated_by_category[category_id]
            finding_ids: list[str] = []
            finding_assessments: list[FindingAssessment] = []
            for finding_index, finding in enumerate(consolidated, start=1):
                finding_id = (
                    f"{contract['contract_id']}:{category_id}:{finding_index:03d}"
                )
                finding_ids.append(finding_id)
                assessment = score_finding(
                    rule_cards=cards_by_id,
                    category_id=category_id,
                    presence_status="present",
                    evidence_text=finding["evidence_text"],
                    contract_type=contract["contract_type"],
                )
                finding_assessments.append(assessment)
                unresolved_material = (
                    assessment.label_status == "weak_abstain"
                    and assessment.material_if_unresolved
                )
                clause_findings.append(
                    {
                        "finding_id": finding_id,
                        "contract_id": contract["contract_id"],
                        "source_contract_id": contract["source_contract_id"],
                        "source_partition": contract["source_partition"],
                        "source_index": contract["source_index"],
                        "split": contract["split"],
                        "context_group_id": contract["context_group_id"],
                        "contract_title": contract["title"],
                        "contract_type": contract["contract_type"],
                        "contract_type_confidence": contract[
                            "contract_type_confidence"
                        ],
                        "category_id": category_id,
                        "category_name": category["category_name"],
                        "rule_card_id": category.get("rule_card_id", ""),
                        "review_bundle_id": category.get("review_bundle_id", ""),
                        "risk_domain": risk_domain,
                        "issue_family_id": issue_family_id,
                        "presence_status": "present",
                        "finding_kind": _finding_kind("present", assessment),
                        "unresolved_material": unresolved_material,
                        **_usage_fields(contract["split"], assessment),
                        **finding,
                        **_assessment_fields(assessment),
                    }
                )

            presence_status = "present" if consolidated else "absent"
            evidence_text = "\n\n--- DISTINCT CLAUSE FINDING ---\n\n".join(
                finding["evidence_text"] for finding in consolidated
            )
            if finding_assessments:
                category_assessment = _choose_category_assessment(
                    finding_assessments
                )
            else:
                scoring_context = (
                    revenue_evidence if category_id == "audit_rights" else ""
                )
                category_assessment = score_finding(
                    rule_cards=cards_by_id,
                    category_id=category_id,
                    presence_status=presence_status,
                    evidence_text=scoring_context,
                    contract_type=contract["contract_type"],
                )
            unresolved_material = any(
                assessment.label_status == "weak_abstain"
                and assessment.material_if_unresolved
                for assessment in (
                    finding_assessments or [category_assessment]
                )
            )
            category_row = {
                "assessment_id": f"{contract['contract_id']}:{category_id}",
                "contract_id": contract["contract_id"],
                "source_contract_id": contract["source_contract_id"],
                "source_partition": contract["source_partition"],
                "source_index": contract["source_index"],
                "split": contract["split"],
                "context_group_id": contract["context_group_id"],
                "contract_title": contract["title"],
                "contract_type": contract["contract_type"],
                "contract_type_confidence": contract[
                    "contract_type_confidence"
                ],
                "category_id": category_id,
                "category_name": category["category_name"],
                "rule_card_id": category.get("rule_card_id", ""),
                "review_bundle_id": category.get("review_bundle_id", ""),
                "risk_domain": risk_domain,
                "issue_family_id": issue_family_id,
                "presence_status": presence_status,
                "finding_kind": _finding_kind(
                    presence_status, category_assessment
                ),
                "finding_count": len(consolidated),
                "finding_ids": finding_ids,
                "evidence_count": sum(
                    len(finding["provenance"]) for finding in consolidated
                ),
                "evidence_text": evidence_text,
                "unresolved_material": unresolved_material,
                **_usage_fields(contract["split"], category_assessment),
                "contract_text_sha256": contract["text_sha256"],
                **_assessment_fields(category_assessment),
            }
            category_rows.append(category_row)
            contract_category_rows.append(category_row)
        category_rows_by_contract[contract["contract_id"]] = contract_category_rows

    contract_rows: list[dict[str, Any]] = []
    for contract in contracts:
        contract_category_assessments = category_rows_by_contract[
            contract["contract_id"]
        ]
        rollup_inputs = [
            {
                "finding_id": row["assessment_id"],
                "severity_ordinal": row["severity_ordinal"],
                "risk_domain": row["risk_domain"],
                "issue_family_id": row["issue_family_id"],
                "unresolved_material": row["unresolved_material"],
            }
            for row in contract_category_assessments
        ]
        rollup = roll_up_contract(rollup_inputs)
        unresolved_required_categories = sorted(
            row["category_id"]
            for row in contract_category_assessments
            if row["unresolved_material"]
        )
        contract_rows.append(
            {
                "contract_id": contract["contract_id"],
                "source_contract_id": contract["source_contract_id"],
                "source_partition": contract["source_partition"],
                "source_index": contract["source_index"],
                "split": contract["split"],
                "context_group_id": contract["context_group_id"],
                "contract_title": contract["title"],
                "contract_type": contract["contract_type"],
                "contract_type_confidence": contract[
                    "contract_type_confidence"
                ],
                "rule_contract_risk_band": rollup.risk_band,
                "rule_contract_risk_ordinal": rollup.risk_ordinal,
                "rule_contract_review_priority_band": (
                    rollup.review_priority_band
                ),
                "rule_contract_review_priority_ordinal": (
                    rollup.review_priority_ordinal
                ),
                "rule_label_status": "weak_rule_rollup",
                "rollup_policy_id": "buyer_risk_rollup",
                "triggering_assessment_ids": list(rollup.triggering_finding_ids),
                "triggering_domains": list(rollup.triggering_domains),
                "unresolved_required_categories": (
                    unresolved_required_categories
                ),
                "rationale": rollup.rationale,
                # These are policy-derived rule outputs, not human labels.
                # Preserve them for analysis without advertising them as a
                # fit-ready direct contract target.
                "use_for_model_fit": False,
                "use_for_model_validation": False,
                "contract_text_sha256": contract["text_sha256"],
            }
        )

    numeric_development_findings = [
        finding
        for finding in clause_findings
        if finding["split"] in {"train", "validation"}
        and finding["severity_ordinal"] is not None
    ]
    train_evidence_keys = {
        _normalized_evidence_key(
            str(finding["category_id"]), str(finding["evidence_text"])
        )
        for finding in numeric_development_findings
        if finding["split"] == "train"
    }
    risk_training_examples = []
    for finding in numeric_development_findings:
        evidence_key = _normalized_evidence_key(
            str(finding["category_id"]), str(finding["evidence_text"])
        )
        risk_training_examples.append(
            {
                "example_id": finding["finding_id"],
                "finding_id": finding["finding_id"],
                "contract_id": finding["contract_id"],
                "source_contract_id": finding["source_contract_id"],
                "source_partition": finding["source_partition"],
                "source_index": finding["source_index"],
                "split": finding["split"],
                "context_group_id": finding["context_group_id"],
                "contract_title": finding["contract_title"],
                "contract_type": finding["contract_type"],
                "contract_type_confidence": finding[
                    "contract_type_confidence"
                ],
                "category_id": finding["category_id"],
                "category_name": finding["category_name"],
                "paragraph_index": finding["paragraph_index"],
                "answer_start": finding["answer_start"],
                "answer_end": finding["answer_end"],
                "model_input_text": finding["evidence_text"],
                "severity_ordinal": finding["severity_ordinal"],
                "target_risk_band": _three_class_risk_band(
                    int(finding["severity_ordinal"])
                ),
                "label_confidence": finding["confidence"],
                "exact_text_seen_in_train": (
                    finding["split"] == "validation"
                    and evidence_key in train_evidence_keys
                ),
                "use_for_model_fit": finding["split"] == "train",
                "use_for_model_validation": finding["split"] == "validation",
                "target_name": "severity_ordinal",
                "target_provenance": TARGET_PROVENANCE,
            }
        )
    numeric_development_category_rows = [
        row
        for row in category_rows
        if row["split"] in {"train", "validation"}
        and row["severity_ordinal"] is not None
    ]
    train_category_evidence_keys = {
        _normalized_evidence_key(
            str(row["category_id"]), str(row["evidence_text"])
        )
        for row in numeric_development_category_rows
        if row["split"] == "train" and str(row["evidence_text"]).strip()
    }
    category_training_examples = []
    for row in numeric_development_category_rows:
        category_evidence_key = _normalized_evidence_key(
            str(row["category_id"]), str(row["evidence_text"])
        )
        category_training_examples.append({
            "assessment_id": row["assessment_id"],
            "contract_id": row["contract_id"],
            "source_contract_id": row["source_contract_id"],
            "source_partition": row["source_partition"],
            "source_index": row["source_index"],
            "split": row["split"],
            "context_group_id": row["context_group_id"],
            "contract_title": row["contract_title"],
            "contract_type": row["contract_type"],
            "contract_type_confidence": row["contract_type_confidence"],
            "category_id": row["category_id"],
            "category_name": row["category_name"],
            "presence_status": row["presence_status"],
            "finding_kind": row["finding_kind"],
            "finding_count": row["finding_count"],
            "evidence_count": row["evidence_count"],
            "model_input_text": row["evidence_text"],
            "severity_ordinal": row["severity_ordinal"],
            "target_risk_band": _three_class_risk_band(
                int(row["severity_ordinal"])
            ),
            "label_confidence": row["confidence"],
            "exact_text_seen_in_train": (
                row["split"] == "validation"
                and bool(str(row["evidence_text"]).strip())
                and category_evidence_key in train_category_evidence_keys
            ),
            "use_for_model_fit": row["split"] == "train",
            "use_for_model_validation": row["split"] == "validation",
            "target_name": "severity_ordinal",
            "target_provenance": TARGET_PROVENANCE,
        })

    review_rows: list[dict[str, Any]] = []
    for contract in contracts:
        if contract["split"] != "official_test":
            continue
        for reviewer_slot in (1, 2):
            review_rows.append(
                {
                    "contract_id": contract["contract_id"],
                    "source_contract_id": contract["source_contract_id"],
                    "source_partition": contract["source_partition"],
                    "source_index": contract["source_index"],
                    "split": contract["split"],
                    "context_group_id": contract["context_group_id"],
                    "contract_title": contract["title"],
                    "contract_type": contract["contract_type"],
                    "contract_type_confidence": contract[
                        "contract_type_confidence"
                    ],
                    "contract_text_sha256": contract["text_sha256"],
                    "reviewer_slot": reviewer_slot,
                    "reviewer_id": "",
                    "human_risk_band": "",
                    "human_risk_ordinal": "",
                    "human_confidence": "",
                    "human_rationale": "",
                    "reviewed_at": "",
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    contract_text_rows = [
        {
            "contract_id": contract["contract_id"],
            "source_contract_id": contract["source_contract_id"],
            "source_partition": contract["source_partition"],
            "source_index": contract["source_index"],
            "split": contract["split"],
            "context_group_id": contract["context_group_id"],
            "contract_title": contract["title"],
            "contract_type": contract["contract_type"],
            "contract_type_confidence": contract["contract_type_confidence"],
            "paragraphs": contract["paragraphs"],
            "contract_text": contract["text"],
            "contract_text_sha256": contract["text_sha256"],
        }
        for contract in contracts
    ]
    _write_jsonl(output_dir / "contracts.jsonl", contract_text_rows)
    _write_jsonl(output_dir / "clause_findings.jsonl", clause_findings)
    _write_jsonl(
        output_dir / "risk_training_examples.jsonl",
        risk_training_examples,
    )
    _write_csv(output_dir / "category_assessments.csv", CATEGORY_FIELDS, category_rows)
    _write_csv(
        output_dir / "category_training_examples.csv",
        CATEGORY_TRAINING_FIELDS,
        category_training_examples,
    )
    _write_csv(output_dir / "contract_assessments.csv", CONTRACT_FIELDS, contract_rows)
    _write_csv(
        output_dir / "review" / "official_test_reference_template.csv",
        REVIEW_TEMPLATE_FIELDS,
        review_rows,
    )

    input_hashes = {
        "train_json": _file_sha256(train_json),
        "test_json": _file_sha256(test_json),
        "split_map": _file_sha256(split_map),
        "rule_cards": _file_sha256(rule_cards),
    }
    source_registry_path = rule_cards.with_name("source_registry.json")
    if source_registry_path.is_file():
        input_hashes["source_registry"] = _file_sha256(source_registry_path)

    manifest = {
        "dataset_name": config["dataset_name"],
        "category_ids": sorted(category_ids),
        "category_order": category_ids,
        "parameters": {
            "same_finding_max_gap_chars": MAX_SAME_FINDING_GAP_CHARS,
            "frozen_split_grouping": "context_ + md5(unchanged_context_utf8)[:10]",
            "official_test_reviewer_slots": 2,
        },
        "generator": generator_fingerprint(),
        "input_sha256": input_hashes,
        "package_sha256": _package_sha256(output_dir),
        "counts": {
            "contracts": len(contracts),
            "contract_texts": len(contract_text_rows),
            "clause_findings": len(clause_findings),
            "source_answer_spans": sum(
                int(row["evidence_count"]) for row in category_rows
            ),
            "category_assessments": len(category_rows),
            "contract_assessments": len(contract_rows),
            "risk_training_examples": len(risk_training_examples),
            "category_training_examples": len(category_training_examples),
            "reference_template_rows": len(review_rows),
        },
        "distributions": {
            "contracts_by_split": _sorted_counts(
                contract["split"] for contract in contracts
            ),
            "contracts_by_type": _sorted_counts(
                contract["contract_type"] for contract in contracts
            ),
            "clause_findings_by_category": _sorted_counts(
                finding["category_id"] for finding in clause_findings
            ),
            "category_assessments_by_presence": _sorted_counts(
                row["presence_status"] for row in category_rows
            ),
            "category_assessments_by_risk_band": _sorted_counts(
                row["risk_band"] for row in category_rows
            ),
            "contract_assessments_by_risk_band": _sorted_counts(
                row["rule_contract_risk_band"] for row in contract_rows
            ),
            "contract_assessments_by_review_priority_band": _sorted_counts(
                row["rule_contract_review_priority_band"]
                for row in contract_rows
            ),
            "risk_training_examples_by_split": _sorted_counts(
                row["split"] for row in risk_training_examples
            ),
            "risk_training_examples_by_severity": _sorted_counts(
                str(row["severity_ordinal"])
                for row in risk_training_examples
            ),
            "risk_training_examples_by_target_risk_band": _sorted_counts(
                row["target_risk_band"] for row in risk_training_examples
            ),
            "development_clause_findings_by_label_status": _sorted_counts(
                finding["label_status"]
                for finding in clause_findings
                if finding["split"] in {"train", "validation"}
            ),
            "risk_training_examples_by_label_confidence": _sorted_counts(
                row["label_confidence"] for row in risk_training_examples
            ),
            "category_training_examples_by_split": _sorted_counts(
                row["split"] for row in category_training_examples
            ),
            "category_training_examples_by_severity": _sorted_counts(
                str(row["severity_ordinal"])
                for row in category_training_examples
            ),
            "category_training_examples_by_target_risk_band": _sorted_counts(
                row["target_risk_band"]
                for row in category_training_examples
            ),
        },
        "quality": {
            "development_clause_findings": sum(
                finding["split"] in {"train", "validation"}
                for finding in clause_findings
            ),
            "numeric_development_clause_findings": len(
                risk_training_examples
            ),
            "numeric_development_clause_coverage": round(
                len(risk_training_examples)
                / max(
                    1,
                    sum(
                        finding["split"] in {"train", "validation"}
                        for finding in clause_findings
                    ),
                ),
                6,
            ),
            "validation_examples_with_exact_train_text": sum(
                row["exact_text_seen_in_train"]
                for row in risk_training_examples
            ),
            "validation_category_examples_with_exact_train_text": sum(
                row["exact_text_seen_in_train"]
                for row in category_training_examples
            ),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
