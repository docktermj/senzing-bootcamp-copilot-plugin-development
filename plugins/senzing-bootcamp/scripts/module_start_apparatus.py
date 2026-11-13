#!/usr/bin/env python3
"""Shared builder for the module-start apparatus reminder (#851, INV-420).

The module-start apparatus (the banner, journey map, before/after framing, step overview,
time estimate and model/effort nudge) is required at every content-module start and at
graduation, and only the model's attention enforced it: one session skipped it at five of
eight module starts. Two hooks now put a deterministic reminder into the guide's context at
the moment it is due:

- ``module-start-reminder.py`` (``userPromptSubmitted``), on the reply to a transition or
  graduation question;
- ``session-start.py`` (``sessionStart``), on a resume into a module that has not begun.

Both build the reminder here, so its wording is stated once and the two cannot drift
(INV-300). The rules it summarizes are owned by ``ground-rules.md`` ("Module start banners
and transitions"), ``module-completion.md`` (Step 4 and "Reaching graduation") and the
invariants cited in the text; this file only points the guide at them when they are due.

It also holds the finished-bootcamp rule, ``bootcamp_complete()`` (#905): the flag in either
the progress file or the preferences file, so every hook that asks "is the bootcamp over?"
reads the same answer.

It also holds each module's display name by state token (``DISPLAY_NAMES``, #874), so
``session-start.py`` names the recorded module in its resume message rather than leaving the
guide to improvise a name, which it did from the skill heading, number included (INV-079).

Every reminder is conditional, so it never turns a "not yet" into a module start, and it
is ASCII-only: ``session-start.py`` prints it as plain text, and a non-ASCII character on a
Windows console code page would raise instead of printing.

This is NOT a hook. Python puts each hook script's own directory (this ``scripts/``
directory) on ``sys.path``, so ``import module_start_apparatus`` resolves here on Linux,
macOS and Windows alike. Standard library only (INV-052). Nothing here raises on a missing,
empty or malformed progress or preferences file.
"""
import json
import os
import re

PROGRESS = os.path.join("config", "bootcamp_progress.json")
PREFERENCES = os.path.join("config", "bootcamp_preferences.yaml")

#: The apparatus-exempt setup modules, as normalized tokens: Bootcamp preparation (INV-075)
#: and Entity Resolution Concepts (INV-078). Matched against the state token
#: (``bootcamp_preparation``) and the display name ("Bootcamp preparation") alike.
EXEMPT = frozenset({"bootcamp_preparation", "entity_resolution_concepts"})

#: Graduation, which gets the INV-102 form rather than the module form.
GRADUATION = frozenset({"graduation", "bootcamp_graduation"})

#: Each module's display name by its state token, as the module table in
#: ``bootcamp-preparation/SKILL.md`` spells it (#874). That table is the source of truth
#: (INV-079); this copy exists because a hook cannot read a skill file cheaply on every
#: session start, and ``tests/test_resume_names_the_module.py`` fails the moment the two
#: differ, so a renamed or added module cannot drift here (INV-300). ``session-start.py``
#: names the recorded module with it, so the resume offer never has to improvise a name
#: from a skill heading that carries a number.
DISPLAY_NAMES = {
    "bootcamp_preparation": "Bootcamp preparation",
    "entity_resolution_concepts": "Entity Resolution Concepts",
    "business_problem": "Discover the Business Problem",
    "sdk_setup": "SDK setup",
    "system_verification": "System verification",
    "truthset_visualization": "Truth Set visualization",
    "data_collection": "Data collection",
    "data_quality_mapping": "Data Quality, Mapping, and Transformation",
    "data_processing": "Data processing",
    "query_visualize_discover": "Query, Visualize and Discover",
    "graduation": "Bootcamp graduation",
}

#: The display name the graduation offer starts.
GRADUATION_NAME = DISPLAY_NAMES["graduation"]


def token(module):
    """``module`` as a comparable token: lower case, runs of other characters as ``_``, and
    any leading skill-directory number (``module_00_``) dropped."""
    text = re.sub(r"[^a-z0-9]+", "_", str(module).lower()).strip("_")
    return re.sub(r"^module_\d+[a-z]?_", "", text)


def is_exempt(module):
    """True for an apparatus-exempt setup module (INV-075, INV-078)."""
    return token(module) in EXEMPT


def is_graduation(module):
    """True for Bootcamp graduation (INV-102)."""
    return token(module) in GRADUATION


def display_name(module):
    """The display name of ``module`` (a state token, a skill-directory name or a display
    name in any case), or None when it names no module in ``DISPLAY_NAMES``."""
    if not isinstance(module, str) or not module.strip():
        return None
    key = token(module)
    if key in GRADUATION:
        return GRADUATION_NAME
    if key in DISPLAY_NAMES:
        return DISPLAY_NAMES[key]
    for name in DISPLAY_NAMES.values():
        if token(name) == key:
            return name
    return None


def _apparatus(name):
    """The steps and the apparatus items for a content module, in order."""
    return (
        "(1) first give the one-line acknowledgment naming %s, a statement with no "
        "question, before any skill invocation or file read (INV-272), then invoke that "
        "module's skill; (2) before its Step 1, present the module-start apparatus in this "
        "order: the MODULE: banner with the module's name in caps, never a number "
        "(INV-079); the journey map of the selected modules, with the completed ones "
        "checked, %s current and the rest upcoming (INV-029); the before/after framing "
        "(INV-030); the numbered step overview (INV-031); the estimated time-to-complete "
        "per the active verbosity preset, suppressed under minimal and one line under "
        "concise (INV-096); and the recommended model/effort nudge, compared against the "
        "model and effort currently running (INV-063, INV-138)." % (name, name)
    )


