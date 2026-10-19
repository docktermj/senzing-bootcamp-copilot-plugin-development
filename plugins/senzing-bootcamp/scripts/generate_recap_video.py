#!/usr/bin/env python3
"""Render the graduation storyboard into a narrated, captioned recap video.

Reads ``docs/video/storyboard.json`` and writes ``docs/bootcamp_recap.mp4``: H.264 video and
AAC audio in an mp4, ``yuv420p`` for broad playability, 1920x1080 at 30 fps.

The agent writes the content; this script renders it. It follows the pattern of
``generate_recap_pdf.py`` and ``capture_screenshots.py``: a deterministic, tested renderer
behind a file the agent authors, so a language model never has to produce video itself.

How it works, in three passes:

1. **Validate.** Every scene is checked against ``SCENE_TYPES``, the one table that maps a
   scene type to its data fields and to the function that draws it. A problem is reported
   with the field that caused it (``scenes[3].items[0].value: ...``) and nothing is written.
2. **Voice, then plan the timeline.** A voice-selection stage tries a local Piper neural voice
   first (``voice_with_piper``): it voices every scene or none. When it voices none, each
   scene's narration is synthesized with the platform's own speech engine instead. Either way
   the scene lasts ``max(planned duration, narration length)``.
3. **Stream.** Frames are drawn with Pillow and written as raw RGB straight into one ffmpeg
   process's stdin. Its audio inputs are the assembled narration (48 kHz stereo, each
   narration at its scene's start) and the synthesized music bed; the same ffmpeg call mixes
   them (``audio_filter_graph``) and encodes the result. No frame is ever written to disk.

⛔ **(INV-342) Narration is never truncated: a scene whose narration runs longer than its planned
duration is extended to fit, and every overrun is reported on stderr.** Without a voice the
narration's length is estimated at ``WORDS_PER_MINUTE``, so the burned-in caption gets the
time a listener would have had.

⛔ **(INV-342) Captions are always burned in, whether or not there is a voice.** The caption defaults to
the narration, so a video rendered without a speech engine still carries every word.

⛔ **(INV-342) A storyboard image must be a project-relative local file; an absolute path, a URL, or a
path that resolves outside the project is rejected as an invalid storyboard.** A
project-relative image that is missing or unreadable is not an error: that scene is drawn as a
title card instead, and stderr says so.

⛔ **(INV-342) The renderer is offline: it opens only local files and never fetches from the network.**
Fonts come from the operating system, the palette from ``brand_tokens.py`` (INV-081), the voice
from a local Piper model already on disk (never downloaded here) or the platform's built-in
speech engine.

Storyboard format
-----------------

::

    {
      "video": {"bootcamper": "Ada Lovelace", "graduation_date": "2026-09-30",
                "music": true},
      "scenes": [
        {"type": "title_card", "duration": 6,
         "narration": "It started with a business problem.",
         "module": "Business Problem", "highlight": "Three sources, one customer view"},
        {"type": "image", "duration": 8, "narration": "...",
         "image": "docs/visualizations/results_visualization-match-keys.png",
         "heading": "Match keys"},
        {"type": "counter", "duration": 8, "narration": "...",
         "title": "Records loaded", "items": [{"label": "CRM", "value": 1200}]},
        {"type": "certificate", "duration": 8, "narration": "..."},
        {"type": "tag_line", "duration": 5, "narration": "..."}
      ]
    }

``video.music`` is optional and defaults to ``true``: a light, upbeat music bed synthesized at
render time with the standard library (no audio file ships), ducked under the voice with
``sidechaincompress`` and loudness-normalized with the voice to about -16 LUFS. The voice is
leveled first (``LEVELER``), so its peaks leave ``loudnorm`` room to reach that target. ``false``
turns it off.

Every scene carries ``type``, ``duration`` (planned seconds), ``narration`` and an optional
``caption`` (defaults to the narration). The rest depends on the type; ``--schema`` prints the
table. Keys beginning with ``_`` are comments and are ignored. The scene types:

* ``title_card`` -- a module name plus its highlight, for a module with nothing on screen.
* ``image`` -- a slow pan and zoom over a screenshot.
* ``counter`` -- animated bars and numbers: record counts per source, entities resolved.
* ``mapping`` -- source fields flowing to Senzing attributes.
* ``loading`` -- records flowing into entities, with a rising counter.
* ``entity_merge`` -- records converging into resolved entities.
* ``certificate`` -- the Certificate of Completion, drawn from the same name, date and
  completed-module list the recap PDF's certificate uses (INV-100, INV-342): the recap
  (``docs/bootcamp_recap.md``) read by ``generate_recap_pdf``'s own parser, with the
  preferences name outranking it exactly as it does there. It is drawn, never rasterized from
  the PDF.
* ``tag_line`` -- the closing card. ``text`` defaults to
  ``Resolved: <bootcamper>, Senzing graduate.``

Fallbacks, each stated on stderr (INV-111)
------------------------------------------

* **Piper first.** The voice is a local Piper neural voice (``piper-tts``, run as
  ``sys.executable -m piper``, never imported) when ``piper`` is findable by this interpreter
  and the ``--voice-model`` ``.onnx`` file and its ``.onnx.json`` config both exist. The model
  defaults to ``data/temp/piper-voices/en_US-ljspeech-high.onnx`` under ``--project-root``.
  Otherwise stderr names the case (``piper`` not installed for this interpreter, the model
  missing, or its config missing) and the platform engine below is used. Numbers in Piper's
  speech text are spelled out; the captions keep the digits.
* **Piper fails on any scene:** Piper is dropped for the whole video, and every scene is
  re-voiced with the platform engine, so the video never mixes two voices. stderr says so.
* No speech engine (macOS ``say``, Windows SAPI through PowerShell ``System.Speech``, Linux
  ``espeak-ng`` or ``espeak``), ``--no-voice``, or an engine that voiced no scene: the video
  renders without a voice-over and the captions carry the narration. The music bed still plays,
  normalized to the same -16 LUFS, so the video keeps an audio stream unless ``video.music`` is
  ``false`` as well.
* ffmpeg is not on ``PATH`` (or lacks the H.264/AAC encoders, or the ``sidechaincompress`` and
  ``loudnorm`` filters the mix needs): the binary bundled with the ``imageio-ffmpeg`` package is
  used instead, and stderr names what the first one lacked.
* A missing or unreadable image: the scene becomes a title card.
* No recap to read the certificate from: the storyboard's name and date are used.
* No TrueType font: Pillow's built-in font. ``brand_tokens.py`` unavailable: the inlined palette.

Exit codes
----------

⛔ **(INV-342) The exit codes are separate, and no video is written unless the exit is 0; a video already
at the output path is left as it was.** The render goes to a hidden partial file beside the
output and replaces it only once ffmpeg has succeeded.

= ===========================================================================================
0 rendered: prints ``Video generated: <path>``, its duration, a ``Voice:`` line and a
  ``Music:`` line
1 invalid storyboard: each problem names its field; nothing is written
2 a required capability is missing (no ffmpeg, or no Pillow); nothing is written
3 the encode itself failed (ffmpeg exited non-zero); nothing is written
= ===========================================================================================

Usage::

    python3 generate_recap_video.py [--storyboard docs/video/storyboard.json]
                                    [--output docs/bootcamp_recap.mp4]
                                    [--project-root .] [--voice-model <model.onnx>]
                                    [--no-voice] [--check] [--schema]

``--check`` validates the storyboard and exits 0 or 1 without rendering; it needs neither
Pillow nor ffmpeg. ``--voice-model`` names a local Piper ``.onnx`` model whose ``.onnx.json``
config sits beside it (default: ``data/temp/piper-voices/en_US-ljspeech-high.onnx`` under
``--project-root``). Source issues: #299, #339, #341.
"""

from __future__ import annotations

import argparse
import array
import datetime
import importlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Dict, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_STORYBOARD = "docs/video/storyboard.json"
DEFAULT_OUTPUT = "docs/bootcamp_recap.mp4"
DEFAULT_RECAP = "docs/bootcamp_recap.md"
DEFAULT_PREFERENCES = "config/bootcamp_preferences.yaml"

EXIT_RENDERED = 0
EXIT_INVALID_STORYBOARD = 1
EXIT_MISSING_CAPABILITY = 2
EXIT_RENDER_FAILED = 3

WIDTH, HEIGHT, FPS = 1920, 1080, 30
#: Divisible by FPS, so every frame owns a whole number of audio samples and the narration
#: can never drift against the picture however long the video runs.
AUDIO_RATE = 48000
AUDIO_CHANNELS = 2
SAMPLES_PER_FRAME = AUDIO_RATE // FPS

#: Silence before and after a scene's narration. Part of the time a narration needs.
NARRATION_LEAD = 0.3
NARRATION_TAIL = 0.5
#: Speaking rate used to estimate a narration's length when there is no voice to measure.
WORDS_PER_MINUTE = 160
#: A planned duration above this is almost certainly milliseconds or a typo.
MAX_SCENE_SECONDS = 60.0

FADE_IN = 0.3
FADE_OUT = 0.8

CAPTION_SIZE = 44
CAPTION_MAX_WIDTH = 1560
CAPTION_LINES = 2
CAPTION_BOTTOM = HEIGHT - 44

#: Modules whose import would mean a network fetch. The renderer imports none of them.
NETWORK_MODULES = ("urllib", "http", "socket", "requests", "ftplib", "smtplib")

#: The default Piper voice (#341). The default ``--voice-model`` path is built from it.
#: License record (from #341; the model card was read 2026-10-01):
#:   - the voice: ``en_US-ljspeech-high``, trained from scratch on the LJ Speech dataset, which
#:     is public domain;
#:   - the engine: ``piper-tts`` 1.8.0 is GPL-3.0-or-later. It is installed into the
#:     Bootcamper's venv and run as a separate process, never imported; the plugin does not
#:     ship it.
#: Never a voice from the CC BY-NC-SA or Blizzard 2013 families (``ryan``, ``hfc_*``,
#: ``lessac``): their licenses do not allow a shareable keepsake.
DEFAULT_PIPER_VOICE = "en_US-ljspeech-high"
PIPER_VOICE_DIR = "data/temp/piper-voices"
DEFAULT_VOICE_MODEL = f"{PIPER_VOICE_DIR}/{DEFAULT_PIPER_VOICE}.onnx"
#: Speaking parameters from the version the Bootcamper accepted (#331, P3-22).
PIPER_LENGTH_SCALE = "1.0"
PIPER_SENTENCE_SILENCE = "0.15"


def _report(prefix: str, message: str) -> None:
    sys.stderr.write(f"{prefix}: {message}\n")
    sys.stderr.flush()


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def _ease(x: float) -> float:
    """Cubic ease-out: quick start, gentle landing."""
    x = _clamp(x)
    return 1.0 - (1.0 - x) ** 3


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _format_number(value) -> str:
    if isinstance(value, int) or float(value).is_integer():
        return f"{int(round(value)):,}"
    return f"{value:,.1f}"


