---
name: qualtrics-implement
description: Use to build version N of a survey in Qualtrics from instrument_vN.md — copies the version N−1 Qualtrics survey into a new project, applies the changes between instrument_v(N-1).md and instrument_vN.md through the Qualtrics REST API, writes the new QIDs back into instrument_vN.md, and publishes. The only skill that writes to Qualtrics.
---

# Implement an instrument version in Qualtrics

The previous version's survey is copied, and only the Markdown diff is applied to the copy. The source survey is never modified, so it doubles as the backup. Read `${CLAUDE_PLUGIN_ROOT}/format.md` and [gotchas.md](gotchas.md) before writing anything.

All Qualtrics calls go through the REST API with `curl` or Python. Never use a Qualtrics MCP server.

## Inputs (ask for any that are missing)
- `instrument_v(N-1).md` and `instrument_vN.md`.
- The instance: `qualtrics` (Stanford) or `qualtrics-mit` (MIT).
- The source survey: the Qualtrics project for version N−1. If the user names it rather than giving an ID, list the surveys (`GET /API/v3/surveys`, `.result.elements`) and confirm which one.
- **First build:** if there's no previous survey, the user creates an empty survey in Qualtrics, and `instrument_v(N-1).md` is just a title line. Every question is then `NEW`.

Work in `./.qualtrics/vN/`. Append one JSON line per write to `log.jsonl`, with the change, the endpoint, the status, and a note.

## 1. Check the starting point
```bash
source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh <instance>
S=${CLAUDE_PLUGIN_ROOT}/scripts
python3 $S/instrument.py diff instrument_v(N-1).md instrument_vN.md > .qualtrics/vN/diff.json
python3 $S/qualtrics.py dump <SOURCE_ID> > .qualtrics/vN/source.json
python3 $S/qualtrics.py compare instrument_v(N-1).md .qualtrics/vN/source.json
```
- The compare must be empty, because v(N−1) has to describe the source survey. If it isn't, stop and show the mismatches. The fix belongs in the frozen instrument or the survey, and a human decides which.
- If any step errors, stop and show the error.

## 2. Confirm once
Show:
- the source survey (name and ID);
- the new project's name, `<source name minus version> vN`;
- a summary of the diff: questions added, removed, and changed; blocks added, removed, and reordered; setup changes.

Ask the user to confirm. This is the only question before the build.

## 3. Copy and check the copy
- Copy the source survey (see gotchas: *Copying*).
- Dump the copy and compare its `blocks` and `questions` to `source.json`. They must be identical.
- If QIDs or structure differ, stop. Don't build on a copy that doesn't match.

## 4. Apply the diff to the copy
Work through `diff.json` in this order. Implement each change directly from the Markdown of `instrument_vN.md`, and GET after every write to verify it.

1. **Blocks added:** `POST /blocks`, then fix the auto-added flow node.
2. **Questions changed:** GET → merge → PUT, for each changed field.
   - `text`: Markdown → HTML. `**x**` → `<strong>`, `*x*` → `<em>`, line breaks → `<br>`, a visible `###` heading → `<h3>`. A piped `[Field]` → `${e://Field/Field}` for embedded data, or the matching `${q://QIDn/...}` when it refers to an answer.
   - `choices`: edit the existing choices in place (see gotchas: choice IDs).
   - `settings` and `notes`: type, validation, randomization, display logic, and skip logic, as the code describes.
   - `block`: the question moves blocks. This is handled in step 4.
3. **Questions added:**
   - `POST /questions?blockId=…`.
   - Then write the new QID into the instrument:
     ```bash
     python3 $S/instrument.py assign instrument_vN.md <line> <QID>
     ```
   - Assign from the bottom of the file upwards, so earlier line numbers stay valid.
4. **Layout:** for every block in `pages_changed` / `reordered`, and every block that gained or lost questions, PUT the block's final `BlockElements` (questions plus `{"Type": "Page Break"}`) in a single PUT.
5. **Questions removed:** `DELETE /questions/{qid}`.
6. **Blocks removed:** `DELETE /blocks/{bid}`, once they're empty.
7. **Flow:** for `setup_changed`, `notes_changed`, block order, and any logic in the notes, GET `/flow`, edit it, and PUT it. This covers embedded data, branches, randomizers, end-of-survey, and block order.

When a code note is ambiguous, don't guess. Leave that change out, log it as skipped, and list it in the report.

## 5. Verify, then publish
- Run `qualtrics-test` on the copy against `instrument_vN.md`, and fix mismatches that come from this build.
- Then publish: `POST {BASE}/versions` with `{"Description": "Instrument vN", "Published": true}`.

## 6. Report
- **New survey:** its name, ID, and preview link.
- **Applied:** counts by change type.
- **Skipped or failed:** each with the reason.
- **QIDs assigned:** `instrument_vN.md` was edited, and a human commits it.
- **Manual steps:** the API can't upload images, so list each question whose image is new or renamed, with its file from `/images_vN`. Also list anything else that couldn't be done through the API.

## API endpoints
| Operation | Call |
|---|---|
| Full definition | `GET {BASE}` |
| Question | `GET` / `PUT` / `DELETE {BASE}/questions/{qid}`, `POST {BASE}/questions?blockId={bid}` |
| Block | `GET` / `PUT {BASE}/blocks/{bid}`, `POST {BASE}/blocks`, `DELETE {BASE}/blocks/{bid}` |
| Flow | `GET` / `PUT {BASE}/flow` |
| Publish | `POST {BASE}/versions` |
| Copy survey / who am I | `POST /API/v3/surveys` (copy headers), `GET /API/v3/whoami` |
