#!/usr/bin/env python3
"""userPromptSubmitted hook: "to capture bootcamp feedback, notes and verbosity changes".

Only active during a bootcamp (a config/bootcamp_progress.json file exists in the
working directory). If the bootcamper's message asks to give feedback, to jot a note
down, or to change verbosity, inject guidance so those "at any time" requests are
handled the same way anywhere in the bootcamp. Emits nothing otherwise, so the plugin
never alters unrelated GitHub Copilot sessions.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052.
"""
import json
import os
import re
import sys


def plugin_version():
    """The version of the plugin THIS hook ships in, resolved from the hook's own path.

    GitHub Copilot substitutes ``${PLUGIN_ROOT}`` in the hook's ``args``, but not
    inside the text the hook injects -- so handing the guide that path leaves it to
    resolve the manifest with a variable that may be unset, and on a machine carrying
    two plugin roots (an installed plugin plus a clone, or an un-removed upgrade) a
    search for `plugin.json` then answers with the wrong checkout's version. This file
    always knows where it lives, so it answers with the value instead of a path.

    Returns "Unknown" rather than guessing when the manifest cannot be read or parsed.
    """
    manifest = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "plugin.json",
    )
    try:
        with open(manifest, encoding="utf-8") as handle:
            version = json.load(handle).get("version")
    except (OSError, ValueError):
        return "Unknown"
    return version.strip() if isinstance(version, str) and version.strip() else "Unknown"


raw = sys.stdin.read()

# Gate: outside a bootcamp, do nothing at all.
if not os.path.isfile(os.path.join("config", "bootcamp_progress.json")):
    sys.exit(0)

# The prompt text is what we inspect; fall back to the raw payload if it is not JSON.
try:
    prompt = json.loads(raw).get("prompt", "")
except (ValueError, AttributeError):
    prompt = raw
lower = prompt.lower()

# ⛔ THE TWO HALVES OF THIS VOCABULARY ARE NOT SYMMETRIC, AND THAT IS DELIBERATE.
#
# Widening this pattern looks like a free win and is not. Modules 5-7 have the bootcamper
# writing and debugging *their own* loader, mapper and query code, so in this bootcamp
# "I found a bug", "something is broken" and "this is wrong" overwhelmingly mean THEIR
# code, not the plugin. Injecting the feedback workflow there is not a harmless false
# positive: it prepends an instruction to open a feedback entry, present a banner and
# gather structured feedback on top of a turn where the bootcamper wants their traceback
# explained. A missed capture is far cheaper than a spurious one (INV-054's reasoning by
# analogy), because the workflow is still reachable by `the bootcamp feedback workflow` and by
# feedback.md, while a derailed debugging turn is not recoverable.
#
# So:
#   * UNAMBIGUOUS - the word "feedback" in any construction, or bug/issue/problem/broken
#     language that NAMES the bootcamp, plugin, module or tutorial. Widen aggressively.
#   * AMBIGUOUS - bare bug/broken/wrong/problem with no such referent. Must NOT trigger.
#
# ⛔ Do not "fix" a miss by deleting that distinction. The regex will be edited again; the
# reasoning above is the part that will not be rediscovered.

#: Verbs that make "feedback" a request to give it rather than a mention of the word.
_GIVE = r"(?:give|giving|gave|have|having|has|got|send|sending|submit|submitting|share|sharing|" \
        r"provide|providing|offer|offering|leave|leaving|report|reporting|pass|passing|add|adding)"
#: A short qualifier window, so an interposed word does not defeat the match. This is the
#: one-word gap that made `I have feedback` hit and `I have some feedback about module 5`
#: miss: the old pattern required the pair to be adjacent.
_GAP = r"(?:\W+\w+){0,3}?\W+"
#: Words that attribute a fault to the bootcamp rather than to the bootcamper's own code.
#: ⛔ Deliberately does NOT include "this step", "these instructions" or "this skill". In
#: Modules 5-7 "this step is wrong" is far more often the bootcamper's own work in
#: progress than a defect in the plugin, so those phrasings stay in the ambiguous half.
#: The referents here are the four the plugin can actually be blamed by name for.
_OURS = r"(?:bootcamp|plugin|senzing bootcamp|this tutorial|tutorial|module \d+)"

