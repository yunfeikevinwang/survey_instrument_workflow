from pathlib import Path

import pytest

from instrument import InstrumentError, assign, diff, parse

REPO = Path(__file__).resolve().parents[2]

BASIC = """\
## `Survey`

```
Set [pid] from URL
Images: Drive Qualtrics/main_images/images_v1, https://drive.example/f; Qualtrics folder "Survey - v1"; 3px solid border on every image.
Page timers: every page except in: Demographics
```

## `Consent`

`Block note`

##### `Q1: Text [QID1]`

`logo_w300.png`

**Welcome** `Heading`

This takes *10 minutes*.

##### `Q2: Multiple choice, single answer [QID2]`

**Do you agree, `[pid]`?**

- I agree
- I do not agree `→ End of survey`

---

##### `New: Text entry [NEW]`

**Why?**

## `Demographics`

##### `Q3: Multiple choice [QID3]`

**Age?**

1. 18–24
2. 25+
"""


@pytest.fixture
def basic():
    return parse(BASIC)


def q(parsed, qid):
    return next(x for x in parsed["questions"] if x["id"] == qid)


# --- parse -------------------------------------------------------------------

def test_title_and_setup(basic):
    assert basic["title"] == "Survey"
    assert basic["setup"] == ["Set [pid] from URL\nImages: Drive Qualtrics/main_images/images_v1, https://drive.example/f; Qualtrics folder \"Survey - v1\"; 3px solid border on every image.\nPage timers: every page except in: Demographics"]
    assert basic["page_timers"] == {"except": ["Demographics"]}


@pytest.mark.parametrize("line, expected", [
    ("Page timers: every page", {"except": []}),
    ("Page timers: none", None),
])
def test_page_timer_forms(line, expected):
    parsed = parse(f"## `S`\n\n`{line}`\n\n## `B`\n")
    assert parsed["page_timers"] == expected


def test_undeclared_page_timers_are_unknown():
    assert parse("## `S`\n\n## `B`\n")["page_timers"] == "undeclared"


def test_malformed_page_timer_line_fails():
    with pytest.raises(InstrumentError, match="must be `every page`"):
        parse("## `S`\n\n`Page timers: every page, named Timer_x`\n\n## `B`\n")


def test_page_timer_exception_must_name_a_block():
    with pytest.raises(InstrumentError, match="no block named 'Nope'"):
        parse("## `S`\n\n`Page timers: every page except in: Nope`\n\n## `B`\n")


def test_blocks_with_notes_and_pages(basic):
    consent, demo = basic["blocks"]
    assert consent["name"] == "Consent"
    assert consent["notes"] == ["Block note"]
    assert consent["pages"] == [["QID1", "QID2"], ["NEW@30"]]
    assert demo["pages"] == [["QID3"]]


def test_question_fields(basic):
    q2 = q(basic, "QID2")
    assert q2["block"] == "Consent"
    assert q2["label"] == "Q2"
    assert q2["settings"] == "Multiple choice, single answer"
    assert q2["text"] == "**Do you agree, [pid]?**"
    assert q2["choices"] == [
        {"text": "I agree", "notes": []},
        {"text": "I do not agree", "notes": ["→ End of survey"]},
    ]


def test_images_and_styling_notes(basic):
    q1 = q(basic, "QID1")
    assert q1["images"] == ["logo_w300.png"]
    assert q1["text"] == "**Welcome**\nThis takes *10 minutes*."
    assert q1["notes"] == ["Heading"]


def test_new_question_keyed_by_line(basic):
    new = q(basic, "NEW")
    assert new["key"] == "NEW@30"
    assert new["line"] == 30
    assert new["label"] == "New"
    assert new["settings"] == "Text entry"


def test_numbered_choices(basic):
    assert [c["text"] for c in q(basic, "QID3")["choices"]] == ["18–24", "25+"]


