# Contract Review Challenge

**Company / Org:** Accenture  
**Challenge Advisor:** Sebastian Avery, seb@theaverys.org.uk    
**Program:** Break Through Tech AI Studio - Fall 2026  

---

## 🏢 About Accenture
Accenture is a leading global professional services company that provides a broad range of services and solutions in strategy, consulting, technology, and operations. 

---

## 🎯 The Challenge
### Project Summary
In this project, you will use real-world commercial contracts from the CUAD dataset (510 contracts, 41 expert-annotated clause categories) and NLP techniques including chunk-based multi-label classification with a lightweight pre-trained transformer encoder, paired with an explainable rule-based risk-scoring layer, to build a pipeline that automatically detects key clauses, flags them as Low/Medium/High risk, and rolls these up into a contract-level triage score. The core project will focus on 10 high-impact clause categories selected with the Challenge Advisor, with broader category coverage reserved as a stretch goal. This will help our company address the bottleneck legal and procurement teams face when manually reviewing tens of thousands of contracts a year to find the small number of clauses that carry meaningful risk, enabling reviewers to prioritize which contracts to open first.

### Success Criteria
Success has two tracks:

- For clause detection across the 10 core categories: per-category precision/recall/F1 clearly beating the baseline (accuracy is misleading under CUAD's imbalance), with error analysis on where the model struggles.
- For risk scoring: since there are no ground-truth labels, success means strong Spearman correlation and bucket agreement between the model's risk rankings and the advisor's hand-ranked clauses, plus a sensitivity analysis showing the High/Medium boundary is stable.

Overall, a successful December outcome is a working end-to-end pipeline producing risk-scored clause registers the advisor finds plausible and useful, a clean documented repo, and a final report covering results, limitations, and estimated reviewer time saved — an auditable triage tool the advisor would actually trust, not a black box.

### Stretch Goals
Stretch goals include span extraction, a trained risk model benchmarked against the rule-based baseline, LLM-generated clause explanations, broader category coverage, a Streamlit/Gradio demo, and an active-learning loop using advisor/model disagreements. These extend modeling or usability without affecting core deliverables.

### Project Milestones
Use these milestones to guide your work. Your team will create a GitHub Projects board to track tasks within each milestone.

| Month | Milestone | Key Activities |
|-------|-----------|----------------|
| **September** | Data Understanding & Baseline Modeling | Load the provided JSON train/test splits, run EDA on class imbalance, select the 10 core categories with the Challenge Advisor, build a chunking strategy, and establish a TF-IDF/keyword baseline with per-category metrics. |
| **October** | Transformer Modeling & Evaluation | Fine-tune a lightweight pre-trained transformer encoder for multi-label clause classification, address class imbalance, evaluate with per-category precision/recall/F1, and conduct error analysis. |
| **November** | Risk Scoring & Pipeline Integration | Build and calibrate the rule-based risk-scoring layer, assemble the end-to-end pipeline, and validate risk rankings against advisor-labeled examples. |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset
**Name and Source:** CUAD v1 (Contract Understanding Atticus Dataset), The Atticus Project

**Format:** SQuAD-style JSON with CSV category metadata

**Size:** under 1 GB

**Location:** [Data folder](data/cuad)

### Key Details
- `CUADv1.json` contains 510 commercial contracts and 13,823 annotated answer spans across 41 contract-review categories.
- Use the prepared JSON files: `train_separate_questions.json` contains 408 contracts and `test.json` contains 102 contracts.
- Contract text is already available in each JSON document's `paragraphs[].context` field, with clause questions in `paragraphs[].qas[]` and labeled spans in `paragraphs[].qas[].answers[]`. **Do not parse raw PDFs for this project.**
- `category_descriptions.csv` provides the name, description, answer format, and group for each category.
- Contracts vary substantially in length, so teams should develop a chunking strategy, preserve important legal terminology during cleaning, and account for class imbalance.

---

## 🛠️ Suggested Approach
**ML Problem Type:** NLP, Multi-label Classification & Explainable Risk Scoring

**Algorithm Examples:** TF-IDF/keyword baselines and a lightweight pre-trained transformer encoder such as DistilRoBERTa

**Recommended Libraries:** Hugging Face Transformers, PyTorch, scikit-learn, pandas

**Evaluation Metrics:** Precision, Recall, F1-Score for classification; Spearman Correlation for risk-ranking alignment.

---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project:

**Background Reading:**
- [CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review](https://arxiv.org/abs/2103.06268)
- [CUAD dataset overview from The Atticus Project](https://www.atticusprojectai.org/cuad/)

**Technical Tutorials:**
- [Hugging Face text-classification guide](https://huggingface.co/docs/transformers/main/tasks/sequence_classification)
- [Hugging Face padding and truncation guide](https://huggingface.co/docs/transformers/main/pad_truncation)

**Code Examples:**
- [Official CUAD repository](https://github.com/TheAtticusProject/cuad)
- [Guide to the provided data files](data/cuad/README.md)

**Other:**
- [scikit-learn precision, recall, and F-score documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)

*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🤝 How We'll Work Together

**Official check-ins:** During our biweekly 45-minute AI Studio Lab Section meeting block (2nd and 4th week of every month)

**Communication:** Email (address to be added above); please copy your teammates and AI Studio Coach

**Additional meetings:** Request a team check-in on Zoom as needed

**Response time:** Within 48 business hours; please reach out to your AI Studio Coach with urgent questions

**Recommended Tools:**
- **Coding:** Google Colab
- **Collaboration:** GitHub
- **Virtual Meetings:** Zoom

---

## 🚀 Getting Started

1. **Review this overview document** and note any questions for our first meeting
2. **Begin reviewing the JSON dataset** in the [data folder](data/cuad)
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

I’m excited to work with you!

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th (Break Through Tech’s Bridge to Studio - Session C). 
