"""Select a precision-oriented threshold and evaluate the test set once."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.pipeline import Pipeline

from src.stage1_data_profile import load_data
from src.stage2_features import build_feature_bundle, build_preprocessor
from src.stage3_splits_baseline import create_development_splits
from src.stage4_train_models import RANDOM_STATE, evaluate_predictions

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = PROJECT_ROOT / "docs" / "stage5_final_results.json"
MINIMUM_VALIDATION_RECALL = 0.40
THRESHOLD_GRID = [round(value, 2) for value in np.arange(0.30, 0.86, 0.05)]


def build_logistic_pipeline() -> Pipeline:
    return Pipeline(steps=[
        ("preprocess", build_preprocessor()),
        ("model", LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE
        )),
    ])


def choose_precision_threshold(y_true, probabilities):
    """Maximize precision while keeping validation recall at or above 40%."""
    tradeoffs = [
        evaluate_predictions(y_true, probabilities, threshold)
        for threshold in THRESHOLD_GRID
    ]
    eligible = [row for row in tradeoffs if row["recall"] >= MINIMUM_VALIDATION_RECALL]
    assert eligible, "No threshold satisfies the minimum recall guardrail"
    selected = max(
        eligible, key=lambda row: (row["precision"], row["f1"], row["threshold"])
    )
    return float(selected["threshold"]), tradeoffs


def top_coefficients(pipeline: Pipeline, limit: int = 10):
    """Return strongest associations; coefficients do not establish causation."""
    names = pipeline.named_steps["preprocess"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    rows = sorted(
        ({"feature": str(name), "coefficient": float(value)}
         for name, value in zip(names, coefficients)),
        key=lambda row: row["coefficient"],
    )
    return {
        "lower_predicted_attrition": rows[:limit],
        "higher_predicted_attrition": rows[-limit:][::-1],
    }


def subgroup_review(y_true, predictions, fairness_data: pd.DataFrame):
    """Provide descriptive subgroup error rates for groups with at least 20 records."""
    review = fairness_data.copy()
    review["AgeBand"] = pd.cut(
        review["Age"], bins=[0, 29, 39, 49, np.inf],
        labels=["Under30", "30-39", "40-49", "50Plus"],
    )
    results = {}
    for attribute in ["Gender", "MaritalStatus", "AgeBand"]:
        groups = {}
        for group in review[attribute].dropna().unique():
            mask = review[attribute] == group
            if int(mask.sum()) < 20:
                continue
            group_true = np.asarray(y_true)[mask.to_numpy()]
            group_pred = np.asarray(predictions)[mask.to_numpy()]
            tn, fp, fn, tp = confusion_matrix(group_true, group_pred, labels=[0, 1]).ravel()
            groups[str(group)] = {
                "records": int(mask.sum()),
                "precision": float(precision_score(group_true, group_pred, zero_division=0)),
                "recall": float(recall_score(group_true, group_pred, zero_division=0)),
                "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
                "true_positive": int(tp), "false_positive": int(fp),
                "false_negative": int(fn), "true_negative": int(tn),
            }
        results[attribute] = groups
    return results


def run_stage5():
    """Select on validation, refit on train+validation, and inspect test once."""
    splits = create_development_splits(build_feature_bundle(load_data()))
    selection_model = build_logistic_pipeline()
    selection_model.fit(splits.train.X, splits.train.y)
    validation_probabilities = selection_model.predict_proba(splits.validation.X)[:, 1]
    threshold, tradeoffs = choose_precision_threshold(
        splits.validation.y, validation_probabilities
    )

    development_X = pd.concat([splits.train.X, splits.validation.X])
    development_y = pd.concat([splits.train.y, splits.validation.y])
    final_model = build_logistic_pipeline()
    final_model.fit(development_X, development_y)

    test_probabilities = final_model.predict_proba(splits.test.X)[:, 1]
    test_metrics = evaluate_predictions(splits.test.y, test_probabilities, threshold)
    test_predictions = (test_probabilities >= threshold).astype(int)

    results = {
        "business_priority": "generate fewer false alerts",
        "threshold_policy": {
            "selection_data": "validation only",
            "objective": "maximize precision",
            "minimum_recall_guardrail": MINIMUM_VALIDATION_RECALL,
            "selected_threshold": threshold,
            "validation_tradeoffs": tradeoffs,
        },
        "final_fit_population": "training plus validation after threshold selection",
        "test_evaluation_count": 1,
        "test_metrics": test_metrics,
        "coefficient_associations": top_coefficients(final_model),
        "descriptive_fairness_review": subgroup_review(
            splits.test.y, test_predictions, splits.test.fairness_review
        ),
        "limitations": [
            "Synthetic cross-sectional data; not a real forward-looking HR forecast.",
            "Subgroup samples are small; differences are descriptive and not proof of fairness.",
            "Coefficients describe associations and do not establish causes.",
            "Not approved for individual employment decisions.",
        ],
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(run_stage5(), indent=2))
