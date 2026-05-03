import os
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from pathlib import Path
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from logger import get_logger

logger = get_logger("publishability")

CATEGORY_LIST = ["Machine Learning", "NLP", "Computer Vision", "Systems", "Theory"]


def _get_tracking_uri() -> str:
    """
    Always returns a proper file:/// URI for MLflow.
    Works on Windows (C:\\path) and Linux (/path) alike.
    """
    env_val = os.getenv("MLFLOW_TRACKING_URI", "")

    if env_val.startswith(("http://", "https://", "file:///")):
        # Already a valid URI — use as-is
        return env_val

    if env_val:
        # Raw path from env var (e.g. C:\Personal\...\mlruns)
        path = Path(env_val).resolve()
    else:
        # Default: mlruns folder inside backend/
        path = (Path(__file__).parent / "mlruns").resolve()

    path.mkdir(parents=True, exist_ok=True)

    # Path.as_uri() correctly produces file:///C:/... on Windows
    return path.as_uri()


class PublishabilityModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_enc = LabelEncoder()
        self.label_enc.classes_ = np.array(CATEGORY_LIST)
        self.is_trained = False
        self.feature_names = [
            "abstract_length",
            "keyword_count",
            "citation_count",
            "year_normalized",
            "category_encoded",
        ]

    def _build_features(self, df: pd.DataFrame) -> np.ndarray:
        feats = pd.DataFrame()
        feats["abstract_length"] = df["abstract"].str.len().fillna(0)
        feats["keyword_count"] = df["keywords"].fillna(0).astype(float)
        feats["citation_count"] = df["citations"].fillna(0).astype(float)
        feats["year_normalized"] = (df["year"].fillna(2020) - 2010) / 14.0
        cats = df["category"].fillna("Machine Learning")
        try:
            feats["category_encoded"] = self.label_enc.transform(cats)
        except ValueError:
            feats["category_encoded"] = 0
        return feats.values.astype(float)

    def _make_pseudo_scores(self, df: pd.DataFrame) -> np.ndarray:
        cit_norm = np.log1p(df["citations"].fillna(0)) / np.log1p(5000)
        len_norm = np.clip(df["abstract"].str.len().fillna(0) / 1000, 0, 1)
        kw_norm  = np.clip(df["keywords"].fillna(0) / 12.0, 0, 1)
        year_norm = (df["year"].fillna(2020) - 2010) / 14.0
        scores = 0.45 * cit_norm + 0.25 * len_norm + 0.15 * kw_norm + 0.15 * year_norm
        noise  = np.random.RandomState(42).normal(0, 0.05, len(scores))
        return np.clip(scores + noise, 0.0, 1.0).values

    def train_all_runs(self, df: pd.DataFrame):
        tracking_uri = _get_tracking_uri()
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"MLflow tracking URI: {tracking_uri}")

        mlflow.set_experiment("Research+ Publishability")

        scores = self._make_pseudo_scores(df)
        X = self._build_features(df)
        X_train, X_test, y_train, y_test = train_test_split(
            X, scores, test_size=0.2, random_state=42
        )

        configs = [
            {"name": "LinearRegression_all_features", "model_type": "LinearRegression", "alpha": None, "features": "all"},
            {"name": "Ridge_alpha0.1",                "model_type": "Ridge",            "alpha": 0.1,  "features": "all"},
            {"name": "Ridge_alpha1.0",                "model_type": "Ridge",            "alpha": 1.0,  "features": "all"},
        ]

        best_mse    = float("inf")
        best_model  = None
        best_scaler = None

        for cfg in configs:
            with mlflow.start_run(run_name=cfg["name"]):
                sc  = StandardScaler()
                Xtr = sc.fit_transform(X_train)
                Xte = sc.transform(X_test)

                m = LinearRegression() if cfg["model_type"] == "LinearRegression" else Ridge(alpha=cfg["alpha"])
                m.fit(Xtr, y_train)

                preds = np.clip(m.predict(Xte), 0, 1)
                mse   = mean_squared_error(y_test, preds)
                r2    = r2_score(y_test, preds)

                mlflow.log_param("model_type", cfg["model_type"])
                mlflow.log_param("alpha",      cfg["alpha"])
                mlflow.log_param("features",   cfg["features"])
                mlflow.log_param("n_features", len(self.feature_names))
                mlflow.log_metric("mse",  mse)
                mlflow.log_metric("r2",   r2)
                mlflow.log_metric("rmse", np.sqrt(mse))
                mlflow.sklearn.log_model(m, "model")

                logger.info(f"MLflow run '{cfg['name']}' | MSE={mse:.4f} R2={r2:.4f}")

                if mse < best_mse:
                    best_mse    = mse
                    best_model  = m
                    best_scaler = sc

        self.model      = best_model
        self.scaler     = best_scaler
        self.is_trained = True
        logger.info(f"Best model selected | MSE={best_mse:.4f}")

    def predict_score(self, title: str, abstract: str, citations: int,
                      year: int, keywords: int, category: str) -> float:
        if not self.is_trained:
            return 0.5
        row = pd.DataFrame([{
            "title": title, "abstract": abstract, "citations": citations,
            "year": year, "keywords": keywords, "category": category,
        }])
        X = self._build_features(row)
        score = float(np.clip(self.model.predict(self.scaler.transform(X))[0], 0.0, 1.0))
        return round(score, 4)

    def predict_batch(self, df: pd.DataFrame) -> list[float]:
        if not self.is_trained:
            return [0.5] * len(df)
        X = self._build_features(df)
        scores = np.clip(self.model.predict(self.scaler.transform(X)), 0, 1)
        return [round(float(s), 4) for s in scores]


_pub_model = PublishabilityModel()

def get_pub_model() -> PublishabilityModel:
    return _pub_model