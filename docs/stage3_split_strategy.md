# Stage 3 split and baseline strategy

## Development partition

The 1,470 synthetic records are divided reproducibly using random state `42` and stratification on the attrition label:

- Training: 1,029 records (70%)
- Validation: 220 records (15%)
- Test: 221 records (15%)

Stratification keeps the approximately 16.12% attrition rate similar across all three partitions. Automated checks prove that no `EmployeeNumber` occurs in more than one partition.

## Leakage control

The preprocessor is fitted only on the training partition. The validation partition is transformed using training-derived medians, scaling statistics, and categorical vocabulary. The test partition remains untouched until the final model is chosen.

## Baseline

The first baseline always predicts the majority outcome: no attrition. Because the dataset is imbalanced, this produces high accuracy but zero recall for attrition. This demonstrates why accuracy alone is an unacceptable success measure.

The Stage 4 models must improve meaningfully on positive-class recall, F1, PR-AUC, ROC-AUC, and calibration while remaining explainable and governed.

## Production limitation

This random split is appropriate only for demonstrating the ML workflow with a synthetic snapshot. A real Employee Central attrition product should construct point-in-time observations and use older periods for training, a later period for validation, and the newest fully observed period for testing.