def _graduation_apparatus():
    """The steps and the INV-102 graduation-start apparatus, in order."""
    return (
        "(1) first give the one-line acknowledgment naming graduation, a statement with "
        "no question, before any skill invocation or file read (INV-272), then invoke the "
        "graduation skill; (2) before its Step 1, present the graduation-start apparatus "
        "(INV-102) in this order: the BOOTCAMP GRADUATION banner; the journey map with "
        "every selected module checked as experienced, Bootcamp graduation as the current "
        "and final stage, and nothing upcoming; the before/after framing; the numbered "
        "step overview; the estimated time-to-complete per the active verbosity preset, "
        "suppressed under minimal and one line under concise; and the recommended "
        "model/effort nudge, compared against the model and effort currently running "
        "(INV-063, INV-138)."
    )


def reminder(module, on_resume=False):
    """The apparatus reminder for starting ``module``, or ``""`` for an exempt module.

    ``module`` is used as written. With ``on_resume`` false the condition is the
    Bootcamper's reply to the transition or graduation question; with it true, their
    acceptance of the resume offer. Either way the reminder starts with its condition and
    says to ignore it otherwise, so it never instructs an unconditional start.
    """
    if is_exempt(module):
        return ""
    graduation = is_graduation(module)
    name = GRADUATION_NAME if graduation else str(module).strip()
    if on_resume:
        if graduation:
            lead = ("Module-start reminder: %s has not begun yet. Only if the bootcamper "
                    "accepts resuming and graduation starts now:" % name)
        else:
            # The progress file holds a state token (`sdk_setup`), not the name the
            # bootcamper reads, so the text names it once and then says "that module".
            lead = ("Module-start reminder: the recorded module, `%s`, has not begun yet "
                    "(name it by its display name, never this token or a number). Only "
                    "if the bootcamper accepts resuming and that module starts now:" % name)
            name = "that module"
        otherwise = "If they do not accept resuming, ignore this reminder."
    else:
        lead = "Module-start reminder. Only if this reply accepts starting %s:" % name
        otherwise = ("If this reply does not accept starting %s (for example \"not yet\", a "
                     "question, or a request about something else), ignore this "
                     "reminder." % name)
    steps = _graduation_apparatus() if graduation else _apparatus(name)
    return " ".join((lead, steps, otherwise,
                     "Do not mention this reminder to the bootcamper."))


def _progress():
    """The progress file as a dict, or ``{}``. Never raises."""
    try:
        with open(PROGRESS, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


#: The values a ``bootcamp_complete`` flag reads as set.
TRUTHY = ("1", "true", "yes", "on")


def _preferences_flag():
    """True when ``config/bootcamp_preferences.yaml`` has a top-level
    ``bootcamp_complete: true``. Read line by line, with no YAML dependency. Never raises."""
    try:
        with open(PREFERENCES, encoding="utf-8") as fh:
            for line in fh:
                name, sep, value = line.partition(":")
                if sep and name == "bootcamp_complete":
                    value = value.split("#", 1)[0].strip().strip("\"'").lower()
                    return value in TRUTHY
    except (OSError, ValueError):
        pass
    return False


def _progress_flag():
    """True when ``config/bootcamp_progress.json`` carries ``bootcamp_complete: true``.
    Never raises."""
    value = _progress().get("bootcamp_complete")
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY
    return value is True


def bootcamp_complete():
    """True once graduation has ended the bootcamp: ``bootcamp_complete: true`` in
    **either** ``config/bootcamp_progress.json`` or ``config/bootcamp_preferences.yaml``.

    Graduation's closing step writes the flag to both files (#905). Either one is enough,
    so a project graduated before the progress-file write existed, which carries the flag
    only in preferences, still reads as finished, and so does one whose progress file is
    missing or malformed. The rule is stated in ``bootcamp-onboarding/SKILL.md`` step 2;
    this is its one implementation, shared by ``session-start.py``, ``stop-nudge.py`` and
    ``module-number-reminder.py`` (INV-300). Never raises."""
    return _progress_flag() or _preferences_flag()


def recorded_position():
    """``(current_module, current_step)`` as the progress file records them, each None when
    absent. Values are returned as written, unvalidated. Never raises."""
    progress = _progress()
    return progress.get("current_module"), progress.get("current_step")


def resume_reminder():
    """The reminder ``session-start.py`` adds to its resume message, or ``""``.

    Only for a module that has not begun: ``current_step`` null or absent, which module
    completion's Step 1 leaves when it moves ``current_module`` on (INV-413). Nothing when
    ``current_step`` is set (a resume partway through a module), when ``current_module`` is
    missing or apparatus-exempt, or when the bootcamp is complete.
    """
    progress = _progress()
    module = progress.get("current_module")
    if not isinstance(module, str) or not module.strip():
        return ""
    if progress.get("current_step") is not None or bootcamp_complete():
        return ""
    return reminder(module, on_resume=True)
