# Module 6, Phase A: Build Loading Program (steps 1–4a)

Follow the ground rules. `🛑`/`⛔` are internal control directives, never render them; signal
a stop by ending the turn on the single 👉 question and waiting. All loading, redo, and query
code comes from the MCP tools (`generate_scaffold` / `sdk_guide`), never hand-written.

## Before Loading: pre-load checks

Complete these three checks before starting step 1.

### Conditional workflow, check Phase 3 status

Read `config/data_sources.yaml` and check `test_load_status` per source:

- **`complete`**, Phase 3 was done in Module 5. Acknowledge: "You already test-loaded this
  source during Data Quality, Mapping, and Transformation (Phase 3) and saw [entity_count] entities. Data processing builds on that with
  production-quality loading, error handling, progress tracking, throughput optimization, redo
  processing, and incremental strategies." Skip the basic test-load step and go straight to the
  production loading workflow.
- **`skipped` or missing**, note that a brief test load is **owed** for that source, and say so:
  "You skipped the sandbox test load in Data Quality, Mapping, and Transformation, so we'll do a
  quick one before the full load." ⛔ **Do not run it here.** Phase B step 5 runs it, and it
  cannot run any earlier (INV-089 is why the ordering is not a preference): it needs the loading program, which step 3 builds from the volume tier
  captured at step 1, and the registered `DATA_SOURCE` codes, which step 4a creates — without
  which the load fails with `SENZ2207`, the exact error step 4a exists to prevent.

**Phase 3 results integration:** if `test_load_status` is `complete` for multiple sources, use
`test_entity_count` to estimate total volume and plan resource allocation, use Phase 3 quality
assessments to inform load order (higher quality → stronger baseline), and note any issues
found during Phase 3 that may affect orchestration.

### Pre-load data freshness check (advisory only)

If the bootcamper is using CORD sample data (downloaded via `get_sample_data`), remind them to
confirm their data files haven't changed since download. This is advisory only, never block
loading. If they are using their own data, skip silently. (The Kiro CORD-freshness helper
`scripts/cord_metadata.py` is a later porting phase; give the reminder inline for now.)

### Anti-pattern check

Call `search_docs(query="loading", category="anti_patterns", version="current")`. Key pitfalls:
bulk-loading issues, threading problems, redo processing, load-order dependencies. The top hit is
*Senzing Anti-Patterns: Configuration and Initialization*; read past the first hit to *Senzing
Anti-Patterns: Architecture and Performance*, which carries "Do Not Use Single-Threaded Loading",
"Do Not Use SQLite in Production" and the redo anti-patterns.

## 1. Assess production record volume

Present this pinned question verbatim (INV-056), including the explanation, which **precedes** the
👉 as its framing (INV-211) — the explanation is what stops the bootcamper answering with the
bootcamp's record count instead of their real target. The options sit directly beneath the 👉, and
nothing follows them:

> The question below is about the system you're ultimately building, **not** the dataset we're
> working with here. It changes the loading program's *architecture*: a demo loader and a
> fifty-million-record loader are genuinely different programs (single-threaded vs. thread-pooled,
> batching, checkpoint/resume, throughput instrumentation, queue-based distribution). Answer for
> your real target volume even if it dwarfs the bootcamp dataset. This program is yours to take home.
>
> If you're not sure, pick the range your best estimate falls in — it can be revisited.
>
> 👉 **In production — not in this bootcamp — how many records do you expect to load? Reply with the option number:**
>
> 1. 500 or fewer — demo/evaluation
> 2. More than 500, up to 500,000 — small production
> 3. More than 500,000, up to 10,000,000 — medium production
> 4. More than 10,000,000 — large production

⛔ Never substitute the bootcamp's own record count into this question — reference it dynamically or
not at all, or the pinned wording goes stale the moment the dataset changes.

*(Internal: end the turn on this question and wait.)*

