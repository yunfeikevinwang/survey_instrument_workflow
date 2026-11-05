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

Each Markdown element means something different in plain text and in code.
Code goes *inside* other elements, e.g. a heading or a list item, never the other way round: Markdown inside code doesn't render.
In general, use Markdown as you like if the meaning is clear.

| Element | Markdown syntax | Plain text | Code text |
|---|---|---|---|
| **In general** | | Visible to participants | Not visible to participants |
| Heading | `# H1`<br>`## H2`<br>`### H3` | Heading shown to participants, e.g. `### Welcome!` | Internal name (block, question sub-version), e.g. ``## `Block 1` `` |
| Bold | `**bold text**` | Bold text shown to participants | Not applicable: doesn't render inside code |
| Italic | `*italicized text*` | Italic text shown to participants | Not applicable: doesn't render inside code |
| Blockquote | `> blockquote` | Not used | Not used |
| Ordered list | `1. First item`<br>`2. Second item`<br>`3. Third item` | Answer options, when logic refers to options by number | Not applicable: put code inside the item instead, e.g. ``2. No `→ Skip to Block 4` `` |
| Unordered list | `- First item`<br>`- Second item`<br>`- Third item` | Answer options | Not applicable: put code inside the item instead, e.g. ``- No `→ Skip to Block 4` `` |
| Code | `` `code` `` | Not applicable | Variables: `` `[Variable]` ``<br>Logic: `` `If true, set [Variable] = 1` ``<br>Piped text: ``You selected `[Variable]`.``<br>Images: `` `image_of_cat.png` `` |
| Code block | ` ``` ` on the lines before and after | Not applicable | Logic spanning several lines |
| Horizontal rule | `---` | Page break | Not applicable |
| Link | `[title](https://www.example.com)` | Link shown to participants | Not applicable: shows as a literal URL |
| Image | `![alt text](image.jpg)` | Not used: images live in Google Drive | Not used: write the file name in code instead |

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
