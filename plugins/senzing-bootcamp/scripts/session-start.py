#!/usr/bin/env python3
"""sessionStart hook: to resume an in-progress bootcamp by injecting resume context.

Also folds any in-progress module recap checkpoint into docs/bootcamp_recap.md on
resume, so a module that was interrupted (quit / compaction / prior session) keeps
its in-progress narrative in the recap (see recap_checkpoint.py).

A finished bootcamp is checked first (#905): when ``bootcamp_complete`` is true in the
progress file or in the preferences (``module_start_apparatus.bootcamp_complete()``), the
hook makes no resume offer, folds no checkpoint and adds no apparatus reminder. It tells the
guide to follow the finished case of ``bootcamp-onboarding/SKILL.md`` step 2 instead: say the
bootcamp is complete, name ``the package-bootcamp skill`` and ask what they would like to explore. That
holds even when the progress file is missing or malformed, because a finished project must
never read as a fresh bootcamp and run onboarding again. The message is ASCII-only, like the
reminder, so a Windows console code page cannot break it.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. Python is already a hard bootcamp dependency (the graduation recap PDF always
runs under python3; the Truth Set visualization server also does when the chosen language is
Python).
"""
import sys

import docker_lifecycle
import recap_checkpoint

import module_start_apparatus

#: What the guide is told on a finished project (#905). ASCII-only (see the docstring).
FINISHED = ("This Senzing bootcamp is complete: bootcamp_complete is set, so graduation has "
            "ended it. Do not offer to resume a module and do not run onboarding. Follow the "
            "finished case of bootcamp-onboarding/SKILL.md step 2: when the bootcamper writes, "
            "say the bootcamp is complete, name the package-bootcamp skill, and end on the one open "
            "question it pins, asking what they would like to explore.")


# A finished bootcamp first: either file's flag ends it, whatever the progress file records.
if module_start_apparatus.bootcamp_complete():
    print(FINISHED)
    sys.exit(0)

if recap_checkpoint.bootcamp_active():
    folded = recap_checkpoint.fold_checkpoint()
    # Fold first, then guarantee the file exists for the module about to resume.
    recap_checkpoint.ensure_checkpoint()
    message = (
        "A Senzing bootcamp is in progress. Read config/bootcamp_progress.json "
        "and offer to resume from the last recorded module before doing anything else. End the resume offer with exactly one 👉 question; when offering choices, use numbered options and add no narration after them."
    )
    if folded:
        message += (
            " An in-progress module recap checkpoint was found and folded into "
            "docs/bootcamp_recap.md (source: docs/progress/recap_checkpoint.md). "
            "Continue that module and finalize its recap section on completion."
        )
    else:
        message += (
            " No in-progress recap narrative was found to fold. Keep "
            "docs/progress/recap_checkpoint.md current at each step boundary of the "
            "resumed module — it is the only copy that survives a compaction."
        )
    containers = docker_lifecycle.resume_summary()
    if containers:
        message += " " + containers
    print(message)

sys.exit(0)