**Classify and persist the tier.** Map the answer to a tier, `demo` (500 or fewer), `small`
(more than 500 up to 500,000), `medium` (more than 500,000 up to 10,000,000), `large` (more than
10,000,000). Each boundary value belongs to exactly one tier. **500 itself is `demo`**, and that is
deliberate: `sdk_guide` returns the single-threaded demo template at or below 500 (see "The cutover
is 500 records" below), so classifying exactly 500 as `small` would route the bootcamper to the
threaded-pattern instructions and then hand them a loader the tool itself labels "demo-only".
If the reply is a bare option number (1–4),
select that tier directly and persist `raw_value: null`.
⛔ **(INV-328) An option picks a range, not a count, so the option number is never stored in `raw_value`.**
Steps 3 and 4 pass `raw_value` to
`sdk_guide` as `record_count`, and an option number there reads as a count below the demo cutover:
picking **3 — medium production** returned the single-threaded demo loader
(`sdk_guide(topic='load', language='java', record_count=3)` → `LoadRecords.java`, server 1.37.13,
2026-09-26). If it is free text, parse the number, classify, and store the parsed number as
`raw_value`. If it is unparseable, ask ONE clarifying follow-up presenting the four numbered
tiers, then classify; if still unparseable, default to `demo`, persist `raw_value: null`, and tell
the bootcamper demo/evaluation was selected as the default. Persist `production_volume` (`tier`
and `raw_value`) to `config/bootcamp_preferences.yaml` and checkpoint step 1 to
`config/bootcamp_progress.json`. ⚠️ **`raw_value: null` beside a set `tier` is a recorded answer —
"no count was given" — not a missing or unreadable value.** The tier still decides, and every step
that reads `raw_value` has a branch for `null`.

(The Kiro helpers `answer_binding.py` / `volume_utils.py` encode this parsing and persistence;
the script port is a later phase, apply the logic inline for now.)

⛔ **Echo the consequence back before generating any code.** State the tier *and* the architecture
it selects, and invite a correction — a misread costs nothing to fix here and is expensive to
discover once the loader is written. For example: "Medium production, so I'll build a thread-pooled
loader with batching, checkpoint/resume, and throughput reporting — say the word if that volume
isn't right." For `demo`, name what they are getting and why: "Demo/evaluation, so a single-threaded
loader — simplest to read, and appropriate below the license limit. If your real target is larger,
tell me now and I'll build the threaded version instead." When `raw_value` is null, also say that
no count was given, so the Bootcamper knows the build follows the range: "Medium production — you
picked a range rather than a count, so I'll build for the range: a thread-pooled loader…"

**License framing (default + expansion paths).** After the tier is classified, present
licensing as a default the bootcamper already has, never as a hard cap:

- ⛔ **Read the measured `license_record_limit` from `config/bootcamp_progress.json` before framing
  anything, and suppress this entire block when it does not bind (INV-244, INV-012).** `0` (no cap),
  or a value **≥ the dataset size**, means the bootcamper is not constrained: say nothing here about
  licenses, defaults, expansion paths or downsizing, and go straight to step 2. Only a **positive
  limit below the dataset size** puts licensing in scope at this step. If the field is **absent or
  null** that means *"never measured"*, not *"no custom license"* — follow the three branches under
  *"Reconcile it against the license already detected"* below rather than restating them here
  (INV-183, INV-300), then re-enter this bullet with the measured value. ⛔ **Do not measure it again here**:
  the value you would be re-deriving was already measured and persisted by the step that owns this
  question, and a second SDK call is the way two answers start to differ.
  ⛔ **(INV-295) One exception, and it is the reason `license_record_limit_measured_at` exists: a reading marked
  provisional (or carrying no marker) takes the absent branch, not this one.** SDK setup's Step 5a
  reads the license before Step 8 writes `CONFIGPATH`, so that reading cannot see a license installed
  at the system config path; Step 8a re-takes it, but its "cannot re-measure" branch deliberately
  leaves the provisional figure in place rather than blanking it. A provisional value is therefore a
  real measurement of an incomplete view — which is exactly what the "do not measure again" rule
  above must not apply to, because re-deriving it is the point.
  ⚠️ **`license` in `config/bootcamp_preferences.yaml` is not this gate.** It records *how* a license
  was obtained — applied or requested — and a bootcamper who simply has a good one installed is
  measured and never writes it. The measured limit governs (the same precedence the branches below
  state: a value measured on this machine outranks generic guidance about that value).
- **When the limit does bind:** frame the built-in evaluation license as the default they already
  have. Present the expansion
  paths — apply an existing license, request one through the external channel
  (<support@senzing.com>), and, when available, request one in-flow via the Senzing MCP server —
  before any mention of downsizing. Downsizing (sampling or a smaller subset) is one option
  among these, not the only path.
- Source the record capacity and validity period from a Senzing MCP tool — **from the server,
  not from this file** (a sourcing floor) — and present exactly what it returns. If a value is unavailable or the MCP server can't be reached,
  omit the figure and say it is currently unavailable, never substitute a remembered figure.
- Gate the in-flow path as Module 1 does: check `submit_feedback` availability via
  `get_capabilities` (wait up to 30s), and omit the in-flow path when it is unavailable, errors,
  or does not respond. If the bootcamper already has a license (`license` set in
  `config/bootcamp_preferences.yaml`), route them to the apply-an-existing-license path and omit
  the in-flow option — that key narrows **which** expansion path to show, never **whether**
  licensing is in scope, which the measured limit decided above. Refer to the Senzing MCP server by name only, never a URL.

**Checkpoint:** write step 1 to `config/bootcamp_progress.json`.

## 2. Identify the input data

Determine where each source's Senzing-formatted JSON records are — read the source's `file_path`
from `config/data_sources.yaml` rather than assuming a fixed directory:

- Mapped sources: transformation output from Module 5, in `data/senzing-ready/`
- Fast-pathed CORD / already-Senzing-ready sources (`fast_pathed: true`): the original file in
  `data/raw/`, which Module 5's fast-path kept as the source's `file_path` (no transformation)
- Direct Entity Specification-compliant data files; database query results or API responses

Update the source's `load_status` to `loading` in `config/data_sources.yaml` and set
`updated_at`.

**Checkpoint:** write step 2.

## 3. Create the production loading program

Help the bootcamper build a complete, production-quality loading program for this source. All
generated code must follow the coding standards for the chosen language. (Full
`CODE_QUALITY_STANDARDS` reference is a later porting phase; apply clean-code conventions for
the language for now.)

**Volume-aware scaffold.** Read `production_volume` from `config/bootcamp_preferences.yaml`.

⛔ **`record_count` is a parameter of `sdk_guide`, not of `generate_scaffold`.** `sdk_guide` is the
tool that *selects* the threaded or single-threaded template from the record count; passing
`record_count` to `generate_scaffold` does nothing, because that tool takes only `language`,
`workflow`, and `version` and returns the whole snippet list. Verify both signatures via
`get_capabilities` rather than trusting this note (a sourcing floor).

**The cutover is 500 records, from `sdk_guide`'s own `record_count` contract** (re-read on MCP
server 1.32.9, 2026-08-14) — `sdk_guide`'s own
contract for `record_count` states that at or below 500 it returns the single-threaded demo, and
above 500 (or when the count is omitted) it returns the threaded production pattern. A call at a
few thousand records returns the thread-pool template and labels the single-threaded alternative
"demo-only, single-threaded — do not use for production volumes (>500)". This matches
`search_docs(query="loading", category="anti_patterns")` → "Senzing Anti-Patterns: Architecture and
Performance" (its second hit: read past the first) → **"Do Not Use Single-Threaded Loading"**, whose remedy is a thread pool of 2–8
workers per CPU core. Re-confirm the threshold from MCP at implementation time; do not carry this
number forward as a remembered fact.

