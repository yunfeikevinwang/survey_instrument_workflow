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
        "QID2": {"QuestionText": "<div><strong>Agree?</strong></div>", "QuestionType": "MC", "Selector": "SAVR",
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


def with_arm_html(html):
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {"QuestionText": html, "QuestionType": "DB", "Selector": "TB",
                                       "DataExportTag": "ArmText"}
    return normalize(definition)


IMAGES_SETUP = ('`Images: Drive Qualtrics/main_images, https://d/f; Qualtrics folder "Consumer AI Survey 1"; '
                '3px solid border on every image.`')
BORDERED = ('Arm text<img src="https://x/?IM=IM_1" width="250" height="544" '
            'style="width: 250px; height: 544px; border-width: 3px; border-style: solid;">')


def with_image(name="arm_w250.png", setup=IMAGES_SETUP):
    return (INSTRUMENT.replace("`Page timers: none`", f"`Page timers: none`\n\n{setup}")
            .replace("\nArm text", f"\n`{name}`\n\nArm text"))


def test_dump_records_each_image():
    dump = with_arm_html(BORDERED)
    assert dump["questions"]["QID3"]["images"] == [{"im": "IM_1", "width": 250, "height": 544, "border_px": 3}]


def test_image_count_is_compared():
    dump = with_arm_html(BORDERED)
    found = {(m["qid"], m["field"]) for m in compare(parse(INSTRUMENT), dump)}
    assert found == {("QID3", "images")}
    assert compare(parse(with_image()), dump) == []


def test_image_width_and_border_are_compared():
    dump = with_arm_html(BORDERED.replace("border-width: 3px; border-style: solid;", ""))
    found = {(m["qid"], m["field"]) for m in compare(parse(with_image("arm_w300.png")), dump)}
    assert found == {("QID3", "image_width"), ("QID3", "image_border")}
    excepted = IMAGES_SETUP.replace("every image.", "every image except arm_w250.png.")
    assert compare(parse(with_image(setup=excepted)), dump) == []


def test_pixels_catch_stretching_and_upscaling():
    dump = with_arm_html(BORDERED)
    assert compare(parse(with_image()), dump, pixels={"IM_1": (942, 2048)}) == []
    found = {m["field"] for m in compare(parse(with_image()), dump, pixels={"IM_1": (942, 1000)})}
    assert found == {"image_stretched"}
    found = {m["field"] for m in compare(parse(with_image()), dump, pixels={"IM_1": (200, 435)})}
    assert found == {"image_upscaled"}


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


def _with_links():
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {
        "QuestionText": 'Arm text by <a href="https://x.org/p" target="_blank"><strong>Prof X</strong></a>. '
                        'Go to <a href="https://y.com/" target="_blank">https://y.com/</a>',
        "QuestionType": "DB", "Selector": "TB", "DataExportTag": "ArmText"}
    return normalize(definition)


def test_dump_records_links():
    assert _with_links()["questions"]["QID3"]["links"] == [["Prof X", "https://x.org/p"],
                                                          ["https://y.com/", "https://y.com/"]]


def test_markdown_links_match_live_links():
    edited = INSTRUMENT.replace("\nArm text\n", "\nArm text by **[Prof X](https://x.org/p)**. Go to <https://y.com/>\n")
    assert compare(parse(edited), _with_links()) == []


def test_link_target_mismatch_is_reported():
    edited = INSTRUMENT.replace("\nArm text\n", "\nArm text by **[Prof X](https://x.org/q)**. Go to <https://y.com/>\n")
    assert compare(parse(edited), _with_links()) == [
        {"qid": "QID3", "field": "links", "instrument": [["Prof X", "https://x.org/q"], ["https://y.com/", "https://y.com/"]],
         "survey": [["Prof X", "https://x.org/p"], ["https://y.com/", "https://y.com/"]]}]


def _with_text(html_text):
    definition = {**DEFINITION, "Questions": {**DEFINITION["Questions"]}}
    definition["Questions"]["QID3"] = {"QuestionText": html_text, "QuestionType": "DB", "Selector": "TB",
                                       "DataExportTag": "ArmText"}
    return normalize(definition)


def test_dump_records_bold_and_italic_runs():
    q = _with_text('<b>Welcome</b> to the <em>study</em>, <span style="font-weight: bold;">${e://Field/pid}</span>.'
                   '<h2>Title</h2><i>aside</i>')["questions"]["QID3"]
    assert q["bold"] == ["Welcome", "[pid]", "Title"]
    assert q["italic"] == ["study", "aside"]


def test_adjacent_runs_merge_and_line_breaks_split_them():
    q = _with_text("<strong>Log in</strong> <strong>now</strong>&nbsp;<strong>please</strong>"
                   "<br><strong>Next</strong><br>\n<strong>line</strong> plain")["questions"]["QID3"]
    assert q["bold"] == ["Log in now please", "Next", "line"]


def test_markdown_bold_and_italic_match_live_runs():
    dump = _with_text("<h2><strong>Title</strong></h2>\n<strong>Log in</strong> to <em>your</em> account.")
    edited = INSTRUMENT.replace("\nArm text\n", "\n**Title** `Heading`\n\n**Log in** to *your* account.\n")
    assert compare(parse(edited), dump) == []


def test_bold_and_italic_mismatches_are_reported():
    dump = _with_text("Log in to <em>your</em> account.")
    edited = INSTRUMENT.replace("\nArm text\n", "\n**Log in** to your account.\n")
    assert compare(parse(edited), dump) == [
        {"qid": "QID3", "field": "bold", "instrument": ["Log in"], "survey": []},
        {"qid": "QID3", "field": "italic", "instrument": [], "survey": ["your"]}]


def test_bold_in_choices_is_compared(dump):
    edited = INSTRUMENT.replace("- Yes", "- **Yes**")
    assert [(m["qid"], m["field"]) for m in compare(parse(edited), dump)] == [("QID2", "bold")]
