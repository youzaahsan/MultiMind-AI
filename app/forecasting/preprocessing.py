from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from app.utils.logging import get_logger

logger = get_logger("ts_preprocessor")

class TimeSeriesPreprocessor:
    """Prepares and engineers chronological features and lag windows for time series forecasting."""

    def prepare_series(
        self,
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        freq: str = "D",
    ) -> pd.DataFrame:
        """Parses dates, handles missing values, and aggregates chronological values."""
        if date_column not in df.columns or target_column not in df.columns:
            raise ValueError(f"Columns '{date_column}' or '{target_column}' not found in dataframe.")

        ts_df = df[[date_column, target_column]].dropna().copy()
        ts_df[date_column] = pd.to_datetime(ts_df[date_column])
        ts_df = ts_df.sort_values(by=date_column)

        # Aggregate duplicates by taking sum
        ts_df = ts_df.groupby(date_column)[target_column].sum().reset_index()

        return ts_df

    def create_features(
        self,
        ts_df: pd.DataFrame,
        date_column: str,
        target_column: str,
        lags: int = 3,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Constructs temporal calendar indicators and autoregressive lag variables."""
        df_feat = ts_df.copy()

        # Calendar features
        dt = df_feat[date_column].dt
        df_feat["trend_idx"] = np.arange(len(df_feat))
        df_feat["month"] = dt.month
        df_feat["day_of_week"] = dt.dayofweek
        df_feat["day_of_month"] = dt.day

        feature_cols = ["trend_idx", "month", "day_of_week", "day_of_month"]

        # Lag features
        for lag in range(1, lags + 1):
            col_name = f"lag_{lag}"
            df_feat[col_name] = df_feat[target_column].shift(lag)
            feature_cols.append(col_name)

        # Rolling statistics
        df_feat["rolling_mean_3"] = df_feat[target_column].shift(1).rolling(window=3, min_periods=1).mean()
        feature_cols.append("rolling_mean_3")

        # Drop rows with NaN from lags
        df_clean = df_feat.dropna().reset_index(drop=True)

        return df_clean, feature_cols