⛔ **The same call also returns a licensing verdict — and it is computed from the record count
alone.** `sdk_guide`'s own contract for `record_count` states that values above 500 "surface license
guidance (default Senzing license limit)". The tool has no way to know what license is installed, so
above the threshold it emits a `LICENSE REQUIRED` note prescribing an evaluation license or sampling
to the first 500 records — **whether or not any of that applies to this bootcamper**.

**Reconcile it against the license already detected before relaying or acting on it.** Read
`license_record_limit` from `config/bootcamp_progress.json` (Module 4's license gate, Step 8a,
persists it from `SzProduct.get_license()`) and apply the same effective-limit rule as
`phaseB-load-first-source.md`:

- **`0` (no cap), or ≥ the dataset size** — the note does not apply. **Suppress it entirely**: say
  nothing about licenses or sampling, take the returned code, and ignore the licensing prose. A
  warning the bootcamper cannot act on is noise (INV-012).
- **Positive and below the dataset size** — the note applies. The single License Key gate (Module 4,
  Step 8a) already offered to expand capacity; restate that as a choice, never force downsizing.
  ⛔ **Do not improvise a menu of options here, and do not ask what to load.** This phase builds the
  loader; the load decision — with its pinned question, the *"a license may already have arrived"*
  readout, and the pointer to Step 8a sub-step 5's apply procedure — belongs to
  `phaseB-load-first-source.md` step 7, once. Improvising a choice at this point is how a Bootcamper
  came to be offered *"wait until the evaluation license is applied"* with no way to reach it.
- **Absent or null** — ⛔ **(INV-244) this means "never measured", not "no custom license". Measure it, do not
  assume it.** **Every step that writes `license_record_limit` writes only a MEASURED value** —
  including this branch, below. ⚠️ **Do not reason from a count of writers**; that number has been
  stated wrongly twice. What makes absence uninformative about the *license* is that no step writes
  this field without measuring it: SDK setup's Step 5a measures as soon as the SDK is verified and
  deliberately writes nothing when it cannot, and Module 4's Step 8a gate is **volume-gated by
  design**, so a bootcamper with a small dataset never triggers it. In both cases the **absence says
  nothing about the installed license** — it is a measurement that did not happen. Assuming the default here relays a 500-record note —
  and `sdk_guide`'s sampling prescription with it — to someone whose license may have no cap at
  all, which is the same harm named just above, reached through the branch that is taken far more
  often. It also contradicts a higher-precedence rule: a value you measured on this machine governs
  over generic guidance about that same value, and `ground-rules.md` names the license record limit
  explicitly (INV-012). It is one SDK call away.
  - **Measure it** by Module 4 Step 8a sub-step 7, which calls `SzProduct.get_license()` and parses
    `recordLimit`. Follow that step rather than re-deriving it (INV-300); the module already builds
    and runs SDK programs in the bootcamper's language, so this needs no new machinery.
  - **Persist it** as `license_record_limit` in `config/bootcamp_progress.json`, together with
    `license_record_limit_measured_at: "module-06 phase A (engine configuration in force)"`, so later
    steps, Phase B and graduation see a detected value instead of the same absence — and can tell it
    was taken with a complete view rather than SDK setup's provisional one.
  - **Then re-enter these three branches** with the measured value. `recordLimit: 0` lands on the
    first branch and correctly suppresses the note.
  - **Only if the call fails** (no engine yet, SDK error) does the default-limit note apply — and
    say plainly that it is an assumption, naming what could not be measured, rather than presenting
    it as the detected limit.

