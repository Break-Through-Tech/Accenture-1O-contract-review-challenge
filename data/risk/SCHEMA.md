# Data schema

## Formats and nulls

- JSONL files contain one JSON object per line and preserve booleans, numbers, arrays, and nulls.
- CSV booleans are serialized as `True` or `False`.
- List-valued CSV cells such as `finding_ids`, `trigger_ids`, and `source_ids` contain JSON arrays; parse them with a JSON parser.
- Empty CSV cells represent unavailable or inapplicable values. Do not convert every empty field to zero.
- `severity_ordinal` is internal. Use `target_risk_band` as the three-class supervised target.

## Common identifiers and provenance

| Field | Meaning |
|---|---|
| `contract_id` | Package-wide unique contract identifier; use this for joins. |
| `source_contract_id` | Identifier within the original CUAD partition; not guaranteed package-wide unique. |
| `source_partition` | Original CUAD source file: `train` or `test`. |
| `source_index` | One-based document position within the original source partition. |
| `split` | Package ML split: `train`, `validation`, or `official_test`. |
| `context_group_id` | Groups duplicate/equivalent contract contexts for leakage control. |
| `contract_text_sha256` | Hash of the complete `contract_text` bundled in `contracts.jsonl`. |
| `contract_title` | Source contract title. |
| `contract_type` | Contract type inferred conservatively from the title. |
| `contract_type_confidence` | `high` when a title pattern matched; otherwise `low`. |
| `category_id`, `category_name` | Stable machine ID and display name for the CUAD category. |

## Contract text

### `contracts.jsonl`

One row per contract for all three package splits. This is the source-text table fellows can use for chunking, full-contract review, and evidence verification.

| Field | Meaning |
|---|---|
| `contract_id` | Join key used throughout this package. |
| `paragraphs` | Original CUAD paragraph contexts in source order. |
| `contract_text` | Complete contract text, formed by joining `paragraphs` with two newline characters. |
| `contract_text_sha256` | SHA-256 of UTF-8 `contract_text`; use it to verify text identity and prevent split leakage. |

The remaining fields are the common identifiers and contract metadata described above.

## Training files

### `risk_training_examples.jsonl`

One row per numeric present-clause finding from train or validation. This is the most direct text-classification view.

| Field | Meaning |
|---|---|
| `example_id`, `finding_id` | Unique example ID and join key to `clause_findings.jsonl`. |
| `paragraph_index` | Zero-based index into the matching contract's `paragraphs` array in `contracts.jsonl`. |
| `answer_start`, `answer_end` | Character offsets in `paragraphs[paragraph_index]`; end is exclusive. |
| `model_input_text` | Clause/finding text supplied to a severity model. |
| `severity_ordinal` | Internal numeric target: 0–3. |
| `target_risk_band` | Required three-class target: `low`, `medium`, or `high`. |
| `label_confidence` | Weak-label confidence metadata; do not use as a feature. |
| `exact_text_seen_in_train` | For validation rows, whether normalized same-category text also occurs in train. |
| `use_for_model_fit` | True only for training rows. |
| `use_for_model_validation` | True only for validation rows. |
| `target_name` | Name of the internal numeric target. |
| `target_provenance` | Identifies the target as a research-derived weak rule. |

### `category_training_examples.csv`

One numeric contract-category state per train/validation contract and selected category when a target is available. This view can represent expected-but-missing protection as well as present text.

Additional fields:

| Field | Meaning |
|---|---|
| `assessment_id` | Join key to `category_assessments.csv`. |
| `presence_status` | Whether CUAD annotated the category as present or absent. |
| `finding_kind` | Present clause, expected missing protection, ambiguity, or conflict. |
| `finding_count` | Number of consolidated findings represented by the category row. |
| `evidence_count` | Number of original CUAD answer spans represented. |
| `model_input_text` | Consolidated evidence; blank for missing-protection states. |

The remaining target, confidence, duplicate, and fit flags have the same meanings as in the clause training file.

## Audit files

### `clause_findings.jsonl`

Full finding-level audit table for all splits, including numeric findings and abstentions. It is not a clean feature matrix.

| Field group | Fields and meaning |
|---|---|
| Finding identity | `finding_id`, `finding_kind`, `presence_status` |
| Source location | `paragraph_index`, `answer_start`, `answer_end`, `provenance`; offsets resolve against the matching row in `contracts.jsonl` |
| Evidence | `evidence_text` and the original answer records in `provenance` |
| Rubric structure | `rule_card_id`, `review_bundle_id`, `risk_domain`, `issue_family_id` |
| Audit label | `severity_ordinal`, `risk_band`, `direction`, `confidence`, `label_status`, `applicability` |
| Explanation | `trigger_ids`, `source_ids`, `rationale` |
| Uncertainty | `unresolved_material`, `supervised_target_available` |
| Usage flags | `use_for_model_fit`, `use_for_model_validation` |

`risk_band` in audit files can be `none`, `low`, `medium`, `high`, `unresolved`, or `not_applicable`. It is not the same field as the three-class `target_risk_band`.

### `category_assessments.csv`

Exactly one row per contract × selected category: 510 × 10 = 5,100 rows. It aggregates finding-level evidence and also represents category absence.

Additional fields include `assessment_id`, `finding_count`, `finding_ids`, `evidence_count`, `evidence_text`, and the same rubric/audit/usage fields described above. A row can have a numeric maximum severity and `unresolved_material=True` when another finding in the same category abstained.

### `contract_assessments.csv`

One deterministic rollup row per contract. This file is for analysis, explanation, and optional rule-distillation experiments; it is not an independent training target.

| Field | Meaning |
|---|---|
| `rule_contract_risk_band`, `rule_contract_risk_ordinal` | Evidence-based Low/Medium/High contract rollup and 1–3 ordinal. |
| `rule_contract_review_priority_band`, `rule_contract_review_priority_ordinal` | Uncertainty-aware review priority; may exceed the risk band when material items are unresolved. |
| `rule_label_status` | Identifies the row as a weak deterministic rollup. |
| `rollup_policy_id` | Stable identifier for the included rollup policy. |
| `triggering_assessment_ids` | Category assessment IDs that determine risk or review priority. |
| `triggering_domains` | Distinct risk domains represented by the triggers. |
| `unresolved_required_categories` | Material categories needing review. |
| `rationale` | Short explanation of the rollup. |
| `use_for_model_fit`, `use_for_model_validation` | Always False by design. |

## Review template

### `review/official_test_reference_template.csv`

Two blank reviewer rows per official-test contract. Contract identifiers and provenance fields are prefilled; `reviewer_id`, `human_risk_band`, `human_risk_ordinal`, `human_confidence`, `human_rationale`, and `reviewed_at` are intentionally blank. See [`review/README.md`](review/README.md) before use.

## Supporting metadata

- [`rule_cards.json`](rule_cards.json) contains category applicability, ordered matching rules, severity, direction, confidence, rationale, and source IDs.
- [`source_registry.json`](source_registry.json) resolves every source ID and states each source's scope and limitations.
- [`manifest.json`](manifest.json) records counts, distributions, build parameters, upstream-input fingerprints, an aggregate generator-implementation fingerprint, and hashes for every other file in this package.
