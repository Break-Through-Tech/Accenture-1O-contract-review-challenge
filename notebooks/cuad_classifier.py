from pathlib import Path

import hashlib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

CHUNK_FIELDS = (
    "chunk_id", "document_id", "contract_id", "context_group_id",
    "chunk_text", "char_start", "char_end",
)

class CUADClassifier:
    def __init__(self, model_dir, tokenizer_dir, categories, thresholds=None, max_length=512, device=None):
        # load model + tokenizer, model.eval(), move to device, store categories
        self.model_version = "cuad_model_v1"
        self.model_dir = model_dir
        self.tokenizer_dir = tokenizer_dir
        self.categories = categories
        self.thresholds = thresholds
        self.max_length = max_length
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)

        self.model.eval()  # switches model from training to inference mode
        self.model.to(self.device)  # use GPU

        # safeguard to check if target labels match up
        if self.model.config.num_labels != len(self.categories):
            raise ValueError(
                f"Model has {self.model.config.num_labels} labels, "
                f"got {len(self.categories)} categories"
            )

    @torch.no_grad()
    def predict_logits(self, texts, batch_size=32) -> np.ndarray:  # (N, 10)
        """
        Predicts logits
        """

        if isinstance(texts, str):
            texts = [texts]
        texts = list(texts)
        if not texts:
            return np.empty((0, len(self.categories)), dtype=np.float32)

        all_logits = []
        # loop through batches of text
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            enc = self.tokenizer(
                batch,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt"
            ).to(self.device)
            outputs = out = self.model(**enc)
            all_logits.append(out.logits.float().cpu().numpy())

        return np.concatenate(all_logits)

    def predict_proba(self, texts, batch_size=32) -> np.ndarray:
        logits = self.predict_logits(texts, batch_size=batch_size)
        return 1.0 / (1.0 + np.exp(-logits))  # sigmoid function

    def score(self, texts, batch_size=32):
        """
        Scores text, classifying it as in a category or not
        """

        if self.thresholds is None:
            raise ValueError("thresholds required for score()")

        scores = self.predict_proba(texts, batch_size)

        thresholds = np.array([self.thresholds[c] for c in self.categories])  # (10,)
        predicted = scores >= thresholds  # (N, 10) bool

        return [
            [
                {
                    "category_id": category,
                    "score": round(float(score), 4),
                    "threshold": float(threshold),
                    "predicted": bool(is_positive),
                }
                for category, score, threshold, is_positive in
                zip(self.categories, score_row, thresholds, predicted_row)
            ]
            for score_row, predicted_row in zip(scores, predicted)
        ]

    def score_chunks(self, df, batch_size=32, text_col="chunk_text"):
        """
        df: one row per chunk. Needs CHUNK_FIELDS columns (text_col is renamed to chunk_text).
        Extra columns (labels, masks, method, num_tokens...) are ignored and never copied out.
        """
        if "chunk_text" not in df.columns:
            if "text" not in df.columns:
                raise KeyError("Need a 'chunk_text' (or 'text') column")
            df = df.rename(columns={"text": "chunk_text"})

        missing = [f for f in CHUNK_FIELDS if f not in df.columns]
        if missing:
            raise KeyError(f"Missing required columns: {missing}")
        if df["chunk_id"].duplicated().any():
            raise ValueError("Duplicate chunk_id values in input")

        records = df[list(CHUNK_FIELDS)].to_dict("records")
        results = self.score([r["chunk_text"] for r in records], batch_size=batch_size)

        return {
            "model_version": self.model_version,
            "chunk_predictions": [
                {
                    **r,
                    "char_start": int(r["char_start"]),
                    "char_end": int(r["char_end"]),
                    "category_results": res,
                }
                for r, res in zip(records, results)
            ],
        }

    @classmethod
    def from_run(cls, root, seed, thresholds, categories, device=None):
        """
        Builds the paths from 'standard' drive folder layout (assumes october_task4_outputs/full_weighted structure)
        """
        rows = thresholds.loc[thresholds["seed"] == seed, ["category", "threshold"]]

        if rows.empty:
            raise ValueError(f"No thresholds for seed {seed}")
        if rows["category"].duplicated().any():
            raise ValueError(f"Duplicate categories for seed {seed}")

        seeded_thr = {c: round(float(t), 2) for c, t in zip(rows["category"], rows["threshold"])}
        root = Path(root)
        model_dir = root / f'final_weighted_Legal-BERT_seed{seed}'
        tokenizer_dir = root / f'run_weighted_Legal-BERT_seed{seed}' / 'checkpoint-2034'

        return cls(model_dir, tokenizer_dir, categories, thresholds=seeded_thr, max_length=512, device=device)


    @staticmethod
    def _sha256_file(path, chunk=1 << 20):
        """
        Hashes an entire file
        """
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while block := f.read(chunk):
                h.update(block)
        return h.hexdigest()


    def hashes(self) -> dict:
        """
        Hashes the model file for later comparison
        """
        model_file = Path(self.model_dir) / "model.safetensors"
        tok_files = ["tokenizer.json", "tokenizer_config.json"]

        return {
            "model.safetensors": self._sha256_file(model_file),
            **{
                name: self._sha256_file(Path(self.tokenizer_dir) / name)
                for name in tok_files
            },
        }
