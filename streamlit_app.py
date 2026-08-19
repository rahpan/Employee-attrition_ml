"""Interactive aggregate workforce-planning dashboard."""

import streamlit as st
from src.stage7_dashboard_data import (
    dashboard_kpis, filter_reported_departments, load_aggregate_output,
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
    st.markdown("**Business priority:** Fewer false alerts")

filtered = filter_reported_departments(source, selected_departments)
kpis = dashboard_kpis(filtered)
if filtered.empty:
    st.warning("Select at least one reported department.")
    st.stop()

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

st.warning(
    "This dataset is synthetic and cross-sectional. A real product requires "
    "effective-dated HR history, a verified attrition definition, legal/privacy "
    "approval, fairness assessment, UAT, monitoring, and access controls."
)
