# Module 6, Phase C: Multi-Source Orchestration (conditional, 2+ sources, steps 12–20)

Continues from Phase B. Follow the ground rules; `🛑`/`⛔` are internal control directives.
Senzing SDK calls (the loader, redo and engine setup) come from the MCP tools, never
hand-written. The orchestration around them (ordering, retries, per-source isolation, health
summaries, reconciliation) is ordinary code in the bootcamper's language, because no MCP route
serves it.

**Conditional gate.** Read `config/data_sources.yaml` and count sources with `mapping_status:
complete`. If there is only ONE data source, skip Phase C entirely and proceed to Phase D
(`phaseD-validation.md`). Only present these steps when the bootcamper has 2 or more sources to
load.

## 12. Inventory all data sources

Read `config/data_sources.yaml` for `quality_score`, `mapping_status`, and `load_status` per
source. Enumerate every data source. For each: source name / DATA_SOURCE identifier, record
count, quality score, mapping status, loaded status. Present a summary table so the bootcamper
can review and confirm the list is complete.

⛔ **A source whose `validation_checks.load_count_matches_source` is `expected_delta` is a
RECONCILED result, not a failure and not a plain pass.** Show the figures and the chain its
`load_reconciliation` note cites — "7,386 loaded from a 7,386-record overlap-preserving sample of
63,863 collected", or "3,727 loaded from 3,488 collected records; 239 embedded masters, per the
source's mapping specification" — and never render it as `failed`. It is the visible consequence of
a sampling or mapping decision the bootcamper made in an earlier module, so it is worth showing
rather than flattening. The outcomes and what each cites are `phaseB-load-first-source.md` Step 7's
two-stage reconciliation, the canonical statement; do not restate it here (INV-300).

⛔ **The `record_count` shown here is a figure presented to the bootcamper, so it carries the
reconciliation requirement with it.** (INV-243) Phase B reconciles each count in two stages before
writing it; a source whose count was never reconciled — one loaded outside this bootcamp, or
carried in from an earlier session — **or whose stage 2 recorded `unexplained_delta`** MUST be shown
as unverified rather than as a plain number (INV-245), with the figures from its `issues` entry. An
`unexplained_delta` source loaded every record it was given, so it is never shown as `failed`
either: what is unverified is its gap to the collected file. A table is where an unchecked figure
acquires the look of a result, which is exactly the shape this rule exists for: the numbers are
plausible, they sum, and nothing about them invites a second look.

