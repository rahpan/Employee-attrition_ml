# Employee Attrition ML — Guided Product Owner Project

This repository is a step-by-step educational project showing how a Product Owner takes an employee-attrition idea from business definition to a tested ML prototype.

## Stage 1: understand and validate the data

The first stage answers four questions:

1. What business outcome are we predicting?
2. What does each source field mean?
3. Is the sample data structurally usable?
4. Which fields must be excluded before modeling?

The project uses the public **IBM HR Analytics Employee Attrition & Performance** synthetic dataset. It has 1,470 rows and 35 columns. It is a cross-sectional teaching dataset, not real Employee Central history and not suitable for real employment decisions.

## Intended and prohibited use

**Intended:** education and aggregate workforce-planning experimentation.

**Prohibited:** hiring, termination, promotion, compensation, disciplinary, or other individual employment decisions.

## Project layout

```text
data/raw/                  downloaded sample data (not committed)
docs/                      Product Owner definitions and decisions
notebooks/                 executable guided notebooks
src/                       reusable Python code
tests/                     automated data validations
```

## Run Stage 1

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.stage1_data_profile
pytest
jupyter notebook notebooks/01_data_understanding.ipynb
```

## Planned stages

- Stage 1 — business definition, download, profiling, validation
- Stage 2 — feature catalog, exclusions, preprocessing
- Stage 3 — train/validation/test split and baseline
- Stage 4 — logistic regression and random forest
- Stage 5 — evaluation, calibration, explainability, fairness review
- Stage 6 — production architecture and Product Owner handoff
