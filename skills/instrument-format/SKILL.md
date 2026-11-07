---
name: instrument-format
description: Use whenever writing, editing, or reviewing a survey instrument Markdown file (instrument_vN.md) — drafting questions, changing wording or logic, adding blocks or images, or checking an instrument for format errors. Defines what is visible to participants (plain text) versus not (code), and how blocks, questions, and QIDs are written.
---

# Instrument format

Read `${CLAUDE_PLUGIN_ROOT}/format.md` before touching an instrument. It is the only copy of the rules.

The essentials:
- Plain text is visible to participants. Anything else (block names, question settings, logic, piped variables, image file names) is in `code`.
- The first `` ## `Name` `` is the survey title; every later `##` is a Qualtrics block. ``##### `Label: settings [QID12]` `` starts a Qualtrics question, where the label is its data export tag. A new question ends in `[NEW]`. No other heading levels.
- Plain text is never a heading. Bold, italic and links (`[words](url)`, `<url>`) stay Markdown; any other style is a code note: ``**Welcome** `Heading` ``.
- Page timers are one setup line (`Page timers: every page`), not questions.
- Answer options are the list at the end of a question; any other list is visible text.
- A question's logic goes under its own header, never above it; a short display condition goes in the header itself.
- Survey flow is written block by block, not in one block at the top. Code of three or more lines in a row goes in a fence; one or two lines stay inline.

## Rules when editing
- **Edit only the newest version.** Older `instrument_vN.md` files are frozen: they describe surveys that are already built.
- **Never invent or edit a QID.** Add new questions as `NEW`. `qualtrics-implement` replaces `NEW` with the real QID.
- **A changed image gets a new file name,** e.g. `logo.png` → `logo_v2.png`. The file name is how the change is detected. Images live in the Drive folder `/images_vN`.
- **Starting a new version:** copy `instrument_v(N-1).md` to `instrument_vN.md` and edit the copy.

## Check the file
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instrument.py parse instrument_vN.md > /dev/null
```
This fails loudly on format errors and names the line: visible text outside a question, a heading on visible text or at another level, a malformed question header, a duplicate QID, label or block, a malformed `Page timers:` line, or an unclosed code block.

To see what changed between versions:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/instrument.py diff instrument_v(N-1).md instrument_vN.md
```