def _format_duration(seconds: float) -> str:
    whole = int(round(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


def _word_count(text: str) -> int:
    return len(text.split())


def estimated_narration_seconds(text: str) -> float:
    """How long `text` takes to say at WORDS_PER_MINUTE."""
    return _word_count(text) * 60.0 / WORDS_PER_MINUTE


# --------------------------------------------------------------------------- #
# Brand palette (INV-081)
# --------------------------------------------------------------------------- #
# Fallback palette (RGB), used only if brand_tokens is unavailable. Named at module scope so
# tests/test_brand_sync.py can assert it stays equal to the brand_tokens values (INV-184).
_FALLBACK_RGB = {
    "OBSIDIAN": (15, 13, 12), "DEEP": (24, 22, 15), "SURFACE_DARK": (32, 30, 22),
    "EMBER_HOT": (255, 78, 31), "EMBER_CORE": (245, 120, 38), "EMBER_END": (240, 146, 10),
    "EMBER_SOFT": (253, 238, 227), "SIGNAL_GREEN": (29, 158, 117), "WHITE": (255, 255, 255),
    "WARM_OFF_WHITE": (250, 248, 243), "DARK_INK": (24, 22, 15), "BODY_INK": (74, 70, 64),
    "WARM_LINE": (229, 223, 211),
}

#: The brand_tokens name behind each palette entry.
_TOKEN_NAMES = {
    "OBSIDIAN": "OBSIDIAN", "DEEP": "DEEP", "SURFACE_DARK": "SURFACE_DARK",
    "EMBER_HOT": "EMBER_HOT", "EMBER_CORE": "EMBER_CORE", "EMBER_END": "EMBER_GRAD_END",
    "EMBER_SOFT": "EMBER_SOFT", "SIGNAL_GREEN": "SIGNAL_GREEN", "WHITE": "WHITE",
    "WARM_OFF_WHITE": "WARM_OFF_WHITE", "DARK_INK": "DARK_INK", "BODY_INK": "BODY_INK",
    "WARM_LINE": "WARM_LINE",
}


def _load_palette():
    """(palette, brand_tokens module or None, fallback note or None)."""
    try:
        import brand_tokens as bt

        return ({k: bt.hex_to_rgb(getattr(bt, v)) for k, v in _TOKEN_NAMES.items()}, bt, None)
    except ModuleNotFoundError:
        return (dict(_FALLBACK_RGB), None,
                f"brand_tokens.py not importable from {SCRIPT_DIR} (copy it next to this "
                "script); using the inlined brand palette.")
    except Exception as exc:  # present but unusable
        return (dict(_FALLBACK_RGB), None,
                f"brand_tokens.py present but unusable ({exc}); using the inlined brand palette.")


PALETTE, _BRAND, PALETTE_NOTE = _load_palette()
P = PALETTE


def _mix(a, b, t: float) -> Tuple[int, int, int]:
    t = _clamp(t)
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


#: On-dark body text: the brand's 60% white, flattened onto obsidian.
MUTED_ON_DARK = _mix(P["OBSIDIAN"], P["WHITE"], 0.6)
#: Small-caps labels on the light certificate: body ink blended toward the off-white, the
#: same derivation the recap PDF's certificate uses.
MUTED_ON_LIGHT = _mix(P["BODY_INK"], P["WARM_OFF_WHITE"], 0.48)


def source_fills(labels: Sequence[str]) -> List[Tuple[int, int, int]]:
    """One categorical fill per label, from brand_tokens' source encoding when it loads."""
    if _BRAND is not None and hasattr(_BRAND, "color_for_sources"):
        assigned = _BRAND.color_for_sources(labels)
        return [_BRAND.hex_to_rgb(assigned[str(l)]["fill"]) if str(l).strip() in assigned
                else P["EMBER_CORE"] for l in labels]
    return [P["EMBER_CORE"] for _ in labels]


# --------------------------------------------------------------------------- #
# The storyboard schema: one declarative table
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FieldSpec:
    """One data field of a scene (or of an item inside a list field).

    ``kind`` is one of FIELD_KINDS. ``minimum`` bounds a count or number; ``max_items`` bounds
    a list, and ``item_fields`` describes each object in an ``items`` list.
    """

    name: str
    kind: str
    required: bool = True
    minimum: float = 0
    max_items: int = 0
    item_fields: Tuple["FieldSpec", ...] = ()
    help: str = ""


FIELD_KINDS = ("text", "count", "number", "seconds", "date", "image", "path", "text_list",
               "items", "boolean")


def F(name, kind, required=True, **kw) -> FieldSpec:
    return FieldSpec(name, kind, required, **kw)


#: Carried by every scene, whatever its type.
COMMON_FIELDS = (
    F("type", "text", help="one of the scene types"),
    F("duration", "seconds", help="planned seconds; extended if the narration needs longer"),
    F("narration", "text", help="spoken by the voice-over, and the caption's default"),
    F("caption", "text", False, help="burned-in caption; defaults to the narration"),
)

#: The storyboard's `video` object.
VIDEO_FIELDS = (
    F("bootcamper", "text", help="the Bootcamper's name, as the video should say it"),
    F("graduation_date", "date", help="YYYY-MM-DD"),
    F("title", "text", False),
    F("music", "boolean", False,
      help="the synthesized music bed under the narration; defaults to true, false turns it off"),
)

TOP_LEVEL_KEYS = ("version", "video", "scenes")


@dataclass(frozen=True)
class SceneType:
    name: str
    summary: str
    fields: Tuple[FieldSpec, ...]
    draw: Callable
    #: Cross-field rules a single field cannot express: (scene, where) -> [problems].
    check: Optional[Callable] = None


# --------------------------------------------------------------------------- #
# Validation (needs neither Pillow nor ffmpeg)
# --------------------------------------------------------------------------- #
_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def project_relative_problem(value, root: Path) -> Optional[str]:
    """Why `value` is not a project-relative local path, or None when it is.

    Existence is not checked here: a missing project-relative image is a fallback (a title
    card), not an invalid storyboard. Anything that is not project-relative is rejected.
    """
    if not isinstance(value, str) or not value.strip():
        return "must be a project-relative path to a local file"
    v = value.strip()
    if _URL.match(v) or v.lower().startswith(("file:", "data:", "http:", "https:")):
        return (f"{v!r} is a URL; storyboard files must be project-relative local files "
                "(the renderer never fetches from the network)")
    if (v.startswith(("/", "\\", "~")) or PureWindowsPath(v).drive
            or PurePosixPath(v).is_absolute()):
        return f"{v!r} is an absolute path; it must be relative to the project root"
    base = root.resolve()
    target = (base / v).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return f"{v!r} resolves outside the project ({base})"
    return None


def _is_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _check_value(spec: FieldSpec, value, where: str, root: Path, errors: List[str]) -> None:
    kind = spec.kind
    if kind == "text":
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}: must be a non-empty string")
    elif kind == "count":
        if isinstance(value, bool) or not isinstance(value, int) or value < spec.minimum:
            errors.append(f"{where}: must be a whole number of at least {int(spec.minimum)}")
    elif kind == "number":
        if not _is_number(value) or value < spec.minimum:
            errors.append(f"{where}: must be a number of at least {spec.minimum:g}")
    elif kind == "seconds":
        if not _is_number(value) or not 0 < value <= MAX_SCENE_SECONDS:
            errors.append(f"{where}: must be a number of seconds greater than 0 and at most "
                          f"{MAX_SCENE_SECONDS:g}")
    elif kind == "date":
        ok = isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip())
        if ok:
            try:
                datetime.date.fromisoformat(value.strip())
            except ValueError:
                ok = False
        if not ok:
            errors.append(f"{where}: must be a date written YYYY-MM-DD")
    elif kind in ("image", "path"):
        problem = project_relative_problem(value, root)
        if problem:
            errors.append(f"{where}: {problem}")
    elif kind == "text_list":
        if not isinstance(value, list) or any(
                not isinstance(v, str) or not v.strip() for v in value):
            errors.append(f"{where}: must be a list of non-empty strings")
        elif spec.max_items and len(value) > spec.max_items:
            errors.append(f"{where}: at most {spec.max_items} entries")
    elif kind == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{where}: must be true or false")
    elif kind == "items":
        if not isinstance(value, list) or not value:
            errors.append(f"{where}: must be a non-empty list")
            return
        if spec.max_items and len(value) > spec.max_items:
            errors.append(f"{where}: at most {spec.max_items} entries (found {len(value)})")
        for i, item in enumerate(value):
            _check_object(item, spec.item_fields, f"{where}[{i}]", root, errors)
    else:  # pragma: no cover - the table is checked by the tests
        errors.append(f"{where}: unknown field kind {kind!r}")


