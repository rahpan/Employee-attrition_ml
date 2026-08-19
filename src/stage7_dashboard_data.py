"""Prepare privacy-safe aggregate data for the Streamlit dashboard."""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_PATH = PROJECT_ROOT / "docs" / "stage6_sample_aggregate_output.csv"
REQUIRED_COLUMNS = {
    "Department", "employees", "high_risk_count",
    "average_predicted_probability", "high_risk_rate", "reporting_status",
}


def load_aggregate_output(path: Path = AGGREGATE_PATH) -> pd.DataFrame:
    """Load and validate the approved aggregate scoring output."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    assert not missing, f"Missing dashboard columns: {sorted(missing)}"
    assert "EmployeeNumber" not in df.columns
    assert (df["employees"] > 0).all()
    return df


def filter_reported_departments(df: pd.DataFrame, departments=None) -> pd.DataFrame:
    """Return approved, reported groups selected by the user."""
    filtered = df[df["reporting_status"] == "reported"].copy()
    if departments:
        filtered = filtered[filtered["Department"].isin(departments)].copy()
    return filtered.sort_values("high_risk_rate", ascending=False).reset_index(drop=True)


def dashboard_kpis(df: pd.DataFrame):
    """Calculate weighted portfolio KPIs from aggregate rows."""
    if df.empty:
        return {
            "employees": 0, "high_risk_count": 0,
            "high_risk_rate": 0.0, "weighted_average_score": 0.0,
        }
    employees = int(df["employees"].sum())
    high_risk_count = int(df["high_risk_count"].sum())
    weighted_score = float(
        (df["average_predicted_probability"] * df["employees"]).sum() / employees
    )
    return {
        "employees": employees,
        "high_risk_count": high_risk_count,
        "high_risk_rate": float(high_risk_count / employees),
        "weighted_average_score": weighted_score,
    }
