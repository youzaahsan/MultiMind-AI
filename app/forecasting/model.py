from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from app.utils.logging import get_logger

logger = get_logger("ts_model")

class TimeSeriesModel:
    """Wrapper for autoregressive time series predictive models."""

    def __init__(self, model_type: str = "ridge"):
        self.model_type = model_type
        if model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            self.model = Ridge(alpha=1.0)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")
        return self.model.predict(X)
