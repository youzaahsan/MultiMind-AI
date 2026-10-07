from typing import Any, Dict, List
from app.utils.logging import get_logger

logger = get_logger("bi_insights")

class BIInsightGenerator:
    """Derives actionable commercial intelligence and operational highlights from KPI calculations."""

    @staticmethod
    def generate_insights(kpis: Dict[str, Any], dimensions: List[Dict[str, Any]]) -> List[str]:
        insights = []

        # Revenue & Profit Insights
        if "total_revenue" in kpis and "gross_profit" in kpis:
            margin = kpis.get("profit_margin_percent", 0.0)
            if margin >= 30.0:
                insights.append(
                    f"Strong Financial Health: The business maintains a healthy gross margin of {margin}%, "
                    f"generating ${kpis['gross_profit']:,} in gross profit on ${kpis['total_revenue']:,} revenue."
                )
            elif margin > 10.0:
                insights.append(
                    f"Moderate Profitability: Gross profit margin stands at {margin}%. "
                    "Review operational and supplier costs to optimize contribution margins."
                )
            else:
                insights.append(
                    f"Low Margin Warning: Current profit margin is {margin}%. Immediate cost control "
                    "or pricing model realignment is advised."
                )

        # Growth Insight
        if "latest_period_growth_percent" in kpis:
            growth = kpis["latest_period_growth_percent"]
            if growth > 0:
                insights.append(f"Positive Growth Momentum: Period-over-period sales expansion grew by +{growth}%.")
            else:
                insights.append(f"Sales Contraction Notice: Period-over-period performance declined by {growth}%.")

        # Dimension / Concentration Insight
        if dimensions:
            top_item = dimensions[0]
            if top_item.get("share_percent", 0) > 40.0:
                insights.append(
                    f"High Concentration Risk: Top item '{top_item['dimension']}' drives "
                    f"{top_item['share_percent']}% of total volume. Consider diversifying the portfolio."
                )
            else:
                insights.append(
                    f"Leading Contributor: '{top_item['dimension']}' leads performance with a {top_item['share_percent']}% share."
                )

        if not insights:
            insights.append("Dataset analyzed. Insufficient financial columns to compute specialized profit metrics.")

        return insights
