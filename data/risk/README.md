# CUAD buyer-side risk-label data

This folder is a self-contained data handoff for the ten CUAD categories selected by the team. It supplies research-derived weak labels for Low/Medium/High procurement triage. It does not supply a classifier, chunking pipeline, trained model, notebook solution, or application.

The labels are not expert legal judgments, legal advice, enforceability decisions, or proof that a contract is safe to sign. CUAD's expert provenance applies to the source clause spans and categories; the risk ratings were added using the documented buyer-side rubric included here.

## Start here

| Goal | File | How to use it |
|---|---|---|
| Read contracts, create chunks, or verify clause offsets | [`contracts.jsonl`](contracts.jsonl) | Contains all 510 complete contract texts plus their original paragraph boundaries and package split assignments. Join on `contract_id`. |
| Experiment with present-clause severity classification | [`risk_training_examples.jsonl`](risk_training_examples.jsonl) | Use `model_input_text` as text and `target_risk_band` as the target. Fit only rows where `use_for_model_fit=true`; High has only one example and is not learnable from this view alone. |
| Primary three-band structured experiments | [`category_training_examples.csv`](category_training_examples.csv) | Use category, presence, contract type, and text together. This view includes missing-protection states; its High class is mostly missing-cap states rather than diverse High clause text. |
| Audit how labels were produced | [`clause_findings.jsonl`](clause_findings.jsonl), [`category_assessments.csv`](category_assessments.csv), and [`rule_cards.json`](rule_cards.json) | These retain rationales, rule triggers, confidence, applicability, and provenance. Do not use target-derived audit fields as model features. |
| Inspect contract-level rule outputs | [`contract_assessments.csv`](contract_assessments.csv) | Analysis only. Every row is marked non-fit-ready because these are deterministic policy outputs, not independent human labels. |
| Understand every field | [`SCHEMA.md`](SCHEMA.md) | Read before loading the tables. |
| Understand the selected CUAD categories | [`CATEGORY_DEFINITIONS.md`](CATEGORY_DEFINITIONS.md) | Contains the ten category scopes used by this package. |
| Understand the labeling assumptions | [`METHODOLOGY.md`](METHODOLOGY.md) | Explains the perspective, scale, rollup, provenance, and limitations. |
| Create an optional team reference set | [`review/README.md`](review/README.md) | The included template is blank; no human-reviewed risk labels are supplied. |

## Snapshot

| Item | Count |
|---|---:|
| Contracts | 510 |
| Train / validation / official-test contracts | 325 / 83 / 102 |
| Contract-category assessments | 5,100 |
| Consolidated clause findings | 3,517 |
| Original CUAD answer spans retained in provenance | 4,661 |
| Numeric clause-level training examples | 1,962 |
| Numeric category-state training examples | 1,801 |
| Blank official-test reviewer rows | 204 |

Clause training targets: Low 1,100, Medium 861, High 1. The internal clause severities are None 308, Low 792, Medium 861, and High 1; internal None and Low both map to the challenge-facing Low target.

Category-state training targets: Low 832, Medium 886, High 83. Of the 83 High rows, 82 represent an expected liability cap that is missing and one represents a broad license grant.

The automatic contract rollup is Low 41, Medium 364, and High 105. Review priority is tracked separately: unresolved material can raise review priority without fabricating a higher evidence-based risk label.

## Three-class target

Use `target_risk_band` for the required classification target:

| Internal severity | Internal finding band | `target_risk_band` |
|---:|---|---|
| 0 | none | low |
| 1 | low | low |
| 2 | medium | medium |
| 3 | high | high |

`unresolved` and `not_applicable` are audit states with no numeric target. They are intentionally excluded from the training views rather than forced into Low.

The fixed perspective is a U.S. corporate-procurement organization reviewing as buyer, customer, or licensee. Direction and severity are separate, so a favorable term cannot cancel an unrelated exposure.

## Split rules

