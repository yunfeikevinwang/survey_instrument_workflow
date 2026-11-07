"""Read-only access to a live Qualtrics survey (this script never writes).

  qualtrics.py dump SURVEY_ID              normalized snapshot of the survey (JSON)
  qualtrics.py compare INSTRUMENT DUMP     mismatches between an instrument and a dump (JSON)

Credentials come from the environment: `source scripts/load_env.sh <instance>` first.
"""

import argparse
import html
import json
import re
import sys
import subprocess
from pathlib import Path

from instrument import image_width, parse

RE_TAG = re.compile(r"<[^>]+>")
RE_LINE_BREAK = re.compile(r"<br\s*/?>|</p>|</div>", re.IGNORECASE)
RE_FIELD_PIPE = re.compile(r"\$\{e://Field/([^}]+)\}")
RE_MD_STRONG = re.compile(r"(\*\*|__)(.+?)\1")
RE_MD_EM = re.compile(r"(?<!\w)([*_])(\S(?:.*?\S)?)\1(?!\w)")
RE_MD_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!])")
RE_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
RE_IMG_ID = re.compile(r"IM=(IM_\w+)")
RE_STYLE_PX = r"(?<![-\w]){}\s*:\s*(\d+)px"
RE_ATTR = r'\b{}="(\d+)"'
RE_ANCHOR = re.compile(r'<a\b[^>]*?\bhref="([^"]*)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)|<(https?://[^>\s]+)>")
HELPER_TYPES = {"Timing", "Meta"}


def fetch(survey_id: str) -> dict:
    from qualtrics_api import call
    return call("GET", f"/survey-definitions/{survey_id}")


def clean_html(text) -> str:
    text = "" if text is None else str(text)  # choice labels can be numbers, e.g. years
    text = RE_TAG.sub("", RE_LINE_BREAK.sub("\n", text))
    text = RE_FIELD_PIPE.sub(r"[\1]", html.unescape(text).replace("\xa0", " "))
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def image_tags(html_text: str) -> list[dict]:
    """Each <img>: graphic id, displayed size (style wins over attributes) and solid-border width."""
    out = []
    for tag in RE_IMG_TAG.findall(html_text or ""):
        def size(name):
            m = re.search(RE_STYLE_PX.format(name), tag) or re.search(RE_ATTR.format(name), tag)
            return int(m.group(1)) if m else None
        border = re.search(r"border-width\s*:\s*(\d+)px", tag)
        solid = re.search(r"border-style\s*:\s*solid", tag)
        im = RE_IMG_ID.search(tag)
        out.append({"im": im.group(1) if im else None, "width": size("width"), "height": size("height"),
                    "border_px": int(border.group(1)) if border and solid else 0})
    return out


def html_links(fragments: list) -> list[list[str]]:
    return [[clean_html(label), html.unescape(href)]
            for fragment in fragments for href, label in RE_ANCHOR.findall(str(fragment or ""))]


def markdown_links(fragments: list[str]) -> list[list[str]]:
    """`[text](url)` and `<url>` links, in order."""
    return [[clean_markdown(m[1]), m[2]] if m[1] else [m[3], m[3]]
            for fragment in fragments for m in RE_MD_LINK.finditer(fragment)]


def clean_markdown(text: str) -> str:
    text = RE_MD_LINK.sub(lambda m: m[1] or m[3], text)
    text = RE_MD_EM.sub(r"\2", RE_MD_STRONG.sub(r"\2", text))
    text = RE_MD_ESCAPE.sub(r"\1", text)
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def flow_block_ids(nodes: list) -> list[str]:
    ids = []
    for node in nodes:
        if node.get("Type") in ("Block", "Standard") and node.get("ID"):
            ids.append(node["ID"])
        ids.extend(flow_block_ids(node.get("Flow", [])))
    return ids


def redact_web_service_headers(node):
    """Web-service headers can hold live credentials; never write them to a dump."""
    if isinstance(node, dict):
        out = {k: redact_web_service_headers(v) for k, v in node.items()}
        if node.get("Type") == "WebService" and isinstance(node.get("Headers"), list):
            out["Headers"] = [{**h, "value": "[redacted]"} for h in node["Headers"]]
        return out
    if isinstance(node, list):
        return [redact_web_service_headers(x) for x in node]
    return node


def normalize(definition: dict) -> dict:
    blocks_raw = definition["Blocks"]
    flow = redact_web_service_headers(definition["SurveyFlow"])
    blocks, questions = [], {}
    for block_id in dict.fromkeys(flow_block_ids(flow.get("Flow", []))):
        block = blocks_raw[block_id]
        if block.get("Type") == "Trash":
            continue
        pages = [[]]
        for element in block.get("BlockElements", []):
            if element["Type"] == "Question":
                pages[-1].append(element["QuestionID"])
            elif element["Type"] in ("Page Break", "PageBreak"):
                pages.append([])
        blocks.append({"id": block_id, "name": block["Description"], "pages": [p for p in pages if p]})
        for qid in (q for p in pages for q in p):
            q = definition["Questions"][qid]
            choice_order = q.get("ChoiceOrder") or list(q.get("Choices") or {})
            questions[qid] = {
                "block": block["Description"],
                "type": f"{q['QuestionType']}/{q.get('Selector')}",
                "export_tag": q.get("DataExportTag"),
                "text": clean_html(q.get("QuestionText", "")),
                "choices": [clean_html(q["Choices"][str(c)]["Display"]) for c in choice_order],
                "answers": [clean_html(a["Display"]) for a in (q.get("Answers") or {}).values()],
                "display_logic": q.get("DisplayLogic"),
                "validation": q.get("Validation"),
                "images": image_tags(q.get("QuestionText") or "")
                          + [t for c in (q.get("Choices") or {}).values()
                             for t in image_tags(str(c.get("Display") or ""))],
                "js": (q.get("QuestionJS") or "").strip() or None,
                "links": html_links([q.get("QuestionText")]
                                    + [c.get("Display") for c in (q.get("Choices") or {}).values()]),
            }
    embedded = [f["Field"] for node in flow.get("Flow", []) if node.get("Type") == "EmbeddedData"
                for f in node.get("EmbeddedData", [])]
    return {"survey_id": definition.get("SurveyID"), "name": definition.get("SurveyName"),
            "blocks": blocks, "questions": questions, "embedded_data": embedded, "flow": flow}


def compare(instrument: dict, dump: dict, pixels: dict | None = None) -> list[dict]:
    """`pixels` maps graphic id -> (width, height) of the image file, to check stretching and upscaling."""
    mismatches = []

    def report(qid, field, expected, found):
        mismatches.append({"qid": qid, "field": field, "instrument": expected, "survey": found})

    # Page timers and metadata questions may be left out of the instrument
    listed = {q["id"] for q in instrument["questions"]}
    helpers = {qid for qid, q in dump["questions"].items()
               if q["type"].split("/")[0] in HELPER_TYPES and qid not in listed}

    def visible_pages(block: dict) -> list[list[str]]:
        pages = ([qid for qid in page if qid not in helpers] for page in block["pages"])
        return [page for page in pages if page]

    survey_blocks = {b["name"]: b for b in dump["blocks"]}
    instrument_order = [b["name"] for b in instrument["blocks"]]
    if instrument_order != [b["name"] for b in dump["blocks"]]:
        report("survey", "block_order", instrument_order, [b["name"] for b in dump["blocks"]])
    for block in instrument["blocks"]:
        survey_block = survey_blocks.get(block["name"])
        found = visible_pages(survey_block) if survey_block else None
        if block["pages"] != found:
            report(block["name"], "pages", block["pages"], found)

    timers = instrument["page_timers"]
    if timers == "undeclared":
        report("survey", "page_timers", "undeclared", None)
    else:
        for block in dump["blocks"]:
            found = [any(dump["questions"][qid]["type"].startswith("Timing/") for qid in page)
                     for page in block["pages"]]
            timed = timers is not None and block["name"] not in timers["except"]
            if found != [timed] * len(found):
                report(block["name"], "page_timers", [timed] * len(found), found)

    seen = set()
    for q in instrument["questions"]:
        if q["id"] == "NEW":
            report(q["key"], "not_implemented", q["settings"], None)
            continue
        seen.add(q["id"])
        live = dump["questions"].get(q["id"])
        if live is None:
            report(q["id"], "missing_in_survey", q["settings"], None)
            continue
        if q["label"] != live["export_tag"]:
            report(q["id"], "label", q["label"], live["export_tag"])
        if q["block"] != live["block"]:
            report(q["id"], "block", q["block"], live["block"])
        if clean_markdown(q["text"]) != live["text"]:
            report(q["id"], "text", clean_markdown(q["text"]), live["text"])
        choices = [clean_markdown(c["text"]) for c in q["choices"]]
        if choices != live["choices"]:
            report(q["id"], "choices", choices, live["choices"])
        links = markdown_links([q["text"]] + [c["text"] for c in q["choices"]])
        if links != live["links"]:
            report(q["id"], "links", links, live["links"])
        if len(q["images"]) != len(live["images"]):
            report(q["id"], "images", q["images"], len(live["images"]))
        else:
            border = instrument["images"]["border"] if instrument["images"] else None
            for name, tag in zip(q["images"], live["images"]):
                want_border = border["px"] if border and name not in border["except"] else 0
                if image_width(name) != tag["width"]:
                    report(q["id"], "image_width", name, tag["width"])
                if want_border != tag["border_px"]:
                    report(q["id"], "image_border", f"{name}: {want_border}px", f"{tag['border_px']}px")
                if pixels and tag["im"] in pixels:
                    pw, ph = pixels[tag["im"]]
                    if tag["width"] > pw:
                        report(q["id"], "image_upscaled", f"{name}: file is {pw}px wide", tag["width"])
                    elif tag["height"] is None or abs(tag["height"] - tag["width"] * ph / pw) > 2:  # Qualtrics rounds heights loosely
                        report(q["id"], "image_stretched", f"{name}: height {round(tag['width'] * ph / pw)}",
                               tag["height"])
    for qid in dump["questions"]:
        if qid not in seen and qid not in helpers:
            report(qid, "missing_in_instrument", None, dump["questions"][qid]["text"])
    return mismatches


def fetch_pixels(dump: dict) -> dict:
    from images import image_size
    from qualtrics_api import graphic_base
    base = graphic_base()
    ids = {t["im"] for q in dump["questions"].values() for t in q["images"] if t["im"]}
    return {im: image_size(subprocess.run(["curl", "-sS", "--fail", base + im], capture_output=True, check=True).stdout)
            for im in sorted(ids)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dump").add_argument("survey_id")
    p_compare = sub.add_parser("compare")
    p_compare.add_argument("instrument", type=Path)
    p_compare.add_argument("dump", type=Path)
    p_compare.add_argument("--pixels", action="store_true",
                           help="download each graphic and check it is neither stretched nor upscaled")
    args = parser.parse_args()

    if args.command == "dump":
        out = normalize(fetch(args.survey_id))
    else:
        dump = json.loads(args.dump.read_text())
        pixels = fetch_pixels(dump) if args.pixels else None
        out = compare(parse(args.instrument.read_text()), dump, pixels)
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
