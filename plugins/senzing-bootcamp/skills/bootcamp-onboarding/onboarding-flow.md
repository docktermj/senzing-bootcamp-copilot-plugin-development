# Onboarding Flow (fresh bootcamp)

Follow these steps in order. Follow `ground-rules.md` throughout. Do not narrate administrative
work in detail: do the setup quietly, then present the WELCOME banner.

The bootcamper-facing preface is deliberately short — it welcomes the bootcamper and orients them,
then hands off to the first module. It follows this order:

1. **Welcome + overview** (WELCOME banner + overview) — step 3.
2. **Any questions** — step 4.

Steps 0-2 are administrative and mostly silent; they run before the WELCOME banner.

**Setup questions live in the Bootcamp preparation module, not the preface.** The
Core-vs-Customized path choice, per-module selection, level of detail (verbosity), and programming
language are asked in
the first module — **Bootcamp preparation**
(`../bootcamp-preparation/SKILL.md`) — which the preface hands off to at step 5. That module also
initializes version control (git, no prompt — INV-095). (The
software-integration and deployment-target questions are asked later, in Module 1 Phase 2, per
INV-097 — not in the preface and not in Bootcamp preparation.) Entity resolution
concepts are also **not** part of the preface: they are an optional module
(`../module-00-entity-resolution-concepts/SKILL.md`) run only when selected during Bootcamp
preparation.

## 0. Setup preamble

Tell the bootcamper, in your own words:

"I'm going to do some quick administrative setup: creating your project directory and checking
your environment."

Read the plugin version from the plugin manifest (`plugin.json`, the `version`
field) and hold it to display with the WELCOME banner (step 3) and to record in the recap.
**Resolve the manifest in this order and stop at the first that reads (INV-252):**

1. `${PLUGIN_ROOT}/plugin.json`, when `PLUGIN_ROOT` is set **and
   non-empty**.
2. `<this-skill-dir>/../../plugin.json` — this skill's own directory, two levels
   up. The harness supplies that directory at invocation, so by construction it belongs to the
   plugin whose files are running. This is the same skill-relative fallback INV-185 documents for
   bundled scripts.
3. "Unknown" — reported as the version, never replaced by a guess.

⛔ **Never search the filesystem for a `plugin.json`, and never read one outside the resolved
plugin root.** Two plugin roots on one machine is a normal state, not a broken one — an installed
plugin plus a clone, or an upgrade whose old copy was never removed — so the first match a search
reaches is not the plugin serving this run. With `PLUGIN_ROOT` empty, a search made the
banner report `v0.5.0` from a second checkout while `0.5.1` was running, and a version line that
can be wrong is worse than none: its whole job is provenance.

Every other step needing the plugin version resolves it the same way — the feedback entry
(`feedback.md`), the recap header (`module-completion.md`) and the recap's provenance block
(`../graduation/SKILL.md`) — so all four report one version.

## 0b. MCP health check (required)

Confirm the Senzing MCP server is reachable before starting. It is required: it generates SDK
code in the chosen language, looks up Senzing facts, and provides working examples.

- **Probe:** call `get_capabilities` (about a 10-second timeout) — never a content-returning
  tool (INV-204). This is the call
  `ground-rules.md` → "Session start" already requires once before any other Senzing MCP call, so
  it doubles as the reachability probe and the preface makes **one** MCP call here, not two. Its
  response is also the tool manifest the guide needs anyway.
  - Do **not** probe with `search_docs`. It was specified here as "a lightweight call such as
    `search_docs(query="health check")`", which it is not: that query returns a multi-page FAQ
    article (~5 KB) for a question that only needed "did the server answer at all".
- **Success** (any response, even empty results): proceed silently.
- **Failure** (timeout or error): display a blocking message and STOP. Do not proceed until the
  bootcamper fixes the connection and says "retry":

  ```text
  The Senzing MCP server is unreachable.

  The MCP server is required for the bootcamp - it generates SDK code, looks up Senzing facts,
  and provides working examples. The bootcamp cannot proceed without it.

  Troubleshooting:
  1. Verify internet connectivity.
  2. Confirm the "senzing" MCP server is configured and enabled in GitHub Copilot
     (it ships with this plugin's .mcp.json, pointing at https://mcp.senzing.com/mcp).
  3. If behind a corporate proxy, allowlist mcp.senzing.com.

  After fixing the connection, say "retry".
  ```

## 1. Project setup

Do this silently:

1. Create the working directory structure: `src/`, `data/`, `docs/`, `config/`, `database/`
   (and subfolders as modules need them - see file placement in `ground-rules.md`).
