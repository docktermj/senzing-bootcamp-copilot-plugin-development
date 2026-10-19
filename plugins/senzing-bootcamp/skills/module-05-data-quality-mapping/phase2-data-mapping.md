# Module 5, Phase 2: Data Mapping (steps 8–20)

Continues from Phase 1. Follow the ground rules; `🛑`/`⛔` are internal directives: do not
render them. Signal a stop by ending the turn on the single 👉 question and waiting.

**Iterative process:** Users can jump between steps. The goal is a working transformation
program, not strict sequence.

**Before starting:** Confirm which data source. Track multi-source progress (In Progress /
Complete / Pending).

**MCP-first invariant (this phase especially):** ALL JSON mappings and attribute names come
from the `mapping_workflow` MCP tool. NEVER hand-code or guess Senzing attribute names, and
never reuse mapping output from one source for another. Never guess SDK method signatures: use
`generate_scaffold` / `get_sdk_reference`.

<a id="receiving-a-quality-iteration"></a>

## Receiving a `quality_iteration` (from Query, Visualize and Discover)

⛔ **(INV-284) Check for it before anything else in this phase.** When
`config/bootcamp_progress.json` carries a `quality_iteration` whose `stage` is `remap`, the
Bootcamper chose the return at Module 7 step 3b, and this is not a run of this module: show no start
banner, journey map or overview, write no Module 5 checkpoint (leave `current_module` and
`current_step` as Module 7 set them, so its progress is not overwritten), and remap only the sources
the key names. Which stages run and where Module 7 resumes are stated once, in
`../module-07-query-visualize-discover/phase1-query-visualize.md` step 3b → "The quality-iteration
route" (INV-300); this block says only how the remap is done.

For each source in `sources` not yet listed in `completed`, in order:

