# Scorer spec (DRAFT for team review) - October Task #3

## Unit of scoring
One **chunk-category pair**. The chunk set is the approved paragraph-based chunking (config hash in
`task10_outputs/chunking_config_frozen.json`). Each chunk has exactly 10 pairs, one per category, in this fixed order:
governing_law, renewal_term, revenue_profit_sharing, cap_on_liability, uncapped_liability,
termination_for_convenience, anti_assignment, audit_rights, license_grant, exclusivity.

## One score, one detection
- The model and each baseline emit **exactly one score per pair** (10 scores per chunk, no more, no fewer).
- A pair is **detected** when its score is >= that category's frozen threshold; otherwise it is not detected.
- Thresholds are chosen on the validation split only, then frozen before the locked run. No threshold or
  weight changes after the locked run.

## Targets
- `positive`: the chunk fully contains at least one annotated span for the category.
- `negative`: the category is not annotated in the contract, or the annotation does not touch the chunk.
- `masked`: the annotation has no usable offsets, or the chunk only partly overlaps a span (boundary split).

## What is scored
- Metrics (per-category precision, recall, F1; macro-F1 headline) are computed on **unmasked pairs only**.
- Masked pairs are excluded from the loss, from class-weight counts, from threshold selection, and from metrics.
- No post-processing between the score and the detection (no top-k, no cross-category rules).

## Splits
- Training: class weights (pos_weight = negatives / positives, unmasked pairs, per category) come from the train split only.
- Validation: model selection and threshold selection.
- Test: touched once, in the locked run (Task #11).

## Open items (confirm with the team / Beth)
- Confirm paragraph-based chunking is the approved set (the Task 9 settings file lists a 512/128 sliding window).
- Confirm masked pairs are excluded from the metrics for all three systems, including the baselines.
