# Stage 7 dashboard guide

## Purpose

The Streamlit dashboard demonstrates how an HR workforce-planning user could consume aggregate model output. It does not display employee identifiers or individual risk scores.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## User workflow

1. Select one or more departments.
2. Review the population represented and model high-risk rate.
3. Compare departments using the bar chart and aggregate table.
4. Review the model version, threshold, performance, and limitations.
5. Use results only as a planning signal requiring further business investigation.

## UAT acceptance criteria

- Only approved aggregate departments appear.
- Employee identifiers and individual scores are absent.
- Small groups remain suppressed.
- Department filters update all metrics consistently.
- Percentages use employee-weighted calculations.
- Model version and threshold are visible.
- Performance and limitations are visible.
- Empty selections produce a clear message rather than an error.

## Production equivalent

In the Darwin environment, the aggregate output would be written to a governed BigQuery prediction table and consumed by Power BI. Row-level security, authorized views, policy tags, audit logging, freshness indicators, and approved minimum-group suppression would be enforced upstream and in the reporting layer.
