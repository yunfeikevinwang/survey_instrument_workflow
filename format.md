# Instrument format

The instrument is one Markdown file per version: `instrument_vN.md`.
See [instrument_v1.md](instrument_v1.md) for a complete example.

## The rule

| Usage | Rule | Syntax |
|---|---|---|
| Things directly visible to participants | Use plain text | `This is plain text` |
| Things not directly visible to participants | Use code | `` `This is code` `` |

## Plain text rules

| Usage | Rule | Syntax |
|---|---|---|
| Questions | Use bold | `**How are you?**` |
| Answer options | Use bullets (the list at the end of a question) | `- Yes` |
| Instructions | Use bold and italics as needed | `Please **read** this _carefully_.` |
| Links | Markdown link on the visible words; a bare URL as `<url>` | `[Professor Salz](https://example.edu)`, `<https://chatgpt.com/>` |
| Headings and other styling | Plain line; the style is a code note beside it (`Heading` = `<h2>`, `Subheading` = `<h3>`) | ``**Welcome to the study** `Heading` `` |
| Page break | Use horizontal rule | `---` |

## Code rules

| Usage | Rule | Syntax |
|---|---|---|
| Survey title | The first `##` header, name in code | ``## `Consumer AI Survey` `` |
| Qualtrics block | `##` header, name in code | ``## `Consent` `` |
| Qualtrics question | `#####` header: label, settings, then the QID in brackets, in code; a short display condition ends the settings | ``##### `ChatbotsUsed: Multiple choice, select all that apply. Display if QID11 == Yes. [QID12]` `` |
| New question | `#####` header ending in `[NEW]` | ``##### `WeeklyHours: Text entry, numeric 0–168 [NEW]` `` |
| Page timers | One setup line: `every page`, `every page except in: A; B`, or `none` | `` `Page timers: every page` `` |
| Piped variable | Bracketed name, no spaces | `` This is piped: `[Variable]` `` |
| Logic | Inline code, one note per line, for one or two lines; three or more go in a fenced code block | `` `If true, set [Variable] = 1` `` |
| Numeric answer options | One code line instead of a long list; a descending range counts down | `` `Choices: 1950–2025, one per year` `` |
| Images | File name ending in its display width | `` `q5a_comparison_chart_w700.png` `` |
| Answer box | Code: Qualtrics draws the box from the question type | `` `_______________` `` |

## Structure

````
## `Survey title`

```
survey-wide settings: survey ID, required questions, survey options
Images: Drive Qualtrics/<family>_images, https://drive.google.com/drive/folders/<id>; Qualtrics folder "<Project> <Survey>"; 3px solid border on every image.
All links open in a new tab.
Page timers: every page
```

## `Block name`

`Before this block: flow steps that run first`

`Shown if …`

`After this block: …`

##### `Label1: settings [QID1]`

question content: text, options, images, logic

---                      ← page break

##### `Label2: settings [QID2]`

...
````

- **Only two heading levels:** `##` for the title and the blocks, `#####` for the questions. Plain text is never a heading.
- **Every Qualtrics question gets a `#####` header**, including text-only and image-only screens (`` `Intro: Text [QID5]` ``). Everything up to the next header or page break belongs to that question.
- **The label is the question's Qualtrics data export tag:** no spaces, colons or brackets, unique within the file. A new question gets one in the same style.
- **Bold, italic and links are the only Markdown on plain text.** Any other styling (heading, size, colour, alignment) is a code note on the same line. The setup says how links open, e.g. `All links open in a new tab.`
- **Logic about a question goes under its header.** A display condition written above a header belongs to the question before it.
- **Survey flow lives with the blocks.** The top of the file holds only survey-wide settings. Each block says when it is shown. A flow step between blocks (embedded data, randomizer, web service) goes on the next block as `Before this block: …`; an end of survey goes on the block it ends as `After this block: …`.
- **Keep code short.** Write logic as inline code, one note per line. One or two lines of code stay inline; three or more lines in a row go in a fenced block, e.g. a table or a script's rules. Don't repeat what the header already says.
- **Tables are grid tables at most 80 characters wide.** A table is code, so it goes in a fence. Wrap a long cell onto more lines rather than widening the column; the parser rejects a table row over 80 characters.

    ```
    +-----+----------------------+
    | Arm | Activity             |
    +=====+======================+
    | BT  | Try all four         |
    |     | Offer payment for    |
    |     | blocking PrimaryLLM  |
    +-----+----------------------+
    ```
- **Answer options are the list at the end of a question.** Other lists are visible text: a list followed by more text, numbered steps just before bulleted options, and any list in a `Text` question. To show a literal number that isn't a list, escape it: `1\. Click the three dots`.
- **A line of only `---`, `___` or `***` is always a page break.** So an answer box drawn with underscores must be code, `` `_______________` ``, never bare `___`.
- **A bracketed note with spaces is code, not a piped variable:** `` `[show if they say yes]` ``.
- **One question per condition.** When the survey shows different copies of a question under different conditions (iPhone and Android, control and treatment), each copy is its own question with its own condition.
- **Page timers are one setup line, not questions.** `Page timers: every page` means each page has a Qualtrics timer; list blocks without timers after `except in:`, separated by `;`. Metadata questions (Qualtrics *Meta* type) may be left out. Both carry over when a survey is copied.
- **New questions end in `[NEW]`.** After implementation, `NEW` is replaced by the real QID.
- **QIDs are never edited by hand,** and a QID appears once per file.
- **Visible text and images always sit inside a question.** Only code may appear between a block header and its first question.
- **An image's file name ends in its display width:** `_w<width>`, e.g. `consent_logo_w300.png`. The height is never written; it comes from the file's own pixels, so an image is never stretched, and the width may not exceed the file's pixel width. Pick the width of nearby images of the same kind (phone screenshots next to phone screenshots, desktop screenshots next to desktop screenshots), rounded to 10, 50 or 100; otherwise judge it by eye.
- **A changed image gets a new file name,** e.g. `consent_logo_v2_w300.png`; a new width is a new name too. The file name is how a change is detected.
- **The setup's `Images:` line names where images live and how they look,** in three parts separated by `;`:
    - `Drive <path>, <link>`: the one Google Drive folder that collects every image of a family of surveys and all their versions, e.g. `Qualtrics/main_images`. The path is relative to the shared drive's root. Files there are never overwritten or renamed, because a changed image always gets a new name, so every earlier version still finds the files it used.
    - `Qualtrics folder "<name>"`: the Qualtrics library folder for this survey, shared by all its versions, e.g. `AIMarket Main Survey 1`. A human creates it once; its name must be unique in the library. A registry file next to the instruments, `qualtrics_images.json`, records which files each folder holds and their graphic ids. Write `Qualtrics folder none` for a legacy survey whose images predate this rule.
    - `<N>px solid border on every image`, optionally `except <file>, <file>` for images shown without one, or `no border`.
