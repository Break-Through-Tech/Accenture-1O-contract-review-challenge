# Accenture Oct Milestone

This guide proposes gates for the October milestone of the Accenture project. The checkboxes are blocking evidence checks, not a claim that September or October work is complete. Use the [September milestone guide](../september-execution/Accenture-Sept-Milestone.md), its [Glossary](../september-execution/Glossary.md), and the approved September handoff as the starting record.

**October Milestone:**

Transformer Modeling & Evaluation -> Fine-tune a lightweight pre-trained transformer encoder for multi-label detection of the 10 approved Core Categories, address class imbalance, evaluate per-category precision/recall/F1 against the September baselines, and conduct error analysis. The [Challenge Project Overview](../../../Challenge-Project-Overview.md#project-milestones) places the rule-based risk-scoring layer and pipeline integration in November.

| October requirement | Evidence needed to finish the milestone | Gate |
| --- | --- | --- |
| Fine-tune a lightweight encoder for 10-category multi-label detection | Saved checkpoint showing trained encoder weights, a 10-output head, and a working label-free scorer | 2–3 |
| Address class imbalance | Training-only support counts, comparison of an imbalance treatment with an unweighted reference, and a selection rationale | 2 |
| Evaluate clause detection | Per-category precision, recall, and F1 against the September baselines on identical units, plus a category-level success decision | 3–4 |
| Analyze errors | Complete error populations, a repeatable reviewed sample, and evidence-backed failure themes | 4 |

## Gate Handoffs

The October project has 4 [**Gates**](../september-execution/Glossary.md#gate).

1. **Gate 1**: October Plan Ready
1. **Gate 2**: Transformer Candidate Ready
1. **Gate 3**: Evaluation Ready
1. **Gate 4**: October Complete

For each Gate Handoff:

1. **Evidence owner prepares:** every checklist item links to exact committed evidence or verified [Artifact Bundle IDs](../september-execution/Glossary.md#artifact-bundle).
1. **Independent teammate verifies:** someone who did not produce the critical artifact reproduces or independently checks its key result.
1. **Team Readiness Review:** the owner demonstrates the evidence; the team records limitations, open disagreements, anomalies, and dissent.
1. **Board updates:** dependent items become ready only after the explicit decision is recorded.

### Artifacts

Keep the October [Artifacts](../september-execution/Glossary.md#artifacts), [Artifact Manifests](../september-execution/Glossary.md#artifact-manifest), and [Run Receipts](../september-execution/Glossary.md#run-receipt) in the team's shared Google Colab space. Record the exact code revision, input and configuration hashes, model and tokenizer revisions, environment, and output IDs in each [Workflow Run](../september-execution/Glossary.md#workflow-run). Every fellow, the coach, and the Challenge Advisor must be able to access the materials and results.

### Evaluation boundary

Once September official-test results and error reviews enter the handoff, that test cannot serve as **new unbiased evidence** for a model designed afterward. October model selection and threshold setting must use training-approved data and the frozen validation split. September official-test observations may motivate evidence-linked hypotheses, but their influence must be recorded. A later comparison on the same official test can be useful, but it must be identified as a reused-set, descriptive comparison. A fresh, locked, independently labeled evaluation set is needed for a new unbiased effectiveness claim. Record which kind of evidence October can actually produce before training begins.

### October error-review codes

Use the September [error-review categories](../september-execution/Glossary.md#error-review-categories) for shared causes. For a transformer error, replace the primary code `baseline` with `model`: the available source text is adequate, but the transformer score or detection is wrong. Keep `gold_data`, `chunking`, `language_context`, `pipeline`, and `unresolved` unchanged. Shared secondary causes still apply. Add `tokenization or input truncation`, `training support or imbalance treatment`, and `learned representation or optimization` as possible transformer secondary causes; reserve keyword- and TF-IDF-specific causes for reviews of those baselines. Freeze the code list and reviewer instructions before the October evaluation.

### October support warnings

Apply the September [low-support warning](../september-execution/Glossary.md#low-support-warnings) thresholds to **each model and evaluation set**, including the transformer and any fresh set: `low_gold_support` for fewer than 20 distinct gold-positive context groups, `low_predicted_support` for fewer than 20 distinct predicted-positive context groups, and `zero_support` when no usable positive or negative example exists. Report support in chunks, Contracts, and context groups, and record bootstrap repetitions with zero positive support. Warnings do not remove a category from the results.

## Gate 1 - October Plan Ready

### September handoff and scope

- [ ] Record the September Gate 4 status and link its approval, final report, retrospective, October Recommendation Register, approved Artifact Bundle IDs, and unresolved limitations or anomalies when available. If Gate 4 remains open, record its carryover owner and dependencies. Milestone-2 planning and general compute setup may proceed, but do not release experiments that depend on unapproved September evidence or mark this gate open until the handoff is approved.
- [ ] Record the approved 10 Core Categories and category IDs, normalization schema, context groups, model-training/validation split, team-approved chunking method and settings, target and mask rules, metric definitions, selected baseline configurations and thresholds, and their exact versions and hashes.
- [ ] Review every relevant September recommendation by ID. Record whether the team adopts, defers, or rejects it, with the linked evidence and reason. A recommendation by itself does not authorize a change.
- [ ] For any adopted recommendation that changes frozen September categories, labels, split, chunking, or baseline evidence, identify the affected September Gate and approve the change. Before comparison on revised units, rerun the keyword scorer, refit and retrain TF-IDF on revised training chunks, reselect both baselines' validation thresholds, and evaluate both on the revised units.
- [ ] Put September carryover and the four October Gates into the Milestone-2 GitHub Project plan with owners and dependencies. Add weekly evidence-backed implementation tasks after the September handoff approval; keep any preparatory October items visibly blocked by the missing handoff decision.

### Experiment and evaluation plan

- [ ] Define the label-free scorer output: exactly one score and detection for each approved `(chunk_id, category_id)` pair, with source location, category order, model version, and threshold traceable to the input. Keep targets and masks in separate evaluation records joined only inside the evaluator. Confirm that the classifier predicts categories separately even when they share a Review Bundle.
- [ ] Choose a lightweight pre-trained encoder and tokenizer, recording their exact published revisions, input-length limit, license, and the reason they fit the available Google Colab compute budget. Record the maximum number of training runs and the fallback if a run fails or resources are insufficient.
- [ ] Pre-register the candidate model configurations, seeds, training budget, checkpoint-selection rule, imbalance treatments to compare, validation-based threshold rule, primary baseline comparator, tie-breakers, and failure criteria. Choose the primary comparator from the approved September validation record; retain both September baselines in the final report.
- [ ] Define the comparison on the [September metric unit](../september-execution/Glossary.md#metric-calculation-rules): unmasked chunk-category pairs. Have the team pre-register a **category-level** acceptance rule for all 10 categories and seek Challenge Advisor feedback before evaluation. Specify the required F1 improvement over the named baseline, minimum acceptable precision and recall, treatment of regressions, uncertainty, and low support; record any unresolved disagreement. Use macro-F1 and micro metrics as summaries; neither alone can establish the detection success criterion. Report unsuccessful and inconclusive outcomes.
- [ ] Approve the evaluation source, designate the primary set for error review, and state the claim it supports. A fresh set must contain Contracts and context groups unseen in all September and October development, including September official-test review; lock its source, labeling protocol, exclusions, and overlap checks, and have reviewers assign and adjudicate labels without seeing model or baseline predictions. The provided 510 CUAD Contracts have already been allocated to September training, validation, or official test, so relabeling them does not create a fresh set. If October reuses the September official test, label its comparison descriptive and state why it cannot establish a new unbiased improvement claim.
- [ ] Define the comparison's uncertainty method before looking at October evaluation results. Resample by `context_group_id`, keep all chunks and categories in each group together, pair the transformer and baseline predictions on the same resamples, and keep model weights and thresholds fixed. State the seed, repetitions, interval method, and how zero-support repetitions will be handled.

## Gate 2 - Transformer Candidate Ready

### Data and training interface

- [ ] Use the approved September training chunks, category order, labels, and masks. Confirm that each chunk still has exactly 10 category-assignment rows and that no Contract or `context_group_id` crosses the model-training, validation, or publisher official-test boundaries.
- [ ] Verify the selected tokenizer's actual token lengths, including special tokens. Audit training and validation Spans for truncation and record affected source locations; keep evaluation chunking label-free. Do not silently truncate a labeled Span or turn a masked row into a usable negative. If the model cannot use the approved chunks without material content loss, approve a revised chunking decision and rerun the full baseline development and evaluation steps in Gate 1 before comparing results.
- [ ] Confirm that chunk generation and inference use source text without reading gold Spans or labels. Use training labels only to construct training targets and masks. Train a 10-output independent multi-label head with a mask-aware binary loss, such as binary cross-entropy over unmasked category pairs; exclude masked pairs from the loss and all later metrics.
- [ ] Record aggregate positive and negative unmasked training and validation support for each category, plus distinct supporting context-group counts. Confirm that each category has both classes available in each split, or stop and document the approved correction. Derive any class weights, sampling rates, or focal-loss parameters from model-training data only. Explain how the selected imbalance treatment avoids duplicating validation or official-test examples and how it affects rare categories.
- [ ] Fine-tune at least part of the pre-trained encoder together with the 10-output head. Record trainable encoder layers and parameter counts. Train the pre-registered unweighted reference and imbalance-treatment candidates under comparable data, compute budgets, and selection rules. Keep completed and failed runs, including loss curves, finite-value checks, checkpoint IDs, class-weight or sampling values, seeds, and resource use.
- [ ] Check that the model produces 10 finite independent scores in the approved category order for every input chunk. Record whether scores are logits or probabilities and how category thresholds are applied. A fully negative chunk may still have several predicted categories; do not force the outputs into a single-label choice.

### Candidate selection

- [ ] Evaluate every completed candidate on the frozen validation split using only unmasked pairs. Select one checkpoint and one threshold per category by the pre-registered rules; preserve the full candidate and threshold search, confusion counts, metrics, and tie decisions.
- [ ] Show the effect of imbalance treatment on each category's precision, recall, F1, and support. Record categories where recall improves by creating unacceptable false positives, where support is too low for a stable conclusion, and where the selected treatment fails to help.
- [ ] Freeze the selected checkpoint, tokenizer, preprocessing, category order, chunking configuration, thresholds, and inference code. Save portable model weights and metadata with hashes, plus a label-free scorer that does not require gold labels to produce detections.
- [ ] Have a teammate who did not train the selected model verify the input-to-output interface, masks, category order, saved checkpoint loading, and a sample of score-to-detection calculations.

## Gate 3 - Evaluation Ready

- [ ] Confirm that the selected transformer and both September baselines can be compared on the same approved chunk-category keys, source locations, masks, and category order. If any unit changed, preserve the old results separately and use the approved keyword rerun, TF-IDF refit and retraining, validation-threshold selection, and evaluation of both baselines on the new units.
- [ ] Confirm that every required chunk-category pair has one finite score and one detection, with a single frozen threshold for its category. Predictions must contain no gold label, and targets and masks must be joined one-to-one only inside the evaluator.
- [ ] Independently recalculate the selected transformer's validation confusion counts, per-category precision/recall/F1, macro-F1, micro metrics, and paired differences from saved row-level outputs. Apply the September [metric rules](../september-execution/Glossary.md#metric-calculation-rules) and the [October support warnings](#october-support-warnings).
- [ ] From a clean committed version in Google Colab, reproduce preprocessing and label-free inference from the frozen checkpoint through the validation results. Record exact agreement for IDs, masks, detections, counts, and metrics; document any allowed numerical score tolerance and any hardware nondeterminism. Do not substitute a new training run for verification of the frozen checkpoint.
- [ ] Before scoring against any locked evaluation labels in October, including descriptive reuse of September's official test, freeze the code revision, checkpoint and tokenizer hashes, thresholds, comparison rules, uncertainty procedure, complete error-population method, repeatable error-sampling seed, review categories, and reviewer order.
- [ ] Record an explicit authorization for each locked evaluation run, naming the approver, executor, permitted action, evaluation-source hash, Git commit, checkpoint, configuration, and Artifact Bundle IDs. Confirm shared Colab access to the inputs and results. The authorization controls use of protected labels, not who may access them.
- [ ] Have someone other than the evaluation executor inspect the frozen package and authorization for completeness. Identify any October decisions motivated by September official-test evidence and record the resulting threats to validity before the run.

## Gate 4 - October Complete

### Results and error review

**Workload note:** The primary evaluation set can yield up to 60 selected transformer errors and 120 individual reviews. Assign batches by category or error type, track completion, and keep this gate open until the independent reviews and any required corrections are finished. Preserve complete error lists for every evaluated set; a second set does not automatically double the review assignment.

- [ ] Execute the authorized evaluation once with the frozen package. Save row-level scores and detections, joined evaluation rows, logs, Run Receipts, and complete Artifact Manifests. Keep validation, reused official-test, and any fresh evaluation results in separate tables and bundles.
- [ ] Have someone other than the executor independently recalculate the confusion counts, main metrics, paired differences, uncertainty intervals, and error samples from the saved row-level results.
- [ ] Begin the results summary with macro-F1 for the transformer and both September baselines on identical evaluation units. For each category, report positive and negative unmasked support, predicted-positive count, TP/FP/FN/TN, precision, recall, F1, paired baseline differences, and applicable low-support warnings. Also report micro metrics and the exact Workflow Run and Artifact Bundle IDs.
- [ ] For each category, state whether its pre-registered detection criterion was met, not met, or inconclusive, then state whether the overall category-level success rule was met. Show uncertainty intervals and regressions; do not use a macro-F1 gain to hide category failures. Qualify any verdict from the reused official test as descriptive; only a fresh independent set can support a new unbiased effectiveness claim. If the rule was not met, record an evidence-backed corrective plan and report October training/evaluation as completed without claiming detection success.
- [ ] For each evaluation set, create complete false-positive and false-negative lists for all 20 transformer combinations: 10 categories × two error types. On the designated primary set, adapt the September [repeatable selection method](../september-execution/Glossary.md#repeatable-error-selection) with a stable model ID and evaluation-set ID in the ranking key and select up to three cases per combination. Record empty combinations, keep sets separate, and do not replace inconvenient cases. Review of a secondary set may be assigned if time and evidence warrant it.
- [ ] Have two teammates independently review each selected error before discussion, using the frozen October error-review codes. Preserve their original assessments, evidence notes, confidence, secondary causes, and disagreement records. Treat patterns in the reviewed sample as hypotheses, not rates for all errors.
- [ ] Compare the transformer's correct and incorrect pairs with both baselines on the same rows. Identify newly corrected errors, new errors, persistent errors, and whether class imbalance, chunk boundaries, label ambiguity, or surrounding contract context plausibly explains them.
- [ ] Resolve confirmed data-processing or evaluation defects before closing the gate. If a defect requires a rerun, record the reason, changed versions, renewed authorization, and new Run and Bundle IDs; keep the superseded outputs traceable. Do not retune the model against locked evaluation results and present the rerun as an unbiased first test.

### Handoff and communication

- [ ] Prepare a plain-language report for the team, coach, and Challenge Advisor explaining the selected model and imbalance treatment, observed performance and uncertainty, category-specific weaknesses, error-review themes, compute cost, and what the evidence does and does not establish.
- [ ] Explain that results are measured on CUAD contract chunks, annotations may be incomplete or ambiguous, excluded categories and surrounding clauses can matter, and clause detection does not determine legal risk or provide legal advice.
- [ ] Preserve the selected model, tokenizer, thresholds, interface definitions, inference instructions, comparison and error-review evidence, anomalies, approved deviations, and all relevant manifests and Run Receipts in the shared Google Colab space.
- [ ] Create a November handoff with evidence-linked recommendations for the risk-scoring and pipeline-integration milestone. State which detector outputs are stable enough to consume, what uncertainty or abstention information should be carried forward, and what further validation is needed before claiming reviewer benefit.
- [ ] In the team retrospective, record one practice to keep, one to change, one experiment to try, and any unfinished work with owners. Record the explicit Gate 4 decision before opening dependent November tasks.
