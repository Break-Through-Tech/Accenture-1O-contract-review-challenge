# Optional nonexpert contract-risk review

This optional process can create a team reference set for evaluation. The included [`official_test_reference_template.csv`](official_test_reference_template.csv) is blank; this package does not contain advisor-, attorney-, or human-reviewed risk labels.

The complete source text is included in [`contracts.jsonl`](../contracts.jsonl). Join the template to that file on `contract_id`; `paragraphs` preserves the original paragraph contexts and `contract_text` provides the complete joined text. No separate CUAD data file is required for this review.

## Roles and scope

- Two reviewers independently rate each of the 102 official-test contracts.
- A third team member adjudicates disagreements without deleting either original rating.
- Review from the fixed perspective of a U.S. corporate-procurement buyer, customer, or licensee.
- Consider only the ten categories in [`CATEGORY_DEFINITIONS.md`](../CATEGORY_DEFINITIONS.md) and their combined contract-level effect.
- Use the rubric in [`rule_cards.json`](../rule_cards.json) consistently, while recording uncertainty rather than inventing missing facts.

## Stay blinded

Reviewers should read the contract text in [`contracts.jsonl`](../contracts.jsonl), the category definitions, rubric, and public sources. Do not open these automatic outputs until both initial ratings are frozen:

- [`contract_assessments.csv`](../contract_assessments.csv)
- the risk, severity, direction, confidence, trigger, and rationale columns in [`category_assessments.csv`](../category_assessments.csv)
- any model predictions

The review template intentionally contains no automatic band.

## Rating rubric

Record one final band per contract:

- **Low (1):** no identified issue exceeds routine or minor review priority.
- **Medium (2):** at least one material deviation or ambiguity warrants closer review before approval.
- **High (3):** at least one documented hard stop or explicit material exposure is present, such as clearly uncapped buyer-side liability.

High means “review first,” not “invalid.” Low does not mean “safe to sign.” Do not promote several Medium issues to High merely because of their count. If the evidence cannot support a confident band, record that uncertainty in `human_confidence` and `human_rationale` and resolve it during adjudication rather than quietly assuming Low.

## Fill the template

Each reviewer fills only rows for their assigned `reviewer_slot`:

- `reviewer_id`: stable initials or team identifier
- `human_risk_band`: `low`, `medium`, or `high`
- `human_risk_ordinal`: `1`, `2`, or `3`
- `human_confidence`: `low`, `medium`, or `high`
- `human_rationale`: concise evidence and relevant category or rule IDs
- `reviewed_at`: ISO 8601 date or timestamp

Do not edit contract identifiers, split fields, hashes, or the other reviewer's row.

## Adjudication and reporting

1. Freeze both independent review files or commits.
2. Compare exact agreement, weighted Cohen's kappa, and the disagreement matrix.
3. Have the third reviewer adjudicate disagreements from the contract text and documented rubric.
4. Store consensus in a new reference column or file; never overwrite the original votes.
5. Call the result `team_consensus_reference` or `team_adjudicated_nonexpert`, never gold or expert.

Report unresolved cases, class counts, and High-to-Low disagreements. Do not tune rules on official-test decisions and then report evaluation on those same decisions as an untouched final test.
