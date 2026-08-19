"""Download and validate the public synthetic IBM employee attrition dataset."""

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

DATA_URL = (
    "https://raw.githubusercontent.com/mrc03/"
    "IBM-HR-Analytics-Employee-Attrition-Performance/master/"
    "WA_Fn-UseC_-HR-Employee-Attrition.csv"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "employee_attrition.csv"

EXPECTED_ROWS = 1470
EXPECTED_COLUMNS = 35
EXPECTED_TARGET_VALUES = {"Yes", "No"}
CONSTANT_COLUMNS = {"EmployeeCount", "Over18", "StandardHours"}


def download_data(path: Path = DATA_PATH) -> Path:
    """Download the dataset only when it is not already available locally."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urlretrieve(DATA_URL, path)
    return path


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the CSV after ensuring that it exists."""
    return pd.read_csv(download_data(path))


def validate_data(df: pd.DataFrame) -> dict[str, object]:
    """Run the Stage 1 structural and business-rule validations."""
    assert df.shape == (EXPECTED_ROWS, EXPECTED_COLUMNS), (
        f"Expected {(EXPECTED_ROWS, EXPECTED_COLUMNS)}, received {df.shape}"
    )
    assert set(df["Attrition"].unique()) == EXPECTED_TARGET_VALUES
    assert df["EmployeeNumber"].notna().all()
    assert df["EmployeeNumber"].is_unique

    nonnegative_columns = [
        "Age",
        "DistanceFromHome",
        "MonthlyIncome",
        "TotalWorkingYears",
        "YearsAtCompany",
        "YearsInCurrentRole",
        "YearsSinceLastPromotion",
        "YearsWithCurrManager",
    ]
    assert (df[nonnegative_columns] >= 0).all().all()

    observed_constant_columns = {
        column for column in df.columns if df[column].nunique(dropna=False) == 1
    }
    assert CONSTANT_COLUMNS.issubset(observed_constant_columns)

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_employees": int(df["EmployeeNumber"].nunique()),
        "attrition_count": df["Attrition"].value_counts().to_dict(),
        "attrition_rate": float((df["Attrition"] == "Yes").mean()),
        "constant_columns": sorted(observed_constant_columns),
    }


def main() -> None:
    """Print a concise, reproducible Stage 1 report."""
    df = load_data()
    report = validate_data(df)
    print("Stage 1 data-quality report")
    for key, value in report.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
