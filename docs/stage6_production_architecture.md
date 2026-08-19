# Stage 6 production architecture and operating model

## Outcome

The educational model is packaged as one pipeline containing both preprocessing and logistic regression. Batch scoring produces department-level workforce-planning summaries. Employee identifiers and individual risk scores are not included in the reporting output.

## Darwin-aligned flow

1. **Employee Central** provides approved employment and job-history fields.
2. **TIBCO** authenticates, calls the approved APIs, validates responses, and publishes JSON messages.
3. **Pub/Sub** receives messages through source-specific topics and delivers them to subscribers.
4. **Dataflow** parses, deduplicates, validates, and loads raw and processed BigQuery data.
5. **BigQuery curated HR tables** create point-in-time employee observations and approved features.
6. **Model training pipeline** uses older labeled periods for training, later periods for validation, and the newest completed period for final testing.
7. **Model registry** stores the approved pipeline, metadata, version, threshold, evaluation, and governance status.
8. **Batch scoring job** scores the current approved population on a schedule.
9. **Aggregate prediction table** stores department/location/job-family workforce forecasts with small-group suppression.
10. **Power BI** presents approved aggregate workforce-planning views.

## Monitoring

Each run should record source and feature freshness, batch size, missing values, duplicates, schema changes, category changes, average score, high-risk rate, model version, threshold, pipeline failures, rejected records, realized forecast error, calibration, and subgroup diagnostics.

## Operational controls

- Fail closed when required fields or source feeds are incomplete.
- Preserve the last approved aggregate forecast with a freshness warning.
- Restrict raw and row-level data to approved HR roles.
- Suppress reporting for groups below the approved minimum size.
- Log model and forecast access.
- Require governance approval for every new model or feature version.
- Never automate individual employment decisions.

## Product Owner Definition of Done

- Approved business definition and intended use
- Governed feature catalog and source lineage
- Reproducible training and evaluation
- Model, threshold, and metadata versioned together
- Data-quality and drift monitoring active
- Aggregate reporting UAT completed
- Security, privacy, legal, and responsible-AI approval obtained
- Runbook, support owner, rollback, and retraining policy documented
