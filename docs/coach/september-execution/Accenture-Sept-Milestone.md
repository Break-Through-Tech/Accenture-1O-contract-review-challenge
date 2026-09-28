# Accenture Sept Milestone

This guide is meant to be used as a suggestion to the September milestone for the Accenture project.

**September Milestone:**

Data Understanding & Baseline Modeling -> Use the team's shared Google Colab space for all September work. Load the provided training and official-test JSON files into the Colab space, run EDA on class imbalance, select the 10 core categories with the Challenge Advisor, compare chunking methods and record the method approved by the team, and establish a TF-IDF/keyword baseline with per-category metrics.

## Gate Handoffs

The Accenture project has 4 [**Gates**](./Glossary.md#gate).

1. **Gate 1**: Data Ready
1. **Gate 2**: Core Scope Frozen
1. **Gate 3**: Evaluation Ready
1. **Gate 4**: September Complete

In practice this **Gate Handoff** should work as follows:

1. **Evidence owner prepares:** all checklist items link to exact committed evidence or verified [**Artifact Bundle IDs**](./Glossary.md#artifact-bundle).
1. **Independent teammate verifies:** someone who did not produce the critical artifact reproduces or independently checks the key result.
1. **Team Readiness Review:** the owner demonstrates evidence; the team records limitations, open disagreements, anomalies, and dissent.
1. **Board updates:** dependent items become ready only after the explicit decision is recorded.

### Artifacts

When completing tasks you will produce [Artifacts](./Glossary.md#artifacts). Store the Artifacts in the team's shared Google Colab space so every fellow, the coach, and the Challenge Advisor can access them. To make handoffs easy in an async environment [Artifact Bundles](./Glossary.md#artifact-bundle) are recommended.

## Gate 1 - Data Ready

- [ ] Load all provided data and shared project materials into the team's Google Colab space.
- [ ] Confirm that every fellow, the coach, and the Challenge Advisor can access all project data, materials, and Artifacts in the Google Colab space, including the official-test data and results.
- [ ] Create and record the [Normalization Schema](./Glossary.md#normalization-schema).
- [ ] Confirm these exact totals:
  - 408 Contracts
  - 408 Documents
  - 41 Categories
  - 16,728 Annotation Sets
  - 11,180 Spans
- [ ] Confirm that every required ID or key is unique and that all links between records point to valid records.
- [ ] Confirm that every annotated Span falls within its source text and exactly matches the referenced text.
- [ ] Keep overlapping and nested Spans. Identify exact duplicates instead of automatically deleting them.
- [ ] Keep the known Contracts with duplicate text as separate Contracts, but assign them the same `context_group_id` so they always remain in the same data split.
- [ ] Create one fixed 80/20 training and validation split. The split must:
  - use training-approved data only;
  - treat each `context_group_id` as one split unit and keep every Contract in that group together;
  - use the combined 41-category presence of the Contracts in each context group for stratification; and
  - use seeded iterative multilabel stratification with seed `20260901`.
- [ ] Freeze the resulting split. Do not try additional splits because a model receives a better score on them.
- [ ] Confirm that no Contract or context group appears in more than one publisher or model split.
- [ ] Confirm that every fellow, the coach, and the Challenge Advisor can access all official-test files, labels, results, and statistics.
- [ ] Confirm that normal development outputs in Google Colab do not include official-test label information, including:
  - annotated Spans;
  - target or gold-label values;
  - Span counts;
  - label prevalence;
  - examples; or
  - other statistics calculated from official-test labels.
- [ ] Confirm that the training-data profile includes:
  - integrity checks;
  - document-length statistics;
  - support for every category;
  - category co-occurrence;
  - annotation density;
  - inputs the team will use to compare candidate chunking methods;
  - figures the team chooses to clearly communicate contract and Span lengths, category support, co-occurrence, annotation density, and anomalies; and
  - an anomaly log.
- [ ] Generate every table and figure from the recorded data and configuration. Do not hand-edit calculated values in the report.
- [ ] Confirm that all reported totals match the normalized data and that every metric clearly states what it measures—for example, Contracts, Documents, Spans, or Annotation Sets.
- [ ] Resolve every blocking anomaly. For each non-blocking anomaly, record its severity, owner, status, impact, and final decision.
- [ ] Complete and document one clean Workflow Run in Google Colab that reproduces both the training profile and its machine-readable evidence.
- [ ] Have someone other than the original author independently verify:
  - the record counts;
  - split isolation;
  - leakage protections; and
  - bundle integrity.

## Gate 2 — Core Scope Frozen

### Plain-language materials

- [ ] Present exactly five Review Bundles. Each bundle must contain exactly two different CUAD categories, for a total of 10 categories. Do not rank the five selected bundles by importance. A Review Bundle groups related categories so a person can review them together. For example, Cap on Liability and Uncapped Liability can be placed in one bundle because both concern limits on liability.
- [ ] Include a few clear positive source-text excerpts and difficult negative source-text excerpts from the training Contracts for each category. A positive excerpt must show the annotated Span with enough surrounding text to understand it. A negative excerpt must show similar-looking Contract text that should not count as that category.
- [ ] Explain that the system identifies clauses without deciding which party they favor. Categories grouped in the same Review Bundle must still be predicted separately.
- [ ] Identify related clauses or context that a reviewer may also need to consider. Explain which related categories or details are not included in the current scope.
- [ ] Name the best-supported alternative two-category Review Bundle that was considered but not selected, and explain why it was not selected. This comparison does not rank the five selected Review Bundles against one another.

### Technical record supporting the decision

- [ ] List the exact 10 proposed CUAD categories and show each category assigned to exactly one of the five Review Bundles, with two categories in each bundle.
- [ ] Using training data only, report the number of positive Contracts, distinct context groups, and annotated Spans for each category.
- [ ] Show how often related categories appear together and whether the selected source-text excerpts are overly concentrated in a small number of Contracts, context groups, or contract types.
- [ ] Confirm that each category has at least 20 positive Contracts and 20 positive context groups. Document and justify any exception.
- [ ] Provide five representative positive source-text excerpts and five realistic hard-negative source-text excerpts from the training Contracts for each category. For every excerpt, record its source Contract and text location. For each positive excerpt, also identify the annotated Span.
- [ ] Have someone who did not select the categories independently review the annotations for clarity. Record recurring rules about what Contract language should and should not count for each category.
- [ ] Document known data problems, unclear annotations, and other uncertainties for each category.
- [ ] Explain important relationships between categories, related context that is not included, and limitations involving intellectual-property and restrictive-covenant categories.
- [ ] Confirm that no official-test statistics, source-text excerpts, labels, or results influenced the category selection.
- [ ] Record who performed the independent review, any disagreements, known limitations, and the exact versions or IDs of the evidence used.

## Gate 3 - Evaluation Ready

- [ ] After Gate 2 Core Scope Frozen approval, confirm that every approved Core Category has at least one positive Contract and one negative Contract in both the model-training set and the validation set, according to the training labels.
- [ ] Before comparing chunking methods, have the team record the criteria it will use to make the decision. Identify which criteria are required and which involve tradeoffs. The criteria must address:
  - complete Span coverage;
  - Spans split across boundaries;
  - masked labels;
  - extra data created by overlapping chunks; and
  - processing cost.
- [ ] Using the same code and training data, compare at least two candidate chunking methods. Include fixed 512-token chunks with 128-token overlaps as one candidate. Do not describe any candidate as approved or rejected before the team records its decision.
- [ ] Have the team approve one chunking method for September and reject the other candidates. Record:
  - the approved method and its exact settings;
  - each rejected method and its exact settings;
  - the evidence used to compare them;
  - why the team approved the selected method;
  - why the team rejected each alternative; and
  - important tradeoffs, limitations, or disagreements.
- [ ] Freeze the team-approved chunking method and its exact settings for the rest of the September work. If the team wants to change the method or its settings, repeat the comparison and record a new team decision before continuing.
- [ ] Confirm that the team-approved chunker does not read or use annotated Spans or correct labels when producing chunks for official evaluation in Google Colab. This software safeguard does not restrict the team's access to those materials.
- [ ] For the team-approved method, record the training results, including:
  - the total number of chunks;
  - the number of masked chunk-category pairs;
  - the number of Spans split across chunk boundaries; and
  - the number of positive annotations lost during chunking. No positive annotations may be lost.
- [ ] Confirm that every chunk produced by the team-approved method has exactly 10 category-assignment rows and that:
  - a fully contained Span produces a positive target;
  - no overlapping Span produces a usable negative target; and
  - a partially overlapping Span is masked and excluded from training and evaluation.
- [ ] Confirm that every chunk produced by the team-approved method has the correct ID, source-text location, text hash, boundary and overlap details, configuration version, and output order.

### Keyword baseline evidence

- [ ] Build the versioned configuration using the [keyword baseline rules](./Glossary.md#keyword-baseline-rules). Confirm that it covers all 10 categories and that every rule and evidence group has a unique ID.
- [ ] Confirm that the keyword vocabulary came only from the [allowed keyword-rule sources](./Glossary.md#keyword-rule-sources), and record the source and rationale for every accepted rule.
**Optional automated testing:** Automated tests are not required to pass Gate 3. If the team chooses to create them, use them to check keyword rule paths, vetoes, text-normalization behavior, and the [category-confusion cases](./Glossary.md#required-category-confusion-cases).
- [ ] Confirm that every keyword match points back to the exact location in the source text and that repeated runs produce identical results.
- [ ] Confirm that each score can be recalculated from the recorded evidence and rule configuration.
- [ ] Freeze the rules before examining validation results. Select one threshold for each of the 10 categories using the [keyword threshold-selection rules](./Glossary.md#threshold-selection-rules).
- [ ] Confirm that the validation results contain one prediction for every required chunk-category pair produced by the team-approved chunking method and that the scorer’s output contains no correct labels.
- [ ] Document weak or unsuccessful behavior. Confirm that no rules were changed in response to validation results.
- [ ] Have a teammate who did not write the rules review every category’s decision table and a representative sample of matched source-text locations.

### TF-IDF baseline evidence

- [ ] Use the [fixed TF-IDF settings](./Glossary.md#tf-idf-fixed-settings). Fit the shared vocabulary using only model-training chunks produced by the team-approved chunking method.
- [ ] Evaluate exactly six overall configurations using every combination of:
  - `min_df`: 2 or 5; and
  - `C`: 0.1, 1.0, or 10.0.
  Keep the settings listed in the glossary fixed. If a configuration fails, preserve the details explaining why.
- [ ] Train 10 separate classifiers—one for each category. Exclude masked rows for that category and confirm that each classifier receives at least one positive and one negative unmasked model-training chunk-category pair.
- [ ] Record the use of balanced class weights, iteration counts, convergence results, finite-value checks, and other training diagnostics.
- [ ] For every valid configuration and category, select its threshold using the [TF-IDF threshold-selection rules](./Glossary.md#threshold-selection-rules).
- [ ] Select one overall configuration by:
  1. highest macro-F1;
  1. then `min_df=5` if there is a tie; and
  1. then the lower `C` value if a tie remains.
- [ ] Preserve the complete diagnostics, threshold searches, margins, and metrics for every valid configuration. Preserve complete failure details for every excluded configuration.
- [ ] Save the selected vocabulary, feature order, IDF values, coefficients, intercepts, thresholds, and hashes as non-object NPZ files with JSON metadata. Do not use pickle or joblib files.
- [ ] Confirm that the label-free scorer reproduces the expected detections and meets the [reproducibility tolerance](./Glossary.md#reproducibility-tolerance).

### Evaluation and reproducibility evidence

- [ ] Confirm that the keyword and TF-IDF baselines:
  - use the same unique record keys;
  - use the chunks produced by the team-approved chunking method;
  - produce exactly 10 predictions per approved chunk;
  - produce only finite scores;
  - use one consistent threshold per category; and
  - produce detections that can be recalculated from their scores and thresholds.
- [ ] Confirm that predictions connect to labels one-to-one, targets and masks are binary, and masked rows are never used in metrics or error analysis.
- [ ] Confirm that the evaluation follows the [metric calculation rules](./Glossary.md#metric-calculation-rules), including macro and micro calculations and zero-denominator handling.
- [ ] Before using the official-test labels in the official evaluation, record that the implementation follows the locked rules for:
  - [paired uncertainty intervals](./Glossary.md#paired-uncertainty-intervals);
  - [low-support warnings](./Glossary.md#low-support-warnings);
  - complete false-positive and false-negative populations for both baselines and all 10 categories;
  - [repeatable error selection and reviewer order](./Glossary.md#repeatable-error-selection); and
  - [error-review categories and secondary causes](./Glossary.md#error-review-categories).
- [ ] Record the team's chunking criteria, candidate comparisons, approval and rejection decision, approved method and settings, and exact chunking configuration version with the Artifact Manifests and Run Receipts.
- [ ] Record the shared Google Colab access settings that give every fellow, the coach, and the Challenge Advisor access to all project materials. Also record the development-use rules, schemas, workflow settings, code revision, dependency lock, Google Colab notebook and runtime versions, processing-thread settings, and inputs.
- [ ] From a clean committed version of the project in Google Colab, rerun the development workflow through validation only. Confirm that the team-approved training and validation chunks, validation predictions, threshold selections, metrics, and all other required pre-authorization results can be reproduced. Do not use official-test data or official-test labels during this clean rerun.
- [ ] Have someone other than the original author independently recalculate the confusion counts and main validation metrics from the frozen row-level results.
- [ ] Complete a final check confirming that official-test inputs, labels, results, and statistics did not influence development work. This is a separation-of-use check, not an access restriction.

### Authorization to run the official-test evaluation

- [ ] Confirm that the Markdown approval and official JSON authorization contain the same:
  - approved Git commit;
  - approver;
  - executor;
  - unique authorization ID;
  - workflow hash and the team-approved chunking configuration hash;
  - approved Artifact Bundle IDs;
  - official source-file hash;
  - authorization time; and
  - permitted action.
- [ ] Confirm that the entire team, the coach, and the Challenge Advisor can access the official-test data and results in the team's Google Colab space.

## Gate 4 - September Complete

- [ ] Confirm that both approved baseline models were run in the team's Google Colab space during the same authorized official-test event and used the same contract chunks produced by the team-approved chunking method and settings.
- [ ] Have someone other than the official-test executor independently recalculate the confusion counts, main metrics, bootstrap results, and error samples from the saved predictions in Google Colab.
- [ ] Include a validation-selection table showing:
  - the keyword baseline;
  - all six TF-IDF configurations;
  - how ties were resolved; and
  - results for each category.
- [ ] Begin the official-results summary with macro-F1. Also include:
  - micro-level metrics;
  - combined true-positive, false-positive, false-negative, and true-negative counts;
  - differences between the two baselines; and
  - the exact Workflow Run and Artifact Bundle IDs.
- [ ] For each category, report:
  - the number of actual positive and negative unmasked chunk-category pairs;
  - the number of unmasked chunk-category pairs predicted as positive;
  - precision;
  - recall;
  - F1;
  - the difference between the baselines; and
  - links to any relevant warnings or limitations.
- [ ] Keep validation results and official-test results separate. Never combine them into a single result.
- [ ] Include all [paired uncertainty intervals](./Glossary.md#paired-uncertainty-intervals) and [low-support warnings](./Glossary.md#low-support-warnings). Clearly identify:
  - cases where macro and micro metrics suggest different conclusions; and
  - intervals that are too wide or unstable to support a firm conclusion.
- [ ] Describe results only as:
  - directly observed;
  - consistent with a pattern within the CUAD dataset; or
  - inconclusive.

### Error review

**Workload note:** This step may include up to 200 selected error pairs and, because every pair has two independent reviewers, up to 400 individual assessments. Break the work into smaller, clearly assigned batches—such as by baseline, category, or error type—and share those batches across the team. Track which batches are assigned, completed, and still open so work is not duplicated or missed. If the review extends into October, that is acceptable. Keep Gate 4 open until the required reviews, resulting corrections, and final handoff are complete; do not reduce the sample or skip the second independent review only to meet the end-of-September date.

- [ ] Create the complete false-positive and false-negative lists of unmasked official-test chunk-category pairs for all 40 combinations: two baselines × 10 categories × two error types.
- [ ] Select up to five chunk-category pairs from each combination using the [repeatable error-selection method](./Glossary.md#repeatable-error-selection). Record combinations with no errors, and do not replace selected pairs because they are inconvenient or unclear.
- [ ] Before reviewers see selected official-test errors in Google Colab, have them practice and align their review approach using false-positive and false-negative chunk-category pairs from the development data.
- [ ] Have two reviewers independently assess every selected official-test error pair in the team's Google Colab space before they discuss it with each other.
- [ ] For every review, record:
  - one main source of the error from the [error-review categories](./Glossary.md#error-review-categories);
  - any applicable secondary causes from the same reference;
  - a short explanation supported by evidence;
  - the reviewer’s confidence; and
  - the workflow stage where the issue should be addressed.
- [ ] If reviewers disagree, preserve both original assessments. Do not treat the reviewed sample’s error patterns as rates for the full dataset.
- [ ] Resolve every confirmed data-processing or workflow defect before completing the gate. If resolving a defect requires rerunning one or both baseline models, record the reason for the rerun, the corrected workflow or model version, and the new Workflow Run and Artifact Bundle IDs. Use the corrected run for verification and final reporting.

### Handoff and communication

- [ ] Prepare a plain-language report explaining:
  - what the September work established;
  - the observed results and their uncertainty;
  - important exceptions;
  - the main patterns found during error review;
  - one next-step direction supported by evidence; and
  - conclusions or actions that the evidence does not justify.
- [ ] Explain the important limitations, including:
  - results apply only to the CUAD dataset;
  - annotations may be incomplete or uncertain;
  - evaluation was performed on contract chunks produced by the team-approved method rather than on whole contracts;
  - related clauses and surrounding context may still be needed;
  - some categories and modifying details were excluded; and
  - the results do not provide legal advice or determine contract risk.
- [ ] Create the [October recommendation register](./Glossary.md#october-recommendation-register) using every required field in the template, and link each recommendation to the exact supporting evidence.
- [ ] Preserve the following in the team's shared Google Colab space so every fellow, the coach, and the Challenge Advisor can access them:
  - approved Artifact Bundle IDs;
  - manifests;
  - instructions for reproducing the results;
  - the chunking criteria, candidate comparisons, approval and rejection decision, and approved method and settings;
  - model and workflow configurations;
  - interface definitions;
  - recorded anomalies;
  - approved deviations; and
  - the official-test run authorization and team-wide access confirmation.
- [ ] In the team retrospective, record:
  - one practice to keep;
  - one practice to change;
  - one experiment to try; and
  - broader lessons from the September work.
- [ ] Do not create speculative October implementation tickets before the handoff is approved. Begin October planning using the approved handoff and its evidence.