def _check_object(obj, specs: Sequence[FieldSpec], where: str, root: Path,
                  errors: List[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{where}: must be an object")
        return
    known = {s.name for s in specs}
    for key in obj:
        if key not in known and not str(key).startswith("_"):
            errors.append(f"{where}.{key}: unknown field (known: {', '.join(sorted(known))})")
    for spec in specs:
        if spec.name not in obj:
            if spec.required:
                errors.append(f"{where}.{spec.name}: required field is missing")
            continue
        _check_value(spec, obj[spec.name], f"{where}.{spec.name}", root, errors)


def validate_storyboard(data, root) -> List[str]:
    """Every problem with the storyboard, each naming its field. Empty when it is valid."""
    root = Path(root)
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["(document): the storyboard must be a JSON object"]
    for key in data:
        if key not in TOP_LEVEL_KEYS and not str(key).startswith("_"):
            errors.append(f"{key}: unknown top-level field (known: {', '.join(TOP_LEVEL_KEYS)})")
    if "video" not in data:
        errors.append("video: required object is missing (bootcamper, graduation_date)")
    else:
        _check_object(data["video"], VIDEO_FIELDS, "video", root, errors)
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes: must be a non-empty list of scenes")
        return errors
    for i, scene in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(scene, dict):
            errors.append(f"{where}: must be an object")
            continue
        kind = scene.get("type")
        if kind not in SCENE_TYPES:
            errors.append(f"{where}.type: {kind!r} is not a scene type "
                          f"(known: {', '.join(SCENE_TYPES)})")
            continue
        scene_type = SCENE_TYPES[kind]
        _check_object(scene, COMMON_FIELDS + scene_type.fields, where, root, errors)
        if scene_type.check:
            errors.extend(scene_type.check(scene, where))
    return errors


def _entities_not_above_records(scene, where) -> List[str]:
    records, entities = scene.get("records"), scene.get("entities")
    if isinstance(records, int) and isinstance(entities, int) and entities > records:
        return [f"{where}.entities: {entities} entities cannot come from {records} records"]
    return []


def schema_description() -> dict:
    """The table, as data: what `--schema` prints."""
    def fields(specs):
        out = {}
        for s in specs:
            entry = {"kind": s.kind, "required": s.required}
            if s.help:
                entry["help"] = s.help
            if s.max_items:
                entry["max_items"] = s.max_items
            if s.item_fields:
                entry["item_fields"] = fields(s.item_fields)
            out[s.name] = entry
        return out

    return {
        "video": fields(VIDEO_FIELDS),
        "every_scene": fields(COMMON_FIELDS),
        "scene_types": {name: {"summary": t.summary, "fields": fields(t.fields)}
                        for name, t in SCENE_TYPES.items()},
        "images": "project-relative local files only; a missing one becomes a title card",
    }


# --------------------------------------------------------------------------- #
# Capabilities: Pillow, ffmpeg, a voice
# --------------------------------------------------------------------------- #
class CapabilityMissing(Exception):
    """A required capability is absent; the message says which and how to get it."""


def _find_spec(name: str):
    try:
        return importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return None


def load_pillow():
    """(Image, ImageDraw, ImageFont), or CapabilityMissing naming the case (INV-111)."""
    if _find_spec("PIL") is None:
        raise CapabilityMissing(
            f"Pillow is not installed for {sys.executable}, so no frame can be drawn. "
            "Install it for this interpreter: python3 -m pip install Pillow")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        raise CapabilityMissing(
            f"Pillow is installed for {sys.executable} but unusable ({exc}); no frame can be "
            "drawn.")
    return Image, ImageDraw, ImageFont


_ENCODER = {
    "libx264": re.compile(r"^\s*V\S*\s+libx264\b", re.M),
    "aac": re.compile(r"^\s*A\S*\s+aac\b", re.M),
}

#: The filters the audio mix needs, required the same way as the encoders (#339).
_FILTER = {
    "sidechaincompress": re.compile(r"^\s*\S+\s+sidechaincompress\b", re.M),
    "loudnorm": re.compile(r"^\s*\S+\s+loudnorm\b", re.M),
}


def missing_encoders(ffmpeg: str) -> List[str]:
    """The required encoders `ffmpeg` lacks (all of them if it cannot be run)."""
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True,
                           text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return list(_ENCODER)
    return [name for name, pattern in _ENCODER.items() if not pattern.search(r.stdout)]


def missing_filters(ffmpeg: str) -> List[str]:
    """The filters the audio mix needs that `ffmpeg` lacks (all of them if it cannot be run)."""
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True,
                           text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return list(_FILTER)
    return [name for name, pattern in _FILTER.items() if not pattern.search(r.stdout)]


def _lacking(ffmpeg: str) -> str:
    """What `ffmpeg` lacks of the required encoders and filters, as a phrase; "" if nothing."""
    parts = []
    encoders, filters = missing_encoders(ffmpeg), missing_filters(ffmpeg)
    if encoders:
        parts.append(f"the {', '.join(encoders)} encoder(s)")
    if filters:
        parts.append(f"the {', '.join(filters)} filter(s)")
    return " and ".join(parts)


def _imageio_ffmpeg() -> Tuple[Optional[str], str]:
    """(path, "") from the imageio-ffmpeg package, or (None, why not)."""
    if _find_spec("imageio_ffmpeg") is None:
        return None, f"imageio-ffmpeg is not installed for {sys.executable}"
    try:
        module = importlib.import_module("imageio_ffmpeg")
        return module.get_ffmpeg_exe(), ""
    except Exception as exc:
        return None, f"imageio-ffmpeg is installed for {sys.executable} but unusable ({exc})"


def find_ffmpeg() -> Tuple[str, List[str]]:
    """(ffmpeg path, fallback notes): PATH first, then imageio-ffmpeg.

    Raises CapabilityMissing when neither yields an ffmpeg with the H.264 and AAC encoders and
    the ``sidechaincompress`` and ``loudnorm`` filters the audio mix needs.
    """
    notes: List[str] = []
    tried: List[str] = []
    on_path = shutil.which("ffmpeg")
    if on_path:
        lacking = _lacking(on_path)
        if not lacking:
            return on_path, notes
        tried.append(f"ffmpeg on PATH ({on_path}) lacks {lacking}")
    else:
        tried.append("ffmpeg is not on PATH")
    bundled, why = _imageio_ffmpeg()
    if bundled:
        lacking = _lacking(bundled)
        if not lacking:
            notes.append(f"{tried[-1]}; using the ffmpeg bundled with imageio-ffmpeg "
                         f"({bundled}).")
            return bundled, notes
        tried.append(f"the imageio-ffmpeg binary ({bundled}) lacks {lacking}")
    else:
        tried.append(why)
    raise CapabilityMissing(
        "no usable ffmpeg: " + "; ".join(tried) + ". Install the imageio-ffmpeg package into "
        "the project's virtualenv (python3 -m pip install imageio-ffmpeg), or put an ffmpeg "
        "with libx264, aac, sidechaincompress and loudnorm on PATH.")


@dataclass(frozen=True)
class SpeechEngine:
    name: str
    #: (text file, wav file) -> (argv, extra environment)
    command: Callable[[str, str], Tuple[List[str], Dict[str, str]]]


_SAPI_SCRIPT = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$s.SetOutputToWaveFile($env:SBCP_TTS_OUT); "
    "$s.Speak([System.IO.File]::ReadAllText($env:SBCP_TTS_IN, [System.Text.Encoding]::UTF8)); "
    "$s.Dispose()"
)


def _sapi_available(powershell: str) -> bool:
    try:
        r = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command",
             "Add-Type -AssemblyName System.Speech"],
            capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def find_speech_engine() -> Tuple[Optional[SpeechEngine], List[str]]:
    """The platform's built-in speech engine, or (None, what was tried)."""
    tried: List[str] = []
    if sys.platform == "darwin":
        say = shutil.which("say")
        if say:
            return SpeechEngine("say", lambda txt, wav: (
                [say, "--file-format=WAVE", "--data-format=LEI16@22050", "-o", wav, "-f", txt],
                {})), tried
        tried.append("say (not on PATH)")
    if sys.platform == "win32":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if powershell and _sapi_available(powershell):
            return SpeechEngine("Windows SAPI (System.Speech)", lambda txt, wav: (
                [powershell, "-NoProfile", "-NonInteractive", "-Command", _SAPI_SCRIPT],
                {"SBCP_TTS_IN": txt, "SBCP_TTS_OUT": wav})), tried
        tried.append("PowerShell System.Speech (" +
                     ("not loadable" if powershell else "no PowerShell on PATH") + ")")
    for name in ("espeak-ng", "espeak"):
        exe = shutil.which(name)
        if exe:
            return SpeechEngine(name, lambda txt, wav, exe=exe: (
                [exe, "-w", wav, "-f", txt], {})), tried
        tried.append(f"{name} (not on PATH)")
    return None, tried


def choose_voice(no_voice: bool) -> Tuple[Optional[SpeechEngine], Optional[str]]:
    """(engine, fallback note): the voice-over engine, or None and why there is none."""
    if no_voice:
        return None, ("voice-over turned off by --no-voice; the video has no voice-over and "
                      "the burned-in captions carry the narration.")
    engine, tried = find_speech_engine()
    if engine is None:
        return None, ("no speech engine found (tried " + ", ".join(tried) + "); the video has "
                      "no voice-over and the burned-in captions carry the narration.")
    return engine, None


def decode_to_pcm(ffmpeg: str, audio_file: str) -> bytes:
    """Any audio file -> mono signed 16-bit PCM at AUDIO_RATE, through ffmpeg."""
    r = subprocess.run(
        [ffmpeg, "-v", "error", "-i", audio_file, "-f", "s16le", "-acodec", "pcm_s16le",
         "-ac", "1", "-ar", str(AUDIO_RATE), "pipe:1"],
        capture_output=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or "ffmpeg failed")
    data = r.stdout
    return data[: len(data) - (len(data) % 2)]


def synthesize_pcm(engine: SpeechEngine, text: str, ffmpeg: str, workdir: Path,
                   stem: str) -> bytes:
    """Speak `text` with `engine` and return its PCM. Raises RuntimeError on failure."""
    txt = workdir / f"{stem}.txt"
    wav = workdir / f"{stem}.wav"
    txt.write_text(text, encoding="utf-8")
    argv, extra = engine.command(str(txt), str(wav))
    env = dict(os.environ, **extra)
    try:
        r = subprocess.run(argv, capture_output=True, timeout=300, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(str(exc))
    if r.returncode != 0 or not wav.is_file() or wav.stat().st_size <= 44:
        detail = r.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"{engine.name} exited {r.returncode}" +
                           (f": {detail}" if detail else ""))
    pcm = decode_to_pcm(ffmpeg, str(wav))
    if not pcm:
        raise RuntimeError(f"{engine.name} produced no audio")
    return pcm


