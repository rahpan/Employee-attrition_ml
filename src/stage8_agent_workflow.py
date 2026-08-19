"""Governed, deterministic agent workflow for aggregate workforce planning."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping
from uuid import uuid4


MODEL_VERSION = "1.0.0-educational"
POLICY_VERSION = "1.0.0"
REVIEW_THRESHOLD = 0.15

REQUIRED_FIELDS = {
    "Department", "employees", "high_risk_count",
    "average_predicted_probability", "high_risk_rate", "reporting_status",
}
PROHIBITED_FIELDS = {
    "employeenumber", "employee_id", "name", "email", "individual_score",
    "age", "gender", "maritalstatus", "ethnicity", "disability", "medical_data",
}
ACTION_PLAYBOOK = {
    "WORKLOAD_REVIEW": "Review aggregate workload and overtime patterns.",
    "CAREER_PROGRAM": "Offer a department-wide career-development program.",
    "MANAGER_LISTENING": "Run a voluntary listening session or anonymous pulse survey.",
    "SCHEDULE_REVIEW": "Review department scheduling practices.",
    "MONITOR_ONLY": "Review the aggregate indicator during the next cycle.",
}
REVIEW_DECISIONS = {"APPROVED", "MODIFIED", "REJECTED"}


class PolicyBlocked(ValueError):
    """Raised when an input or requested action violates the Stage 8 policy."""


@dataclass(frozen=True)
class Recommendation:
    run_id: str
    timestamp_utc: str
    model_version: str
    policy_version: str
    department: str
    reporting_status: str
    input_hash: str
    triggered_rule: str
    proposed_action: str
    explanation: str
    requires_human_approval: bool
    workflow_status: str


def _normalized_keys(values: Mapping[str, Any]) -> set[str]:
    return {str(key).replace(" ", "").lower() for key in values}


def _input_hash(row: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(row), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_aggregate_input(row: Mapping[str, Any]) -> None:
    """Block incomplete, suppressed, or individual-level data."""
    missing = REQUIRED_FIELDS.difference(row)
    if missing:
        raise PolicyBlocked(f"Missing required aggregate fields: {sorted(missing)}")
    prohibited = _normalized_keys(row).intersection(PROHIBITED_FIELDS)
    if prohibited:
        raise PolicyBlocked(f"Individual or sensitive fields are prohibited: {sorted(prohibited)}")
    if row["reporting_status"] != "reported":
        raise PolicyBlocked("Suppressed or unapproved groups cannot enter the workflow")
    if int(row["employees"]) < 20:
        raise PolicyBlocked("Groups smaller than 20 employees cannot enter the workflow")
    rate = float(row["high_risk_rate"])
    if not 0 <= rate <= 1:
        raise PolicyBlocked("high_risk_rate must be between 0 and 1")


def recommend_action(
    row: Mapping[str, Any], context: Mapping[str, bool] | None = None,
) -> Recommendation:
    """Select one approved action using versioned, reproducible rules."""
    validate_aggregate_input(row)
    context = dict(context or {})
    rate = float(row["high_risk_rate"])

    if rate < REVIEW_THRESHOLD:
        action = "MONITOR_ONLY"
        rule = "HIGH_RISK_RATE_BELOW_REVIEW_THRESHOLD"
        explanation = (
            f"The aggregate high-risk rate is {rate:.1%}, below the "
            f"{REVIEW_THRESHOLD:.0%} review threshold. This is a planning indicator."
        )
    elif context.get("aggregate_workload_concern"):
        action, rule = "WORKLOAD_REVIEW", "ELEVATED_SIGNAL_WITH_WORKLOAD_CONTEXT"
        explanation = "The aggregate signal and approved workload context support a workload review; no causal claim is made."
    elif context.get("aggregate_development_concern"):
        action, rule = "CAREER_PROGRAM", "ELEVATED_SIGNAL_WITH_DEVELOPMENT_CONTEXT"
        explanation = "The aggregate signal and approved development context support a department-wide career program."
    elif context.get("aggregate_schedule_concern"):
        action, rule = "SCHEDULE_REVIEW", "ELEVATED_SIGNAL_WITH_SCHEDULE_CONTEXT"
        explanation = "The aggregate signal and approved scheduling context support a department scheduling review."
    else:
        action, rule = "MANAGER_LISTENING", "ELEVATED_SIGNAL_WITHOUT_VERIFIED_CAUSE"
        explanation = "The aggregate signal warrants voluntary listening, but available information does not establish a cause."

    approval_required = action != "MONITOR_ONLY"
    return Recommendation(
        run_id=str(uuid4()),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        model_version=MODEL_VERSION,
        policy_version=POLICY_VERSION,
        department=str(row["Department"]),
        reporting_status=str(row["reporting_status"]),
        input_hash=_input_hash(row),
        triggered_rule=rule,
        proposed_action=action,
        explanation=explanation,
        requires_human_approval=approval_required,
        workflow_status="PENDING_HR_REVIEW" if approval_required else "MONITORING",
    )


def apply_hr_review(
    recommendation: Recommendation,
    decision: str,
    modified_action: str | None = None,
    rationale: str = "",
) -> dict[str, Any]:
    """Apply the human approval gate and create only simulated tasks."""
    decision = decision.upper()
    if decision not in REVIEW_DECISIONS:
        raise PolicyBlocked(f"Review decision must be one of {sorted(REVIEW_DECISIONS)}")
    if not recommendation.requires_human_approval:
        raise PolicyBlocked("MONITOR_ONLY recommendations do not create follow-up tasks")

    final_action = recommendation.proposed_action
    if decision == "MODIFIED":
        if modified_action not in ACTION_PLAYBOOK or modified_action == "MONITOR_ONLY":
            raise PolicyBlocked("Modified action must be an approved intervention")
        final_action = modified_action
    elif decision == "REJECTED":
        final_action = None

    task_created = decision in {"APPROVED", "MODIFIED"}
    return {
        **asdict(recommendation),
        "review_decision": decision,
        "review_rationale": rationale,
        "final_action": final_action,
        "simulated_task_created": task_created,
        "follow_up_status": "SIMULATED_TASK_OPEN" if task_created else "NO_TASK_CREATED",
    }
