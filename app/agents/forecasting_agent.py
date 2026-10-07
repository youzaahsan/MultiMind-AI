from pathlib import Path
from typing import Any, Dict
import pandas as pd
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.config.settings import settings

class ForecastingAgent:
    """Specialized agent for time series forecasting and demand prediction."""

    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    def run(self, state: AgentState) -> AgentState:
        query = state.resolved_query or state.user_query

        # Find latest CSV or Excel file
        file_path = state.metadata.get("file_path")
        if not file_path or not Path(file_path).exists():
            data_files = list(settings.UPLOAD_DIR.glob("*.csv")) + list(settings.UPLOAD_DIR.glob("*.xlsx"))
            if data_files:
                file_path = str(data_files[-1])

        if file_path and Path(file_path).exists():
            df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)

            # Heuristically find date and target columns
            date_col = None
            target_col = None

            for c in df.columns:
                c_low = c.lower()
                if not date_col and any(k in c_low for k in ["date", "time", "day", "month", "timestamp"]):
                    date_col = c
                elif not target_col and pd.api.types.is_numeric_dtype(df[c]):
                    target_col = c

            if not date_col or not target_col:
                # If cannot find explicit date, create index date sequence
                date_col = "date"
                df["date"] = pd.date_range(start="2025-01-01", periods=len(df), freq="D")
                num_cols = df.select_dtypes(include=["number"]).columns
                target_col = num_cols[0] if len(num_cols) > 0 else None

            if target_col:
                res = self.tools.forecasting(
                    df=df,
                    date_column=date_col,
                    target_column=target_col,
                    horizon_periods=7,
                )

                state.tool_calls.append(ToolCallRecord(
                    tool_name="forecasting",
                    arguments={"file": Path(file_path).name, "target": target_col, "horizon": 7},
                    output={"metrics": res["metrics"]},
                ))

                pts = res["forecast_points"]
                lines = [
                    f"### Forecast Projections for '{target_col}' ({Path(file_path).name})\n",
                    f"- **Model Used:** {res['model_type'].title()} Autoregressive Forecaster",
                    f"- **Validation Metrics:** MAE: {res['metrics'].get('mae')}, RMSE: {res['metrics'].get('rmse')}, MAPE: {res['metrics'].get('mape_percent')}%\n",
                    "**Projected Values (Next 7 Periods):**",
                ]
                for p in pts:
                    lines.append(f"- **{p['date']}:** {p['forecast_value']:,}")

                state.final_response = "\n".join(lines)
                state.sources = [{"filename": Path(file_path).name, "page": 1, "section": "Predictive Modeling"}]
            else:
                state.final_response = "Dataset does not contain a numeric column suitable for time series forecasting."
        else:
            state.final_response = "Please upload a time series dataset (CSV/Excel) to perform forecasting."

        return state
