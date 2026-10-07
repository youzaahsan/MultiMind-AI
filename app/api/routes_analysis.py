from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import pandas as pd
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories import AnalyticsRepository
from app.ml.inference import MLPredictor
from app.business_intelligence.kpis import KPICalculator
from app.business_intelligence.analytics import BusinessAnalytics
from app.business_intelligence.insights import BIInsightGenerator
from app.forecasting.inference import TimeSeriesForecaster
from app.utils.logging import get_logger

logger = get_logger("routes_analysis")
router = APIRouter()

class MLAnalysisRequest(BaseModel):
    file_path: str
    task_type: str = "classification"  # classification, regression, clustering, anomaly_detection
    target_column: Optional[str] = None
    model_name: Optional[str] = None
    n_clusters: int = 3

class BIAnalyticsRequest(BaseModel):
    file_path: str
    revenue_column: Optional[str] = None
    cost_column: Optional[str] = None
    dimension_column: Optional[str] = None

class ForecastRequest(BaseModel):
    file_path: str
    date_column: str
    target_column: str
    horizon_periods: int = 7
    model_type: str = "ridge"

def _load_df(file_path: str) -> pd.DataFrame:
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data file '{file_path}' not found.")
    try:
        if p.suffix.lower() == ".csv":
            return pd.read_csv(p)
        elif p.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(p)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported data file format. Use CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read file: {e}")

@router.post("/analyze-data")
def run_ml_analysis(payload: MLAnalysisRequest, db: Session = Depends(get_db)):
    """Executes full ML pipeline (cleaning, encoding, scaling, training, evaluation) on dataset."""
    df = _load_df(payload.file_path)
    predictor = MLPredictor()
    try:
        results = predictor.run_pipeline(
            df=df,
            task_type=payload.task_type,
            target_column=payload.target_column,
            model_name=payload.model_name,
            n_clusters=payload.n_clusters,
        )
        # Save to database
        summary = f"Executed {payload.task_type} model on {Path(payload.file_path).name}."
        AnalyticsRepository.save_analysis(
            db=db,
            filename=Path(payload.file_path).name,
            analysis_type=payload.task_type,
            summary=summary,
            raw_results=results,
            insights=[],
        )
        return results
    except Exception as e:
        logger.error(f"ML analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/analytics")
def calculate_bi_analytics(payload: BIAnalyticsRequest, db: Session = Depends(get_db)):
    """Computes Revenue, Cost, Profit, Profit Margins, Growth Rates, and dimension breakdowns."""
    df = _load_df(payload.file_path)
    kpis = KPICalculator.calculate_core_kpis(
        df=df,
        revenue_col=payload.revenue_column,
        cost_col=payload.cost_column,
    )
    dimensions = []
    if payload.dimension_column and payload.revenue_column:
        dimensions = BusinessAnalytics.analyze_dimensions(
            df=df,
            value_col=payload.revenue_column,
            dimension_col=payload.dimension_column,
        )

    insights = BIInsightGenerator.generate_insights(kpis, dimensions)

    # Save to database
    summary = f"Computed BI KPIs for {Path(payload.file_path).name}."
    AnalyticsRepository.save_analysis(
        db=db,
        filename=Path(payload.file_path).name,
        analysis_type="business_intelligence",
        summary=summary,
        raw_results={"kpis": kpis, "dimensions": dimensions},
        insights=insights,
    )

    return {
        "filename": Path(payload.file_path).name,
        "kpis": kpis,
        "dimensions": dimensions,
        "insights": insights,
    }

@router.post("/forecast")
def run_forecasting(payload: ForecastRequest, db: Session = Depends(get_db)):
    """Executes time series demand/sales/revenue forecasting with out-of-sample metrics."""
    df = _load_df(payload.file_path)
    forecaster = TimeSeriesForecaster()
    try:
        results = forecaster.forecast(
            df=df,
            date_column=payload.date_column,
            target_column=payload.target_column,
            horizon_periods=payload.horizon_periods,
            model_type=payload.model_type,
        )
        # Save to database
        AnalyticsRepository.save_forecast(
            db=db,
            filename=Path(payload.file_path).name,
            date_column=payload.date_column,
            target_column=payload.target_column,
            model_name=payload.model_type,
            horizon_periods=payload.horizon_periods,
            metrics=results["metrics"],
            historical_points=results["historical_points"],
            forecast_points=results["forecast_points"],
        )
        return results
    except Exception as e:
        logger.error(f"Forecasting error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