# --------------------------------------------------------------------------- #
# The voice-selection stage: Piper first, for every scene or for none (#341)
# --------------------------------------------------------------------------- #
_ONES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
         "seventeen", "eighteen", "nineteen")
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_SCALES = ((10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"),
           (1000, "thousand"))

#: A free-standing number: an integer, with or without thousands separators, and an optional
#: decimal part. Digits joined to a letter or underscore (``CORD2``, ``v4``, ``4th``) are not
#: matched, nor is a run of digits glued to another by ``.`` or ``,`` that is not a number.
_NUMBER = re.compile(r"(?<![\w.,])([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.([0-9]+))?"
                     r"(?![\w]|[.,][0-9])")


def _integer_words(n: int) -> str:
    """`n` (0 <= n < 10**15) in English words: 1540 -> "one thousand five hundred forty"."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        return f"{_ONES[hundreds]} hundred" + (f" {_integer_words(rest)}" if rest else "")
    for size, name in _SCALES:
        if n >= size:
            head, rest = divmod(n, size)
            return f"{_integer_words(head)} {name}" + (f" {_integer_words(rest)}" if rest else "")
    raise AssertionError(n)  # pragma: no cover - every n >= 1000 meets a scale


def spell_numbers(text: str) -> str:
    """`text` with each free-standing number written in English words, for Piper only.

    ``10,000`` -> ``ten thousand``; ``3.5`` -> ``three point five`` (the digits after the point
    are read one by one). Digits joined to letters (``CORD2``, ``v4``) are left as they are, as
    is a number of a quadrillion or more. Standard library only; the captions and the
    platform engines never see this text.
    """
    def words(match: "re.Match") -> str:
        whole = int(match.group(1).replace(",", ""))
        if whole >= 10 ** 15:
            return match.group(0)
        spoken = _integer_words(whole)
        if match.group(2):
            spoken += " point " + " ".join(_ONES[int(d)] for d in match.group(2))
        return spoken

    return _NUMBER.sub(words, text)


def piper_config_path(model: Path) -> Path:
    """The ``.onnx.json`` config that sits beside a Piper ``.onnx`` model."""
    return model.with_name(model.name + ".json")


def _voice_name(model: Path) -> str:
    return model.name[:-len(".onnx")] if model.name.endswith(".onnx") else model.name


def find_piper_voice(model: Path) -> Tuple[Optional[SpeechEngine], Optional[str]]:
    """(the Piper engine, None), or (None, which case kept Piper out) (INV-111).

    Piper is never imported: ``find_spec`` only asks whether this interpreter could find it,
    and the engine runs it as ``sys.executable -m piper``. Only the model and its config are
    looked at, and only on the local disk (INV-342).
    """
    if _find_spec("piper") is None:
        return None, (f"Piper (piper-tts) is not installed for {sys.executable}; using the "
                      "platform speech engine.")
    if not model.is_file():
        return None, f"no Piper voice model at {model}; using the platform speech engine."
    config = piper_config_path(model)
    if not config.is_file():
        return None, (f"the Piper voice model {model} has no config beside it ({config} is "
                      "missing); using the platform speech engine.")

    def command(txt: str, wav: str) -> Tuple[List[str], Dict[str, str]]:
        return ([sys.executable, "-m", "piper", "-m", str(model), "-c", str(config),
                 "-i", txt, "-f", wav, "--length-scale", PIPER_LENGTH_SCALE,
                 "--sentence-silence", PIPER_SENTENCE_SILENCE], {})

    return SpeechEngine(f"Piper ({_voice_name(model)})", command), None


def voice_with_piper(scenes: Sequence[dict], piper: SpeechEngine, ffmpeg: str, workdir: Path,
                     note: Callable[[str], None]) -> Optional[List[bytes]]:
    """Every scene's narration voiced by `piper`, as PCM in scene order; or None.

    The narration Piper speaks has its numbers spelled out (``spell_numbers``). All or
    nothing: a failure on any scene returns None, states the switch through `note`, and
    removes what this stage wrote, so the platform engine re-voices the whole video and no
    video ever mixes two voices.
    """
    stage = workdir / "piper"
    stage.mkdir(parents=True, exist_ok=True)
    voices: List[bytes] = []
    for index, scene in enumerate(scenes):
        try:
            voices.append(synthesize_pcm(piper, spell_numbers(scene["narration"]), ffmpeg,
                                         stage, f"scene-{index:03d}"))
        except RuntimeError as exc:
            note(f"scenes[{index}] ({scene['type']}): {piper.name} could not voice this "
                 f"narration ({exc}); Piper is dropped for the whole video and every scene "
                 "is re-voiced with the platform speech engine, so the video never mixes two "
                 "voices.")
            shutil.rmtree(stage, ignore_errors=True)
            return None
    return voices


# --------------------------------------------------------------------------- #
# The render context: fonts, caches, the certificate's fields
# --------------------------------------------------------------------------- #
_FONT_CANDIDATES = {
    "regular": ("Roboto-Regular.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
                "Arial.ttf", "arial.ttf", "segoeui.ttf", "Helvetica.ttc",
                "HelveticaNeue.ttc"),
    "bold": ("Roboto-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
             "Arial Bold.ttf", "arialbd.ttf", "segoeuib.ttf", "Helvetica.ttc",
             "HelveticaNeue.ttc"),
}


class RenderContext:
    """What every drawer shares: Pillow, fonts, caches, and the storyboard's `video`."""

    def __init__(self, pil, video: dict, root: Path):
        self.Image, self.ImageDraw, self.ImageFont = pil
        self.video = video
        self.root = Path(root)
        self.cache: Dict = {}
        self._font_paths: Dict[str, Optional[str]] = {}
        self._fonts: Dict = {}
        self._noted: set = set()

    def note(self, message: str) -> None:
        """A fallback, stated once on stderr (INV-111)."""
        if message not in self._noted:
            self._noted.add(message)
            _report("FALLBACK", message)

    def _font_path(self, style: str) -> Optional[str]:
        if style not in self._font_paths:
            found = None
            for name in _FONT_CANDIDATES[style]:
                try:
                    found = self.ImageFont.truetype(name, 20).path
                    break
                except (OSError, AttributeError):
                    continue
            self._font_paths[style] = found
            if found is None:
                self.note(f"no TrueType {style} font found (tried "
                          f"{', '.join(_FONT_CANDIDATES[style])}); using Pillow's built-in font.")
        return self._font_paths[style]

    def font(self, style: str, size: int):
        key = (style, size)
        if key not in self._fonts:
            path = self._font_path(style)
            if path:
                self._fonts[key] = self.ImageFont.truetype(path, size)
            else:
                try:
                    self._fonts[key] = self.ImageFont.load_default(size=size)
                except TypeError:  # Pillow < 10.1 has one fixed-size bitmap font
                    self._fonts[key] = self.ImageFont.load_default()
        return self._fonts[key]


def _text_width(font, text: str) -> float:
    try:
        return font.getlength(text)
    except AttributeError:
        box = font.getbbox(text)
        return box[2] - box[0]


def _line_height(font) -> int:
    return int(getattr(font, "size", 12) * 1.28)


def wrap_text(font, text: str, max_width: float) -> List[str]:
    """Greedy word wrap by measured width; an over-long word is broken by characters."""
    lines: List[str] = []
    for paragraph in str(text).split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if _text_width(font, candidate) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            while _text_width(font, word) > max_width and len(word) > 1:
                cut = len(word) - 1
                while cut > 1 and _text_width(font, word[:cut]) > max_width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
        if current:
            lines.append(current)
    return lines


def _draw_text(draw, x: float, y: float, text: str, font, fill, align: str = "left") -> None:
    """Text with its top at `y`; `x` is the left edge, center or right edge per `align`."""
    width = _text_width(font, text)
    if align == "center":
        x -= width / 2
    elif align == "right":
        x -= width
    draw.text((round(x), round(y)), text, font=font, fill=fill)


def _draw_lines(draw, x, y, lines, font, fill, align="left", spacing=1.0) -> float:
    """Draw `lines` from `y` down; returns the y below the last one."""
    step = _line_height(font) * spacing
    for line in lines:
        _draw_text(draw, x, y, line, font, fill, align)
        y += step
    return y


def _fit_font(ctx, style: str, text: str, size: int, max_width: float, floor: int = 24):
    """The largest font no bigger than `size` that sets `text` on one line in `max_width`."""
    while size > floor and _text_width(ctx.font(style, size), text) > max_width:
        size -= 4
    return ctx.font(style, size)


def _solid(ctx, color):
    key = ("solid", color)
    if key not in ctx.cache:
        ctx.cache[key] = ctx.Image.new("RGB", (WIDTH, HEIGHT), color)
    return ctx.cache[key]


def _vertical_gradient(ctx, top, bottom):
    key = ("vgrad", top, bottom)
    if key not in ctx.cache:
        column = ctx.Image.new("RGB", (1, HEIGHT))
        column.putdata([_mix(top, bottom, y / (HEIGHT - 1)) for y in range(HEIGHT)])
        ctx.cache[key] = column.resize((WIDTH, HEIGHT), ctx.Image.NEAREST)
    return ctx.cache[key].copy()


def _dark_background(ctx):
    return _vertical_gradient(ctx, P["DEEP"], P["OBSIDIAN"])


def _ember_strip(ctx, width: int, height: int, vertical: bool = False):
    """The brand's ember gradient (hot to amber) as a strip."""
    width, height = max(1, int(width)), max(1, int(height))
    key = ("ember", width, height, vertical)
    if key not in ctx.cache:
        n = height if vertical else width
        if vertical:
            strip = ctx.Image.new("RGB", (1, n))
        else:
            strip = ctx.Image.new("RGB", (n, 1))
        strip.putdata([_mix(P["EMBER_HOT"], P["EMBER_END"], i / max(1, n - 1))
                       for i in range(n)])
        ctx.cache[key] = strip.resize((width, height), ctx.Image.NEAREST)
    return ctx.cache[key]


def _heading(ctx, draw, img, title: str, y: int = 90) -> None:
    font = _fit_font(ctx, "bold", title, 64, WIDTH - 320)
    _draw_text(draw, 160, y, title, font, P["WHITE"])
    img.paste(_ember_strip(ctx, 180, 8), (160, y + _line_height(font) + 10))


# --------------------------------------------------------------------------- #
# Drawers: one per scene type. Each returns the frame at `t` seconds into the scene.
# --------------------------------------------------------------------------- #
def _draw_title_card(ctx, ps, t):
    data = ps.data
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    rise = (1 - _ease(t / 0.8)) * 40
    eyebrow = ctx.font("bold", 32)
    title_font = ctx.font("bold", 96)
    body = ctx.font("regular", 48)
    title = wrap_text(title_font, data.get("module", ""), 1500)[:3]
    highlight = wrap_text(body, data.get("highlight", ""), 1400)[:3]
    block = (_line_height(eyebrow) + 30 + _line_height(title_font) * len(title) + 50
             + _line_height(body) * len(highlight))
    y = (880 - block) / 2 + rise
    _draw_text(draw, WIDTH / 2, y, "S E N Z I N G   B O O T C A M P", eyebrow, P["EMBER_HOT"],
               "center")
    y += _line_height(eyebrow) + 30
    y = _draw_lines(draw, WIDTH / 2, y, title, title_font, P["WHITE"], "center")
    bar = int(360 * _ease((t - 0.3) / 0.9))
    if bar > 0:
        img.paste(_ember_strip(ctx, bar, 8), (int(WIDTH / 2 - bar / 2), int(y + 12)))
    fade = _ease((t - 0.5) / 0.8)
    _draw_lines(draw, WIDTH / 2, y + 50, highlight, body,
                _mix(P["OBSIDIAN"], MUTED_ON_DARK, fade), "center")
    return img


def _draw_image(ctx, ps, t):
    source = ctx.cache.get(("image", ps.index))
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    win_x, win_y, win_w, win_h = 200, 40, 1520, 855
    sw, sh = source.size
    target = win_w / win_h
    if sw / sh > target:           # wider than the window: crop the sides
        base_h, base_w = sh, sh * target
    else:                          # taller: crop top and bottom
        base_w, base_h = sw, sw / target
    p = t / max(ps.duration, 0.001)
    zoom = 1.0 + 0.10 * _ease(p)
    box_w, box_h = base_w / zoom, base_h / zoom
    # Pan: drift across the slack the crop leaves; tall pages drift downwards.
    slack_x, slack_y = sw - box_w, sh - box_h
    if sw / sh > target:
        x0 = _lerp(slack_x * 0.35, slack_x * 0.65, p)
        y0 = slack_y / 2
    else:
        x0 = slack_x / 2
        y0 = _lerp(0, min(slack_y, box_h * 0.6), p)
    frame = source.resize((win_w, win_h), ctx.Image.BILINEAR,
                          box=(x0, y0, x0 + box_w, y0 + box_h))
    img.paste(frame, (win_x, win_y))
    draw.rectangle((win_x - 2, win_y - 2, win_x + win_w + 1, win_y + win_h + 1),
                   outline=_mix(P["OBSIDIAN"], P["WHITE"], 0.18), width=2)
    heading = ps.data.get("heading")
    if heading:
        font = ctx.font("bold", 34)
        pad = 18
        w = _text_width(font, heading) + 2 * pad
        draw.rounded_rectangle((win_x + 24, win_y + 24, win_x + 24 + w,
                                win_y + 24 + _line_height(font) + 16), radius=10,
                               fill=P["EMBER_HOT"])
        _draw_text(draw, win_x + 24 + pad, win_y + 30, heading, font, P["WHITE"])
    return img


def _draw_counter(ctx, ps, t):
    data = ps.data
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    _heading(ctx, draw, img, data["title"])
    items = data["items"]
    fills = source_fills([i["label"] for i in items])
    top, bottom = 260, 860
    row = min(120, (bottom - top) / len(items))
    bar_h = row * 0.56
    label_font = ctx.font("bold", max(24, min(40, int(row * 0.34))))
    value_font = ctx.font("bold", max(24, min(44, int(row * 0.38))))
    peak = max((i["value"] for i in items), default=0) or 1
    bar_x, bar_max = 620, 1060
    grow = max(0.6, 0.65 * ps.duration)
    unit = data.get("unit", "")
    for n, item in enumerate(items):
        y = top + n * row
        p = _ease((t - 0.2 - n * 0.12) / grow)
        label = item["label"]
        lf = _fit_font(ctx, "bold", label, label_font.size, 420, 20)
        _draw_text(draw, bar_x - 30, y + (bar_h - _line_height(lf)) / 2 + 4, label, lf,
                   P["WHITE"], "right")
        length = bar_max * item["value"] / peak * p
        draw.rounded_rectangle((bar_x, y, bar_x + bar_max, y + bar_h), radius=8,
                               fill=P["SURFACE_DARK"])
        if length >= 2:
            draw.rounded_rectangle((bar_x, y, bar_x + length, y + bar_h), radius=8,
                                   fill=fills[n])
        shown = item["value"] * p
        text = _format_number(shown if isinstance(item["value"], float) else round(shown))
        _draw_text(draw, bar_x + length + 20, y + (bar_h - _line_height(value_font)) / 2 + 4,
                   f"{text}{(' ' + unit) if unit else ''}", value_font, MUTED_ON_DARK)
    return img


def _chip(ctx, draw, x0, y0, x1, y1, text, fill, outline, ink, visible):
    fill = _mix(P["OBSIDIAN"], fill, visible)
    outline = _mix(P["OBSIDIAN"], outline, visible)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=fill, outline=outline, width=3)
    font = _fit_font(ctx, "regular", text, int(min(34, (y1 - y0) * 0.5)), x1 - x0 - 40, 18)
    _draw_text(draw, (x0 + x1) / 2, y0 + ((y1 - y0) - _line_height(font)) / 2 + 3, text, font,
               _mix(P["OBSIDIAN"], ink, visible), "center")


