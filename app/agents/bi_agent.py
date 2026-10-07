from pathlib import Path
from typing import Any, Dict
import pandas as pd
from app.agents.state import AgentState, ToolCallRecord
from app.agents.tools import ToolRegistry
from app.config.settings import settings

class BusinessIntelligenceAgent:
    """Specialized agent for calculating financial KPIs, margins, and operational intelligence."""

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
            res = self.tools.business_analysis(df)

            state.tool_calls.append(ToolCallRecord(
                tool_name="business_analysis",
                arguments={"file": Path(file_path).name},
                output={"kpis_calculated": list(res["kpis"].keys())},
            ))

            kpis = res["kpis"]
            insights = res["insights"]

            response_lines = [
                "### Business Intelligence & Performance Dashboard\n",
                f"**Financial KPIs for {Path(file_path).name}:**",
            ]
            if "total_revenue" in kpis:
                response_lines.append(f"- **Total Revenue:** ${kpis['total_revenue']:,}")
            if "total_cost" in kpis:
                response_lines.append(f"- **Total Cost:** ${kpis['total_cost']:,}")
            if "gross_profit" in kpis:
                response_lines.append(f"- **Gross Profit:** ${kpis['gross_profit']:,}")
            if "profit_margin_percent" in kpis:
                response_lines.append(f"- **Profit Margin:** {kpis['profit_margin_percent']}%")
            if "average_order_value" in kpis:
                response_lines.append(f"- **Average Order Value (AOV):** ${kpis['average_order_value']:,}")
            if "latest_period_growth_percent" in kpis:
                response_lines.append(f"- **Growth Rate:** {kpis['latest_period_growth_percent']}%")

            response_lines.append("\n**Actionable Strategic Insights:**")
            for ins in insights:
                response_lines.append(f"- {ins}")

            state.final_response = "\n".join(response_lines)
            state.sources = [{"filename": Path(file_path).name, "page": 1, "section": "Financial Metrics"}]
        else:
            state.final_response = (
                "Please upload a sales or financial dataset (CSV/Excel) to compute business KPIs and profit margins."
            )

        return state
