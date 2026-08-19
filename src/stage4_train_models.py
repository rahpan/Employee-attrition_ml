"""Train and compare interpretable candidate attrition models."""

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline

from src.stage1_data_profile import load_data
from src.stage2_features import build_feature_bundle, build_preprocessor
from src.stage3_splits_baseline import create_development_splits, evaluate_majority_baseline

RANDOM_STATE = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = PROJECT_ROOT / "docs" / "stage4_model_results.json"


def candidate_models() -> dict[str, Pipeline]:
    """Define candidates with independent training-only preprocessors."""
    return {
        "logistic_regression": Pipeline(steps=[
            ("preprocess", build_preprocessor()),
            ("model", LogisticRegression(
                class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE
            )),
        ]),
        "random_forest": Pipeline(steps=[
            ("preprocess", build_preprocessor()),
            ("model", RandomForestClassifier(
                n_estimators=400, min_samples_leaf=4, class_weight="balanced",
                random_state=RANDOM_STATE, n_jobs=-1,
            )),
        ]),
    }


def evaluate_predictions(y_true, probabilities, threshold: float = 0.50) -> dict[str, object]:
    """Evaluate positive-class performance and probability quality."""
    predictions = (np.asarray(probabilities) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "confusion_matrix": {
            "true_negative": int(tn), "false_positive": int(fp),
            "false_negative": int(fn), "true_positive": int(tp),
        },
    }


def train_and_compare() -> tuple[dict[str, Pipeline], dict[str, object]]:
    """Train on training data and compare only on validation data."""
    splits = create_development_splits(build_feature_bundle(load_data()))
    fitted_models: dict[str, Pipeline] = {}
    metrics: dict[str, object] = {}
    for name, pipeline in candidate_models().items():
        pipeline.fit(splits.train.X, splits.train.y)
        probabilities = pipeline.predict_proba(splits.validation.X)[:, 1]
        fitted_models[name] = pipeline
        metrics[name] = evaluate_predictions(splits.validation.y, probabilities)

    baseline = evaluate_majority_baseline(splits)
    recommended = max(metrics, key=lambda name: metrics[name]["pr_auc"])
    results = {
        "development_rule": "train on training; compare on validation; do not inspect test",
        "baseline": baseline,
        "candidate_metrics": metrics,
        "selection_metric": "validation PR-AUC",
        "recommended_candidate": recommended,
        "recommendation_status": "candidate only; final test evaluation pending",
        "test_set_status": "untouched",
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return fitted_models, results


if __name__ == "__main__":
    _, result = train_and_compare()
    print(json.dumps(result, indent=2))
