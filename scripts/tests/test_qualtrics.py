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
        "QID3": {"QuestionText": "Arm text", "QuestionType": "DB", "Selector": "TB", "DataExportTag": "ArmText"},
        "QID9": {"QuestionText": "Old", "QuestionType": "DB", "Selector": "TB"},
    },
    "SurveyFlow": {"Type": "Root", "Flow": [
        {"Type": "EmbeddedData", "EmbeddedData": [{"Field": "pid"}]},
        {"Type": "Block", "ID": "BL_a"},
        {"Type": "Branch", "Flow": [{"Type": "Standard", "ID": "BL_b"}]},
    ]},
}

INSTRUMENT = """\
## `S`

`Page timers: none`

## `Consent`

##### `Intro: Text [QID1]`

**Welcome** to the study.
Hi `[pid]`!

---

##### `Agree: Multiple choice [QID2]`

**Agree?**

- Yes
- No

## `Arm`

##### `ArmText: Text [QID3]`

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
    edited = INSTRUMENT.replace("##### `ArmText: Text [QID3]`\n\nArm text\n",
                                "##### `New: Text [NEW]`\n\nNew text\n")
    found = {(m["qid"], m["field"]) for m in compare(parse(edited), dump)}
    assert found == {("QID3", "missing_in_instrument"), ("NEW@23", "not_implemented"), ("Arm", "pages")}


def test_block_membership_and_order(dump):
    edited = """\
## `S`

`Page timers: none`

## `Arm`

##### `ArmText: Text [QID3]`

Arm text

## `Consent`

##### `Intro: Text [QID1]`

**Welcome** to the study.
Hi `[pid]`!

##### `Agree: Multiple choice [QID2]`

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
    definition["Questions"]["QID4"] = {"QuestionText": "Timing", "QuestionType": "Timing", "Selector": "PageTimer",
                                       "DataExportTag": "Q4"}
    definition["Questions"]["QID5"] = {"QuestionText": "Browser", "QuestionType": "Meta", "Selector": "Browser"}
    dump = normalize(definition)
    timed = INSTRUMENT.replace("Page timers: none", "Page timers: every page except in: Consent")
    assert compare(parse(timed), dump) == []

    listed = timed + "\n##### `Q4: Page timer [QID4]`\n"
    assert compare(parse(listed), dump) == [
        {"qid": "QID4", "field": "text", "instrument": "", "survey": "Timing"}]


def test_non_string_choice_labels_are_kept():
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID2"] = {**DEFINITION["Questions"]["QID2"],
                                       "Choices": {"1": {"Display": 1950}, "2": {"Display": "Yes"}}}
    assert normalize(definition)["questions"]["QID2"]["choices"] == ["Yes", "1950"]


def test_escaped_list_number_matches_literal_number(dump):
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {"QuestionText": "1. Arm text", "QuestionType": "DB", "Selector": "TB", "DataExportTag": "ArmText"}
    edited = INSTRUMENT.replace("\nArm text", "\n1\\. Arm text")
    assert compare(parse(edited), normalize(definition)) == []


def test_image_count_is_compared():
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {"QuestionText": 'Arm text<img src="https://x/IM_1">',
                                       "QuestionType": "DB", "Selector": "TB", "DataExportTag": "ArmText"}
    dump = normalize(definition)
    assert dump["questions"]["QID3"]["images"] == 1
    found = {(m["qid"], m["field"]) for m in compare(parse(INSTRUMENT), dump)}
    assert found == {("QID3", "images")}
    with_image = INSTRUMENT.replace("\nArm text", "\n`arm.png`\n\nArm text")
    assert compare(parse(with_image), dump) == []


def test_dump_keeps_javascript_and_redacts_web_service_headers():
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {**DEFINITION["Questions"]["QID3"], "QuestionJS": "alert(1)"}
    definition["SurveyFlow"] = {"Type": "Root", "Flow": [
        *DEFINITION["SurveyFlow"]["Flow"],
        {"Type": "Branch", "Flow": [{"Type": "WebService", "URL": "https://api",
                                     "Headers": [{"key": "Authorization", "value": "Basic secret"}]}]}]}
    dump = normalize(definition)
    assert dump["questions"]["QID3"]["js"] == "alert(1)"
    assert "secret" not in str(dump)
    assert dump["flow"]["Flow"][-1]["Flow"][0]["Headers"] == [{"key": "Authorization", "value": "[redacted]"}]


def test_label_must_match_export_tag(dump):
    edited = INSTRUMENT.replace("`Agree: Multiple", "`Consent2: Multiple")
    assert compare(parse(edited), dump) == [
        {"qid": "QID2", "field": "label", "instrument": "Consent2", "survey": "Agree"}]


def test_page_timers_are_checked_per_page():
    definition = {**DEFINITION, "Blocks": {**DEFINITION["Blocks"]}, "Questions": {**DEFINITION["Questions"]}}
    definition["Blocks"]["BL_a"] = {"Type": "Standard", "Description": "Consent", "BlockElements": [
        {"Type": "Question", "QuestionID": "QID1"}, {"Type": "Question", "QuestionID": "QID4"},
        {"Type": "Page Break"}, {"Type": "Question", "QuestionID": "QID2"}]}
    definition["Questions"]["QID4"] = {"QuestionText": "Timing", "QuestionType": "Timing", "Selector": "PageTimer"}
    dump = normalize(definition)
    every = INSTRUMENT.replace("Page timers: none", "Page timers: every page")
    assert compare(parse(every), dump) == [
        {"qid": "Consent", "field": "page_timers", "instrument": [True, True], "survey": [True, False]},
        {"qid": "Arm", "field": "page_timers", "instrument": [True], "survey": [False]}]


def test_undeclared_page_timers_are_reported(dump):
    undeclared = INSTRUMENT.replace("`Page timers: none`\n\n", "")
    assert compare(parse(undeclared), dump) == [
        {"qid": "survey", "field": "page_timers", "instrument": "undeclared", "survey": None}]
