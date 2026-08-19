from src.stage7_dashboard_data import (
    dashboard_kpis, filter_reported_departments, load_aggregate_output,
)


def test_dashboard_source_contains_no_employee_identifier():
    df = load_aggregate_output()
    assert "EmployeeNumber" not in df.columns
    assert len(df) == 3


def test_filters_and_weighted_kpis():
    source = load_aggregate_output()
    filtered = filter_reported_departments(source, ["Sales"])
    kpis = dashboard_kpis(filtered)
    assert list(filtered["Department"]) == ["Sales"]
    assert kpis["employees"] == 446
    assert kpis["high_risk_count"] == 82
    assert round(kpis["high_risk_rate"], 4) == round(82 / 446, 4)


def test_empty_selection_is_safe():
    source = load_aggregate_output()
    empty = filter_reported_departments(source, ["Not a department"])
    assert dashboard_kpis(empty)["employees"] == 0
