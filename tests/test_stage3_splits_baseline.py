from src.stage1_data_profile import load_data
from src.stage2_features import build_feature_bundle
from src.stage3_splits_baseline import (
    create_development_splits,
    evaluate_majority_baseline,
    fit_training_preprocessor,
    validate_splits,
)


def _splits():
    return create_development_splits(build_feature_bundle(load_data()))


def test_split_sizes_overlap_and_balance():
    manifest = validate_splits(_splits())
    assert manifest["counts"] == {"train": 1029, "validation": 220, "test": 221}
    assert manifest["employee_overlap"] == 0


def test_preprocessor_fits_training_only_and_transforms_validation():
    splits = _splits()
    preprocessor, X_train, X_validation = fit_training_preprocessor(splits)
    assert hasattr(preprocessor, "transformers_")
    assert X_train.shape[0] == 1029
    assert X_validation.shape[0] == 220
    assert X_train.shape[1] == X_validation.shape[1]


def test_majority_baseline_reveals_accuracy_trap():
    metrics = evaluate_majority_baseline(_splits())
    assert metrics["accuracy"] > 0.80
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["roc_auc"] == 0.5