Acting on the unreconciled note is not harmless: it sends a bootcamper with an unlimited license to
sample down to 500 records, and the shrunken dataset then under-demonstrates the cross-source
resolution that Modules 6 and 7 exist to show. Observed with `record_count=23152` against a license
reporting `recordLimit: 0`.

So only the `demo` tier — which is below the default license limit anyway — gets a single-threaded
loader. Every tier that represents a real production system gets the threaded pattern:

- **`small`, `medium`, or `large`:** call `sdk_guide(topic='load', language='<chosen_language>',
  record_count=<raw_value>)` for the threaded production pattern. **When `raw_value` is null**
  (the tier came from an option, so no count was given), call `sdk_guide(topic='load',
  language='<chosen_language>')` **without** `record_count`: omitting it returns the threaded
  pattern, the same safe default the "Missing or unreadable" branch below relies on. Never pass
  the null, or an option number, as `record_count` (INV-328). Add a code comment stating the
  tier and the architecture recommendation (thread pool for small and medium; distributed /
  queue-based for large). When `raw_value` is null, the comment also says the tier came from a
  range and no count was given.

  ⛔ **(INV-296) The tier picks the PATTERN; `database_type` picks the WORKER COUNT — read both.** Read
  `database_type` from `config/bootcamp_preferences.yaml` (the key SDK setup's Step 7 writes when the
  engine is chosen, valued `sqlite` or `postgresql` — the same file and key the SQLite pre-load
  check below reads, never `bootcamp_progress.json`) **here**, not only at that check
  further down. The tier answers "what shape of program"; it cannot answer "how many writers this
  datastore tolerates", and taking the worker count from the tier alone is how a
  production-tier loader ends up pointed at a datastore that cannot take it.

  **The server makes this a database question, in its own words.**
  `search_docs(query='loading', category='anti_patterns')` → *"Do Not Use Single-Threaded Loading"*
  (in its second hit, *Senzing Anti-Patterns: Architecture and Performance*: read past the first
  hit) says *"Start with 2-8 workers per CPU core and **tune based on your database and storage
  throughput**"*, and *"Do Not Use SQLite in Production"* says SQLite *"does not support concurrent
  writes"*, listing *"Database locked errors under concurrent access"* among its symptoms (server
  **1.37.19**, docs index 2026-10-02 18:46 UTC, 2026-10-02). So:

  - **`postgresql`** (or any supported RDBMS) — take the tier's full concurrency. This is the case
    the 2-8-per-core figure is written for; nothing is capped.
  - **`sqlite`** — keep the tier's threaded *pattern* and **serialize the writes**: a single writer,
    or a small fixed ceiling if the language's pool cannot be sized to one. ⚠️ **This ceiling is a
    DERIVATION, not a served figure** — no MCP route returns a SQLite worker count. What the server
    serves is the property (no concurrent writes; locked errors under concurrent access) and the
    instruction to tune by database; the ceiling is that property's consequence. Mark it that way in
    the code comment rather than presenting a number as documented (INV-080/INV-149).
  - **Absent or unreadable** — treat it as the SQLite case and say so. The conservative reading is
    the one that cannot corrupt: a serialized loader on PostgreSQL is merely slower, while a
    thread-pooled loader on SQLite is the documented failure.

  **Say it in the code comment the step already requires**, so the take-home loader carries both
  halves: the tier and its architecture, *and* that concurrency was reduced for this datastore with
  what to raise it to when they move to PostgreSQL. A loader tuned for a database the Bootcamper is
  not using is a defect they inherit silently — and they **do** inherit it: graduation copies
  `src/load/**` into `production/src/load/` **verbatim** and deliberately does not rewrite it
  (`../graduation/SKILL.md` → Step 2, "the loader is theirs"). This comment is therefore the only
  place the concurrency decision is explained to them at all, and the only thing that tells them
  what to change when the production datastore is not SQLite.
- **`demo`:** call `sdk_guide(topic='load', language='<chosen_language>', record_count=<raw_value>)`
  — the same call, with a count below the threshold, which returns the single-threaded demo
  template. Add a code comment stating the tier and that single-threaded loading is appropriate at
  demo scale **and is a documented anti-pattern above it**, so the bootcamper knows what to change
  if their volume grows.
  **When `raw_value` is null** (an option reply, or the unparseable default), pass the **demo
  cutover** as `record_count`: the top of the single-threaded range, as `sdk_guide`'s own
  `record_count` contract states it **at call time**. Read it from that parameter's description,
  never from this file (INV-080). That returns the single-threaded demo template Step 1's echo
  promised. The code comment says the count is the tier's upper bound, not the Bootcamper's
  figure. If the contract can't be read (the MCP server is unavailable), take the "Missing or
  unreadable" branch below, and say in the code comment that the demo loader couldn't be
  selected.
