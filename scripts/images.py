"""Upload an instrument's images into its survey's Qualtrics library folder and point the survey at them.

  images.py upload INSTRUMENT --survey SV_ID --drive-root PATH [--registry FILE] [--log FILE]

The `Images:` setup line names one Qualtrics library folder per survey, shared by all its versions.
It must already exist and have a name no other folder in the library has: the API can't create or list
folders, and it files an upload into the first folder with that name, or into Uncategorized when there
is none. Because folders can't be listed, a registry file (folder -> file name -> graphic id), kept in
git next to the instruments, records what each folder holds; only files missing from it are uploaded.
File names never change meaning (a changed image gets a new name), so a registered upload is reused.
Each question's <img> tags (and `<!-- image: … -->` placeholders) are replaced in order with tags at
the width in the file name, the height from the file's pixels, and the setup's border. Nothing is deleted.

Credentials come from the environment: `source scripts/load_env.sh <instance>` first.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

from instrument import image_width, parse

RE_IMAGE_SLOT = re.compile(r"<img\b[^>]*>|<!--\s*image:[^>]*-->", re.IGNORECASE)


def image_size(data: bytes) -> tuple[int, int]:
    """(width, height) from a PNG, JPEG or GIF header."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack(">HH", data[i + 5:i + 9])
                return width, height
            i += 2 + length
    raise ValueError("not a PNG, JPEG or GIF image")


def img_tag(base: str, graphic: str, width: int, size: tuple[int, int], border_px: int) -> str:
    file_w, file_h = size
    if width > file_w:
        raise ValueError(f"{graphic}: {width}px is wider than the file ({file_w}px); images are never upscaled")
    height = round(width * file_h / file_w)
    style = f"width: {width}px; height: {height}px;"
    if border_px:
        style += f" border-width: {border_px}px; border-style: solid;"
    return f'<img src="{base}{graphic}" width="{width}" height="{height}" style="{style}">'


def replace_image_tags(html_text: str, tags: list[str]) -> str:
    slots = RE_IMAGE_SLOT.findall(html_text)
    if len(slots) != len(tags):
        raise ValueError(f"{len(slots)} image slots, {len(tags)} images")
    it = iter(tags)
    return RE_IMAGE_SLOT.sub(lambda _: next(it), html_text)


def plan_tags(parsed: dict, sizes: dict, ids: dict, base: str) -> dict:
    """QID -> the question's new <img> tags, in instrument order."""
    border = parsed["images"]["border"]
    plan = {}
    for q in parsed["questions"]:
        if not q["images"]:
            continue
        plan[q["id"]] = [img_tag(base, ids[name], image_width(name), sizes[name],
                                 border["px"] if border and name not in border["except"] else 0)
                         for name in q["images"]]
    return plan


def to_upload(files: list[str], registry: dict, folder: str) -> list[str]:
    known = registry.get(folder, {})
    return [f for f in files if f not in known]


def upload(instrument: Path, survey: str, drive_root: Path, registry_path: Path, log: str):
    import qualtrics_api as api

    parsed = parse(instrument.read_text())
    setup = parsed["images"]
    if not setup or not setup["folder"]:
        sys.exit("error: the Images: setup line must name a Qualtrics folder")
    if any(q["id"] == "NEW" for q in parsed["questions"] if q["images"]):
        sys.exit("error: assign QIDs to new questions before uploading images")
    folder = drive_root / setup["drive"]
    files = sorted({f for q in parsed["questions"] for f in q["images"]})
    missing = [f for f in files if not (folder / f).is_file()]
    if missing:
        sys.exit(f"error: not in {folder}: {', '.join(missing)}")
    sizes = {f: image_size((folder / f).read_bytes()) for f in files}
    for f in files:
        if image_width(f) > sizes[f][0]:
            sys.exit(f"error: {f} is {sizes[f][0]}px wide; its _w width would upscale it")

    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    known = registry.setdefault(setup["folder"], {})
    library = api.library_id()
    uploaded = []
    for f in to_upload(files, registry, setup["folder"]):
        known[f] = api.upload_graphic(library, str(folder / f), f, setup["folder"], log)
        uploaded.append(f)
        registry_path.write_text(json.dumps(registry, indent=1, sort_keys=True) + "\n")
    for qid, tags in plan_tags(parsed, sizes, known, api.graphic_base()).items():
        before = api.call("GET", f"/survey-definitions/{survey}/questions/{qid}")
        new_text = replace_image_tags(before["QuestionText"], tags)
        if new_text != before["QuestionText"]:
            api.put_question(survey, qid, {"QuestionText": new_text}, log)
    print(json.dumps({"folder": setup["folder"], "uploaded": uploaded, "reused": len(files) - len(uploaded)}, indent=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("upload")
    p.add_argument("instrument", type=Path)
    p.add_argument("--survey", required=True)
    p.add_argument("--drive-root", type=Path, required=True,
                   help="local folder that holds the Drive path in the Images: line (the shared drive's root)")
    p.add_argument("--registry", type=Path,
                   help="folder -> file name -> graphic id, committed with the instruments (default: qualtrics_images.json next to the instrument)")
    p.add_argument("--log", default=None)
    args = parser.parse_args()
    registry = args.registry or args.instrument.parent / "qualtrics_images.json"
    log_dir = args.instrument.parent / ".qualtrics"
    log_dir.mkdir(exist_ok=True)
    upload(args.instrument, args.survey, args.drive_root, registry, args.log or str(log_dir / "log.jsonl"))


if __name__ == "__main__":
    main()
