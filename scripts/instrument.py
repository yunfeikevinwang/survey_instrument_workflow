"""Parse, diff, and update survey instruments written in the format of format.md.

  instrument.py parse FILE              structured JSON of the instrument
  instrument.py diff OLD NEW            changes between two versions, keyed by QID
  instrument.py assign FILE LINE QID    replace [NEW] in the question header on LINE with [QID] (in place)
  instrument.py handoff FROM TO         fields TO's authenticator reads that FROM's workflow doesn't write (JSON list)
"""

import argparse
import json
import re
import sys
from pathlib import Path

RE_FENCE = re.compile(r"^\s*(```|~~~)")
RE_TABLE_ROW = re.compile(r"^\s*[|+]")
MAX_TABLE_WIDTH = 80
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
RE_CODE_ONLY = re.compile(r"^(`+)(.+?)\1$")
RE_CODE_SPAN = re.compile(r"(`+)(.+?)\1")
RE_PAGE_BREAK = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
RE_LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+(.*)$")
RE_QUESTION_HEADER = re.compile(r"^(?P<label>[^\s:\[\]]+):\s*(?P<settings>.*?)\s*\[(?P<id>QID\d+|NEW)\]$")
RE_PAGE_TIMERS_LINE = re.compile(r"^Page timers:(.*)$", re.MULTILINE)
RE_PAGE_TIMERS = re.compile(r"^\s*(?P<rule>none|every page(?:\s+except in:\s*(?P<blocks>.+))?)\s*$")
RE_PIPED = re.compile(r"^\[[^\]\s]+\]$")
RE_TEXT_QUESTION = re.compile(r"^Text\b(?!\s+entry)", re.IGNORECASE)
RE_CHOICE_RANGE = re.compile(r"^Choices:\s*(\d+)\s*[–-]\s*(\d+)\b")
RE_IMAGE = re.compile(r"^[\w.\-/]+\.(png|jpe?g|gif|svg|webp)$", re.IGNORECASE)
RE_IMAGE_WIDTH = re.compile(r"_w(\d+)\.[a-z]+$", re.IGNORECASE)
RE_IMAGES_LINE = re.compile(r"^Images:(.*)$", re.MULTILINE)
RE_IMAGES_DRIVE = re.compile(r"^Drive\s+(?P<drive>[^,]+?),\s*(?P<link>\S+)$")
RE_IMAGES_FOLDER = re.compile(r'^Qualtrics folder\s+(?:"(?P<folder>[^"]+)"|none)$')
RE_IMAGES_BORDER = re.compile(r"^(?:(?P<px>\d+)px solid border on every image"
                              r"(?:\s+except\s+(?P<except>[\w\-]+(?:\.[\w\-]+)+(?:,\s*[\w\-]+(?:\.[\w\-]+)+)*))?|no border)\.?$")
IMAGES_LINE_FORMAT = ('`Images: Drive <path>, <link>; Qualtrics folder "<name>" (or none); '
                      '<N>px solid border on every image [except a_w20.png, b_w200.png] (or no border).`')

RE_WORKFLOW_LINE = re.compile(r'^Workflow "(?P<name>[^"]+)":(?P<rest>.*)$', re.MULTILINE)
RE_AUTH_LINE = re.compile(r"^Authenticator before the first block:(.*)$", re.MULTILINE)
RE_LIST_ID = re.compile(r"contact list \"[^\"]+\" \((CG_\w+)")
RE_FIELDS_LINE = r"^{} fields:(.*)$"

QUESTION_FIELDS = ["block", "label", "settings", "text", "choices", "notes", "images"]


class InstrumentError(ValueError):
    pass


def split_code(text: str) -> tuple[str, list[str], list[str]]:
    """Split a line into (visible text, code notes, image file names); piped `[Var]` stays visible."""
    notes, images = [], []

    def replace(match):
        content = match.group(2).strip()
        if RE_PIPED.match(content):
            return content
        (images if RE_IMAGE.match(content) else notes).append(content)
        return ""

    visible = re.sub(r"\s{2,}", " ", RE_CODE_SPAN.sub(replace, text)).strip()
    return visible, notes, images


