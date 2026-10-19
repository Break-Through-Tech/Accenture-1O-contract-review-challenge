# Accenture Contract Review Challenge

---

### 👥 **Team Members**

| Name | GitHub Handle | Contribution |
|---|---|---|
| Amie Binan | @Flippyfun02 | Data loading and normalization, category evidence, baseline modeling, training harness, LoRA runs |
| Aishat Kolawole | @AishatK21 | EDA, reproducibility verification, review bundles, chunk validation, comparison pre-registration |
| Maya Mukabe | @MayaMukabe | Category selection, chunking comparison, encoder/tokenizer pre-registration, evaluation and model selection |
| Quinn Hinde-Schuster | @quinnhs | Train/validation split, independent category review, keyword baseline, evaluation, verification and reporting |
| Liliana Hidalgo | @LilianaHid | Baseline modeling, target/mask table, support and class-weight analysis, model inspection |

---

## 🎯 **Project Highlights**

- Built a contract-review NLP pipeline using the **Contract Understanding Atticus Dataset (CUAD)**.
- Normalized and validated **408 contracts, 408 documents, 41 categories, 16,728 annotation sets, and 11,180 annotated spans**.
- Established a fixed **80/20 train-validation split** using `context_group_id`, multilabel stratification, and a reproducible seed.
- Narrowed the original **41 CUAD categories to 10 priority categories** for the initial modeling scope.
- Compared multiple long-document chunking strategies and selected **paragraph-based chunking**, which achieved approximately **97.14% span coverage** with a **2.86% boundary-split rate**.
- Developed and evaluated keyword, TF-IDF, and logistic-regression baseline approaches.
- Began transformer-model development using **Hugging Face**, encoder/tokenizer comparison, LoRA planning, class-imbalance handling, and pre-registered model-selection rules.
- Designed the project around reproducibility, validation, independent review, error analysis, and clear separation between validation and official-test results.

---

## 👩🏽‍💻 **Setup and Installation**

The project is developed primarily in **Google Colab** and Python notebooks, with shared code and project artifacts maintained in GitHub.

The repository contains normalized CUAD data, frozen split files, reusable utility functions, chunking helpers, baseline-model outputs, evaluation artifacts, and milestone-specific notebooks.

The project uses Python libraries including:

- Pandas and NumPy for data processing and analysis
- Scikit-learn for baseline machine-learning models and evaluation
- Hugging Face Transformers for tokenizers and transformer encoders
- Sentence Transformers for embedding-based baseline modeling
- PyTorch for transformer training
- PEFT/LoRA for parameter-efficient fine-tuning

Shared data and artifacts are loaded either directly from the repository or from frozen project outputs to keep results consistent across team members.

The notebooks are organized around the project pipeline, beginning with data preparation and validation, followed by category analysis, chunking, baseline modeling, transformer development, evaluation, error analysis, and final verification.

---

## 🏗️ **Project Overview**

This project is part of the **Break Through Tech AI/ML Fellowship with Cornell Tech for the 2026–2027 cohort**. The year-long fellowship consists of four main sections:

* Spring: Python Bootcamp
* Summer: Machine Learning Certificate Bootcamp
* Fall: AI Studio
* Spring: AI Specializations

This project takes place during the Fall AI Studio, where fellows are placed into teams and partnered with industry host companies to apply their machine learning skills to real-world business problems.

Our team is partnered with **Accenture** to explore how natural language processing and machine learning can support the review of commercial contracts.

The project focuses on identifying important contractual clauses, classifying contract text across selected CUAD categories, preserving useful evidence from long documents, and evaluating models that can help prioritize information for human review.

Commercial contracts may contain large amounts of legal text covering liability, renewal, licensing, financial obligations, termination, and other business-critical provisions. Manually locating and reviewing this information can be time-consuming.

Our goal is to develop a reproducible contract-review pipeline that can support reviewers by identifying relevant clauses and organizing evidence for further analysis. The system is intended as **decision support and not as a replacement for professional legal review**.

---

## 📊 **Data Exploration**

The project uses the **Contract Understanding Atticus Dataset (CUAD)**, which contains commercial contracts annotated for legal clause categories.

The normalized project data contains:

| Data Component | Count |
|---|---:|
| Contracts | 408 |
| Documents | 408 |
| Categories | 41 |
| Annotation Sets | 16,728 |
| Annotated Spans | 11,180 |

The raw project data was normalized into separate tables for:

- Contracts
- Documents
- Categories
- Annotation sets
- Annotated clause spans

A frozen train-validation split was created using `context_group_id` as the split unit. The split uses multilabel stratification and a fixed seed to support reproducibility and prevent context-group leakage between training and validation data.

Exploratory data analysis examines:

- Contract and document lengths
- Category support
- Category co-occurrence
- Annotation density
- Missing values and anomalies
- Chunking-related document statistics
- Positive-example support across categories

The team also performs reproducibility checks on IDs, links, duplicate records, span locations, split isolation, leakage protection, and artifact integrity.

### Current 10-Category Scope

The original CUAD dataset includes **41 clause categories**. For the initial modeling scope, the team selected 10 categories based on positive-data support, business relevance, category coverage, annotation evidence, and project review priorities.

The current working categories are:

1. Governing Law
2. Renewal Term
3. Revenue / Profit Sharing
4. Cap on Liability
5. Uncapped Liability
6. Termination for Convenience
7. Anti-Assignment
8. Audit Rights
9. License Grant
10. Exclusivity