def _draw_mapping(ctx, ps, t):
    data = ps.data
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    _heading(ctx, draw, img, data.get("title") or f"Mapping {data['source']} to Senzing")
    fields = data["fields"]
    label = ctx.font("bold", 30)
    _draw_text(draw, 480, 250, data["source"].upper(), label, P["EMBER_HOT"], "center")
    _draw_text(draw, 1440, 250, "SENZING ATTRIBUTES", label, P["EMBER_HOT"], "center")
    top, bottom = 320, 870
    row = min(100, (bottom - top) / len(fields))
    chip_h = row * 0.72
    step = min(0.7, 0.7 * ps.duration / len(fields))
    for n, pair in enumerate(fields):
        y = top + n * row
        start = 0.3 + n * step
        left = _ease((t - start) / 0.25)
        travel = _clamp((t - start - 0.2) / 0.6)
        right = _ease((t - start - 0.8) / 0.25)
        _chip(ctx, draw, 200, y, 760, y + chip_h, pair["from"], P["SURFACE_DARK"],
              _mix(P["OBSIDIAN"], P["WHITE"], 0.25), P["WHITE"], left)
        x_from, x_to, cy = 760, 1160, y + chip_h / 2
        if travel > 0:
            x_dot = _lerp(x_from, x_to, _ease(travel))
            draw.line((x_from, cy, x_dot, cy), fill=_mix(P["OBSIDIAN"], P["EMBER_CORE"], 0.6),
                      width=4)
            if travel < 1:
                draw.ellipse((x_dot - 10, cy - 10, x_dot + 10, cy + 10), fill=P["EMBER_HOT"])
        _chip(ctx, draw, 1160, y, 1720, y + chip_h, pair["to"], P["SURFACE_DARK"],
              P["EMBER_CORE"], P["WHITE"], right)
    return img


def _particles(ctx, ps, count, seed_offset):
    key = ("particles", ps.index)
    if key not in ctx.cache:
        rng = random.Random(1000 * (ps.index + 1) + seed_offset)
        ctx.cache[key] = [(rng.uniform(470, 810), rng.uniform(-60, 60), rng.randrange(12),
                           rng.uniform(0, 1)) for _ in range(count)]
    return ctx.cache[key]


def _draw_loading(ctx, ps, t):
    data = ps.data
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    title = data.get("title") or (f"Loading {data['source']}" if data.get("source")
                                  else "Loading records")
    _heading(ctx, draw, img, title)
    dur = ps.duration
    label = ctx.font("bold", 26)
    big = ctx.font("bold", 72)
    records = data["records"] * _ease(t / max(0.5, 0.8 * dur))
    entities = data["entities"] * _ease((t - 0.3) / max(0.5, 0.8 * dur))
    _draw_text(draw, 160, 250, "RECORDS LOADED", label, MUTED_ON_DARK)
    _draw_text(draw, 160, 285, _format_number(round(records)), big, P["WHITE"])
    _draw_text(draw, 1760, 250, "ENTITIES RESOLVED", label, MUTED_ON_DARK, "right")
    _draw_text(draw, 1760, 285, _format_number(round(entities)), big, P["SIGNAL_GREEN"],
               "right")
    # The source: a stack of records on the left.
    draw.rounded_rectangle((160, 440, 440, 840), radius=16, fill=P["SURFACE_DARK"],
                           outline=_mix(P["OBSIDIAN"], P["WHITE"], 0.2), width=2)
    for k in range(7):
        yy = 470 + k * 52
        draw.rounded_rectangle((190, yy, 410, yy + 34), radius=6,
                               fill=_mix(P["SURFACE_DARK"], P["EMBER_CORE"], 0.35))
    # Twelve entity bins on the right, filling as records arrive.
    bins = [(1240 + (k % 4) * 130, 460 + (k // 4) * 130) for k in range(12)]
    particles = _particles(ctx, ps, 48, 1)
    spawn_span = max(0.3, 0.7 * dur - 1.0)
    flight = min(1.0, max(0.3, 0.3 * dur))
    arrived = [0] * 12
    in_flight = []
    for j, (y_start, wobble, target, jitter) in enumerate(particles):
        start = 0.2 + (j + jitter) / len(particles) * spawn_span
        f = (t - start) / flight
        if f >= 1:
            arrived[target] += 1
        elif f > 0:
            in_flight.append((y_start, wobble, target, f))
    most = max(4, max(arrived))
    for k, (bx, by) in enumerate(bins):
        fill = _mix(P["SURFACE_DARK"], P["SIGNAL_GREEN"], 0.25 + 0.75 * arrived[k] / most
                    if arrived[k] else 0)
        draw.rounded_rectangle((bx, by, bx + 100, by + 100), radius=20, fill=fill,
                               outline=_mix(P["OBSIDIAN"], P["WHITE"], 0.2), width=2)
    for y_start, wobble, target, f in in_flight:
        bx, by = bins[target]
        e = _ease(f)
        x = _lerp(440, bx + 50, e)
        y = _lerp(y_start, by + 50, e) + math.sin(f * math.pi) * wobble
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=P["EMBER_CORE"])
    return img


def _draw_entity_merge(ctx, ps, t):
    data = ps.data
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    _heading(ctx, draw, img, data.get("title") or "Records resolve into entities")
    sub = ctx.font("bold", 44)
    _draw_text(draw, 160, 210, f"{_format_number(data['records'])} records  →  "
               f"{_format_number(data['entities'])} entities", sub, MUTED_ON_DARK)
    clusters = max(1, min(data["entities"], 5))
    dots = max(clusters, min(data["records"], 36))
    key = ("merge", ps.index)
    if key not in ctx.cache:
        rng = random.Random(2000 * (ps.index + 1))
        centers = [(360 + 1200 * (k + 0.5) / clusters, 590) for k in range(clusters)]
        members = [[d for d in range(dots) if d % clusters == k] for k in range(clusters)]
        layout = []
        sources = data.get("sources") or []
        fills = source_fills(sources) if sources else [P["EMBER_CORE"]]
        for k, group in enumerate(members):
            radius = min(110, 22 * math.sqrt(len(group)) + 14)
            for m, d in enumerate(group):
                angle = 2 * math.pi * m / max(1, len(group))
                end = (centers[k][0] + radius * math.cos(angle),
                       centers[k][1] + radius * math.sin(angle)) if len(group) > 1 \
                    else centers[k]
                start = (rng.uniform(180, 1740), rng.uniform(320, 860))
                layout.append((start, end, k, fills[d % len(fills)]))
        ctx.cache[key] = (centers, layout)
    centers, layout = ctx.cache[key]
    p = _ease((t - 0.3) / max(0.5, 0.55 * ps.duration))
    if p > 0.5:
        line = _mix(P["OBSIDIAN"], P["WARM_LINE"], (p - 0.5) * 0.7)
        for start, end, k, _fill in layout:
            x = _lerp(start[0], end[0], p)
            y = _lerp(start[1], end[1], p)
            draw.line((x, y, centers[k][0], centers[k][1]), fill=line, width=2)
    if p > 0.85:
        ring = _mix(P["OBSIDIAN"], P["SIGNAL_GREEN"], (p - 0.85) / 0.15)
        for k, (cx, cy) in enumerate(centers):
            count = sum(1 for item in layout if item[2] == k)
            radius = min(110, 22 * math.sqrt(count) + 14) + 34
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=ring,
                         width=6)
    for start, end, _k, fill in layout:
        x = _lerp(start[0], end[0], p)
        y = _lerp(start[1], end[1], p)
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=fill)
    return img


def _draw_certificate(ctx, ps, t):
    key = ("certificate", ps.index)
    if key not in ctx.cache:
        ctx.cache[key] = _certificate_face(ctx, ps.data["certificate"])
    return ctx.cache[key].copy()


