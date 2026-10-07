from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.utils.logging import get_logger

logger = get_logger("bi_kpis")

class KPICalculator:
    """Computes standard financial, commercial, and operational KPIs from tabular data."""

    @staticmethod
    def calculate_core_kpis(
        df: pd.DataFrame,
        revenue_col: Optional[str] = None,
        cost_col: Optional[str] = None,
        order_id_col: Optional[str] = None,
        date_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        # Heuristic detection if columns not provided
        cols_lower = {c.lower(): c for c in df.columns}

        rev_name = revenue_col or cols_lower.get("revenue") or cols_lower.get("sales") or cols_lower.get("amount") or cols_lower.get("price")
        cost_name = cost_col or cols_lower.get("cost") or cols_lower.get("expenses") or cols_lower.get("cogs")
        order_name = order_id_col or cols_lower.get("order_id") or cols_lower.get("id") or cols_lower.get("transaction_id")
        d_name = date_col or cols_lower.get("date") or cols_lower.get("timestamp") or cols_lower.get("order_date")

        total_rev = None
        total_cost = None

        # 1. Total Revenue
        if rev_name and rev_name in df.columns:
            total_rev = float(df[rev_name].sum())
            results["total_revenue"] = round(total_rev, 2)
            results["revenue_column"] = rev_name

        # 2. Total Cost
        if cost_name and cost_name in df.columns:
            total_cost = float(df[cost_name].sum())
            results["total_cost"] = round(total_cost, 2)
            results["cost_column"] = cost_name

        # 3. Profit = Revenue - Cost
        if total_rev is not None and total_cost is not None:
            profit = total_rev - total_cost
            results["gross_profit"] = round(profit, 2)

            # Profit Margin = (Profit / Revenue) * 100
            margin = (profit / total_rev * 100) if total_rev > 0 else 0.0
            results["profit_margin_percent"] = round(margin, 2)

        # 4. Average Order Value (AOV)
        if total_rev is not None:
            if order_name and order_name in df.columns:
                num_orders = df[order_name].nunique()
            else:
                num_orders = len(df)
            aov = (total_rev / num_orders) if num_orders > 0 else 0.0
            results["average_order_value"] = round(aov, 2)
            results["total_orders"] = num_orders

        # 5. Sales Growth Rate over periods
        if d_name and rev_name and d_name in df.columns:
            try:
                temp_df = df[[d_name, rev_name]].dropna().copy()
                temp_df[d_name] = pd.to_datetime(temp_df[d_name])
                temp_df = temp_df.sort_values(by=d_name)
                # Resample by month if multiple dates
                monthly = temp_df.set_index(d_name).resample("ME")[rev_name].sum()
                if len(monthly) >= 2:
                    current_val = float(monthly.iloc[-1])
                    prev_val = float(monthly.iloc[-2])
                    growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0.0
                    results["latest_period_growth_percent"] = round(growth, 2)
                    results["growth_periods_count"] = len(monthly)
            except Exception as e:
                logger.warning(f"Could not compute periodic growth: {e}")

        return results
