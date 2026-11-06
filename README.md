# Survey instrument workflow
A simple, AI-friendly workflow for implementing survey instruments. This repo is also a Claude Code plugin with the skills that run it.

## Basic components
1. **Instrument and images:** the instrument is in Markdown on GitHub; images are in a Google Drive folder.
    - Each `instrument_vN.md` is a complete copy of the instrument for version N.
    - Each image has a descriptive name. The Google Drive folder `/images_vN` contains all images needed in version N.
2. **Implementation:** built in Qualtrics from the Markdown using AI.
    - Each implementation on Qualtrics is a separate project for version N, copied from version N−1.
3. **Review document:** humans comment on a Google Docs copy of the instrument and implementation.
    - Each review is a separate document tab for version N.

## Iteration loop

1. **Create instrument and images.** AI and humans create version N of the instrument and images. *(skill: `instrument-format` and `convert-legacy-instrument`)*
2. **Implement.** AI copies the version N−1 Qualtrics project and applies the changes between `instrument_v(N-1).md` and `instrument_vN.md`. New questions get their QIDs written into `instrument_vN.md`. A human checks everything for correctness, formatting, and maintainable logic. At this point, it is okay to tweak the new instrument to make sure things are fully specified and match. *(skills: `qualtrics-implement`, `qualtrics-test`)*
3. **Review.** Now, `instrument_vN.md`, `/images_vN`, and the implementation are _frozen_. Based on the implementation, PIs leave comments and suggested edits on the instrument uploaded to Google Docs.
4. **Update instrument and images.** Now the review document is _frozen_. Download the comments and suggestions as a Word document. AI and humans read it and draft `instrument_v(N+1).md`. *(skill: `ingest-review-feedback`)*

**Getting started:**
- **From an existing Google Doc:** use `convert-legacy-instrument`. If that survey is already live, the converted file becomes `instrument_v0.md` and must match the live survey. `qualtrics-test` lists any mismatches.
- **From scratch:** create an empty Qualtrics survey and an `instrument_v0.md` with just a title line.

## Instrument formatting rules
See [format.md](format.md), with [instrument_v1.md](instrument_v1.md) as an example. In short:
- plain text is visible to participants, and `code` is not;
- the first `` ## `Name` `` is the title, and every later `##` is a Qualtrics block;
- ``##### `Label: settings [QID12]` `` starts a question, and new questions end in `[NEW]`.

## Skills
| Skill | Does |
|---|---|
| `instrument-format` | Rules for writing and editing an instrument; checks the file |
| `convert-legacy-instrument` | Google Docs `.docx` → `instrument_vN.md` + `images_vN/` |
| `qualtrics-implement` | Copies the v(N−1) survey, applies the diff, writes back QIDs, publishes |
| `qualtrics-test` | Compares a live survey with its instrument (read-only) |
| `ingest-review-feedback` | Reviewed `.docx` → draft `instrument_v(N+1).md` + decisions |

## Setup

### 1. Install the plugin
```bash
claude plugin marketplace add ~/Documents/Github/survey_instrument_workflow
```
```bash
claude plugin install survey-instrument-workflow@survey-tools
```
The plugin loads from this folder in place, so after pulling changes, run `/reload-plugins` or start a new session.

### 2. Qualtrics credentials (only needed for the qualtrics skills)
Create `~/.claude/secrets/qualtrics_tokens.env`. Never commit it. Add one block per Qualtrics account you use:
```bash
QUALTRICS_STANFORD_TOKEN=...   # instance "qualtrics"
QUALTRICS_STANFORD_DC=iad1
QUALTRICS_STANFORD_BRAND=stanforduniversity

QUALTRICS_MIT_TOKEN=...        # instance "qualtrics-mit"
QUALTRICS_MIT_DC=co1
QUALTRICS_MIT_BRAND=mit
```
- **Token:** Qualtrics → Account Settings → Qualtrics IDs → API.
- **Data center:** the label before `.qualtrics.com` in your account's address, e.g. `mit.co1.qualtrics.com` → `co1`.

Then lock the file down and check the token. A `userId` in the response means it works; `401` means a bad token, and a connection error means a wrong data center.
```bash
chmod 600 ~/.claude/secrets/qualtrics_tokens.env
```
```bash
source scripts/load_env.sh qualtrics && curl -s -H "X-API-TOKEN: $QUALTRICS_API_TOKEN" "https://$QUALTRICS_DATA_CENTER.qualtrics.com/API/v3/whoami"
```

## Development
The scripts in `scripts/` use only the Python standard library. Tests:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pytest
```