2. Create `config/bootcamp_progress.json` and `config/bootcamp_preferences.yaml` if they do not
   exist.
3. Create the project `README.md` if it does not exist, with the two headings Module 1 Step 12
   fills in and a placeholder line under each. It is the **only** `.md` permitted at the project
   root besides the generated `production/` deliverable (INV-017, and the root whitelist in
   `ground-rules.md`) — do not add others.

   ```markdown
   # <project name>

   ## Overview

   _To be completed during the bootcamp._

   ## Business Problem

   _To be completed during the bootcamp._
   ```

   Nothing else belongs in this file: Module 1 Step 12 fills these two sections and adds nothing
   further, and every other artifact has its own home under `docs/` (INV-017). Creating it here
   is what makes Step 12 an **update** rather than an instruction to edit a file that does not
   exist — the file is written silently, like the rest of this step (INV-012).

(The Kiro Power installed Agent Hooks here via `createHook`. In the GitHub Copilot plugin, hooks ship
with the plugin in `hooks/hooks.json` and are already active - there is no hook-install step.)

## 2. Prerequisite check

Verify the basics for the bootcamper's platform: a working shell, Python 3 (for helper
scripts), and internet access to the MCP server. Report anything missing and let them fix it.
If the Senzing SDK is not yet installed, note that SDK setup covers installation - do not block.

(A full preflight script is a later porting phase; keep this check lightweight for now.)

## 3. Welcome and overview (preface item 1)

State that setup is complete ("Administrative setup is complete. The bootcamp is starting."),
then display the WELCOME banner:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then show the plugin version as a one-line statement (INV-105): `Senzing Bootcamp vX.Y.Z`.

**Verbosity applies here only if a preset already exists.** Read `verbosity` from
`config/bootcamp_preferences.yaml`: when it is `minimal`, suppress this line; otherwise show it.
⛔ On a **fresh** bootcamp there is no preset yet — verbosity is chosen in Bootcamp preparation
(INV-075 moved it out of the preface, superseding INV-024), and step 4 below writes no preferences —
so the line is simply shown, and that is correct rather than an oversight. The suppression path is
reachable only on a resumed run, or when the bootcamper pre-seeded the file (INV-133). Do not stall
trying to honor a preference that cannot exist yet, and do not ask for verbosity here.

Then give the overview (cover naturally, do not ask a question yet).

⛔ **Every bullet below has a verbosity treatment — none is unconditional (INV-214).** Three carry
their own (the version line above, and the feedback-trigger and make-a-note bullets below); the rest
are governed as a group, so there is no bullet whose behavior under a preset is left to guesswork:

| Preset | The overview is |
|---|---|
| `minimal` | the **module list** plus the **how-long-it-takes** bullet, and nothing else — orientation only |
| `concise` | all bullets except *guided discovery* and *unfamiliar terms*, each trimmed to one line |
| `standard` / `detailed` | every bullet below, as written |

The split is orientation versus encouragement: the module list and the resume-and-time facts are
what a bootcamper needs to navigate, and the rest is framing an expert moving fast does not. On a
**fresh** bootcamp no preset exists yet, so every bullet is shown and that is correct rather than an
oversight (INV-075/INV-133) — the reduced forms are reachable only on a resumed run or a pre-seeded
file.

- This is a **guided discovery** of how to use Senzing. It is not a race - take it slow, read
  what the bootcamp tells you, and ask questions any time. Be curious.
- Goal: get comfortable generating Senzing SDK code, finishing with running code you can build on.
- You finish with a professional **recap PDF** — a keepsake of everything you built, module by
  module, to keep and share with your team.
- The bootcamp is a sequence of named modules: **Bootcamp preparation**, *Entity Resolution
  Concepts* (optional), **Discover the Business Problem**, **SDK setup**, *System verification* (optional),
  *Truth Set visualization* (optional), **Data collection**, **Data Quality, Mapping, and Transformation**, **Data
  processing**, **Query, Visualize and Discover**, and **Bootcamp graduation**.
- Right after this welcome, the first module — **Bootcamp preparation** — lets you pick how to run
  the bootcamp: **Core** (every module, in order) or **Customized** (you choose which optional
  modules to include). It also sets your level of detail and programming language, and sets up
  version control for you automatically (no question). Required modules always run; the optional
  ones are yours to include or skip.
- One thing to know if you customize: *Truth Set visualization* is the interactive web app that
  shows Senzing working on your machine — if you deselect it, you won't see that visual
  verification.
- Licensing: a built-in evaluation license covers the bootcamp's demos. If your own data needs
  more capacity, Data collection checks once your record count is known and walks you through the
  options then.
