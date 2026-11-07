# Qualtrics REST API gotchas

Only behaviour seen on the REST API (`/API/v3`) is listed here.
`BASE = https://$QUALTRICS_DATA_CENTER.qualtrics.com/API/v3/survey-definitions/<SURVEY_ID>`, with every call sending `X-API-TOKEN: $QUALTRICS_API_TOKEN`.

## Responses
- Call the API with `curl` (from Python, through `subprocess`). Python's `urllib` fails with `CERTIFICATE_VERIFY_FAILED` on python.org builds for macOS, which lack CA certificates.
- Parse with `json.loads(raw.decode("utf-8"), strict=False)`. Question HTML contains control characters that strict parsing rejects.
- A single item is in `.result`, and a list is in `.result.elements`.
- Check `meta.httpStatus`. The `PUT /flow` and `PUT /options` responses have no `result`, so GET afterwards to verify.

## A PUT replaces the whole resource
- **Question:** `PUT {BASE}/questions/{qid}` replaces the question with exactly the body sent. Any writable field left out is cleared, including `DataExportTag`, `DisplayLogic`, `Configuration`, `ChoiceOrder`, and `Randomization` (re-verified 2026-11-05: a text-only PUT also cleared `Validation`).
  - So always GET the question, change only the target field, and PUT a body built from this whitelist:
    `QuestionText, QuestionType, Selector, SubSelector, Configuration, QuestionDescription, Choices, ChoiceOrder, Validation, Language, DataExportTag, DisplayLogic, ChoiceDataExportTags, QuestionJS, Answers, AnswerOrder, DefaultChoices, RecodeValues, VariableNaming, SubProperties, DynamicChoices, DynamicChoicesData, Randomization`
    (drop `None` values).
  - After the PUT, GET again and compare every field against the pre-PUT copy.
- **Block:** `PUT {BASE}/blocks/{bid}` without `BlockElements` empties the block. GET, change, PUT the whole block. If a block is both renamed and reordered, send the final `BlockElements` in a single PUT.
- To remove DisplayLogic, leave `DisplayLogic` out of the PUT body. Sending `"DisplayLogic": null` is rejected with `ESDEF10` ("Invalid type. Expected: object, given: null"; seen 2026-11-06).
- **Moving a question between blocks:** a PUT of the target block that lists the question does not take it out of its old block, so it sits in both. PUT the old block without it as well (seen 2026-11-06).
- `DELETE {BASE}/questions/{qid}` also removes the question from its block's `BlockElements`.

## Creating
- **`POST {BASE}/blocks` appends a flow node for the new block at the end of the survey flow.** After creating blocks, GET `/flow`, remove the auto-added trailing node, and place the block where it belongs. Otherwise the block is shown twice.
- `POST {BASE}/questions?blockId={bid}` takes the full question, including `DataExportTag` and `DisplayLogic`. The response carries the new QID.
- **Question types:**
  - multiple choice: `QuestionType: "MC"` with `Selector` `SAVR` (single answer), `MAVR` (multiple answer), or `DL` (dropdown);
  - text entry: `TE` / `SL`;
  - text or graphic: `DB` / `TB`;
  - slider: `Slider` / `HSLIDER`.
  - `MC.MAVR` is not a valid type.
- **Choice IDs change if a question is deleted and re-created,** and response data tied to the old IDs no longer lines up. Edit in place instead:
  - change `Display` on existing choices;
  - add new choice IDs;
  - drop removed ones from both `Choices` and `ChoiceOrder`.

## DisplayLogic and flow
- DisplayLogic shape:
  ```json
  {"0": {"0": {"LogicType": "EmbeddedField", "LeftOperand": "treatment_arm", "Operator": "EqualTo",
               "RightOperand": "info", "Type": "Expression",
               "Description": "<span class=\"ConjDesc\">If</span> treatment_arm Is Equal to info"},
         "Type": "If"},
   "Type": "BooleanExpression", "inPage": false}
  ```
- OR conditions use `"Conjuction": "Or"`, which is Qualtrics' own misspelling. Spelling it correctly fails silently.
- Branches are if-only, with no else. Write a second branch for the other path.
- `BlockRandomizer` takes only `Type`, `FlowID`, `SubSet`, `EvenPresentation`, `Flow`. Adding a `Randomizer` property is rejected.
- Declare every embedded-data field in the `EmbeddedData` node at the top of the flow. A condition on an undeclared field quietly evaluates false.
- Embedded data set by question JavaScript is available from the next page on.

## Copying and publishing
- Copy a survey with `POST /API/v3/surveys`, sending:
  - headers `X-COPY-SOURCE: <SV_id>` and `X-COPY-DESTINATION-OWNER: <userId>` (the user ID comes from `GET /API/v3/whoami`, at `.result.userId`);
  - body `{"projectName": "<name>"}`.
  - The new survey's ID is in `.result.id`.
  - QIDs and block IDs are kept (verified 2026-11-05).
- **The copy must go to the account's home data center.** Through a proxied data center, the copy headers are dropped and the call fails with `SR_1` ("both X-COPY-SOURCE and X-COPY-DESTINATION-OWNER headers are required"). Any response's `meta.notice` names the home host ("use this host instead: pdx1.qualtrics.com"). For Stanford that is `pdx1`, while `load_env.sh` gives `iad1`. For MIT, `load_env.sh` already gives the home host, `co1`.
- **Writes land in the draft. Respondent and preview links serve the last published version.** Publish with `POST {BASE}/versions` and body `{"Description": "...", "Published": true}`.
- `PUT {BASE}/options` merges, so a key you leave out stays unchanged.
