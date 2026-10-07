from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from app.utils.logging import get_logger

logger = get_logger("csv_processor")

class CSVProcessor:
    """Processes, analyzes, and extracts structured insights from CSV files."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        if self.df is None:
            if not self.file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {self.file_path}")
            try:
                self.df = pd.read_csv(self.file_path)
            except UnicodeDecodeError:
                self.df = pd.read_csv(self.file_path, encoding="latin-1")
        return self.df

    def extract(self) -> Dict[str, Any]:
        """Returns structured metadata, column stats, sample rows, and summary text."""
        df = self.load()
        rows, cols = df.shape
        columns = list(df.columns)

        # Missing values
        missing_counts = df.isnull().sum().to_dict()
        missing_pct = {k: round((v / max(rows, 1)) * 100, 2) for k, v in missing_counts.items()}

        # Dtypes
        dtypes = {col: str(df[col].dtype) for col in columns}

        # Numeric statistics
        numeric_df = df.select_dtypes(include=["number"])
        stats_dict = {}
        if not numeric_df.empty:
            desc = numeric_df.describe().to_dict()
            for col, metrics in desc.items():
                stats_dict[col] = {k: round(v, 4) if isinstance(v, (int, float)) else v for k, v in metrics.items()}

        # Categorical summaries
        cat_df = df.select_dtypes(include=["object", "category"])
        cat_summary = {}
        for col in cat_df.columns:
            top_vals = df[col].value_counts().head(5).to_dict()
            cat_summary[col] = {
                "unique_count": int(df[col].nunique()),
                "top_values": top_vals,
            }

        # Samples
        head_sample = df.head(5).to_dict(orient="records")
        # Native markdown table generator without tabulate dependency
        headers = [str(c) for c in df.columns]
        rows_data = [[str(val) for val in row] for row in df.head(10).values]
        md_lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for r in rows_data:
            md_lines.append("| " + " | ".join(r) + " |")
        markdown_table = "\n".join(md_lines)

        # Build natural text summary for vector store ingestion
        summary_text = self._build_text_summary(rows, cols, columns, stats_dict, cat_summary, missing_pct)

        return {
            "metadata": {
                "filename": self.file_path.name,
                "file_size": self.file_path.stat().st_size,
                "rows": rows,
                "columns_count": cols,
                "columns": columns,
                "dtypes": dtypes,
                "has_missing_values": any(v > 0 for v in missing_counts.values()),
            },
            "statistics": stats_dict,
            "categorical_summary": cat_summary,
            "missing_values": missing_counts,
            "missing_percentages": missing_pct,
            "preview_markdown": markdown_table,
            "sample_rows": head_sample,
            "full_text": summary_text,
        }

    def _build_text_summary(
        self,
        rows: int,
        cols: int,
        columns: List[str],
        stats: Dict[str, Any],
        cat_summary: Dict[str, Any],
        missing: Dict[str, float],
    ) -> str:
        lines = [
            f"Dataset Summary: {self.file_path.name}",
            f"Total Rows: {rows}, Total Columns: {cols}",
            f"Columns: {', '.join(columns)}",
            "",
            "--- Column Data Profiles & Statistics ---",
        ]
        for col, metrics in stats.items():
            lines.append(
                f"Numeric Column '{col}': mean={metrics.get('mean')}, min={metrics.get('min')}, max={metrics.get('max')}, std={metrics.get('std')}"
            )
        for col, data in cat_summary.items():
            lines.append(
                f"Categorical Column '{col}': {data['unique_count']} unique values. Top values: {data['top_values']}"
            )
        lines.append("")
        lines.append("--- Missing Values ---")
        for col, pct in missing.items():
            if pct > 0:
                lines.append(f"Column '{col}' has {pct}% missing data.")
            else:
                lines.append(f"Column '{col}' is complete (0% missing).")

        return "\n".join(lines)