1. **Record what was loaded, before anything is rewritten.** Write the RECORD_IDs of the source's
   current load input to `data/mapping/{source_name}_loaded_record_ids.txt`, one per line: its
   registry `file_path`, narrowed by its `load_subset:` block when one is recorded (Module 6
   Phase B's [subset record](../module-06-data-processing/phaseB-load-first-source.md#load-subset-record)).
   Module 6's receiving branch compares the remapped file against this set. If the file already
   exists, an interrupted return wrote it: keep it, because the load input may since have been
   rewritten.
2. **Run Steps 8–18 for this source:** a full `mapping_workflow` run, as Step 8's per-source
   requirement demands, never a reuse of the earlier run's output. Address the finding Module 7 named
   in its explanation statement where it arises, most often at Step 11. Step 18 rewrites
   `docs/mapping/{source_name}_mapper.md` and the source's lineage document. The source's own
   `config/mapping_state_[datasource].json` is still written and deleted as "Mapping state
   checkpointing" says; only the steps' `config/bootcamp_progress.json` checkpoints are not written.
   **A named source with `fast_pathed: true` is remapped too:** "Skip fast-pathed sources" below
   does not apply to a source the key names. Step 17's registry write also sets `fast_pathed:
   false`, so Module 6 reloads the remapped output at the `file_path` Step 18 records, not the
   original `data/raw/` file.
3. ⛔ **(INV-177) Step 19's relocation guard runs between sources:** before the next named source's
   `mapping_workflow(action='start')`, confirm this source's profile report, `schema_hints.md` and
   `JOURNAL.md` are relocated under their source-qualified names. Step 19's per-source completion
   check also applies: `docs/mapping/{source_name}_mapper.md` exists before the source is done.
4. **Add the source to `completed`** in one quiet write.

**Phase 1, Phase 3 and Step 20 do not run.** ⛔ **(INV-284) No re-scoring, no test load, and no
Module Completion:** no second Module 5 recap section, no progress update, no transition question,
and `data_quality_mapping` is not added to `modules_completed` again.

**When every named source is remapped,** set `stage` to `reload` and `completed` to `[]` in one
write, then continue into Module 6's
[Receiving a `quality_iteration`](../module-06-data-processing/phaseB-load-first-source.md#receiving-a-quality-iteration).

## Skip fast-pathed sources

Before starting the mapping workflow for a source, check its registry entry in
`config/data_sources.yaml`. If `fast_pathed` is `true` and `mapping_status` is `complete`, skip
this source entirely: it has already been routed to Module 6. Proceed to the next unmapped
source. A source a `quality_iteration` names is not skipped: the receiving branch above remaps it.

## Mapping verbosity check (before starting the mapping workflow)

Read `config/bootcamp_preferences.yaml` and check the `mapping_verbosity` key.

- **If `mapping_verbosity` is `null` or absent:**

  👉 **Before we start mapping, which mode would you like? Reply with a number:**

  1. **Verbose mode** — I'll show each mapping step in detail: field detection, attribute selection rationale, transformation preview.
  2. **Concise mode** — I'll map quickly and show only the final mapped record and any warnings.

  *(Internal: end the turn on this question and wait.)* Persist their choice (`verbose` or
  `concise`) to `mapping_verbosity` in `config/bootcamp_preferences.yaml`.

  If the bootcamper skips or doesn't answer directly: default to `verbose`, persist it, and
  say: "Defaulting to verbose mode: say 'switch to concise' anytime if you want less detail."

- **If `mapping_verbosity` is already set to `verbose` or `concise`:** Say "Using your
  [verbose/concise] mapping preference from last time: say 'switch to [other]' if you'd prefer
  [less detail/more detail]" and proceed without waiting.

## Mid-mapping verbosity switch

If the bootcamper says "switch to verbose", "switch to concise", "more detail", "less detail",
or any natural variant indicating they want to change mapping verbosity:

1. Update `mapping_verbosity` in `config/bootcamp_preferences.yaml` to the requested mode.
2. Apply the new mode immediately to all subsequent presentation output.
3. Confirm briefly: "Switched to [verbose/concise] mode.": then continue without interruption.

## Mapping state checkpointing (applies to every step below)

`mapping_workflow` is stateful. Each call returns state that MUST be passed, unchanged, to the
next `mapping_workflow` call for that source: never alter or reconstruct it. After each step,
write a checkpoint to `config/mapping_state_[datasource].json`:

```json
{"data_source":"CUSTOMERS","source_file":"data/raw/customers.csv","current_step":3,"completed_steps":["profile","plan","map"],"decisions":{"entity_type":"PERSON","field_mappings":{"full_name":"NAME_FULL"}},"last_updated":"2026-04-14T10:30:00Z"}
```

On session resume: read the checkpoint, show the user where they left off, restart
`mapping_workflow`, fast-track through decided steps, and resume from the first incomplete step.
**Delete the checkpoint when mapping for that source is complete.**

When step-3 validation rejects a payload, append the **verbatim** returned text to a
`validation_rejections` array on the same checkpoint, and record `mapper_source` once the mapper
exists (`mapping_workflow` or `entity_specification`, with the reason when it is the latter):

```json
{"data_source":"NOMINO-RISK","current_step":3,"validation_rejections":["<raw rejection text, unedited>"],"mapper_source":"entity_specification","mapper_source_reason":"step-3 validation rejected twice with a truncated error naming no field"}
```

Keep the rejection text unedited — truncating or summarizing it destroys the only evidence the
upstream defect can be diagnosed from.

## File placement during the workflow

`mapping_workflow` downloads workflow resources and later produces output into a workspace
directory. Override any MCP-suggested `/tmp/` paths to project-local paths. Place files per the
ground-rules file-placement contract:

- Reusable resources at download time: transformation/workflow `.py` scripts → `src/`; the
  entity specification (`senzing_entity_specification.md`) → `docs/reference/`; other reference
  `.md` → `docs/`; config JSON → `config/`; data → `data/`.
- **Transient run artifacts stay in the workspace while the run is in progress:** the workflow
  reads and writes them for its own use. Do NOT relocate, delete, or redirect these mid-run:
  `profile_report.md` (or the `profile_report_<stem>.md` files a multi-file start writes),
  `schema_hints.md`, `JOURNAL.md`, and generated JSONL output.
- **After the run for a source completes (after the iterate/finalize step), relocate the
  transient artifacts to their durable homes — and source-qualify the three mapping-phase
  Markdown filenames as you do:** `profile_report.md` → `docs/mapping/{source_name}_profile_report.md`,
  `schema_hints.md` → `docs/mapping/{source_name}_schema_hints.md`, `JOURNAL.md` →
  `docs/mapping/{source_name}_JOURNAL.md`. Mapping working data (`*_mapping_spec.json`, the
  per-source `{source}_sample.jsonl`, intermediate analyzer JSONL) → `data/mapping/`. Final
  transformed, load-ready JSONL stays in `data/senzing-ready/`, and nothing partial does (INV-084).
  - ⛔ **The profile report has TWO possible filenames, and BOTH must be relocated.** A single-file
    start writes `profile_report.md`; a multi-file start writes one
    `profile_report_<stem>.md` **per input** (server 1.33.0, verified 2026-08-23 — see "the
    profile-report filename depends on how many files you pass"). Relocate whichever the workspace
    actually received: `profile_report.md` → `docs/mapping/{source_name}_profile_report.md`, and
    each `profile_report_<stem>.md` → `docs/mapping/{source_name}_profile_report_<stem>.md`.
    ⛔ **The rule is that NO profile report is left in the shared workspace, whatever the server
    named it** — list the workspace and relocate every `profile_report*` file rather than matching
    one literal name. A suffixed report left behind is the exact overwrite INV-177 exists to
    prevent, arriving through a filename the invariant's original text did not cover.
  - ⛔ **The source qualifier is required, not tidiness (INV-177).** Every source's `mapping_workflow` run
    uses the **same** `workspace_dir` (`data/mapping`, per step 8), and the workflow writes those
    three files there under **fixed** names — verified against the live tool: step 1's instructions
    name `<workspace_dir>/profile_report.md`, `<workspace_dir>/schema_hints.md` and
    `<workspace_dir>/JOURNAL.md`, with `JOURNAL.md` explicitly append-only
    (`mapping_workflow(action='start')`, server 1.32.2, verified 2026-07-29). So relocating them
    under their unqualified names makes source B's run overwrite source A's durable record — and
    for `JOURNAL.md`, append source B's entries onto source A's log. This matches the qualifier
    step 18 already requires for `docs/mapping/{source_name}_mapper.md`.
- If a downloaded file matches no placement rule, leave it in the workspace and surface it as a
  warning rather than inventing a destination. If the plugin write-gate blocks a write, leave
  the file in the workspace and report it: do not retry against a different location.

The plugin's preToolUse write-gate enforces the temp-path and secret rules; file-type placement
is your responsibility. (The Kiro `organize_mapping_files.py` and `generate_docs_index.py`
scripts are a later porting phase: place files directly per the contract above for now.)

## Calling `mapping_workflow` correctly (⛔ read before step 8)

Verified against the live tool schema on 2026-07-26; rule 4 added and re-verified on server
1.33.0, 2026-08-23. Rules 1-3 are details the workflow **cannot run without** — each one was wrong
or missing here before, and each fails at the first call rather than degrading. Rule 4 is what a
mistake **costs**.

1. ⛔ **`start` requires BOTH `file_paths` and `data.workspace_dir`.** The tool's own contract:
   "The call WILL FAIL without both", and "do NOT assume `/tmp` exists". Pass the project-local
   mapping directory, which is where this bootcamp already keeps mapping working data (INV-050) —
   never `/tmp`, never a home-relative path:

   ```text
   mapping_workflow(action='start',
                    file_paths=['data/raw/<source>.csv'],
                    data={'workspace_dir': 'data/mapping'})
   ```

   This is the same rule as the file-placement contract above, expressed as a parameter: the
   workspace is where the tool writes its scripts, reference docs, mapper code and outputs, so
   pointing it at `data/mapping/` is what keeps those files inside the project.

2. ⛔ **There are exactly five actions: `start`, `advance`, `back`, `status`, `reset`.** Nothing
   else is valid. Every step below advances with **`action='advance'`**; the step's data goes in
   `data` (or the typed `payload`), and its field names are **not** action names. Five field names
   were previously written as actions here — `profile_summary`, `entity_plan`, `schema_mappings`,
   `paths`, `verdict` — which the server rejects.

3. **Echo the returned `state` verbatim on every call after `start`.** Each response carries an
   opaque `state` object; pass it back exactly, never reconstructed from memory or from this
   bootcamp's own checkpoint file. (The checkpoint above is for *bootcamper-facing resume*, not a
   substitute for the server's state.) If the state is lost, restart with `action='start'`.

4. ⛔ **A malformed advance costs one of five, and five ends the run.** A payload the published
   advance schema forbids is rejected with an `ENFORCEMENT NOTICE` that names a machine-readable
   reason code — `step2_missing_plan_key`, `step3_missing_schema_mappings` — and states the budget
   in the server's own words: *"This is grammar-impossible advance N of 5 before this workflow
   terminates."* The count comes back as `grammar_violation_count` in the returned `state`.

   **A successful advance clears it.** Verified on server **1.33.0, 2026-08-23** by reproducing the
   whole sequence: a bad payload at step 2 returned *"advance 1 of 5"* and
   `grammar_violation_count: 1`; the next **valid** advance returned a `state` with the field
   **absent**; a second bad payload, at step 3, reported *"advance 1 of 5"* again — not 2. So from
   the caller's side it counts **consecutive** failures, not failures per run. (Whether the server
   resets a counter or simply rebuilds `state` per step is not observable from here, and the effect
   is the same either way, because rule 3 requires echoing the returned `state` verbatim.)

   ⛔ **On a rejection, re-read the response's `advance_schema` and match it field for field —
   do not retry a variant.** The rejection carries the exact schema for the step you are advancing
   *from*; a second guess spends a second violation, and five in a row ends the workflow. This
   module runs one workflow **per source**, so the budget is per source rather than per module — but
   because the count resets, losing a run needs five consecutive misses, not five across the
   session.

   ⚠️ **A rejection is evidence about that payload, never a general map of what the tool
   tolerates.** Not every payload the published schema fails to describe is refused — some are
   accepted with `status: ok` and no notice at all (observed on the same server and date). So do
   not infer from one enforcement notice which other shapes are safe, and do not infer from a
   silent acceptance that the schema sanctions what you sent. ⛔ **Follow each step's stated shape
   regardless** — at step 1 that means the **array** form of `profile_summary`, per the step-1
   caution later in this file.

**If a step's guidance arrives truncated mid-sentence, suspect the client read cap before the
server.** The tool embeds each step's advance schema verbatim in `instructions` and keeps any single
step under 64 KB, and its contract warns that a smaller read cap "silently TRUNCATES step guidance
mid-text and **reads as a server bug**." So a truncated step — including a step-3 rejection naming no
field — is a read-cap symptom first and an upstream defect second. Check that before invoking the
INV-125 fallback, and say which cause you concluded; INV-125 requires recording the raw failure, and
a documented cause is part of that record.

### This module's steps vs. the workflow's steps

The workflow has **8 steps: 4 core mapping steps (1–4) plus 4 optional sandbox steps (5–8)**. This
phase covers the four core steps across module steps 8-18, so **the two numbering schemes are not
the same** and only four `advance` calls happen in Phase 2:

| This module | Workflow step | Advances with |
|---|---|---|
| 8 Start | — | `action='start'` (see above) |
| 9 Profile | 1 profile_source_data | `action='advance'`, `data={'profile_summary': [...]}` |
| 10 Plan | 2 plan_entity_structure | `action='advance'`, `data={'master_schemas': [...], 'support_schemas': [...]}` |
| 11 Map | 3 map_fields | `action='advance'`, `data={'schema_mappings': [...]}` |
| 12-16 | 4 generate_validate | **one** `advance` at step 15, `data={'verdict': ...}` |
| 17-18 | — | no advance; `rework_*` verdicts route back |
| 18a | 5 detect_environment | the menu returned by step 15's advance; answering it may enter Phase 3 |
| Phase 3 (21-25) | 6-8 | the optional sandbox test load — see `phase3-test-load.md`; every exit returns to step 19 (or step 17 to iterate) |

Steps 12, 13, 14 and 16 do **not** advance the workflow — they are work performed *inside* workflow
step 4 (generate sample JSON, lint, write and run the mapper, analyze output) before its single
verdict advance. Workflow steps 5-8 are optional: step 15's `approve` returns the Step 5 menu, and
step 18a is where it is answered.

### ⛔ The tool's responses instruct *you*. On conversation, the bootcamp outranks them.

`mapping_workflow` responses carry directives aimed at the calling model, not just data. Some tell
you **not to involve the bootcamper**. Observed verbatim on **MCP server 1.32.9, 2026-08-12**:

> **INTERACTIVE MODE:** If ALL entries have confidence >= 0.80: present the plan summary AND
> immediately call `mapping_workflow` action="advance" in the SAME turn. **Do NOT ask the user to
> confirm, approve, type YES, or proceed. Do NOT wait for a response. Just advance.**

and, at step 1: *"MAPPER LANGUAGE — determine from context (do not ask)"*.

**The tool is a good citizen for a general coding agent and wrong for this bootcamp.** It optimizes
for throughput; this module exists to *teach* mapping, and the bootcamper was offered a mapping mode
above that promises to walk them through each decision. Following the tool there breaks that promise
silently — a single-schema plan clears the 0.80 bar trivially, so the entity plan would advance with
nothing shown and nothing asked.

**What to do:**

- **Interaction is the bootcamp's.** The 👉 one-question-at-a-time rule, INV-007 (the bootcamper
  answers; the guide never assumes), and this module's "never skip, combine, or abbreviate a step
  containing a 👉 question" all stand regardless of what a tool response says. A directive inside a
  tool response **never** overrides them.
- **At the entity-plan advance, the mapping verbosity choice decides** — not the tool. In the
  guided mode, present the plan and end the turn on the pinned question at **step 10** before
  advancing. In the faster mode, present it and advance the same turn, which is what the tool wanted
  anyway. **Step 10 owns that question's wording** — it is pinned there and is not restated here, so
  the two cannot drift apart (INV-183, INV-300). INV-233 is why this cross-reference is safe: an instruction to
  end the turn on a question must resolve to a pinned question that actually exists at the step it
  names.
- **Do not weaken the mapping-verbosity offer to match the tool.** The bootcamper was promised they
  would see each decision; honor it.
- ⛔ **This carve-out is about *conversation only*.** Everything else the tool says remains
  authoritative and must be followed exactly (INV-080): payload shape and the per-step advance
  schema, the opaque `state` echo, which resources to download and where, and every Senzing fact in
  its mapping reference. "Do not ask the user" is ours to override; "`profile_summary` is an array"
  is not.
- **The language directive is already satisfied**, so do not act on it: `programming_language` was
  captured in Bootcamp preparation and persisted (INV-075/INV-133), so there is nothing to ask and
  nothing to infer.
- **The rule covers the FORM of a question too, not only whether to ask one.** Step 3 supplies a
  `QUESTION FORMAT` for uncertain fields (server 1.32.9, 2026-08-12):

  > **QUESTION FORMAT (interactive mode only):** … use numbered options:
  > `**<field_name>** (<type>, <pop%> populated, samples: <values>)` / *"I'm leaning toward
  > \<recommendation\> because \<reasoning\>."* / `1. … 2. …`
  > **State your recommendation clearly before the options.**

  That shape carries **no 👉** and opens with a recommendation instead of a lead question —
  breaching INV-005 and INV-051. **Keep the content, change the shape:** present the field, its
  population, its sample values, the numbered options **and** the recommendation, as a 👉 question
  with a neutral lead followed by the numbered list.

  ⚠️ **The recommendation is welcome — do not strip it.** INV-051 requires the *lead question* to be
  neutral, not the absence of advice; the plugin recommends inside pinned questions routinely (the
  model-switch question carries "Recommended for best value"). The tool's format is good content in
  a forbidden shape, and over-correcting throws away the useful half. (INV-205, scope extended
  2026-08-12.)

### ⛔ A second entity hiding in a column: `embedded_master`, and when to go `back`

Some sources carry a **secondary entity inside a column** — an employer on an employee record, a
lender on a loan record, a parent company on a subsidiary. `mapping_workflow` models this as
**`embedded_master`**: the value becomes its own Senzing record, and the parent points at it.

**Three signals that a column holds one:**

- it holds many **distinct real-world names** rather than categories (239 bank names, not 3 status
  values — check the values, never the column name);
- the same name **repeats across records**, so resolving it merges them;
- a **later source could name the same thing**, so resolving it links the two sources.

**Why it matters:** as `payload`, the name rides along on each record and Senzing never matches on
it. As an `embedded_master`, every record naming the same organization resolves to one entity, and a
later source naming it resolves against that. That difference *is* entity resolution.

⛔ **Look for it at step 1, declare it at step 2 — the profile already tells you.** An embedded
master can only be **declared at step 2** (`plan_entity_structure`), and everything you need to
discover one is in the step-1 profile report, before that declaration is due. Read three columns of
the profiler's field table:

- **`Unique`** — a high distinct count on a 100%-populated text field is signal one;
- **`Unique %`** — low (a few percent) means the values *repeat*, which is signal two;
- the **`Sample`** columns, which are frequency-annotated (`Zions Bank, A Division of (527)`), so you
  can see at a glance whether they are real-world names or categories. Verified against
  `sz_schema_generator.py` on server 1.32.9, 2026-08-13.

**The tool asks you for this at step 2 too**, in its own words: *"Step 1 — IDENTIFY MASTERS: … **Also
identify embedded masters** — fields within another schema that represent a distinct secondary entity
(e.g., employer name/address on employee records)"*, and it lists `embedded_master` second in its
`SCHEMA DISPOSITIONS`, ahead of `child` and `relationship` (verbatim, server 1.32.9, 2026-08-13). So
module step 10 is where this belongs, and doing it there costs one extra entry in the step-2 payload.

⛔ **If it was missed at plan time, going `back` is the sanctioned fix — not a failure.** Being
**declared at step 2** while the values are what discover it means step 3 is where a missed one
surfaces, and step 3 cannot introduce a new schema: its `schema_mappings` are keyed to the step-2
plan and the server validates `FIELD INTEGRITY` against it. So when step 3 reveals one:

1. call **`mapping_workflow(action='back')`** — it returns to step 2 with the existing `schema_plan`
   preserved (verified on server 1.32.9, 2026-08-12);
2. re-plan with the embedded master declared;
3. re-advance to step 3 and map it.

`back` is one of the five valid actions and **this is what it is for.** Prefer catching it at step 10:
this route costs a round trip *and* the legacy-payload drop documented next, which is why the profile
columns above are worth reading before you advance the plan.

⛔ **Declaring an `embedded_master` requires the LEGACY `entity_plan` payload.** The typed step-2
branch (`for_step 2`) enumerates `support_schemas.disposition` as `lookup | relationship | child`
only, with `additionalProperties: false` — **`embedded_master` is in neither slot**, so the tool's
own *preferred* typed payload cannot express it. Send the legacy flat shape as `data` instead. This
exact payload **validated and advanced to step 3** on server **1.32.9, 2026-08-12**:

```text
data={'entity_plan': [
  {'schema_name': '<parent>',   'disposition': 'master',          'data_source': '<DS>',
   'record_type': 'ORGANIZATION', 'record_id_source': '<natural key field>',
   'field_count': <parent's full field count>},
  {'schema_name': '<embedded>', 'disposition': 'embedded_master', 'data_source': '<DS>',
   'record_type': 'ORGANIZATION', 'record_id_source': 'RECORD_HASH', 'embedded_in': '<parent>',
   'field_count': <fields belonging to it>}]}
```

The step-2 response documents this shape as "also accepted for backward compatibility". Re-check it
rather than assuming; if the typed branch gains the disposition, retire this note rather than
inverting it. Three details in that payload are each load-bearing, and each was established by a
rejection rather than by reading the response:

⛔ **`entity_plan` REPLACES the whole plan — re-declare every schema, not just the new one.** The
`schema_plan` preserved by `back` is still sitting in `state`, which makes a one-entry payload look
like an addition to it. It is not. Omitting the parent master fails with `profile schema '<name>' has
no disposition in schema_plan` and `schema_plan must contain at least one 'master' disposition`.

⛔ **`embedded_in` is required, and the tool never documents it.** The step-2 response advertises the
legacy shape with five keys — `schema_name`, `disposition`, `data_source`, `record_type`,
`record_id_source` — and says of this disposition only *"For embedded_master: provide field_count
(number of fields from parent schema that belong to this entity)"*. The validator also demands
`embedded_in`, naming the parent schema, and enforces `record_id_source` on the embedded entry:
`'embedded_master' requires 'record_id_source'` / `'embedded_master' requires 'embedded_in'`. Because
no response text names it, **`embedded_in` is discoverable only by sending a payload without it and
reading the error** — so send it from the start.
<!-- MCP-NEGATIVE: mapping_workflow(action='advance', from step 2) — step-2 instructions never name the required embedded_in key — owner: the step-2 validator's rejection names it ('embedded_master' requires 'embedded_in'), so the error is the only route — server 1.33.0, 2026-08-21 -->

**`record_id_source` is `RECORD_HASH` for the embedded entity**, because a name embedded in someone
else's row has no per-record natural key of its own. That sentinel is not a placeholder — step 4
defines its behavior: *"If it is the sentinel `RECORD_HASH` … generate `RECORD_ID` as a
deterministic hash over that entity's stable IDENTITY fields only — never the whole record (a
whole-record hash re-keys on any change, creating duplicate/stale entities)"*. It is the same hash the
EMBEDDED MASTER RULES below require, reached from the plan side.

⚠️ **Choosing the sentinel here decides a step-4 outcome: it widens the verbatim check's REL_*
rejection to include `REL_ANCHOR_KEY` and `REL_POINTER_KEY`.** A hashed RECORD_ID appears nowhere in
the source, so the keys mirroring it are unharvestable too. That is expected, not a mapping defect —
limitation 2 under "Four further limitations" has the condition and the offender-count check that
distinguishes it from one.

On success the server **moves the field count**: the embedded entry's `field_count` is subtracted from
the parent's, so a 19-field source declaring 1 embedded field returns `parent: 18, embedded: 1`. Seeing
the parent shrink is the confirmation that the declaration took.

**What the tool requires once it is declared** (its step-3 EMBEDDED MASTER RULES): the embedded
master gets a derived `RECORD_ID` (a deterministic hash of its identifying features, e.g.
`hash(NAME_ORG + ADDR_FULL)`), a derived `REL_ANCHOR` so the parent can point at it, and a derived
`RECORD_TYPE`; the parent master gets a derived `REL_POINTER` naming domain, key and role.

⚠️ **`KEY` has no key.** The typed `derived` entry carries `domain` and `role` properties and **no
`key`** (`additionalProperties: false`, so inventing one is rejected) — the tool's own example packs
it into `value`. Both of these were accepted on 1.32.9, 2026-08-12:

```text
parent  : {'disposition': 'derived', 'derived_as': 'REL_POINTER', 'domain': '<DS>', 'role': '<ROLE>',
           'value': 'DOMAIN=<DS>, KEY=hash(<field>), ROLE=<ROLE>'}
embedded: {'disposition': 'derived', 'derived_as': 'REL_ANCHOR',  'domain': '<DS>',
           'value': 'DOMAIN=<DS>, KEY=hash(<field>)'}
```

⛔ **Never silently downgrade a bootcamper's choice to `payload`.** Offer the decision **at step 3**,
where the values are in front of them, and state the trade-off both ways — a resolvable entity and
more records, against a string that never matches. If the bootcamper asks for the entity, carry it
out. If it will not be modeled — they declined, or going back is not possible — **say so and record
it** in `config/data_sources.yaml`, so the outcome is visible rather than inferred from its absence.
Mapping it to `payload` while they asked for an entity is assuming an answer they gave differently,
which **INV-007** forbids.

## Workflow (per data source)

### 8. Start

Call `mapping_workflow` with `action='start'`, `file_paths` naming the source file from
`data/raw/` or `data/samples/`, and `data={'workspace_dir': 'data/mapping'}` — **both parameters
are required and the call fails without either** (see the call contract above). Override any
`/tmp/` paths to project-local. Tell the user: "Starting mapping for [source]. I'll walk through
each step and explain what I find."

> **Data source registry:** Update the source's `mapping_status` to `in_progress` in
> `config/data_sources.yaml` and set `updated_at`.

> **Per-source mapping requirement:** Each data source **must** complete its own full
> `mapping_workflow` run from start to finish. Do NOT reuse the mapping output, field mappings,
> or mapping specification from one source for another: even if the schemas appear similar.
> Every source gets its own independent `mapping_workflow` execution and its own mapping
> specification markdown (`docs/mapping/{source_name}_mapper.md`). Mapper code may be shared
> across sources if schemas are identical, but mapping documentation is always per-source.

After `mapping_workflow(action='start')` finishes downloading its workflow resources, and
before any further mapping work (profiling, planning, mapping), place the just-downloaded
reusable resources at their policy-correct locations per the file-placement guidance above.

**Checkpoint:** write step 8 to `config/bootcamp_progress.json`.

### 9. Profile

Run the profiler, then summarize columns/types/completeness/quality. Advance workflow step 1 with
`action='advance'`, carrying `profile_summary` (one entry per source schema, each with
`schema_name`, `record_count`, `field_count`) in `data`.

⛔ **Send `profile_summary` as the array** — `[{"schema_name": "<name>", "record_count": N, "field_count": N}]` — **because the step's `advance_schema` declares it (INV-136)**. The step's prose states the same list form, and this payload advanced with `status: "ok"` on server 1.37.16, 2026-10-01.

**The profile-report filename depends on how many files you pass, and the server handles the
multi-file case itself.** Verified on server **1.33.0, 2026-08-23** by calling
`mapping_workflow(action='start')` twice and reading the emitted `commands` both times:

- **one** `file_paths` entry → a single invocation writing `-o <workspace_dir>/profile_report.md`;
- **more than one** → one invocation per input, each writing
  `-o <workspace_dir>/profile_report_<stem>.md` (`profile_report_crm.md`,
  `profile_report_orders.md`).

Run the commands as issued. ⛔ **Do not concatenate the per-file reports into one
`profile_report.md`** — that recreates the single-schema file whose silent wrongness this entry
used to warn about, and the relocation contract above already covers both filenames.

⚠️ **Server-side inconsistency, observation-only (INV-080).** At 1.33.0 step 1's *prose* still
hardcodes the unsuffixed name in both places it names a report — *"the profiler writes a detailed
markdown report to `<workspace_dir>/profile_report.md`"* and *"Read
`<workspace_dir>/profile_report.md`"* — while the emitted `commands` for a multi-file start write
the suffixed names. For a multi-file source the prose therefore points at a file that is never
created. **Read the `commands` array, not the prose.** The plugin cannot fix this; it can only stop
depending on the prose.

⛔ **One profiler limitation to expect, and it produces a wrong profile rather than an
error.** Observed 2026-07-27 on SDK 4.3.3.26191; **reported upstream 2026-07-31** and **not re-run
since**, so check whether it still applies rather than assuming.

1. **A headerless CSV is profiled by consuming its first data row as column names.** The profiler
   assumes a header row. On a documented headerless source (the free-data catalog ships one, with 12
   positional columns in its README) that means **one record disappears** and every column is
   mislabeled with a value from that row. Nothing fails — you get a confident, wrong profile, and
   every step-3 mapping decision rests on it. **Write a headered copy for profiling only**, using
   the documented column order, and let the mapper keep reading the raw file positionally.

⚠️ **A column's population percentage is not a quality signal when a sentinel token is in use.** A
null sentinel is a *value*, so the profiler counts it as present: a source using `-0-` for "no data"
reported **100% population on all 12 columns** when 8 carried no information. Treat population as
"has a value", never as "has information", and do not let it feed a completeness judgment —
that distinction is INV-128's, one layer upstream of where it usually bites.

⛔ **Work around these; do not ship a patched profiler.** `sz_schema_generator.py` is
MCP-delivered, and a forked copy masks the upstream fix (INV-173).

⛔ **Profile sanity check — interpret the field count, never just report it.** Before presenting
anything, check whether the profile is *plausible*: roughly **more than 100 fields, or more than 50
distinct field patterns**, is not a wide source — it is a signal that the source is shaped like a
document rather than a table. Report the likely cause instead of the raw number.

The usual cause is **dynamic keys — the source using data values as attribute names**, so each
record contributes new "fields" that are really values. When the count is implausible:

1. **Look for dynamic/unbounded keys:** many root keys appearing in only one or two records each,
   especially keys that are purely numeric or otherwise value-shaped. Report the count and a
   sample, not the full column table.
2. **Cross-check for redundancy:** check whether those key *names* also appear as **values**
   elsewhere in the same record (e.g. matching an ID field the record already carries). If they do,
   say so — that redundancy is precisely what makes dropping them lossless, and it is the
   difference between a safe pre-process and silent data loss.
3. **Recommend the sanctioned route explicitly:** pre-process to strip the dynamic keys, then
   **re-profile**. Name it as the expected next step; do not leave the bootcamper to infer that
   pre-processing is allowed.
4. **Require before/after proof:** show the removed data is redundant *before* dropping it, and
   that record counts and preserved features are unchanged *after*. Without that proof,
   pre-processing is silent data loss — worse than an unmappable profile.

This is a **finding, not a gate**: genuinely wide sources exist. Report, recommend, and let the
bootcamper decide — never block mapping on a field count.

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Present a full column table with types, sample values, completeness %, and
>   what each means for mapping (maps to Senzing / will skip / needs attention). Explain the
>   key takeaway. **Exception — when the sanity check above fires, do NOT print the full table**
>   (a 1,373-row column table is noise precisely when the bootcamper most needs to understand
>   what happened): show the diagnosis, a sample of the offending keys, and the recommendation.
> - **Concise:** Present one summary line: N columns detected, X% overall completeness, and key
>   issues only (e.g., "12 columns, 94% complete, 2 fields need attention"). When the sanity check
>   fires, lead with the diagnosis rather than the count — "1,373 fields detected, which almost
>   certainly means dynamic keys rather than a genuinely wide source" beats a bare number.

**Checkpoint:** write step 9.

### 10. Plan

Identify entity type (person/org/both), structure (flat/nested), relationships. Advance workflow
step 2 with `action='advance'`, carrying `master_schemas` (at least one, each with `schema_name`,
`data_source` in UPPERCASE, `record_type`, `record_id_source`) and `support_schemas` (lookups,
relationships, children) in `data`. Tell the user: explain the entity type decision, which fields
map vs. skip and why.

⛔ **(INV-300) Read the source's Record Type Check before you advance workflow step 2.** (INV-336) Open
`docs/mapping/{source_name}_mapper.md` → `## Record Type Check`. Its rule is Phase 1 Step 6's
"Type/name check" (`phase1-quality-assessment.md`), the canonical statement; do not restate it here.
With **Keep as-is**, `none needed`, no section, or a Retype that names every candidate as an
exception, change nothing. With **Retype**, the source now carries both types:

- Send each master schema's `record_type` as the source's predominant type **after** the retype. It
  stays enum-valid and is never `MIXED`: that is the enum-valid `record_type` half of the mixed-type
  rule below. Its other half, a step 3 `type_discriminator`, does not apply to a suffix retype;
  step 11 declares how each record is typed.
- Say in the plan summary that the source now carries PERSON and ORGANIZATION records, and how many
  records the retype moves. This is content in the summary, not a new question.
- Declare nothing else here: step 11 declares how each record is typed.

⛔ **(INV-280) On a mixed-type source, send an enum-valid `record_type` and declare the mixture at step 3 —
the step-2 prose asks for a value its own schema rejects.** Both halves are in the **same response**
(re-read live, server **1.33.0, 2026-08-21**): the instructions say *"If a schema has mixed entity
types discriminated by a field (e.g., type=person/company), set record_type to `"MIXED"` and note the
discriminator field"*, while that response's `advance_schema` declares
`record_type` as `enum: ["PERSON", "ORGANIZATION", "VESSEL", "AIRCRAFT"]` — and the typed `payload`
branch for `for_step 2` carries the same enum, so a client using constrained decoding **cannot emit**
the documented value at all.

Sending `MIXED` is accepted and warns: `status: "ok"` plus, in `warnings[]`,
`schema_plan[0] (<your schema>): record_type 'MIXED' is non-standard — expected one of: PERSON,
ORGANIZATION, VESSEL, AIRCRAFT` (reproduced on the same server and date). So send the source's
predominant type and let step 3's `type_discriminator` do the typing — which is
what the tool's own prose says happens anyway (*"The type_discriminator details will be defined in
Step 3 mapping"*), so nothing is lost.

⛔ **(INV-125) Step 3 rejects a source that declares BOTH organization and person name
fields — even when no record carries both — and its message leads with the wrong problem.** A source whose name fields are
disjoint *by record type* is rejected with this message (re-read live, server **1.37.15,
2026-09-29**; the attribute list names the person attributes the mapping declared):

```text
NAME_ORG cannot co-exist with person name attributes NAME_FIRST, NAME_LAST — a record is either
a person or an organization. FIX: declare the name ONCE and let the mapper emit NAME_ORG for an
ORGANIZATION record and NAME_FULL (or parsed person parts) for a PERSON record, branched by
RECORD_TYPE; or use a type_discriminator to make the mapping conditional.
```

**Where the type comes from a source field's value, the fix is to declare the names through
`type_discriminator.field_overrides`**, the message's second route. That includes where the override
is **identity in both branches**, declared purely to satisfy the validator. Observed on two sources
on server **1.33.0**, 2026-08-25, and again on 2026-08-27; both had verified-disjoint fields (one
populated per record, selected by `RECORD_TYPE`; zero rows carrying both). A retype chosen by a name
suffix has no such field, so it takes the message's first route, as step 11 declares it.

- ⚠️ **Read the first sentence as "declare it differently", not "your data is wrong".** It states a
  **record-level** rule, and the mapping already satisfied it — the rejection is about the *field
  declarations*, which is what the `FIX:` clause says (the 1.33.0 message had no `FIX:`). A run that
  stops at the first sentence spends its first attempt re-checking data that is correct. The rule's authoritative scope is narrower still: the Entity Specification's `Feature:
  NAME` section says *"do not mix `NAME_ORG` with parsed person fields **in the same object**"*
  (`search_docs(query='entity specification attribute names feature tables NAME_ORG ADDR_LINE1
  PHONE_NUMBER', category='data_mapping')`, server **1.37.19**, docs index 2026-10-02 18:46 UTC,
  2026-10-02; read past the first hit) — one NAME object, not one record, and certainly not one
  declaration.
- ⚠️ **Expect the coverage count to drop after you apply it.** Fields moved into `field_overrides`
  are counted by nothing, so the mapping reports fewer covered fields than it dispositions. That is
  the known field-count warning described below — **not** unmapped data. Do not chase it.
- ⛔ **(INV-343) Do not pre-emptively emit a `type_discriminator` on every source.** It is the fix for this
  rejection, not a default: adding an identity override to a mapping that does not need one buys the
  same coverage-count surprise for nothing.

⚠️ **If a warning like that reaches you, it is not your error and not a mapping defect** — record it
as expected and proceed (INV-048/INV-173). This is **one** known-bad interaction, and it does not
license ignoring step-2 warnings generally: the others are real. And note the prose's *"must be PERSON or
ORGANIZATION"* is wrong against its own enum — `VESSEL` and `AIRCRAFT` are valid, which a watchlist
source can genuinely need. **Retire this note once step 2's prose and its `advance_schema` agree.**

⛔ **Before you advance, check the profile for a second entity hiding in a column.** This is the
one structural thing step 2 commits to that step 3 cannot add later, and the profile report you read
at step 9 already holds the evidence: scan its `Unique`, `Unique %` and frequency-annotated `Sample`
columns for a populated text field carrying many repeating real-world names. If there is one, declare
it as an `embedded_master` in this step's payload. See **"A second entity hiding in a column:
`embedded_master`, and when to go `back`"** above for the three signals, the payload it requires, and
the recovery route if this check is missed — do not restate them here (INV-183, INV-300: the rule is named and
linked at the step that needs it, never forked into a second copy).

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Explain the entity type decision and rationale. For each field, state whether
>   it maps or is skipped and why (e.g., "phone maps to PHONE_NUMBER: standard contact
>   attribute" / "internal_id skipped: no Senzing attribute match, not useful for
>   resolution").
> - **Concise:** State the entity type and a count of mapped vs. skipped fields without
>   per-field rationale (e.g., "Entity type: Person. 8 fields mapped, 3 skipped.").

**Then route on `mapping_verbosity`. This is the advance the INV-205 carve-out governs**, and the
tool's step-2 response asks for the opposite (verbatim, server 1.32.9, 2026-08-14): *"If ALL entries
have confidence >= 0.80: present the plan summary AND immediately call mapping_workflow
action="advance" in the SAME turn. **Do NOT ask the user to confirm, approve, type YES, or proceed.
Do NOT wait for a response. Just advance.**"* On conversation the bootcamp outranks that; on
everything else the tool remains authoritative.

- **Verbose:** present the plan per the rules above, then **end the turn on the pinned question
  below** before advancing. Advance on option 1. On options 2-4, revise the plan and re-present it —
  do not re-ask the parts already settled (INV-006). A single-schema plan clears the 0.80 bar
  trivially, so without this gate the entity plan would advance with nothing shown and nothing
  asked, silently breaking the promise the verbosity offer made one step earlier.
- **Concise:** present the plan summary and advance in the **same turn**, with **no** question. This
  is the tool's own fast path and needs no gate.

Pin the guided-mode question verbatim (INV-056, INV-233) — verbose mode only:

> 👉 **Here's the entity plan for {source}. How would you like to proceed? Reply with a number:**
>
> 1. **Looks right — map the fields.**
> 2. **Change the entity type** (currently {record_type}).
> 3. **Change which field identifies each record** (currently {record_id_source}).
> 4. **Something else** — tell me what to adjust.

*(Internal: end the turn on this question and wait — INV-007.)*

⚠️ **Options 2-4 are why this is a question rather than a courtesy.** A confirmation gate whose only
answer is "yes" is the pointless question INV-012 forbids, and the bootcamper in this mode was
promised the decisions — so the gate has to let them change the two things the plan actually commits
to. **Option 3 is the one that matters most:** `record_id_source` cannot be revised after step 3
without going `back`, and the tool's own inline reference warns that a whole-record hash "re-keys
whenever ANY field changes, so the resolver treats every source update as a NEW record
(duplicate/stale entities)" — a stable natural key is preferred, and a derived hash is a documented
last resort (server 1.32.9, 2026-08-14).

**Checkpoint:** write step 10.

### 11. Map

Map fields to Senzing attributes, then advance workflow step 3 with `action='advance'`, carrying
`schema_mappings` in `data` (per schema, a `field_mappings` list whose entries each declare a
`disposition` — `feature`, `payload`, `ignore`, `derived`, or `extract`). NEVER guess
attribute names. For non-Latin data:
`search_docs(query='data quality practices multi-language non-Latin', category='globalization')`
(the Globalization Guide's *CJK+English cross-script matching* section) — the other query terms, the sections to ask for, and the phrasings that return wrong content
are in this module's `SKILL.md` → "Multi-language data" (INV-212); do not re-derive them here.
Tell the user: show
the mapping table with reasoning for each decision and a confidence score.

⛔ **A single name field maps to `NAME_FULL` — it is not split.** This is the authority Module 1 and
Data collection route here for, so state it before mapping any name column. The specification
documents `NAME_FULL` as the *"Single-field name when type (person vs org) is unknown or only a full
name is provided"*, and its `NAME` rule reads *"Prefer parsed person names
(`NAME_FIRST`/`NAME_LAST`/…) when available; use `NAME_ORG` for organizations; use `NAME_FULL` only
when the type is unknown or only a single field exists"*
(`search_docs(query='NAME_FULL NAME_ORG parsed person name single field', category='data_mapping')` →
*Name > Feature: NAME*, top hit; server 1.32.9, 2026-08-17, query re-verified on
1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-04). "When available" means **the source provides
separate fields** — so one `full_name` column is a direct mapping to `NAME_FULL`, and a
`"Last, First"` column is too, however parseable it looks.

⚠️ **Two further rules from the same section, because getting them wrong is silent.** Do not mix
`NAME_FULL` with parsed name fields in one `NAME` object, do not mix `NAME_ORG` with parsed person
fields, and do not split one name across two `NAME` objects. *Name > Feature: NAME* states the
first two as a Rules line, and shows ❌ worked examples for the last two: the split, and `NAME_ORG`
with parsed person fields. The `NAME_FULL` mix has the Rules line only (re-verified with the query
above on 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-04). An organization name belongs in
`NAME_ORG`, not `NAME_FULL`.

⚠️ **This is the reversal these routes exist to prevent:** one run recorded, a module earlier, that a
`full_name` and a `"Last, First"` `member_name` each "needed splitting" — in both
`config/data_sources.yaml` and `docs/data_source_locations.md`, where it read as settled fact.
Splitting them would have produced a mapping that loads and validates cleanly while degrading
resolution quality silently, which is exactly the class a quality score cannot detect.

⛔ **(INV-300, INV-336) Read the source's Record Type Check before you advance workflow step 3.**
Open `docs/mapping/{source_name}_mapper.md` → `## Record Type Check`. Its rule is Phase 1 Step 6's
"Type/name check" (`phase1-quality-assessment.md`), the canonical statement; do not restate it here.
With **Keep as-is**, `none needed`, no section, or a Retype that names every candidate as an
exception, map as usual. With **Retype**, declare the name **once** and type each record with a
computed `RECORD_TYPE`. Declare no `NAME_ORG` entry and no `type_discriminator` (INV-336):

- **Parsed person name fields.** Declare them once, as the person attributes they are (for example
  `NAME_FIRST` and `NAME_LAST`). The mapper emits `NAME_ORG` for a retyped (ORGANIZATION) record and
  the parsed parts for a PERSON record, branched on `RECORD_TYPE`.
- **One name field.** Declare it once as `NAME_FULL`. The mapper emits `NAME_ORG` for a retyped
  (ORGANIZATION) record and `NAME_FULL` for a PERSON record, branched on `RECORD_TYPE`. The step 2
  inline reference says why the ORGANIZATION branch is not `NAME_FULL`: *"On an ORGANIZATION record,
  EVERY name maps as NAME_ORG … NAME_FULL is PERSON-only"*.
- **The computed `RECORD_TYPE` is one `derived` field mapping:**

  ```json
  {"disposition": "derived", "derived_as": "RECORD_TYPE",
   "source": "<the name field the rule reads>",
   "justification": "<the Phase 1 rule and its exceptions>"}
  ```

  `source` names the single name field or, for parsed fields, the field that ends the joined name.
  `justification` says the record is PERSON except where the Record Type Check rule retypes it to
  ORGANIZATION, names the exceptions, and says an ORGANIZATION record's name is emitted as
  `NAME_ORG`. Re-verified on server **1.37.15, 2026-09-29** (`mapping_workflow` workflow step 3, on
  synthetic fields): both name shapes, declared this way, returned `status: ok` at `step: 4`. The
  step 3 `advance_schema` gives a `derived` entry its `derived_as`, `source` and `justification`
  keys, and its instructions reject a derived `RECORD_TYPE` that carries neither `source` nor a
  non-empty `justification`.

⚠️ **Declaring `NAME_ORG` beside the parsed fields is what step 3 rejects** with
`NAME_ORG cannot co-exist with person name attributes …`, the block under step 10. That block's
`type_discriminator.field_overrides` fix does not apply to a suffix retype. A `type_discriminator`
branches on the values of one real source field (*"all sample values must be enumerated in types or
covered by default"*, step 3 instructions, 1.37.15), and a retype is chosen by a name suffix, not a
field value. A uniform type field, such as CORD's `NODE_TYPE: OFFICER` on every record, cannot drive
one either. The message's own `FIX:` names the declare-once route above.

⚠️ **This advance is unconditional in both modes — there is no general guided-mode gate here, and
that is deliberate.** Unlike step 10, the questions this step needs are *conditional*, and each is
already pinned or specified where it triggers: a field the tool returns below 0.80 confidence gets
its `QUESTION FORMAT` options reshaped into a 👉 question (see the carve-out above), the
shared-feature collision check below asks only about the cross-source pairs its exemptions leave
(its "Asked — every other pair" list), and a validator that
rejects twice without saying why gets its own. Present the mapping table and advance. Stated here so
a later reader does not read the absence as the same omission step 10 once had.

⛔ **Before accepting the plan: a root-level `payload` key MUST NOT be a registered feature
attribute name.** This prohibition is documented: `mapping_workflow` step 2's inline *SENZING
MAPPING REFERENCE* says an optional root-level payload attribute "must NOT be a registered feature
attribute", and says to rename a source field whose name collides with a reserved feature
attribute but means something different (server **1.37.16, 2026-10-01**). Check every
`disposition: payload` field's emitted key against the attribute catalog you already consult for
`feature` mappings — the same lookup, asked of the other disposition. This runs **here**, where
the routing decision is made, not after the output is analyzed.

⚠️ **This mechanism is OBSERVATION-ONLY** — one run, one SDK build, 2026-08-17, with the bundled
analyzer's own SCHEMA warning as the corroborating instrument (it fired on the collision and cleared
on the rename). Observed: a field routed to `payload` but emitted under its own name at the record
root, where that name is a registered feature attribute, was extracted by Senzing as a **feature**
anyway — so the Bootcamper's explicit routing answer was honored in form and not in effect. Only
the prohibition is documented: `mapping_workflow` step 2 states the rule but not what breaking it
does, and no indexed `search_docs` section states that consequence either (the marker below).
Treat the extracted-as-feature consequence as a strong local observation, not as documented
behavior, and re-confirm before relying on it elsewhere (INV-080/INV-149).

<!-- MCP-NEGATIVE: search_docs(query='payload attribute versus registered feature attribute record root extracted as feature precedence', category='data_mapping') — no indexed section states that a root-level key named after a registered feature attribute is extracted as a feature — owner: mapping_workflow step 2's inline SENZING MAPPING REFERENCE carries the prohibition ("must NOT be a registered feature attribute") but states no consequence of breaking it, so search_docs over the Entity Specification IS the route that would carry the consequence, and its *Attribute reference* section states the rule for the inside-a-feature-object case -- "Only the attributes listed here may appear inside a feature object. Anything else is treated as payload" -- while no returned section states what happens to a record-root key whose name belongs to a registered feature, which is the case asked about (absence negative) — server 1.37.16, 2026-10-01 -->

**On a collision, do NOT silently re-route or override the answer (INV-006).** Their intent — *do
not match on this* — is achievable; only the key **name** is wrong. Say what will actually happen
and offer the fix, ending the turn on one pinned 👉 question:

> 👉 **`{field}` is routed to payload, but `{KEY}` is a registered Senzing feature attribute — at the record root Senzing will resolve on it anyway. Shall I store it as `{KEY}_PAYLOAD` instead, so it rides along without matching?** (respond yes or no)

On **yes**, emit the renamed key and record the rename in the mapping table's reasoning column. On
**no**, record that the Bootcamper accepts the field being matched on, so the decision is theirs and
is visible later — never leave the collision unrecorded either way.

⚠️ **A list-valued field routed to `payload` is joined into ONE literal value.** A multi-valued
column becomes a single meaningless string: the observed signature was `"XXX; VGB; GBR"` in
**13,803 of 19,050 records** (72%). Say so before accepting a payload route on a repeating field —
the Bootcamper usually wants either the first value, a chosen one, or the field split, none of which
a join produces.

**Surface the analyzer's SCHEMA warnings here, not only in the output analysis.** The analyzer is
the instrument that already detects this class, and it currently reports one step too late to
prevent it: read its SCHEMA warnings at this gate and resolve them before the plan is accepted.

⛔ **The general shape, and the reason every existing gate missed this.** The analyzer, the verbatim
check and the routing report all confirm the **output matches the plan** and the **plan is faithful
to the source**. None of them confirms the plan does what the Bootcamper **asked for** — so an
answer that selects a *behavior* rather than a *value* is unverified by construction, and passes
every gate while being silently unhonored. Wherever a question's answer chooses a behavior,
something must check the behavior was actually obtained.

> ⛔ **Heads-up before you map anything with `disposition: extract` — read this now, not after the
> gate fails.** `extract` is for pulling a value out of a prose field, and **every correct
> multi-word extraction is rejected by step 4's verbatim gate**, by construction: the gate compares
> whole values, `|`/`;` segments and single whitespace tokens by equality, never substrings
> (confirmed on server 1.32.9, 2026-08-14 — see "Four further limitations" below for the mechanism
> and the evidence). `extract` is not exotic: any prose field with an embedded address, date of birth
> or identifier reaches it.
>
> So when that gate fires on an extraction you know is faithful: **do not iterate on the mapper.**
> The gate's own wording ("a code bug: fix the mapper … Do NOT proceed until it passes") points you
> at your own correct code. Confirm the value is faithful to the source, **record the exemption and
> its reason** in the source's mapping notes, and **proceed** — a checker limitation must not become
> an iterate-forever loop or a blocked module (INV-048/INV-173). The four numbered steps under
> "Four further limitations" are the full procedure; this pointer exists because that block sits
> below the step where the collision happens.

> **Heads-up before you map a dynamic-key field.** When a value is derived from the source **field
> name** rather than a field value — the mapping reference's own
> `"Digital Currency Address - <CODE>"` → `ACCOUNT_DOMAIN` pattern is the common case — the verbatim
> check **will** report it when validation runs, and that report is a known checker limitation, not a
> mapping defect. Read "⛔ A value derived from a source *field name*…" later in this step **before**
> you get there, so an expected exit 1 does not read as a bug in your mapper.

⚠️ **The field-count warning is half fixed. The `derived` half is gone; the `type_discriminator`
half still fires — and the warning now tells you which.** Both halves re-checked on server
**1.33.0, 2026-08-21**.

The **`derived` half is fixed**, and the counter now says so in its own text rather than merely
falling silent: it reports `derived=N are synthesized and not source fields`, which is exactly the
correct treatment.

The **`field_overrides` half reproduces.** A step-3 advance for an 8-field master schema carrying a
`type_discriminator` on one field, whose `types.*.field_overrides` declared one further source field,
returned `{"status":"ok","step":4,…}` with:

```text
Schema 'watchlist_pep': mapping covers 7 of the 8 profiled source fields
(dispositions: feature=2, payload=3, ignore=1, extract=0, code_mapping=0,
 discriminator=1; derived=2 are synthesized and not source fields)
```

**Check the arithmetic against your own mapping — that is the confirmation, and you can run it
yourself.** `feature + payload + ignore + extract + code_mapping + discriminator` sums to **7**
against a `field_count` of 8. `discriminator=1` counts the discriminator field alone; the field
declared only inside `type_discriminator.types.*.field_overrides` is counted by nothing. Expect the
count to fall short by exactly the number of `field_overrides`-only fields you declared.

**The earlier observation, kept as history.** Through server **1.32.3** (verified **2026-07-31**)
step 3 emitted "mapped N fields … but profile reported M fields" on mappings using `derived` entries
or a `type_discriminator`. The diagnosis: the counter included those `derived` entries — which are
**not source fields** — while excluding fields declared only inside
`type_discriminator.field_overrides`, which **are**. The two errors do not cancel, so the count was
wrong in both directions. Measured 2026-07-27 across four sources on SDK **4.3.3.26191**: 12 fields
reported as 13 (high), and 16 reported as 14 (low), with every source field dispositioned in both
cases. Reported upstream 2026-07-31.

**Both mechanisms the diagnosis rests on are still in the schema** — re-read on server **1.33.0,
2026-08-21**: a `derived` entry still requires a `derived_as` key whose enum is `DATA_SOURCE`,
`RECORD_ID`, `RECORD_TYPE`, `REL_ANCHOR`, `REL_POINTER`, and `type_discriminator` is still a step-3
field carrying its own `field_overrides`. So the diagnosis was right in **both** directions, and one
direction has since been fixed.

✅ **The `type_discriminator` half is confirmed, not un-re-run.** An earlier version of this block
called it the one half never re-run and named what would settle it: *a source with a per-record
entity-type field, mapped with a `type_discriminator` whose `field_overrides` declare at least one
source field*. That is exactly the mapping run on **1.33.0, 2026-08-21**, and it fires — see the
quoted warning and its arithmetic at the top of this block.

**What to do:** confirm every source field carries a disposition — that is the real question the
warning gestures at, and it holds whether or not the counter is wrong — and if it does, record any
count mismatch as expected and proceed. ⚠️ **Do not start ignoring this step's warnings generally.**
Its *other* warnings are real; this is one known-bad counter, not a noisy step.

**Do not send `feature_count`, `payload_count` or `ignored_count` — the server derives them.** Step
3's instructions list all three under DISPOSITION COUNT BALANCE as though the client must supply
them, so a future reader comparing this module against the tool's prose will read the plugin's
silence as an omission. It is not, and the 2026-08-14 advance above is the evidence: it was accepted
without any of the three, and the returned `state` carried the server's own computation —
`"meridian_crm":{…,"field_count":6,"feature_count":4,"payload_count":1,"ignored_count":1,"extract_count":0}`.
The step-3 typed `payload` branch does not declare the three properties at all, which is consistent
with the server computing them rather than reading them.

⛔ **Shared-feature collision check (cross-source) (INV-012, INV-251, INV-006) — ask only about
pairs whose sameness the guide cannot show.** After mapping a source, compare its feature targets
against the sources already mapped. A **pair** is two sources sending different source fields to
the same Senzing feature. Every pair is either exempt or asked; a question whose answer is
self-evident is output the Bootcamper does not need (INV-012).

**Exempt — recorded, not asked.** A pair is exempt when either of these holds:

1. **Parsed vs. full NAME or ADDRESS, with the same subject and role.** One source sends the full
   form (`full_name`, `address`), the other the parsed components (`first_name` + `last_name`;
   `street`/`city`/`state`/`zip`), **and** both describe the same subject in the same role: both
   the record subject's name, or both the same address usage.
2. **Same quantity under a different name, on a feature-specific feature.** The feature names
   exactly one quantity, and both field names denote that quantity: `DOB` (`date_of_birth` vs.
   `birth_date`), `SSN`.

Record each exempt pair as one line in that source's `docs/mapping/` write-up, in both verbose and
concise `mapping_verbosity`. In verbose mode the line also goes in the mapping table's rationale
column. An exempt pair produces no chat output (INV-012).

**Asked — every other pair.** That includes:

- a pair on a **feature-generic** feature, meaning one that admits several different quantities:
  `REGISTRATION_DATE` ("year established" vs. "incorporation filing date"), `OTHER_ID`,
  `NATIONAL_ID`;
- a pair whose field names denote **different quantities** (`BID` vs. `EFX_ID`);
- a pair whose **subject or role differs or is unclear**: a full home `address` vs. a parsed
  `billing_street`/…, or a `contact_name` that may name someone other than the record subject;
- any pair the guide cannot show is the same quantity.

For an asked pair, stop and confirm the two fields measure the *same quantity*, not merely the same
*kind* of thing. Ask **one** 👉 question per source, covering every asked pair that source has: list
each pair with its feature, ask whether each pair measures the same quantity, and ask the
Bootcamper to name any pair that doesn't (INV-251: one question per turn; its wording is
necessarily specific to the pairs, so it is not a pinned question). Record the answer per pair with
the mapping rationale. A source with both kinds records its exempt pairs and asks only about the
rest. A source with only exempt pairs asks nothing, and the step does not yield on this check. A
pair's recorded answer is not asked again when a later source is mapped (INV-006).

This is the one check the validation scripts structurally **cannot** perform: they each see a single
source, and the defect only exists in the relationship between two. Watch **date** and **identifier**
features hardest, where near-miss semantics are the norm — "year established" vs. "incorporation
filing date" are both plausible `REGISTRATION_DATE` candidates and mean different things; `BID` vs.
`EFX_ID` are both identifiers and are not the same identifier. If they measure different things,
route one to payload instead of the shared feature. Getting this wrong does not produce an error —
it produces silently suppressed merges that only the post-load match-key audit will reveal.

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Show the full mapping table with a rationale column explaining each mapping
>   decision and a confidence score per field (e.g., "first_name → NAME_FIRST: standard given
>   name field, confidence: high").
> - **Concise:** Show the mapping table with source field → Senzing attribute only, no
>   rationale column or confidence scores (e.g., "first_name → NAME_FIRST").

> **Availability-aware mapping validation:** `mapping_workflow` advertises three validation
> scripts. Run them by availability: do NOT treat any one as a hard blocking gate.
>
> 1. **`sz_json_analyzer.py` (primary validation):** structural + Entity-Specification
>    validation, currently hosted (HTTP 200). When available, run it and use its result as the
>    authoritative check **for what it actually measures** — conformance to the *recommended*
>    schema, which is not the same question as "will this data load and resolve" (see the ⛔
>    conformance block below). It is **sufficient to proceed**: when the verbatim/routing scripts
>    below are unavailable, a passing `sz_json_analyzer.py` result lets you continue.
> 2. **`sz_verbatim_check.py` (verbatim-fidelity, optional/best-effort):** if available, run it
>    and report the result; if unavailable (HTTP 404 / no working inline fallback), tell the
>    bootcamper it is being skipped because the script is unavailable, treat it as
>    optional/best-effort, and proceed: do NOT block on it.
>    ⛔ **On a CSV source it will crash, and that is expected.** Both this script and the routing
>    report call `load_jsonl(source_path)` and are documented `<source.jsonl> <output.jsonl>`, while
>    `mapping_workflow` accepts CSV inputs — so a CSV source produces
>    `json.decoder.JSONDecodeError: Extra data: line 1 column 5 (char 4)`. Report it as a **tool
>    limitation, not an environment problem**, and either adapt CSV→JSONL and call the checker's own
>    `verify()` (keeping upstream's logic unmodified) or proceed without it. Observed 2026-07-27 on
>    SDK 4.3.3.26191; see the ⛔ limitations block below.
> 3. **`sz_routing_report.py` (routing-coverage, optional/best-effort):** same handling as the
>    verbatim check, including the CSV crash.
>
> In short: anchor validation on `sz_json_analyzer.py`; degrade the verbatim and routing checks
> to optional/best-effort when their scripts are unavailable, and never leave the bootcamper
> blocked at this step because of a 404.

⛔ **The verbatim check harvests source *values* only, so whatever it cannot harvest is
unsatisfiable — not strict.** Verified against the current resource (server **1.32.2**,
**2026-07-29**): `collect_strings()` flattens every **string** and every **int/float** (stringified
via `str(obj)`) out of the nested source record, recursing through lists and dicts, and the test is
whole-value membership (`if v.strip() not in allowed`). Its only waiver is key-based —
`EXEMPT_KEYS = {"DATA_SOURCE", "RECORD_ID"}` plus any attribute ending `_TYPE` — so a *value* cannot
be exempted at all.

Two things it cannot harvest. That is the whole of the **harvesting** limitation — three further
limitations of a *different* kind are listed below it, where the harvester works fine and something
else does not:

1. **A boolean.** `collect_strings()` skips `bool` deliberately, and says why in its own docstring:
   there is no unambiguous verbatim string form for a JSON boolean (Python's `str(True)` is `"True"`,
   not JSON's `"true"`), so admitting booleans would let a case transform slip through rather than
   catch one. A source `true` emitted as `"true"` is therefore reported however you emit it.
2. **A value derived from a source field NAME rather than a field value** — see the section below,
   which is the common case in practice.

✅ **Numbers are NOT in that list any more.** A numeric source value now enters the allowed set and
passes: a source `RegKey: 1001` emitted as `"1001"`, and `98.6` emitted as `"98.6"`, both exit **0**
(re-run 2026-07-29). Through server 1.32.1 they failed under either emission — reported on all 53,321
relationship rows of one real run, reported upstream 2026-07-28, and **fixed in 1.32.2**. So do
**not** record a numeric-value exemption: run the check and read its actual output. The plugin pins
no MCP server version, so every bootcamper is on the current server and this is simply the behavior.

**What to do — in this order:**

1. **Do not conclude the mapping is wrong.** This finding is a limitation of the checker's harvesting,
   not evidence about your data. Confirm separately that the emitted value is faithful to the source:
   same value, and a JSON type you chose deliberately.
2. **Choose the emission on the Entity Specification's terms, not the checker's.** Confirm the
   attribute's expected form via `search_docs(query='REL_ANCHOR_KEY REL_POINTER disclosed relationship keys',
   category='data_mapping')` at the time you map it — `query` is the tool's only required
   parameter, so a bare category is not a callable form, and naming the vocabulary is what makes
   the check re-runnable (INV-212). Swap the query for the attribute you are actually confirming.
   For
   the relationship keys, the specification's JSON examples show string values (`"ORG1001"`,
   `"ACME-1001"`) while its `REL_ANCHOR_KEY` row shows a bare `1001` in the Example column, so it
   does not mandate a type (re-verified with the query above on 1.37.19, docs index 2026-10-02
   18:46 UTC, 2026-10-04, in *Feature: REL_ANCHOR*). Neither emission is made correct or incorrect by what the
   checker can see.
3. **Record the exemption and its reason** in the source's mapping notes — which attribute, why the
   checker cannot harvest it (a boolean source value, a value derived from a field name, or a
   `NAME_ORG` joined from parsed name fields, which equals no single source value), and that the
   value is faithful — then **proceed**. A checker limitation MUST NOT become an iterate-forever
   loop or a blocked module (INV-048).
4. ⛔ **Never change a source value to satisfy the tool.** For a value the harvester cannot reach it
   would not even work — the allowed set was built without it, under either emission — and distorting
   data to turn a gate green is the one outcome worse than the gate being wrong.

⛔ **Four further limitations (INV-173), where the harvester works and something else does not.** First
observed 2026-07-27 on SDK 4.3.3.26191, across four sources mapped end to end (`OPENSANCTIONS_PEP`,
`OFAC_SDN`, `ICIJ`, `UK_COMPANIES_HOUSE`); those three were reported upstream the same day.
**Limitation 4 came later** — found 2026-08-31 on a CORD source and reported upstream that day.

⚠️ **Freshness, per limitation — all four are CURRENT behavior.**
Limitations 1 and 3 were re-confirmed on **MCP server 1.32.9, 2026-08-14**, by reading the scripts
the server itself delivers — `download_resource(filenames=['sz_verbatim_check.py',
'sz_routing_report.py'])`, whose response is a **listing of URLs, not the scripts**, so reading them
means fetching each `url` first (`ground-rules.md` → "Three tools answer with a listing") — and the live
`mapping_workflow` step-3 schema. That is a check of the
**mechanism**, which is what these entries assert, and it does not depend on re-running a mapping.
Limitation **2** was confirmed end to end on **2026-08-18** by a run that finally had a source with
**disclosed relationships** — and that run also **widened** it: see the entry itself, which now
states the condition under which the KEY attributes fail too.
Limitation **4** was re-confirmed on **MCP server 1.35.3, 2026-09-01**, the same way as 1 and 3 — by
reading the delivered `sz_routing_report.py` and checking `discover_payload_fields()`'s `return []`
against the resource list `download_resource` advertises. Mechanism, not a re-run.

1. **Any correct `extract` output is rejected. CONFIRMED CURRENT — server 1.32.9, 2026-08-14.** The
   workflow documents `extract` for prose fields
   and names OFAC SDN `REMARKS` as its canonical example — the live `mapping_workflow` schema still
   declares `extract` as a disposition whose branch **requires** `expected_features` (re-read from the
   tool's own step-3 payload schema, same server and date). The gate's `allowed_values()` accepts only
   a whole value, a `|`/`;`
   segment, or a whitespace token — re-read from the delivered script: `check_verbatim()` tests
   `if v.strip() not in allowed`, and the script's own docstring says the set is compared by
   "**Equality against this set (not substring)**". So the workflow offers a disposition its own
   step-4 gate rejects **by construction**, and a *multi-word* extraction is unreachable: it is
   neither a whole value, nor a `|`/`;` segment, nor a single whitespace token. Observed: `Remarks = "a.k.a. 'BNC'."` → a correct extraction emits
   `NAME_ORG="BNC"` → reported as a violation, because the whitespace tokens are `a.k.a.` and
   `'BNC'.`. **Any** substring pulled from prose fails the same way. Emitting `'BNC'.` to satisfy it
   would write quotes and a period into a name field; dropping the alias loses real data. Take the
   exemption path instead.
2. **Every REL_* attribute whose value the harvester cannot see is rejected. CONFIRMED END TO END —
   2026-08-18, engine-side observation.** `REL_ANCHOR_DOMAIN`, `REL_POINTER_DOMAIN` and
   `REL_POINTER_ROLE` always; `REL_ANCHOR_KEY` and `REL_POINTER_KEY` **conditionally** — read the
   next paragraph before you conclude your keys are wrong.

   The DOMAIN and ROLE attributes are structural constants that by definition have no source value,
   so the harvester cannot see them and `is_exempt()`'s waiver — `DATA_SOURCE`, `RECORD_ID`, and any
   attribute ending `_TYPE` (re-read on 1.32.9, 2026-08-14: `is_exempt()` is still `attr in
   {"DATA_SOURCE", "RECORD_ID"} or attr.endswith("_TYPE")`) — does not cover them.

   <!-- MCP-NEGATIVE-SCAN: not-a-tool-claim — "a computed value that appears nowhere in the source"
        is a fact about the Bootcamper's own data and their mapper's output, not about any MCP tool's
        content, so it needs no MCP-NEGATIVE marker. The tool claims in this entry are POSITIVE and
        cited inline: `record_id_source`'s RECORD_HASH sentinel and step 4's deterministic-hash
        prescription, both re-read live from mapping_workflow on server 1.33.0, 2026-08-21. Triaged
        2026-08-21 from `coverage_reports.py unmarked`. -->
   ⛔ **`REL_ANCHOR_KEY` and `REL_POINTER_KEY` pass only when `record_id_source` names a source
   field. On the `RECORD_HASH` sentinel they fail alongside the others** — and that is the *normal*
   case for an `embedded_master`, which is the disposition that produces REL_* scaffolding in the
   first place (see "`record_id_source` is `RECORD_HASH` for the embedded entity" earlier in this
   step). A REL_*_KEY mirrors the RECORD_ID it points at; when that RECORD_ID is a deterministic hash
   over identity fields, the key is a **computed value that appears nowhere in the source**, so the
   harvester cannot see it either. The condition is current: `mapping_workflow`'s step-2 advance
   schema documents `record_id_source` as *"field name of the stable natural key (PREFERRED), or
   RECORD_HASH only when no stable unique field exists"*, and step 4 still prescribes *"a
   deterministic hash over that entity's stable IDENTITY fields only"* on the sentinel (both re-read
   live, server **1.33.0, 2026-08-21**).

   **The offender count is how you tell this limitation from a real mapping defect, and you can
   check it yourself.** It reconciles to `records × REL_* attributes per record`, and every offender
   is scaffolding rather than a data value. Two measurements, both engine-side observations with
   their conditions: 31 offenders across 21 records on a source whose keys came from source fields
   (DOMAIN and ROLE only, 2026-07-27, SDK 4.3.3.26191); and **83,338** offenders on a `RECORD_HASH`
   embedded master — `25,000 senders × 3 pointer attributes + 4,169 beneficiaries × 2 anchor
   attributes`, the KEY attributes included (2026-08-18). If your count reconciles that way, record
   the exemption and proceed; if it does not, look at your mapping.

   The Entity Specification defines all of them — its *Feature: REL_ANCHOR* and *Feature:
   REL_POINTER* sections give `REL_ANCHOR_DOMAIN`/`KEY` and `REL_POINTER_DOMAIN`/`KEY`/`ROLE` with
   rules and worked examples (`search_docs`, server 1.32.3, docs index 2026-07-31 20:21 UTC) — so the
   gate rejects scaffolding the specification prescribes.

   When you choose the `REL_ANCHOR_DOMAIN` and `REL_POINTER_DOMAIN` values, use codes without dashes.
   The Entity Specification's *Feature: REL_ANCHOR* defines the domain as *"a code (without dashes)"*
   and gives the rule *"Use a domain code without dashes to avoid confusion in downstream match key
   parsing."* — its *Feature: REL_POINTER* refers `REL_POINTER_DOMAIN` back to that definition
   (`search_docs(query='MATCH_KEY disclosed relationship REL_POINTER role in match key')`, server
   1.37.13, docs index 2026-09-24 18:45 UTC).
3. **Neither script runs on a CSV source. CONFIRMED CURRENT — server 1.32.9, 2026-08-14.**
   `sz_verbatim_check.py` and `sz_routing_report.py` both
   define `load_jsonl(path)` as `json.loads(ln)` over the file's non-blank lines, with **no** CSV
   branch and **no** `try` around the parse, and both are documented `<source.jsonl> <output.jsonl>`
   — re-read from the scripts the server delivers, same date — while
   `mapping_workflow` accepts CSV inputs and its own step-4 PATHS block names the CSV as
   `<input_file>`. On CSV both therefore die with an **unhandled
   `json.decoder.JSONDecodeError`, exit 1 — and its message text depends on the CSV's first line**,
   so do not match on the wording: `Extra data: line 1 column 5 (char 4)` and
   `Expecting value: line 1 column 1 (char 0)` are the same crash from the same cause on different
   headers. A crash here is a **tool
   limitation, not an environment problem** — see the gate presentation at step 4, which says so
   where you will meet it.

4. **The routing report counts every PAYLOAD field as "dropped". CONFIRMED CURRENT — server
   1.35.3, 2026-09-01.** `sz_routing_report.py` exempts payload fields from its dropped list —
   `exempt_fields = NEVER_FROM_SOURCE | set(payload_fields)` — but `discover_payload_fields()`
   populates that set only from a `--payload-fields` override or from a `phase1_manifest.json`
   beside the output, and **neither exists in this workflow**: step 4's own command passes no
   override, and `phase1_manifest.json` is not among the seven resources `mapping_workflow`
   delivers (`sz_schema_generator.py`, `sz_json_analyzer.py`, `sz_verbatim_check.py`,
   `sz_routing_report.py`, `senzing_entity_specification.md`, `senzing_mapping_examples.md`,
   `identifier_crosswalk.json`) nor written by any step. So the set is always empty and the
   exemption never engages. Re-read from the script the server delivers today (6,855 bytes): the
   `return []` at the end of `discover_payload_fields()` is still what runs.

   **Measured, server 1.35.1, 2026-08-31** — mapping the 1,554-record `las-vegas /
   US-LABOR-VIOLATIONS` CORD source (61 fields; 6 feature, 6 payload, 49 ignore): **14,480** dropped
   entries as the workflow instructs, against **5,620** with `--payload-fields` supplied by hand.
   The **8,860** difference — 61% of the report — is the six correctly-dispositioned payload
   fields, all present at the root of all 1,554 output records. **The report contradicts itself
   within one page**: it prints those same fields under *"Payload root keys"* a few lines above the
   dropped list.

   ⛔ **(INV-173) Never promote a payload field into a feature to quiet this report.** Step 4 tells you to
   reconsider every dropped entry *and* not to route dropped values into payload; with payload
   fields listed as dropped those two instructions conflict, and the path of least resistance is
   the **dumping-ground anti-pattern the workflow's own mapping reference warns against** — reached
   by believing a broken measurement. Read the dropped list with your payload fields struck out,
   or re-run with `--payload-fields "<your payload fields, comma-separated>"` for the true list.
   ⚠️ **This is a reporting defect, not a mapping one**: it says nothing about your dispositions,
   and nothing about the mapping needs changing because of it.

**Handling is the same for all four: the four steps above.** Do not conclude the mapping is wrong,
confirm faithfulness against the Entity Specification via MCP, record the exemption and its reason,
and proceed (INV-173). For the CSV case the workable route is to adapt CSV→JSONL and call the
checker's own `verify()`, so the executed logic stays upstream's, unmodified.

⛔ **Do not ship a patched copy of any of these scripts.** They are MCP-delivered, and a fork masks
the upstream fix (INV-173) — the numeric-value entry above is the proof that these do get fixed. Work
around them and re-check whether the workaround is still needed.

Do not ship a patched copy of `sz_verbatim_check.py`: it is delivered by the MCP server, so the fix
arrives from upstream and a fork would mask it (INV-080). The numeric case is the worked example —
reported 2026-07-28, fixed in 1.32.2 — and a fork would still be carrying the workaround today.

**One mechanism, three known reachings — recognize the fourth on sight rather than filing it as a
discovery.** `sz_verbatim_check.py` harvests the allowed set from source **values**, and every
entry in this block is that one scope limit reached by a different route:

| The emitted value is derived from… | Where it is documented here |
|---|---|
| a source value stored as a **JSON number** (non-string) | the non-string-values entry above |
| a source **field name** | this entry |
| a **hash** over identity fields (`RECORD_HASH`) | limitation 2's REL_*_KEY condition |

Any value the mapper computes rather than copies will be absent from the allowed set, whatever
produced it. If you meet a fourth route, the resolution is the same four steps — confirm
faithfulness on the Entity Specification's terms, record the exemption and its reason, proceed, and
never alter a source value to satisfy the tool (INV-048/INV-173).

⛔ **A value derived from a source *field name* is a second, distinct cause of the same failure —
and unlike the cases above it has no correct alternative emission.** The allowed set is built from
source **values** only. So any value that is faithfully derived from a source **field name** — a
dynamic-key convention such as `"Digital Currency Address - <CODE>"` or
`"Listing Date (EO 14024 Directive N):"` — will never be in it, **whatever that value's own type
is**. The upstream numeric fix does not help here: the string is simply not a value anywhere in the
record.

**The concrete case, which this module's own worked example produces.** The mapping reference
delivered inline at `mapping_workflow` step 2 states (server **1.32.2**, verified **2026-07-29**):

> "A crypto/'Digital Currency Address' (Bitcoin/XBT, ETH, USDT, XMR, LTC, TRX, XRP, BCH, …) maps as
> ACCOUNT_NUMBER = the address string, ACCOUNT_DOMAIN = the currency/network code (e.g. 'Digital
> Currency Address - XBT 1A1zP...' -> ACCOUNT_NUMBER:'1A1zP...', ACCOUNT_DOMAIN:'XBT'). One ACCOUNT
> object per address."

Follow that exactly on a source whose fields are `"Digital Currency Address - XBT"`,
`"- LTC"`, `"- ETH"`, and the verbatim check **fails** every such record on `ACCOUNT_DOMAIN`
(reproduced 2026-07-29: two records → `rec0 ACCOUNT_DOMAIN='XBT'; rec1 ACCOUNT_DOMAIN='LTC'`,
exit 1). `ACCOUNT_DOMAIN` is not in `EXEMPT_KEYS` and does not end `_TYPE`, so there is no waiver.
The mapping is **right** — `ACCOUNT_DOMAIN` is defined as "Domain/system for the account number"
(`search_docs(query='ACCOUNT_NUMBER ACCOUNT_DOMAIN account feature',
category='data_mapping')`, Entity Specification, *Identifiers > Feature: ACCOUNT*, verified
2026-07-29; query re-verified as top hit on 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-04, returning
"Domain/system for the account number" verbatim), and a currency/network code is exactly that.

**What to do:**

1. **Confirm it really is field-name-derived, not fabricated.** Check that the code does not appear
   as a standalone value elsewhere in that same record. If it *does*, the checker is right and your
   mapping should route the value from that field instead.
2. **Do not submit `rework_code`.** `mapping_workflow` step 4's generic instruction — "Exit 1 = a
   code bug… do NOT proceed until it passes" — **does not apply to this class**: no code change
   produces a different, still-faithful `ACCOUNT_DOMAIN`, so `rework_code` would be inaccurate and
   would loop. Advance with `verdict='approve'`.
3. **Record the exemption and its reason** in the source's mapping notes — which attribute, that its
   value is derived from the source field name, and that the checker harvests values only — then
   proceed, exactly as for the boolean case above (INV-048: a checker limitation MUST NOT become an
   iterate-forever loop or a blocked module).

⛔ **Separate structural invalidity from conformance-to-recommendation before acting on the
analyzer's output.** The analyzer's exit code alone is NOT the gate — its findings fall into two
kinds, and only one of them blocks:

- **Structural invalidity — blocking.** Malformed JSON, a missing `DATA_SOURCE`, an unparseable
  record. The data cannot load. Fix it before proceeding.
- **Conformance to the recommended schema — informational.** The record loads and resolves, but
  does not use the shape Senzing now recommends. Report it as a notice. It is **never** a reason
  to remap a source.

The observed instance of the second kind is the older **flat** format: feature attributes at the
record root, with a per-feature root sub-list (`NAMES`, `ADDRESSES`, `IDENTIFIERS`) wherever a
feature repeats. A source with no repeating feature is in this shape with no sub-list at all.
Against such a source the analyzer returns a non-zero exit with errors of the form:

```text
Line 1: Missing or non-array FEATURES
Line 1: Feature attribute 'RECORD_TYPE' must be inside FEATURES array
```

— hundreds per source, plus the warning `No NAME features found`.

**That data is supported.** The Senzing Entity Specification, § "Recommended JSON schema", says so
in as many words:

> "In prior versions we allowed a flat JSON structure with a separate sub-list for each feature
> that had multiple values. **While we still support that**, we now recommend the following JSON
> schema that has just one list for all features."

Re-confirm that statement from the MCP server rather than trusting this file (a sourcing floor)
(`search_docs(query='recommended JSON schema FEATURES list multiple values sub-list',
category='data_mapping')` — that query returns the *Recommended JSON schema* section carrying the
sentence above as its top hit, verified server 1.37.19, docs index 2026-10-02 18:46 UTC,
2026-10-04; `query` is the tool's only
required parameter, so the vocabulary is part of the instruction (INV-212) — or
`download_resource(filename='senzing_entity_specification.md')`
— that second call returns a **listing**, so fetch its `url` before reading, per `ground-rules.md` →
"Three tools answer with a listing") — INV-080 applies to this claim as much as to any attribute name.

**Do not assume a source's shape from its provenance.** CORD ships both forms: verified against the
MCP server, London/`GLOBALDATA` returns a `FEATURES` array while Las Vegas/`PPP_LOANS` returns flat
root attributes. Read the actual records.

⚠️ **Why the analyzer is not wrong, and still must not block.** The same specification section's
*Schema Validation Rules* state `FEATURES (required, array)`. The analyzer applies the
**recommended** schema's rules; the prose above grants continued support for the **legacy** shape.
Both statements are true, and they answer different questions. The analyzer measures conformance;
the gate this module needs is loadability.

**`No NAME features found` does not mean the names are missing.** It is an artifact of the analyzer
not looking inside the sub-list — it reports `NAMES` and `ADDRESSES` as *payload* attributes and
skips feature analysis entirely. Names in sub-list records are extracted normally at load. This is
the single most misleading line in the report, because a bootcamper cannot tell "the analyzer did
not look there" from "there are no names", and the natural conclusion is that the source is unusable.

**When the analyzer and the specification disagree, resolve it empirically — do not pick a
document.** Load **one** unmodified record and inspect the features Senzing extracted. If they come
back extracted, the data is loadable and every finding of this kind is conformance advice. Record
the probe's result and the conclusion you drew in that source's
`config/mapping_state_[datasource].json` (INV-125 already requires recording the raw failure and the
concluded cause). Module 5's own test load (`phase3-test-load.md`) is the same instrument one phase
later — this is that check, run early and on a single record.

⛔ **Never hand-write a mapper to convert a supported format into the recommended one in order to
clear this finding.** That is real work — five sources in the reported session — spent to satisfy a
notice. Converting is a legitimate *optional* improvement, on the grounds that new Senzing work
should target the recommended shape; offer it that way, never as remediation of a defect, and never
as a precondition for continuing.

⛔ **When `mapping_workflow`'s step-3 validation rejects the payload without an actionable
reason.** The block above handles a validator that is *unavailable*; this handles one that runs and
rejects unusably. Treat a rejection as **unactionable** when its text names no field and carries no
line or pointer the payload could be corrected against — a truncated error string is the observed
case.

1. **Bound the retry at two.** After two unactionable rejections for the same source, stop. A third
   attempt is guesswork with no convergence signal, and guessing costs the bootcamper more than the
   documented path saves.
2. **Capture the evidence first.** Before falling back, write the raw rejection text **verbatim**
   into that source's `config/mapping_state_[datasource].json` (a `validation_rejections` array).
   It is the only diagnostic the upstream fix has, and it is otherwise lost when the session ends.
3. **Ask, do not decide.** Present this pinned 👉 question (INV-051/INV-056, numbered, no "or"):

   👉 **The mapping validator rejected this source twice without saying why. How would you like to proceed? Reply with a number:**

   1. **Write the mapper against the Senzing Entity Specification** *(recommended)* — all three quality gates still run.
   2. **Try the mapping workflow once more** — it may succeed with a different payload.
   3. **Skip this source** — continue with the sources that mapped successfully.

   *(Internal: end the turn on this question and wait — INV-007.)*

4. **On option 1, the fallback is bounded, not a free hand.** State plainly what still holds:
   - Attribute names come from the Senzing Entity Specification in `docs/reference/` (see
     "Entity specification reference" below) — **never** from training data or memory. The
     "NEVER hand-code or guess Senzing attribute names" rule at the top of this phase is
     unchanged: reading the specification is not guessing (INV-080).
   - **All three quality gates still run**, with the same availability-aware handling as above.
   - The ⛔ cross-source shared-feature collision check still runs — it is cross-source, and the
     validator never performed it anyway.
   - The mapping is still only **structurally** validated; Data processing's match-key audit
     remains the semantic check (INV-117).
5. **Record how each mapper was produced.** Note the fallback and its reason in the source's
   mapping-state checkpoint and in its `docs/mapping/` write-up, so a reader of the deliverable can
   tell which sources went through `mapping_workflow` and which did not.

`mapping_workflow` remains the default and documented path. Never offer this fallback
preemptively — only after two unactionable rejections of the same source.

⛔ **These gates are structural, not semantic — say so; do not let green be mistaken for correct.**
Every check above validates **one source at a time** and asks whether the output is *well-formed*:
the analyzer checks structure against the Entity Specification, the verbatim check that values were
not altered, the routing report that fields reached a feature, the quality score completeness and
format. **None of them evaluates whether a field means what the feature means**, and none compares
how two sources populate the *same* feature. A mapping can pass all of them and still be wrong in
the way that matters most — telling Senzing two things conflict when they do not, which suppresses
legitimate merges.

Tell the bootcamper this plainly when reporting a passing result: the mapping is **structurally
valid**, and it is not **semantically validated** until data is loaded and the match keys are read.
Data processing's match-key audit is where that happens. A bootcamper who hears "all gates green"
and infers "the mapping is correct" has been misled by omission.

**Checkpoint:** write step 11.

### 12. Generate starter code

This step does **not** advance the workflow — generating the sample JSON and starter mapper is work
performed inside workflow step 4, which advances once at step 15 with its verdict (see the call
contract above). Tell the user: show a sample target JSON record so they see the output format.

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Show a sample target JSON record with annotations explaining the structure
>   (which fields became which Senzing attributes, how DATA_SOURCE and RECORD_ID are set, nested
>   vs. flat layout).
> - **Concise:** State the output file path and format only (e.g., "Output:
>   data/senzing-ready/customers.jsonl: one JSON record per line").

After `mapping_workflow` generates output files into the workspace, place them into the correct
project subdirectories per the file-placement guidance above (`.py` → `src/`, transformed JSONL
→ `data/senzing-ready/`, mapping docs → `docs/mapping/`, etc.). Regenerating a `docs/README.md`
docs index is a later porting phase: skip it for now.

**Checkpoint:** write step 12.

### 13. Build the transformation program

Use `generate_scaffold` or the mapping workflow output as the foundation. Handle: input
reading, field mapping, type conversion, cleansing, `DATA_SOURCE`/`RECORD_ID`, and error
handling. Save to `src/transform/transform_[name].[ext]`. Tell the user: the file path, what it
reads/writes, and what it handles.

⛔ **On Java, that `snake_case` filename and an idiomatic class name cannot both be `public`** —
declare the top-level class package-private and keep the prescribed path. Applies equally to the
`<name>_mapper.<ext>` the workflow's own step 4 asks for. The rule, its reason and the C# difference
are in `../bootcamp-onboarding/ground-rules.md` → "File placement" (INV-237, INV-300); do not restate them
here.

**Keep JSON handling dependency-free.** This is usually the first Java the bootcamp generates, and
the bootcamp compiles with plain `javac` and never sets up Maven or Gradle — so the mapper must not
depend on an external JSON library (a scaffold importing `javax.json` will not compile as written).
Write the reader here so it needs only the standard library, and **reuse this same reader in later
modules** rather than re-deriving one per module: Data processing's loading program expects it. Full
rationale, and the rule that replacing the JSON library is safe while altering SDK calls is not, are
in `../module-02-sdk-setup/SKILL.md` → "The launch environment" (INV-300).

On Java, a reused reader is a shared class, whose filename rule is in
`../bootcamp-onboarding/ground-rules.md` → "File placement" (INV-237, INV-300); do not restate it
here.

**Apply a retype decision from Phase 1.** If `docs/mapping/{source_name}_mapper.md` already has a
`## Record Type Check` section whose decision is **Retype**, the transform applies that section's
rule as written: the records it names are emitted with `RECORD_TYPE` `ORGANIZATION`, their name is
emitted as `NAME_ORG` and never as parsed person fields, and the listed exceptions stay `PERSON`.
That is the branch on `RECORD_TYPE` that step 11 declared. With parsed name fields, a retyped
record's `NAME_ORG` value is the parsed fields joined in the order Phase 1 Step 6 reads them. The
check and the rule's wording are Phase 1 Step 6's "Type/name check"
(`phase1-quality-assessment.md`), the canonical statement; do not restate them here (INV-300). Step
15's verbatim check may report a joined `NAME_ORG`: that is a checker limitation, not a mapping
defect, so follow its "What to do — in this order" procedure and never undo the retype to turn the
gate green (INV-173). With **Keep as-is**, or no such section, change nothing.

**Checkpoint:** write step 13.

### 14. Test

Run the transformation program on 10-100 records from `data/samples/` and write its output to
`data/mapping/{source}_sample.jsonl`, the sample step 18 records. Validate with
`analyze_record(workspace_dir='data/mapping')` — ⛔ `workspace_dir` is a **required** parameter on
this tool as well (INV-136), and it is where the analyzer script and its reports are written, so it
takes the same project-local mapping directory as the workflow, which INV-200 requires of every
tool argument naming a writable directory. Re-confirmed on MCP server 1.33.0, 2026-08-21:
`get_capabilities` describes `analyze_record` as taking a "REQUIRED parameter: `workspace_dir` (a
writable directory where the analyzer script and any reports are saved); do NOT assume /tmp
exists". Tell the user: pass/fail, output file path,
sample record, any observations.

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Show pass/fail result, the output file path, a sample transformed record, and
>   any observations (warnings, skipped records, format issues).
> - **Concise:** Show pass/fail result and the output file path only (e.g., "✅ Pass: output:
>   data/mapping/customers_sample.jsonl").

**Checkpoint:** write step 14.

### 15. Quality analysis

Run the transformation program on 1000+ records, or on every record when the source has 1000 or
fewer, and write its output to `data/mapping/{source}_quality.jsonl`. The output stays there even
when the run covers every record: this is a test run, and the load-ready file is step 18's alone.
Its name differs from step 14's, so this run never overwrites the sample. Evaluate feature
distribution, coverage, quality scores. This is workflow
step 4's single advance: `action='advance'`, carrying `verdict` in `data` — `approve`,
`rework_mapping`, or `rework_code` — plus `output_path` (`data/mapping/{source}_quality.jsonl`)
and `records_output`. A `rework_*` verdict
is what routes step 17's iterate path. On `approve`, the response carries the workflow's Step 5
(`detect_environment`) menu; keep its `state` and handle that menu at **step 18a**, after this
source's mapper is written, reviewed and documented — not here. Tell the user: overall score, per-feature coverage with what
it means for matching, any issues found.

⚠️ **This advance is unconditional in both modes too, and for a different reason than step 11's.**
The `verdict` is not a preference the bootcamper holds — it is a QA judgment that follows from the
analyzer's own output (features at 0%, a short record count, a payload that should have been a
feature), so putting it to a vote would be asking them to ratify evidence they have just been shown.
Compute it, say which check decided it, and advance. The bootcamper's decision points here are the
pinned 👉 questions that follow — the visualization offer and the quality-gate branches — not the
verdict itself.

> **Presentation (conditional on `mapping_verbosity`):**
>
> - **Verbose:** Show the overall quality score, per-feature coverage breakdown with matching
>   implications (e.g., "NAME coverage 98%: strong for matching" / "ADDR coverage 42%: may
>   reduce match accuracy"), and all issues found with explanations.
> - **Concise:** Show the overall quality score, a count of mapped vs. unmapped fields, and
>   warnings only (e.g., "Quality: 85/100. 8 mapped, 3 unmapped. ⚠️ Low address coverage may
>   affect matching.").

**Offer visualization:** Pin the offer verbatim:

> 👉 **Would you like a web page showing the quality analysis (coverage charts and the field mapping summary)?**

If yes, generate a self-contained HTML page and save it to
`docs/visualizations/mapping_[name]_quality.html` (INV-070).

⛔ **Same four rules as the quality-assessment visual in `phase1-quality-assessment.md`** — this is a
bootcamper-facing visual deliverable too, and the reasons are identical: brand tokens from
`${PLUGIN_ROOT}/scripts/brand_tokens.py` (INV-081; skill-relative fallback
`../../scripts/brand_tokens.py`, INV-252); **renders offline**, so no CDN or web font
— inline the vendored `${PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js` (skill-relative fallback
`../../scripts/vendor/d3.v7.min.js`, INV-252) if a chart library is needed (INV-081/INV-091);
every data-sourced string escaped for the context it lands in, including `<`/`>`/`&` as `\uXXXX`
inside any inline `<script>` payload (INV-106); and verify the rendered page rather than the exit
status (INV-129). The mapping summary carries **more** bootcamper-authored text than the phase 1
page — source field names, target attributes, sample values — so the escaping rule matters most here.
`ground-rules.md` → "Visual deliverables (Senzing brand)" and the visualization contract's
"Rendering contract" are the statements of record.

**Capture it for the recap, right after the page is written and verified.** Follow
`../bootcamp-onboarding/module-completion.md` → "Capturing visualization screenshots", using its
`--single` case: this page has no tabs, so it is one image, with `{name}` = `mapping_[name]_quality`.
That section is the statement of record for the helper, its exit codes and the skip rules (INV-300).
Record the PNG path in this step's checkpoint, in the same turn (INV-146). It is embedded in this
module's recap at module close.

**Checkpoint:** write step 15 (with the captured PNG path, when there is one).

### 16. Review

Confirm with the user: output format correct, quality acceptable, ready for production or needs
adjustment.

**Iterate vs. proceed decision gate:** After presenting quality results, guide the decision and
close the turn on one 👉 question. Which questions apply depends on whether an **unmapped source
remains**: `config/data_sources.yaml` has a source other than this one whose `mapping_status` is
not `complete`. Fast-pathed sources are `complete` (see "Skip fast-pathed sources"), so they never
count. Read the registry before choosing the question. Each question is pinned verbatim (INV-056).

**While one or more unmapped sources remain** (INV-344), ask about the next source, not about loading.
`{source}` is this source's name, and `{next}` is the next unmapped source, the one step 19 maps next:

- **Quality ≥80% and all critical fields mapped:**

  👉 **Quality looks strong for {source}. Ready to map the next source, {next}? Reply with a number:**

  1. Yes, map {next}.
  2. No, I'd like to iterate on {source} first.

- **Quality 70-79%:**

  👉 **Quality for {source} is acceptable. What would you like to do? Reply with a number:**

  1. Move on to the next source, {next}.
  2. Iterate to improve [specific weak areas] first.

- **Quality <70%:**

  👉 **Quality for {source} needs improvement before loading will produce meaningful results. I'd recommend going back to address [specific issues]. What would you like to do? Reply with a number:**

  1. Iterate to improve the data.
  2. Move on to {next} anyway, knowing results may be limited.

Handling (INV-284): "Yes, map {next}", "Move on to the next source, {next}" and "Move on to
{next} anyway" continue through steps 17–18a, where 18a's multi-source rule recommends `skip`, to
step 19, which starts {next}'s own `mapping_workflow` run. Every iterate option goes to step 17.

**When no unmapped source remains** (INV-344; this is the last source, or the only one), ask the loading
question:

- **Quality ≥80% and all critical fields mapped:**

  👉 **Quality looks strong. Ready to proceed to loading (Data processing)? Reply with a number:**

  1. Yes, proceed to loading.
  2. No, I'd like to iterate on something first.

- **Quality 70-79%:**

  👉 **Quality is acceptable. What would you like to do? Reply with a number:**

  1. Proceed to loading now.
  2. Iterate to improve [specific weak areas] first.

- **Quality <70%:**

  👉 **Quality needs improvement before loading will produce meaningful results. I'd recommend going back to address [specific issues]. What would you like to do? Reply with a number:**

  1. Iterate to improve the data.
  2. Proceed anyway, knowing results may be limited.

Handling (INV-284): a proceed answer ("Yes, proceed to loading", "Proceed to loading now",
"Proceed anyway") continues through steps 17–18a, where it settles the sandbox menu as `skip`
(see 18a's last-source rule), then to steps 19 and 20. Every iterate option goes to step 17.

*(Internal: end the turn on the applicable question and wait.)*

**Checkpoint:** write step 16.

### 17. Iterate

If issues are found, go back to the relevant step. Retest after changes.

> **Data source registry:** Update the source's `mapping_status` to `complete` in
> `config/data_sources.yaml` and set `updated_at`.

**Checkpoint:** write step 17.

### 18. Save and document

- Program in `src/transform/`.
- Full output: run the transformation program on the whole source and write
  `data/senzing-ready/[name].jsonl`, the load-ready file Data processing loads. Point the source's
  `file_path` in `config/data_sources.yaml` at it.
- Docs in `docs/mapping/mapping_[name].md` (field mappings, logic, quality, how to run).
- Sample output in `data/mapping/[name]_sample.jsonl`.
- **Transformation lineage:** Create `docs/mapping/transformation_lineage_[name].md` for this
  data source, covering source file info, transformation program, output file info, field
  mappings, format changes, filters, quality improvements, and before/after record counts. (The
  Kiro `templates/transformation_lineage.md` template is a later porting phase; compose the
  lineage document directly for now.)
- **Entity specification reference:** The Senzing entity specification reference lives only at
  `docs/reference/senzing_entity_specification.md`: a single canonical copy. Do NOT create a
  copy in the `docs/` root; if one exists there, remove it.
- **Per-source mapping specification:** Save a mapping specification markdown to
  `docs/mapping/{source_name}_mapper.md` for this data source. This file is always per-source,
  even when the transformation program is shared. Use this structure:

  ```markdown
  # Mapping Specification: {SOURCE_NAME}

  **Source file:** data/raw/{source_file}
  **Data source name:** {DATA_SOURCE}
  **Entity type:** Person / Organization / Both
  **Generated by:** mapping_workflow

  ## Field Mappings

  | Source Field | Senzing Attribute | Transformation | Notes |
  |---|---|---|---|
  | ... | ... | ... | ... |

  ## Mapping Decisions

  - [Key decisions made during mapping]

  ## Quality Notes

  - [Quality observations specific to this source]

  ## Record Type Check

  - **Candidates:** [N] of [M] PERSON-typed records (suffix heuristic, Module 5 Phase 1 step 6)
  - [Decision, and its rule or cost, as Phase 1 wrote them]
  ```

  **Keep the `## Record Type Check` section Phase 1 wrote.** Phase 1 Step 6's type/name check
  creates this file with that section when a source has candidates. Write the rest of the file
  around it and leave the section as written. When Phase 1 wrote none, the source had no
  candidates: write the section with `0 of [M]` and the decision `none needed`. The section's
  content is Phase 1 Step 6's "Type/name check", the canonical statement (INV-300).

**Checkpoint:** write step 18.

### 18a. Step 5 `detect_environment` menu handling (the optional-sandbox decision)

The `approve` verdict at step 15 advances workflow step 4, and the response to that advance carries
the workflow's **Step 5 (`detect_environment`)**, which takes one decision with two values, `skip`
or `test_load` (server 1.37.16, 2026-10-01: `ADVANCE FORMAT: {"decision": "skip|test_load"}`, and
its `advance_schema` declares `decision` as `enum ["skip", "test_load"]`). The same response's
message lists four numbered *next steps* (more sources to map, sandbox QA, load and report, done):
those are advice, not values the step accepts. Handle the decision **here**, once
this source's mapper is written, run, reviewed and documented (steps 12–18) — not at the moment the
response arrives.

⛔ **Why the placement matters.** This block previously sat under step 11 (Map), and
`phase3-test-load.md` pointed at step 11 as its entry. Both were wrong in the same direction:
choosing `test_load` there entered Phase 3 before the transformation program existed, so Phase 3's
step 22 had no "Phase 2 transformation output" to sample, and Phase 3's exits rejoin Phase 2 at
step 19 — which would have skipped steps 12–18 entirely, including the transform code
INV-042/INV-043 require and the `docs/mapping/{source_name}_mapper.md` that step 19's per-source gate
checks. Entering from 18a, every prerequisite Phase 3 assumes is already on disk.

Do NOT stop at the menu: explain it and relay a recommendation so the bootcamper never hits a dead
end.

**`mapping_workflow` Steps 5–8 are optional sandbox validation** (Phase 3). They let you
trial-load the mapped source into a throwaway sandbox to preview entity resolution. They are
NOT the production load: the real load happens in **Data processing**. The two options are:

- **skip:** skip the per-source sandbox test load and move on. **Recommended when one or
  more unmapped sources remain.**
- **test_load:** run the optional sandbox test load (enters Phase 3) for this source.

**Multi-source continuation (recommended path):** When one or more unmapped sources remain,
recommend **skip**: the real load is deferred to Data processing, so a per-source sandbox test load
adds little here — and automatically continue to the next unmapped source (step 19) by starting its
own `mapping_workflow` run. Tell the bootcamper: "Steps 5–8 are an optional sandbox preview; since
you still have sources to map and the real load happens in Data processing, I'll skip the per-source
test load and move on to the next unmapped source."

**Last source (no unmapped source remains):** (INV-344) a step-16 answer that proceeds to loading (≥80%
option 1, 70-79% option 1, or <70% option 2) settles this decision as **skip**. Tell the bootcamper
so in one line, for example "You chose to proceed to loading, so I'll skip the optional sandbox test
load; the real load happens in Data processing.", advance with `skip`, ask no 👉 question here, and
continue to step 19.

**Explicit choice is preserved:** If the bootcamper explicitly asks for the sandbox test load
(**test_load**), at any source, follow that path into Phase 3 (`phase3-test-load.md`) unchanged.
The real production load still happens in Data processing regardless. Phase 3 tests this source
only, and every exit from it returns here: its step 25 "yes" and its skip exits resume at step 19,
and its step 25 "no" at step 17 (`phase3-test-load.md` → "Leaving Phase 3", INV-344). So a test load
chosen on a source that is not the last continues to the next unmapped source, with no question
about the whole run.

**Checkpoint:** write step 18a.

### 19. Repeat for remaining data sources

Each source gets its own transformation program and its own `mapping_workflow` run.

⛔ **Before starting the next source's `mapping_workflow(action='start')`, confirm this source's
profile report (`profile_report.md`, or every `profile_report_<stem>.md` when several files were
profiled), `schema_hints.md` and `JOURNAL.md` have already been relocated to
`docs/mapping/` under their source-qualified names** (`{source_name}_profile_report.md`,
`{source_name}_schema_hints.md`, `{source_name}_JOURNAL.md` — see "File placement during the
workflow"). This is INV-177: relocation under a source-qualified name happens **before** the next
source's run begins. Every source shares one `workspace_dir`, and the next run rewrites those three fixed
workspace filenames for its own profiling, so anything still sitting there under an unqualified
name is lost — silently, with no error.

> **Mandatory internal gate (do not render to the bootcamper):** BEFORE writing the module
> completion checkpoint, list ALL files in `data/senzing-ready/` and verify that EACH has a
> corresponding `docs/mapping/{source_name}_mapper.md`. If any are missing, create them NOW. Do
> NOT write the module completion checkpoint until all mapping specs exist. This is a hard
> requirement: the module is not complete without a per-source mapping specification for every
> transformed data source.

**Per-source completion checkpoint:** Before marking a source as complete, verify that
`docs/mapping/{source_name}_mapper.md` exists for that source. Do not proceed to the next source
or mark the current source done until its mapping specification markdown is saved. When all
sources are mapped, confirm every completed source has its own file. When a source's mapping is
complete, delete its `config/mapping_state_[datasource].json` checkpoint.

**Checkpoint:** write step 19.

### 20. Module completion and transition

Once all sources are mapped, **complete the module** — this is Module 5's only completion site,
whether or not any source took the optional Phase 3 test load (Phase 3 returns to step 19 and never
completes the module).

> **Optional: baseline status summary (advisory, non-blocking):** When any source took the Phase 3
> test load, you MAY surface which data sources still lack an ER baseline (compare the set of
> `config/er_baseline_*.json` files against the mapped sources). It is read-only, never blocks
> the workflow, and never creates, modifies, or deletes a baseline. (The Kiro
> `baseline_status.py` helper is a later porting phase; report coverage directly if you choose
> to.)

Run the standard **Module Completion** process in
`../bootcamp-onboarding/module-completion.md`: present the end-of-module summary (INV-032), append
the name-based Module 5 recap section to `docs/bootcamp_recap.md` (INV-085), show the
`✅ Module complete: Data Quality, Mapping, and Transformation` line (INV-079), and end the turn on the pinned
transition 👉 question naming the **next selected module** from `selected_modules` (INV-076 / INV-079):

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)*

Do **not** choose the next module by re-checking SDK state — `selected_modules` already fixes the
order (SDK setup precedes Data Quality, Mapping, and Transformation; Data processing follows it). **Run Module
Completion exactly once,** here: Phase 3 never runs it. A resume that finds Module 5 already complete
presents only the transition question above (this module's `SKILL.md` → "Resuming").

**Checkpoint:** write step 20.
