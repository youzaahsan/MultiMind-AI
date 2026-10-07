from datetime import timedelta
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.forecasting.preprocessing import TimeSeriesPreprocessor
from app.forecasting.model import TimeSeriesModel
from app.forecasting.training import TimeSeriesTrainer
from app.utils.logging import get_logger

logger = get_logger("ts_forecaster")

class TimeSeriesForecaster:
    """Orchestrates end-to-end forecasting: data preparation, model training, evaluation, and future recursive projections."""

    def __init__(self):
        self.preprocessor = TimeSeriesPreprocessor()
        self.trainer = TimeSeriesTrainer()

    def forecast(
        self,
        df: pd.DataFrame,
        date_column: str,
        target_column: str,
        horizon_periods: int = 7,
        model_type: str = "ridge",
    ) -> Dict[str, Any]:
        if df.empty:
            raise ValueError("Input DataFrame is empty")

        # 1. Clean and aggregate
        ts_df = self.preprocessor.prepare_series(df, date_column, target_column)
        if len(ts_df) < 5:
            raise ValueError(f"Insufficient chronological data points (found {len(ts_df)}, minimum 5 required).")

        # 2. Feature engineering
        lags = min(3, max(1, len(ts_df) // 3))
        df_feat, feature_cols = self.preprocessor.create_features(
            ts_df, date_column, target_column, lags=lags
        )

        X = df_feat[feature_cols].values
        y = df_feat[target_column].values

        # 3. Train/validation split (80/20)
        split_idx = max(int(len(X) * 0.8), len(X) - 2)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        model = TimeSeriesModel(model_type=model_type)
        metrics = self.trainer.train_and_evaluate(model, X_train, y_train, X_test, y_test)

        # Refit on all historical data
        model.fit(X, y)

        # 4. Recursive Future Forecasting
        last_date = ts_df[date_column].iloc[-1]
        last_trend = df_feat["trend_idx"].iloc[-1]
        recent_values = list(ts_df[target_column].iloc[-lags:])

        # Determine frequency (days or months)
        if len(ts_df) > 1:
            delta = (ts_df[date_column].iloc[-1] - ts_df[date_column].iloc[-2]).days
            step_days = max(1, delta)
        else:
            step_days = 1

        forecast_points: List[Dict[str, Any]] = []
        curr_date = last_date
        curr_trend = last_trend

        for step in range(1, horizon_periods + 1):
            curr_date += timedelta(days=step_days)
            curr_trend += 1

            # Construct row features
            row = [
                curr_trend,
                curr_date.month,
                curr_date.weekday(),
                curr_date.day,
            ]
            # Add lags (most recent first)
            for i in range(1, lags + 1):
                val = recent_values[-i] if i <= len(recent_values) else recent_values[0]
                row.append(val)

            # Rolling mean 3
            recent_mean = float(np.mean(recent_values[-3:]))
            row.append(recent_mean)

            pred_val = float(model.predict(np.array([row]))[0])
            pred_val = round(max(0.0, pred_val), 2)  # non-negative constraint

            forecast_points.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "forecast_value": pred_val,
                "step": step,
            })

            # Update recent values for next recursive step
            recent_values.append(pred_val)

        # Historical points for chart alignment
        historical_points = [
            {"date": row[date_column].strftime("%Y-%m-%d"), "value": round(float(row[target_column]), 2)}
            for _, row in ts_df.tail(20).iterrows()
        ]

        return {
            "target_column": target_column,
            "date_column": date_column,
            "model_type": model_type,
            "horizon_periods": horizon_periods,
            "metrics": metrics,
            "historical_points": historical_points,
            "forecast_points": forecast_points,
        }
