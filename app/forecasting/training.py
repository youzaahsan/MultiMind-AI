from typing import Any, Dict, Tuple
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from app.forecasting.model import TimeSeriesModel

class TimeSeriesTrainer:
    """Trains time series models and calculates verified out-of-sample metrics."""

    @staticmethod
    def train_and_evaluate(
        model: TimeSeriesModel,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Dict[str, float]:
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        mse = float(mean_squared_error(y_test, preds))
        rmse = float(np.sqrt(mse))

        # MAPE with non-zero protection
        non_zero_mask = y_test != 0
        if np.any(non_zero_mask):
            mape = float(np.mean(np.abs((y_test[non_zero_mask] - preds[non_zero_mask]) / y_test[non_zero_mask])) * 100)
        else:
            mape = 0.0

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape_percent": round(mape, 2),
        }
