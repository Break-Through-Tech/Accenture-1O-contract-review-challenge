from sklearn.linear_model import LogisticRegression
import pandas as pd
import numpy as np

class LogisticRegressionByCategory:
    """One binary logistic regression per category, on chunk embeddings."""

    def __init__(self, categories, **lr_kwargs):
        """
        :param categories: ids of all categories to be classified
        :param lr_kwargs:  arguments for scikit-learn's logistic regression
        """
        self.lr_kwargs = {**lr_kwargs}
        self.categories = categories
        self.models = {}
        self.threshold = 0.5

    def fit(self, X, y):
        """
        Trains a Logistic Regression model for each of the categories
        :param X: np.array containing chunk embeddings for training data
        :param y: DataFrame aligned with X, providing 0/1 per category
        :return:
        """
        # y: DataFrame, one 0/1 column per category, rows aligned with X
        self.models = {
            cat: LogisticRegression(**self.lr_kwargs).fit(X, y[cat])
            for cat in self.categories
        }
        return self

    def predict_proba(self, X, index=None):
        """
        Predicts probability of a chunk being a part of a category, for every category
        :param X: a np.array containing chunk embeddings for test data
        :param index: chunk ids for the rows of X (e.g. test_chunks["chunk_id"])
        :return:
        """
        probs = np.column_stack([
            self.models[c].predict_proba(X)[:, 1]
            for c in self.categories
        ])
        return pd.DataFrame(probs, columns=self.categories, index=index)

    def predict(self, X, threshold=None , index=None):
        """
        :param X: np.array of chunk embeddings
        :param threshold: float, or dict of category -> float
        :param index: chunk ids for the rows of X (e.g. test_chunks["chunk_id"])
        :return: DataFrame of 0/1 predictions, one column per category
        """
        proba = self.predict_proba(X, index=index)

        if threshold is None:
            threshold = self.threshold

        if isinstance(threshold, dict):
            return pd.DataFrame(
                {cat: (proba[cat] >= threshold.get(cat, self.threshold)).astype(int) for cat in self.categories},
                index=proba.index
            )

        return (proba >= threshold).astype(int)
