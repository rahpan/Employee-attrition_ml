# Stage 4 candidate-model strategy

## Candidates

### Logistic regression

- Interpretable and suitable as the first serious model
- Produces probabilities
- Uses balanced class weights because attrition is the minority outcome
- Provides a strong benchmark for more complex algorithms

### Random forest

- Captures nonlinear relationships and interactions
- Uses balanced class weights
- Uses minimum leaf size to reduce overfitting on the small dataset
- Compared against logistic regression rather than assumed superior

## Development boundary

Both candidates are fitted only on the 1,029 training records. Metrics are calculated using the 220 validation records. The 221 test records remain untouched until a candidate and decision threshold are finalized.

## Selection metric

Validation PR-AUC is the primary comparison because attrition is the minority class. Precision, recall, F1, ROC-AUC, Brier score, and the confusion matrix provide additional business context. Accuracy is reported but cannot drive the decision.

## Product Owner decision

Selecting an algorithm is not only choosing the highest score. The Product Owner must ask:

- How many actual attrition cases are identified?
- How many staying employees are incorrectly flagged?
- Which error is more costly to the approved workforce-planning use case?
- Is the output explainable and sufficiently calibrated?
- Does the candidate improve materially over the current business process?

The selected model remains a candidate until final test evaluation, governance review, and UAT are complete.
