# Methodology and interpretation

## Why these labels exist

CUAD supplies expert-annotated clause categories and text spans, but it does not supply Low/Medium/High risk judgments. Contract risk depends on the reviewing party, transaction, governing law, business priorities, and risk tolerance. The ratings in this package are therefore research-derived weak labels created under a fixed scenario, not expert legal ground truth.

The package is intended to help fellows experiment with clause/category risk classification and transparent contract triage. It must not be described as legal advice, an enforceability assessment, a prediction of loss, or a universal measure of contract quality.

## Fixed assessment perspective

- Reviewer role: corporate procurement
- Reviewed party: buyer, customer, or licensee
- Counterparty default: seller, supplier, provider, or licensor
- Jurisdictional baseline: United States commercial procurement
- Scope: text-only triage of the ten selected CUAD categories
- Unknown business context: preserved as uncertainty rather than silently treated as Low

## Label dimensions

The rubric keeps these concepts separate:

| Dimension | Values | Meaning |
|---|---|---|
| `direction` | protective, balanced, adverse, mixed, unclear | Who benefits or bears the burden under the fixed perspective |
| `severity_ordinal` | 0, 1, 2, 3 | Review urgency under the included rubric |
| `target_risk_band` | low, medium, high | Three-class target supplied to fellows |
| `confidence` / `label_confidence` | low, medium, high | Confidence in rule application, not confidence that a contract is safe |
| `applicability` | applicable, not_applicable, unclear | Whether the category rule can be used for the contract |
| `finding_kind` | present_clause, expected_but_missing, ambiguity, conflict | Why an assessment exists |

Internal severity 0 means no material deviation was found; severity 1 means a minor or routine review item. Both map to the challenge-facing Low target. Severity 2 maps to Medium, and severity 3 maps to High. `unresolved` and `not_applicable` remain nonnumeric audit states.

A signed negative-to-positive score was not used because it would allow a favorable provision to cancel an unrelated exposure. Each issue is assessed independently before contract rollup.

## Weak-label procedure

1. Start with CUAD's complete contract text and annotated spans for the ten selected categories, both represented in this package.
2. Consolidate nearby or overlapping answer spans that represent one provision.
3. Apply the ordered rules in [`rule_cards.json`](rule_cards.json) from the fixed buyer-side perspective.
4. Preserve the matched rule, direction, rationale, sources, applicability, and confidence.
5. Abstain when the text does not support a stable assessment instead of forcing a numeric label.
6. Create one contract-category state for each of the 510 contracts and ten categories, including expected-but-missing, not-applicable, and unresolved states.
7. Map numeric severities to `target_risk_band` for the two training views.

The source IDs attached to findings resolve to [`source_registry.json`](source_registry.json). The sources support the methodology and documented project rubric; they do not convert weak labels into legal ground truth.

## Contract rollup

The deterministic rollup is intentionally simple and monotonic:

1. Any explicit High category assessment makes the contract High.
2. Otherwise, any explicit Medium category assessment makes the contract Medium.
3. Otherwise, the evidence-based contract result is Low.
4. Multiple Medium findings are not promoted to High merely because of their count.
5. Material unresolved items raise `rule_contract_review_priority_band` to at least Medium without changing the evidence-based risk result.

Related Cap on Liability and Uncapped Liability assessments share an issue family so they describe one liability-allocation problem rather than two unrelated votes.

Contract rows are deterministic rubric outputs and are deliberately marked non-fit-ready. They are useful for inspection, joining, or rule-distillation experiments, but they are not independent human training labels.

## Split and leakage controls

- 325 contracts are assigned to train, 83 to validation, and 102 to official test.
- Exact contract contexts stay together through `context_group_id` and `contract_text_sha256`.
- Both training files exclude official-test rows.
- Duplicate normalized validation text is marked with `exact_text_seen_in_train`.
- The blank review template contains no automatic rating.

`source_partition` records the original CUAD JSON partition. `split` records the machine-learning split in this package. Because validation was carved from CUAD's original training partition, validation rows legitimately have `source_partition=train` and `split=validation`.

## Evaluation boundary

The included risk labels measure agreement with this rubric. They do not measure legal correctness. Suitable reporting includes per-class precision, recall, and F1; macro-F1; ordinal error; High recall; coverage and abstention; and results by category, confidence, contract type, and duplicate-excluded validation slice.

No advisor- or attorney-rated reference set is included. Teams may create an optional blinded, independently reviewed nonexpert reference set using the instructions in [`review/README.md`](review/README.md). Such a set must be described as team-created and nonexpert.

## Known limitations

- Present-clause High has only one development example.
- Most category-state High rows are expected liability caps that are absent, not High clause text.
- CUAD often uses party names instead of buyer/supplier role words.
- Text can be incomplete, redacted, or dependent on cross-references.
- Contract type is inferred from titles and may remain unknown.
- Weak-label rules share assumptions and are not independent annotator votes.
- Low means lower review priority under this rubric, never “safe to sign.”