def test_fenced_block_inside_question_is_note():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Text [QID1]`\n\nHi\n\n```\nIf x\n- not a choice\n```\n"
    q1 = parse(md)["questions"][0]
    assert q1["notes"] == ["If x\n- not a choice"]
    assert q1["choices"] == []


def test_wrapped_grid_table_parses():
    table = "+---+-----+\n| a | one |\n|   | two |\n+---+-----+"
    md = "## `S`\n\n## `B`\n\n```\n" + table + "\n" + "a long note " * 10 + "\n```\n"
    assert parse(md)["blocks"][0]["notes"] == [table + "\n" + "a long note " * 10]


def test_repo_sample_parses():
    parsed = parse((REPO / "instrument_v1.md").read_text())
    assert [b["name"] for b in parsed["blocks"]] == ["Consent", "AI usage", "Treatment", "Demographics"]
    assert len(parsed["questions"]) == 8


@pytest.mark.parametrize(
    "md, message",
    [
        ("## `S`\n\n## `B`\n\nVisible text\n", "outside a question"),
        ("## `S`\n\nVisible text\n", "outside a question"),
        ("## `S`\n\n## `B`\n\n##### `Q12: Text`\n", "must be `Label: settings \\[QIDn\\]`"),
        ("## `S`\n\n## `B`\n\n##### `QID12: Text`\n", "must be `Label: settings"),
        ("## `S`\n\n## `B`\n\n##### `Text [QID12]`\n", "must be `Label: settings"),
        ("## `S`\n\n## `B`\n\n##### `A: Text [QID1]`\n\n##### `A: Text [QID2]`\n", "Duplicate label 'A'"),
        ("## `S`\n\n## `B`\n\n#### `Q1: Text [QID1]`\n", "only `##` and `#####`"),
        ("## `S`\n\n## `B`\n\n### `Org`\n", "only `##` and `#####`"),
        ("# `S`\n", "only `##` and `#####`"),
        ("## `S`\n\n## `B`\n\n##### `Q1: Text [QID1]`\n\n### Welcome\n", "line 7: visible text can't be a heading"),
        ("## `S`\n\n##### `Q1: Text [QID1]`\n", "question before the first block"),
        ("## `S`\n\n## `B`\n\n##### `Q1: Text [QID1]`\n\n##### `Q1: Text [QID1]`\n", "Duplicate QID1"),
        ("## `S`\n\n## `B`\n\n## `B`\n", "Duplicate block"),
        ("## `S`\n\n## `B`\n\n```\nunclosed\n", "Unclosed code block"),
        ("## `S`\n\n```\n| a | " + "x" * 80 + " |\n```\n", "line 4: table row over 80 characters"),
        ("## `S`\n\n```\n+---+" + "-" * 80 + "+\n```\n", "line 4: table row over 80 characters"),
    ],
)
def test_format_violations_fail_loudly(md, message):
    with pytest.raises(InstrumentError, match=message):
        parse(md)


# --- diff --------------------------------------------------------------------

OLD = """\
## `S`

## `A`

##### `Q1: Text [QID1]`

Hello

##### `Q2: Multiple choice [QID2]`

**Pick**

- x
- y

## `B`

##### `Q3: Text [QID3]`

Bye
"""


def test_identical_instruments_have_no_changes():
    assert diff(parse(OLD), parse(OLD)) == {
        "setup_changed": False,
        "blocks": {"added": [], "removed": [], "order_changed": False,
                   "notes_changed": [], "pages_changed": [], "reordered": []},
        "questions": {"added": [], "removed": [], "changed": []},
    }


def test_question_changes_are_reported_by_field():
    new = OLD.replace("Hello", "Hi there").replace("- y", "- y\n- z")
    changes = diff(parse(OLD), parse(new))["questions"]["changed"]
    assert changes == [
        {"id": "QID1", "fields": {"text": {"old": "Hello", "new": "Hi there"}}},
        {"id": "QID2", "fields": {"choices": {
            "old": [{"text": "x", "notes": []}, {"text": "y", "notes": []}],
            "new": [{"text": "x", "notes": []}, {"text": "y", "notes": []}, {"text": "z", "notes": []}],
        }}},
    ]


def test_added_removed_and_moved():
    new = """\
## `S`

## `A`

##### `Q2: Multiple choice [QID2]`

**Pick**

- x
- y

##### `New: Text [NEW]`

Fresh

## `C`

##### `Q3: Text [QID3]`

Bye
"""
    d = diff(parse(OLD), parse(new))
    assert d["questions"]["removed"] == ["QID1"]
    assert [a["key"] for a in d["questions"]["added"]] == ["NEW@12"]
    assert d["questions"]["changed"] == [{"id": "QID3", "fields": {"block": {"old": "B", "new": "C"}}}]
    assert d["blocks"]["added"] == ["C"]
    assert d["blocks"]["removed"] == ["B"]
    assert d["blocks"]["pages_changed"] == ["A"]


def test_label_change_is_reported():
    new = OLD.replace("`Q1: Text [QID1]`", "`Hello: Text [QID1]`")
    assert diff(parse(OLD), parse(new))["questions"]["changed"] == [
        {"id": "QID1", "fields": {"label": {"old": "Q1", "new": "Hello"}}}]


def test_reorder_within_block():
    new = OLD.replace(
        "##### `Q1: Text [QID1]`\n\nHello\n\n##### `Q2: Multiple choice [QID2]`\n\n**Pick**\n\n- x\n- y\n",
        "##### `Q2: Multiple choice [QID2]`\n\n**Pick**\n\n- x\n- y\n\n##### `Q1: Text [QID1]`\n\nHello\n",
    )
    assert diff(parse(OLD), parse(new))["blocks"]["reordered"] == ["A"]


def test_page_break_change():
    new = OLD.replace("##### `Q2", "---\n\n##### `Q2")
    assert diff(parse(OLD), parse(new))["blocks"]["pages_changed"] == ["A"]


def test_unknown_qid_in_new_version_fails():
    new = OLD.replace("QID3", "QID99")
    with pytest.raises(InstrumentError, match="QID99"):
        diff(parse(OLD), parse(new))


# --- assign ------------------------------------------------------------------

