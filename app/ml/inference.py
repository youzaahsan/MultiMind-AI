from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.ml.preprocessing import MLPreprocessor
from app.ml.features import FeatureEngineer
from app.ml.training import MLModelTrainer
from app.ml.evaluation import MLEvaluator
from app.utils.logging import get_logger

logger = get_logger("ml_inference")

class MLPredictor:
    """End-to-end ML runner executing preprocessing, training, evaluation, and predictions."""

    def __init__(self):
        self.preprocessor = MLPreprocessor()
        self.feature_eng = FeatureEngineer()
        self.trainer = MLModelTrainer()
        self.evaluator = MLEvaluator()

    def run_pipeline(
        self,
        df: pd.DataFrame,
        task_type: str,  # 'classification', 'regression', 'clustering', 'anomaly_detection'
        target_column: Optional[str] = None,
        model_name: Optional[str] = None,
        n_clusters: int = 3,
    ) -> Dict[str, Any]:
        """Runs the complete data -> training -> evaluation pipeline."""
        if df.empty:
            raise ValueError("Input DataFrame is empty")

        correlations = self.feature_eng.compute_correlations(df)

        if task_type == "classification":
            if not target_column or target_column not in df.columns:
                raise ValueError("Target column is required for classification")
            X_train, X_test, y_train, y_test, feat_names = self.preprocessor.clean_and_prepare(
                df, target_column=target_column
            )
            model = self.trainer.train_classification(X_train, y_train, model_type=model_name or "random_forest")
            preds = model.predict(X_test)
            metrics = self.evaluator.evaluate_classification(y_test, preds)

            return {
                "task": "classification",
                "target_column": target_column,
                "features_used": feat_names,
                "metrics": metrics,
                "model_type": model.__class__.__name__,
                "sample_predictions": [{"actual": str(a), "predicted": str(p)} for a, p in zip(y_test[:5], preds[:5])],
                "correlations": correlations["high_correlations"],
            }

        elif task_type == "regression":
            if not target_column or target_column not in df.columns:
                raise ValueError("Target column is required for regression")
            X_train, X_test, y_train, y_test, feat_names = self.preprocessor.clean_and_prepare(
                df, target_column=target_column
            )
            model = self.trainer.train_regression(X_train, y_train, model_type=model_name or "random_forest")
            preds = model.predict(X_test)
            metrics = self.evaluator.evaluate_regression(y_test, preds)

            return {
                "task": "regression",
                "target_column": target_column,
                "features_used": feat_names,
                "metrics": metrics,
                "model_type": model.__class__.__name__,
                "sample_predictions": [{"actual": float(a), "predicted": float(p)} for a, p in zip(y_test[:5], preds[:5])],
                "correlations": correlations["high_correlations"],
            }

        elif task_type == "clustering":
            X_scaled, _, _, _, feat_names = self.preprocessor.clean_and_prepare(df)
            model = self.trainer.train_clustering(X_scaled, n_clusters=n_clusters)
            labels = model.labels_
            metrics = self.evaluator.evaluate_clustering(X_scaled, labels)

            return {
                "task": "clustering",
                "features_used": feat_names,
                "metrics": metrics,
                "cluster_centers_count": len(model.cluster_centers_),
                "correlations": correlations["high_correlations"],
            }

        elif task_type == "anomaly_detection":
            X_scaled, _, _, _, feat_names = self.preprocessor.clean_and_prepare(df)
            model = self.trainer.train_anomaly_detection(X_scaled)
            labels = model.predict(X_scaled)
            metrics = self.evaluator.evaluate_anomalies(labels)

            return {
                "task": "anomaly_detection",
                "features_used": feat_names,
                "metrics": metrics,
                "model_type": "IsolationForest",
                "correlations": correlations["high_correlations"],
            }

        else:
            raise ValueError(f"Unknown task type: {task_type}")