- If you hit unfamiliar terms (Entity Specification, DATA_SOURCE, entity resolution), ask and
  I'll look up the current definition from the Senzing docs on demand.
- **How long it takes:** the bootcamp is **module-sized, not clock-sized** — each module tells you
  its own time estimate right before it starts, so you always know what the next stretch costs.
  There is no fixed total: it depends on whether you pick Core or Customized (still to come, in
  Bootcamp preparation) and on how fast the SDK downloads and installs on your machine. **You do
  not have to finish in one sitting** — progress is saved as you go, and you can stop and pick up
  where you left off.
- **If anything about the bootcamp itself is confusing, broken, or missing, tell me the moment you
  notice it:** start a message with **"bootcamp feedback:"** and I will capture it. You do not lose
  your place — the note is saved under `docs/feedback/`, then the bootcamp question you were on
  comes straight back and we carry on. No need to save it for the end.
- **Had an idea of your own? Say "make a note" and I'll write it down for you.** Ideas, questions,
  reminders and to-dos about *your* work — "remind me to check these counts", "note to self: try
  `dba_name` as a second name". They are saved in your own words to `docs/bootcamp_notes.md`, they
  go into the recap you keep at the end, and they are never sent anywhere. You keep your place here
  too.

**The note bullet is verbosity-aware on the same terms as the feedback bullet** (INV-011/INV-012):
suppress it under `minimal`; one line under `concise` ("Say \"make a note\" any time — it is saved
in your words and goes into your recap."); otherwise the full bullet. ⛔ **State it; never pose it
as a 👉 question**, and do not repeat it at every module start — it is an always-available
control (INV-254), and once, here, is the point. An any-time control nobody is told about is an
any-time control nobody uses.

**The feedback-trigger bullet above is required here** (INV-196: the trigger phrase is named in
bootcamper-facing text before the first content module, as a statement and never a 👉 question,
and it says that using it costs them nothing), **and it is verbosity-aware, exactly like the
version line above**
(INV-011/INV-012 — the treatment INV-096 gives the time estimate): under `minimal`, suppress it;
under `concise`, one line ("Say \"bootcamp feedback:\" any time — it is captured and you keep your
place."); otherwise the full bullet. ⛔ Same caveat as the version line: on a **fresh** bootcamp no
preset exists yet, so the full bullet is simply shown and that is correct, not an oversight
(INV-075/INV-133). ⛔ **State it; never make it a 👉 question** — it needs no answer, and INV-012
forbids output the bootcamper cannot act on. ⛔ **Do not repeat it at every module start** — the
module-start apparatus is already dense (INV-028-031, INV-096, the model/effort nudge), and this is
an always-available control (INV-010). Once, here, is the point; graduation's closing invitation
(`../graduation/SKILL.md`, Step 7) stays as it is.

## 4. Any questions (preface item 2)

Before continuing, invite final questions:

👉 **Do you have any questions before we get started?**

- A clarification question: answer it (using the MCP server for any Senzing facts), then ask once
  more whether they have other questions before continuing.
- A readiness signal ("no", "let's go", "ready", "start"): proceed to step 5.

This is NOT a hard gate: if they say they are ready, advance.

⛔ **"How long will this take?" is the single most likely question here — answer it from step 3's
overview, and NEVER invent a total.** Say what is true: the bootcamp is module-sized, each module
states its own estimate at its start, the total depends on the Core-vs-Customized choice they have
not made yet and on install/download speed, and progress is saved so it can be done across
sittings. ⛔ **Do not offer a figure like "about 4-6 hours."** No per-module estimates exist in this
plugin to sum — the modules state the *requirement* to give an estimate, not values — so any total
would be fabricated, which is exactly what INV-096 exists to prevent. A number invented here is
worse than no number: it sets an expectation the rest of the bootcamp did not agree to.

(No preferences are written in the preface. All setup choices — path, module selection, verbosity,
programming language, git — are captured and persisted in the Bootcamp preparation module in a
single consolidated write, INV-058.)

## 5. Hand off to the Bootcamp preparation module

Invoke the `bootcamp-preparation` skill. Bootcamp preparation is the **first, mandatory module**:
it asks the Core-vs-Customized path choice, per-module selection, verbosity, and programming
language, initializes version control (git, no prompt — INV-095), persists these in one
consolidated write, then hands off to the first selected
content module (the optional Entity Resolution Concepts primer if selected, otherwise Discover the Business Problem).
The selected modules then run in the order recorded in `selected_modules`, each ending with the
standard module completion process in `module-completion.md`.
