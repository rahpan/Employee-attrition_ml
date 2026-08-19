# Product definition

## Problem statement

Build an educational prototype that estimates whether an employee record is associated with attrition, then aggregate results to help demonstrate workforce-planning concepts.

## Target

`Attrition` is the label:

- `Yes` becomes `1`
- `No` becomes `0`

The sample contains general attrition, not a verified definition of voluntary attrition. A real product would require HR to approve termination reason codes, population rules, forecast horizon, and exclusions before model development.

## MVP user

An HR workforce-planning analyst learning how historical HR data can support an ML product.

## MVP output

- Overall historical attrition rate
- Data-quality report
- Reproducible model-ready preparation process
- Later stages: evaluated classification probabilities and aggregate summaries

## Product Owner decisions required before production

- Voluntary versus all attrition
- Employee populations included and excluded
- Forecast horizon and scoring frequency
- Approved and prohibited features
- Cost of false positives versus false negatives
- Privacy, legal, security, fairness, and responsible-use approval
- Minimum group size for reporting
- Model monitoring and retraining policy

## Stage 1 acceptance criteria

- Dataset downloads from a documented public source.
- Dataset has 1,470 rows and 35 columns.
- `Attrition` contains only `Yes` and `No`.
- `EmployeeNumber` is unique and non-null.
- No negative values exist in year, income, or distance fields.
- Constant technical columns are identified for exclusion.
- The observed class balance is reported rather than hidden.
