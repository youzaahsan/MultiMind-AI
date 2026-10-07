from typing import Any, Dict, List
import numpy as np
import pandas as pd
from app.utils.logging import get_logger

logger = get_logger("features")

class FeatureEngineer:
    """Computes correlation matrices, feature importances, and multicollinearity alerts."""

    def compute_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates pairwise Pearson correlation for all numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return {"matrix": {}, "high_correlations": []}

        corr_matrix = numeric_df.corr().round(4).to_dict()

        # Find strong correlations (|r| >= 0.7)
        high_corr = []
        cols = list(numeric_df.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col1, col2 = cols[i], cols[j]
                val = corr_matrix[col1][col2]
                if abs(val) >= 0.7:
                    high_corr.append({
                        "feature_a": col1,
                        "feature_b": col2,
                        "correlation": val,
                        "relationship": "Strong Positive" if val > 0 else "Strong Negative",
                    })

        return {
            "matrix": corr_matrix,
            "high_correlations": high_corr,
        }
