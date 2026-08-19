"""Package the prototype and produce governed aggregate workforce forecasts."""

import json
from pathlib import Path

import joblib
import pandas as pd

from src.stage1_data_profile import load_data
from src.stage2_features import APPROVED_FEATURES, build_feature_bundle
from src.stage3_splits_baseline import create_development_splits
from src.stage5_threshold_final_evaluation import build_logistic_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "artifacts" / "attrition_logistic_pipeline.joblib"
METADATA_PATH = PROJECT_ROOT / "artifacts" / "model_metadata.json"
THRESHOLD = 0.75
MINIMUM_REPORTING_GROUP = 20


def train_and_package_model():
    """Fit the approved prototype on all development data and persist it locally."""
    splits = create_development_splits(build_feature_bundle(load_data()))
    development_X = pd.concat([splits.train.X, splits.validation.X])
    development_y = pd.concat([splits.train.y, splits.validation.y])
    model = build_logistic_pipeline()
    model.fit(development_X, development_y)
    metadata = {
        "model_type": "balanced logistic regression pipeline",
        "model_version": "1.0.0-educational",
        "decision_threshold": THRESHOLD,
        "threshold_business_priority": "generate fewer false alerts",
        "feature_count": len(APPROVED_FEATURES),
        "approved_features": APPROVED_FEATURES,
        "training_population_records": len(development_y),
        "intended_use": "aggregate educational workforce-planning prototype",
        "prohibited_use": "individual employment decisions",
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return model, metadata


def validate_scoring_batch(df: pd.DataFrame):
    """Stop scoring when required inputs or basic quality expectations fail."""
    missing_columns = sorted(set(APPROVED_FEATURES).difference(df.columns))
    assert not missing_columns, f"Missing scoring columns: {missing_columns}"
    assert len(df) > 0, "Scoring batch is empty"
    assert df["EmployeeNumber"].notna().all(), "EmployeeNumber contains nulls"
    assert df["EmployeeNumber"].is_unique, "EmployeeNumber contains duplicates"
    missing_rate = float(df[APPROVED_FEATURES].isna().mean().mean())
    assert missing_rate <= 0.05, "More than 5% of scoring feature values are missing"
    return {
        "records": len(df), "missing_feature_rate": missing_rate,
        "duplicate_employee_ids": int(df["EmployeeNumber"].duplicated().sum()),
        "status": "pass",
    }


def score_aggregate_workforce(
    model, df: pd.DataFrame, group_column: str = "Department",
    threshold: float = THRESHOLD, minimum_group_size: int = MINIMUM_REPORTING_GROUP,
) -> pd.DataFrame:
    """Return department-level results and suppress small groups."""
    validate_scoring_batch(df)
    assert group_column in df.columns
    probabilities = model.predict_proba(df[APPROVED_FEATURES])[:, 1]
    working = pd.DataFrame({
        group_column: df[group_column].values,
        "predicted_probability": probabilities,
        "high_risk_flag": probabilities >= threshold,
    })
    summary = (
        working.groupby(group_column, dropna=False)
        .agg(
            employees=("high_risk_flag", "size"),
            high_risk_count=("high_risk_flag", "sum"),
            average_predicted_probability=("predicted_probability", "mean"),
        )
        .reset_index()
    )
    summary["high_risk_rate"] = summary["high_risk_count"] / summary["employees"]
    summary["reporting_status"] = summary["employees"].apply(
        lambda size: "reported" if size >= minimum_group_size else "suppressed_small_group"
    )
    protected = ["high_risk_count", "average_predicted_probability", "high_risk_rate"]
    summary.loc[summary["reporting_status"] != "reported", protected] = pd.NA
    return summary


def monitoring_snapshot(model, df: pd.DataFrame):
    """Create operational metrics for each scoring run."""
    quality = validate_scoring_batch(df)
    probabilities = model.predict_proba(df[APPROVED_FEATURES])[:, 1]
    return {
        "data_quality": quality,
        "average_model_score": float(probabilities.mean()),
        "high_risk_rate": float((probabilities >= THRESHOLD).mean()),
        "score_minimum": float(probabilities.min()),
        "score_maximum": float(probabilities.max()),
        "threshold": THRESHOLD,
        "alerts": {
            "high_risk_rate_review": bool((probabilities >= THRESHOLD).mean() > 0.30),
            "missing_data_review": bool(quality["missing_feature_rate"] > 0.02),
        },
    }


def run_stage6():
    """Package and demonstrate aggregate scoring on the synthetic dataset."""
    model, metadata = train_and_package_model()
    df = load_data()
    summary = score_aggregate_workforce(model, df)
    monitor = monitoring_snapshot(model, df)
    output_path = PROJECT_ROOT / "docs" / "stage6_sample_aggregate_output.csv"
    summary.to_csv(output_path, index=False)
    result = {
        "metadata": metadata, "monitoring": monitor,
        "aggregate_rows": len(summary), "individual_scores_exposed": False,
        "sample_output": str(output_path.relative_to(PROJECT_ROOT)),
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run_stage6()