- **Missing or unreadable:** call `sdk_guide(topic='load', language='<chosen_language>')` with no
  `record_count`. Omitting it yields the threaded pattern, which is the safe default — a loader that
  is threaded when it need not be merely does extra setup, while one that is single-threaded when it
  should not be is the anti-pattern above. Add a code comment saying no volume selection was found
  and that the production pattern was chosen by default.

Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` to
see the full set of loading snippets alongside the selected one when it helps to compare.

Do not use inline examples, they may use outdated SDK patterns. Customize the scaffold with
the bootcamper's file path, data source name, and progress reporting. If the scaffold uses
`/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database
path to `database/G2C.db` and keep all output files project-relative.

⛔ **Check the scaffold's imports before compiling, not after.** A scaffold may import a package
outside the language's standard library that the environment does not provide — the Java snippets,
for example, import `javax.json` (JSON-P), which plain `javac` does not supply and which this
bootcamp never installs a build tool to fetch. Verify against the actual install rather than
assuming, and resolve it **before** the compile, so the bootcamper never has to diagnose a raw
import error in code they were told was authoritative.

When you resolve it: **replacing the JSON library is safe; altering the SDK calls is not.** Keep
every Senzing method name, signature, and flag exactly as the scaffold has them — that fidelity is
the whole reason to use `generate_scaffold` — swap only the JSON handling (prefer the
dependency-free reader already used for the mappers), and record the substitution in the source
header so the take-home code shows what deviated and why. See
`../module-02-sdk-setup/SKILL.md` → "The launch environment".

The program must include production-quality features:

- **Robust error handling:** per-record error logging with record ID, error code, and message.
  Failed records go to `logs/loading_errors.json` without stopping the load.
- **Progress tracking with throughput reporting:** display progress every N records (e.g. every
  100 or 1000) showing records loaded, error count, elapsed time, and records/second.
- **Statistics reporting:** at completion, report total attempted, loaded, failed, duration,
  throughput, and error summary.
- SDK initialization, record-loading loop, and proper cleanup.

**Save the program** in `src/load/` with a clear name (e.g.
`src/load/load_customer_db.[ext]`).

**Checkpoint:** write step 3.

## 4. Use MCP tools for code generation

Call `generate_scaffold` with workflow `add_records` and the chosen language for version-correct
SDK code. Call `sdk_guide(topic='load', language='<chosen_language>', record_count=<raw_value>)`
for platform-specific loading
patterns — as in step 3, `record_count` belongs to `sdk_guide` and is what selects the threaded
versus single-threaded template. **When `raw_value` is null**, use step 3's null branch for the
tier: for `small`, `medium` or `large`, omit `record_count`; for `demo`, pass the demo cutover
read from `sdk_guide`'s `record_count` contract at call time. Never pass the null, or an option
number, as `record_count` (INV-328).

**Checkpoint:** write step 4.

## 4a. Register the data source codes (before loading)

Register every `DATA_SOURCE` code present in the data about to be loaded into the Senzing
configuration **before** the Phase B load, so the first load does not fail with
`SENZ2207: Data source code [...] does not exist`. Senzing does not auto-create data source
codes — they must be registered in the active config first — and the default config seeded in
Module 2 (SDK setup) knows none of the bootcamper's codes, because the data was collected
afterward (Module 4). This mirrors the register-before-load step that System Verification and the
Truth Set visualization module already run.

1. **Determine the codes to register.** Collect the distinct `DATA_SOURCE` values present in the
   record(s) about to be loaded — from the Senzing-ready JSONL in `data/senzing-ready/` for mapped
   sources, and from the original file in `data/raw/` for `fast_pathed: true` CORD /
   already-Senzing-ready sources — cross-checked against the source's entry in
   `config/data_sources.yaml`. Never register a code that is not present in the data.
