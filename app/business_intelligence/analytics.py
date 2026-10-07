from typing import Any, Dict, List, Optional
import pandas as pd
from app.utils.logging import get_logger

logger = get_logger("bi_analytics")

class BusinessAnalytics:
    """Performs deep aggregations for products, customers, and categories."""

    @staticmethod
    def analyze_dimensions(
        df: pd.DataFrame,
        value_col: str,
        dimension_col: str,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Groups by a dimension (e.g. Product or Category) and ranks by value."""
        if value_col not in df.columns or dimension_col not in df.columns:
            return []

        grouped = (
            df.groupby(dimension_col)[value_col]
            .sum()
            .reset_index()
            .sort_values(by=value_col, ascending=False)
        )
        total_val = grouped[value_col].sum()

        results = []
        for _, row in grouped.head(top_n).iterrows():
            dim_val = str(row[dimension_col])
            val = float(row[value_col])
            share_pct = round((val / total_val * 100), 2) if total_val > 0 else 0.0
            results.append({
                "dimension": dim_val,
                "total_value": round(val, 2),
                "share_percent": share_pct,
            })

        return results
