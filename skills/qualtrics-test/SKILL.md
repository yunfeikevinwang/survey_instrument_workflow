---
name: qualtrics-test
description: Use to check that a Qualtrics survey matches its instrument_vN.md — after qualtrics-implement builds a version, or to reconcile a legacy instrument (v0) with the survey that is already live. Compares the survey through the API, then walks it in a browser to cover what the API can't show. Never changes the survey; the walks record test responses.
---

# Test a survey against its instrument

Parts 1 and 2 only read, through the REST API. Part 3 walks the survey in a browser to cover everything the API can't verify. Nothing here changes the survey; the walks record test responses, which the report lists for deletion.

## Inputs
- `instrument_vN.md`.
- The instance: `qualtrics` (Stanford) or `qualtrics-mit` (MIT).
- The survey ID.
- For Part 3: how the walks reach the survey (see below), and whether they may pass flow steps with outside effects (web-service calls, end-of-survey redirects), and with which test values.

## 1. Structural check (script, by QID)
```bash
source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh <instance>
S=${CLAUDE_PLUGIN_ROOT}/scripts
mkdir -p .qualtrics
python3 $S/qualtrics.py dump <SURVEY_ID> > .qualtrics/test.json
python3 $S/qualtrics.py compare instrument_vN.md .qualtrics/test.json [--pixels]
```
This reports block order, page breaks, block membership, labels (data export tags), link text and targets, page timers against the `Page timers:` line, visible text, choices, images (count, each one's width against the `_w` in its file name, and its border against the `Images:` line and its exceptions; with `--pixels`, also that no image is stretched or upscaled), `NEW` questions not yet built, and questions missing on either side. Which file a graphic came from can't be checked.

Text is compared after removing HTML and Markdown formatting; bold and italic are compared separately, as the runs of styled text (`bold` and `italic` mismatches: headings count as bold, runs separated only by spaces merge, a line break ends a run). A text mismatch can therefore be a formatting-only difference, e.g. a line break or spacing. Say so when that's all it is.

## 2. Logic check (you)
For each question, choice, and block with code notes, and for the setup block, find what the notes describe in the dump. The dump's `display_logic`, `validation`, and `flow` hold DisplayLogic, skip logic, randomization, embedded data, branches, web-service calls, and end-of-survey. Each question's JavaScript is in `js`; read it, because it often holds logic (fields set in JavaScript, answer checks, hidden buttons). The question type is in the dump's `type`. Web-service headers are redacted in the dump; never copy them anywhere. Classify each note:
- **matches**;
- **mismatch:** say what the survey does instead;
- **can't verify through the API:** e.g. JavaScript behaviour or appearance.

## 3. Preview walk (browser)
Walk the survey to cover every item the API can't verify. Use the Playwright tools (`mcp__plugin_playwright_playwright__*`), or the built-in browser.

**Plan the coverage first.** List every item to cover:
- each Part 2 note classed **can't verify through the API**;
- each display condition and branch whose outcome depends on answers or embedded data at runtime: one walk where it's true, and one where it's false when that path differs;
- each randomizer: every arm observed or forced at least once;
- every page with piped text, every image, and every question with JavaScript.

Then choose the fewest walks that cover the list. Force arms and embedded data where the survey allows it, e.g. through a testing block's arm choice, or URL parameters for fields declared in the flow. Write the plan as a table: walk → path (answers, device or OS, arm) → items covered. Show it before running.

**On every page, check:**
- the page that the instrument says should come next is the one that appears;
- no raw `${…}` and no empty piped value (e.g. `, , and`);
- each image loads (`naturalWidth > 0`) at its `_w` width, with the setup's border;
- no console errors;
- any JavaScript behaviour the notes describe (buttons, answer checks, fields set).

**Safety:**
- Start every walk in a fresh session (`Q_NewSession=1`, or a new browser context). The survey's preview link (`https://<brand>.<dc>.qualtrics.com/jfe/preview/<SURVEY_ID>?Q_CHL=preview&Q_NewSession=1`) may need the user's Qualtrics sign-in in the browser. The public link (`…/jfe/form/<SURVEY_ID>`) records real responses.
- Stop before a flow step with outside effects (a web-service call, an end-of-survey redirect to a recruitment site) unless the user allowed it, with the test values they gave. Those steps run on the server as soon as the flow reaches them, not when a page loads.
- Screenshot only failures, into `.qualtrics/walks/`.
- Never change the survey to make a walk possible. List what couldn't be reached and why.

## Report
- **Coverage table:** item → walk → pass, fail or unreached (with the reason).
- **Test responses created:** how many, and on which link, so they can be deleted.
- A table of mismatches: where (block, QID), the field, what the instrument says, what the survey has, and the suggested fix.
- Logic notes you couldn't verify.
- A count of everything that matched.

Where the fix goes:
- **Testing a build:** the fix goes into the survey. On request, make it through the `qualtrics-implement` procedure on the version's own survey.
- **Reconciling a live survey with its legacy instrument (v0):** the fix goes into the Markdown, because v0 has to describe the survey as it actually is.