def parse(md: str) -> dict:
    result = {"title": None, "setup": [], "page_timers": "undeclared", "images": None,
              "blocks": [], "questions": []}
    block = None        # current block dict
    question = None     # current question dict
    page = 0
    entries: list[tuple] = []  # ("text", visible) or ("item", visible, notes, numbered), in order
    fence_start, fence_lines = None, []

    def close_question():
        """Choices are the trailing run of same-style list items; other list items are text."""
        nonlocal question
        if question is not None:
            first_choice = len(entries)
            if not RE_TEXT_QUESTION.match(question["settings"]):
                while (first_choice > 0 and entries[first_choice - 1][0] == "item"
                       and entries[first_choice - 1][3] == entries[-1][3]):
                    first_choice -= 1
            lines = []
            for entry in entries[:first_choice]:
                if entry[0] == "item":
                    question["notes"].extend(entry[2])
                if entry[1]:
                    lines.append(entry[1])
            question["text"] = "\n".join(lines)
            question["choices"] = [{"text": e[1], "notes": e[2]} for e in entries[first_choice:]]
            ranges = [m for m in map(RE_CHOICE_RANGE.match, question["notes"]) if m]
            if ranges:
                if question["choices"] or len(ranges) > 1:
                    raise InstrumentError(f"line {question['line']}: a choice range must be the question's only choices")
                low, high = int(ranges[0].group(1)), int(ranges[0].group(2))
                step = 1 if high >= low else -1  # year lists often run newest first
                question["choices"] = [{"text": str(n), "notes": []} for n in range(low, high + step, step)]
            entries.clear()
        question = None

    def note_target() -> list[str]:
        if question is not None:
            return question["notes"]
        return block["notes"] if block is not None else result["setup"]

    def outside(lineno: int):
        raise InstrumentError(f"line {lineno}: visible text outside a question")

    for lineno, line in enumerate(md.splitlines(), start=1):
        if fence_start is not None:
            if RE_FENCE.match(line):
                note_target().append("\n".join(fence_lines))
                fence_start, fence_lines = None, []
            else:
                if RE_TABLE_ROW.match(line) and len(line) > MAX_TABLE_WIDTH:
                    raise InstrumentError(f"line {lineno}: table row over {MAX_TABLE_WIDTH} characters; "
                                          "wrap long cells onto more lines (a grid table)")
                fence_lines.append(line)
            continue
        if RE_FENCE.match(line):
            fence_start = lineno
            continue
        if not line.strip():
            continue

        heading = RE_HEADING.match(line)
        if heading:
            code_heading = RE_CODE_ONLY.match(heading.group(2))
            if not code_heading:
                raise InstrumentError(f"line {lineno}: visible text can't be a heading; "
                                      "write it as a paragraph with its style as a code note")
            level, name = len(heading.group(1)), code_heading.group(2).strip()
            if level not in (2, 5):
                raise InstrumentError(f"line {lineno}: only `##` and `#####` headings are allowed (title and blocks, questions)")
            close_question()
            if level == 2 and result["title"] is None:
                result["title"] = name
            elif level == 2:
                if any(b["name"] == name for b in result["blocks"]):
                    raise InstrumentError(f"line {lineno}: Duplicate block '{name}'")
                block = {"name": name, "line": lineno, "notes": [], "pages": []}
                result["blocks"].append(block)
                page = 0
            else:
                if block is None:
                    raise InstrumentError(f"line {lineno}: question before the first block")
                m = RE_QUESTION_HEADER.match(name)
                if not m:
                    raise InstrumentError(f"line {lineno}: question header must be `Label: settings [QIDn]` "
                                          f"or `Label: settings [NEW]`: {name}")
                qid, label = m["id"], m["label"]
                key = qid if qid != "NEW" else f"NEW@{lineno}"
                if any(x["key"] == key for x in result["questions"]):
                    raise InstrumentError(f"line {lineno}: Duplicate {qid}")
                if any(x["label"] == label for x in result["questions"]):
                    raise InstrumentError(f"line {lineno}: Duplicate label '{label}'")
                question = {"id": qid, "key": key, "line": lineno, "block": block["name"], "page": page,
                            "label": label, "settings": m["settings"], "text": "", "choices": [],
                            "notes": [], "images": []}
                result["questions"].append(question)
            continue

        if RE_PAGE_BREAK.match(line):
            close_question()
            page += 1
            continue

        item = RE_LIST_ITEM.match(line)
        visible, notes, images = split_code(item.group(2) if item else line)
        if question is None:
            if visible or images or item:
                outside(lineno)
            note_target().extend(notes)
            continue
        for name in images:
            if not RE_IMAGE_WIDTH.search(name):
                raise InstrumentError(f"line {lineno}: image file name must end in _w<width>, e.g. "
                                      f"logo_w300.png: {name}")
        question["images"].extend(images)
        if item:
            entries.append(("item", visible, notes, item.group(1)[0].isdigit()))
        else:
            question["notes"].extend(notes)
            if visible:
                entries.append(("text", visible))

    if fence_start is not None:
        raise InstrumentError(f"line {fence_start}: Unclosed code block")
    close_question()

    result["page_timers"] = page_timers(result)
    result["images"] = images_setup(result)
    result["workflow"] = workflow_setup(result)
    result["authenticator"] = authenticator_setup(result)
    for b in result["blocks"]:
        pages: dict[int, list[str]] = {}
        for x in result["questions"]:
            if x["block"] == b["name"]:
                pages.setdefault(x["page"], []).append(x["key"])
        b["pages"] = [pages[p] for p in sorted(pages)]
    return result


