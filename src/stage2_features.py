"""Define, validate, and prepare the approved Stage 2 ML feature set."""

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "Attrition"
IDENTIFIER_COLUMNS = ["EmployeeNumber"]
CONSTANT_COLUMNS = ["EmployeeCount", "Over18", "StandardHours"]
SENSITIVE_COLUMNS = ["Age", "Gender", "MaritalStatus"]
UNSUPPORTED_RATE_COLUMNS = ["DailyRate", "HourlyRate", "MonthlyRate"]

NUMERIC_FEATURES = [
    "DistanceFromHome", "Education", "EnvironmentSatisfaction", "JobInvolvement",
    "JobLevel", "JobSatisfaction", "MonthlyIncome", "NumCompaniesWorked",
    "PercentSalaryHike", "PerformanceRating", "RelationshipSatisfaction",
    "StockOptionLevel", "TotalWorkingYears", "TrainingTimesLastYear",
    "WorkLifeBalance", "YearsAtCompany", "YearsInCurrentRole",
    "YearsSinceLastPromotion", "YearsWithCurrManager",
]
CATEGORICAL_FEATURES = [
    "BusinessTravel", "Department", "EducationField", "JobRole", "OverTime",
]
APPROVED_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass(frozen=True)
class FeatureBundle:
    """Separate model inputs, label, identifiers, and fairness-review fields."""
    features: pd.DataFrame
    label: pd.Series
    identifiers: pd.DataFrame
    fairness_review: pd.DataFrame


def validate_business_rules(df: pd.DataFrame) -> None:
    """Validate coded values and employment-history consistency."""
    expected = set(APPROVED_FEATURES + SENSITIVE_COLUMNS + IDENTIFIER_COLUMNS + [TARGET])
    missing = expected.difference(df.columns)
    assert not missing, f"Missing required columns: {sorted(missing)}"
    assert set(df[TARGET].dropna().unique()) == {"Yes", "No"}
    assert df["EmployeeNumber"].is_unique
    assert df["EmployeeNumber"].notna().all()

    coded_ranges = {
        "Education": (1, 5), "EnvironmentSatisfaction": (1, 4),
        "JobInvolvement": (1, 4), "JobLevel": (1, 5),
        "JobSatisfaction": (1, 4), "PerformanceRating": (1, 4),
        "RelationshipSatisfaction": (1, 4), "StockOptionLevel": (0, 3),
        "WorkLifeBalance": (1, 4),
    }
    for column, (minimum, maximum) in coded_ranges.items():
        assert df[column].between(minimum, maximum).all(), f"Invalid values in {column}"

    assert (df["YearsAtCompany"] <= df["TotalWorkingYears"]).all()
    assert (df["YearsInCurrentRole"] <= df["YearsAtCompany"]).all()
    assert (df["YearsSinceLastPromotion"] <= df["YearsAtCompany"]).all()
    assert (df["YearsWithCurrManager"] <= df["YearsAtCompany"]).all()


def build_feature_bundle(df: pd.DataFrame) -> FeatureBundle:
    """Create explicitly separated datasets without fitting any transformation."""
    validate_business_rules(df)
    return FeatureBundle(
        features=df[APPROVED_FEATURES].copy(),
        label=df[TARGET].map({"No": 0, "Yes": 1}).astype("int8"),
        identifiers=df[IDENTIFIER_COLUMNS].copy(),
        fairness_review=df[SENSITIVE_COLUMNS].copy(),
    )


def build_preprocessor() -> ColumnTransformer:
    """Return an unfitted transformer; fit it on training data only in Stage 3."""
    numeric_pipeline = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipeline = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(transformers=[
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])
