---
name: qualtrics-test
description: Use to check that a Qualtrics survey matches its instrument_vN.md — after qualtrics-implement builds a version, or to reconcile a legacy instrument (v0) with the survey that is already live. Read-only: reports mismatches with suggested fixes and never writes to Qualtrics.
---

# Test a survey against its instrument

This skill only reads, through the REST API. It never writes to Qualtrics.

## Inputs
- `instrument_vN.md`.
- The instance: `qualtrics` (Stanford) or `qualtrics-mit` (MIT).
- The survey ID.

## 1. Structural check (script, by QID)
```bash
source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh <instance>
S=${CLAUDE_PLUGIN_ROOT}/scripts
python3 $S/qualtrics.py dump <SURVEY_ID> > .qualtrics/test.json
python3 $S/qualtrics.py compare instrument_vN.md .qualtrics/test.json
```
This reports block order, page breaks, block membership, visible text, choices, image counts, `NEW` questions not yet built, and questions missing on either side. Image file names can't be checked, only how many images each question has.

Text is compared after removing HTML and Markdown formatting. A text mismatch can therefore be a formatting-only difference, e.g. a line break or spacing. Say so when that's all it is.

## 2. Logic check (you)
For each question, choice, and block with code notes, and for the setup block, find what the notes describe in the dump. The dump's `display_logic`, `validation`, and `flow` hold DisplayLogic, skip logic, randomization, embedded data, branches, web-service calls, and end-of-survey. Each question's JavaScript is in `js`; read it, because it often holds logic (fields set in JavaScript, answer checks, hidden buttons). The question type is in the dump's `type`. Web-service headers are redacted in the dump; never copy them anywhere. Classify each note:
- **matches**;
- **mismatch:** say what the survey does instead;
- **can't verify through the API:** e.g. JavaScript behaviour or appearance.

## Report
- A table of mismatches: where (block, QID), the field, what the instrument says, what the survey has, and the suggested fix.
- Logic notes you couldn't verify.
- A count of everything that matched.

Where the fix goes:
- **Testing a build:** the fix goes into the survey. On request, make it through the `qualtrics-implement` procedure on the version's own survey.
- **Reconciling a live survey with its legacy instrument (v0):** the fix goes into the Markdown, because v0 has to describe the survey as it actually is.
