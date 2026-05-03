import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
from logger import get_logger

logger = get_logger("classifier")

CATEGORIES = ["Machine Learning", "NLP", "Computer Vision", "Systems", "Theory"]


class PaperClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
        self.model = LogisticRegression(max_iter=500, C=1.0)
        self.label_encoder = LabelEncoder()
        self.label_encoder.classes_ = np.array(CATEGORIES)
        self.is_trained = False
        self.metrics: dict = {}

    def train(self, df: pd.DataFrame) -> dict:
        logger.info("Training classifier...")
        texts = (df["title"] + " " + df["abstract"]).tolist()
        labels = df["category"].tolist()

        X = self.vectorizer.fit_transform(texts)
        y = self.label_encoder.fit_transform(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, target_names=self.label_encoder.classes_, output_dict=True)

        self.is_trained = True
        self.metrics = {"accuracy": acc, "report": report}
        logger.info(f"Classifier trained | accuracy={acc:.4f}")
        return self.metrics

    def predict(self, title: str, abstract: str) -> str:
        if not self.is_trained:
            return "Unknown"
        text = title + " " + abstract
        X = self.vectorizer.transform([text])
        pred = self.model.predict(X)[0]
        return self.label_encoder.inverse_transform([pred])[0]

    def predict_batch(self, df: pd.DataFrame) -> list[str]:
        if not self.is_trained:
            return ["Unknown"] * len(df)
        texts = (df["title"] + " " + df["abstract"]).tolist()
        X = self.vectorizer.transform(texts)
        preds = self.model.predict(X)
        return self.label_encoder.inverse_transform(preds).tolist()


# Singleton
_classifier = PaperClassifier()


def get_classifier() -> PaperClassifier:
    return _classifier
