from src.stage4_train_models import evaluate_predictions, train_and_compare


def test_metric_calculation_uses_positive_attrition_class():
    metrics = evaluate_predictions(
        y_true=[0, 0, 1, 1],
        probabilities=[0.1, 0.8, 0.4, 0.9],
        threshold=0.5,
    )
    assert metrics["confusion_matrix"] == {
        "true_negative": 1, "false_positive": 1,
        "false_negative": 1, "true_positive": 1,
    }


def test_candidates_beat_zero_recall_baseline_without_test_data():
    _, results = train_and_compare()
    assert results["test_set_status"] == "untouched"
    assert results["baseline"]["recall"] == 0.0
    for metrics in results["candidate_metrics"].values():
        assert metrics["recall"] > 0.0
        assert metrics["roc_auc"] > 0.5
        assert metrics["pr_auc"] > results["baseline"]["pr_auc"]
