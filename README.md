# Survey instrument workflow

How we write, implement, and review survey instruments.

- **Source of truth:** the instrument, written in Markdown in this repo.
- **Images:** a Google Drive folder.
- **Implementation:** AI builds the survey in Qualtrics from the Markdown.
- **Review:** PIs comment on a Google Docs copy and a Qualtrics preview.

## Components

```
instrument_v1.md      ← frozen
instrument_v2.md      ← frozen
instrument_v3.md      ← current version (the only file anyone edits)
```

- **Instrument files:** each `instrument_vN.md` is a complete copy of the instrument at version N. Once a version is implemented in Qualtrics, it is frozen and never edited again.
- **Images:** all images are in one Google Drive folder, linked at the top of each instrument file. To change an image, replace the file in Drive under the same name. Earlier copies are under Drive's *File information → Manage versions*.

## Formatting rules

### The key rule

> **Anything that will not appear to respondents exactly as written goes in `code`.**

Plain text is exactly what respondents see.
Everything else uses inline code, or a fenced code block for longer text: block names, question labels, logic, piped text, images, and notes.

| What | How | Example |
|---|---|---|
| Survey title, blocks, question sub-versions | Headings `#` / `##` / `###`, with the name in code | ``## `Block 2: AI usage` `` |
| Question label | Code | `` `Q2.` `` |
| Question text | Bold | `**Have you used an AI chatbot in the past 30 days?**` |
| Instructions shown to respondents | Italics | `*(Select all that apply)*` |
| Answer options | Bullets; numbers when logic refers to options by number | `- Yes` / `1. ChatGPT` |
| Short logic | Inline code | `` `→ Skip to Block 4` `` |
| Longer logic | Fenced code block | see [instrument_v1.md](instrument_v1.md) |
| Piped text | Inline code, as Qualtrics writes it | `` `${q://QID3/ChoiceGroup/SelectedChoices}` `` |
| Images | Inline code with the file name in double brackets | `` `[[q5a_comparison_chart.png]]` `` |
| Text entry boxes | Inline code | ``- Other: `text entry box` `` |

The one exception: the Google Drive folder link at the top of each file stays a normal link, so it is clickable.

### Other rules

- **One sentence per line.** Separate paragraphs with a blank line. Lines next to each other still display as one paragraph, and git diffs show changes sentence by sentence.
- **Image file names are descriptive** (`q5a_comparison_chart.png`, not `image3.png`). Use the file name only, with no path or description.
- **Formatting inside code doesn't work.** Bold or italics inside backticks shows as literal asterisks. Logic doesn't need formatting, so this shouldn't come up.

## Iteration loop

1. **Finalize.** The Markdown and images for version N are final: `instrument_vN.md` is committed and the Drive folder is up to date.
2. **Implement.** AI implements the changes in Qualtrics with the `qualtrics-plan` and `qualtrics-implement` skills, comparing `instrument_v(N-1).md` (old) with `instrument_vN.md` (new). `instrument_vN.md` is now frozen.
3. **Share for review.**
   - Upload `instrument_vN.md` to Google Drive and open it with Google Docs.
   - Share it with the PIs as **Commenter**, not Editor.
   - Send the Google Doc link together with the Qualtrics preview link.
4. **Review.** PIs leave comments and suggested edits in the Google Doc, and can click through the live survey in the preview.
5. **Bring feedback back.** Download the reviewed doc with *File → Download → Microsoft Word (.docx)*. AI reads its comments and suggestions and drafts `instrument_v(N+1).md`, flagging anything that needs a decision. Resolve those, then return to step 1.

## Rules for operators

- **Only edit the newest version.** Never edit a frozen file. Step 2 relies on `v(N-1)` matching what is live in Qualtrics.
- **Share the Google Doc as Commenter.** Commenters can still suggest edits, but every change arrives as a comment or a suggestion, so nothing is missed in step 5.
- **Don't edit the Google Doc yourself.** It is a review copy. Make a fresh one each round from the Markdown.
- **When in doubt, use code.** If you're unsure whether respondents will see a piece of text exactly as written, it belongs in code.

## Known limitations

- **Logic isn't blue in Google Docs.** After upload, text in code appears in a monospace font, which still sets it apart from respondent-facing text.
- **Images aren't shown inline** in GitHub or Google Docs. Reviewers see them in the Drive folder or in the Qualtrics preview.