def page_timers(parsed: dict):
    """The setup line `Page timers: every page [except in: A; B]` or `Page timers: none`."""
    lines = [m.group(1) for note in parsed["setup"] for m in RE_PAGE_TIMERS_LINE.finditer(note)]
    if not lines:
        return "undeclared"
    if len(lines) > 1:
        raise InstrumentError("more than one `Page timers:` line")
    rules = [RE_PAGE_TIMERS.match(lines[0])]
    if not rules[0]:
        raise InstrumentError(f"Page timers: must be `every page`, `every page except in: A; B` or `none`: {lines[0]}")
    if rules[0]["rule"] == "none":
        return None
    excepted = [name.strip() for name in (rules[0]["blocks"] or "").split(";") if name.strip()]
    names = {b["name"] for b in parsed["blocks"]}
    for name in excepted:
        if name not in names:
            raise InstrumentError(f"Page timers: no block named '{name}'")
    return {"except": excepted}


def image_width(name: str) -> int:
    m = RE_IMAGE_WIDTH.search(name)
    if not m:
        raise InstrumentError(f"image file name must end in _w<width>: {name}")
    return int(m.group(1))


def images_setup(parsed: dict):
    """The setup line naming the images' Drive folder, Qualtrics library folder and border rule."""
    lines = [m.group(1).strip() for note in parsed["setup"] for m in RE_IMAGES_LINE.finditer(note)]
    if not lines:
        if any(x["images"] for x in parsed["questions"]):
            raise InstrumentError(f"the instrument uses images but has no Images: setup line; write {IMAGES_LINE_FORMAT}")
        return None
    if len(lines) > 1:
        raise InstrumentError("more than one `Images:` line")
    parts = [p.strip() for p in lines[0].split(";")]
    matches = [rx.match(p) for rx, p in zip((RE_IMAGES_DRIVE, RE_IMAGES_FOLDER, RE_IMAGES_BORDER), parts)]
    if len(parts) != 3 or not all(matches):
        raise InstrumentError(f"Images: line must read {IMAGES_LINE_FORMAT}: {lines[0]}")
    drive, folder, border = matches
    excepted = [x.strip() for x in (border["except"] or "").split(",") if x.strip()]
    used = {name for x in parsed["questions"] for name in x["images"]}
    for name in excepted:
        if name not in used:
            raise InstrumentError(f"Images: border exception {name} is not an image in the instrument")
    return {"drive": drive["drive"].strip(), "link": drive["link"], "folder": folder["folder"],
            "border": {"px": int(border["px"]), "except": excepted} if border["px"] else None}


def setup_lines(parsed: dict, regex) -> list:
    return [m for note in parsed["setup"] for m in regex.finditer(note)]


def field_list(parsed: dict, kind: str):
    lines = [m.group(1) for m in setup_lines(parsed, re.compile(RE_FIELDS_LINE.format(kind), re.MULTILINE))]
    if len(lines) > 1:
        raise InstrumentError(f"more than one `{kind} fields:` line")
    return [f.strip() for f in lines[0].split(",") if f.strip()] if lines else None


def list_id(line: str, what: str) -> str:
    m = RE_LIST_ID.search(line)
    if not m:
        raise InstrumentError(f'{what} must name its contact list as contact list "<name>" (CG_…): {line.strip()}')
    return m.group(1)


def workflow_setup(parsed: dict):
    """`Workflow "<name>": … contact list "<name>" (CG_…) …` plus `Workflow fields: source → target, …`."""
    lines, fields = setup_lines(parsed, RE_WORKFLOW_LINE), field_list(parsed, "Workflow")
    if not lines and fields is None:
        return None
    if len(lines) != 1 or fields is None:
        raise InstrumentError("a workflow needs one `Workflow \"<name>\": …` line and one `Workflow fields:` line")
    pairs = [f.split("→") for f in fields]
    if any(len(p) != 2 or not p[0].strip() or not p[1].strip() for p in pairs):
        raise InstrumentError(f"Workflow fields: write each as `source → target`: {', '.join(fields)}")
    return {"name": lines[0]["name"], "list": list_id(lines[0]["rest"], "Workflow"),
            "fields": {s.strip(): d.strip() for s, d in pairs}}