2. **Generate the registration code from the MCP server** (never hand-write it): call
   `sdk_guide(topic='configure', language=<from `programming_language`>, data_sources=[<the codes
   from step 1>])` (and `generate_scaffold` if it exposes a data-source registration workflow),
   reading the language from `config/bootcamp_preferences.yaml` (never a hardcoded default). Save it
   to `src/load/register_data_sources.[ext]` (INV-018).

   <!-- MCP-NEGATIVE: sdk_guide(topic='configure', language='python', data_sources=['ECOMMERCE_ORDERS','POS_LOYALTY','EMAIL_MARKETING']) — none of the three supplied codes appears anywhere in the response; the returned snippet still carries the hardcoded sample tuple — owner: sdk_guide(topic='configure', data_sources=[...]) IS the route that would carry substituted codes — data_sources is its own documented parameter ("Data sources to register (for configure topic)"), so this call was asked WITH the codes rather than inferred from a sibling call, and its response selected the registration snippet correctly while substituting nothing (absence negative) — server 1.36.0, 2026-09-02 -->
   ⛔ **`data_sources` SELECTS the snippet and SUBSTITUTES nothing — you must fill in the codes
   yourself.** Passing it makes the **registration** snippet primary; omitting it returns the
   **seeding** snippet instead, which is not what this step needs. The returned code hardcodes a
   sample tuple of Senzing's own demo data source codes, its own `notes` say *"Replace sample data
   source names with your own"*, and **none of the codes you passed appears anywhere in the
   response**. Locate the snippet by its **`source_path`**, not by position among the alternatives,
   then substitute the step-1 codes into it. Shipping it unsubstituted registers codes the
   Bootcamper does not have and leaves the first load failing `SENZ2207` on the codes they do —
   which is what item 1 above exists to prevent.

   ⛔ **(INV-002/INV-090) Match the response against that PROPERTY, never against a literal tuple
   or filename from this page — both are per-language.** The property holds in every language and
   survives a snippet being re-authored; the literals do not. Verified with the three codes passed
   explicitly on server **1.36.0, 2026-09-02**: Python's snippet
   (`python/configuration/register_data_sources.py`) hardcodes
   `("CUSTOMERS", "REFERENCE", "WATCHLIST")`, while **Java's**
   (`java/snippets/configuration/RegisterDataSources.java`) hardcodes
   `{"CUSTOMERS", "EMPLOYEES", "WATCHLIST"}` — **`EMPLOYEES`, not `REFERENCE`**, and a different
   `source_path` shape. Telling a Java Bootcamper to look for `REFERENCE` sends them hunting for a
   line that is not in the response they received. Read `programming_language` from preferences and
   describe what you actually got back.

   ⚠️ **The config-replacement mechanics differ per language too, and neither shape is canonical.**
   Both languages register the modified config and then replace the default config id; **Java's
   snippet wraps that pair in a retry loop** — `while (!replacedConfig)`, catching
   `SzReplaceConflictException` and re-reading the current default config id — where Python's does
   not (server **1.36.0, 2026-09-02**). The substitution rule is unaffected either way: keep every
   Senzing method, signature and flag exactly as the snippet has them, and change only the codes.

   ⚠️ **On a freshly schema-created datastore, call it WITHOUT `data_sources` first.** The
   registration snippet reads the *current* default config, so it assumes one is already registered;
   the same response's `compatibility_notes` say that on a fresh datastore
   `get_default_config_id()` returns 0 and `create_config_from_config_id(0)` raises SENZ7221. The
   no-`data_sources` call returns the seeding snippet that creates one.

   The generated code MUST load the current default config, register each code from step 1, export
   it, register the new config, and replace the default config ID — and the **whole sequence must be
   safe to re-run**, so re-runs and multi-source orchestration stay safe.

   ⛔ **Build re-runnability into the sequence; do not make it depend on catching an error (INV-263).**
   Registering an identical configuration returns the **existing** config ID rather than failing —
   Senzing's release notes record *"Fix `G2ConfigMgr.addConfig` function to return success and the
   ConfigID if the configuration already exists"* — so the sequence is idempotent one call **later**
   than the per-code registration, by construction. ⛔ **No route documents a raised error for
   re-registering a code, for any binding:**
   `get_sdk_reference(topic='parameters', filter='register_data_source', language='python')` returns
   `register_data_source(data_source_code: str) -> str` with warnings only about argument types
   across bindings and no error condition (server **1.33.0, 2026-08-21**). A per-code error catch is
   therefore a permitted **fallback** and must not be the mechanism: code whose idempotency rests on
   it is untested by construction and will fail in exactly the case it was written for. Read the
   signature for the chosen binding and build for re-runnability; do not name any binding's
   exception type as a contract (INV-002).

   <!-- SEARCH-DOCS-CATEGORY-PROSE: this names the `sdk` category to describe WHAT IT INDEXES,
        not to instruct a call, so it carries no `query`. `tests/test_search_docs_calls_pass_a_query.py`
        exempts a reference carrying this marker; the marker must sit on the line above it. -->
   ⛔ **`search_docs(category='sdk')` indexes community-maintained wrapper docs alongside the
   official ones, so an error contract found there may not be your binding's.** `get_capabilities`
   states the index covers "Python, Java, C# official; Rust, TypeScript/Node.js community … not
   official Senzing SDKs". A search for this method's failure mode returns, as its top hit, a
   community Rust trait doc stating `SzError::BadInput` for an already-existing code — which
   describes that wrapper, not the official Python binding, and the result does not say so.
   `get_sdk_reference(…, language=<binding>)` is the route that answers per binding. It already warns
   about name and type divergence; **error-condition divergence is the gap this note covers.**

   ⚠️ **`get_capabilities` is quoted here deliberately, and the reason is now historical: the two
   sources once disagreed about this index, and the upstream report was acted on.** On server
   **1.33.0** `find_examples`' declared description — the text a client loads from the manifest —
   omitted TypeScript and JavaScript from both the language list and the indexed extensions and gave
   a lower repository count, which was settled by a call rather than by argument
   (`find_examples(query='add record engine initialization', language='typescript')` returned
   `brianmacy/sz-napi` → `code-snippets/initialization/engine-priming/index.ts`, so `.ts` **was**
   indexed) and reported upstream 2026-08-27. **Re-checked on server 1.36.0, 2026-09-02: the server
   aligned the two.** The declared description now gives the **same** repository count as
   `get_capabilities`, lists `.py, .java, .cs, .rs, .ts, .js`, and names TypeScript/Node.js. ⚠️ **The
   count is deliberately not written here** — the rule below forbids quoting it, and a note that
   exempted itself to say the two figures now match would be the one place in the plugin holding a
   coverage figure. Ask `get_capabilities` if you need it. ⛔ **(INV-280) Do not
   quote a repository count anywhere in this plugin** — **not because the two sources disagree
   today, but because a coverage figure is volatile server-side state**: the count moves as
   repositories are indexed, so a number pinned in shipped guidance goes stale on the server's
   schedule and nothing here notices. That reason survives the alignment; the prohibition is
   unchanged. Quote `get_capabilities` for what
   the index covers.
