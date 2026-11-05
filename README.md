# Survey instrument workflow
A simple workflow for implementing survey instruments that is AI-friendly.

## Basic Components
1. **Instrument + Images:** former is written in Markdown on Github, latter is a Google Drive folder.
    - Each `instrument_vN.md` is a complete copy of the instrument for version N.
    - Each image should have a descriptive name, and are in Google Drive folder `/images_vN` containing all images needed in version N.
2. **Implementation:** built in Qualtrics from the Markdown using AI.
    - Each implementation on Qualtrics is a separate project for version N.
3. **Review Document** humans comment on a Google Docs copy of the instrument and implementation.
    - Each review is a separate document tab for version N.

## Iteration loop

1. **Create Instrument and Images.** AI+predocs create version N of the instrument and images.
2. **Implement.** AI implements the changes in Qualtrics with skills, comparing old `instrument_v(N-1).md` with new `instrument_vN.md`. Predocs checks everything for correctness, formatting, and maintainable logic. At this point, it is okay to tweak the new instrument to make sure things are fully specified and match.
3. **Review.** Now, `instrument_vN.md`, `/images_vN`, and implementation are _frozen_. Based on the implementation, PIs leave comments and suggested edits to the instrument uploaded to Google Docs.
4. **Update Instrument and Images.** Now the review document are _frozen_. Download comments and suggestions as word document. AI+predoc reads it and drafts `instrument_v(N+1).md`.


## Instrument Formatting rules
### Basic rule
| Usage | Rule | Syntax |
|---|---|---|
| Things directly visible to participants | Use plain text | `This is plain text` |
| Things not directly visible to participants | Use code | `` `This is code` `` |  |

### Plain text rules 
| Usage | Rule | Syntax |
|---|---|---|
| Questions | Use bold | `**How are you?**` |
| Answer options | Use bullets | `- Yes` |
| Instructions | Use bold and italics as needed | `Please **read** this _carefully_.` |
| Section headings | Use headers| `### Welcome to the study` |
| Page break | Use horizontal rule | `---` |
| Line break | Leave a blank line; adjacent lines join into one paragraph | `First line.`<br><br>`Second line.` |

### Code rules
| What | Recommendation | Syntax |
|---|---|---|
| Internal headings | Use headers, with only the name in code | ``### `Block 1` `` |
| Question types and settings | Use code next to the question | `` `Multiple choice, select all that apply` `` |
| Variable definitions | List every variable with a description in a code block at the top of the instrument, mirroring the embedded data at the top of the Qualtrics survey flow | `` `[Variable]: description` `` |
| Piped Variable | Use bracketed name | `` `[Variable]` `` |
| Logic | No constraints, use code blocks for longer sections | `` `If true, set [Variable] = 1` `` |
| Images | Use filename | `` `q5a_comparison_chart.png` `` |
