#!/usr/bin/env python3
"""userPromptSubmitted hook: to keep modules named by their names after a module number slips
into a reply (#874, INV-079).

INV-079 has the guide name a module, never number it, and ``ground-rules.md`` says so. In two
``auto-test`` walks the guide read that rule and still wrote "Module 5" to the Bootcamper,
then kept doing it in later turns: the skill headings and descriptions it reads carry the
number. A rule already read does not hold, so this hook catches the leak when it happens.
When the guide's previous turn showed a module number, it puts a short reminder into the
guide's context before the next reply, so the leak does not repeat. It never blocks: a number
already shown stays shown, and the reminder tells the guide not to correct or apologize for
it, and not to mention the reminder, so the Bootcamper never sees it.

Gates, checked in order; every failed gate is silent (exit 0, no stdout):
  1. ``config/bootcamp_progress.json`` exists. This gate tests the file's EXISTENCE on
     purpose, not ``recap_checkpoint.bootcamp_active()``: existence answers "is this a
     bootcamp project", not "is a bootcamp in progress" (INV-227). The onboarding preface
     creates the file empty and nothing records a module until Bootcamp preparation's final
     write, yet the preface and Bootcamp preparation are Bootcamper-facing and name modules
     too (the same gate and reason as ``stop-nudge.py`` gate 2).
  2. The bootcamp is not complete (``bootcamp_complete: true`` in the progress file or in
     the preferences, set by graduation; ``module_start_apparatus.bootcamp_complete()``), as
     ``stop-nudge.py`` gate 3b.
  3. The payload names a readable, UTF-8 transcript, and the previous turn has settled on a
     final assistant message, read by ``transition_reply.previous_turn_texts``: the same
     reader the transition detector uses, so sidechain (subagent) and meta records are
     skipped, and the prompt being submitted is skipped if it is already on disk.
  4. A match of ``MODULE_NUMBER`` in ANY assistant text of that turn, not only its final
     message: the Bootcamper reads a text block written before a tool call too. Text inside
     fenced code is scanned as well, because the Bootcamper reads it.

``MODULE_NUMBER`` is the pattern ``transcript_lint.check_module_numbers`` uses, so this hook
and the linter agree on what a module number is; ``tests/test_module_number_reminder.py``
fails if they differ. No state is kept between turns, so the reminder repeats on every turn
that shows a number.

Biased toward silence like ``stop-nudge.py`` (INV-054): a missed reminder costs less than a
wrong one, so anything undecided is silent and nothing here raises on bad input.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. The JSON on stdout
is ASCII-escaped, so no console code page can break it.
"""
import json
import os
import re
import sys

import module_start_apparatus
import transition_reply

#: A module number as the Bootcamper would read it ("Module 5"). The same pattern as
#: ``transcript_lint.check_module_numbers``, asserted equal by a test.
MODULE_NUMBER = re.compile(r"\bModule\s+\d+\b")


def hits_in(texts):
    """Each distinct module number in ``texts``, in first-seen order, whitespace collapsed."""
    seen = []
    for text in texts:
        for match in MODULE_NUMBER.finditer(text):
            hit = " ".join(match.group(0).split())
            if hit not in seen:
                seen.append(hit)
    return seen


def reminder(hits):
    """The reminder for ``hits``, quoting each one."""
    quoted = ", ".join('"%s"' % hit for hit in hits)
    return ("Module-name reminder: your previous reply showed the bootcamper a module "
            "number (%s). From now on name every module by its name, as the module table in "
            "bootcamp-preparation/SKILL.md spells it (for example \"SDK setup\" or \"Data "
            "Quality, Mapping, and Transformation\"), never by a number (INV-079). Do not "
            "correct or apologize for the earlier reply, and do not mention this reminder "
            "to the bootcamper." % quoted)


# Drain stdin first, whatever the gates decide: a hook that leaves it unread can break the
# writer on some platforms. Read as bytes so a Windows console code page cannot fail the
# decode; json.loads takes UTF-8 bytes directly.
try:
    payload = json.loads(sys.stdin.buffer.read())
except (AttributeError, OSError, ValueError):
    payload = None

# Gate 1: a bootcamp project, recorded module or not (existence, on purpose; see above).
if not os.path.isfile(os.path.join("config", "bootcamp_progress.json")):
    sys.exit(0)

# Gate 2: not after graduation has ended the bootcamp.
if module_start_apparatus.bootcamp_complete():
    sys.exit(0)

# Gate 3: every assistant text of the previous turn, once it has settled.
texts = transition_reply.previous_turn_texts(payload)
if not texts:
    sys.exit(0)  # undecided, or a turn with no text -> silent

# Gate 4: a module number the Bootcamper read.
hits = hits_in(texts)
if not hits:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "userPromptSubmitted",
        "additionalContext": reminder(hits),
    }
}))
sys.exit(0)
