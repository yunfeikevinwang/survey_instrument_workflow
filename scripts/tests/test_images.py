import struct
import zlib

import pytest

from images import image_size, img_tag, replace_image_tags, plan_tags
from instrument import parse


def png(width, height):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))
    return b"\x89PNG\r\n\x1a\n" + chunk


def jpeg(width, height):
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, height, width, 1) + b"\x01\x11\x00"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def test_image_size_reads_png_and_jpeg_headers():
    assert image_size(png(942, 2048)) == (942, 2048)
    assert image_size(jpeg(1179, 2556)) == (1179, 2556)


def test_image_size_rejects_unknown_formats():
    with pytest.raises(ValueError):
        image_size(b"not an image")


def test_img_tag_keeps_proportions_and_adds_border():
    tag = img_tag("https://mit.co1.qualtrics.com/CP/Graphic.php?IM=", "IM_abc", 250, (942, 2048), 3)
    assert 'src="https://mit.co1.qualtrics.com/CP/Graphic.php?IM=IM_abc"' in tag
    assert 'width="250" height="544"' in tag
    assert "width: 250px; height: 544px; border-width: 3px; border-style: solid;" in tag


def test_img_tag_without_border():
    tag = img_tag("https://x/?IM=", "IM_abc", 20, (23, 25), 0)
    assert "border" not in tag
    assert 'height="22"' in tag


def test_img_tag_never_upscales():
    with pytest.raises(ValueError, match="wider than the file"):
        img_tag("https://x/?IM=", "IM_abc", 700, (647, 410), 3)


def test_replace_image_tags_by_position_including_placeholders():
    html = 'A<img src="old1">B<!-- image: b_w250.png (upload manually) -->C'
    assert replace_image_tags(html, ["<img 1>", "<img 2>"]) == "A<img 1>B<img 2>C"


def test_replace_image_tags_count_must_match():
    with pytest.raises(ValueError, match="2 image slots, 1 images"):
        replace_image_tags('<img a><img b>', ["<img 1>"])


INSTRUMENT = """\
## `S — v1`

```
Images: Drive Qualtrics/main_images, https://drive.example/f; Qualtrics folder "AIMarket Main Survey 1"; 3px solid border on every image except icon_w20.png.
Page timers: none
```

## `B`

##### `One: Text [QID1]`

Look: `a_w700.png` `b_w250.png`

##### `Two: Text [QID2]`

`icon_w20.png` Icon.
"""


def test_plan_tags_gives_each_question_its_tags_in_order():
    parsed = parse(INSTRUMENT)
    sizes = {"a_w700.png": (1400, 700), "b_w250.png": (500, 1000), "icon_w20.png": (40, 40)}
    ids = {"a_w700.png": "IM_a", "b_w250.png": "IM_b", "icon_w20.png": "IM_i"}
    plan = plan_tags(parsed, sizes, ids, "https://x/?IM=")
    assert list(plan) == ["QID1", "QID2"]
    assert 'IM=IM_a"' in plan["QID1"][0] and 'height="350"' in plan["QID1"][0]
    assert 'IM=IM_b"' in plan["QID1"][1] and "border-width: 3px" in plan["QID1"][1]
    assert "border" not in plan["QID2"][0]


def test_registry_reuses_known_uploads_per_folder():
    from images import to_upload
    registry = {"AIMarket Main Survey 1": {"a_w700.png": "IM_a"}, "Other": {"b_w250.png": "IM_b"}}
    assert to_upload(["a_w700.png", "b_w250.png"], registry, "AIMarket Main Survey 1") == ["b_w250.png"]
    assert to_upload(["a_w700.png"], {}, "New folder") == ["a_w700.png"]


def test_question_images_are_replaced_in_the_question_text():
    from images import replace_question_images
    question = {"QuestionText": 'A<img src="old">', "Choices": {"1": {"Display": "Yes"}}}
    assert replace_question_images("QID5", question, ["<img new>"]) == "A<img new>"


def test_images_in_answer_choices_are_refused():
    from images import replace_question_images
    question = {"QuestionText": "Pick one", "Choices": {"1": {"Display": '<img src="x">'}}}
    with pytest.raises(ValueError, match="QID5: images in answer choices"):
        replace_question_images("QID5", question, ["<img new>"])


def test_slot_count_mismatch_names_the_question():
    from images import replace_question_images
    with pytest.raises(ValueError, match="QID5: 0 image slots, 1 images"):
        replace_question_images("QID5", {"QuestionText": "No slots"}, ["<img new>"])