3. **Build the registration code if the language requires it** (compiled languages — Java, C#,
   Rust, TypeScript), using the same per-language build command as the loader.
4. **Execute it before the Phase B load.** On success, record the registered codes in
   `config/data_sources.yaml`. On failure, capture the output, call `explain_error_code` for any
   SENZ codes, and report with remediation; the loading program's generic SENZ handling remains a
   fallback.

In Phase C (multiple sources), register each additional source's code the same way before its
load — idempotently, so re-registering an existing code is a no-op.

**Checkpoint:** write step 4a to `config/bootcamp_progress.json`.

## SQLite volume pre-load check (stop-and-confirm heads-up, not a mandatory gate)

Run this once at the end of Phase A, immediately before the Phase B load begins. This is a
stop-and-confirm heads-up, NOT a mandatory gate, the bootcamper may always proceed on SQLite.

1. **Read inputs** from `config/bootcamp_preferences.yaml`: `production_volume.tier`,
   `production_volume.raw_value`, and `database_type` — the last is the key
   `../module-02-sdk-setup/SKILL.md` Step 7 writes when the engine is chosen, valued `sqlite` or
   `postgresql`. Also read the **loadable total:** the record count across **every** mapped
   source's file in `data/senzing-ready/` together, since they all land in the same SQLite
   database across Phases B and C. If any value is missing/unreadable, or the loadable total
   cannot be computed, treat it as indeterminate, do not fail; fall back to the existing advisory
   behavior and continue to the load.
   - ⛔ **An absent `database_type` is a recording failure, not a non-SQLite answer.** Because
     step 3 prompts only when the database *is* SQLite, a missing key silently disables this
     heads-up entirely. Before treating it as indeterminate, fall back to the engine Module 2
     recorded in `config/bootcamp_progress.json`, and note the gap internally so it reaches the
     recap rather than vanishing.