FEEDBACK = re.compile(
    # The noun, in any construction: "bootcamp feedback", "I have some feedback about
    # module 5", "I'd like to give feedback", "can I give you some feedback", "sharing
    # feedback". Either order, since both "give feedback" and "feedback to give" occur.
    r"(?:bootcamp|plugin|power) feedback"
    r"|feedback (?:on|about|for|regarding) (?:the )?" + _OURS +
    r"|" + _GIVE + _GAP + r"feedback"
    r"|feedback" + _GAP + _GIVE +
    # An explicit report, already framed as one by the user.
    r"|report (?:an? )?(?:issue|bug|problem|defect)"
    # Fault language WITH a bootcamp/plugin referent - the attributed half. Kept narrow:
    # the referent must appear near the fault word, not merely somewhere in the prompt.
    r"|(?:bug|issue|problem|defect|broken|wrong|error)(?:\W+\w+){0,6}?\W+" + _OURS +
    r"|" + _OURS + r"(?:\W+\w+){0,6}?\W+(?:is |are |seems? )?(?:bug|issue|problem|defect|"
    r"broken|wrong)"
)

# ⛔ THE SAME ASYMMETRY APPLIES HERE, IN A NEW VOCABULARY. DO NOT REPEAT THE MISTAKE.
#
# "note" and "remember" are among the most common words in a debugging conversation, and
# in Modules 5-7 the bootcamper is debugging their own loader and asking the guide to
# recall things constantly. So this pattern is anchored on an IMPERATIVE TO RECORD
# SOMETHING, never on the bare verb:
#
#   * FIRES - "make a note", "note to self", "jot this down", "remind me", "don't let me
#     forget", "add a to-do", "for my notes", "capture this idea", "remember to <verb>".
#   * MUST NOT FIRE - "do you remember", "remember when", "I remember", "note that
#     <claim>", "as noted above", or any bare "remember"/"note" with no record-this
#     imperative.
#
# A spurious capture here is expensive in exactly the way a spurious feedback capture is:
# it prepends a banner and a recital to a turn where the bootcamper wanted a traceback
# explained. A missed capture is cheap - the flow stays reachable by `the bootcamp note workflow` and
# by notes.md. Same trade as FEEDBACK above, same reasoning, and the reasoning is the
# part that will not be rediscovered.
#: The nouns, always at a word boundary. Without the trailing \b, "note" matches inside
#: "noted" and the pattern fires on "as noted above" -- one of the phrasings the block
#: above names as must-not-fire.
_NOTE_NOUN = r"(?:notes?|memos?|to-?dos?|reminders?|ideas?)\b"

NOTE = re.compile(
    # An explicit imperative to record something.
    r"\b(?:make|take|add|write|jot|capture|create|start)\b"
    r"(?:\W+\w+){0,2}?\W+(?:a |an |this |that |some |my )?" + _NOTE_NOUN +
    # "note to self", "for my notes", "on my list", "in my notes".
    r"|\bnote to self\b"
    r"|\b(?:for|in) my (?:notes?|list|memos?)\b"
    r"|\b(?:on|to) my (?:to-?do )?list\b"
    r"|\bbootcamp note\b"
    # "jot/write this down", "put this down".
    r"|\b(?:jot|write|put)\b(?:\W+\w+){0,2}?\W+down\b"
    # "remind me", "don't let me forget" - imperative, so unambiguous.
    r"|\bremind me\b"
    r"|\b(?:do ?n[o']?t|dont) let me forget\b"
    # "remember to <verb>" is an instruction to record; "remember when/that/how" is not.
    r"|\bremember to \w+"
)

VERBOSITY = re.compile(
    # Same qualifier tolerance, lower stakes: verbosity is re-adjustable at any time and
    # carries no consent or durability guarantee, so a false positive is self-correcting.
    r"change verbosity|more detail|less detail|more code walkthrough|"
    r"too verbose|too terse|more verbose|less verbose|"
    r"(?:be|answer|reply|respond|make it|keep it)" + _GAP +
    r"(?:more |less |)(?:concise|verbose|detailed|wordy|brief|terse|short|shorter|"
    r"longer|succinct)|"
    r"(?:shorter|longer|briefer|more concise|less wordy|more wordy)\W+"
    r"(?:answers?|replies|responses?|explanations?)"
)

