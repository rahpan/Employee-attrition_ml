import pytest

from src.stage8_agent_workflow import (
    ACTION_PLAYBOOK, PolicyBlocked, apply_hr_review, recommend_action,
)


def aggregate_row(rate=0.18, status="reported", employees=100, **extra):
    return {
        "Department": "Sales",
        "employees": employees,
        "high_risk_count": 18,
        "average_predicted_probability": 0.44,
        "high_risk_rate": rate,
        "reporting_status": status,
        **extra,
    }


def test_low_signal_is_monitor_only():
    result = recommend_action(aggregate_row(rate=0.10))
    assert result.proposed_action == "MONITOR_ONLY"
    assert result.requires_human_approval is False


def test_elevated_signal_uses_safe_default():
    result = recommend_action(aggregate_row())
    assert result.proposed_action == "MANAGER_LISTENING"
    assert result.proposed_action in ACTION_PLAYBOOK
    assert result.workflow_status == "PENDING_HR_REVIEW"


def test_approved_context_selects_specific_playbook_action():
    result = recommend_action(
        aggregate_row(), {"aggregate_workload_concern": True}
    )
    assert result.proposed_action == "WORKLOAD_REVIEW"


@pytest.mark.parametrize("bad_field", ["EmployeeNumber", "Age", "email"])
def test_individual_or_sensitive_fields_are_blocked(bad_field):
    with pytest.raises(PolicyBlocked):
        recommend_action(aggregate_row(**{bad_field: "prohibited"}))


def test_suppressed_and_small_groups_are_blocked():
    with pytest.raises(PolicyBlocked):
        recommend_action(aggregate_row(status="suppressed_small_group"))
    with pytest.raises(PolicyBlocked):
        recommend_action(aggregate_row(employees=10))


def test_task_requires_hr_approval():
    recommendation = recommend_action(aggregate_row())
    reviewed = apply_hr_review(recommendation, "APPROVED", rationale="Pilot approved")
    assert reviewed["simulated_task_created"] is True
    assert reviewed["final_action"] == "MANAGER_LISTENING"


def test_rejection_creates_no_task_and_bad_modification_is_blocked():
    recommendation = recommend_action(aggregate_row())
    rejected = apply_hr_review(recommendation, "REJECTED")
    assert rejected["simulated_task_created"] is False
    with pytest.raises(PolicyBlocked):
        apply_hr_review(recommendation, "MODIFIED", "TERMINATE_EMPLOYEE")
