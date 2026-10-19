# Module 5, Phase 3: Test Load and Validate (Optional) (steps 21–25)

Continues from Phase 2. Follow the ground rules; `🛑`/`⛔` are internal directives: do not
render them. Signal a stop by ending the turn on the single 👉 question and waiting.

> **This phase is optional.** Bootcampers who prefer to write custom loading programs can skip
> Phase 3 (step 18a's `skip`): the real load happens in Data processing, which always follows this
> module. Phase 3 uses `mapping_workflow` steps 5–8 to give immediate feedback on ER quality without
> leaving Data Quality, Mapping, and Transformation.

> **Entry from the Step 5 `detect_environment` menu:** Phase 3 is entered from the
> `detect_environment` menu handled in `phase2-data-mapping.md` at **step 18a** — after that
> source's mapper has been written, run, reviewed and documented (steps 12–18), so the
> transformation output step 22 samples below actually exists. When the bootcamper explicitly
> chooses **test_load** at that menu, follow the workflow below
> (`mapping_workflow` steps 5–8, Steps 21–25) unchanged. When sources remain unmapped, the
> Phase 2 guidance instead recommends **skip** and continues to the next source; at the last
> source, a step-16 answer that proceeds to loading settles it as **skip**. The real production
> load is still deferred to Data processing in every case. Phase 3 is a detour for **this source**
> inside Phase 2's per-source loop, so every way out of it returns to Phase 2: see
> [Leaving Phase 3](#leaving-phase-3).

**Before starting Phase 3:** The Senzing SDK must be installed and configured (SDK setup). If it
is not yet set up, inform the bootcamper: "Phase 3 requires the Senzing SDK (from SDK setup). You can
skip the test load for this source and carry on mapping (the real load happens in Data processing),
or complete SDK setup first and return here." If the bootcamper chooses to skip, leave by the
**skip exit** in [Leaving Phase 3](#leaving-phase-3): `test_load_status: skipped` for **this source
only**, then Phase 2 step 19.

## Workflow (per data source that completed Phase 2)

### 21. SDK environment detection

Call `mapping_workflow(action='advance')` to advance to step 5 (SDK environment detection). The
workflow checks whether the Senzing SDK is installed and a database is configured. If detection
fails, offer to skip this source's test load or return to Module 2. If the bootcamper skips, leave
by the **skip exit** in [Leaving Phase 3](#leaving-phase-3): `test_load_status: skipped` for **this
source only**, then Phase 2 step 19. (Pass the exact `mapping_workflow` state
from Phase 2 unchanged; checkpoint to `config/mapping_state_[datasource].json` after this step.)

**Checkpoint:** write step 21 to `config/bootcamp_progress.json`.

### 21a. Register the data source code (before the test load)

Before the step 22 test load, ensure the source's `DATA_SOURCE` code is registered in the Senzing
engine config (INV-089), so the load does not fail with `SENZ2207: Data source code [...] does not exist` —
the same register-before-load guarantee System Verification and Module 6 use. Collect the distinct
`DATA_SOURCE` value(s) in this source's Phase 2 transformation output. If `mapping_workflow` step 6
registers the code as part of loading, this is already satisfied; otherwise generate the
registration via `sdk_guide(topic='configure')` (in the `programming_language`), saving any
generated file under `src/` (e.g. `src/load/`) per INV-018 — it loads the current default config,
registers the code, and sets it as the new default, idempotently — and run it first. Never rely on Module 2's default config, which predates data collection.

⚠️ **If this phase's sandbox database was created fresh, seed its default configuration first.** The
registration snippet reads the current default config and builds from it, so against a
just-schema-created datastore it fails with `SENZ7221
EAS_ERR_NO_CONFIG_REGISTERED_FOR_DATA_ID` — a different failure from the `SENZ2207` above, and one
whose own `explain_error_code` guidance **does** now name the cause and the remedy — call it
(re-verified on MCP server 1.32.8, 2026-08-11: its first cause is *"No default config has EVER been
registered on this datastore"* and its first resolution step names `create_config_from_template()` →
`set_default_config(...)`, adding that `sdk_guide` `topic='configure'` "called WITHOUT `data_sources`
… returns the seeding snippet"). Seed by calling `sdk_guide(topic='configure', language=…)` **without
`data_sources`** — that call's **primary** `code` block is `init_default_config` — then call it again
**with** `data_sources` to register (see `../module-02-sdk-setup/SKILL.md` → Step 8a). Where `mapping_workflow` step 6 creates
and initializes the sandbox database itself, this is already handled — confirm rather than assume.

**Checkpoint:** write step 21a.

### 22. Test data loading

Advance through `mapping_workflow` step 6: load test data into a fresh SQLite database. This
loads a sample from the Phase 2 transformation output to verify the mapping produces valid
Senzing records.

**Checkpoint:** write step 22.

### 23. Validation report generation

Advance through `mapping_workflow` step 7: generate a validation report covering record counts,
feature coverage, and data quality metrics for the test load.

**Checkpoint:** write step 23.

### 24. Entity resolution evaluation

Advance through `mapping_workflow` step 8: evaluate entity resolution results from the test
load. Present match counts, entity counts, and quality assessment to the bootcamper. Explain
what the numbers mean: how many records resolved into how many entities, what the deduplication
rate suggests about data quality, and whether the mapping is producing good results.

**Checkpoint:** write step 24.

#### 24a. Capture ER statistics

After evaluating entity resolution results, capture the current statistics to a JSON file for
comparison tracking. Query the following counts through the Senzing SDK: never with direct SQL
against `database/G2C.db`. Per the ground-rules MCP routing, get counts/stats via
`reporting_guide`, or generate SDK code with `generate_scaffold` / `find_examples` and run it:

- **entity_count:** total resolved entities
- **record_count:** total records loaded
- **match_count:** number of matches (records that resolved together)
- **possible_match_count:** number of possible matches flagged
- **relationship_count:** number of disclosed relationships

Save the statistics to `config/er_current_{datasource}.json` (datasource name lowercased):

```json
{
  "datasource": "CUSTOMERS",
  "entity_count": 847,
  "record_count": 1000,
  "match_count": 153,
  "possible_match_count": 12,
  "relationship_count": 45,
  "captured_at": "2026-04-20T14:30:00Z"
}
```

#### 24b. Baseline detection

Check whether a baseline file exists at `config/er_baseline_{datasource}.json` (lowercase
datasource name).

- **If no baseline exists:** This is the first test load for this data source. Save the current
  statistics as the baseline:

  ```text
  No baseline found for {DATASOURCE}. Saving current statistics as your first baseline.
  ```

  Copy `config/er_current_{datasource}.json` to `config/er_baseline_{datasource}.json`. Inform
  the bootcamper that future test loads will compare against this baseline so they can see how
  mapping changes affect entity resolution quality.

- **If a baseline exists:** Proceed to step 24c (comparison).

#### 24c. Compare against baseline

When a baseline exists, compute the diff between `config/er_baseline_{datasource}.json` and
`config/er_current_{datasource}.json` and present it. (The Kiro `compare_results.py` helper is a
later porting phase; compute the per-metric deltas directly for now.) Show per-metric deltas
(entities gained/lost, matches gained/lost) and an overall quality assessment (improved,
degraded, or unchanged). Explain what the changes mean:

- **Fewer entities + more matches** → better deduplication, mapping improvement
- **More entities + fewer matches** → less deduplication, possible mapping regression
- **Unchanged** → mapping change had no measurable impact on ER quality

#### 24d. Accept or reject new baseline

> **Only present this gate when a prior baseline existed** (i.e., this is not the first test
> load). On the first test load, the baseline is saved automatically in step 24b without asking.

👉 **Your mapping change resulted in [quality_assessment]. What would you like to do? Reply with a number:**

1. Accept these results as your new baseline.
2. Iterate on the mapping and try again.

*(Internal: end the turn on this question and wait.)*

- **If accepted:** Copy `config/er_current_{datasource}.json` to
  `config/er_baseline_{datasource}.json`. Confirm: "New baseline saved. Future test loads will
  compare against these results."
- **If rejected:** Keep the existing baseline unchanged. Inform the bootcamper they can return
  to Phase 2 to adjust their mapping and re-run Phase 3 to see updated results.

After `mapping_workflow` steps 5–8 generate output files into the workspace, place them into the
correct project subdirectories per the file-placement guidance in `phase2-data-mapping.md`.

### 25. Present results and decision gate

Present the Phase 3 results summary for this data source: records loaded, entities created,
deduplication rate, quality assessment, and any issues found. Then pin the decision-gate question
verbatim:

👉 **Are you ready to proceed?** (respond yes or no)

*(Internal: end the turn on this question and wait.)*

> **Data source registry:** Update the source's `test_load_status` to `complete` and
> `test_entity_count` to the entity count from the test load in `config/data_sources.yaml`. Set
> `updated_at`.

Handling (INV-284), each named again in [Leaving Phase 3](#leaving-phase-3):

- **yes** → Phase 2 step 19 (`phase2-data-mapping.md`). Step 19 starts the next unmapped source's
  own `mapping_workflow` run, or, when no unmapped source remains, continues to step 20, which runs
  Module Completion and asks the transition question. Ask no question about the whole run here
  (INV-344).
- **no** → Phase 2 step 17, to iterate on this source, as step 16's iterate options do. Re-entering
  Phase 3 afterwards needs the bootcamper's explicit **test_load** at step 18a again.

**Checkpoint:** write step 25.

<a id="leaving-phase-3"></a>

## Leaving Phase 3

⛔ **(INV-344) Every exit from Phase 3 returns to Phase 2's per-source loop.** Phase 3 runs for one
source, so its exits are gates inside the per-source loop: none asks a question about the whole run,
none proceeds to Data processing directly, and none writes the registry entry of any source other
than this one.

| Exit | This source's registry entry | Resumes at |
|---|---|---|
| SDK not set up, and the bootcamper skips (Before starting Phase 3) | `test_load_status: skipped` | Phase 2 step 19 |
| Step 21 detection fails, and the bootcamper skips | `test_load_status: skipped` | Phase 2 step 19 |
| Step 25 **yes** | `test_load_status: complete`, `test_entity_count` (step 25's registry note) | Phase 2 step 19 |
| Step 25 **no** | as step 25's registry note left it | Phase 2 step 17 |

> **Data source registry (skip exit):** Update **this source's** `test_load_status` to `skipped`
> in `config/data_sources.yaml` and set `updated_at`. Leave every other source's entry as it is: a
> source still to be mapped reaches step 18a's decision itself. (Data processing Phase A treats
> `skipped` and a missing value the same way.)

⛔ **(INV-076) Phase 3 offers no route past Data processing.** Data processing is a Required
module, so it always follows this module, in `selected_modules` order. Module 5 is completed only at
Phase 2 step 20 (`phase2-data-mapping.md`), its single completion site: Phase 3 never runs Module
Completion, and step 19's per-source mapping-spec gate covers the Phase 3 path too. Step 20 also
carries the optional baseline status summary.

## Phase 3 session resume

On session resume during Phase 3, read both the mapping state checkpoint
(`config/mapping_state_[datasource].json`) and `config/bootcamp_progress.json` to determine
which Phase 3 steps (21–25) completed. Restart `mapping_workflow` and fast-track through
completed steps (5–8). If the test load (step 22) completed but evaluation (step 24) did not,
re-run evaluation without reloading. Step 25 is Phase 3's last gate: if the session was interrupted
before it was answered, present the Phase 3 results again and resume from step 25.

A progress file written under the old flow can record a Module 5 step that this phase no longer
has, after its Module Completion already ran: this module's `SKILL.md` → "Resuming" handles it.

## Rules

- NEVER hand-code attribute names: use `mapping_workflow`.
- NEVER guess method signatures: use `generate_scaffold` / `get_sdk_reference`.
- NEVER save to `/tmp/`: all files project-relative per the ground-rules file-placement
  contract.
- Never generate direct SQL against `database/G2C.db`: all data access goes through Senzing
  SDK methods (counts/stats via `reporting_guide`).
- Always validate with `analyze_record` before loading, passing its **required**
  `workspace_dir='data/mapping'` — the call fails without it, and the parameter is what keeps the
  analyzer script and its reports inside the project rather than in `/tmp`.

## Success criteria

- ✅ Test load completed for each data source (or explicitly skipped).
- ✅ Entity resolution results reviewed (deduplication rate, quality assessment).
- ✅ Step 25 answered, and the flow returned to Phase 2 (step 19, or step 17 to iterate).

## Interpreting `analyze_record` results

Errors from `analyze_record` can leave the Feature Analysis table empty with headers but no rows.
The table being empty is expected in that case, not a bug: feature analysis is skipped when the
record does not present features where the analyzer looks for them.

⛔ **Before fixing anything, sort the findings the way `phase2-data-mapping.md` requires** — the
analyzer reports conformance to the *recommended* schema, which is a different question from
whether the data loads. This split is INV-144 (only structural invalidity may block; a conformance
finding must not trigger remapping) and INV-145 (every shape the Entity Specification supports is
accepted, not only the recommended one):

- **Genuinely structural** (malformed JSON, missing `DATA_SOURCE`, unparseable record): the data
  cannot load. Fix it in the transformation program, then re-validate.
- **Conformance to the recommended schema** — above all the older **flat** format: feature
  attributes at the record root, with a per-feature root sub-list (`NAMES`/`ADDRESSES`/
  `IDENTIFIERS`) wherever a feature repeats. It is reported as "Missing or non-array FEATURES" and
  "Feature attribute 'X' must be inside FEATURES array", and the Entity Specification states the
  shape is **still supported**. It loads and resolves. Report it as a notice and continue. Do
  **not** rewrite the transformation program to clear it, and do not read the accompanying
  `No NAME features found` as evidence that names are absent — they are extracted normally at load.

The arbiter is this phase's own instrument: load one unmodified record and read back the features
Senzing extracted. Extracted features settle it in favor of loadability, whatever the analyzer's
exit code was.

⚠️ **One SCHEMA finding is NOT a conformance notice, and it belongs one phase earlier.** A
`disposition: payload` field emitted at the record root under a **registered feature attribute's
name** is reported here as a schema finding — but it is not a question of recommended-versus-flat
shape. It means the Bootcamper's routing answer was not honored: at the record root that name is
extracted as a feature regardless of the payload intent (observation-only, 2026-08-17 — see
`phase2-data-mapping.md` step 11, which carries the full marker and its evidence). If it reaches
this phase at all, step 11's collision check did not run or was skipped; resolve it as step 11
prescribes — offer the rename, never silently re-route — rather than filing it under the conformance
split above and continuing.

## Encoding

- Detect encoding in the profiling step. Convert to UTF-8 in the transformation program.
- Non-Latin scripts: `search_docs(query="globalization", category="globalization")`. For the
  sections to ask for by topic — and the two phrasings that return wrong content — see this
  module's `SKILL.md` → "Multi-language data" (INV-212, INV-300) rather than restating them.
- Strip the UTF-8 BOM from Windows CSV files. JSON libraries handle special character escaping.
- That covers a BOM arriving in **input** data. The more damaging case is a BOM you *write*: on
  PowerShell 5.1, `Out-File -Encoding utf8` prefixes the file it creates, so record 1 of a generated
  JSONL fails to parse while the rest are fine — which reads as one bad source record, not an
  encoding fault. See `../bootcamp-onboarding/ground-rules.md` → "Windows and PowerShell" before
  writing any generated file through PowerShell.

## Hooks

In the GitHub Copilot plugin, bootcamp hooks ship with the plugin: there is no manual hook-install
step (this replaces the Kiro `install_hooks.py` / `.kiro/hooks/` workflow). The plugin's Stop
hook is a safety net for the closing 👉 question; you still own that question on every yielding
turn (see the ground rules).
