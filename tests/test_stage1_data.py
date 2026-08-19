from src.stage1_data_profile import load_data, validate_data


def test_public_dataset_passes_stage1_validation():
    report = validate_data(load_data())
    assert report["rows"] == 1470
    assert report["columns"] == 35
    assert report["unique_employees"] == 1470
    assert 0 < report["attrition_rate"] < 1
