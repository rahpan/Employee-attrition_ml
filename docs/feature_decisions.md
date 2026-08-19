# Stage 2 feature decisions

## Outcome

`Attrition` is mapped from `Yes/No` to `1/0`. It is the label and is never included in the feature matrix.

## Primary model boundary

The primary educational model uses 24 approved features. It excludes:

- Identifier: `EmployeeNumber`
- Constants: `EmployeeCount`, `Over18`, `StandardHours`
- Sensitive/fairness-only: `Age`, `Gender`, `MaritalStatus`
- Unclear synthetic rates: `DailyRate`, `HourlyRate`, `MonthlyRate`

Sensitive fields are separated into a fairness-review dataset. They are not supplied to the primary model.

## Transformation approach

- Numeric features are median-imputed and standardized.
- Categorical features are most-frequent-imputed and one-hot encoded.
- Transformation is defined now but fitted later using training data only, preventing information from validation and test data from leaking into training.

## Important limitation

The public dataset is a single synthetic snapshot. It does not contain a true observation date, forecast horizon, voluntary termination reason, or effective-dated HR history. Stage 3 will therefore use a stratified development split for teaching purposes and clearly distinguish it from a production time-based split.

## Product Owner approval questions

- Does HR approve the label definition?
- Is compensation data legitimately required and appropriately restricted?
- Are performance measures appropriate for the approved use?
- Which sensitive attributes may be used only for fairness evaluation?
- What minimum group size prevents identification in reporting?
- Which mistakes are more harmful: overforecasting or underforecasting attrition?
