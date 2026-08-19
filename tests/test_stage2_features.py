from src.stage1_data_profile import load_data
from src.stage2_features import (
    APPROVED_FEATURES,
    CONSTANT_COLUMNS,
    IDENTIFIER_COLUMNS,
    SENSITIVE_COLUMNS,
    UNSUPPORTED_RATE_COLUMNS,
    build_feature_bundle,
    build_preprocessor,
)


def test_feature_bundle_separates_model_and_governance_data():
    bundle = build_feature_bundle(load_data())
    assert bundle.features.shape == (1470, 24)
    assert bundle.label.value_counts().to_dict() == {0: 1233, 1: 237}
    assert list(bundle.identifiers.columns) == IDENTIFIER_COLUMNS
    assert list(bundle.fairness_review.columns) == SENSITIVE_COLUMNS


def test_excluded_columns_are_not_model_features():
    excluded = set(CONSTANT_COLUMNS + IDENTIFIER_COLUMNS + SENSITIVE_COLUMNS + UNSUPPORTED_RATE_COLUMNS)
    assert excluded.isdisjoint(APPROVED_FEATURES)


def test_preprocessor_is_defined_but_unfitted():
    preprocessor = build_preprocessor()
    assert not hasattr(preprocessor, "transformers_")
