from typing import Any, Dict, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.cluster import KMeans
from app.utils.logging import get_logger

logger = get_logger("ml_training")

class MLModelTrainer:
    """Trains classification, regression, clustering, and anomaly detection models."""

    def train_classification(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = "random_forest",
    ) -> Any:
        if model_type == "logistic_regression":
            model = LogisticRegression(max_iter=1000, random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=100, random_state=42)

        model.fit(X_train, y_train)
        return model

    def train_regression(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = "random_forest",
    ) -> Any:
        if model_type == "ridge":
            model = Ridge(alpha=1.0)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        model.fit(X_train, y_train)
        return model

    def train_clustering(
        self,
        X: np.ndarray,
        n_clusters: int = 3,
    ) -> KMeans:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X)
        return kmeans

    def train_anomaly_detection(
        self,
        X: np.ndarray,
        contamination: float = 0.05,
    ) -> IsolationForest:
        iso = IsolationForest(contamination=contamination, random_state=42)
        iso.fit(X)
        return iso
