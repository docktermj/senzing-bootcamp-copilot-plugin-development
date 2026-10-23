#!/usr/bin/env python3
"""userPromptSubmitted hook: "to keep the in-progress recap checkpoint durable".

Guarantees `docs/progress/recap_checkpoint.md` exists while a bootcamp is running,
and reminds the guide to keep it current **before** anything is at risk.

Why this runs per turn rather than at session start. A bootcamp becomes active
partway through a session — `config/bootcamp_progress.json` is written during
onboarding — by which time the sessionStart hook has already run and found no
bootcamp. Only a per-turn hook creates the file within one turn of the bootcamp
starting. The cost is one `os.path.exists` on turns where it already exists.

Why the reminder cannot live only in the pre-compaction (no Copilot preCompact handler is configured) hook. That hook cannot fire until
a compaction is already under way, which is after the window in which the checkpoint
had to have been written for there to be anything to preserve. A full bootcamp ran ten
modules without the file existing, in a session that had crossed a compaction
boundary. So the reminder is emitted here, once per session, while it can still act.

Non-blocking and silent apart from that one reminder: the checkpoint's own status goes
to stderr (see recap_checkpoint.py), never to stdout, which for this event carries a
structured JSON payload.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052.
"""
import json
import os
import sys

import recap_checkpoint

# Read and discard the payload: this hook keys off project state, not the prompt, but
# a hook that leaves stdin unread can break the writer on some platforms.
sys.stdin.read()

if not recap_checkpoint.bootcamp_active():
    sys.exit(0)

created = recap_checkpoint.ensure_checkpoint()

# Announce the checkpoint once per session, on the turn the file is created. On every
# later turn this hook is silent, so it never competes with the current step's
# pending question (INV-012).
if created:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "userPromptSubmitted",
            "additionalContext": (
                "The bootcamp's in-progress recap checkpoint now exists at "
                "docs/progress/recap_checkpoint.md (created empty). Keep it current: at "
                "each step boundary -- not per sub-step -- write the module's "
                "accumulating Information Shared / Questions & Responses / Actions Taken "
                "/ End-of-Module Summary-so-far between its "
                "<!-- RECAP-CHECKPOINT:START --> and <!-- RECAP-CHECKPOINT:END --> "
                "markers. This is the only copy that survives a quit, compaction, or new "
                "session mid-module; the pre-compaction (no Copilot preCompact handler is configured), sessionEnd and sessionStart hooks "
                "fold whatever is in it into docs/bootcamp_recap.md, and fold nothing "
                "while it holds only its scaffold. Finalize and clear it on module "
                "completion (module-completion.md step 2d). Do not mention this file to "
                "the bootcamper and do not let it interrupt the current step."
            ),
        }
    }))

sys.exit(0)
