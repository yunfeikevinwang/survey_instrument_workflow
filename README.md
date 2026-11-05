# Survey instrument workflow

A system for writing, reviewing, and implementing survey instruments where:

- the instrument lives in **Markdown on GitHub**, easy for AI tools to read and edit;
- people review it with **line comments and suggested changes in pull requests**;
- **images live in Google Drive**, not in the repo;
- each reviewed version is a **frozen file**, so the Qualtrics pipeline always has an old and a new version to compare.

Google Docs is not part of the workflow.

## Repository layout

```
instrument_v1.md      ← frozen (reviewed and merged)
instrument_v2.md      ← frozen
instrument_v3.md      ← current round (the only file anyone edits)
```

Each file is a complete, self-contained copy of the instrument at that version.

## Markdown conventions

| What | How | Example |
|---|---|---|
| Survey title | `#` | `# Consumer AI Survey — Instrument v2` |
| Blocks | `##` | `## Block 2: AI usage` |
| Sub-versions of a question (e.g. treatment arms) | `###` | `### Q5a (information arm)` |
| Question text | Bold | `**Q2. Have you used an AI chatbot?**` |
| Instructions to respondents | Italics | `*(Select all that apply)*` |
| Answer options | Bullets; numbers when logic refers to options by number | `- Yes` / `1. ChatGPT` |
| Short logic | Inline code | `` `→ Skip to Block 4` `` |
| Longer logic | Fenced code block | see [instrument_v1.md](instrument_v1.md) |
| Images | File name in double brackets | `[[q5a_comparison_chart.png]]` |
| Piped text | Plain text, as Qualtrics writes it | `${q://QID3/ChoiceGroup/SelectedChoices}` |

**Rule of thumb:** plain text is what respondents see, `code` is for the programmer, and `[[...]]` points to an image.

### One sentence per line

Write each sentence on its own line, and separate paragraphs with a blank line.
Lines next to each other still display as one paragraph, but GitHub comments and suggestions apply to whole lines.
With one sentence per line, reviewers can target a single sentence instead of a whole paragraph.

## Images

- All images are in one Google Drive folder, linked once at the top of each instrument file.
- In the Markdown, an image is just its file name: `[[q5a_comparison_chart.png]]`. Use descriptive file names; there are no descriptions or paths.
- **To change an image, replace the file in Drive under the same name.** Older instrument versions then point to the current image. Earlier copies of a file are under Drive's *File information → Manage versions*.
- GitHub cannot show the images inline, so reviewers open the Drive folder to see them.

## Review rounds

Each round adds a new version file, so the PR shows the entire instrument as new and **every line can take comments**, not just the lines that changed.

1. **Start the round.** On a branch named `round-N`, copy the newest version to `instrument_vN.md`, update the title line, and make the planned edits.
2. **Open a PR** from `round-N` into `main`, titled *Instrument review: round N*. In the description, write a **changelog** of what changed since `v(N-1)`. The PR can't show this, because the whole file looks new.
3. **Review.** Reviewers open *Files changed* and click a line number (or drag over several) to:
   - leave a comment, or
   - suggest an edit with the ± *suggestion* button. The author accepts it with *Commit suggestion*, which commits straight to `round-N`.

   Comments that don't belong to a line go in the PR's *Conversation* tab.
4. **Address feedback.** Make edits on `round-N`, push, and resolve each thread.
5. **Close the round.** Merge the PR. `instrument_vN.md` is now frozen.
6. **Implement in Qualtrics.** Run the `qualtrics-plan` skill with `instrument_v(N-1).md` as the old instrument and `instrument_vN.md` as the new one, then `qualtrics-implement`.

To check just whether feedback was addressed, without a full review, use a normal PR with small edits to the current `vN` before it is merged.

## Rules for operators

- **Only edit the newest version.** Never edit a frozen file. The Qualtrics comparison relies on `v(N-1)` matching what is live.
- **One round, one version, one PR.** Don't start `v(N+1)` while round N is open.
- **Keep logic in code formatting.** Anything a respondent should not see must be in `code`. Otherwise it may end up in the question text.
- **Write a changelog in every round's PR description.** It's the only way reviewers can see what changed.

## Known quirks

- **Large files collapse.** For a long instrument, GitHub may show *Large diffs are not rendered by default*. Click *Load diff* once, and commenting works normally. If this gets annoying, split the instrument into one file per block.
- **Outdated comments.** Comments on lines that change later are marked *Outdated*. They stay visible in the *Conversation* tab.

## One-time move from an existing Google Doc

1. In Google Docs, choose *File → Download → Microsoft Word (.docx)*.
2. Convert it to Markdown with pandoc (`brew install pandoc`), using a small pre-pass that wraps blue (logic) text in backticks.
3. Move the images extracted from the `.docx` to the Drive folder, give them descriptive names, and replace each image with a `[[file_name.png]]` marker.
4. Split the text to one sentence per line, check the result against the original doc, and commit it as `instrument_v1.md`.
