import pandas as pd

from src.stage1_data_profile import load_data
from src.stage6_package_and_monitor import (
    monitoring_snapshot, score_aggregate_workforce,
    train_and_package_model, validate_scoring_batch,
)


def test_scoring_batch_validation_and_duplicate_protection():
    df = load_data()
    assert validate_scoring_batch(df)["status"] == "pass"
    duplicate = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    try:
        validate_scoring_batch(duplicate)
        raise AssertionError("Duplicate protection did not run")
    except AssertionError as error:
        assert "duplicates" in str(error)


def test_output_is_aggregate_and_contains_no_employee_identifier():
    model, _ = train_and_package_model()
    summary = score_aggregate_workforce(model, load_data())
    assert "EmployeeNumber" not in summary.columns
    assert set(summary["reporting_status"]) == {"reported"}
    assert summary["employees"].sum() == 1470


def test_monitoring_snapshot_is_complete():
    model, _ = train_and_package_model()
    snapshot = monitoring_snapshot(model, load_data())
    assert snapshot["data_quality"]["status"] == "pass"
    assert 0 <= snapshot["high_risk_rate"] <= 1
    assert snapshot["threshold"] == 0.75
