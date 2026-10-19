# Module 6, Phase B: Load First Source (steps 5–11)

Continues from Phase A. Follow the ground rules; `🛑`/`⛔` are internal control directives.
Loading and redo code comes from the MCP tools (`generate_scaffold` / `sdk_guide`), never
hand-written. Back up `database/G2C.db` before loading. The `DATA_SOURCE` codes in this data
were registered in Phase A (step 4a), so the load runs against a config that already knows them
(the loader's generic `SENZ2207` handling remains a fallback).

**Choosing the first source (2 or more sources only).** Phase B loads one source, and with 2 or
more sources with `mapping_status: complete` in `config/data_sources.yaml` (the count Phase C's
conditional gate uses) that choice decides the entity baseline the rest load against. Choose it
by the ordering heuristics in Phase C step 14 (`phaseC-multi-source.md`, "Determine load order"),
applied in that step's priority order (INV-327). Step 14 owns the list; cite it rather than restating it
here, so the two cannot drift (INV-300). If a heuristic's input is missing for a source (for
example no `quality_score` on a `fast_pathed` source that skipped Module 5's assessment), skip
that heuristic and apply the next one. When Module 5's optional test load ran
(`test_load_status: complete`), its quality results feed the same heuristics, as Phase A's
"Phase 3 results integration" already says.

Before step 5, tell the bootcamper in one line which source loads first and the heuristic that
actually decided it, for example *"Loading `<source>` first: `<the heuristic that decided it>`."*
⛔ **This is a statement, not a 👉 question (INV-225).** It asks nothing and does not end the
turn; continue to step 5. The order of the remaining sources is still reviewed at step 14.

Record the choice and its reason in `docs/loading_strategy.md` as the **first-source choice**
(the source and the deciding heuristic), in the file Phase C step 13 and Phase D also write. Note
it in step 5's checkpoint too. Step 14 reads it from the file, so a resumed session does not lose
it. With a single source there is no choice: say nothing and record nothing.

<a id="receiving-a-quality-iteration"></a>

## Receiving a `quality_iteration` (from Query, Visualize and Discover)

⛔ **(INV-284) Check for it before anything else in this module, Phase A included.** When
`config/bootcamp_progress.json` carries a `quality_iteration` whose `stage` is `reload`, the
Bootcamper chose the return at Module 7 step 3b and Module 5 has remapped the named sources. This is
not a run of this module: show no start banner, journey map or overview, write no Module 6
checkpoint (leave `current_module` and `current_step` as Module 7 set them, so its progress is not
overwritten), and reload only the sources the key names. Which stages run and where Module 7 resumes
are stated once, in `../module-07-query-visualize-discover/phase1-query-visualize.md` step 3b → "The
quality-iteration route" (INV-300); this block says only how the reload is done.

For each source in `sources` not yet listed in `completed`, in order:

1. **Phase A runs only when the source's input path changed.** When the remap left the registry
   `file_path` the loading program reads unchanged, reuse the existing program in `src/load/` as it
   is. When it changed, run Phase A for this source only before the reload.
2. **Compare the RECORD_ID sets before the reload.** The previous set is the one Module 5's
   [receiving branch](../module-05-data-quality-mapping/phase2-data-mapping.md#receiving-a-quality-iteration)
   recorded in `{source_name}_loaded_record_ids.txt` before the remap. The new set is the
   RECORD_IDs the reload will load: the remapped file, narrowed by the source's `load_subset:` block
   when one is recorded ([the subset record](#load-subset-record)). An `overlap_preserving` subset
   file was cut from the previous mapping, so rewrite it from the remapped file with the same
   RECORD_IDs, and re-measure its `record_count`, before comparing.
3. **Delete the records whose RECORD_IDs no longer appear,** using the record-delete call the Senzing
   MCP server documents for the chosen language, never one from memory (INV-080):
   `sdk_guide(topic='delete', language='<chosen_language>')` returns the delete loop, and
   `get_sdk_reference(topic='parameters', filter='delete_record', language='<chosen_language>')`
   returns that binding's signature, whose name and arguments differ by binding. Report how many
   were deleted. When the sets are equal, nothing is deleted. The remaining records need no delete:
   a record whose data source code and RECORD_ID match a loaded record replaces it
   (`search_docs(query='Data Source Records DSRs Explained same DATA_SOURCE RECORD_ID replaces')` →
   "Data Source Records (DSRs) Explained" → "Uniquely Identifying Records in Senzing", its second
   hit: read past the first, the same document's "Important Nuances > Expanding Data Sources";
   server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02).
4. **Reload the source with the existing loading program:** `phaseB-load-first-source.md` Step 7
   (below) on a single-source run, or `phaseC-multi-source.md` Step 19 for this source alone on a
   multi-source run. Step 7's license check, its two-stage reconciliation (INV-243) and its `load_status` update in
   `config/data_sources.yaml` apply as written. Back up `database/G2C.db` first, as for any load.
5. **Add the source to `completed`** in one quiet write, and delete its
   `{source_name}_loaded_record_ids.txt`.

When every named source is reloaded, **process redo once** by Step 9 below on a
single-source run, or `phaseC-multi-source.md` Step 20 on a multi-source run. Then return to Module 7
step 3b's resume, which clears the key.

⛔ **(INV-327) This deliberate replacement by record key is not the first-source reload INV-327
forbids.** That rule forbids repairing a broken load-order dependency by reloading the first source,
which double-loads its records. Here each record replaces its own earlier version by key, and the
records whose RECORD_IDs left the source are deleted first, so nothing is loaded twice.

**Phase D and Module 6's completion step do not run.** ⛔ **(INV-284) No validation, no
iterate-vs-proceed gate and no Module Completion:** no second Module 6 recap section, no progress
update, no transition question, and `data_processing` is not added to `modules_completed` again.
Module 7 step 3b is where the re-evaluation happens. The first-source choice above, and Phase B's
other steps, do not run either.

## 5. Test with sample data (if Phase 3 was skipped)

If the bootcamper did not complete Phase 3 in Module 5, run the loading program on a small
subset first:

- Start with 10–100 records
- Verify the program connects to the engine
- Check that records are being added successfully
- Observe any errors or warnings

**On success, set `test_load_status: complete` for that source in `config/data_sources.yaml`.**
Phase A's pre-load check reads this field to decide whether a test load is owed, so a run that
is not recorded is a run that Phase A will ask for again on a resumed session.

⛔ **This is the earliest point the test load can run, which is why it lives here and not in
Phase A's pre-load checks (INV-089).** It needs two things Phase A produces: the loading program itself,
built at step 3 from the volume tier captured at step 1, and the registered `DATA_SOURCE` codes
from step 4a — without which the load fails with `SENZ2207` (*"Data source code [{0}] does not
exist"*, `explain_error_code('SENZ2207')`, server 1.32.9, 2026-08-14), the exact error step 4a
exists to prevent. Do not move it earlier, and do not add a second copy upstream.

If Phase 3 was completed, skip this step, the test load already verified basic loading. Proceed
directly to production loading.

**Checkpoint:** write step 5 (with 2 or more sources, note the first-source choice).

## 6. Observe entity resolution in real time

As records load, Senzing resolves entities automatically:

- Watch the console output for resolution activity
- Note how entities are being formed
- See how new records match or create entities
- This gives immediate feedback on data quality and matching behavior

⛔ **(INV-297) The engine writes its own diagnostics to that console, and they are NOT per-record failures —
say which is which before the Bootcamper reads one.** This step and step 7 both point them at the
output, so they will see engine-level lines prefixed `ERR:` (they carry an `[szstatic:…]` thread
tag) sitting beside a loader summary that says **0 failed**, with nothing telling them the two are
different things. **The loader's own `failed` count and its error log are the authority on record
failures**; a line the engine wrote about its internal state is not one, and neither confirms nor
denies the other.

What to say when one appears: name it as engine output rather than a failed record, and point at
the reconciliation that settles it — records attempted equals records loaded, the redo queue
reached empty, and the error log is absent or empty. If those three hold, nothing was lost.

⚠️ **Do not explain what a specific engine message means unless a route serves it.**
`search_docs(query='resolved entity is out of sync expected got concurrent loading SQLite lock')`
returns **no document naming that message** — owner-checked: `search_docs` is the corpus route for a
documented engine message, and the nearest material it serves is the *"Enabling the Per-Entity
Feature Store & Advisory Locking in Senzing 4.4.0"* article, which states that on SQLite the engine
*"falls back to `LEASE` automatically"* with no advisory locks; so the message is uncovered by the
corpus rather than missed by the query (absence negative) — server **1.37.19**, docs index
2026-10-02 18:46 UTC, 2026-10-02. An
`out of sync` line seen during a concurrent SQLite load is therefore reported as **an environment
observation**, with the SDK version and date, or not characterized at all (INV-080/INV-149) — never
as a Senzing fact and never as reassurance the plugin cannot source.
<!-- MCP-NEGATIVE: search_docs(query='resolved entity is out of sync expected got concurrent loading SQLite lock') — no indexed document names the "Resolved entity … is out of sync" engine message — owner: search_docs IS the corpus route for a documented engine message and the nearest material it serves is the 4.4.0 advisory-locking article stating SQLite falls back to LEASE with no advisory locks, so the message is uncovered by the corpus rather than missed by the query (absence negative) — server 1.36.0, 2026-09-02 -->

**Checkpoint:** write step 6.

## 7. Load the full dataset

Run the program on the complete data source with production-quality monitoring:

- Monitor progress and throughput performance
- Watch for error-rate trends (increasing errors may indicate data issues)
- Note loading statistics (time, throughput, error rate)
- If errors exceed 5%, pause and investigate before continuing

**License capacity before loading.** Before warning that the load will stop at the built-in
evaluation limit (a licensing error at the cap), read `license_record_limit` from
`config/bootcamp_progress.json` (the Module 4 license gate at Step 8a persists it after a custom
license is configured) and drive the decision from that effective limit, never a remembered or
hardcoded figure:

⛔ **(INV-295) Read `license_record_limit_measured_at` alongside it, and treat a reading marked provisional —
or carrying no marker — as the absent case below.** SDK setup's Step 5a takes its reading before
Step 8 writes `CONFIGPATH`, so it cannot see a license installed at the system config path. A
provisional figure is a genuine measurement of an incomplete view, which is the one shape the
absent-versus-present split above cannot see on its own.

**"The dataset size" in these branches is the whole load, not this source.** It is the loadable
total across **every** mapped source, the record count of their files in `data/senzing-ready/`
together, which is the same whole-load total Phase A's SQLite volume pre-load check reads
(`phaseA-build-loading.md`, item 1). It is not the first source alone: the license cap covers
every record Phases B and C load into the same repository.

- **`0` (no cap), or ≥ the dataset size**, the active license permits the full load: omit the
  evaluation-capacity warning and proceed.
- **Positive and below the dataset size**, the dataset genuinely exceeds the cap: the single
  License Key gate (Module 4, Step 8a) already offered to expand capacity — restate that a larger
  license lets the full load proceed, as a choice, not a wall; do not force downsizing.

  ⛔ **Read `license_key_requested` from `config/bootcamp_progress.json` first, and say the license may
  already be here.** When it records a sent request, state plainly that the license is delivered **by
  email**, that it may already have arrived, and that it can be applied now — including in a later
  session. ⚠️ **Only when a request is outstanding.** `license: evaluation` is written both after a
  request was sent *and* when the Bootcamper **declined** to send one, so keying this reminder to it
  would tell someone who declined to go hunting for a license they never asked for. Absent
  `license_key_requested` → no reminder; say nothing about email.

  **The apply procedure already exists — point at it, do not restate it (INV-300).** Module 4 Step 8a
  **sub-step 5** decodes a Base64 key or copies a `.lic` to `licenses/g2.lic`, adds `LICENSEFILE` to
  the engine-config PIPELINE section, and records `license: custom`. ⛔ **Do not write a second copy
  of it here, and do not substitute a different mechanism.** A platform-specific procedure duplicated
  is a procedure that drifts, and the MCP server describes a *different* route
  (`SENZING_LICENSE_FILE`, or a license file in `etc/`) which is real but is **not** the one wired
  into this bootcamp's file layout — using it here would leave the engine config pointing at nothing.

  **Then re-measure and re-enter these branches.** After applying, re-read the license by Module 4
  Step 8a sub-step 7, which calls `SzProduct.get_license()`, refreshes `config/license.json` and
  lets you parse `recordLimit`; follow that step rather than restating it (INV-300). Then confirm it
  actually moved, and route again on the new value — a license reporting `0` lands on the first
  branch and the whole cap discussion dissolves. ⚠️ Do **not** state the evaluation license's size
  or duration from this file: those figures change between releases, so take them from a runtime
  lookup at the moment of use or say they are unavailable.

  End the turn on this single pinned question (INV-056), which replaces the improvised one — it is
  **one** 👉 (INV-251) and it is **not** a second License Key gate (INV-093: that decision was asked
  once, in Module 4, and is settled — this offers a *procedure* and a *status readout*, not the
  question again):

  > 👉 **Your dataset is larger than this license allows. How would you like to proceed? Reply with a number:**
  >
  > 1. **Load an overlap-preserving subset now** — keeps cross-source matches visible at this capacity.
  > 2. **Apply a license I have** — I'll walk you through it, then load everything.
  > 3. **Load the first records as they come** — simplest, but cross-source overlap may be lost.

  *(Internal: end the turn on this question and wait.)* On **2**, follow Step 8a sub-step 5, then
  re-measure and re-enter these branches. ⛔ **Option 2 stays on the list even when
  `license_key_requested` is absent** — a Bootcamper may hold a license the bootcamp never asked about,
  and it is the option this branch previously omitted entirely; what the `license_key_requested`
  marker gates is only the *"check your email, it may have arrived"* line above.

  Options **1** and **3** load a subset. For either, measure the **remaining cap** first, as
  [the subset record](#load-subset-record) below defines it; when it is indeterminate or not
  positive, stop where that definition says. Otherwise:

  - On **1**, write `license_cap_prompt` and each selected source's `load_subset:` block as
    [the subset record](#load-subset-record) defines (INV-325), with `choice: overlap_preserving`. Select
    **once, across every mapped source** in `data/senzing-ready/`, within the remaining cap: the
    same whole-load scope as the dataset size above. The selection method is Module 4's
    [sampling rule](../module-04-data-collection/SKILL.md#overlap-preserving-sampling); follow it
    and do not restate it here (INV-300). For each selected source, write its subset file under
    `data/subsets/` and its block with `strategy: overlap_preserving`, `file_path`, the measured
    `record_count`, and `reason: license_cap`. Phase B loads the first source's subset; Phase C
    loads the rest. With a **single source** there is no cross-source overlap to preserve, so the
    sampling rule's first-N case applies: write `strategy: first_n` with `limit` = the remaining
    cap and `reason: license_cap`, and say which case applies.
  - On **3**, write `license_cap_prompt` and the first source's `load_subset:` block as
    [the subset record](#load-subset-record) defines (INV-325), with `choice: first_n` and
    `load_subset: {strategy: first_n, limit: N, reason: license_cap}`, where N = the remaining
    cap. Write the block **before** the load, and have the loader load exactly the first N
    records, stopping there on purpose, not at the license error. Tell the bootcamper that later
    sources get only what is left of the cap, possibly nothing: the cost this option's own warning
    names ("cross-source overlap may be lost").
- **Absent or null** — ⛔ **"never measured", not "no custom license": measure before warning.** (INV-244) This
  is the same branch, and the same trap, as Phase A's — **every step that writes
  `license_record_limit` writes only a MEASURED value**, so its absence says nothing about the
  installed license: SDK setup's Step 5a measures as soon as the SDK is verified and deliberately
  writes nothing when it cannot, and Module 4's **volume-gated** Step 8a fires only when the
  collected volume approaches the limit.
  ⚠️ **Do not reason from a count of writers**; that number has been stated wrongly twice. Measure
  it by Module 4 Step 8a sub-step 7, which calls `SzProduct.get_license()` and parses
  `recordLimit`, rather than restating it (INV-300); persist it as Phase A's absent branch
  instructs, and re-enter these three branches with the measured value — a license reporting
  `recordLimit: 0` then lands on the first branch and the warning is correctly omitted. If Phase A
  already measured and persisted it, this branch is not reached.
  - **Only if the measurement fails** does the evaluation-capacity warning apply. Say it is an
    assumption, and confirm the current capacity figure and the exact over-limit error code and
    behavior from the Senzing MCP server at request time. If no figure is returned, say it is
    currently unavailable rather than restating a remembered one.

<a id="load-subset-record"></a>

**The subset record.** This is the one definition of what a subset choice in this step records.
License-cap options 1 and 3 above and the SQLite first-1,000 choice below each write it as this
definition says, adding only their own values, and the two-stage reconciliation below cites it
(INV-300).

- **`load_subset:`**, a block in the source's own entry in `config/data_sources.yaml`, written
  **before** that source's load, whenever the source loads fewer records than its load input:
  `load_subset: {strategy, limit, file_path, record_count, reason}`.
  - `strategy`: `first_n` or `overlap_preserving`.
  - `limit` (for `first_n`): N. The loader loads exactly the first N records of the registry
    `file_path` and stops there on purpose.
  - `file_path` and `record_count` (for `overlap_preserving`): the subset file under
    `data/subsets/`, and the record count **measured from the written file**, never the target
    that was asked for. A source the selection took nothing from still gets the block, with a
    measured `record_count: 0`, so nothing loads for it and its reconciliation cites a record
    rather than finding none.
  - `reason`: `license_cap` or `sqlite_volume`.

  Like Module 4's `sample:` block, writing it never touches the source's top-level
  `record_count` or `expected_record_count` (INV-243), and it leaves `sample:` as it is.
- **Subset files live under `data/subsets/`, never in `data/senzing-ready/`.** Phase A's loadable
  total counts every file there, so a subset file inside it would count its source twice. The
  directory is created when option 1 first writes to it.
- **`license_cap_prompt`**, the whole-load marker in `config/bootcamp_preferences.yaml`, modeled on
  `sqlite_volume_prompt`: `{decided: true, choice, license_record_limit}`. `choice` is
  `overlap_preserving` (option 1) or `first_n` (option 3), and `license_record_limit` is the limit
  the choice was made under. It records the license-cap question as asked once (INV-006), so
  Phase C applies the choice without asking again, even when the first source fit under the cap.
  A marker recorded under a different `license_record_limit` does not match.
- **`sqlite_volume_prompt` with `choice: "subset"`**, the SQLite first-1,000 choice's asked-once
  marker: `{decided: true, choice: "subset", loadable}`, beside Phase A's `proceed` and `migrate`.
- **(INV-325) Neither marker records N or a subset file.** They record that the question was answered.
  What each source loads is its `load_subset:` block, and that block is the only subset record
  the reconciliation cites.
- **The remaining cap** is `license_record_limit` minus the number of records already in the
  repository.
  - ⛔ **(INV-324) That count is measured through the SDK at this step, never summed from the registry.**
    Route the code through the Senzing MCP server, exactly as Module 5 Step 24a counts
    `record_count` (`module-05-data-quality-mapping/phase3-test-load.md`), and never count with
    direct SQL against `database/G2C.db`. Records a test load left in the repository count
    against the cap whatever `config/data_sources.yaml` says.
  - **The count cannot be measured:** the remaining cap is indeterminate. Offer no subset size,
    say the figure is currently unavailable, and never substitute a remembered or estimated one,
    the same rule as an unmeasured `license_record_limit` (INV-244).
  - **Zero or less:** the repository already holds `license_record_limit` records. Load nothing
    and say so; do not start a load that can only hit the license error.

**Data source registry.** On success, update `load_status` to `loaded` in
`config/data_sources.yaml`. On failure, set `load_status` to `failed` and add an `issues` entry
describing the error. Update `updated_at` either way. ⛔ **Do not write the loaded count over
`record_count` — reconcile first, per the rule below, which decides both what `load_status` becomes
and where the loaded figure is recorded.**

<a id="two-stage-load-reconciliation"></a>

⛔ (INV-243) **Reconcile the loaded count in two stages *before* writing it — the value you are
about to overwrite is the baseline.** This is the canonical statement of the two-stage load
reconciliation and its outcomes; Phase C Steps 12 and 17 and Phase D Step 27 point here and add
only what their own site needs (INV-300). `record_count` already holds the count Data collection
**measured in the collected file**, alongside `expected_record_count` (what the provider stated),
recorded there precisely "so the two can be compared here and re-checked later". But the collected
file is often **not** what the loader read: Data collection directs a working sample whenever the
scenario is sized below the collected volume (Module 4 → "Sampling rule"), and Module 5 maps it and
repoints `file_path` at its own output. So there are two comparisons, made in order, and the outcome
is recorded under `validation_checks` as `load_count_matches_source` — the same auditable idiom Data
collection already uses for `record_count_matches_expected`, so the comparison lives in the registry
rather than only in the turn that ran it.

1. **Stage 1 — the loaded count against the load input.** Compare the loader's success count
   against the **load input** first: the records the loader was actually given, counted from the
   file it read — the registry `file_path` (for a `fast_pathed: true` source, the raw or sample file
   it loaded) — or, when a **recorded subset limit** applies, the subset the source's
   `load_subset:` block records ([the subset record](#load-subset-record) above): the first `limit`
   records of that file, or the subset file at its `file_path`. This is the only comparison that
   can verify the load itself, so **stage 1 is the only stage that can record `failed`**. It has no
   explained branch: the loader's error count and error log explain a shortfall, but they do not
   excuse it, and a license error before the subset is loaded is still a mismatch.
2. **Stage 2 — the load input against the collected `record_count`, through the recorded chain.**
   Reached only when stage 1 is equal. Every step between the collected file and the load input is
   cited from a record, in order — collected → sample → mapped → subset:
   - **the `sample:` block** Module 4 wrote into this source's registry entry (collected → sample),
     whose `record_count` was measured from the written sample file, with its `strategy` and
     `reason`. Module 4 writes it from Step 6's sample files or from Step 8b's `sample` load
     decision, so either one is cited here, once, as the sample step;
   - **a mapping disposition** (→ mapped file), cited as the source's own mapping specification, or
     the recorded disposition in `config/data_sources.yaml`;
   - **the `load_subset:` block** this step wrote into the source's registry entry (mapped →
     subset), with its `strategy`, its `limit` or measured `record_count`, and its `reason`: the
     only subset record, as [the subset record](#load-subset-record) above defines it.

⛔ **Four outcomes across two stages, not two. Do not collapse them.** INV-245 forbids presenting a
value that **failed its own verification check**, and stage 1 is that check. A stage-2 delta the
chain predicts has not failed verification — it is verified and reconciled, which is a different
state from unverified. An uncited stage-2 gap has not failed either — every record the loader was
given loaded — but its relation to the collected file is **unverified**, so it is loaded and shown
as unverified, never as a plain number and never as `failed`. Route on which of these it is:

| Stage | Outcome | `load_status` | What else to record |
|---|---|---|---|
| 1 | **Loaded ≠ load input** | `failed` | `load_count_matches_source` not written; both figures in the `issues` entry |
| 2 | **Equal** — load input = `record_count` | `loaded` | `validation_checks.load_count_matches_source: pass` |
| 2 | **Explained delta** — every chain step cited | `loaded` | every figure; `validation_checks.load_count_matches_source: expected_delta`; a `load_reconciliation` note naming **each chain step and the record it cites** |
| 2 | **Unexplained delta** — any step uncited | `loaded` | `validation_checks.load_count_matches_source: unexplained_delta`; an `issues` entry with every figure |

⛔ **If either stage disagrees, write the discrepancy rather than the count** (INV-245): leave the
existing `record_count` in place, record the figures as the table says, and do not present the
loaded count as a bare result. Overwriting on a mismatch is the worst outcome available — it destroys
the input baseline and files a partial load as a complete one, after which nothing downstream can
tell the difference. This is the point where the figure enters durable state: `phaseC` step 12 reads
it straight back out and presents it to the bootcamper, and Phase D writes it into
`docs/loading_strategy.md`, so a number that was never checked here is never checked at all — it
simply acquires the authority of having been written down. Reporting the aggregate alone does not
discharge this: the failure mode this exists for produces figures that are plausible and sum
correctly.

⛔ **The explained branch is reachable ONLY with a citation, never with an assertion.** The note must
name, for every step, the record that predicts it: the `sample:` block, the `load_subset:` block,
or the mapping artifact — the source's own mapping specification, or the recorded disposition in
`config/data_sources.yaml`. *"The mapping probably explains it"* and *"it was probably sampled"* are
precisely the failure INV-245 exists to prevent, and without the citation requirement this branch
becomes a universal escape hatch wearing the rule as a disguise. No citation → `unexplained_delta`.

- **No `sample:` block** (INV-326) — a registry written before Module 4 recorded samples: a gap only a sample
  could explain is **unexplained**. Nothing is inferred from a file's name or location; a path under
  `data/samples/` is not a citation.
- **No `load_subset:` block** — a registry written before this step recorded subsets, or a subset
  recorded nowhere: a gap only a subset could explain is **unexplained**. A path under
  `data/subsets/` is not a citation either.
- **A substitute dataset** (Module 4 Step 6's smaller substitute) is a new collection, not a sample:
  it carries its own measured `record_count` and no `sample:` block, so it adds no chain step.
- **A source that skips mapping** (`fast_pathed: true`): the chain is the sample alone, or empty.

⚠️ **The sampled case is the common one, not the edge.** A source collected at **63,863** records was
sampled overlap-preserving to **7,386** and loaded **7,386** of 7,386 with zero errors. Stage 1 is
equal; stage 2 cites the `sample:` block (`record_count: 7386`, its `strategy` and `reason`) for the
whole gap → `expected_delta`. Compared against `record_count` alone, that clean load had no compliant
outcome but `failed`.

⚠️ **The mapping branch is not hypothetical either: the bootcamp teaches the mapping that reaches it.**
`embedded_master` is a disposition Module 5 teaches under its own heading, defined as *"the value
becomes its own Senzing record, and the parent points at it"* — a disposition whose definition is
"emit an additional record" **necessarily** makes the loaded count exceed the input count Data
collection measured. One source loaded **3,727** records against a measured `record_count` of
**3,488**: 239 distinct lenders emitted as embedded masters, exactly as that source's mapping
specification prescribes, every input record loaded, zero errors. Stage 1 compares the 3,727 loaded
against the 3,727 records in the mapped file and is equal; stage 2 cites the mapping specification
for the 239 → `expected_delta`. Under a two-way rule the only compliant action was to file a
completely successful load as `failed`, and to write that into the Bootcamper's own loading
strategy. **A sampled source whose mapping also multiplies records cites both steps, in order:
collected → sample → mapped.**

**The baseline stays immutable in every branch** (INV-243) — `record_count` and
`expected_record_count` are never overwritten and the loaded figure is recorded beside it. That half
of the rule is correct and is not what changed.

**⚠️ SQLite performance note — only when the volume question is still open.** On SQLite with
single-threaded loading, entity resolution gets progressively slower as the database grows.

⛔ **Check first whether this was already decided, and say nothing if it was.** Read the
`sqlite_volume_prompt` marker in `config/bootcamp_preferences.yaml` (Phase A's pre-load check) and
the `sqlite_load_time_prompt` marker Module 4 Step 8b writes there, which covers this load only
as item 2 of Phase A's
[pre-load check](phaseA-build-loading.md#sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate)
matches it (INV-300). If either records a choice for this same load — `proceed`, `subset`,
`sample`, or a database switch — **honor it silently and load what it says**. For
`subset`, take N from the source's `load_subset:` block (its `limit`), because
`sqlite_volume_prompt` does not record N. Two gates already put
this to the bootcamper; re-opening it here would be a third ask on a settled question (INV-006) and
would push a dataset smaller than the one they chose, which is exactly what leaves Modules 6 and 7
under-demonstrating cross-source resolution (INV-150).

Only when the database is SQLite AND the loadable total exceeds the MCP-sourced threshold — the
same trigger as Phase A's pre-load check, item 3 — AND **no** decision is recorded may you suggest
starting smaller:
"Let's start with the first 1,000 records so we can see results quickly. Once we validate the
results here, we can load the full dataset, or switch to PostgreSQL for better performance with
larger volumes (a production follow-up; see the graduation migration checklist)." Record the
resulting choice in `sqlite_volume_prompt`, with `loadable`, so the question stays asked once.
On the first 1,000 records, write it as [the subset record](#load-subset-record) defines (INV-325), with
only this choice's values: `sqlite_volume_prompt` with `choice: "subset"`, and on the source
`load_subset: {strategy: first_n, limit: 1000, reason: sqlite_volume}`.
⛔ **An absent marker is "not asked", never "answered" (INV-244).** A load at or below the
threshold, or one whose total or threshold is indeterminate, never needed the question and leaves
no marker; say nothing here and write none.

**Checkpoint:** write step 7.

## 8. Save and document the loading program

- Save in `src/load/` with a clear name (e.g. `src/load/load_customer_db.[ext]`); all loading
  programs live in `src/load/`
- Document how to run it (command line, configuration)
- Note any prerequisites or dependencies
- Keep it for future reloads or updates

**Checkpoint:** write step 8.

## 9. Process redo records

After loading completes, drain the redo queue. Redo records are deferred re-evaluations that
refine the entity resolution graph, without processing them, results are incomplete.

Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` for the
redo processing pattern. The loading program (or a separate script) should sequentially process
all pending redos until the queue is empty. If the generated redo scaffold uses `/tmp/`,
`ExampleEnvironment`, or any path outside the working directory, override the database path to
`database/G2C.db`.

⛔ **The bootcamp needs a batch drain that terminates. Check the returned snippet before running
it.** The MCP redo templates target *streaming ingest*, where never stopping is the point: the
observed `sdk_guide(topic='redo')` answer prints "pausing for 30 seconds" on an empty queue and
loops forever. Run that unmodified after a batch load and the session simply hangs — no error, no
output, indistinguishable from slow work, which is the worst shape a failure can take here.

If the snippet loops on an empty queue, adapt it: keep its structure and concurrency, and replace
the sleep-and-continue with a break. The shape the batch step needs, stated language-agnostically
(INV-002):

1. Fetch the next redo record.
2. If none was returned, the queue is empty — exit the loop.
3. Otherwise process it, and repeat.

**The fetch's return value is the loop sentinel.** ⛔ Do **not** poll a redo-*count* method as the
loop condition: it is a full table scan per call, so the drain becomes O(n²) — and because
processing a redo record generates more redo records, the loop runs longer than the initial count
suggests (a backlog of 384 took 400 processed calls in the reported session). Confirm the method
names for the chosen binding from MCP (INV-080/INV-132), and confirm the anti-pattern itself via
`search_docs(query="redo", category="anti_patterns")` → *Senzing Anti-Patterns: Architecture and
Performance*, "Do Not Use count_redo_records() as a Loop Condition", rather than trusting this
note.

Report the terminal condition: how many redo records were processed, and that the queue reached
empty. A drain that finishes silently cannot be told from one still running.

Include a code comment explaining that in production, redos are typically handled by an
always-running redo processor that wakes, checks for pending redos, processes them, and sleeps
when the queue is empty — that is the **streaming** pattern, and it is deliberately *not* what this
batch step runs. Naming the difference is what stops the non-terminating template looking like the
correct answer.

Tell the bootcamper: "Processing the redo queue now. This refines entity resolution, without
it, some matches would be incomplete."

**Checkpoint:** write step 9.

## 10. Incremental loading strategy

Discuss incremental loading as a production concern distinct from the initial bulk load:

- **Full reload** (what we just did): load all records every time. Simple but slow for large
  datasets.
- **Incremental load** (production pattern): track which records are new or changed since the
  last load; load only deltas. Requires a change-detection mechanism (timestamps, sequence
  numbers, change data capture).
- **Upsert pattern:** use `add_record` with the same `RECORD_ID` to update existing records.
  Senzing re-evaluates entity resolution automatically.
- Help the bootcamper understand when each strategy applies and document the choice in
  `docs/loading_strategy.md`.

**Checkpoint:** write step 10.

## 11. Mark first data source as loaded

Once loading and redo processing are complete, mark this data source as loaded in
`config/data_sources.yaml`.

**Checkpoint:** write step 11.

**Next:** if the bootcamper has 2 or more data sources with `mapping_status: complete`, proceed
to Phase C (`phaseC-multi-source.md`). If only ONE data source, skip Phase C and go directly to
Phase D (`phaseD-validation.md`).