ctx = ""
if FEEDBACK.search(lower):
    ctx = (
        "The bootcamper is submitting bootcamp feedback. Follow the bootcamp "
        "feedback workflow (the feedback.md file in the bootcamp-onboarding skill): "
        "begin with the pinned BOOTCAMP FEEDBACK entry banner and end with the "
        "FEEDBACK SAVED exit banner (see feedback.md for the verbatim banner wording); "
        "silently capture as much relevant context as possible (the time; the plugin "
        "version, which is " + plugin_version() + " -- already resolved from the running "
        "plugin, so record it as given and do NOT go looking for a plugin.json; "
        "current_module, current_step, and "
        "completed modules from config/bootcamp_progress.json; the recent questions "
        "asked and the bootcamper's responses; what the plugin was doing behind the "
        "scenes; the observed problem; the expected behavior per the active "
        "hooks/skills; and why expected did not match actual) -- never ask extra "
        "questions, and record \"Unknown\" when a source is missing. Then gather the "
        "feedback one leading question at a time. APPEND (never overwrite) a "
        "formatted entry to docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md, "
        "creating that file with its header if it does not exist; then verify the "
        "entry landed (re-read and re-append if missing) before telling the "
        "bootcamper it was saved (INV-067). Triage whether the issue is in this "
        "plugin or in the Senzing MCP server (feedback.md Step 2b) and record the "
        "verdict in the entry's Routing field -- every entry is saved locally "
        "whatever the verdict (INV-015). Only for an mcp-server/both verdict, and "
        "only after the local entry is confirmed saved, offer ONCE to forward it via "
        "the MCP server's submit_feedback tool, showing the exact message first and "
        "stripping anything identifying (INV-321); never send anything external "
        "without that yes. When done, "
        "return the bootcamper to exactly where they left off without making them "
        "re-explain their context."
    )
elif NOTE.search(lower):
    # ⛔ PRECEDENCE IS STATED HERE, NOT LEFT TO BRANCH ORDER. "make a note that the
    # bootcamp is broken" matches both vocabularies, and FEEDBACK wins -- deliberately.
    # FEEDBACK's fault half only fires when the bootcamp, plugin, module or tutorial is
    # NAMED as the thing at fault, so a message satisfying both is an attributed defect
    # report that happens to be phrased as a note. Nothing is lost by routing it to
    # feedback: that flow is also durable, also banner-bracketed, and also returns the
    # bootcamper to the pending question -- and it additionally reaches the maintainer,
    # which the notes flow never does. Routing it to notes would silently drop a defect
    # report into a private keepsake. The `elif` above IS this decision; this comment is
    # what stops it being "simplified" into a different one.
    ctx = (
        "The bootcamper wants to capture a note of their own (an idea, question, "
        "reminder, to-do or memo) -- NOT feedback about the plugin. Follow the "
        "bootcamp note workflow (the notes.md file in the bootcamp-onboarding "
        "skill): begin with the pinned BOOTCAMP NOTE entry banner and end with the "
        "NOTE SAVED exit banner (see notes.md for the verbatim banner wording, which "
        "uses a pin glyph, never the feedback flow's memo glyph); silently capture "
        "the time, current_module and current_step from "
        "config/bootcamp_progress.json, and the pending question -- never ask an "
        "extra question for context, and record \"Unknown\" rather than guessing. If "
        "the bootcamper's message ALREADY contains the note, take it from the message "
        "and do NOT ask what they would like to note. Classify it silently as idea, "
        "question, reminder, to-do or memo -- never ask. Recite the note for approval "
        "with the pinned numbered question, then APPEND (never overwrite) it to "
        "docs/bootcamp_notes.md, creating that file with its header if it does not "
        "exist, and verify it landed (re-read and re-append if missing) before "
        "telling the bootcamper it was saved. Store any elaboration or context under "
        "its own label -- never merged into the bootcamper's own words. The note is "
        "the bootcamper's, stays on their machine, and is never sent anywhere: there "
        "is no routing verdict and no upstream offer. It is folded into their recap "
        "at graduation. A failed write warns in one line and never blocks. When done, "
        "re-present the exact pending bootcamp question verbatim so exactly one "
        "question ends the turn."
    )
elif VERBOSITY.search(lower):
    ctx = (
        "The bootcamper wants to change the bootcamp's verbosity. Update the "
        "verbosity settings in config/bootcamp_preferences.yaml per the bootcamp "
        "ground rules, confirm the new setting in one sentence, then continue from "
        "where they left off. This is not a gate and must not interrupt the current "
        "step's pending question."
    )

if ctx:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "userPromptSubmitted",
            "additionalContext": ctx,
        }
    }))
sys.exit(0)
