# Stage 5 threshold and final-evaluation policy

## Product Owner priority

The selected priority is **generate fewer false alerts**. A false alert means the model flags attrition even though the employee stays.

## Guardrail

Optimizing only precision could lead to an extreme threshold that flags almost nobody. To prevent that, the policy maximizes validation precision while requiring at least 40% validation recall.

The threshold is selected using validation data only. After selection, logistic regression is refitted using the combined training and validation records. The untouched test set is then evaluated exactly once.

## Interpretation

- Raising the threshold generally reduces false alerts and increases precision.
- Raising it also misses more actual attrition and reduces recall.
- The threshold is a business operating policy, not an inherent truth produced by the algorithm.

## Governance

Test-set subgroup results are descriptive diagnostics, not proof that the model is fair. The dataset is synthetic and small. Real deployment would require approved protected-group definitions, statistical uncertainty, adverse-impact review, legal/privacy approval, and continuous monitoring.
