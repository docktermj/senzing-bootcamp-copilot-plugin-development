# Bootcamp Note Workflow (available at any time)

The bootcamper can capture a note at any point in the bootcamp: onboarding, any module,
or graduation (INV-254). A note is an **idea, question, reminder, to-do or memo of their
own** — a thought about *their* work, not a report about the plugin.

⛔ **This is not a variant of `feedback.md`, and the difference is the whole point.**
Feedback points **outward**: it carries a `Routing:` verdict, it is the maintainer's
triage input, and an `mcp-server` verdict may be offered upstream. A note points
**inward**: it has no routing verdict, no upstream offer, and no `submit_feedback` path.
It is the bootcamper's, it stays on their machine, and it ends up in their keepsake
rather than in anyone's inbox. Saved to `docs/bootcamp_notes.md` and folded into
`docs/bootcamp_recap.pdf` at graduation.

Triggered by the plugin's `userPromptSubmitted` hook, by the `the bootcamp note workflow` command, or
whenever the bootcamper says something like "make a note", "remind me", "jot this down",
"don't let me forget" or "note to self". Follow `ground-rules.md`: one 👉 question per
yielding turn (INV-251), and the turn ends on it.

⚠️ **When a message is both a note and a feedback report, it is feedback.** "Make a note
that the bootcamp is broken" names the bootcamp as the thing at fault, so it is an
attributed defect report that happens to be phrased as a note. Routing it here would drop
a defect report into a private keepsake the maintainer never sees. Nothing is lost by
preferring feedback: that flow is also durable, also banner-bracketed, and also returns
the bootcamper to the pending question. The precedence is stated in
`../../scripts/feedback-capture.py` rather than left to branch order.

## Step 0: Capture context silently

Before asking anything, silently capture what is available. Gather only from sources you
already have — **never spend a 👉 question on it** — and record "Unknown" rather than a
guess:

- **Time:** the current date and time, with timezone offset.
- **Module and step:** `current_module` and `current_step` from
  `config/bootcamp_progress.json`.
- **The pending question:** the exact 👉 question the bootcamper was on when they
  interrupted, so it can be re-presented verbatim at Step 5.

This is what Step 3's option 2 offers to attach, so it must already be in hand before
that question is asked.

## Step 1: Ensure the notes file exists

If `docs/bootcamp_notes.md` does not exist, create it with this header once:

```markdown
# Senzing Bootcamp Notes

Ideas, questions, reminders and to-dos captured during the Senzing Bootcamp, in your own
words. Every note here is folded into your recap at graduation and appears in
`docs/bootcamp_recap.pdf`. Nothing here is ever sent anywhere.

**Started:** YYYY-MM-DD

## Your Notes
```

It is a top-level `docs/*.md` file, so INV-017 is satisfied and graduation's normalizer
picks it up with the rest.

## Step 1b: Mark the start of the note (entry banner)

Steps 0 and 1 are silent. This is the first bootcamper-facing moment: present the pinned
entry banner **verbatim**, before the first 👉 question, in the same turn (INV-255):

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌📌📌  BOOTCAMP NOTE  📌📌📌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

⛔ **The emoji is 📌, never 📝.** 📝 is the feedback banner's (INV-074). Two any-time
flows opening with the same glyph are two flows the bootcamper cannot tell apart at a
glance, which is the entire reason INV-074 exists.

The banner is a statement, not a question; it never counts against INV-251.

## Step 2: Get the note

⛔ **If the triggering message already carries the note, take it from the message and do
not ask.** "Remind me to check the truth-set counts" *is* the note. Asking what they would
like to note makes them say it twice — the pointless question INV-006 and INV-012 forbid.

Only when the trigger carried no content ("make a note", `the bootcamp note workflow` with no
argument), ask this pinned question (INV-056) and end the turn on it:

> 👉 **What would you like to note?**

## Step 2b: Classify it silently

Assign a type — `idea` | `question` | `reminder` | `to-do` | `memo` — from the wording, as
an assessment, exactly as `feedback.md` Step 2b triages routing.