def _certificate_face(ctx, cert: "CertificateFields"):
    img = ctx.Image.new("RGB", (WIDTH, HEIGHT), P["WARM_OFF_WHITE"])
    img.paste(_ember_strip(ctx, 150, HEIGHT, vertical=True), (0, 0))
    draw = ctx.ImageDraw.Draw(img)
    x0, y0, x1, y1 = 230, 40, 1860, 895
    draw.rectangle((x0, y0, x1, y1), fill=P["WHITE"], outline=P["WARM_LINE"], width=3)
    draw.rectangle((x0 + 16, y0 + 16, x1 - 16, y1 - 16), outline=P["WARM_LINE"], width=1)
    cx = (x0 + x1) / 2
    width = x1 - x0 - 200
    text = cert.text
    y = 82
    _draw_text(draw, cx, y, " ".join(text["eyebrow"]), ctx.font("bold", 26), P["EMBER_CORE"],
               "center")
    y += 50
    _draw_text(draw, cx, y, text["headline"], _fit_font(ctx, "bold", text["headline"], 80,
                                                        width), P["DARK_INK"], "center")
    y += 128
    _draw_text(draw, cx, y, text["presented"], ctx.font("bold", 22), MUTED_ON_LIGHT, "center")
    y += 42
    name_font = _fit_font(ctx, "bold", cert.name, 88, width, 36)
    _draw_text(draw, cx, y, cert.name, name_font, P["EMBER_CORE"], "center")
    y += _line_height(name_font) + 18
    draw.line((cx - 480, y, cx + 480, y), fill=P["WARM_LINE"], width=3)
    y += 26
    y = _draw_lines(draw, cx, y, wrap_text(ctx.font("regular", 30), cert.citation, 1300)[:3],
                    ctx.font("regular", 30), P["BODY_INK"], "center")
    modules = "  ·  ".join(cert.modules)
    if modules:
        for size in (28, 26, 24, 22, 20, 18):
            font = ctx.font("regular", size)
            lines = wrap_text(font, modules, 1400)
            if len(lines) * _line_height(font) <= 190 or size == 18:
                break
        _draw_lines(draw, cx, y + 14, lines, font, P["DARK_INK"], "center")
    label = ctx.font("bold", 20)
    value = ctx.font("bold", 30)
    for bx, caption, content in ((cx - 420, text["date_label"], cert.date),
                                 (cx + 420, text["issuer_label"], cert.issuer)):
        _draw_text(draw, bx, 740, content or "—", value, P["DARK_INK"], "center")
        draw.line((bx - 200, 786, bx + 200, 786), fill=P["WARM_LINE"], width=2)
        _draw_text(draw, bx, 798, caption, label, MUTED_ON_LIGHT, "center")
    if cert.colophon:
        _draw_text(draw, cx, 852, cert.colophon, ctx.font("regular", 20), MUTED_ON_LIGHT,
                   "center")
    return img


def _draw_tag_line(ctx, ps, t):
    img = _dark_background(ctx)
    draw = ctx.ImageDraw.Draw(img)
    text = ps.data["text"]
    font = ctx.font("bold", 96)
    prefix, sep, rest = text.partition(":")
    if sep and rest.strip():
        lines = [(prefix + sep, P["EMBER_HOT"], 0.2)]
        lines += [(line, P["WHITE"], 0.6) for line in wrap_text(font, rest.strip(), 1600)]
    else:
        lines = [(line, P["WHITE"], 0.3) for line in wrap_text(font, text, 1600)]
    lines = lines[:5]
    y = (860 - _line_height(font) * len(lines)) / 2
    for line, color, start in lines:
        _draw_text(draw, WIDTH / 2, y, line, font, _mix(P["OBSIDIAN"], color,
                                                         _ease((t - start) / 0.6)), "center")
        y += _line_height(font)
    bar = int(420 * _ease((t - 0.9) / 0.9))
    if bar > 0:
        img.paste(_ember_strip(ctx, bar, 10), (int(WIDTH / 2 - bar / 2), int(y + 24)))
    return img


#: THE TABLE. Every scene type, the data fields it carries, and the function that draws it.
#: Validation and drawing both read it, so a field cannot be validated and then ignored, or
#: drawn without having been validated.
SCENE_TYPES: Dict[str, SceneType] = {t.name: t for t in (
    SceneType("title_card", "a module name plus its highlight, for a module with nothing on "
              "screen",
              (F("module", "text"), F("highlight", "text", False)),
              _draw_title_card),
    SceneType("image", "a slow pan and zoom over a screenshot",
              (F("image", "image", help="project-relative path to a PNG or JPEG"),
               F("heading", "text", False),
               F("module", "text", False, help="used by the title-card fallback")),
              _draw_image),
    SceneType("counter", "animated bars and numbers, such as record counts per source",
              (F("title", "text"),
               F("items", "items", max_items=8,
                 item_fields=(F("label", "text"), F("value", "number"))),
               F("unit", "text", False)),
              _draw_counter),
    SceneType("mapping", "source fields flowing to Senzing attributes",
              (F("source", "text"),
               F("fields", "items", max_items=8,
                 item_fields=(F("from", "text"), F("to", "text"))),
               F("title", "text", False)),
              _draw_mapping),
    SceneType("loading", "records flowing into entities, with a rising counter",
              (F("records", "count"), F("entities", "count"), F("source", "text", False),
               F("title", "text", False)),
              _draw_loading, _entities_not_above_records),
    SceneType("entity_merge", "records converging into resolved entities",
              (F("records", "count", minimum=1), F("entities", "count", minimum=1),
               F("sources", "text_list", False, max_items=12), F("title", "text", False)),
              _draw_entity_merge, _entities_not_above_records),
    SceneType("certificate", "the Certificate of Completion, from the recap's own fields",
              (F("recap", "path", False, help=f"defaults to {DEFAULT_RECAP}"),
               F("preferences", "path", False, help=f"defaults to {DEFAULT_PREFERENCES}"),
               F("modules", "text_list", False,
                 help="used only when no recap can be read")),
              _draw_certificate),
    SceneType("tag_line", "the closing card",
              (F("text", "text", False,
                 help="defaults to 'Resolved: <bootcamper>, Senzing graduate.'"),),
              _draw_tag_line),
)}


# --------------------------------------------------------------------------- #
# The certificate's fields: the recap PDF's, read by the recap PDF's own code (INV-100)
# --------------------------------------------------------------------------- #
_CERT_TEXT_FALLBACK = {
    "eyebrow": "SENZING BOOTCAMP", "headline": "Certificate of Completion",
    "presented": "THIS CERTIFICATE IS PROUDLY PRESENTED TO",
    "date_label": "DATE COMPLETED", "issuer_label": "ISSUED BY",
}


@dataclass
class CertificateFields:
    name: str
    date: str
    modules: List[str]
    citation: str
    issuer: str
    colophon: str
    text: Dict[str, str]
    source: str


def _recap_module():
    try:
        return importlib.import_module("generate_recap_pdf"), None
    except Exception as exc:
        return None, str(exc)


def certificate_fields(scene: dict, video: dict, root: Path,
                       note: Callable[[str], None]) -> CertificateFields:
    """The name, date and module list the recap PDF's certificate prints.

    Read from the recap by ``generate_recap_pdf``'s own parser, with the preferences name
    outranking the recap header as it does there, so the two certificates cannot disagree.
    Only when no recap can be read does the storyboard supply them, and stderr says so.
    """
    rp, import_error = _recap_module()
    text = dict(_CERT_TEXT_FALLBACK)
    if rp is not None:
        text.update({
            "eyebrow": rp._CERT_EYEBROW, "headline": rp._CERT_HEADLINE,
            "presented": rp._CERT_PRESENTED, "date_label": rp._CERT_DATE_LABEL,
            "issuer_label": rp._CERT_ISSUER_LABEL,
        })
    recap_rel = scene.get("recap", DEFAULT_RECAP)
    prefs_rel = scene.get("preferences", DEFAULT_PREFERENCES)
    recap_path = root / recap_rel
    why = None
    if rp is None:
        why = f"generate_recap_pdf.py could not be imported ({import_error})"
    elif not recap_path.is_file():
        why = f"no recap at {recap_rel}"
    else:
        try:
            source = recap_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            why = f"the recap at {recap_rel} could not be read ({exc})"
    if why is None:
        recap = rp.parse_recap(source)
        rp.set_certificate_name_override(rp.read_preferences_name(root / prefs_rel))
        try:
            name, date, labels = rp._cert_fields(recap)
            attribution = rp._cert_attribution(recap)
            citation = rp._cert_citation(labels)
        finally:
            rp.set_certificate_name_override("")
        if name == rp.CERTIFICATE_NAME_PLACEHOLDER:
            note(f"the recap at {recap_rel} carries no printable Bootcamper name, so the "
                 f"certificate shows the placeholder {name!r}, as the recap PDF's does.")
        if name != video.get("bootcamper", name):
            _report("NOTE", f"the storyboard names {video.get('bootcamper')!r}, but the "
                    f"certificate prints {name!r}: it takes the name the recap PDF's "
                    "certificate prints.")
        return CertificateFields(name, date, labels, citation, attribution[0],
                                 attribution[1] if len(attribution) > 1 else "", text,
                                 f"from {recap_rel}")
    note(f"{why}; the certificate uses the storyboard's name and date"
         + (" and module list" if scene.get("modules") else " and names no modules")
         + ", so it may not match the recap PDF's certificate.")
    labels = list(scene.get("modules") or [])
    raw_date = video.get("graduation_date", "")
    date = rp._format_date(raw_date) if rp is not None else raw_date
    if rp is not None:
        citation = rp._cert_citation(labels)
    else:
        citation = "for successfully completing the Senzing Bootcamp."
    return CertificateFields(video.get("bootcamper", ""), date, labels, citation,
                             "Senzing Bootcamp", "", text, "from the storyboard")


# --------------------------------------------------------------------------- #
# The timeline
# --------------------------------------------------------------------------- #
@dataclass
class PlannedScene:
    index: int
    type: str                       # the type as written
    kind: str                       # the drawer used (a title card for a missing image)
    data: dict
    planned: float
    duration: float
    frames: int
    caption: str
    narration_seconds: float
    voiced: bool
    pcm: bytes = b""
    chunks: List[str] = field(default_factory=list)
    is_last: bool = False

    @property
    def label(self) -> str:
        return f"scenes[{self.index}] ({self.type})"


def _load_image(ctx, path: Path):
    with ctx.Image.open(path) as handle:
        handle.load()
        return handle.convert("RGB")


def caption_chunks(ctx, caption: str) -> List[str]:
    """The caption split into screens of at most CAPTION_LINES lines."""
    font = ctx.font("regular", CAPTION_SIZE)
    lines = wrap_text(font, caption, CAPTION_MAX_WIDTH)
    return ["\n".join(lines[i:i + CAPTION_LINES])
            for i in range(0, len(lines), CAPTION_LINES)] or [""]