The team also built supporting evidence for the categories, reviewed positive and hard-negative examples, examined category co-occurrence, created review bundles, and independently reviewed annotations for unclear or inconsistent cases.

### Long-Document Chunking

Because many contracts are much longer than the input limits of transformer models, the project compares several chunking strategies:

- 512 tokens with no overlap
- 512 tokens with 64-token overlap
- 512 tokens with 128-token overlap
- Paragraph-based chunking

The methods are evaluated using:

- Span coverage
- Boundary splits
- Masking
- Additional chunks
- Processing cost

Paragraph-based chunking currently provides the strongest overall balance, achieving approximately:

- **97.14% span coverage**
- **2.86% boundary splits**

The approved chunks are also validated for IDs, hashes, boundaries, positive and negative targets, category rows, and preservation of positive annotations.

---

## 🧠 **Model Development**

The project follows a staged modeling approach, beginning with simpler baselines before moving to transformer-based models.

### Baseline Models

The team has developed multiple baseline approaches, including:

- Keyword-based classification rules
- TF-IDF-based classification
- Logistic-regression classification using transformer embeddings

Baseline development includes:

- Per-category classifiers
- Threshold selection
- Hyperparameter comparison
- Mask-aware evaluation
- Validation diagnostics
- Saved model artifacts
- Separate validation and official-test evaluation

The logistic-regression baseline uses transformer-based sentence embeddings generated from contract chunks before applying a classifier for each category.

### Transformer Modeling

The October milestone focuses on developing a transformer-based multi-label classification pipeline.

Current work includes:

- Encoder and tokenizer comparison
- Compute-fit analysis
- Token-length and truncation audits
- LoRA configuration
- Fixed random seeds
- Run limits and fallback rules
- Class-imbalance treatment
- Training harness development
- Mask-aware binary cross-entropy loss
- Per-category threshold selection
- Reproducible evaluation

Candidate encoders being explored include:

- DistilRoBERTa
- RoBERTa-base
- Legal-BERT

Legal-BERT is currently being investigated as a leading candidate because of its legal-domain pretraining and more efficient tokenization of the contract chunks.

The transformer training plan includes **LoRA (Low-Rank Adaptation)** to reduce memory and compute requirements while adapting the pretrained model to the contract-classification task.

Class imbalance is also being addressed through training-only support analysis and positive-class weighting.

Model development is still in progress, and the final transformer configuration has not yet been frozen.

---

## 📈 **Results & Key Findings**

The project is still in progress, so current results represent baseline and preprocessing findings rather than final project conclusions.

### Data and Preprocessing Findings

- The project contains **408 contracts** across **41 CUAD categories**.
- Category support varies significantly, creating a class-imbalance challenge.
- Paragraph-based chunking currently provides the strongest clause-preservation performance among the tested chunking strategies.
- Token-length audits show that different tokenizers represent the same legal text differently, which affects model input length and truncation risk.
- Fresh tokenizer-specific token counts are being used for the transformer pipeline rather than relying only on historical stored token counts.

### Baseline Modeling

The team has evaluated baseline models using metrics including:

- Precision
- Recall
- F1 score
- Macro F1
- Micro F1
- Precision-Recall AUC
- Category-level precision, recall, and F1

The current baseline provides a reference point for determining whether the transformer-based model improves contract-clause classification.

Evaluation work also examines false positives, false negatives, category-specific behavior, and differences between validation and official-test performance.

Results will continue to be updated as transformer training, evaluation, verification, and error analysis are completed.

---

## 🚀 **Next Steps**

The project is currently moving from baseline modeling into transformer development and evaluation.

Upcoming work includes:

- Finalizing encoder, tokenizer, and model pre-registration
- Completing category-support and class-weight analysis
- Building the transformer training harness
- Running weighted and unweighted LoRA experiments
- Freezing the selected checkpoint, tokenizer, thresholds, and model configuration
- Producing row-level baseline predictions for comparison
- Evaluating per-category precision, recall, and F1
- Comparing transformer performance with keyword, TF-IDF, and logistic-regression baselines
- Performing an independent verification pass
- Running the authorized locked evaluation
- Generating complete false-positive and false-negative populations
- Conducting independent error reviews
- Categorizing model failure patterns
- Documenting limitations, compute costs, and reproducibility results
- Preparing the final project handoff and retrospective

Current limitations being monitored include:

- Strong class imbalance across categories
- Limited positive examples for some clauses
- Long-contract input constraints
- Tokenizer-dependent chunk lengths
- Variation in contract formatting
- Annotation ambiguity
- Transformer compute requirements

---

## 📝 **License**

The project license is currently **pending approval from the team and Challenge Advisor**.

---

## 📄 **References**

- Contract Understanding Atticus Dataset (CUAD)
- Hugging Face Transformers
- Sentence Transformers
- Legal-BERT
- Break Through Tech AI Studio
- Cornell Tech
- Accenture

---

## 🙏 **Acknowledgements**

We thank **Accenture** for serving as our AI Studio industry partner and supporting the development of this project.

We also thank **Break Through Tech AI**, **Cornell Tech**, our **AI Studio Coach**, **Challenge Advisor**, teaching staff, and team members for their guidance, feedback, technical support, and collaboration throughout the project.
