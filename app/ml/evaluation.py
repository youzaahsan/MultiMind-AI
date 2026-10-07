from typing import Any, Dict
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from app.utils.logging import get_logger

logger = get_logger("ml_evaluation")

class MLEvaluator:
    """Calculates factual, un-fabricated validation metrics for all ML models."""

    @staticmethod
    def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        # Handle binary or multiclass
        is_binary = len(np.unique(y_true)) <= 2
        avg_mode = "binary" if is_binary else "weighted"

        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, average=avg_mode, zero_division=0))
        rec = float(recall_score(y_true, y_pred, average=avg_mode, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average=avg_mode, zero_division=0))

        return {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
        }

    @staticmethod
    def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_true, y_pred))

        return {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "r2_score": round(r2, 4),
        }

    @staticmethod
    def evaluate_clustering(X: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
        num_clusters = len(np.unique(labels))
        # Silhouette score requires at least 2 clusters and less than N samples
        sil = None
        if 2 <= num_clusters < len(X):
            try:
                sil = float(silhouette_score(X, labels))
            except Exception:
                pass

        # Cluster distribution
        counts = {f"cluster_{k}": int(np.sum(labels == k)) for k in np.unique(labels)}

        return {
            "cluster_count": num_clusters,
            "silhouette_score": round(sil, 4) if sil is not None else None,
            "distribution": counts,
        }

    @staticmethod
    def evaluate_anomalies(labels: np.ndarray) -> Dict[str, Any]:
        # IsolationForest returns -1 for anomaly, 1 for normal
        anomalies_count = int(np.sum(labels == -1))
        normal_count = int(np.sum(labels == 1))
        total = len(labels)
        pct = round((anomalies_count / max(total, 1)) * 100, 2)

        return {
            "total_records": total,
            "anomalies_detected": anomalies_count,
            "normal_records": normal_count,
            "anomaly_rate_percent": pct,
        }