def plan_timeline(storyboard: dict, ctx: RenderContext, engine: Optional[SpeechEngine],
                  ffmpeg: Optional[str], workdir: Optional[Path],
                  voices: Optional[Sequence[bytes]] = None) -> List[PlannedScene]:
    """Resolve fallbacks, synthesize narration, and fix every scene's length.

    `voices`, when given, is every scene's narration already voiced by the voice-selection
    stage (``voice_with_piper``), and nothing is synthesized here. A scene lasts
    max(planned, narration + lead + tail), so narration is never cut; each extension is
    reported on stderr as an OVERRUN.
    """
    video = storyboard["video"]
    plan: List[PlannedScene] = []
    scenes = storyboard["scenes"]
    for index, scene in enumerate(scenes):
        kind = scene["type"]
        data = {k: v for k, v in scene.items() if not k.startswith("_")}
        label = f"scenes[{index}] ({kind})"
        if kind == "image":
            path = ctx.root / scene["image"]
            problem = None
            if not path.is_file():
                problem = f"image {scene['image']} not found"
            else:
                try:
                    ctx.cache[("image", index)] = _load_image(ctx, path)
                except Exception as exc:
                    problem = f"image {scene['image']} could not be read ({exc})"
            if problem:
                ctx.note(f"{label}: {problem}; drawing a title card instead.")
                kind = "title_card"
                data = {"module": scene.get("module") or scene.get("heading")
                        or "Senzing Bootcamp", "highlight": scene.get("heading", "")
                        if scene.get("module") else ""}
        elif kind == "certificate":
            data["certificate"] = certificate_fields(scene, video, ctx.root, ctx.note)
        elif kind == "tag_line" and not scene.get("text"):
            data["text"] = f"Resolved: {video['bootcamper']}, Senzing graduate."
        narration = scene["narration"]
        caption = scene.get("caption") or narration
        pcm, voiced = b"", False
        if voices is not None:
            pcm, voiced = voices[index], True
        elif engine is not None and ffmpeg and workdir is not None:
            try:
                pcm = synthesize_pcm(engine, narration, ffmpeg, workdir, f"scene-{index:03d}")
                voiced = True
            except RuntimeError as exc:
                ctx.note(f"{label}: {engine.name} could not voice this narration ({exc}); "
                         "the scene is silent and its caption carries the narration.")
        spoken = len(pcm) / 2 / AUDIO_RATE if voiced else estimated_narration_seconds(narration)
        planned = float(scene["duration"])
        needed = NARRATION_LEAD + spoken + NARRATION_TAIL
        duration = max(planned, needed)
        frames = max(1, math.ceil(duration * FPS - 1e-9))
        if needed > planned:
            how = ("" if voiced else
                   f", estimated at {WORDS_PER_MINUTE} words a minute with no voice")
            _report("OVERRUN", f"{label}: the narration needs {needed:.1f} s ({spoken:.1f} s "
                    f"spoken{how}, plus {NARRATION_LEAD + NARRATION_TAIL:g} s of lead and "
                    f"tail), more than the planned {planned:g} s; the scene is extended to "
                    f"{frames / FPS:.1f} s so nothing is cut.")
        plan.append(PlannedScene(index, scene["type"], kind, data, planned, frames / FPS,
                                 frames, caption, spoken, voiced, pcm,
                                 caption_chunks(ctx, caption)))
    if plan:
        plan[-1].is_last = True
    return plan


def _stereo(mono: bytes) -> bytes:
    """Mono signed 16-bit PCM -> the same sound on both channels, interleaved."""
    samples = array.array("h", mono)
    both = array.array("h", bytes(2 * len(mono)))
    both[0::2] = samples
    both[1::2] = samples
    return both.tobytes()


def _wav_writer(path: Path):
    out = wave.open(str(path), "wb")
    out.setnchannels(AUDIO_CHANNELS)
    out.setsampwidth(2)
    out.setframerate(AUDIO_RATE)
    return out


def write_audio_track(plan: Sequence[PlannedScene], path: Path) -> None:
    """One 48 kHz stereo WAV for the whole video, each narration at its scene's start + lead."""
    lead = int(NARRATION_LEAD * AUDIO_RATE) * 2
    with _wav_writer(path) as out:
        for ps in plan:
            size = ps.frames * SAMPLES_PER_FRAME * 2
            body = (b"\0" * lead + ps.pcm)[:size]
            out.writeframes(_stereo(body + b"\0" * (size - len(body))))


# --------------------------------------------------------------------------- #
# The music bed: synthesized with the standard library, mixed in the encode's ffmpeg call
# --------------------------------------------------------------------------- #
#: The bed's level before the mix, how the voice ducks it, and the one loudness target
#: every audio stream is normalized to, with a voice or without one.
MUSIC_VOLUME = 0.3
DUCKING = "sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"
#: A compressor keyed on the voice itself, applied to every voiced stream before anything
#: else (#372). Speech peaks high above its loudness: a ducked mix of real narration peaks
#: about 18 dB over its integrated level, more than the 14.5 dB between LOUDNORM's -16 LUFS
#: and its -1.5 dBTP ceiling, so loudnorm had to limit and landed near -17.6 LUFS. Leveling
#: the voice lowers that ratio, and the mix reaches the target.
LEVELER = ("asplit=2[lv][lk];"
           "[lv][lk]sidechaincompress=threshold=0.05:ratio=4:attack=5:release=150:makeup=1")

MUSIC_BPM = 120
MUSIC_FADE_IN = 2.0
MUSIC_FADE_OUT = 3.0
#: I-V-vi-IV in C major, one chord a bar: four 2 s bars at 120 BPM make the 8 s cycle the
#: bed repeats. MIDI note numbers.
MUSIC_PROGRESSION = ((60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60))


