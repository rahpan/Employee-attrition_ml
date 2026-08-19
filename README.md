# Employee Attrition ML — Guided Product Owner Project

This repository is a step-by-step educational project showing how a Product Owner takes an employee-attrition idea from business definition to a tested ML prototype.

## Dataset and use

The project uses the public **IBM HR Analytics Employee Attrition & Performance** synthetic dataset: 1,470 rows and 35 columns. It is a cross-sectional teaching dataset, not real Employee Central history.

**Intended:** education and aggregate workforce-planning experimentation.

**Prohibited:** individual hiring, termination, promotion, compensation, disciplinary, or other employment decisions.

## Completed stages

- Stage 1 — business definition, download, profiling, validation
- Stage 2 — feature catalog, exclusions, preprocessing
- Stage 3 — train/validation/test split and baseline
- Stage 4 — logistic regression and random forest
- Stage 5 — threshold policy, final test, explainability, fairness review
- Stage 6 — packaging, aggregate scoring, monitoring, production architecture
- Stage 7 — privacy-safe interactive Streamlit dashboard
- Stage 8 — governed agent policy, deterministic recommendations, HR approval gate, simulated tasks, audit trail

## Project layout

```text
data/raw/                  public synthetic sample data
docs/                      Product Owner definitions, results, model card
notebooks/                 executable guided notebooks
src/                       reusable Python code
tests/                     automated validation and governance checks
streamlit_app.py           aggregate workforce-planning dashboard
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## Run the dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard shows aggregate department-level indicators only. It does not display EmployeeNumber or individual risk scores.

## Run the governed Stage 8 simulation

```bash
python -m src.stage8_orchestrator
```

The simulation reads only aggregate department output, requires HR approval for interventions, creates simulated tasks, and writes a privacy-safe local audit log.