- Fit model parameters only on `split=train` rows.
- Use `split=validation` for model selection and evaluation during development.
- Do not fit, tune, select thresholds, or choose features using `split=official_test`.
- `source_partition=train` identifies the original CUAD file. The validation set was split from that original partition, so `source_partition=train` does not mean the row belongs to this package's training split.
- Keep all examples sharing a `contract_id`, `context_group_id`, or `contract_text_sha256` in the same split.
- `exact_text_seen_in_train=true` marks validation text duplicated in the training set; report a duplicate-excluded sensitivity result.

The risk files supplement a CUAD clause detector; they are not a replacement detector dataset. The complete contract text is included, but prebuilt chunks, negative-chunk labels, and ten-label multi-hot chunk targets are not. Fellows remain responsible for their own chunking, clause-detection, model-training, and application work.

## Important modeling limits

- The clause-text view has only one High development example. It is not sufficient by itself to learn a reliable High clause-text class.
- The structured category-state view has more High examples because it represents missing protections as states rather than clause text.
- `label_confidence` is annotation metadata for filtering, weighting, or subgroup reporting. Do not use it as an input feature.
- Missing category-state rows may have empty `model_input_text`; use presence, category, and contract-type fields rather than treating them as ordinary blank documents.
- Present category rows can contain several findings. Use pooling or structured features instead of assuming the first or truncated text contains the determining clause.
- Contract assessments are rule outputs and are marked `use_for_model_fit=False` and `use_for_model_validation=False`.
- No advisor, attorney, or qualified legal reviewer supplied risk ground truth.

## Package contents

| File | Purpose |
|---|---|
| [`contracts.jsonl`](contracts.jsonl) | Complete text and original paragraph boundaries for all 510 contracts |
| [`risk_training_examples.jsonl`](risk_training_examples.jsonl) | Lean numeric present-clause training examples from train and validation only |
| [`category_training_examples.csv`](category_training_examples.csv) | Lean structured category-state training examples from train and validation only |
| [`clause_findings.jsonl`](clause_findings.jsonl) | Full present-finding audit data, including abstentions and official-test rows |
| [`category_assessments.csv`](category_assessments.csv) | One audit row for each contract × selected category |
| [`contract_assessments.csv`](contract_assessments.csv) | Deterministic contract risk and separate review priority; not fit-ready |
| [`review/official_test_reference_template.csv`](review/official_test_reference_template.csv) | Two blank independent reviewer slots per official-test contract |
| [`rule_cards.json`](rule_cards.json) | Complete machine-readable weak-label rubric |
| [`source_registry.json`](source_registry.json) | Source authority, scope, and limitations for every source ID |
| [`manifest.json`](manifest.json) | Counts, distributions, parameters, and upstream input fingerprints |
| [`SCHEMA.md`](SCHEMA.md) | File and field dictionary |
| [`CATEGORY_DEFINITIONS.md`](CATEGORY_DEFINITIONS.md) | Selected CUAD category definitions |
| [`METHODOLOGY.md`](METHODOLOGY.md) | Label-design rationale and evaluation boundary |
| [`review/README.md`](review/README.md) | Optional nonexpert review procedure |

CSV columns containing lists, including `finding_ids`, `trigger_ids`, and `source_ids`, are JSON arrays encoded inside CSV cells. Parse them as JSON rather than splitting on commas.

## Source and attribution

This package is derived from the Contract Understanding Atticus Dataset (CUAD), published by The Atticus Project. CUAD is distributed under the [Creative Commons Attribution 4.0 license](https://creativecommons.org/licenses/by/4.0/). Work using these files should attribute The Atticus Project and cite the [CUAD paper](https://arxiv.org/abs/2103.06268). The [official CUAD repository](https://github.com/TheAtticusProject/cuad) and [dataset page](https://www.atticusprojectai.org/cuad/) provide the upstream release and citation information.

The research-derived risk labels are an added project layer and do not change the meaning or expert provenance of CUAD's original clause annotations. Source scope and limitations are recorded in [`source_registry.json`](source_registry.json).

## Interpretation boundary

Agreement with these labels measures imitation of the included buyer-side rubric, not real-world legal correctness. Low means lower review priority under this rubric, never “safe to sign.” High means review first, never “invalid.” Report per-class precision, recall, and F1 alongside macro-F1, coverage, confidence, category, contract type, and duplicate-excluded results.