def _hz(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def _music_cycle() -> array.array:
    """One cycle of the progression as interleaved stereo 16-bit samples.

    Pads hold each chord, a decaying bass hits every beat, a soft arpeggio walks the chord in
    eighth notes panned left and right, and a light kick marks each beat. Every note ramps in
    and out, so the cycle joins itself without a click when it repeats.
    """
    rate = AUDIO_RATE
    beat = 60.0 / MUSIC_BPM
    bar = 4 * beat
    frames = round(len(MUSIC_PROGRESSION) * bar * rate)
    left = [0.0] * frames
    right = [0.0] * frames

    def note(start, seconds, hz, gain, pan, attack, release, decay=0.0, drop=0.0):
        """A sine at `hz` from `start`; `pan` 0 is left and 1 right; `drop` sweeps it down."""
        first, count = round(start * rate), round(seconds * rate)
        gl = gain * math.cos(pan * math.pi / 2)
        gr = gain * math.sin(pan * math.pi / 2)
        rise, fall = max(1, round(attack * rate)), max(1, round(release * rate))
        fade = math.exp(-decay / rate)
        settle = math.exp(-30.0 / rate)
        step = 2 * math.pi / rate
        phase, level, sweep = 0.0, 1.0, 1.0
        for j in range(count):
            env = level * min(1.0, j / rise, (count - j) / fall)
            value = env * math.sin(phase)
            left[first + j] += gl * value
            right[first + j] += gr * value
            phase += step * hz * (1.0 + drop * sweep)
            level *= fade
            sweep *= settle

    for n, chord in enumerate(MUSIC_PROGRESSION):
        start = n * bar
        for pitch in chord:
            note(start, bar, _hz(pitch), 0.09, 0.5, 0.25, 0.25, decay=0.4)
        for b in range(4):
            note(start + b * beat, beat, _hz(chord[0] - 24), 0.30, 0.5, 0.005, 0.02, decay=5.0)
            note(start + b * beat, 0.25, 50.0, 0.35, 0.5, 0.002, 0.03, decay=14.0, drop=1.6)
        arpeggio = (chord[0], chord[1], chord[2], chord[1] + 12)
        for e in range(8):
            note(start + e * beat / 2, beat / 2, _hz(arpeggio[e % 4] + 12), 0.08,
                 0.25 if e % 2 == 0 else 0.75, 0.005, 0.03, decay=6.0)

    peak = max(max(map(abs, left)), max(map(abs, right))) or 1.0
    scale = 0.5 * 32767 / peak
    samples = array.array("h", bytes(4 * frames))
    samples[0::2] = array.array("h", [round(v * scale) for v in left])
    samples[1::2] = array.array("h", [round(v * scale) for v in right])
    return samples


def synthesize_music_bed(seconds: float) -> bytes:
    """`seconds` of the music bed: 48 kHz stereo 16-bit PCM, deterministic for a length.

    One cycle is synthesized and repeated to the length, then faded in over MUSIC_FADE_IN and
    out over MUSIC_FADE_OUT across the whole bed. Standard library only.
    """
    frames = max(0, round(seconds * AUDIO_RATE))
    cycle = _music_cycle()
    cycle_frames = len(cycle) // AUDIO_CHANNELS
    bed = cycle * (frames // cycle_frames + 1)
    del bed[frames * AUDIO_CHANNELS:]
    fade_in = min(frames, round(MUSIC_FADE_IN * AUDIO_RATE))
    fade_out = min(frames, round(MUSIC_FADE_OUT * AUDIO_RATE))
    for i in range(fade_in):
        gain = i / fade_in
        for c in (2 * i, 2 * i + 1):
            bed[c] = round(bed[c] * gain)
    for k in range(fade_out):
        i = frames - 1 - k
        gain = k / fade_out
        for c in (2 * i, 2 * i + 1):
            bed[c] = round(bed[c] * gain)
    return bed.tobytes()


def write_music_bed(seconds: float, path: Path) -> None:
    """The music bed for a `seconds`-long video, as a 48 kHz stereo WAV."""
    with _wav_writer(path) as out:
        out.writeframes(synthesize_music_bed(seconds))


def audio_filter_graph(voice: Optional[int], music: Optional[int]) -> Optional[str]:
    """The ``-filter_complex`` graph for ffmpeg's audio inputs, ending at ``[aout]``.

    `voice` and `music` are ffmpeg input indexes, or None when that input is absent. The voice
    is leveled first (LEVELER). The music is lowered to MUSIC_VOLUME and ducked by a compressor
    keyed on the leveled voice, mixed with it, and the mix is loudness-normalized. A lone voice
    (leveled) or a lone music bed goes through the same ``loudnorm``, so every audio stream has
    one target. None when there is no audio.
    """
    if voice is not None and music is not None:
        return (f"[{music}:a]volume={MUSIC_VOLUME}[music];"
                f"[{voice}:a]{LEVELER},asplit=2[key][voice];"
                f"[music][key]{DUCKING}[ducked];"
                f"[ducked][voice]amix=inputs=2:duration=first,{LOUDNORM}[aout]")
    if voice is not None:
        return f"[{voice}:a]{LEVELER},{LOUDNORM}[aout]"
    if music is None:
        return None
    return f"[{music}:a]{LOUDNORM}[aout]"


# --------------------------------------------------------------------------- #
# Frames
# --------------------------------------------------------------------------- #
def caption_at(ps: PlannedScene, t: float) -> str:
    """The caption screen showing at `t`, paced across the narration by word count."""
    chunks = ps.chunks
    if len(chunks) <= 1:
        return chunks[0] if chunks else ""
    start = NARRATION_LEAD
    end = start + ps.narration_seconds
    if end <= start:
        start, end = 0.0, ps.duration
    weights = [max(1, _word_count(c)) for c in chunks]
    position = _clamp((t - start) / (end - start)) * sum(weights)
    for chunk, weight in zip(chunks, weights):
        if position < weight:
            return chunk
        position -= weight
    return chunks[-1]


def burn_caption(ctx, img, text: str) -> None:
    """Draw `text` as a caption on a dark band at the foot of the frame."""
    if not text.strip():
        return
    font = ctx.font("regular", CAPTION_SIZE)
    lines = text.split("\n")
    line_h = _line_height(font)
    pad_x, pad_y = 36, 20
    width = int(max(_text_width(font, line) for line in lines)) + 2 * pad_x
    height = line_h * len(lines) + 2 * pad_y
    x0 = (WIDTH - width) // 2
    y0 = CAPTION_BOTTOM - height
    box = (x0, y0, x0 + width, CAPTION_BOTTOM)
    region = img.crop(box)
    band = ctx.Image.blend(region, ctx.Image.new("RGB", region.size, P["OBSIDIAN"]), 0.8)
    img.paste(band, box[:2])
    draw = ctx.ImageDraw.Draw(img)
    _draw_lines(draw, WIDTH / 2, y0 + pad_y, lines, font, P["WHITE"], "center")


def frame_image(ctx: RenderContext, ps: PlannedScene, t: float):
    """The finished frame for `ps` at `t` seconds into it: drawing, fades and caption."""
    img = SCENE_TYPES[ps.kind].draw(ctx, ps, t)
    if img.size != (WIDTH, HEIGHT) or img.mode != "RGB":
        img = img.convert("RGB").resize((WIDTH, HEIGHT))
    black = _solid(ctx, P["OBSIDIAN"])
    if t < FADE_IN:
        img = ctx.Image.blend(black, img, _ease(t / FADE_IN))
    if ps.is_last and ps.duration - t < FADE_OUT:
        img = ctx.Image.blend(black, img, _clamp((ps.duration - t) / FADE_OUT))
    burn_caption(ctx, img, caption_at(ps, t))
    return img


def render_scene_frame(storyboard: dict, index: int, t: float, project_root=".",
                       pil=None):
    """The frame for scene `index` at `t` seconds, as a PIL image. No ffmpeg, no voice.

    The drawing layer's test seam: it validates, plans the timeline silently, and draws.
    """
    root = Path(project_root).resolve()
    errors = validate_storyboard(storyboard, root)
    if errors:
        raise ValueError("; ".join(errors))
    ctx = RenderContext(pil or load_pillow(), storyboard["video"], root)
    plan = plan_timeline(storyboard, ctx, None, None, None)
    return frame_image(ctx, plan[index], t)


# --------------------------------------------------------------------------- #
# Encoding: raw RGB frames streamed into one ffmpeg
# --------------------------------------------------------------------------- #
def encode_command(ffmpeg: str, audio: Optional[Path], output: Path,
                   music: Optional[Path] = None) -> List[str]:
    """The one ffmpeg call: frames on stdin, the narration and the music bed mixed in."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
           "-framerate", str(FPS), "-i", "pipe:0"]
    inputs = [p for p in (audio, music) if p is not None]
    for path in inputs:
        cmd += ["-i", str(path)]
    graph = audio_filter_graph(1 if audio is not None else None,
                               len(inputs) if music is not None else None)
    cmd += ["-map", "0:v:0"]
    if graph is not None:
        cmd += ["-filter_complex", graph, "-map", "[aout]", "-c:a", "aac", "-b:a", "160k",
                "-ar", str(AUDIO_RATE), "-ac", str(AUDIO_CHANNELS)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-movflags", "+faststart", "-f", "mp4", str(output)]
    return cmd


def stream_frames(ctx, plan, ffmpeg: str, audio: Optional[Path], output: Path,
                  log_path: Path, music: Optional[Path] = None) -> Tuple[bool, str]:
    """Draw every frame and pipe it into ffmpeg. (succeeded, ffmpeg's complaint)."""
    with open(log_path, "wb") as log:
        try:
            proc = subprocess.Popen(encode_command(ffmpeg, audio, output, music),
                                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                    stderr=log)
        except OSError as exc:
            return False, f"could not start {ffmpeg}: {exc}"
        broken = False
        try:
            for ps in plan:
                _report("RENDER", f"{ps.label}: {ps.frames} frames ({ps.duration:.1f} s)")
                for n in range(ps.frames):
                    proc.stdin.write(frame_image(ctx, ps, n / FPS).tobytes())
        except BrokenPipeError:
            broken = True
        finally:
            try:
                proc.stdin.close()
            except BrokenPipeError:
                broken = True
            code = proc.wait()
    detail = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if code != 0 or broken:
        return False, (detail.splitlines()[-1] if detail else f"ffmpeg exited {code}")
    return True, ""


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def load_storyboard(path: Path) -> Tuple[Optional[dict], List[str]]:
    if not path.is_file():
        return None, [f"(document): no storyboard at {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except UnicodeDecodeError as exc:
        return None, [f"(document): {path} is not UTF-8 ({exc})"]
    except json.JSONDecodeError as exc:
        return None, [f"(document): {path} is not valid JSON (line {exc.lineno}, column "
                      f"{exc.colno}: {exc.msg})"]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the graduation storyboard into docs/bootcamp_recap.mp4.",
        epilog="Exit codes: 0 rendered; 1 invalid storyboard; 2 a required capability is "
               "missing (ffmpeg or Pillow); 3 the encode failed. Nothing is written unless 0.")
    parser.add_argument("--storyboard", default=DEFAULT_STORYBOARD)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--project-root", default=".",
                        help="images and the recap resolve against this (default: the "
                             "current directory)")
    parser.add_argument("--voice-model", default=None,
                        help="a local Piper .onnx voice model, its .onnx.json beside it "
                             f"(default: {DEFAULT_VOICE_MODEL} under --project-root)")
    parser.add_argument("--no-voice", action="store_true",
                        help="skip the voice-over; the burned-in captions carry the narration")
    parser.add_argument("--check", action="store_true",
                        help="validate the storyboard and exit; needs neither Pillow nor ffmpeg")
    parser.add_argument("--schema", action="store_true",
                        help="print the scene types and their fields as JSON, and exit")
    args = parser.parse_args(argv)

    if args.schema:
        print(json.dumps(schema_description(), indent=2))
        return EXIT_RENDERED

    root = Path(args.project_root).resolve()
    storyboard, errors = load_storyboard(Path(args.storyboard))
    if not errors:
        errors = validate_storyboard(storyboard, root)
    if errors:
        for problem in errors:
            _report("INVALID", problem)
        _report("ERROR", f"invalid storyboard ({len(errors)} problem(s)); no video written.")
        return EXIT_INVALID_STORYBOARD

    planned = sum(float(s["duration"]) for s in storyboard["scenes"])
    if args.check:
        print(f"Storyboard valid: {len(storyboard['scenes'])} scene(s), planned "
              f"{_format_duration(planned)} ({planned:.1f} s).")
        return EXIT_RENDERED

    try:
        pil = load_pillow()
        ffmpeg, ffmpeg_notes = find_ffmpeg()
    except CapabilityMissing as exc:
        _report("ERROR", f"{exc} No video written.")
        return EXIT_MISSING_CAPABILITY

    ctx = RenderContext(pil, storyboard["video"], root)
    for note in ffmpeg_notes:
        ctx.note(note)
    if PALETTE_NOTE:
        ctx.note(PALETTE_NOTE)

    piper = None
    if not args.no_voice:
        model = Path(args.voice_model) if args.voice_model else root / DEFAULT_VOICE_MODEL
        piper, piper_note = find_piper_voice(model)
        if piper_note:
            ctx.note(piper_note)
    engine = None

    with_music = storyboard["video"].get("music", True)
    output = Path(args.output)
    partial = output.with_name(f".{output.name}.partial")
    created_dir = None if output.parent.exists() else output.parent
    ok, detail = False, ""
    with tempfile.TemporaryDirectory(prefix="sbcp-video-") as tmp:
        workdir = Path(tmp)
        try:
            voices = (voice_with_piper(storyboard["scenes"], piper, ffmpeg, workdir, ctx.note)
                      if piper is not None else None)
            if voices is not None:
                engine = piper
            else:
                engine, voice_note = choose_voice(args.no_voice)
                if voice_note:
                    ctx.note(voice_note)
            plan = plan_timeline(storyboard, ctx, engine, ffmpeg, workdir, voices)
            voiced = [ps for ps in plan if ps.voiced]
            audio = music = None
            if voiced:
                audio = workdir / "narration.wav"
                write_audio_track(plan, audio)
            elif engine is not None:
                ctx.note(f"{engine.name} voiced no scene; the video has no voice-over and "
                         "the burned-in captions carry the narration.")
            if with_music:
                music = workdir / "music.wav"
                write_music_bed(sum(ps.frames for ps in plan) / FPS, music)
            elif not voiced:
                ctx.note("no voice, and the storyboard turns the music off (video.music: "
                         "false); the video has no audio stream.")
            output.parent.mkdir(parents=True, exist_ok=True)
            ok, detail = stream_frames(ctx, plan, ffmpeg, audio, partial,
                                       workdir / "ffmpeg.log", music)
            if ok:
                os.replace(partial, output)
        except Exception as exc:  # a render defect must not masquerade as exit 1
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        finally:
            if partial.exists():
                partial.unlink()
            if created_dir is not None and not output.exists():
                try:
                    created_dir.rmdir()
                except OSError:
                    pass
    if not ok:
        _report("ERROR", f"the video could not be rendered ({detail}); no video written.")
        return EXIT_RENDER_FAILED

    total = sum(ps.frames for ps in plan) / FPS
    print(f"Video generated: {output}")
    print(f"Duration: {_format_duration(total)} ({total:.1f} s, {len(plan)} scenes, planned "
          f"{planned:.1f} s)")
    if voiced:
        print(f"Voice: {engine.name} ({len(voiced)} of {len(plan)} scenes narrated)")
    elif args.no_voice:
        print("Voice: none (--no-voice)")
    elif engine is None:
        print("Voice: none (no speech engine found)")
    else:
        print(f"Voice: none ({engine.name} voiced no scene)")
    print("Music: yes" if with_music else "Music: off (storyboard)")
    return EXIT_RENDERED


if __name__ == "__main__":
    sys.exit(main())