⛔ **Do not ask for it (INV-257).** They reported a thought; naming its kind is the plugin's job, and
a 👉 spent on a taxonomy is a 👉 spent on nothing they care about.

## Step 3: Recite it for approval

Show the note exactly as it will be saved, then this pinned 👉 question (INV-056), and end
the turn on it:

> 👉 **Here's your note — save it as is? Reply with a number:**
>
> 1. **Save it** — exactly as written above.
> 2. **Add my bootcamp context** — record where I was when I made this note.
> 3. **Elaborate it** — expand it into a fuller note, marked as the bootcamp's words.
> 4. **Reword it** — I'll type the correction.

Options 2, 3 and 4 apply the change and **re-present the recital**. That is not a re-ask
under INV-006: the note being recited is different, and ask-once protects the bootcamper
from answering the same question twice, not from confirming a changed artifact.

⚠️ **Options 2 and 3 are each offered once.** Once applied, that option drops off the list,
so the loop is finite by construction and the bootcamper cannot be walked round it.

## Step 3b: Attribution is structural, not stylistic

The note body is the **bootcamper's words**. An elaboration (option 3) is stored under its
own `**Elaboration:**` label, and the context block (option 2) under `**Context:**`
(INV-257).

⛔ **Never merge an elaboration into the note body.** This is a keepsake with their name on
the certificate; a paragraph they did not write, indistinguishable from one they did, is
the plugin putting words in their mouth permanently. The recap PDF renders both labels on
the page, so the distinction survives printing.

## Step 3c: The context block is machine-composed, so INV-322 binds it

No hostname, username, home-directory path or IP address. The module, the step, the time
and the pending question are the content; environment facts are not.

## Step 4: Append, then verify it landed

**Append** — never rewrite — to the "Your Notes" section of `docs/bootcamp_notes.md`:

```markdown
### {Type}: {short title}

**Captured:** {ISO 8601 timestamp with timezone offset}
**Module:** {module name at capture time, or "General"}
**Type:** {idea | question | reminder | to-do | memo}

{the note, in the bootcamper's own words, as approved}

**Context:** {module/step, the pending 👉 question, and the time — only when option 2 was taken}
**Elaboration:** {the bootcamp's expansion — only when option 3 was taken}
```

Then **immediately re-read the file and confirm the entry is present** (INV-256). If it is
missing — a lost or partial write, or a session/compaction boundary — append it again and
re-read. Only continue once it is confirmed on disk.

This is `feedback.md` Step 3b's discipline applied to the notes file, and for the same
reason: a note the bootcamper was told was saved and which is not on disk is worse than
one they know was never captured.

## Step 5: Exit banner and return

Only after Step 4 confirms the entry on disk, present the pinned exit banner **verbatim**
(INV-255):

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌  NOTE SAVED — BACK TO THE BOOTCAMP  📌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then one line: "Saved to `docs/bootcamp_notes.md` — it'll be in your recap at graduation.
Add another anytime by saying \"make a note\"."

The banner and the line are statements. Immediately after them, **re-present the exact
pending 👉 bootcamp question verbatim**, so that exactly one 👉 ends the turn
(INV-006/INV-251). Do not make them re-navigate, and do not merge the note flow's
questions with the resumed bootcamp question into one turn.

## Non-blocking throughout

⛔ **A note is never a gate (INV-048).** A failed write, a failed re-read, or an
unreachable notes file warns in **one line** and returns the bootcamper to the bootcamp.
It must not interrupt a pending question, delay a step, or become a to-do for them.

## What never happens here

- ⛔ **No routing verdict.** A note is not a defect report and is never triaged as one.
- ⛔ **No upstream offer, ever.** `submit_feedback` is not reachable from this flow. The
  note stays on the bootcamper's machine; the only place it travels to is their own recap.
- ⛔ **No who-noticed-it field.** Feedback records whether a finding was
  bootcamper-reported or self-observed (INV-116); a note has exactly one author, always
  the bootcamper.
