from qualtrics_api import question_body


def test_question_body_keeps_writable_fields_and_applies_changes():
    before = {"QuestionText": "old", "DataExportTag": "Q1", "Validation": {"x": 1}, "QuestionID": "QID1",
              "DisplayLogic": {"0": {}}, "NextChoiceId": 4}
    body = question_body(before, {"QuestionText": "new"})
    assert body == {"QuestionText": "new", "DataExportTag": "Q1", "Validation": {"x": 1}, "DisplayLogic": {"0": {}}}


def test_question_body_removes_a_field_set_to_none():
    body = question_body({"QuestionText": "t", "DisplayLogic": {"0": {}}}, {"DisplayLogic": None})
    assert "DisplayLogic" not in body