def authenticator_setup(parsed: dict):
    """Only an instrument that lists `Authenticator fields:` takes part in a handoff, so older ones still parse."""
    lines, fields = setup_lines(parsed, RE_AUTH_LINE), field_list(parsed, "Authenticator")
    if fields is None:
        return None
    if len(lines) != 1:
        raise InstrumentError("`Authenticator fields:` needs one `Authenticator before the first block: …` line")
    return {"list": list_id(lines[0].group(1), "Authenticator"), "fields": fields}


def handoff(sender: dict, receiver: dict) -> list[str]:
    """What breaks between a survey's workflow and the next survey's authenticator."""
    w, a = sender["workflow"], receiver["authenticator"]
    if w is None or a is None:
        raise InstrumentError("handoff needs a Workflow in the first instrument and an Authenticator in the second")
    problems = [] if w["list"] == a["list"] else [f"the workflow writes to {w['list']} but the authenticator reads {a['list']}"]
    written = set(w["fields"].values())
    return problems + [f"the authenticator reads {f}, which the workflow doesn't write" for f in a["fields"] if f not in written]


def diff(old: dict, new: dict) -> dict:
    old_q = {x["id"]: x for x in old["questions"] if x["id"] != "NEW"}
    new_q = {x["id"]: x for x in new["questions"] if x["id"] != "NEW"}
    unknown = sorted(set(new_q) - set(old_q))
    if unknown:
        raise InstrumentError(f"{', '.join(unknown)} appear in the new version but not the old one")

    changed = []
    for qid, nq in new_q.items():
        fields = {f: {"old": old_q[qid][f], "new": nq[f]} for f in QUESTION_FIELDS if old_q[qid][f] != nq[f]}
        if fields:
            changed.append({"id": qid, "fields": fields})

    old_b = {b["name"]: b for b in old["blocks"]}
    new_b = {b["name"]: b for b in new["blocks"]}
    common = [name for name in new_b if name in old_b]

    def common_order(blocks: dict, name: str) -> list[str]:
        return [k for p in blocks[name]["pages"] for k in p if k in old_q and k in new_q]

    return {
        "setup_changed": old["setup"] != new["setup"],
        "blocks": {
            "added": [n for n in new_b if n not in old_b],
            "removed": [n for n in old_b if n not in new_b],
            "order_changed": [n for n in old_b if n in new_b] != common,
            "notes_changed": [n for n in common if old_b[n]["notes"] != new_b[n]["notes"]],
            "pages_changed": [n for n in common if old_b[n]["pages"] != new_b[n]["pages"]],
            "reordered": [n for n in common if common_order(old_b, n) != common_order(new_b, n)],
        },
        "questions": {
            "added": [x for x in new["questions"] if x["id"] == "NEW"],
            "removed": [qid for qid in old_q if qid not in new_q],
            "changed": changed,
        },
    }


def assign(md: str, line: int, qid: str) -> str:
    if not re.fullmatch(r"QID\d+", qid):
        raise InstrumentError(f"{qid} is not a QID")
    if any(x["id"] == qid for x in parse(md)["questions"]):
        raise InstrumentError(f"{qid} is already used")
    lines = md.split("\n")
    target = lines[line - 1] if 0 < line <= len(lines) else ""
    if not re.match(r"^#####\s+`+.*\[NEW\]`+\s*$", target):
        raise InstrumentError(f"line {line} is not a NEW question header")
    lines[line - 1] = target.replace("[NEW]", f"[{qid}]")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("parse").add_argument("file", type=Path)
    p_diff = sub.add_parser("diff")
    p_diff.add_argument("old", type=Path)
    p_diff.add_argument("new", type=Path)
    p_assign = sub.add_parser("assign")
    p_assign.add_argument("file", type=Path)
    p_assign.add_argument("line", type=int)
    p_assign.add_argument("qid")
    p_handoff = sub.add_parser("handoff")
    p_handoff.add_argument("sender", type=Path)
    p_handoff.add_argument("receiver", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "parse":
            out = parse(args.file.read_text())
        elif args.command == "handoff":
            out = handoff(parse(args.sender.read_text()), parse(args.receiver.read_text()))
            json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
            print()
            sys.exit(1 if out else 0)
        elif args.command == "diff":
            out = diff(parse(args.old.read_text()), parse(args.new.read_text()))
        else:
            args.file.write_text(assign(args.file.read_text(), args.line, args.qid))
            print(f"{args.file}: line {args.line} → {args.qid}")
            return
    except InstrumentError as e:
        sys.exit(f"error: {e}")
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
