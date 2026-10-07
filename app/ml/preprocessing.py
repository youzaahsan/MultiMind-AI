from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from app.utils.logging import get_logger

logger = get_logger("ml_preprocessor")

class MLPreprocessor:
    """Cleans, imputes, encodes, and splits tabular data for ML pipelines."""

    def __init__(self):
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: List[str] = []
        self.numeric_columns: List[str] = []
        self.categorical_columns: List[str] = []

    def clean_and_prepare(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], List[str]]:
        """
        Cleans data, imputes missing values, one-hot encodes categoricals,
        scales features, and performs train/test split.
        """
        data = df.copy()
        y = None

        if target_column and target_column in data.columns:
            # Extract target
            y_series = data[target_column]
            # If target has missing values, drop them
            valid_mask = y_series.notnull()
            data = data[valid_mask]
            y_series = y_series[valid_mask]
            data = data.drop(columns=[target_column])
            y = y_series.values

        # Detect column types
        num_cols = list(data.select_dtypes(include=[np.number]).columns)
        cat_cols = list(data.select_dtypes(include=["object", "category"]).columns)

        # Impute missing values
        for c in num_cols:
            median_val = data[c].median() if not data[c].empty else 0.0
            data[c] = data[c].fillna(median_val)

        for c in cat_cols:
            mode_val = data[c].mode()[0] if not data[c].empty and not data[c].mode().empty else "Unknown"
            data[c] = data[c].fillna(mode_val)

        # One-hot encode categoricals if manageable cardinality
        if cat_cols:
            # Keep only columns with cardinality <= 20
            safe_cat_cols = [c for c in cat_cols if data[c].nunique() <= 20]
            data = pd.get_dummies(data, columns=safe_cat_cols, drop_first=True)

        # Drop any remaining non-numeric columns
        data = data.select_dtypes(include=[np.number, bool])
        feature_names = list(data.columns)

        X = data.values.astype(np.float32)

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.feature_columns = feature_names

        if y is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=random_state
            )
            return X_train, X_test, y_train, y_test, feature_names

        return X_scaled, None, None, None, feature_names
