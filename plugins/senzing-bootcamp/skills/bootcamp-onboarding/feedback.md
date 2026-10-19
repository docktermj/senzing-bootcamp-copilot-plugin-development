# Bootcamp Feedback Workflow (available at any time)

The bootcamper can submit feedback at any point in the bootcamp: onboarding, any
module, or graduation. Feedback is saved locally to
`docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` and is never sent anywhere
unless the bootcamper explicitly asks.

This workflow is triggered by the plugin's `userPromptSubmitted` hook ("to capture
bootcamp feedback") or by the `the bootcamp feedback workflow` command, or whenever the
bootcamper says something like "bootcamp feedback", "I have feedback", or "report
an issue". Follow `ground-rules.md`: one 👉 question per turn (INV-251), end the turn on it.

## Step 0: Capture context silently

Before asking anything, silently capture as much relevant context as possible, so
the bootcamper never has to re-explain it and so the maintainer triage can later
reconstruct the exact situation. Gather only from available sources — never ask an
extra question for this — and record "Unknown"/"Unavailable" (never a guess) when a
source is missing:

- **Time:** the current date and time.
- **Plugin version:** the `version` field of the plugin manifest, resolved exactly as
  `onboarding-flow.md` step 0 specifies — `${PLUGIN_ROOT}/.copilot-plugin/plugin.json`, else
  `<this-skill-dir>/../../.copilot-plugin/plugin.json`, else "Unknown". ⛔ Never found by searching
  the filesystem: a machine carrying two plugin checkouts then reports the wrong version (INV-252).
- **Workstation:** the operating system and platform the bootcamper is running on, from the environment/system context — OS name and version, and architecture if available.
- **Model and effort:** the model name/ID and the reasoning-effort level in use, from the environment/system context.
- **Context size:** the approximate size of the conversation context at the time of feedback — a token count and/or percentage of the context window in use. If only an estimate is available, label it as approximate rather than recording a precise-looking guess.
- **Module and step:** `current_module`, `current_step`, and completed modules from `config/bootcamp_progress.json`.
- **Recent questions and responses:** the last few 👉 questions asked and the bootcamper's answers, from the transcript.
- **Behind the scenes:** what the plugin was doing — which hook fired, which skill/phase/gate was active, and any relevant config or state.
- **Observed problem:** what the bootcamper saw.
- **Expected behavior:** what the active hooks, skills, and `ground-rules.md` imply should have happened.
- **Divergence:** the best assessment of why the expected action did not occur.

## Step 1: Ensure the feedback file exists

If `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` does not exist, create the
`docs/feedback/` directory and write this header once:

```markdown
# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** YYYY-MM-DD

## Your Feedback
```

## Step 1b: Mark the start of feedback (entry banner)

Steps 0 and 1 are silent/administrative. This is the first bootcamper-facing moment of the
feedback workflow: present the pinned entry banner **verbatim** so the bootcamper clearly sees
they have switched out of the bootcamp and into feedback collection. Show it before the first 👉
feedback question (Step 2), in the same turn:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝📝📝  BOOTCAMP FEEDBACK  📝📝📝
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The banner is a statement, not a question; it never counts against the one-👉-per-turn rule.

## Step 2: Gather the feedback, one 👉 question at a time

Ask these in order, each as its own turn (pre-fill the module from captured
context so you do not ask the bootcamper to repeat it):

1. 👉 **What would you like to give feedback about?**
2. 👉 **What happened?**
3. 👉 **Why does it matter to you?**
4. 👉 **Do you have a suggested fix?**
5. 👉 **What priority would you give this? Reply with a number:**

   1. **High**
   2. **Medium**
   3. **Low**

⛔ **Ask only the questions their message has not already answered (INV-006).** Anything it supplies
— in whole or in part — is **captured, not re-asked**: confirm what you captured in one line, then
ask only the gaps, one 👉 per turn. If it answers everything, ask nothing and proceed.

