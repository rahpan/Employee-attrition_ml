"""Interactive aggregate workforce-planning and governed agent dashboard."""

from dataclasses import asdict
import json

import streamlit as st

from src.stage7_dashboard_data import (
    dashboard_kpis, filter_reported_departments, load_aggregate_output,
)
from src.stage8_agent_workflow import (
    ACTION_PLAYBOOK, PolicyBlocked, apply_hr_review, recommend_action,
)


st.set_page_config(
    page_title="Attrition Workforce Planning", page_icon="📊", layout="wide"
)
st.title("Attrition workforce-planning prototype")
st.caption(
    "Aggregate educational results from a synthetic dataset — not approved for "
    "individual employment decisions."
)

source = load_aggregate_output()
available_departments = source.loc[
    source["reporting_status"] == "reported", "Department"
].tolist()

with st.sidebar:
    st.header("View controls")
    selected_departments = st.multiselect(
        "Departments", options=available_departments, default=available_departments
    )
    st.divider()
    st.markdown("**Model version:** 1.0.0-educational")
    st.markdown("**Decision threshold:** 0.75")
    st.markdown("**Agent review threshold:** 15% aggregate high-risk rate")
    st.markdown("**Business priority:** Fewer false alerts")

filtered = filter_reported_departments(source, selected_departments)
kpis = dashboard_kpis(filtered)
if filtered.empty:
    st.warning("Select at least one reported department.")
    st.stop()

dashboard_tab, agent_tab = st.tabs(["Workforce dashboard", "Agentic HR workflow"])

with dashboard_tab:
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Employees represented", f"{kpis['employees']:,}")
    metric2.metric("Model high-risk count", f"{kpis['high_risk_count']:,}")
    metric3.metric("Model high-risk rate", f"{kpis['high_risk_rate']:.1%}")
    metric4.metric("Average model score", f"{kpis['weighted_average_score']:.1%}")

    st.subheader("Department comparison")
    st.bar_chart(
        filtered.set_index("Department")[["high_risk_rate"]],
        horizontal=True, color="#C75B39",
    )

    display = filtered[
        ["Department", "employees", "high_risk_count", "high_risk_rate",
         "average_predicted_probability", "reporting_status"]
    ].rename(columns={
        "employees": "Employees",
        "high_risk_count": "Model high-risk count",
        "high_risk_rate": "Model high-risk rate",
        "average_predicted_probability": "Average model score",
        "reporting_status": "Reporting status",
    })
    st.dataframe(
        display, hide_index=True, use_container_width=True,
        column_config={
            "Model high-risk rate": st.column_config.ProgressColumn(format="percent"),
            "Average model score": st.column_config.NumberColumn(format="percent"),
        },
    )

    with st.expander("How to interpret these results"):
        st.markdown("""
- **Model high-risk count** is the number of records with a score of 0.75 or higher.
- **Model high-risk rate** is the flagged count divided by employees represented.
- **Average model score** summarizes model output across the group.
- These values are planning indicators, not confirmed departures or causal findings.
- Small groups are suppressed before they reach this dashboard.
""")

    st.subheader("Final synthetic test performance")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Precision", "57.1%")
    p2.metric("Recall", "44.4%")
    p3.metric("ROC-AUC", "0.840")
    p4.metric("PR-AUC", "0.626")

with agent_tab:
    st.subheader("Governed department-level recommendation")
    st.info(
        "The agent uses aggregate data and approved rules only. It cannot make "
        "individual employment decisions or create a task without HR approval."
    )

    agent_department = st.selectbox(
        "Department to review", available_departments, key="agent_department"
    )
    selected_row = source.loc[
        source["Department"] == agent_department
    ].iloc[0].to_dict()

    a1, a2, a3 = st.columns(3)
    a1.metric("Employees represented", f"{int(selected_row['employees']):,}")
    a2.metric("Aggregate high-risk rate", f"{selected_row['high_risk_rate']:.1%}")
    a3.metric("Average model score", f"{selected_row['average_predicted_probability']:.1%}")

    st.markdown("**Optional approved department context**")
    workload = st.checkbox("Aggregate workload concern", key="agent_workload")
    development = st.checkbox("Aggregate development concern", key="agent_development")
    schedule = st.checkbox("Aggregate scheduling concern", key="agent_schedule")

    if st.button("Generate governed recommendation", type="primary"):
        try:
            st.session_state.agent_recommendation = recommend_action(
                selected_row,
                {
                    "aggregate_workload_concern": workload,
                    "aggregate_development_concern": development,
                    "aggregate_schedule_concern": schedule,
                },
            )
            st.session_state.agent_review_event = None
        except PolicyBlocked as exc:
            st.error(f"Policy blocked this request: {exc}")

    recommendation = st.session_state.get("agent_recommendation")
    if recommendation and recommendation.department == agent_department:
        st.divider()
        st.markdown(f"**Recommended action:** `{recommendation.proposed_action}`")
        st.write(ACTION_PLAYBOOK[recommendation.proposed_action])
        st.caption(recommendation.explanation)
        st.markdown(f"**Triggered rule:** `{recommendation.triggered_rule}`")

        if recommendation.requires_human_approval:
            st.warning("Status: Waiting for an HR reviewer. No task has been created.")
            decision = st.radio(
                "HR decision", ["APPROVED", "MODIFIED", "REJECTED"], horizontal=True
            )
            modified_action = None
            if decision == "MODIFIED":
                intervention_options = [
                    action for action in ACTION_PLAYBOOK if action != "MONITOR_ONLY"
                ]
                modified_action = st.selectbox(
                    "Choose an approved replacement action", intervention_options
                )
            rationale = st.text_area("Reviewer rationale", max_chars=500)

            if st.button("Submit HR decision"):
                try:
                    st.session_state.agent_review_event = apply_hr_review(
                        recommendation, decision, modified_action, rationale
                    )
                except PolicyBlocked as exc:
                    st.error(f"Policy blocked this decision: {exc}")
        else:
            st.success("Status: Monitor only. HR approval and a task are not required.")
            st.session_state.agent_review_event = {
                **asdict(recommendation),
                "review_decision": "NOT_REQUIRED",
                "review_rationale": "",
                "final_action": "MONITOR_ONLY",
                "simulated_task_created": False,
                "follow_up_status": "MONITORING",
            }

    review_event = st.session_state.get("agent_review_event")
    if review_event and review_event.get("department") == agent_department:
        if review_event["simulated_task_created"]:
            st.success(
                f"Simulated task created: {review_event['final_action']} "
                f"({review_event['follow_up_status']})."
            )
        elif review_event["review_decision"] == "REJECTED":
            st.info("Recommendation rejected. No task was created.")

        with st.expander("Audit record"):
            st.json(review_event)
            st.download_button(
                "Download audit record",
                data=json.dumps(review_event, indent=2),
                file_name=f"stage8_audit_{review_event['run_id']}.json",
                mime="application/json",
            )

st.warning(
    "This dataset is synthetic and cross-sectional. A real product requires "
    "effective-dated HR history, a verified attrition definition, legal/privacy "
    "approval, fairness assessment, UAT, monitoring, and access controls."
)
