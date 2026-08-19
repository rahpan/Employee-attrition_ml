from src.stage5_threshold_final_evaluation import choose_precision_threshold, run_stage5


def test_precision_policy_obeys_recall_guardrail():
    y_true = [0, 0, 0, 1, 1]
    probabilities = [0.1, 0.2, 0.7, 0.6, 0.9]
    threshold, tradeoffs = choose_precision_threshold(y_true, probabilities)
    selected = next(row for row in tradeoffs if row["threshold"] == threshold)
    assert selected["recall"] >= 0.40


def test_final_evaluation_uses_test_once_and_selected_policy():
    results = run_stage5()
    assert results["business_priority"] == "generate fewer false alerts"
    assert results["test_evaluation_count"] == 1
    assert results["threshold_policy"]["selected_threshold"] >= 0.50
    assert results["test_metrics"]["precision"] > 0.0