⚠️ **The partial message is the normal shape, not the exception.** A bootcamper who stops to report
something usually writes one sentence naming the subject, what happened, and often a suggested fix
— three of the five above — and leaves the rest. Read as an all-or-nothing shortcut, this step
re-asks the three they just answered, which is the INV-006 violation the whole flow is most exposed
to: they are already spending goodwill to report a defect. The sibling any-time control states the
same rule for the same reason (`notes.md` Step 2 → *"If the triggering message already carries the
note, take it from the message and do not ask."*).

## Step 2b: Triage — plugin issue, Senzing MCP server issue, or neither?

Decide, silently (no 👉 question), which component the report is actually about. This is an
assessment you make from the captured context, not something to ask the bootcamper — they reported a
symptom; identifying the component is the plugin's job.

**The discriminating test — ask the third question first, because a yes there settles it:**

- *Would this still happen with a perfect bootcamp plugin **and** a perfect Senzing MCP server?*
  If yes → **host** (the bootcamper's GitHub Copilot interface owns it; neither component ships it).
- *Would this still happen if the bootcamp plugin were perfect?* If yes → **MCP server**.
- *Would this still happen if the Senzing MCP server were perfect?* If yes → **plugin**.
- Yes to the middle two → **both** (the plugin repeated or failed to guard an upstream defect).
- Nothing above is clear → **unclear**.

⚠️ **`host` exists because the first two questions alone give the wrong answer (INV-248).** A defect in the
GitHub Copilot harness survives a perfect plugin *and* a perfect server, so a two-question test lands
it on `both` — "the plugin repeated or failed to guard an **upstream** defect" — when there is no
upstream Senzing defect at all. `unclear` is wrong for it too: that verdict means the component
*cannot be identified*, and here it can be, exactly.

| Verdict | Looks like | Examples seen in the field |
|---|---|---|
| `plugin` | The bootcamp's own skills, hooks, bundled scripts, questions, gates, banners, ordering, module content or generated deliverables | A question asked twice; a stale instruction; a PDF generator dropping a table off the page; a screenshot helper capturing the wrong tab; a module omitted from the Core path |
| `mcp-server` | A Senzing MCP **tool** returned wrong, incomplete, truncated or unusable output, or its reference data does not match the installed SDK | `mapping_workflow` step-3 validation rejecting a payload with the reason truncated away; `get_sdk_reference` not covering parameter shapes; a flag documented for one language binding but absent from another; a tool unreachable or erroring |
| `both` | The plugin's guidance propagated or failed to guard an upstream defect | The plugin's own docs repeated an incorrect flag claim that came from a tool |
| `host` | The bootcamper's **GitHub Copilot interface** owns it — a harness prompt, dialog, toggle or session control that neither the bootcamp nor Senzing ships, and neither can fix | The GitHub Copilot "Set up auto mode for your environment?" prompt appearing over a pending 👉 question during the onboarding preface (reported twice on 2026-08-15) |
| `unclear` | The symptom is real but the component cannot be identified from the evidence | Wrong entity-resolution results with no way to tell whether the mapping, the SDK, or the guidance caused it |

⛔ **The verdict never changes whether the entry is recorded locally.** Every submitted entry is
appended to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` regardless of verdict (INV-015) —
the file is the bootcamper's own durable record and the maintainer's triage input. The verdict
decides only whether an **additional** upstream submission is *offered* (Step 3c).

Record the verdict in the entry's `**Routing:**` field, with a one-line reason. Do not soften an
`mcp-server` verdict to `plugin` just because this is the bootcamp's feedback file: a misfiled report
reaches the wrong maintainer and gets fixed nowhere.

## Step 3: Append the entry (never overwrite)

Append a formatted entry to the "Your Feedback" section. Append only: never
rewrite the file, so earlier entries are preserved.

Write `**Upstream:**` as `offer pending` when Step 2b's verdict is `mcp-server` or `both`: the
entry is saved before Step 3c asks, so no outcome exists yet. Step 3c replaces it. Every other
verdict gets `not applicable`.

```markdown
## Improvement: [brief title from the bootcamper's description]

**Date:** YYYY-MM-DD
**Module:** [module name or "General"]
**Priority:** [High/Medium/Low]
**Source:** bootcamper-reported
**Routing:** [plugin | mcp-server | both | host | unclear] — [one-line reason, per Step 2b]
**Upstream:** [not applicable | offer pending | offered, declined | submitted YYYY-MM-DD | submission failed: reason | submission blocked: reason]

### What happened

[the bootcamper's description]

### Why it matters

[the bootcamper's stated impact]

### Suggested fix

[the bootcamper's suggestion, or "None provided"]

### Context when reported

- **Time:** [YYYY-MM-DD HH:MM local, or "Unknown"]
- **Plugin version:** [the version captured above, or "Unknown"]
- **Workstation:** [OS name and version, and architecture; e.g. "Linux 6.17.0-35-generic (x86_64)", or "Unknown"]
- **Model / effort:** [model ID and reasoning-effort level; e.g. "copilot-opus-5-5[1m] / high", or "Unknown"]
- **Context size:** [approximate tokens and/or % of context window in use; e.g. "~85k tokens (~42% of window)", or "Unknown"]
- **Module / step:** [`current_module` / `current_step` from `config/bootcamp_progress.json`, or "Unknown"]
- **Recent questions:** [the last few 👉 questions asked]
- **Bootcamper responses:** [their answers to those questions]
- **Behind the scenes:** [active hook/skill/phase/gate and relevant state]
- **Observed problem:** [what the bootcamper saw]
- **Expected behavior:** [what the active hooks/skills/ground-rules imply should happen]
- **Divergence:** [why expected did not match actual]
```

**`Source:`** distinguishes who noticed the problem (INV-116). This bootcamper-driven flow always
writes `bootcamper-reported`. The graduation retrospective (`../graduation/SKILL.md`) reuses this
same template and durability check to file findings the **assistant** noticed, marked
`self-observed (assistant retrospective)` — a maintainer triaging the file needs to tell real user
friction from the assistant's own stumbles, because the two deserve different weight.

## Step 3b: Verify it landed (durability)

Immediately re-read `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` and confirm
the `## Improvement:` entry you just appended is present. If it is missing — a lost or
partial write, or a session/compaction boundary — append it again and re-read to
confirm. Only continue once the entry is confirmed on disk. This mirrors the recap's
"verify it landed" step (`module-completion.md` Step 2c) so submitted feedback is
never silently lost (INV-015).

## Step 3c: Offer to forward an MCP-server issue upstream

Only when Step 2b's verdict is **`mcp-server`** or **`both`**, and only after Step 3b has confirmed
the local entry is on disk. For `plugin`, `host` or `unclear`, skip this step entirely — set
`**Upstream:** not applicable` and go to Step 4.

⛔ **`host` is never forwarded, and the reason is not that it is unimportant (INV-249).** `submit_feedback`
reaches **Senzing**. A report about the GitHub Copilot harness sent there arrives at a party that does
not ship it and cannot fix it — a misrouted report, which the bootcamper cannot follow up because
submissions are anonymous. There is no upstream channel for this class from inside the bootcamp;
the local entry is the whole record.

The Senzing MCP server accepts reports through its own `submit_feedback` tool, and an upstream defect
can only be fixed upstream — recording it here alone means the bootcamper hits it again next time,
and so does everyone else. But this **sends content outside the bootcamper's machine**, so it is
never automatic.

1. **Draft the upstream message.** Self-contained, because the recipient cannot see this bootcamp:
   the **tool name**, what was observed, what was expected, and the Senzing SDK version. Include the
   verbatim error text when there is one. Keep it factual — no speculation about internals.

2. ⛔ **Strip everything identifying.** No hostname, username, file path under a home directory, IP
   address, email, company name, or data values from the bootcamper's records (INV-321). Entity names
   and record IDs from their data are **theirs** — describe the shape of the problem, never the
   content. The bootcamper's own data must never leave the machine as part of a bug report.

   *Scope:* this rule governs the **`bug` / `feature` / `question` / `general`** categories — defect
   reports, which never need to identify anyone. The same tool's **`license_request`** category is a
   different thing: it *requires* a first name and work email to issue an evaluation license, so
   stripping them would break it. That path is therefore not run from here at all — it lives in
   `../module-04-data-collection/SKILL.md` Step 8a.6a behind its own pinned consent gate (INV-135).
   Never send personal details under a defect category, and never send a defect report under
   `license_request`.

3. **Show the exact message and ask.** The `submit_feedback` tool's own contract requires showing the
   message and confirming before sending, so present the full draft, then this pinned 👉 question
   (INV-056), and end the turn on it:

   > 👉 **This looks like an issue in the Senzing MCP server rather than the bootcamp. Send the report above to Senzing? Reply with a number:**
   >
   > 1. **Yes, send it** — helps get it fixed upstream for everyone.
   > 2. **No, keep it local** — it stays in your feedback file only.

   State plainly, above the question, that submissions are **anonymous**: the server records no
   sender identity, so Senzing cannot reply about it. If they want a response, `support@senzing.com`
   is the channel with a return path. Saying no costs them nothing — the entry is already saved.

4. **On "yes":** call `submit_feedback` with `category` = `bug` for wrong/unusable output, `feature`
   for a missing capability, and `message` = the approved draft. Relay whatever the server returns
   **verbatim** — it carries the anonymity notice and the support address, and those are the
   bootcamper's only follow-up route.

5. **Record the outcome** in the entry's `**Upstream:**` field, replacing `offer pending` with the value of its closed set
   (`not applicable | offer pending | offered, declined | submitted YYYY-MM-DD | submission failed: <reason> | submission blocked: <reason>`) that says what happened.
   Update the entry in place for this field only — do not rewrite the prose (append-only
   elsewhere). ⛔ (INV-281) **Never leave `offer pending` once an answer exists.** It means only
   that the question is still open.

   ⛔ **(INV-281) `submission blocked:` is for a *consented* send the runner was forbidden to make — it is
   not a synonym for any other value.** Use it when the answer was **yes** and the send could not
   happen because the session operates under a no-send rule (a maintainer `/dry-run`, which
   never sends on a Bootcamper's in-character yes). ⚠️ **Never record that as
   `offered, declined`.** The bootcamper agreed; writing down that they refused is false, and it
   is the one value that reads as *"this was considered and rejected"* to anyone deciding later
   whether the finding is still owed upstream. `submission failed:` is also wrong — nothing
   failed, and nothing will succeed on a retry.

6. **A failed or unavailable submission never blocks anything.** If the tool errors or the MCP server
   is unreachable, say so in one line, record `submission failed: <reason>`, and continue to Step 4.
   The local entry is the durable record; upstream delivery is a bonus.

⛔ Ask this **once** (INV-006). If the bootcamper declines, do not re-offer for the same entry.

### Unanswered offer on resume

An entry still reading `offer pending` means the offer was presented, or was due, and never
answered: the session ended on the question, or graduation's batch never got its answer. It is
the open question, not an answered one.

⛔ (INV-006) **On resume, present the unanswered offer once more, then never again.** This is
the unanswered question being presented, not a re-ask. When a resumed session finds one or more
`offer pending` entries in `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`:

1. Show the draft for each, stripped as step 2 requires, and ask step 3's pinned 👉 question once
   for all of them, the way graduation Step 0 batches its offer.
2. ⛔ (INV-251) **The offer is its own turn.** End the turn on it. Re-present the pending bootcamp
   👉 question on the next turn, after the answer, never beside the offer.
3. Replace every `offer pending` value with the outcome, as step 5 does, and handle a failure as
   step 6 does. The answer applies to every entry in the batch.

An entry the bootcamp never returns to stays `offer pending`, and `/feedback-to-issues` treats its
report as still owed.

## Step 4: Confirm and return

- Only after Step 3b confirms the entry is on disk, present the pinned exit banner **verbatim**, marking the return from feedback to the bootcamp:

  ```text
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  FEEDBACK SAVED — BACK TO THE BOOTCAMP  ✅
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

  Then, in one line: "Saved to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`. You can add more anytime by saying \"bootcamp feedback\"."
- Do NOT submit feedback anywhere external on your own initiative. The **only** sanctioned external path is Step 3c: an `mcp-server`/`both` verdict, the local entry already saved, the exact message shown, and the bootcamper answering yes to the pinned question. Everything else — `plugin`, `host` and `unclear` verdicts, and any other destination — stays local.
- The exit banner and confirmation are statements, not questions. Immediately after them, return the bootcamper to exactly where they left off by **re-presenting the exact pending 👉 bootcamp question** they were on, verbatim (INV-006 ask-once), so that exactly one 👉 ends the turn (INV-251). Do not make them re-navigate, and do not merge the feedback questions with the resumed bootcamp question into one turn.

## Silent in-run append (no bootcamper involvement)

⚠️ **This is a different entry point to the same file, not a variant of the flow above.**
Everything from Step 1b to Step 4 — the entry banner, the 👉 questions, the exit banner, the
resumed question — belongs to the *bootcamper-initiated* flow and **none of it applies here**.
What is shared is the file, the Step 3 template, and Step 3b's verify-it-landed discipline.

**When to use it.** When `ground-rules.md` → "Reversed decisions: file them when they happen"
fires: an audit of the engine's own output has caused you to withdraw a prior decision. Also used
by `../graduation/SKILL.md` Step 0, which files the same way at the end of the run.

**How:**

1. Ensure the file exists exactly as Step 1 describes (same path, same header).
2. Append a `## Improvement:` entry using the **Step 3 template verbatim**, with:
   - **`Source:` `self-observed (assistant retrospective)`** — never `bootcamper-reported`
     (INV-116). A maintainer must be able to tell the two apart; they carry different weight.
   - **`Module:`** the module you were in when the reversal happened.
   - **`Routing:`** the Step 2b verdict with its one-line reason. A reversed *mapping* is usually
     `plugin` (the guidance let you do it), but triage rather than defaulting.
   - **`Upstream:`** `not applicable`, or `offer pending` when Step 2b says `mcp-server`/`both`.
     ⛔ (INV-012) **Do not offer the upstream forward here** — that offer needs a 👉 question, which
     this path must not ask. Leave it for graduation's Step 0, which batches one offer for the
     whole session and replaces the value.
   - **What happened / Why it matters / Suggested fix** describing what *you* did and withdrew,
     in the plain past tense. The decision, the evidence that overturned it, and the effect of
     withdrawing it.
3. **Verify it landed** exactly as Step 3b requires: re-read the file, confirm the entry is
   present, append again if not. An unwritten note is worse than none, because nobody is watching
   for it.
4. **Note that you filed it** so graduation's Step 0 does not file the same finding twice.

**Constraints:**

- ⛔ **Silent.** No banners, no 👉 question, no announcement, no line in the bootcamper-facing
  output (INV-012). The bootcamper never authors, approves, or hears about this entry.
- ⛔ **Never blocks.** If the append or the re-read fails, warn on stderr and continue the module
  (INV-048). A failed note must not interrupt a pending question, delay a step, or become a
  to-do for the bootcamper.
- ⛔ **Local only.** The single sanctioned external path remains Step 3c, which this route does
  not use.
- **Include the reversal even when it is unflattering, and especially when the correction made a
  number worse.** A correction that lowered a score you reported is the most useful kind: it means
  the earlier number was wrong and something downstream may have been decided on it.
