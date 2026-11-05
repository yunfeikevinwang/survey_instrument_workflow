# Survey instrument workflow

How we write, implement, and review survey instruments.

- **Source of truth:** the instrument, written in Markdown in this repo.
- **Images:** a Google Drive folder.
- **Implementation:** AI builds the survey in Qualtrics from the Markdown.
- **Review:** PIs comment on a Google Docs copy and a Qualtrics preview.

## Components
- **Instrument files:** each `instrument_N.md` is a complete copy of the instrument at version N. Once a version is implemented in Qualtrics, it is frozen and never edited again.
- **Images:** all images are in one Google Drive folder. Each `image_of_cat.png` should have a descriptive name, and updated versions should add a number to it `image_of_cat_N.png`, with the old version kept.

## Formatting rules

### The rule
| Format | Meaning |
|---|---|
| ``Plain text`` | Visible to participants|
| `` `code` `` | Not visible to participants |


### Recommendations
In general, use headings,  lists, and other Markdown as you like if the meaning is clear.

**Plain text (visible to participants)**

| What | Recommendation | Example |
|---|---|---|
| Answer options | Bullets | `- Yes` |
| Headings | Markdown heading | `### Welcome!` |
| Page break | Markdown horizontal line |`---`|

**Code (not visible to participants)**

| What | Recommendation | Example |
|---|---|---|
| Internal names | Markdown heading | `` `## Block 1` `` |
| Variable | Bracketed name | `` `[Variable]` `` |
| Logic | Plain text | `` `If true, set [Variable] = 1` `` |
| Piped text | Plain text | ``You selected `[Variable]`.`` |
| Images | File name in inline code | `` `q5a_comparison_chart.png` `` |

Bold or italics inside code shows as literal asterisks, so don't format text in code.

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