**Show a source's `load_subset:` block when it has one.** It is the subset record Phase B Step 7
defines ([the subset record](phaseB-load-first-source.md#load-subset-record)); read it from the
source's entry and do not restate its fields here (INV-300). For a loaded source, show it as the
"→ subset" step of that source's reconciliation chain. For a source not loaded yet, show it as the
subset that source will load: its `strategy`, its `limit` or measured `record_count`, and its
`reason`.

**Checkpoint:** write step 12.

## 13. Analyze dependencies

Explain the common dependency patterns: parent-child (load parents first), reference data first,
temporal ordering, or none. If a circular dependency is detected, explain that Senzing resolves
entities as records arrive, load the higher-quality source first.

**First, check the data's provenance.** Read the `provenance` field for each source being loaded
(step 12's inventory) in `config/data_sources.yaml` — the same field Module 5's fast-path uses. If
**every** such source is agent-generated (`provenance: cord` or `synthesized`), or
`docs/business_problem.md` carries the bootcamp-generated marker `> 🤖 Bootcamp-generated business
case`, the agent selected these sources itself and already knows both that there are no real
load-order dependencies between them and which loading strategy suits them. State that briefly
(INV-012) and confirm rather than asking an open question — pin the question verbatim (INV-056) and
end the turn on it:

👉 **The generated sources have no load-order dependencies, and I recommend the Sequential loading strategy for this dataset — shall I proceed on both?** (respond yes or no)

*(Internal: end the turn on this question and wait.)*

- **Yes:** record that there are no dependencies **and** that the strategy is Sequential. Step 15
  reads both from here and asks nothing further.
- **No:** the bootcamper is overriding, so give them both decisions in full — first ask them to
  describe the dependencies they see and capture the dependency map, then present step 15's
  numbered strategy menu so they choose (INV-007/INV-051). Neither override is skipped or
  abbreviated because the two were asked together.

⛔ **This one question deliberately covers two decisions, and it must not be split back into two.**
Both facts follow from the same provenance check, established before either was asked, and the
bootcamper was given nothing between them on which to answer differently — so as two gates they are
consecutive rubber stamps, which is what INV-012 and `ground-rules.md`'s warning against
answer-is-always-yes gates forbid. ⚠️ **Proceeding without asking at all is NOT the alternative**:
INV-007 says the plugin cannot answer its own questions or assume answers, so the decision stays the
bootcamper's. One question, both decisions, still theirs.

⚠️ **The shape to watch when adding the next one.** Each provenance-aware confirm in this phase was
written to a per-step budget of one question, and nothing counted questions **across** steps — so a
path can accumulate rubber stamps one defensible step at a time. Step 14 asks nothing, so 13 and 15
were adjacent in the bootcamper's experience while being two steps apart in this file. Weigh any new
confirm added to Phase C against the ones already on the same path, not only against itself.

**Only when some source being loaded is bootcamper-supplied** — `provenance: own`/`free_data`/`unknown`
in `config/data_sources.yaml`, and no generated marker in `docs/business_problem.md` — ask a single
pinned 👉 question (INV-056) exactly as today and end the turn on it:

👉 **Are there load-order dependencies between your data sources?**

*(Internal: end the turn on this question and wait.)* On **yes**, capture the dependency map; on
**no**, record that there are none.

Save the resulting dependency map (or the "no dependencies" record) to `docs/loading_strategy.md`.

**Checkpoint:** write step 13.

## 14. Determine load order

Use `quality_score` from `config/data_sources.yaml` to rank sources; update `load_status` as
loading progresses. Apply ordering heuristics (priority order): (1) reference before
transactional, (2) quality-first for a strong entity baseline, (3) attribute-density-first,
(4) volume-first when quality is similar. This is the one statement of these heuristics: Phase B's
opening (`phaseB-load-first-source.md`) applies them to choose the first source and cites this
step rather than restating them (INV-300).

**The first source is already decided and loaded.** Read the first-source choice Phase B's opening
recorded in `docs/loading_strategy.md`, which survives a resumed session. Present that source as
**already loaded, chosen by `<heuristic>`**, naming the heuristic it records. Then rank only the
remaining sources and present their recommended load order with reasons for the bootcamper to
review. If no choice is recorded, the first source is the one whose `load_status` is `loaded`:
present it as already loaded and name no heuristic, because none was recorded.

If step 13 recorded a dependency the first choice broke (a source that should have loaded before
it), say so plainly, record it in `docs/loading_strategy.md` beside the first-source choice, and
order the remaining sources to honor it.
⛔ **(INV-327) Do not reload the first source.**

This step asks nothing and is not a turn ending: present the order and continue to step 15 in
the same turn.

**Checkpoint:** write step 14.

## 15. Select loading strategy

**First, check the data's provenance** (as in step 13). If **every** source being loaded is
agent-generated (`provenance: cord`/`synthesized` in `config/data_sources.yaml`, or the
`> 🤖 Bootcamp-generated business case` marker is present in `docs/business_problem.md`), then
⛔ **the strategy was already decided at step 13 and this step asks NOTHING.**

Step 13's merged question covers both the dependency decision and the strategy for this path: on
**yes** it recorded **Sequential** — safer, easy to debug, with no real gain from parallelism at
this dataset's scale — and on **no** the bootcamper has already chosen from the numbered menu
below. Read the recorded answer, state the strategy in one line, and continue to step 16.

⛔ **Do not re-ask it here, in any form.** Re-confirming a decision the bootcamper made two steps
ago is the pair of back-to-back rubber stamps this branch was merged to remove — and it is worse
the second time, because nothing has happened in between that could change the answer. This step is
not a turn ending on this path: continue in the same turn to the next step that actually asks
(`ground-rules.md` → "A results presentation is not a turn ending", INV-225).

**Only when some source being loaded is bootcamper-supplied** — `provenance: own`/`free_data`/`unknown`
in `config/data_sources.yaml`, and no generated marker in `docs/business_problem.md` — present the
strategy choices as a neutral lead + numbered list (INV-051), pinned verbatim (INV-056), and end the
turn on the 👉 question:

👉 **Which loading strategy would you like? Reply with a number:**

1. **Sequential** — safer, easier to debug.
2. **Parallel** — faster, uses more resources.
3. **Hybrid** — sequential for dependent sources, parallel for independent.

*(Internal: end the turn on this question and wait.)*

**Checkpoint:** write step 15.

## 16. Pre-load validation checklist

Verify before orchestration: each source's load file exists at its registry `file_path`
(`data/senzing-ready/` for mapped sources; `data/raw/` for `fast_pathed: true` CORD /
already-Senzing-ready sources, which skipped mapping in Module 5) and is non-empty;
each source's DATA_SOURCE code is registered in the engine config (register any not yet
registered, idempotently — per Phase A step 4a; do not rely on Module 2's default config, which
predates data collection); RECORD_IDs unique within each source; a
database backup of `database/G2C.db` exists; sufficient disk space (~2x per source); the
Module 6 loading program works as a template. Fix failures before proceeding.

**Checkpoint:** write step 16.

## 17. Create orchestrator program

The orchestrator's Senzing calls come from the Step 3 loader (Phase A, "Create the production
loading program"), run once per source; its SDK code is
`generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`.
Override any `/tmp/` or `ExampleEnvironment` paths to `database/G2C.db`. Save to
`src/load/orchestrator.[ext]`.

<!-- MCP-NEGATIVE: find_examples(query='multi-source') with and without language='java', and find_examples(query='orchestrator load multiple data sources') — no indexed example is a multi-source load orchestrator (ordered per-source loading, per-source error isolation, reconciliation); the first returns examples: [] plus a hint, the second only single-source loaders, data-source registration snippets and CHANGELOGs — owner: find_examples IS the route for indexed example code and returned none; generate_scaffold IS the route for SDK templates and has no orchestration workflow (workflow='orchestration' is rejected with the list initialize, configure, add_records, delete, query, redo, stewardship, information, error_handling, full_pipeline, and full_pipeline returns single-source initialize/configure/load/search snippets) (absence negative) — server 1.37.13, 2026-09-26 -->

**First, compute the per-source budget table, so the plan is fixed before the run.** The license
cap and the SQLite subset choice apply to the whole load, and Phase B loaded only the first source.
Read the two whole-load markers Phase B recorded in `config/bootcamp_preferences.yaml`,
`license_cap_prompt` and `sqlite_volume_prompt`. Both, and the **remaining cap**, are defined in
[the subset record](phaseB-load-first-source.md#load-subset-record), `phaseB-load-first-source.md`
Step 7; cite that definition and do not restate it here (INV-300). Then show the bootcamper one
row per remaining source, with three columns: **source**, **fill order** (Step 14's load order)
and **limit** (a first-N limit, a subset file with its measured `record_count`, **full**, or
**not loaded**, with the `reason` that set it). Fill the rows by the recorded choice:

- **`license_cap_prompt.choice: overlap_preserving`** (license-cap option 1): Phase B already
  selected across every mapped source and wrote each remaining source's subset file under
  `data/subsets/` and its `load_subset:` block. Each row takes its source's block, and no new
  budget is computed. A block with `record_count: 0` is a **not loaded** row.
- **`license_cap_prompt.choice: first_n`** (license-cap option 3): the budget is the remaining
  cap, and later sources get only what is left of it, possibly nothing. Fill it in Step 14's
  load order: each source's N = min(its load-input count, the budget left), and the budget left
  drops by N. A row whose N is below its load-input count has the limit
  `load_subset: {strategy: first_n, limit: N, reason: license_cap}`. A row whose N equals its
  load input is **full** and gets no block. A row whose N is 0 is **not loaded**.
- **`sqlite_volume_prompt` with `choice: "subset"`**: the first-N figure Phase B Step 7's
  start-smaller suggestion writes is a limit **per source**, never a total split across the
  sources. Each remaining source whose load input exceeds it gets that same limit, with
  `strategy: first_n` and `reason: sqlite_volume`. **With a license cap as well**, a row's limit
  is the smaller of the two, and its `reason` names the limit that bound it.
- **No `license_cap_prompt` marker, or one recorded under a different `license_record_limit`
  than the current measured one** (which does not match, as the definition says): when the
  remaining sources' load inputs together exceed the remaining cap, put Phase B Step 7's
  license-cap question **once, for all the remaining sources together** (INV-006). Its pinned
  wording and its three options are Phase B's; point at them and do not copy them (INV-300).
  Record the marker as the definition says, then fill the rows by the answer, as above. On
  option 1, select across the remaining sources together by Module 4's
  [sampling rule](../module-04-data-collection/SKILL.md#overlap-preserving-sampling), and write
  one subset file under `data/subsets/` and one `load_subset:` block per source, as Phase B's
  option 1 does. On option 2, follow Phase B's apply route and its re-measure; every row is then
  **full**, with no block. When the remaining loads fit under the cap, ask nothing.
- ⛔ **A remaining cap that cannot be measured is indeterminate, never estimated (INV-244).** The
  capped rows get no limit. Say the figure is currently unavailable, and start none of those loads
  on a remembered figure or a sum of the registry's counts (INV-324).

**(INV-320) Then the orchestrator loads each source from its `load_subset:` block.** When a source's load
starts, read that source's block from `config/data_sources.yaml` and load exactly the input it
names: for `overlap_preserving`, the subset file at the block's `file_path`; for `first_n`, the
first `limit` records of the registry `file_path`, stopping there on purpose, not at the license
error. A source with no block loads its whole registry `file_path`. That input is the source's
load input, which its stage-1 reconciliation below compares against. A load that stops short of
that input, including one the license error stops, is a stage-1 mismatch.

Must handle: ordered loading with dependency enforcement, parallel execution if selected,
loading each source from its `load_subset:` block, per-source progress/error tracking with error
isolation, statistics aggregation, and a completion summary.

⛔ **(INV-243) The loading scaffold's counters are process-global, so per-source tracking is not free — you
have to build it.** The loader `sdk_guide(topic='load')` returns is written as a standalone
`main()`, and its counters are process-wide state: in Java, `LoadViaFutures.java` declares
`private static int errorCount / successCount / retryCount` (and a `static` retry file besides);
the equivalent in other bindings is module-level or global state. That is correct for a program
that runs once and exits, and wrong the moment the orchestrator calls it once per source in the
same process — which is exactly what "the Module 6 loading program works as a template" (step 16)
invites. The counts then **accumulate**: each source reports every record loaded so far.
(`sdk_guide(topic='load', language='java', record_count=1000)`, server 1.32.9, 2026-08-14.)

⚠️ **This failure looks like data, not like a bug.** Observed on three sources of 10 / 10 / 8
records, the summary read 10, then 20, then 28 — plausible, monotonic, and summing to the correct
total, with the load itself entirely correct. A bootcamper reads it as "Summit Billing has 28
records". The same arithmetic conceals a real per-source failure: a source that loaded **0 of 8**
still shows a rising success count inherited from its predecessors. This is the silent-wrong-value
class `ground-rules.md` → "Defensive parsing" covers (INV-115), except that a wrong number is
worse than a blank, because nothing about it invites a second look.

Resolve it one of two ways, whichever suits the bootcamper's language (INV-002):

- **Scope the counters per source** — make them state the orchestrator owns, reset at each
  source's boundary, so the loader reports into a fresh tally each time; or
- **Run each source's load in its own process**, so the process-global state starts clean by
  construction. This also isolates a crash in one source's load, which the error-isolation
  requirement above already asks for.

⛔ **Reconcile the per-source figures before showing them.** (INV-243) Each source's reported count
MUST match that source's load input — the records the loader was given, which is the input its
`load_subset:` block names when it has one — reconciled by the same two
stages as `phaseB-load-first-source.md` Step 7, the canonical statement; do not restate it here
(INV-300) — and the per-source counts MUST sum to the aggregate. Report the comparison, not just the
totals; if they disagree — a stage-1 mismatch, or counts that do not sum — say so and stop rather
than printing a number that cannot be traced to an input file (INV-245) — a figure the run has
itself disproved must not appear as a result. A summary that cannot be reconciled against the
inputs is not a summary — and the accumulating-counter defect above passes every check that looks
only at the total.

**Production orchestration patterns to include:**

- **Retry with exponential backoff:** when a source fails to load, retry with increasing delays
  (1s, 2s, 4s, 8s) up to a configurable maximum. Log each retry attempt.
  The backoff loop is ordinary code, but *which* exceptions are retryable comes from
  `sdk_guide(topic='error_handling', language='<chosen_language>')`.
- **Partial success handling:** if some sources succeed and others fail, mark successful sources
  as loaded and report failed sources with error details. Do not roll back successful loads when
  one source fails.
- **Error isolation:** errors in one source's loading must not affect other sources. Each source
  loads in its own error boundary.
- **Orchestrator health monitoring:** track overall health, elapsed time, sources completed vs.
  remaining, error rate across all sources. Log periodic health summaries.

**Checkpoint:** write step 17.

## 18. Test orchestrator with sample data

Test the orchestrator with 10–100 records per source. Verify: sources load without errors,
dependencies respected, progress tracking works, error handling triggers correctly. Report the
sample-data test results and let the bootcamper know the orchestrator is ready for the full
dataset.

A source whose Step 17 budget-table row is **not loaded** gets no test load either: its test
records would count against a remaining cap that has nothing left for it.

**Checkpoint:** write step 18.

## 19. Run full orchestration

Run on the dataset the recorded load decision names — the complete dataset unless a subset was
chosen — and tell the bootcamper which one is being loaded. When it is a subset, say so and that
the full dataset can be loaded afterwards. Monitor per-source progress, error rates, overall
completion, and elapsed/estimated time. If slow, suggest reducing parallelism.

The SQLite volume question was settled before the first load, so add nothing about it here
(INV-006). Each source loads what its own `load_subset:` block records, the only subset record
(INV-325), as [the subset record](phaseB-load-first-source.md#load-subset-record) in Phase B
step 7 (`phaseB-load-first-source.md`) defines it, rather than restating it (INV-300). No block
recorded means none was needed: the source loads its full load input, the complete dataset unless
Module 4 sampled it, with no SQLite remark (INV-244). For a sampled source, that input is its
sample file, and its reconciliation cites the `sample:` block (INV-326), never a subset.

**Before the run starts, re-read the markers and re-measure the remaining cap.** Re-read
`license_cap_prompt` and `sqlite_volume_prompt` in `config/bootcamp_preferences.yaml`, and
re-measure the remaining cap as [the subset record](phaseB-load-first-source.md#load-subset-record)
defines it. Step 18's test load ran after Step 17's table was computed, and its records count
against the cap, as Step 5's do. Recompute Step 17's budget table by its own rules on the new
figure, and show any row that changed, with both figures. Under `overlap_preserving` no new budget
is computed: if the re-measured cap is below the remaining rows' recorded `record_count`s together,
say so with both figures rather than start a load that can only hit the license error. The table
is then fixed for the run.

**(INV-320) Every remaining source's `load_subset:` block is written before the run starts, in Step 14's
load order, for every loading strategy, and the loader reads it** (Step 17). Write each row's
block from the fixed table into the source's entry in `config/data_sources.yaml`, as the
definition says. A row taken from Phase B's option-1 blocks already has its block. A **full** row
writes none. No block is written once any load has started, so every load reads a limit fixed
before the run. Under each loading strategy Step 15 offers:

- **Sequential:** write every row's `load_subset:` block first, in load order, then start the
  loads one after another; each load reads its own source's block.
- **Parallel:** write every row's `load_subset:` block first, then launch the loads together;
  each load reads its own source's block.
- **Hybrid:** write every row's `load_subset:` block first, then launch the sequential chains and
  the parallel group; each load reads its own source's block.

**(INV-320) A not-loaded row starts no load.** A source whose limit is 0, or whose Phase B block records
`record_count: 0`, is skipped: there is nothing to load, or its load could only hit the license
error. Leave its `load_status` unchanged, never `failed`, and name it in the completion summary as
not loaded because license capacity ran out.

**Checkpoint:** write step 19.

## 20. Coordinated redo queue processing

Drain the redo queue, critical after multi-source loading for cross-source match refinement.
Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` and
override paths to `database/G2C.db`.

⛔ **Same batch-drain requirement as Phase B, step 9** (INV-151, INV-300) — read it there rather than
re-deriving it.
In short: the MCP redo templates target streaming ingest and the observed one never terminates on an
empty queue, so check the returned snippet and, if it loops, replace the sleep-and-continue with a
break. The loop sentinel is the **fetch returning no record**, never a redo-count method (full table
scan per call, and processing redo generates more redo). Report the count processed and that the
queue reached empty.

**Production redo patterns:**

- Process redos after all sources are loaded (not between sources) to minimize redundant
  re-evaluations
- Monitor redo queue depth during processing, a growing queue may indicate data-quality issues —
  monitoring depth is not the same as using it as the loop condition, which the batch drain forbids
- Log redo processing statistics: total redos processed, duration, entities affected

Tell the bootcamper: "Processing the redo queue now. This refines cross-source entity resolution.
Without it, some matches between your sources would be incomplete."

**Checkpoint:** write step 20.

⛔ (INV-225) **Steps 17–20 ask nothing unless the license-cap question is due; when it is not,
this turn does not end here** — the orchestration summary and its record counts conclude something
and read like an ending, which is precisely the trap
(`ground-rules.md` → "A results presentation is not a turn ending", INV-225). Continue into Phase D in the
same turn, up to its first 👉. The one question these steps can put is Step 17's license-cap
question, and only when the budget table needs it and no marker records it — at Step 19 instead, if
Step 18's test load is what tips the remaining sources over the cap. That turn ends on it; the next
continues from the table.

Proceed to Phase D (`phaseD-validation.md`).
