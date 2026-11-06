import pytest

from instrument import parse
from qualtrics import compare, normalize

DEFINITION = {
    "SurveyID": "SV_TEST",
    "SurveyName": "Test Survey",
    "Blocks": {
        "BL_a": {"Type": "Standard", "Description": "Consent", "BlockElements": [
            {"Type": "Question", "QuestionID": "QID1"},
            {"Type": "Page Break"},
            {"Type": "Question", "QuestionID": "QID2"},
        ]},
        "BL_b": {"Type": "Standard", "Description": "Arm", "BlockElements": [
            {"Type": "Question", "QuestionID": "QID3"},
        ]},
        "BL_t": {"Type": "Trash", "Description": "Trash / Unused Questions", "BlockElements": [
            {"Type": "Question", "QuestionID": "QID9"},
        ]},
    },
    "Questions": {
        "QID1": {"QuestionText": "<b>Welcome</b> to the&nbsp;study.<br>Hi ${e://Field/pid}!",
                 "QuestionType": "DB", "Selector": "TB", "DataExportTag": "Intro"},
        "QID2": {"QuestionText": "<div>Agree?</div>", "QuestionType": "MC", "Selector": "SAVR",
                 "DataExportTag": "Agree", "ChoiceOrder": [2, 1],
                 "Choices": {"1": {"Display": "No"}, "2": {"Display": "<span>Yes</span>"}},
                 "DisplayLogic": {"0": {"Type": "If"}}},
        "QID3": {"QuestionText": "Arm text", "QuestionType": "DB", "Selector": "TB"},
        "QID9": {"QuestionText": "Old", "QuestionType": "DB", "Selector": "TB"},
    },
    "SurveyFlow": {"Type": "Root", "Flow": [
        {"Type": "EmbeddedData", "EmbeddedData": [{"Field": "pid"}]},
        {"Type": "Block", "ID": "BL_a"},
        {"Type": "Branch", "Flow": [{"Type": "Standard", "ID": "BL_b"}]},
    ]},
}

INSTRUMENT = """\
## `Consent`

##### `QID1: Text`

**Welcome** to the study.
Hi `[pid]`!

---

##### `QID2: Multiple choice`

**Agree?**

- Yes
- No

## `Arm`

##### `QID3: Text`

Arm text
"""


@pytest.fixture
def dump():
    return normalize(DEFINITION)


def test_normalize_blocks_in_flow_order_without_trash(dump):
    assert [(b["name"], b["pages"]) for b in dump["blocks"]] == [
        ("Consent", [["QID1"], ["QID2"]]),
        ("Arm", [["QID3"]]),
    ]
    assert "QID9" not in dump["questions"]


def test_normalize_question_text_and_choices(dump):
    q1, q2 = dump["questions"]["QID1"], dump["questions"]["QID2"]
    assert q1["text"] == "Welcome to the study.\nHi [pid]!"
    assert q1["block"] == "Consent"
    assert q2["choices"] == ["Yes", "No"]
    assert q2["type"] == "MC/SAVR"
    assert q2["display_logic"] == {"0": {"Type": "If"}}
    assert dump["embedded_data"] == ["pid"]


def test_matching_instrument_has_no_mismatches(dump):
    assert compare(parse(INSTRUMENT), dump) == []


def test_mismatches_are_reported_by_field(dump):
    edited = (INSTRUMENT.replace("Arm text", "Different text")
              .replace("- No", "- Maybe")
              .replace("---\n\n", ""))
    found = {(m["qid"], m["field"]) for m in compare(parse(edited), dump)}
    assert found == {("QID3", "text"), ("QID2", "choices"), ("Consent", "pages")}


def test_missing_new_and_moved_questions(dump):
    edited = INSTRUMENT.replace("##### `QID3: Text`\n\nArm text\n",
                                "##### `NEW: Text`\n\nNew text\n")
    found = {(m["qid"], m["field"]) for m in compare(parse(edited), dump)}
    assert found == {("QID3", "missing_in_instrument"), ("NEW@19", "not_implemented"), ("Arm", "pages")}


def test_block_membership_and_order(dump):
    edited = """\
## `Arm`

##### `QID3: Text`

Arm text

## `Consent`

##### `QID1: Text`

**Welcome** to the study.
Hi `[pid]`!

##### `QID2: Multiple choice`

**Agree?**

- Yes
- No
"""
    found = {(m["qid"], m["field"]) for m in compare(parse(edited), dump)}
    assert found == {("survey", "block_order"), ("Consent", "pages")}


def test_helper_questions_are_ignored_unless_listed():
    definition = {**DEFINITION, "Blocks": {**DEFINITION["Blocks"]}, "Questions": {**DEFINITION["Questions"]}}
    definition["Blocks"]["BL_b"] = {"Type": "Standard", "Description": "Arm", "BlockElements": [
        {"Type": "Question", "QuestionID": "QID3"}, {"Type": "Question", "QuestionID": "QID4"},
        {"Type": "Question", "QuestionID": "QID5"}]}
    definition["Questions"]["QID4"] = {"QuestionText": "Timing", "QuestionType": "Timing", "Selector": "PageTimer"}
    definition["Questions"]["QID5"] = {"QuestionText": "Browser", "QuestionType": "Meta", "Selector": "Browser"}
    dump = normalize(definition)
    assert compare(parse(INSTRUMENT), dump) == []

    listed = INSTRUMENT + "\n##### `QID4: Page timer`\n"
    assert compare(parse(listed), dump) == [
        {"qid": "QID4", "field": "text", "instrument": "", "survey": "Timing"}]
