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
| Section headings | Use headers | `### Welcome to the study` |
| Page break | Use horizontal rule | `---` |

## Code rules

| Usage | Rule | Syntax |
|---|---|---|
| Survey title | `#` header, name in code | ``# `Consumer AI Survey` `` |
| Qualtrics block | `##` header, name in code | ``## `Consent` `` |
| Qualtrics question | `#####` header with QID and settings, in code | ``##### `QID12: Multiple choice, select all that apply` `` |
| New question | `#####` header starting with `NEW` | ``##### `NEW: Text entry, numeric 0–168` `` |
| Other internal headings | Any other header level, name in code | ``### `Information arm` `` |
| Piped variable | Bracketed name, no spaces | `` This is piped: `[Variable]` `` |
| Logic | No constraints, use code blocks for longer sections | `` `If true, set [Variable] = 1` `` |
| Images | Use filename | `` `q5a_comparison_chart.png` `` |

## Structure

````
# `Survey title`

```
survey-level logic: embedded data, randomization, survey flow
```

## `Block name`

```
block-level logic (optional)
```

##### `QID1: settings`

question content: text, options, images, logic

---                      ← page break

##### `QID2: settings`

...
````

- **Every Qualtrics question gets a `#####` header**, including text-only and image-only screens (`` `QID5: Text` ``). Everything up to the next header or page break belongs to that question.
- **Logic about a question goes under its header.** A display condition written above a header belongs to the question before it.
- **Answer options are the list at the end of a question.** Other lists are visible text: a list followed by more text, numbered steps just before bulleted options, and any list in a `Text` question. To show a literal number that isn't a list, escape it: `1\. Click the three dots`.
- **A bracketed note with spaces is code, not a piped variable:** `` `[show if they say yes]` ``.
- **One question per condition.** When the survey shows different copies of a question under different conditions (iPhone and Android, control and treatment), each copy is its own question with its own condition.
- **Page timers and metadata questions** (Qualtrics *Timing* and *Meta* types) may be left out. They carry over when a survey is copied.
- **New questions start as `NEW`.** After implementation, `NEW` is replaced by the real QID.
- **QIDs are never edited by hand,** and a QID appears once per file.
- **Visible text and images always sit inside a question.** Only code may appear between a block header and its first question.
- **A changed image gets a new file name,** e.g. `consent_logo_v2.png`. The file name is how a change is detected.
- **Images live in the Google Drive folder `/images_vN`.** It holds every image used by version N.
