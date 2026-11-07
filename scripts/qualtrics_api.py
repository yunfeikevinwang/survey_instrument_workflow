"""Writes to Qualtrics through the REST API (curl underneath: python.org builds on macOS lack CA certificates).

Credentials come from the environment: `source scripts/load_env.sh <instance>` first.
Every write is appended to a JSON-lines log when `log` is given.
"""

import json
import os
import subprocess

QUESTION_FIELDS = ["QuestionText", "QuestionType", "Selector", "SubSelector", "Configuration",
                   "QuestionDescription", "Choices", "ChoiceOrder", "Validation", "Language",
                   "DataExportTag", "DisplayLogic", "ChoiceDataExportTags", "QuestionJS", "Answers",
                   "AnswerOrder", "DefaultChoices", "RecodeValues", "VariableNaming", "SubProperties",
                   "DynamicChoices", "DynamicChoicesData", "Randomization"]


def api_root() -> str:
    return f"https://{os.environ['QUALTRICS_DATA_CENTER']}.qualtrics.com/API/v3"


def graphic_base() -> str:
    return f"https://{os.environ['QUALTRICS_BRAND']}.{os.environ['QUALTRICS_DATA_CENTER']}.qualtrics.com/CP/Graphic.php?IM="


def call(method: str, path: str, body=None, form: dict | None = None, log: str | None = None, note: str = ""):
    url = path if path.startswith("http") else api_root() + path
    cmd = ["curl", "-sS", "-X", method, url, "-H", f"X-API-TOKEN: {os.environ['QUALTRICS_API_TOKEN']}"]
    if form:
        for key, value in form.items():
            cmd += ["-F", f"{key}={value}"]
    elif body is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
    raw = subprocess.run(cmd, input=json.dumps(body).encode() if body is not None and not form else None,
                         capture_output=True, check=True).stdout
    resp = json.loads(raw.decode("utf-8"), strict=False) if raw else {}
    status = str(resp.get("meta", {}).get("httpStatus", ""))
    if log and method != "GET":
        with open(log, "a") as f:
            f.write(json.dumps({"change": note, "endpoint": f"{method} {url.split('/API/v3')[-1]}",
                                "status": status}) + "\n")
    if not status.startswith("200"):
        raise RuntimeError(f"{method} {url}: {status} {json.dumps(resp.get('meta'))[:500]}")
    return resp.get("result")


def question_body(before: dict, changes: dict) -> dict:
    """A PUT replaces the whole question, so send every writable field; a None change removes the field."""
    body = {k: before[k] for k in QUESTION_FIELDS if before.get(k) is not None}
    for k, v in changes.items():
        if v is None:
            body.pop(k, None)  # "DisplayLogic": null is rejected (ESDEF10); omitting clears it
        else:
            body[k] = v
    return body


def put_question(survey: str, qid: str, changes: dict, log: str | None = None) -> dict:
    path = f"/survey-definitions/{survey}/questions/{qid}"
    body = question_body(call("GET", path), changes)
    call("PUT", path, body, log=log, note=f"edit {qid} {sorted(changes)}")
    after = call("GET", path)
    for k in QUESTION_FIELDS:
        if k in body and after.get(k) != body[k] and not (k == "QuestionText" and after.get(k, "").strip() == body[k].strip()):
            raise RuntimeError(f"{qid}: {k} differs after PUT")
        if k in changes and changes[k] is None and after.get(k):
            raise RuntimeError(f"{qid}: {k} was not removed")
    return after


def library_id() -> str:
    return call("GET", "/whoami")["userId"]


def upload_graphic(library: str, path: str, name: str, folder: str, log: str | None = None) -> str:
    """Files into `folder` only if it already exists in the library; otherwise Qualtrics puts it in Uncategorized."""
    result = call("POST", f"/libraries/{library}/graphics",
                  form={"file": f"@{path}", "name": name, "folder": folder}, log=log, note=f"upload {name} → {folder}")
    return result["id"]


def delete_graphic(library: str, graphic: str, log: str | None = None):
    """For manual cleanup only: builds never delete, since earlier survey versions may use the graphic."""
    call("DELETE", f"/libraries/{library}/graphics/{graphic}", log=log, note=f"delete graphic {graphic}")