2. **Decide whether it was already decided.** If a `sqlite_volume_prompt` marker in preferences
   is `decided: true` and its `loadable` matches the current loadable total for this same load (or
   a `sqlite_load_time_prompt` marker covers this same load, as the sub-items below say), skip the
   prompt and proceed. (INV-331) `tier`/`raw_value` do not decide the match; a marker with no `loadable` (written before
   the field existed) does not match, so re-evaluate on the loadable total.

   `sqlite_load_time_prompt` is Module 4's marker in `config/bootcamp_preferences.yaml`, defined by
   [data collection Step 8b](../module-04-data-collection/SKILL.md#8b-sqlite-load-time-warning-collection-time-heads-up)
   sub-step 4, which gives its fields. Its `loadable` is Step 8b's figure, pre-mapping and
   license-capped, not the mapped-file total item 1 reads, so the two are never compared directly.
   These sub-items are the one statement of how Module 6 matches it; Phase B Step 7 cites them
   (INV-300).

   1. **It covers this same load only when Step 8b's figure still holds.** Recompute
      `min(collected_total, effective_limit)` from the current `config/data_sources.yaml` and
      license state by Step 8b sub-step 1's rules, counting each source as sub-step 4's
      `collected_total` does. The marker matches only when that figure equals its `loadable`. A
      source added or removed, a re-sample, or a license applied or changed since Module 4 gives a
      different figure, so the marker does not match. Mapping that changes the record count (for
      example, embedded masters) does not affect the match, because the recomputation reads the
      registry and not `data/senzing-ready/`. A marker with no `loadable` does not match.
   2. **An unreadable registry or license state is indeterminate, so the marker does not match.**
      This overrides Step 8b sub-step 1's "treat an unreadable license state as unbounded" for this
      recomputation. That fallback lets the collection-time warning still fire; here it would
      invent the figure that decides whether a recorded answer applies, so evaluate the load on
      item 3's trigger instead.
   3. **A matching marker covers the load according to its `choice`.**
      - `proceed`: covers the load as this check's own **Proceed on SQLite** does. Skip the
        prompt, and still say item 4's serialized-writer line (INV-296), applying the writer
        reduction if step 3 did not.
      - `sample`: covers the load. The sample is what Module 5 mapped, and `collected_total`
        already counts the sample's `record_count`.
      - `switch_db`: covers the load only when `database_type` is no longer `sqlite`, and on a
        non-SQLite engine item 3 does not prompt anyway. While `database_type` is still `sqlite`,
        the marker does not cover the load: say first, in one line, that the switch chosen at data
        collection was not applied, then evaluate the load on item 3's trigger.
   4. **An absent marker is "not asked", never "answered" (INV-244).** Step 8b writes the marker
      only when its warning fired, so an absent one means the loadable total was at or below the
      threshold, the engine was not SQLite, or the inputs were indeterminate. Evaluate the load on
      item 3's trigger, as for a marker that does not match.
3. **Prompt only when it matters.** Present the prompt only when the database is SQLite AND it was
   not already decided AND the **loadable total** exceeds the SQLite guidance threshold. (INV-331) The
   production tier does not trigger this prompt: it describes the take-home system, not the load
   about to run (the production line below covers it). Source that threshold from MCP rather than
   from this file (a sourcing floor); `search_docs(query="loading",
   category="anti_patterns")` → "Do Not Use SQLite in Production", in its second hit (read past
   the first hit), gives it as roughly 100,000 records ("use SQLite only for quick local testing with small datasets"). If MCP does not return
   it, the threshold is indeterminate — never substitute a remembered figure (INV-080). For a
   loadable total at or below that threshold, any non-SQLite engine, indeterminate inputs, or an
   already-recorded choice: say nothing new about volume/SQLite beyond the production line and
   proceed to the Phase B load.
4. **When prompting**, explain that SQLite entity resolution slows as the database grows, then end
   the turn on this pinned question (INV-056), verbatim — a neutral lead + numbered list (INV-051) —
   and wait (internal stop); do not start the load yet:

   👉 **Loading this data volume into SQLite may slow entity resolution as the database grows. How would you like to proceed? Reply with a number:**

   1. Proceed on SQLite.
   2. Migrate to PostgreSQL.

   *(Internal: end the turn on this question and wait.)* Then act on the choice:

   - **Proceed on SQLite:** record `sqlite_volume_prompt` = `{decided: true, choice: "proceed",
     loadable, tier, raw_value}` in preferences, then continue to the Phase B load. Do not
     re-present this prompt for the same load.
     ⛔ **(INV-296) Proceeding keeps SQLite *and* the serialized writer count step 3 selected for it — say
     so in one line.** Both options in this question are about **where** the data lands; neither
     mentions **how** it is written, so "proceed" reads as accepting a known slowdown rather than
     accepting a loader tuned for this datastore. State that the loader writes serially because
     SQLite does not support concurrent writes, and that its header comment says what to raise the
     worker count to on PostgreSQL. If step 3 did **not** apply the reduction — because
     `database_type` was absent then and is known now — apply it before the load rather than
     carrying a thread-pooled loader into a datastore this question just confirmed is SQLite.
   - **Migrate to PostgreSQL:** record `sqlite_volume_prompt` = `{decided: true, choice:
     "migrate", loadable, tier, raw_value}` in preferences, then hand off to the database-migration
     guidance (PostgreSQL migration is a production follow-up; see the graduation migration checklist). Do not restate migration steps here (INV-300).

   In both branches `loadable` is the total item 3 compared; `tier` and `raw_value` are kept for
   the record only and decide nothing.

**Production line (a statement about the take-home system, no 👉).** Once, at this same point,
when the database is SQLite and `production_volume.tier` is `medium` or `large`, say one line and
ask nothing: "At your production scale, plan on PostgreSQL rather than SQLite; the graduation
migration checklist covers the move." Say it whether or not item 4's question fires — before that
question when it does, so the turn still ends on the question. (INV-331) It changes nothing about today's
load. On PostgreSQL, or on a `demo`/`small` tier, say nothing.

*(Internal: when this heads-up fires, end the turn on the pinned question in item 4 and wait.)* Use
only synthetic/persisted values, never echo credentials or connection strings. (The Kiro
helpers `volume_utils.py`, `preferences_utils.py`, `load_time_warning.py`, and the migration
guide are later porting phases; apply the logic inline and refer to the graduation migration checklist for PostgreSQL migration for
now.)

Proceed to Phase B (`phaseB-load-first-source.md`).
