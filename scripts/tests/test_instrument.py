from pathlib import Path

import pytest

from instrument import InstrumentError, assign, diff, parse

REPO = Path(__file__).resolve().parents[2]

BASIC = """\
# `Survey`

```
Set [pid] from URL
```

## `Consent`

`Block note`

##### `QID1: Text`

`logo.png`

### Welcome

This takes *10 minutes*.

##### `QID2: Multiple choice, single answer`

**Do you agree, `[pid]`?**

- I agree
- I do not agree `→ End of survey`

---

##### `NEW: Text entry`

**Why?**

## `Demographics`

### `Age section`

##### `QID3: Multiple choice`

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
    assert basic["setup"] == ["Set [pid] from URL"]


def test_blocks_with_notes_and_pages(basic):
    consent, demo = basic["blocks"]
    assert consent["name"] == "Consent"
    assert consent["notes"] == ["Block note"]
    assert consent["pages"] == [["QID1", "QID2"], ["NEW@28"]]
    assert demo["pages"] == [["QID3"]]


def test_question_fields(basic):
    q2 = q(basic, "QID2")
    assert q2["block"] == "Consent"
    assert q2["settings"] == "Multiple choice, single answer"
    assert q2["text"] == "**Do you agree, [pid]?**"
    assert q2["choices"] == [
        {"text": "I agree", "notes": []},
        {"text": "I do not agree", "notes": ["→ End of survey"]},
    ]


def test_images_and_visible_headings(basic):
    q1 = q(basic, "QID1")
    assert q1["images"] == ["logo.png"]
    assert q1["text"] == "### Welcome\nThis takes *10 minutes*."
    assert q1["notes"] == []


def test_new_question_keyed_by_line(basic):
    new = q(basic, "NEW")
    assert new["key"] == "NEW@28"
    assert new["line"] == 28
    assert new["settings"] == "Text entry"


def test_numbered_choices(basic):
    assert [c["text"] for c in q(basic, "QID3")["choices"]] == ["18–24", "25+"]


def test_fenced_block_inside_question_is_note():
    md = "## `B`\n\n##### `QID1: Text`\n\nHi\n\n```\nIf x\n- not a choice\n```\n"
    q1 = parse(md)["questions"][0]
    assert q1["notes"] == ["If x\n- not a choice"]
    assert q1["choices"] == []


def test_repo_sample_parses():
    parsed = parse((REPO / "instrument_v1.md").read_text())
    assert [b["name"] for b in parsed["blocks"]] == ["Consent", "AI usage", "Treatment", "Demographics"]
    assert len(parsed["questions"]) == 8


@pytest.mark.parametrize(
    "md, message",
    [
        ("## `B`\n\nVisible text\n", "outside a question"),
        ("Visible text\n", "outside a question"),
        ("## `B`\n\n##### `Q12: Text`\n", "must start with QIDn or NEW"),
        ("## `B`\n\n##### `QID1: Text`\n\n##### `QID1: Text`\n", "Duplicate QID1"),
        ("## `B`\n\n## `B`\n", "Duplicate block"),
        ("## `B`\n\n### `Org`\n\n- option\n", "outside a question"),
        ("## `B`\n\n```\nunclosed\n", "Unclosed code block"),
    ],
)
def test_format_violations_fail_loudly(md, message):
    with pytest.raises(InstrumentError, match=message):
        parse(md)


# --- diff --------------------------------------------------------------------

OLD = """\
## `A`

##### `QID1: Text`

Hello

##### `QID2: Multiple choice`

**Pick**

- x
- y

## `B`

##### `QID3: Text`

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
## `A`

##### `QID2: Multiple choice`

**Pick**

- x
- y

##### `NEW: Text`

Fresh

## `C`

##### `QID3: Text`

Bye
"""
    d = diff(parse(OLD), parse(new))
    assert d["questions"]["removed"] == ["QID1"]
    assert [a["key"] for a in d["questions"]["added"]] == ["NEW@10"]
    assert d["questions"]["changed"] == [{"id": "QID3", "fields": {"block": {"old": "B", "new": "C"}}}]
    assert d["blocks"]["added"] == ["C"]
    assert d["blocks"]["removed"] == ["B"]
    assert d["blocks"]["pages_changed"] == ["A"]


def test_reorder_within_block():
    new = OLD.replace(
        "##### `QID1: Text`\n\nHello\n\n##### `QID2: Multiple choice`\n\n**Pick**\n\n- x\n- y\n",
        "##### `QID2: Multiple choice`\n\n**Pick**\n\n- x\n- y\n\n##### `QID1: Text`\n\nHello\n",
    )
    assert diff(parse(OLD), parse(new))["blocks"]["reordered"] == ["A"]


def test_page_break_change():
    new = OLD.replace("##### `QID2", "---\n\n##### `QID2")
    assert diff(parse(OLD), parse(new))["blocks"]["pages_changed"] == ["A"]


def test_unknown_qid_in_new_version_fails():
    new = OLD.replace("QID3", "QID99")
    with pytest.raises(InstrumentError, match="QID99"):
        diff(parse(OLD), parse(new))


# --- assign ------------------------------------------------------------------

def test_assign_replaces_new_with_qid():
    out = assign(BASIC, line=28, qid="QID9")
    assert "##### `QID9: Text entry`" in out
    assert q(parse(out), "QID9")["settings"] == "Text entry"


def test_assign_rejects_non_new_line_and_existing_qid():
    with pytest.raises(InstrumentError, match="not a NEW question"):
        assign(BASIC, line=11, qid="QID9")
    with pytest.raises(InstrumentError, match="already used"):
        assign(BASIC, line=28, qid="QID1")


# --- list items as text ------------------------------------------------------

def test_list_in_text_question_is_text():
    md = "## `B`\n\n##### `QID1: Text`\n\nYou will:\n\n- Do this.\n1. Then that.\n"
    q1 = parse(md)["questions"][0]
    assert q1["choices"] == []
    assert q1["text"] == "You will:\nDo this.\nThen that."


def test_list_followed_by_text_is_text():
    md = ("## `B`\n\n##### `QID1: Multiple choice`\n\nThat means:\n\n- Step one\n\n"
          "**Agree?**\n\n- Yes\n- No\n")
    q1 = parse(md)["questions"][0]
    assert [c["text"] for c in q1["choices"]] == ["Yes", "No"]
    assert q1["text"] == "That means:\nStep one\n**Agree?**"


def test_numbered_steps_before_bulleted_choice_are_text():
    md = "## `B`\n\n##### `QID1: Multiple choice`\n\n1. Open it\n2. Delete it\n\n- I did it\n"
    q1 = parse(md)["questions"][0]
    assert [c["text"] for c in q1["choices"]] == ["I did it"]
    assert q1["text"] == "Open it\nDelete it"


def test_bracketed_note_with_spaces_is_code():
    md = "## `B`\n\n##### `QID1: Text`\n\nSwipe `[down if iPhone]` now, `[pid]`.\n"
    q1 = parse(md)["questions"][0]
    assert q1["text"] == "Swipe now, [pid]."
    assert q1["notes"] == ["[down if iPhone]"]
