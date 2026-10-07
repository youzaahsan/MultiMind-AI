import numpy as np
import pandas as pd
import pytest

from app.ml.inference import MLPredictor
from app.forecasting.inference import TimeSeriesForecaster
from app.business_intelligence.kpis import KPICalculator
from app.business_intelligence.analytics import BusinessAnalytics
from app.business_intelligence.insights import BIInsightGenerator

def test_ml_classification():
    predictor = MLPredictor()
    df = pd.DataFrame({
        "feature1": [1.2, 2.3, 3.1, 8.5, 9.1, 7.8, 2.1, 8.9, 1.5, 9.4],
        "feature2": [0.5, 1.1, 0.9, 5.2, 4.8, 5.9, 0.8, 6.1, 0.4, 5.5],
        "target": [0, 0, 0, 1, 1, 1, 0, 1, 0, 1],
    })
    res = predictor.run_pipeline(df, task_type="classification", target_column="target")
    assert res["task"] == "classification"
    assert "accuracy" in res["metrics"]
    assert res["metrics"]["accuracy"] >= 0.0

def test_ml_clustering():
    predictor = MLPredictor()
    df = pd.DataFrame({
        "x": [1, 2, 1, 10, 11, 10],
        "y": [1, 1, 2, 10, 10, 11],
    })
    res = predictor.run_pipeline(df, task_type="clustering", n_clusters=2)
    assert res["task"] == "clustering"
    assert res["metrics"]["cluster_count"] == 2

def test_ml_anomaly_detection():
    predictor = MLPredictor()
    df = pd.DataFrame({
        "val": [10, 11, 10, 12, 10, 11, 100, 11, 10],
    })
    res = predictor.run_pipeline(df, task_type="anomaly_detection")
    assert res["task"] == "anomaly_detection"
    assert res["metrics"]["total_records"] == 9
    assert res["metrics"]["anomalies_detected"] >= 1

def test_forecasting():
    forecaster = TimeSeriesForecaster()
    dates = pd.date_range(start="2025-01-01", periods=15, freq="D")
    sales = [100 + i * 10 + (i % 3) * 5 for i in range(15)]
    df = pd.DataFrame({"date": dates, "sales": sales})

    res = forecaster.forecast(df, date_column="date", target_column="sales", horizon_periods=5)
    assert res["horizon_periods"] == 5
    assert len(res["forecast_points"]) == 5
    assert "mae" in res["metrics"]
    assert "rmse" in res["metrics"]

def test_business_intelligence_kpis():
    df = pd.DataFrame({
        "revenue": [1000, 2000, 1500],
        "cost": [600, 1200, 900],
        "product": ["Alpha", "Beta", "Alpha"],
    })
    kpis = KPICalculator.calculate_core_kpis(df, revenue_col="revenue", cost_col="cost")
    assert kpis["total_revenue"] == 4500.0
    assert kpis["total_cost"] == 2700.0
    assert kpis["gross_profit"] == 1800.0
    assert kpis["profit_margin_percent"] == 40.0

    dims = BusinessAnalytics.analyze_dimensions(df, value_col="revenue", dimension_col="product")
    assert len(dims) == 2
    assert dims[0]["dimension"] == "Alpha"  # 1000+1500 = 2500

    insights = BIInsightGenerator.generate_insights(kpis, dims)
    assert len(insights) > 0
    assert any("Gross Margin" in i or "margin" in i.lower() for i in insights)
