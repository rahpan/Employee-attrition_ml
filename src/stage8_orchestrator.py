"""Orchestrate governed Stage 8 recommendations, reviews, tasks, and audit events."""

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.stage8_agent_workflow import (
    PolicyBlocked, apply_hr_review, recommend_action,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_PATH = PROJECT_ROOT / "docs" / "stage6_sample_aggregate_output.csv"
AUDIT_PATH = PROJECT_ROOT / "artifacts" / "stage8_audit_log.jsonl"
TASK_PATH = PROJECT_ROOT / "artifacts" / "stage8_simulated_tasks.csv"


def _safe_blocked_event(row: Mapping[str, Any], error: str) -> dict[str, Any]:
    """Create an audit event without copying unapproved input fields."""
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "department": str(row.get("Department", "UNKNOWN")),
        "reporting_status": str(row.get("reporting_status", "UNKNOWN")),
        "workflow_status": "POLICY_BLOCKED",
        "policy_error": error,
        "simulated_task_created": False,
    }


def process_department(
    row: Mapping[str, Any],
    context: Mapping[str, bool] | None = None,
    review: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Run one aggregate department through recommendation and review gates."""
    try:
        recommendation = recommend_action(row, context)
    except PolicyBlocked as exc:
        return _safe_blocked_event(row, str(exc))

    if not recommendation.requires_human_approval:
        return {
            **asdict(recommendation),
            "review_decision": "NOT_REQUIRED",
            "review_rationale": "",
            "final_action": "MONITOR_ONLY",
            "simulated_task_created": False,
            "follow_up_status": "MONITORING",
        }

    if review is None:
        return {
            **asdict(recommendation),
            "review_decision": "PENDING",
            "review_rationale": "",
            "final_action": None,
            "simulated_task_created": False,
            "follow_up_status": "AWAITING_HR_REVIEW",
        }

    try:
        return apply_hr_review(
            recommendation,
            decision=str(review.get("decision", "")),
            modified_action=review.get("modified_action"),
            rationale=str(review.get("rationale", "")),
        )
    except PolicyBlocked as exc:
        event = asdict(recommendation)
        event.update({
            "review_decision": "POLICY_BLOCKED",
            "review_rationale": str(review.get("rationale", "")),
            "final_action": None,
            "simulated_task_created": False,
            "follow_up_status": "NO_TASK_CREATED",
            "policy_error": str(exc),
        })
        return event


def run_workflow(
    aggregate_df: pd.DataFrame,
    contexts: Mapping[str, Mapping[str, bool]] | None = None,
    reviews: Mapping[str, Mapping[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Process a complete aggregate batch without exposing individual records."""
    contexts, reviews = contexts or {}, reviews or {}
    return [
        process_department(
            row.to_dict(),
            context=contexts.get(str(row["Department"])),
            review=reviews.get(str(row["Department"])),
        )
        for _, row in aggregate_df.iterrows()
    ]


def write_outputs(
    events: list[dict[str, Any]],
    audit_path: Path = AUDIT_PATH,
    task_path: Path = TASK_PATH,
) -> dict[str, Any]:
    """Persist append-only audit events and the current simulated task extract."""
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as audit_file:
        for event in events:
            audit_file.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    task_columns = [
        "run_id", "department", "final_action", "follow_up_status",
        "review_decision", "timestamp_utc",
    ]
    tasks = [
        {column: event.get(column) for column in task_columns}
        for event in events if event.get("simulated_task_created") is True
    ]
    pd.DataFrame(tasks, columns=task_columns).to_csv(task_path, index=False)
    return {
        "audit_events_written": len(events),
        "simulated_tasks_created": len(tasks),
        "pending_hr_reviews": sum(
            event.get("review_decision") == "PENDING" for event in events
        ),
        "policy_blocks": sum(
            event.get("workflow_status") == "POLICY_BLOCKED"
            or event.get("review_decision") == "POLICY_BLOCKED"
            for event in events
        ),
    }


def run_stage8() -> dict[str, Any]:
    """Demonstrate the workflow with synthetic aggregate data and sample reviews."""
    aggregate_df = pd.read_csv(AGGREGATE_PATH)
    reviews = {
        "Sales": {
            "decision": "APPROVED",
            "rationale": "Approve an educational listening-session simulation.",
        }
    }
    events = run_workflow(aggregate_df, reviews=reviews)
    summary = write_outputs(events)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_stage8()
