# Glossary

Terms are arranged alphabetically. Use the table of contents to jump directly to any entry.

## Table of Contents

- [A](#a-entries)
  - [Access classification](#access-classification)
  - [Annotation density](#annotation-density)
  - [Annotation Set](#annotation-set)
  - [Artifact Bundle](#artifact-bundle)
  - [Artifact Manifest](#artifact-manifest)
  - [Artifacts](#artifacts)
- [B](#b-entries)
  - [Bootstrap repetition](#bootstrap-repetition)
  - [Bundle integrity](#bundle-integrity)
- [C](#c-entries)
  - [`C`](#c)
  - [Chunk-category pair](#chunk-category-pair)
  - [Class weights](#class-weights)
  - [`context_group_id`](#context_group_id)
  - [Contract](#contract)
  - [Convergence](#convergence)
  - [Co-occurrence](#co-occurrence)
  - [Core Category](#core-category)
  - [CUAD](#cuad)
- [D](#d-entries)
  - [Dependency lock](#dependency-lock)
  - [Document](#document)
- [E](#e-entries)
  - [Error-Review Categories](#error-review-categories)
- [G](#g-entries)
  - [Gate](#gate)
  - [Gold label](#gold-label)
- [H](#h-entries)
  - [Hard negative](#hard-negative)
- [I](#i-entries)
  - [Interface definition](#interface-definition)
- [K](#k-entries)
  - [Keyword Baseline Rules](#keyword-baseline-rules)
  - [Keyword-Rule Sources](#keyword-rule-sources)
    - [Required Category-Confusion Cases](#required-category-confusion-cases)
- [L](#l-entries)
  - [Leakage](#leakage)
  - [`LinearSVC`](#linearsvc)
  - [Low-Support Warnings](#low-support-warnings)
- [M](#m-entries)
  - [Margin](#margin)
  - [Mask](#mask)
  - [Metric Calculation Rules](#metric-calculation-rules)
  - [`min_df`](#min_df)
  - [Model split](#model-split)
- [N](#n-entries)
  - [Non-finite value](#non-finite-value)
  - [Normalization Schema](#normalization-schema)
- [O](#o-entries)
  - [October Recommendation Register](#october-recommendation-register)
- [P](#p-entries)
  - [Paired interval](#paired-interval)
  - [Paired Uncertainty Intervals](#paired-uncertainty-intervals)
  - [Percentile interval](#percentile-interval)
  - [Processing-thread setting](#processing-thread-setting)
  - [Protected label](#protected-label)
  - [Publisher split](#publisher-split)
- [R](#r-entries)
  - [Repeatable Error Selection](#repeatable-error-selection)
  - [Reproducibility Tolerance](#reproducibility-tolerance)
  - [Run Receipt](#run-receipt)
- [S](#s-entries)
  - [Seeded iterative multilabel stratification](#seeded-iterative-multilabel-stratification)
  - [Span](#span)
- [T](#t-entries)
  - [TF-IDF](#tf-idf)
  - [TF-IDF Fixed Settings](#tf-idf-fixed-settings)
  - [Threshold Selection Rules](#threshold-selection-rules)
    - [Keyword baseline](#keyword-baseline)
    - [TF-IDF baseline](#tf-idf-baseline)
- [W](#w-entries)
  - [Workflow Run](#workflow-run)
- [Usage Guide](#usage-guide)
  - [Example Dialogue](#example-dialogue)
  - [How These Terms Relate](#how-these-terms-relate)
  - [Terminology to Use Consistently](#terminology-to-use-consistently)

## A entries

### Access classification

A label describing whether material is for development or official evaluation; in this project it controls appropriate use and does not limit access by fellows, the coach, or the Challenge Advisor.

### Annotation density

The amount of annotated material in a Contract, described with measures such as Spans per Contract, categories per Contract, or the share of Contract text covered by Spans.

### Annotation Set

The single record connecting one Contract to one CUAD category and containing zero or more annotated Spans for that category.

### Artifact Bundle

An **Artifact Bundle** is a complete package of related **Artifacts** from one successfully completed task or grouping of like tasks. It includes the files, a description of what they contain, and the checks needed to confirm that they are complete and can be used by the next step. Partial or failed work is not an **Artifact Bundle**.

For example:

Building on the [Artifacts](./Glossary.md#artifacts) example. The Python file, README, and output file would be considered an **Artifact Bundle**.

### Artifact Manifest

A machine-readable inventory describing an Artifact Bundle's files, versions, schemas, settings, source relationships, and file hashes.

### Artifacts

**Artifacts** are the work products created by the project. They can be data, reports, models, results, or other evidence that helps the team complete a task or make a decision.

For example:

You are tasks with completing a [FizzBuzz](https://www.geeksforgeeks.org/dsa/fizz-buzz-implementation/) challenge for a job interview. You choose to do this in Python. You produce:

- A Python file that has your FizzBuzz solution
- A README on your approach to your solution and run instructions
- An output file with your results of running your FizzBuzz solution

The Python file, README, and output file are all Artifacts produced as a result of working through this job interview challenge. 

It's important to remember that code files and output files are not the only Artifacts. READMEs and other Markdown files are also Artifacts.

## B entries

### Bootstrap repetition

One trial that samples context groups with replacement from the evaluation data and recalculates the required metrics on that sample.

### Bundle integrity

Confirmation that an Artifact Bundle contains every declared file and that its hashes, schemas, and required checks match its Artifact Manifest.

## C entries

### `C`

The LinearSVC setting that controls how strongly training mistakes are penalized, with larger values generally fitting the training data more closely and smaller values applying more regularization.

### Chunk-category pair

One Contract chunk considered together with one Core Category, which forms one prediction and evaluation row for that category.

### Class weights

Training weights that change how much mistakes on each class matter so a less common positive class is not overwhelmed by a more common negative class.

### `context_group_id`

A stable identifier shared by Contracts with identical source text so those Contracts are always assigned to the same model split.

### Contract

One commercial agreement record from CUAD, kept separate from every other Contract even when two Contracts contain identical text.

### Convergence

The point at which the training process has settled on a solution within its allowed number of iterations and tolerance.

### Co-occurrence

The presence of two categories in the same Contract, counted once per Contract rather than once per Span.

### Core Category

One of the 10 CUAD categories the team selects for September modeling and evaluates separately from the other categories.

### CUAD

The Contract Understanding Atticus Dataset is a collection of 510 commercial Contracts annotated across 41 legal-clause categories; this project uses its 408-Contract training split and 102-Contract official-test split.

## D entries

### Dependency lock

A recorded file or equivalent list that pins the exact software-package versions needed to reproduce a Workflow Run.

### Document

The exact source text belonging to a Contract, together with the character-position system used to locate annotated text.

## E entries

### Error-Review Categories

Each reviewed error must receive exactly one **primary category**:

- `gold_data`: the reference annotation may be unclear, inconsistent, or incorrect.
- `chunking`: a boundary, overlap, containment, or masking decision contributed to the error.
- `language_context`: the necessary meaning is difficult to recover from the local text.
- `baseline`: the available text is adequate, but the keyword rules or TF-IDF classifier failed.
- `pipeline`: there may be an implementation, joining, scoring, or metric-calculation defect.
- `unresolved`: the available evidence does not support a defensible explanation.

Reviewers may also record zero or more **secondary causes**:

- lexical or drafting variation;
- confusion with a neighboring category;
- negation, exception, polarity, or scope;
- party, entity, or coreference;
- long-range dependency or cross-reference;
- generic boilerplate;
- keyword coverage, proximity, veto, or aggregation;
- TF-IDF vocabulary, feature weighting, or linear ranking;
- threshold tradeoff;
- overlap or duplicate-content concentration;
- annotation ambiguity or inconsistency; or
- `other`, with a written explanation.

For every assessment, record a short evidence note, reviewer confidence, and the workflow stage where the issue should be addressed. Preserve both original assessments when reviewers disagree. Report category totals only for the reviewed sample; do not present them as rates for the complete error population.

## G entries

### Gate

**Gate**: A **Gate** in this context will be a set of blocking items that need to be completed. Complete the blocking items and the **Gate** is opened.

For example:

Baking a cake can be divided into serval '**Gates**'.

1. Mix wet and dry materials and mix till combined and batter is smooth.
1. Grease and pour the batter into desired pan.
1. Bake until done.

Each step above is a grouping of like tasks, each number is a '**Gate**' that needs to be completed in order to get that cake.

### Gold label

The reference answer supplied by the dataset that evaluation treats as correct, including whether a category is present and where its annotated Spans occur.

## H entries

### Hard negative

A source-text excerpt that looks similar to a positive example but should not be labeled as the category, making it more useful than an obviously unrelated negative.

## I entries

### Interface definition

A documented agreement describing the inputs, outputs, fields, formats, and allowed behavior between two workflow steps or components.

## K entries

### Keyword Baseline Rules

Build one independent keyword scorecard for each of the 10 Core Categories. A category's score must depend only on the text in the current chunk and that category's frozen rules. Do not use another category's result, a Review Bundle companion, a neighboring chunk, or a correct label to change the score.

Use these fixed evidence effects:

| Evidence effect | Points |
| --- | ---: |
| Anchor evidence | `+2` |
| Supporting evidence | `+1` |
| Counterevidence | `-1` |
| Vetoed occurrence | `0` |

Place synonymous or overlapping rules in one evidence group. Count only the strongest surviving contribution from that group once per chunk. Add the distinct group contributions and do not allow the final score to fall below zero. Repeated matches, chunk length, category prevalence, another category, or another model must not increase the score.

For matching, keep the source text unchanged and create a separate normalized view by applying, in order:

1. Unicode NFKC normalization;
2. Unicode case-folding;
3. consistent equivalents for typographic quotation marks and dashes; and
4. replacement of each whitespace run with one space.

Keep a map from every normalized match back to its exact location in the source text. Do not use implicit stemming, fuzzy matching, embeddings, or arbitrary executable code in the rules.

For each category, create a decision table that records its inclusion meaning, anchor and supporting groups, justified counterevidence or vetoes, context and proximity limits, known near-misses, exclusions, rule sources, and examples that exercise every rule branch. Every category must have at least one anchor evidence group.

### Keyword-Rule Sources

Keyword rules may use only:

1. the canonical CUAD category names and descriptions;
2. annotated Span text, nearby text, and manually reviewed hard negatives from the model-training portion of the official training Contracts; and
3. legal drafting variants supplied by the team or Challenge Advisor when the rule records the rationale and reviewer.

Automatic phrase mining may suggest candidates from the model-training data, but a person must accept every rule. Validation examples, validation labels, official-test content, and unexplained general-purpose legal keyword lists must not influence the vocabulary or rule behavior.

Every accepted rule must record its category, source type, provenance, rationale, reviewer when applicable, and intended inclusion or exclusion behavior.

#### Required Category-Confusion Cases

The keyword decision tables must distinguish the cases below. Automated tests are optional; if the team creates them, they should cover these same cases.

- Cap on Liability from Uncapped Liability carveouts;
- Uncapped Liability from language saying that a party is not liable;
- Termination for Convenience from termination for breach, default, or cause;
- Post-Termination Services from generic survival language;
- IP Ownership Assignment from License Grant and assignment of the Contract;
- License Grant from ownership transfers and incidental uses of the word “license”;
- Anti-Assignment from Change of Control and IP assignment;
- Change of Control from assignment-only language;
- Renewal Term from the initial contract term; and
- Notice Period to Terminate Renewal from a general termination-notice period.

## L entries

### Leakage

Information from validation or official-test data influencing a development decision, model, rule, threshold, or feature that is supposed to be created without that information.

### `LinearSVC`

A linear support-vector classifier that learns a separate boundary for detecting each Core Category from the TF-IDF features.

### Low-Support Warnings

Use these warning names and rules:

- `low_gold_support`: the category has fewer than 20 distinct positive context groups.
- `low_predicted_support`: a baseline's detections for the category cover fewer than 20 distinct context groups.
- `zero_support`: the official-test evaluation has no usable positive examples or no usable negative examples for the category.

These are warnings, not automatic reasons to remove a category or rerun the models. Keep the category in every required table. Report positive support in chunks, Contracts, and context groups. Also record how many bootstrap repetitions contain no positive support for the category; label its interval unstable when this occurs.

## M entries

### Margin

The signed score from `LinearSVC` showing which side of its learned boundary a chunk falls on; it is used with a threshold and is not a probability.

### Mask

A marker that keeps a chunk-category pair traceable but excludes it from training, threshold selection, metrics, and error lists because its label cannot be used reliably.

### Metric Calculation Rules

The evaluation unit is one unmasked `(chunk_id, category_id)` pair. A masked pair remains traceable but does not enter threshold selection, metrics, or error lists. Overlapping chunks remain separate evaluation units.

For each baseline, data split, and Core Category, report:

- true positives (`TP`);
- false positives (`FP`);
- false negatives (`FN`);
- true negatives (`TN`);
- positive and negative support;
- predicted-positive count;
- precision;
- recall; and
- F1.

Calculate the metrics as follows:

- precision = `TP / (TP + FP)`;
- recall = `TP / (TP + FN)`; and
- F1 = `2TP / (2TP + FP + FN)`.

Return zero when a metric's denominator is zero and attach the relevant support warning. In an evaluation table, an unqualified **support** value means the number of unmasked gold-positive chunks. Report Contract and context-group support separately when applying support warnings.

Calculate macro-F1 as the ordinary, equally weighted average of the 10 category F1 scores. Calculate micro precision, recall, and F1 after pooling `TP`, `FP`, `FN`, and `TN` across all 10 categories. Keep full-precision machine-readable values and display enough decimal places to reproduce rankings. Do not use accuracy as the primary success measure.

### `min_df`

The minimum number of model-training chunks in which a word or phrase must appear before TF-IDF includes it as a feature.

### Model split

The team's fixed 80/20 division of the publisher-provided training data into model-training and validation sets.

## N entries

### Non-finite value

A numerical result such as `NaN`, positive infinity, or negative infinity that is not a valid finite number and causes the relevant check to fail.

### Normalization Schema

A **Normalization Schema** describes the standard structure used to organize the project's cleaned data. It identifies each Pandas DataFrame, the columns it must contain, and what each column means.

For example:

```py
import pandas as pd

# Create a DataFrame with the normalization schema
df = pd.DataFrame(columns=['id', 'name', 'age', 'email'])
```

## O entries

### October Recommendation Register

The October recommendation register records evidence-supported possibilities for the next phase. It does not select, schedule, or approve October work. Give each recommendation a stable ID such as `REC-001` and include every field below.

| Field | Required content |
| --- | --- |
| ID | Stable recommendation identity |
| Concise action | A testable possible next step, not a vague aspiration |
| Affected scope | Categories, baseline, module or interface, and Artifact |
| Evidence | Exact links to supporting metrics, intervals, errors, anomalies, and reports |
| Hypothesis | Why the proposed action may address the evidence |
| Proposed experiment or change | What a future planning session could choose to test |
| Expected benefit | The improvement or learning reasonably supported by the evidence |
| Tradeoffs | Complexity, processing cost, explainability, risk, or lost comparability |
| Acceptance criterion | The observable future result needed to accept the change |
| Future evaluation need | The validation design and why the existing official test cannot be reused as new unbiased evidence |
| Dependencies | Required Artifacts, interfaces, permissions, or earlier decisions |
| Rough effort | A planning estimate, not a commitment |
| Suggested owner profile | Helpful starting skills, not a named person |
| Priority | `now`, `next`, `later`, or `not recommended` |
| Reopened Gate | Gate 1, 2, or 3 if adopting the recommendation would change frozen September evidence |

Use this template for each recommendation:

```markdown
## REC-000 — <concise possible action>

- Priority: now | next | later | not recommended
- Affected categories/baseline/module:
- Evidence links:
- Hypothesis:
- Proposed experiment or change:
- Expected benefit:
- Tradeoffs and limitations:
- Acceptance criterion:
- Future validation/evaluation needed:
- Dependencies:
- Rough effort:
- Suggested owner profile:
- Gate reopened if adopted:
```

## P entries

### Paired interval

An uncertainty range for the difference between two baselines calculated by evaluating both baselines on the same bootstrap samples.

### Paired Uncertainty Intervals

Use one paired bootstrap procedure to show how stable the evaluation results are within the CUAD official-test data:

1. Run `10,000` bootstrap repetitions using seed `20260903`.
2. On each repetition, sample `context_group_id` values with replacement. Keep every Contract, overlapping chunk, and category row belonging to a selected context group together.
3. Use the same sampled context groups for the keyword and TF-IDF baselines. This is what makes the comparison **paired**.
4. Keep model predictions and thresholds fixed. Do not fit a model or select a threshold inside a bootstrap repetition.
5. Report 95% percentile intervals for each baseline's macro-F1, micro-F1, and per-category F1.
6. Also report paired 95% percentile intervals for the TF-IDF-minus-keyword differences.

These intervals describe sampling uncertainty within the CUAD official-test data. They do not prove that the results generalize to other legal contracts.

### Percentile interval

An uncertainty range whose lower and upper limits come from selected percentiles of the bootstrap results, such as the 2.5th and 97.5th percentiles for a 95% interval.

### Processing-thread setting

The recorded number of CPU processing threads used by numerical software, which may affect speed and, in some environments, reproducibility.

### Protected label

Another name for an official-test gold label that must not influence development work; “protected” describes how the label may be used, not who may access it.

### Publisher split

The original CUAD assignment of a Contract to either the publisher-provided training data or the publisher-provided official-test data.

## R entries

### Repeatable Error Selection

Create a separate error group for every combination of baseline, Core Category, and error type. With two baselines, 10 categories, and two error types—false positive and false negative—there are 40 groups.

For each group:

1. Review every error when the group contains five or fewer cases. Otherwise, select five.
2. Record groups that contain no errors.
3. Use seed `20260904` and a stable sampling-protocol version.
4. Build a SHA-256 ranking key from the seed, stable evaluation-set ID, baseline ID, category ID, error type, `context_group_id`, and `chunk_id`.
5. Sort by that key and first select no more than one case from each context group.
6. If fewer than five cases have been selected, continue through the ranked cases and fill the remaining spaces.

Do not use an attempt-specific run ID in the ranking key. Do not replace a selected case because it is repetitive, inconvenient, or difficult to interpret.

Use seed `20260905` to create the reviewer order. Two teammates must assess each selected case independently without seeing one another's assessment first.

### Reproducibility Tolerance

A clean rerun must reproduce all discrete results exactly. This includes schemas, IDs, split assignments, chunks, targets and masks, vocabulary and feature order, the selected configuration, thresholds, detections, counts, metrics, samples, and resolved settings.

Only 64-bit floating-point coefficients and raw model margins may use numerical tolerance. They must have the same shape, order, labels, and data type. Compare them using:

- absolute tolerance: `1e-10`; and
- relative tolerance: `1e-8`.

These tolerances allow extremely small numerical differences that can occur across otherwise equivalent runs. A non-finite value, a changed detection, or any other changed discrete result fails the reproducibility check.

Save portable model arrays as non-object NPZ files with JSON metadata. NPZ is NumPy's compressed array format. “Non-object” means that the arrays do not contain serialized Python objects. Do not use pickle or joblib files.

### Run Receipt

The attempt-specific record of who ran a workflow or step, when and where it ran, what happened, and where its logs and outputs can be found.

## S entries

### Seeded iterative multilabel stratification

A repeatable method that assigns whole context groups to model-training or validation while trying to keep the proportions of all 41 categories similar in both sets.

### Span

A continuous start-to-end range of characters in a Document that CUAD identifies as an example of a category.

## T entries

### TF-IDF

Term Frequency–Inverse Document Frequency is a way to represent text numerically by emphasizing words or phrases that matter in a chunk but are not common across all training chunks.

### TF-IDF Fixed Settings

Use one shared TF-IDF vectorizer fitted only on model-training chunk text. Validation and official-test text may use the fitted vectorizer but must not change its vocabulary or weights. When training each category's classifier, exclude the rows masked for that category.

Use these fixed vectorizer settings:

- normalized text produced with the same four steps used by the keyword baseline;
- word tokens matched by `(?u)\b\w+\b`, including one-character and numeric tokens;
- single words and two-word phrases: `ngram_range=(1, 2)`;
- `min_df` is the candidate value `2` or `5`;
- `use_idf=True`;
- `smooth_idf=True`;
- `sublinear_tf=True`;
- L2 row normalization;
- `max_df=1.0`; and
- no maximum feature limit.

For each `min_df` value, train one separate `LinearSVC` classifier per Core Category using each candidate `C` value: `0.1`, `1.0`, and `10.0`. Use these fixed classifier settings:

- L2 penalty;
- squared-hinge loss;
- `dual=True`;
- intercept enabled;
- `tol=1e-4`;
- `max_iter=10000`;
- `class_weight="balanced"`; and
- seed `20260902`.

Exclude masked rows separately for each category. Do not oversample, undersample, duplicate positive chunks, or generate synthetic text. A configuration fails if a classifier lacks positive or negative training examples, does not converge, or produces a non-finite coefficient or margin.

### Threshold Selection Rules

A **threshold** is the score at or above which a model reports that a category was detected. Select thresholds using the validation set only. Freeze the model or keyword rules before looking at validation results.

The metrics used to select a threshold are:

- **Precision:** Of the examples the model detected, how many were correct?
- **Recall:** Of the positive examples in the data, how many did the model find?
- **F1:** A single score that balances precision and recall.

#### Keyword baseline

For each Core Category:

1. Evaluate every whole-number threshold from `1` through that category's maximum possible configured score.
2. A score at or above the threshold is a detection.
3. Select the threshold with the highest validation F1.
4. If thresholds have exactly the same F1, select the one with higher recall.
5. If they also have the same recall, select the lower threshold.

Threshold `0` is not allowed. Do not change the keyword rules after viewing validation results. If the best valid result is weak or has an F1 of zero, preserve and explain that result instead of changing the rules from validation examples.

#### TF-IDF baseline

For every valid TF-IDF configuration and Core Category:

1. Exclude masked validation rows.
2. Confirm that the remaining rows contain at least one positive and one negative example.
3. Treat every distinct finite validation margin as a candidate threshold.
4. A margin at or above the threshold is a detection.
5. Select the threshold with the highest validation F1.
6. Break an exact F1 tie by higher recall and then by the lower threshold.
7. Preserve every candidate threshold with its confusion counts and metrics.

An all-positive result is allowed if these rules select it, but it must be flagged as weak behavior. Do not replace it with an arbitrary threshold.

## W entries

### Workflow Run

One recorded execution of an ordered set of project steps using identified data, code, configuration, and settings.

## Usage Guide

### Example Dialogue

> **Fellow:** “Is a Contract the same thing as a Document?”
>
> **Tech lead:** “Not quite. The Contract is the agreement record, while the Document holds its exact text and character positions. Each Contract-category Annotation Set points to any labeled Spans in that Document.”
>
> **Fellow:** “Does a protected label mean I am not allowed to access it?”
>
> **Tech lead:** “No. Every fellow, the coach, and the Challenge Advisor can access all project materials. The term only means that official-test labels must not influence development work.”
>
> **Fellow:** “What does the model evaluate after the Contract is chunked?”
>
> **Tech lead:** “It evaluates one chunk-category pair at a time. TF-IDF creates the features, LinearSVC produces a margin, and the frozen threshold turns that margin into a detection.”

### How These Terms Relate

- A **Contract** owns its **Document** text and has one **Annotation Set** for each CUAD category; an Annotation Set contains zero or more **Spans**.
- Contracts with the same **`context_group_id`** stay together when the **publisher split** is divided into the team's **model split**.
- Each unmasked **chunk-category pair** receives one baseline prediction that is compared with its **gold label**.
- TF-IDF creates features for `LinearSVC`, `LinearSVC` produces a **margin**, and a threshold turns that margin into a category detection.
- A **Workflow Run** produces **Artifact Bundles** whose **Artifact Manifests** support bundle-integrity checks and whose **Run Receipts** record each execution attempt.
- Many **bootstrap repetitions** produce **percentile intervals**, and using the same repetition for both baselines produces a **paired interval** for their difference.

### Terminology to Use Consistently

- Use **official-test** when referring to the dataset split and **automated test** when referring to optional software tests; do not use “test” alone when the meaning could be unclear.
- Use **source-text excerpt** for Gate 2 examples and **chunk-category pair** for model-training or evaluation rows; do not use “example” when its unit is unclear.
- Use **publisher split** for CUAD's original training-versus-official-test division and **model split** for the team's training-versus-validation division; do not call both simply “the split.”
- Use **margin** for a `LinearSVC` score; do not describe it as a probability or confidence percentage.
- Use **development-use rule** when describing how official-test information is kept out of development; do not use “access restriction” because everyone named in the milestone has access.
- Keep **Artifact Manifest** and **Run Receipt** separate: the manifest describes the reproducible bundle, while the receipt describes one execution attempt.
