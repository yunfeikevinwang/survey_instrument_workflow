# Survey instrument workflow
A simple workflow for implementing survey instruments that is AI-friendly.

## Basic Components
1. **Instrument and images:** the instrument is in Markdown on GitHub; images are in a Google Drive folder.
    - Each `instrument_vN.md` is a complete copy of the instrument for version N.
    - Each image has a descriptive name. The Google Drive folder `/images_vN` contains all images needed in version N.
2. **Implementation:** built in Qualtrics from the Markdown using AI.
    - Each implementation on Qualtrics is a separate project for version N.
3. **Review document:** humans comment on a Google Docs copy of the instrument and implementation.
    - Each review is a separate document tab for version N.

## Iteration loop

1. **Create instrument and images.** AI and humans create version N of the instrument and images.
2. **Implement.** AI implements the changes in Qualtrics with skills, comparing old `instrument_v(N-1).md` with new `instrument_vN.md`. For version 1, AI builds the survey from scratch. A human checks everything for correctness, formatting, and maintainable logic. At this point, it is okay to tweak the new instrument to make sure things are fully specified and match.
3. **Review.** Now, `instrument_vN.md`, `/images_vN`, and the implementation are _frozen_. Based on the implementation, PIs leave comments and suggested edits on the instrument uploaded to Google Docs.
4. **Update instrument and images.** Now the review document is _frozen_. Download the comments and suggestions as a Word document. AI and humans read it and draft `instrument_v(N+1).md`.

## Instrument formatting rules
See [instrument_v1.md](instrument_v1.md) for an example.

### Basic rule
| Usage | Rule | Syntax |
|---|---|---|
| Things directly visible to participants | Use plain text | `This is plain text` |
| Things not directly visible to participants | Use code | `` `This is code` `` |

### Plain text rules
| Usage | Rule | Syntax |
|---|---|---|
| Questions | Use bold | `**How are you?**` |
| Answer options | Use bullets | `- Yes` |
| Instructions | Use bold and italics as needed | `Please **read** this _carefully_.` |
| Section headings | Use headers | `### Welcome to the study` |
| Page break | Use horizontal rule | `---` |

### Code rules
| Usage | Rule | Syntax |
|---|---|---|
| Internal headings | Use headers, with only the name in code | ``### `Block 1` `` |
| Question settings | Use code under the question | `` `Multiple choice, select all that apply` `` |
| Piped variable | Use bracketed name | `` This is piped: `[Variable]` `` |
| Logic | No constraints, use code blocks for longer sections | `` `If true, set [Variable] = 1` `` |
| Images | Use filename | `` `q5a_comparison_chart.png` `` |
