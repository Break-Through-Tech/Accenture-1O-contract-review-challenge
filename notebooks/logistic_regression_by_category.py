from sklearn.linear_model import LogisticRegression
import pandas as pd

class LogisticRegressionByCategory:
    """One binary logistic regression per category, on chunk embeddings."""

    def __init__(self, categories, **lr_kwargs):
        """
        :param categories: ids of all categories to be classified
        :param lr_kwargs:  arguments for scikit-learn's logistic regression
        """
        self.lr_kwargs = {"class_weight": "balanced", **lr_kwargs}
        self.categories = categories
        self.models = {}

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

    def predict_proba(self, X):
        """
        Predicts probability of a chunk being a part of a category, for every category
        :param X: a np.array containing chunk embeddings for test data
        :return:
        """
        return {cat: m.predict_proba(X)[:, 1] for cat, m in self.models.items()}

    def predict(self, X, threshold: float | dict=0.5, index=None):
        """
        :param X: np.array of chunk embeddings
        :param threshold: float, or dict of category -> float
        :param index: chunk ids for the rows of X (e.g. test_chunks["chunk_id"])
        :return: DataFrame of 0/1 predictions, one column per category
        """
        proba = pd.DataFrame(self.predict_proba(X), index=index)
        if isinstance(threshold, dict):
            return pd.DataFrame(
                {cat: (proba[cat] >= threshold.get(cat, 0.5)).astype(int) for cat in proba.columns}
            )
        return (proba >= threshold).astype(int)
