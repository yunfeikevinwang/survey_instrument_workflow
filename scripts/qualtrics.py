"""Read-only access to a live Qualtrics survey (this script never writes).

  qualtrics.py dump SURVEY_ID              normalized snapshot of the survey (JSON)
  qualtrics.py compare INSTRUMENT DUMP     mismatches between an instrument and a dump (JSON)

Credentials come from the environment: `source scripts/load_env.sh <instance>` first.
"""

import argparse
import html
import json
import os
import re
import sys
import subprocess
from pathlib import Path

from instrument import parse

RE_TAG = re.compile(r"<[^>]+>")
RE_LINE_BREAK = re.compile(r"<br\s*/?>|</p>|</div>", re.IGNORECASE)
RE_FIELD_PIPE = re.compile(r"\$\{e://Field/([^}]+)\}")
RE_MD_STRONG = re.compile(r"(\*\*|__)(.+?)\1")
RE_MD_EM = re.compile(r"(?<!\w)([*_])(\S(?:.*?\S)?)\1(?!\w)")
RE_MD_HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)
HELPER_TYPES = {"Timing", "Meta"}


def fetch(survey_id: str) -> dict:
    # curl, not urllib: python.org builds on macOS often lack CA certificates
    token, dc = os.environ["QUALTRICS_API_TOKEN"], os.environ["QUALTRICS_DATA_CENTER"]
    raw = subprocess.run(
        ["curl", "-sS", "--fail-with-body", "-H", f"X-API-TOKEN: {token}",
         f"https://{dc}.qualtrics.com/API/v3/survey-definitions/{survey_id}"],
        capture_output=True, check=True,
    ).stdout
    body = json.loads(raw.decode("utf-8"), strict=False)  # question HTML has control chars
    if not str(body["meta"]["httpStatus"]).startswith("200"):
        raise RuntimeError(f"Qualtrics returned {body['meta']}")
    return body["result"]


def clean_html(text: str) -> str:
    text = RE_TAG.sub("", RE_LINE_BREAK.sub("\n", text or ""))
    text = RE_FIELD_PIPE.sub(r"[\1]", html.unescape(text).replace("\xa0", " "))
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def clean_markdown(text: str) -> str:
    text = RE_MD_EM.sub(r"\2", RE_MD_STRONG.sub(r"\2", RE_MD_HEADING.sub("", text)))
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def flow_block_ids(nodes: list) -> list[str]:
    ids = []
    for node in nodes:
        if node.get("Type") in ("Block", "Standard") and node.get("ID"):
            ids.append(node["ID"])
        ids.extend(flow_block_ids(node.get("Flow", [])))
    return ids


def normalize(definition: dict) -> dict:
    blocks_raw = definition["Blocks"]
    flow = definition["SurveyFlow"]
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
                "has_js": bool((q.get("QuestionJS") or "").strip()),
            }
    embedded = [f["Field"] for node in flow.get("Flow", []) if node.get("Type") == "EmbeddedData"
                for f in node.get("EmbeddedData", [])]
    return {"survey_id": definition.get("SurveyID"), "name": definition.get("SurveyName"),
            "blocks": blocks, "questions": questions, "embedded_data": embedded, "flow": flow}


def compare(instrument: dict, dump: dict) -> list[dict]:
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
        if q["block"] != live["block"]:
            report(q["id"], "block", q["block"], live["block"])
        if clean_markdown(q["text"]) != live["text"]:
            report(q["id"], "text", clean_markdown(q["text"]), live["text"])
        choices = [clean_markdown(c["text"]) for c in q["choices"]]
        if choices != live["choices"]:
            report(q["id"], "choices", choices, live["choices"])
    for qid in dump["questions"]:
        if qid not in seen and qid not in helpers:
            report(qid, "missing_in_instrument", None, dump["questions"][qid]["text"])
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dump").add_argument("survey_id")
    p_compare = sub.add_parser("compare")
    p_compare.add_argument("instrument", type=Path)
    p_compare.add_argument("dump", type=Path)
    args = parser.parse_args()

    if args.command == "dump":
        out = normalize(fetch(args.survey_id))
    else:
        out = compare(parse(args.instrument.read_text()), json.loads(args.dump.read_text()))
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
