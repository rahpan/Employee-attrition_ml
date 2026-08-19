import json

import pandas as pd

from src.stage8_orchestrator import process_department, run_workflow, write_outputs


def row(department="Sales", rate=0.18, status="reported", employees=100, **extra):
    return {
        "Department": department,
        "employees": employees,
        "high_risk_count": 18,
        "average_predicted_probability": 0.44,
        "high_risk_rate": rate,
        "reporting_status": status,
        **extra,
    }


def test_intervention_waits_for_review():
    event = process_department(row())
    assert event["review_decision"] == "PENDING"
    assert event["simulated_task_created"] is False


def test_approval_creates_one_simulated_task():
    event = process_department(row(), review={"decision": "APPROVED"})
    assert event["simulated_task_created"] is True
    assert event["follow_up_status"] == "SIMULATED_TASK_OPEN"


def test_monitor_only_skips_review_and_task():
    event = process_department(row(rate=0.10))
    assert event["review_decision"] == "NOT_REQUIRED"
    assert event["simulated_task_created"] is False


def test_blocked_event_does_not_copy_sensitive_value():
    event = process_department(row(EmployeeNumber=12345))
    assert event["workflow_status"] == "POLICY_BLOCKED"
    assert "EmployeeNumber" not in event
    assert "12345" not in json.dumps(event)


def test_batch_and_output_counts(tmp_path):
    frame = pd.DataFrame([
        row("Sales", 0.18), row("Research & Development", 0.10),
    ])
    events = run_workflow(
        frame, reviews={"Sales": {"decision": "APPROVED"}}
    )
    summary = write_outputs(
        events, tmp_path / "audit.jsonl", tmp_path / "tasks.csv"
    )
    assert summary == {
        "audit_events_written": 2,
        "simulated_tasks_created": 1,
        "pending_hr_reviews": 0,
        "policy_blocks": 0,
    }
    assert len((tmp_path / "audit.jsonl").read_text().splitlines()) == 2
    assert len(pd.read_csv(tmp_path / "tasks.csv")) == 1
