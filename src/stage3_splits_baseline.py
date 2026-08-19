"""Create leakage-controlled development splits and a majority-class baseline."""

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.stage1_data_profile import load_data
from src.stage2_features import FeatureBundle, build_feature_bundle, build_preprocessor

RANDOM_STATE = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = PROJECT_ROOT / "docs" / "stage3_baseline_results.json"


@dataclass(frozen=True)
class DataSplit:
    """Aligned data for one development partition."""
    X: pd.DataFrame
    y: pd.Series
    identifiers: pd.DataFrame
    fairness_review: pd.DataFrame


@dataclass(frozen=True)
class DevelopmentSplits:
    """Training, validation, and untouched test partitions."""
    train: DataSplit
    validation: DataSplit
    test: DataSplit


def _take(bundle: FeatureBundle, indices: pd.Index) -> DataSplit:
    return DataSplit(
        X=bundle.features.loc[indices].copy(),
        y=bundle.label.loc[indices].copy(),
        identifiers=bundle.identifiers.loc[indices].copy(),
        fairness_review=bundle.fairness_review.loc[indices].copy(),
    )


def create_development_splits(bundle: FeatureBundle) -> DevelopmentSplits:
    """Create a reproducible 70/15/15 stratified teaching split."""
    train_idx, remainder_idx = train_test_split(
        bundle.features.index, test_size=0.30, random_state=RANDOM_STATE,
        stratify=bundle.label,
    )
    validation_idx, test_idx = train_test_split(
        remainder_idx, test_size=0.50, random_state=RANDOM_STATE,
        stratify=bundle.label.loc[remainder_idx],
    )
    return DevelopmentSplits(
        train=_take(bundle, pd.Index(train_idx)),
        validation=_take(bundle, pd.Index(validation_idx)),
        test=_take(bundle, pd.Index(test_idx)),
    )


def validate_splits(splits: DevelopmentSplits) -> dict[str, object]:
    """Prove partition separation and comparable label balance."""
    id_sets = {
        name: set(split.identifiers["EmployeeNumber"])
        for name, split in (
            ("train", splits.train), ("validation", splits.validation), ("test", splits.test)
        )
    }
    assert id_sets["train"].isdisjoint(id_sets["validation"])
    assert id_sets["train"].isdisjoint(id_sets["test"])
    assert id_sets["validation"].isdisjoint(id_sets["test"])
    assert len(set.union(*id_sets.values())) == 1470
    rates = {
        "train": float(splits.train.y.mean()),
        "validation": float(splits.validation.y.mean()),
        "test": float(splits.test.y.mean()),
    }
    assert max(rates.values()) - min(rates.values()) < 0.01
    return {
        "random_state": RANDOM_STATE,
        "method": "stratified random split for synthetic snapshot teaching data",
        "counts": {
            "train": len(splits.train.y),
            "validation": len(splits.validation.y),
            "test": len(splits.test.y),
        },
        "attrition_rates": rates,
        "employee_overlap": 0,
    }


def fit_training_preprocessor(splits: DevelopmentSplits):
    """Fit statistics and categories using training records only."""
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(splits.train.X)
    X_validation = preprocessor.transform(splits.validation.X)
    return preprocessor, X_train, X_validation


def evaluate_majority_baseline(splits: DevelopmentSplits) -> dict[str, float]:
    """Establish the minimum validation performance ML must improve upon."""
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(splits.train.X, splits.train.y)
    predictions = baseline.predict(splits.validation.X)
    probabilities = baseline.predict_proba(splits.validation.X)[:, 1]
    return {
        "accuracy": float(accuracy_score(splits.validation.y, predictions)),
        "precision": float(precision_score(splits.validation.y, predictions, zero_division=0)),
        "recall": float(recall_score(splits.validation.y, predictions, zero_division=0)),
        "f1": float(f1_score(splits.validation.y, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(splits.validation.y, probabilities)),
        "pr_auc": float(average_precision_score(splits.validation.y, probabilities)),
    }


def run_stage3() -> dict[str, object]:
    """Execute Stage 3 and persist an auditable result summary."""
    bundle = build_feature_bundle(load_data())
    splits = create_development_splits(bundle)
    manifest = validate_splits(splits)
    preprocessor, X_train, X_validation = fit_training_preprocessor(splits)
    baseline = evaluate_majority_baseline(splits)
    results = {
        "split_manifest": manifest,
        "transformed_shapes": {
            "train": list(X_train.shape), "validation": list(X_validation.shape)
        },
        "preprocessor_fit_population": "training only",
        "baseline_validation_metrics": baseline,
        "test_set_status": "untouched",
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(run_stage3(), indent=2))
