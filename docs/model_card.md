# Model card — Employee attrition educational prototype

## Model

- Type: Class-weighted logistic regression
- Version: `1.0.0-educational`
- Threshold: `0.75`
- Inputs: 24 approved HR features
- Reporting: Aggregate workforce-planning summaries

## Intended use

Learning how an ML Product Owner coordinates data definition, feature governance, model development, evaluation, packaging, monitoring, and adoption.

## Prohibited use

Do not use this prototype or its scores for individual hiring, termination, promotion, compensation, discipline, surveillance, or other employment decisions.

## Final synthetic test performance

- Precision: 57.1%
- Recall: 44.4%
- F1: 0.50
- ROC-AUC: 0.840
- PR-AUC: 0.626
- False alerts: 12 of 185 actual stayers
- Missed attrition: 20 of 36 actual attrition cases

## Limitations

- Synthetic cross-sectional dataset
- No genuine forecast date or effective-dated history
- No verified voluntary-attrition definition
- Small subgroup samples
- Associations are not causes
- Performance will not transfer automatically to a real employer
