#!/usr/bin/env python3
"""sessionStart hook: to resume an in-progress bootcamp by injecting resume context.

Also folds any in-progress module recap checkpoint into docs/bootcamp_recap.md on
resume, so a module that was interrupted (quit / compaction / prior session) keeps
its in-progress narrative in the recap (see recap_checkpoint.py).

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. Python is already a hard bootcamp dependency (the graduation recap PDF always
runs under python3; the Truth Set visualization server also does when the chosen language is
Python).
"""
import sys

import docker_lifecycle
import recap_checkpoint

if recap_checkpoint.bootcamp_active():
    folded = recap_checkpoint.fold_checkpoint()
    # Fold first, then guarantee the file exists for the module about to resume.
    recap_checkpoint.ensure_checkpoint()
    message = (
        "A Senzing bootcamp is in progress. Read config/bootcamp_progress.json "
        "and offer to resume from the last recorded module before doing anything else."
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