def test_assign_replaces_new_with_qid():
    out = assign(BASIC, line=30, qid="QID9")
    assert "##### `New: Text entry [QID9]`" in out
    assert q(parse(out), "QID9")["settings"] == "Text entry"


def test_assign_rejects_non_new_line_and_existing_qid():
    with pytest.raises(InstrumentError, match="not a NEW question"):
        assign(BASIC, line=20, qid="QID9")
    with pytest.raises(InstrumentError, match="already used"):
        assign(BASIC, line=30, qid="QID1")


# --- list items as text ------------------------------------------------------

def test_list_in_text_question_is_text():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Text [QID1]`\n\nYou will:\n\n- Do this.\n1. Then that.\n"
    q1 = parse(md)["questions"][0]
    assert q1["choices"] == []
    assert q1["text"] == "You will:\nDo this.\nThen that."


def test_list_followed_by_text_is_text():
    md = ("## `S`\n\n## `B`\n\n##### `Q1: Multiple choice [QID1]`\n\nThat means:\n\n- Step one\n\n"
          "**Agree?**\n\n- Yes\n- No\n")
    q1 = parse(md)["questions"][0]
    assert [c["text"] for c in q1["choices"]] == ["Yes", "No"]
    assert q1["text"] == "That means:\nStep one\n**Agree?**"


def test_numbered_steps_before_bulleted_choice_are_text():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Multiple choice [QID1]`\n\n1. Open it\n2. Delete it\n\n- I did it\n"
    q1 = parse(md)["questions"][0]
    assert [c["text"] for c in q1["choices"]] == ["I did it"]
    assert q1["text"] == "Open it\nDelete it"


def test_bracketed_note_with_spaces_is_code():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Text [QID1]`\n\nSwipe `[down if iPhone]` now, `[pid]`.\n"
    q1 = parse(md)["questions"][0]
    assert q1["text"] == "Swipe now, [pid]."
    assert q1["notes"] == ["[down if iPhone]"]


def test_choice_range_note_expands_to_choices():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Dropdown list [QID1]`\n\n**Year?**\n\n`Choices: 1950–1953, one per year`\n"
    q1 = parse(md)["questions"][0]
    assert [c["text"] for c in q1["choices"]] == ["1950", "1951", "1952", "1953"]
    assert q1["notes"] == ["Choices: 1950–1953, one per year"]


def test_choice_range_with_listed_choices_fails():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Dropdown list [QID1]`\n\n`Choices: 1–3`\n\n- 1\n"
    with pytest.raises(InstrumentError, match="line 5: .*choice range"):
        parse(md)


def test_descending_choice_range_counts_down():
    md = "## `S`\n\n## `B`\n\n##### `Q1: Dropdown list [QID1]`\n\n`Choices: 2025–2023, one per year`\n"
    assert [c["text"] for c in parse(md)["questions"][0]["choices"]] == ["2025", "2024", "2023"]


def test_format_structure_example_parses():
    section = (REPO / "format.md").read_text().split("## Structure", 1)[1]
    example = section.split("````", 2)[1].split("\n", 1)[1]
    parsed = parse(example)
    assert [b["name"] for b in parsed["blocks"]] == ["Block name"]
    assert parsed["blocks"][0]["notes"][0].startswith("Before this block")


def test_images_setup_line(basic):
    assert basic["images"] == {"drive": "Qualtrics/main_images/images_v1", "link": "https://drive.example/f",
                               "folder": "Survey - v1", "border": {"px": 3, "except": []}}


def test_images_setup_line_with_no_folder_exceptions_and_no_border():
    legacy = BASIC.replace('Qualtrics folder "Survey - v1"; 3px solid border on every image.',
                           "Qualtrics folder none; 3px solid border on every image except logo_w300.png.")
    assert parse(legacy)["images"]["folder"] is None
    assert parse(legacy)["images"]["border"] == {"px": 3, "except": ["logo_w300.png"]}
    plain = BASIC.replace("3px solid border on every image.", "no border.")
    assert parse(plain)["images"]["border"] is None


def test_image_width_comes_from_the_file_name():
    from instrument import image_width
    assert image_width("google_phone_carrot_w250.png") == 250
    with pytest.raises(InstrumentError):
        image_width("logo.png")


def test_image_without_width_is_an_error():
    with pytest.raises(InstrumentError, match="_w<width>"):
        parse(BASIC.replace("logo_w300.png", "logo.png"))


def test_images_need_the_setup_line():
    no_line = "\n".join(l for l in BASIC.split("\n") if not l.startswith("Images:"))
    with pytest.raises(InstrumentError, match="Images:"):
        parse(no_line)


def test_malformed_images_line_is_an_error():
    with pytest.raises(InstrumentError, match="Images:"):
        parse(BASIC.replace("Qualtrics folder", "Folder"))


def test_border_exception_must_be_an_image_in_the_instrument():
    with pytest.raises(InstrumentError, match="other_w20.png"):
        parse(BASIC.replace("every image.", "every image except other_w20.png."))
