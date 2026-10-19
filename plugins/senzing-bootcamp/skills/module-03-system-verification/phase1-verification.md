# Module 3, Phase 1: Verification Pipeline (steps 1–8)

Follow `../bootcamp-onboarding/ground-rules.md`. Execute every numbered step one at a time, in
order; never skip, combine, or abbreviate a step containing a 👉 question. `🛑`/`⛔` are internal
directives, never rendered; signal a stop by ending the turn on the single 👉 question and
waiting. This sequential rule has the same precedence as a mandatory gate; no internal reasoning
overrides it.

⛔ **Every step in this phase is NON-YIELDING** — this module's only 👉 is the module-transition
question at the end of `phase2-report-close.md`. So "one at a time" here means *in order and in
full*, inside the turn that ends on that question; it does **not** mean one turn per step, because a
turn ending on a step that asks nothing would end with zero 👉 (INV-225). A faithful walk therefore
generates code, runs it, registers a data source and loads records before the turn legally ends,
and that is correct — the turn ends where the bootcamper is actually asked something. The concept
and the checkpoint consequence are defined once in
`../bootcamp-onboarding/ground-rules.md` → the 👉 protocol.

## Opt-Out Gate

Before starting Module 3 steps, check whether the bootcamper has explicitly requested to skip.

**Trigger phrases:** "skip verification", "I've already verified", "skip module 3".

**If triggered:**

1. Record the skip in `config/bootcamp_progress.json`:

   ```json
   {"module_3_verification": {"status": "skipped", "reason": "bootcamper_opted_out"}}
   ```

2. Display this warning:

   ```text
   ⚠️ Skipping system verification. If you encounter issues in later modules
   (data loading failures, SDK errors), system verification can help diagnose them.
   Say "run verification" at any time to come back.
   ```

3. Update gate 3→4 to "skipped" and proceed to the next selected module.

> **The visualization is a separate module.** System Verification produces **no** visualization —
> the guaranteed Truth Set web-app "wow moment" is delivered by the selectable **Truth Set
> visualization** module (`truthset_visualization`), a separate, standalone module run **next**
> whenever selected (always in Core; in Customized only if chosen). Skipping System Verification
> does NOT skip that module, and System Verification does not offer a standalone Truth Set demo of
> its own.

**If NOT triggered:** proceed with Module 3 normally (default path).

## Agent Rules

The following rules are mandatory for the agent executing this module:

1. **Synthetic verification data only:** verify with a small set of **synthetic records** you
   generate in Step 2 — designed to resolve deterministically into a known number of entities.
   System Verification MUST NOT acquire, load, or visualize the Senzing Truth Set, nor use CORD,
   Las Vegas, London, or Moscow. (The Truth Set belongs exclusively to the separate, standalone
   **Truth Set visualization** module.) Offer no dataset choice to the bootcamper.
2. **Database path:** the Senzing database is at `database/G2C.db`. All SDK initialization and
   database operations MUST reference this path.
3. **No dataset choice:** do not present any dataset selection prompt, menu, or question. The
   generated synthetic data is the only data used for verification in this phase.
4. **All checks execute regardless of failures:** if any step fails, continue executing all
   subsequent steps. No short-circuiting. The Verification Report MUST include the status of
   every check.
5. **Artifact isolation:** all verification artifacts (scripts and data files) MUST be created
   within `src/system_verification/`. No verification files outside it.
6. **Timeouts enforced:** every step MUST enforce its defined timeout. If a process exceeds its
   timeout, terminate it immediately and record a fail.
7. **MCP as source of truth:** all Senzing facts (SDK method/attribute names, config options,
   error codes) and all generated SDK/loading/query code come from the MCP server tools, never
   from training data. The synthetic records' expected resolution is known **by construction**
   (you design them to merge), so Step 7 validates against that design, not against an MCP
   expected-results set.
8. **Overwrite on re-run:** if the module is re-run, overwrite this module's own synthetic-`VERIFY`
   artifacts in `src/system_verification/` — but leave any Truth Set visualization artifacts
   untouched (its `truthset_data.jsonl` and load/registration code in `src/system_verification/`,
   and its visualization server under `src/server/`, INV-050), since that is a separate module
   (INV-087). The database cleanup ensures a clean slate for the synthetic records.
9. **No orphaned processes:** System Verification starts no web service; the separate Truth Set
   visualization module starts and terminates its own web service within its own phases.
10. **Progress persistence:** every step MUST record its checkpoint in
    `config/bootcamp_progress.json`. Because this phase's steps are non-yielding and share one
    turn, make **one write at the end of that turn** carrying the last completed step rather than
    eleven writes inside it — the per-step record is still complete, and eleven writes in a single
    turn is the noise INV-012 exists to reduce (`../bootcamp-onboarding/ground-rules.md` →
    "Progress and state"). If the turn cannot complete, write what did complete before stopping,
    so resume lands on the right step.

### Step 1: MCP Connectivity Check

Verify MCP server connectivity before code generation operations.

1. Call `get_capabilities` with a 10-second timeout. ⛔ A reachability probe must **not** be a
   document search (INV-204): this step discards the content and keeps only "did the server answer", so a
   `search_docs` query pays for retrieval it throws away. See
   [`../bootcamp-onboarding/onboarding-flow.md`](../bootcamp-onboarding/onboarding-flow.md) →
   "MCP health check", which states the reasoning; do not restate it here (INV-300), and do not restore a
   `search_docs` probe.
2. **If a response is received** (including empty results): MCP connectivity confirmed. Proceed
   silently; do not display connectivity status to the bootcamper.
3. **If the call fails** (timeout or error): retry `get_capabilities` once with the same 10-second
   timeout.
4. **If the retry succeeds:** proceed silently.
5. **If the retry fails:** display troubleshooting steps:
   - Verify internet connectivity.
   - Test the `mcp.senzing.com:443` endpoint.
   - Allowlist the endpoint if behind a corporate proxy.
   - Restart the MCP connection for the senzing server in GitHub Copilot.
   - Verify DNS resolution.

   Block all further module progress until the bootcamper says "retry" and the connectivity
   check passes.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "mcp_connectivity": {"status": "passed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 1a: Engine Initialization Check

⛔ **Confirm an `SzEngine` (or `SzDiagnostic`) actually initializes before generating or loading
anything.** Module 2 verifies this at its Step 9, but this module is the end-to-end verification and
must not assume it: a configuration whose SUPPORTPATH points at the wrong place can pass a version
query and fail only at the first real engine call — and if that call is the synthetic load below, the
failure lands several steps from its cause, mid-load, where it reads as a data problem.

Use the initialization code already generated in Module 2 (or re-obtain it via
`generate_scaffold(language='<chosen_language>', workflow='initialize')` — never hand-write it,
INV-080), create an engine, and release it.

**If it fails, report the error and stop here rather than proceeding to generation or loading:**

1. **If the failure names no SENZ code at all, it is a launch-environment failure, not a Senzing
   one — do not route it through `explain_error_code`.** The common shape here is
   `Unable to get settings` with an `IllegalArgumentException` / `ArgumentException`: that string is
   the null-check in Senzing's own official snippets, which fires when
   `SENZING_ENGINE_CONFIGURATION_JSON` is **unset**. So the question is whether the env script was
   sourced in this shell and whether it resolved its own path there — under zsh a
   `${BASH_SOURCE[0]}`-based script computes the wrong project root and exports nothing. Send the
   bootcamper to Module 2's
   [env script path resolution](../module-02-sdk-setup/SKILL.md#env-script-path-resolution).
   (Snippet guard verified via `search_docs` on MCP server 1.32.1, 2026-07-28.)
2. Call `explain_error_code(error_code="<code>", version="current")` and present what it returns.
3. **If the code is `SENZ2027`**, add the cause its own resolution steps do not name: the libraries
   loaded but their support data did not — the runtime **data directory** is not where the
   configuration points. Send the bootcamper to Module 2's Step 8 SUPPORTPATH check (on Windows/Scoop,
   the sibling-directory case). Verified against the Senzing FAQ on MCP server 1.32.2, 2026-07-30.
3b. **If the code is `SENZ7426`**, relay what `explain_error_code` returned (step 2 already says to)
   and send them to the *same* Step 8 check. How the tool compares with
   `sdk_guide(topic='install', …)` on this code is stated once, in Module 2 Step 8's *"Both tools
   agree on the diagnosis and the fix — not on the macOS literal"* block
   (`../module-02-sdk-setup/SKILL.md`); follow it there rather than a copy here (INV-300). One
   clause travels with the relay: on **macOS**, the tool's cask cause quotes a `SUPPORTPATH` literal
   that holds for cask 4.4.x and earlier only, so never tell the Bootcamper that literal is what
   their ini says. Step 8's `*TransRules.sz` content test applies whatever the literal.
   ⛔ Never restate this as an unconditioned rule (INV-169): stripped of the platform condition and
   of the record-level exception that block names, it becomes the over-generalization it forbids.
4. Do not diagnose from the code alone beyond that: any other code goes through `explain_error_code`
   and `search_docs` per this module's Error handling section.

This is a check, not a 👉 question — run it silently and report only on failure (INV-012).

**Checkpoint:** record `engine_initialization` alongside `mcp_connectivity` in the same
`module_3_verification.checks` object.

### Step 2: Generate Synthetic Verification Records

Generate a small set of **synthetic** records designed to resolve deterministically into a known
number of entities, so verification proves entity resolution works **without touching the Senzing
Truth Set**. The records are the agent's own composition — no MCP Truth Set fetch, no sanctioned
fallback source, no CORD substitute. Keep them obviously synthetic and PII-free (invented
names/addresses).

1. **Compose the records (by construction).** Write at least 4 records to
   `src/system_verification/verification_data.jsonl` (one JSON object per line, overwrite any
   existing file), using **Senzing Entity Specification** attribute names. If unsure of the exact
   attribute names, confirm them via the MCP server (`search_docs` / `mapping_workflow`) — never
   guess (INV-080). Design them so resolution is deterministic and known in advance:
   - **A merge cluster:** 2–3 records for the **same** synthetic person, designed to resolve into
     **one** entity. ⛔ **Make this unambiguous by construction, not by judgment** — "enough
     features, with only trivial variation" is exactly the phrase that produced a false verification
     failure, because two reasonable readings of it give opposite verdicts.

     **Identical across every record in the cluster:**

     - `NAME_FIRST`, `NAME_LAST`, and `NAME_MIDDLE` wherever present — the same strings, not
       equivalents.
     - `DATE_OF_BIRTH`.
     - The address **content** (same street, city, state, postal code).
     - The same feature *set*: if one record carries a phone, they all do.

     **May vary — formatting only:**

     - Punctuation and spacing (`123 Main St` vs `123 Main Street`, `#4` vs `Apt 4`).
     - Phone-number formatting (`702-555-0100` vs `(702) 555-0100`).
     - A middle name abbreviated to its initial where the full form appears elsewhere.

     ⛔ **These are NOT trivial variation, and must not appear in the cluster:** a **nickname**
     (`Mari` for `Marisol`), an **initial in place of a first name**, and an **omitted feature** in
     one record but not the others. Each *reduces corroboration*, and the engine may then correctly
     decline to merge — that is a defensible resolution decision, not a fault, and building it into a
     cluster you have predicted will merge sets the module up to report a healthy install as broken.

     ⚠️ **Worked counter-example, observed on a real walk (Senzing 4.3.4, 2026-08-13):** three
     records for one person with the first name varied `Marisol` / `Mari` / `Marisol` and one record
     missing its phone number resolved to **3 entities** — the `Mari` record stayed a singleton — and
     Step 7 reported FAILED. The same three records with the first name identical throughout and only
     phone/address *formatting* varied resolved to **2 entities** with a 3-record cluster, and passed.
     The engine was right both times; only the prediction changed. (This is an observation of this
     install's behavior, not an MCP claim — INV-080/INV-149.)
   - **At least one distractor:** 1+ record for a **different** synthetic person that must stay a
     **singleton** (its own entity).
   - Give every record a `DATA_SOURCE` of `VERIFY` (one synthetic source code is enough) and a
     unique `RECORD_ID`.
2. **Record the expected outcome** (by construction) for Step 7 to validate against — e.g. "4
   records → 2 entities, one entity with 3 constituent records". These figures come from the
   records you just wrote; never fetch them from anywhere.

**Checkpoint:** write to `config/bootcamp_progress.json` (a data-prep marker, not one of the
report's verification checks):

```json
{"module_3_verification": {"synthetic_data": {
  "status": "generated", "records": <record_count>, "data_source": "VERIFY",
  "expected_entities": <entity_count>, "expected_merge_record_count": <largest_cluster_size>}}}
```

`expected_merge_record_count` here is the pre-load *expectation*; the post-load *verified*
count is recorded separately as `matches_verified` in the Step 7 `results_validation` check.
The two are intentionally distinct fields (expected vs. verified), not a rename.

### Step 3: SDK Initialization

Verify the Senzing SDK initializes correctly and connects to the database.

1. Generate an SDK initialization script using `generate_scaffold(workflow='initialize')` in the
   bootcamper's chosen language.
2. **Fetch the snippet, then** save it to `src/system_verification/verify_init.[ext]` where `[ext]`
   matches the chosen-language file extension (`.py`, `.java`, `.cs`, `.rs`, `.ts`).
   <!-- MCP-NEGATIVE: generate_scaffold(language='python', workflow='initialize') — its snippets[] carry file_path, source_url, repo, raw_url, size_bytes and line_count with no content field at all — owner: generate_scaffold IS the route that would return source text, and it returns a listing plus an ordered access_steps (fetch raw_url, else git clone) instead, so fetching raw_url is the documented route (routing negative) — server 1.36.0, 2026-09-02 -->
   ⛔ (INV-234) `generate_scaffold` returns a **listing**, not code — `file_path`, `source_url`, `raw_url`,
   `size_bytes`, `line_count` per snippet, with no source text. Follow its own `access_steps` step
   1 and fetch each `raw_url`; use step 2's `git clone` if the fetch is blocked. If both fail,
   take the terminal step in `../bootcamp-onboarding/ground-rules.md` → "Once `raw_url` and
   `git clone` have both failed" (INV-160). **Never pass
   `inline=true`** — the tool's `access_steps` advertises it but its declared schema has no such
   parameter (only `language`, `version`, `workflow`), so the call cannot work (INV-160's rule,
   confirmed live for `generate_scaffold` on server 1.32.2, 2026-07-29). And never reconstruct the
   snippet from memory of "what a scaffold like this looks like" — that is the training-data
   fallback INV-080 forbids.
3. Execute the initialization script with a 30-second timeout.
4. **If the script exits with code 0 and produces no SENZ error codes:** report pass; the SDK
   connected to the database at `database/G2C.db`.
5. **If the script exits non-zero or produces a SENZ error code:** report fail. Call
   `explain_error_code` for any SENZ codes. Generate a Fix_Instruction referencing Module 2
   remediation steps.
6. **If the script does not complete within 30 seconds:** terminate the process. Report fail
   with a timeout Fix_Instruction advising a check of database accessibility and system
   resources.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "sdk_initialization": {"status": "passed|failed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 4: Code Generation

Verify the MCP server can generate a full pipeline script in the chosen language.

1. Call `generate_scaffold(workflow='full_pipeline')` in the bootcamper's chosen language.
2. ⛔ **This returns MANY files, and which one you save decides whether Step 6 can run at all.**
   The response is a **listing** of snippets across four groups — `initialization`,
   `configuration`, `loading` and `searching` — not "the" generated script. For Python that was
   **22** snippets (10 / 4 / 6 / 2) on server 1.32.9, verified 2026-08-14.

   ⚠️ **That figure is illustration, never a check to perform** — and its own history is the
   argument for the rule below. It was 18 across three groups on server 1.32.2 (2026-07-29): the
   count moved and a whole group (`configuration`) appeared, while the two loading snippets named
   below stayed exactly where they were. So a count or a position is precisely what selection must
   **not** depend on. If your live response returns a different number, that is the server indexing
   more snippets, not a problem to report. So:
   - **Pick the loading snippet that READS AN INPUT FILE line by line**, not the self-contained
     demo whose records are hardcoded in the source. For Python those are
     `loading/add_records_loop.py` (reads `INPUT_FILE`) versus `loading/add_records.py`
     (hardcoded records, no file input); every language's set has the same pair, so match on the
     **shape** — does it open a data file? — never on position in the list (INV-267).
   - **The server states this as its own anti-pattern for this workflow**, at severity `error`:
     *"Hardcoded John Doe / TEST / 1001 records"* → *"Records read line-by-line from JSONL"*, and
     *"/opt/senzing/er/testdata/truth-sets/..."* → *"User's input_file"* (returned inline in the
     `anti_patterns` field of the same call). Picking the hardcoded demo violates the server's own
     guidance, not merely this module's.
   - **Override any hardcoded input path** the snippet ships with (Python's ships
     `INPUT_FILE = Path("../../resources/data/load-500.jsonl")`) to point at
     `src/system_verification/verification_data.jsonl`. That path does not exist in a bootcamp
     project, so leaving it crashes Step 6.
   - **Fetch before saving.** As in Step 3: the listing carries no source text, so fetch each
     `raw_url` (or `git clone` per `access_steps` step 2). If both fail, take the terminal step in
     `../bootcamp-onboarding/ground-rules.md` → "Once `raw_url` and `git clone` have both failed".
     **Never pass `inline=true`** — undeclared in the schema (INV-160).

   Why this is a ⛔ and not a preference: **Step 6 executes this file "pointing it at
   `src/system_verification/verification_data.jsonl`"**, which presupposes a script that takes a
   data path. Saving the hardcoded demo satisfies every check in this step and then makes Step 6
   impossible without rewriting the file — a failure that surfaces two steps away from its cause.
3. Save it to `src/system_verification/verify_pipeline.[ext]` where `[ext]` is the standard file
   extension for the chosen language.
4. **Validate the generated file:**
   - Confirm it contains at least 1 line of non-whitespace content.
   - Confirm it includes at least one language-appropriate structural element: an import
     statement, a function definition, or a class declaration.
   - ⛔ **Confirm it reads its records from an external file** — the check that actually
     distinguishes the right snippet from the wrong one. The three checks above are satisfied by
     *any* file in the returned set, which is why they never caught this.
5. ⛔ **(INV-279) Check the saved file's imports for a package outside the standard library BEFORE
   Step 5
   compiles it — resolve it here, not from a raw compiler error.** The full procedure is stated
   once in `../module-02-sdk-setup/SKILL.md` → **"MCP Java scaffolds may need a JSON library the
   install does not provide"**; follow it there rather than a copy here (INV-183, INV-300). Two things are
   restated at this step deliberately, because a bootcamper hitting this is reading *this* file:

   - ⛔ **Replacing the JSON library is safe. Altering the Senzing SDK calls is not.** Keep
     `SzRecordKey.of`, `engine.addRecord` and every flag constant exactly as the scaffold returned
     them, and substitute only the JSON-**extraction** lines. Rewriting the SDK calls to clear an
     import error is the failure `generate_scaffold` exists to prevent.
   - ⛔ **Record the substitution in the saved file's header** — what was replaced and why — so
     `verify_pipeline.[ext]` self-documents its one departure from the authoritative scaffold
     rather than silently diverging. Never just strip the import.

   ⚠️ **On Java this is the expected path, not an edge case, and there is no sibling to escape
   to.** Every `loading/` snippet in this workflow's response that reads an input file imports
   `javax.json` — `LoadViaLoop`, `LoadViaFutures`, `LoadWithInfoViaFutures`, `LoadViaQueue`,
   `LoadWithStatsViaLoop`, `LoadTruthSetWithInfoViaLoop` (all six fetched and checked on server
   **1.33.0**, 2026-08-28). The only one that does not is `LoadRecords.java`, which hardcodes its
   records — the file item 2 above forbids picking. So the selection rule routes *toward* the
   dependency by design. `javax.json` (JSON-P) is not in Java SE, and the stock
   `senzingsdk-runtime` install does not supply it: no jar under `/opt/senzing` contains a
   `javax/json` class (checked 2026-08-28 against `sz-sdk.jar` and its siblings; environment
   observation, INV-080/INV-149). Verify per install rather than assuming.
6. **If validation passes:** report pass for code generation.
7. **If the generator returns an empty response, an error, or does not respond within 30
   seconds:** report fail with a Fix_Instruction advising a check of MCP connectivity to
   `mcp.senzing.com:443`, then retry.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "code_generation": {"status": "passed|failed", "file": "verify_pipeline.[ext]"}
    }
  }
}
```

### Step 5: Build/Compile

Verify the generated code compiles or passes syntax checking. Enforce a 120-second timeout for
all build commands.

| Language | Build Command |
|----------|--------------|
| Python | `python3 -m py_compile src/system_verification/verify_pipeline.py` |
| Java | `javac src/system_verification/verify_pipeline.java` |
| C# | `dotnet build src/system_verification/` |
| Rust | `cargo build --manifest-path src/system_verification/Cargo.toml` |
| TypeScript | `tsc src/system_verification/verify_pipeline.ts --noEmit` |

⛔ **On Java, keep `verify_pipeline.java` and declare the top-level class package-private** — the
filename is `snake_case` and the idiomatic class name is not, and only a `public` top-level class is
filename-bound. The rule, its reason and the C# difference are in `../bootcamp-onboarding/ground-rules.md`
→ "File placement" (INV-237); do not restate them here (INV-300) and do not rename the file, which this table's
own tests pin.

1. Execute the build command for the chosen language.
2. **If the build exits with code 0:** report pass.
3. **If the build fails** (non-zero exit code): report fail including the first 50 lines of
   compiler error output. Generate a Fix_Instruction identifying common causes (missing SDK
   libraries, incorrect PATH, missing build tools) — and ⛔ **name a missing *non-SDK* dependency
   as its own cause, separately from the SDK ones.** An unresolved `javax.json` import reads as an
   install problem in the module that just finished verifying the install, which sends the
   bootcamper to re-check a working install. Step 4 item 5 should have caught it before this
   point; if it reaches here, resolve it there rather than reporting an install fault.
4. **If the build does not complete within 120 seconds:** terminate the process. Report fail
   with a timeout Fix_Instruction suggesting a check for dependency-resolution issues or
   network-dependent build steps.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "build_compilation": {"status": "passed|failed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 5a: Register the Synthetic Data Source Code

Register the synthetic verification data's source code(s) in the Senzing configuration
**before** loading (INV-083), so Step 6 does not fail with `SENZ2207: Data source code [...] does not
exist`. The default config seeded in Module 2 has no data sources registered, yet
the load below references the code(s) the Step 2 records carry, which must exist
first — so without this step every Module 3 run hits SENZ2207 on the first load attempt.

1. **Determine the source codes to register.** Collect the distinct `DATA_SOURCE`
   values present in the synthetic verification data
   (`src/system_verification/verification_data.jsonl` from Step 2) — normally just
   **VERIFY**. Never register a code that is not present in the data.
2. **Generate the registration code from the MCP server** (Agent Rule 7 — never
   hand-write it): call `sdk_guide(topic='configure')` (and `generate_scaffold` if
   it exposes a data-source registration workflow) in the language read from
   `programming_language` in `config/bootcamp_preferences.yaml` (never a hardcoded
   default). Save the result to
   `src/system_verification/register_data_sources.[ext]` (Agent Rule 5 — artifact
   isolation; INV-018). The generated code MUST:
   - Load the current default Senzing configuration.
   - Register each data source code from step 1 in that configuration.
   - Set the updated configuration as the new default, so `verify_pipeline` and every
     later SDK session see the codes. Use the exact config classes/methods returned by
     `sdk_guide`/`generate_scaffold` — never hardcode SDK names from memory.
   - Be **safe to re-run:** the whole sequence — load, register each code, export,
     register the config, replace the default config ID — must tolerate a second run,
     so re-running Module 3 or resuming mid-module still passes. ⛔ **Build that in;
     do not make it depend on catching an error (INV-263).** Registering an identical
     configuration returns the existing config ID rather than failing (Senzing release
     notes: *"Fix `G2ConfigMgr.addConfig` function to return success and the ConfigID
     if the configuration already exists"*), so re-runnability comes from the sequence,
     one call later than the per-code registration. **No route documents a raised error
     for re-registering a code, in any binding** —
     `get_sdk_reference(topic='parameters', filter='register_data_source',
     language='python')` returns the signature with no error condition (server
     **1.33.0, 2026-08-21**) — so a per-code catch is a permitted fallback, never the
     mechanism, and no binding's exception type is a contract (INV-002). The full
     reasoning, including the community-versus-official `search_docs` hazard, is stated
     once at `../module-06-data-processing/phaseA-build-loading.md` step 4a item 2
     (INV-183, INV-300); do not restate it here.
   - ⛔ **Pass `data_sources` so the registration snippet is primary, then substitute
     your codes into it** — the parameter selects the snippet and fills in nothing, so
     the returned code still carries the sample tuple. Locate it by `source_path`. Same
     step 4a item 2 for the detail and the citation.
3. **Build the registration code if the language requires it** (compiled languages
   — Java, C#, Rust, TypeScript), using the same per-language build command as
   Step 5. Enforce a 120-second build timeout.
4. **Execute** `register_data_sources.[ext]` with a 60-second timeout.
5. **If it completes with exit code 0:** report pass listing the source codes now
   registered, and record them in `config/data_sources.yaml` (INV-050).
6. **If it fails:** capture the error output, call `explain_error_code` for any
   SENZ codes, and report fail with remediation. Per Agent Rule 4, continue to
   Step 6 regardless; Step 6 keeps its generic SENZ handling as a fallback.
7. **If it does not complete within 60 seconds:** terminate the process and report
   fail with a timeout note.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "data_source_registration": {"status": "passed|failed", "sources_registered": ["VERIFY"]}
    }
  }
}
```

### Step 6: Data Loading

Execute the verification script to load the synthetic verification data
(`src/system_verification/verification_data.jsonl` from Step 2) into Senzing. The `VERIFY`
data source code was registered in Step 5a, so the load runs against a config that already
knows it; the SENZ handling below remains as a fallback.

1. Execute the generated `verify_pipeline.[ext]` script with a 120-second timeout, pointing it
   at `src/system_verification/verification_data.jsonl`.
2. **While executing:** display a progress indicator updated at least every 5 seconds showing
   records processed out of total expected.
3. **If the script completes with exit code 0:** confirm the number of records loaded exactly
   matches the synthetic record count generated in Step 2.
4. **If the record count matches:** report pass with the number of records loaded.
5. **If the script encounters an error:** capture error output, call `explain_error_code` for
   any SENZ codes, and report fail with remediation guidance.
6. **If fewer records load than expected without error:** report fail identifying records loaded
   versus expected. Instruct the bootcamper to check the synthetic data file integrity.
7. **If the script does not complete within 120 seconds:** terminate the process. Report fail
   indicating execution timed out.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "data_loading": {"status": "passed|failed", "records_loaded": <count>}
    }
  }
}
```

### Step 7: Deterministic Results Validation

Validate that entity resolution produced the outcome you defined **by construction** in Step 2.
Each validation check has a 30-second timeout.

1. Recall the expected outcome recorded in Step 2 (`module_3_verification.synthetic_data`): the
   expected entity count, the record IDs designed to **merge** into one entity, and the
   distractor record(s) designed to stay **singletons**. These come from the records you wrote,
   not from the MCP server.
2. Query the resolved entities (generate the query/report SDK code via `get_sdk_reference` +
   `sdk_guide`, or use `reporting_guide` for counts; never direct SQL) and perform the following
   validation checks. Execute ALL checks regardless of whether earlier checks pass or fail:

   **a) Entity count:**

   - Verify the total number of resolved entities equals the expected entity count from Step 2.

   **b) Merge cluster resolves to one entity:**

   - Verify the 2–3 records designed to match resolve to the **same** single entity ID.

   **c) Cross-record resolution:**

   - Verify the resolved entity count is strictly less than the total record count loaded,
     confirming that the merge cluster collapsed rather than every record loading as a singleton.

   **d) Distractor stays a singleton:**

   - Verify the distractor record(s) resolve to their own entity, separate from the merge cluster.

3. **If all checks pass:** report pass with the entity count and confirmation of the merge.
4. ⛔ **If a check fails, this is a DIAGNOSTIC, not a verdict on the install — there are two
   candidate explanations and you must tell them apart before reporting either.** Every other check
   in this module is an unambiguous statement about the installation; this one alone compares the
   engine against **a prediction the guide made**, so a mismatch means *either* the engine is wrong
   *or* the expectation was. Reporting the second as the first tells a bootcamper their working
   system failed, at the end of the module whose entire purpose is to tell them it works.

   **Ask the engine why, before concluding anything:**

   - For a cluster that did **not** merge, call `why_records` on the pair that stayed apart (or
     `why_entities` on the two entities), generating the call via `get_sdk_reference` +
     `sdk_guide` — never from memory. Report the **match key** and the **feature scores** it returns.
   - For an unexpected merge, do the same on the pair that joined.

   **Then decide, and say which you decided:**

   - **The engine explains its decision coherently** — e.g. a name variant scored below the
     threshold, or a record carried one fewer corroborating feature. Then **the expectation was
     wrong, and the install is fine.** Report it as an expectation mismatch: state the expected and
     actual counts, quote the engine's explanation, and say plainly that entity resolution behaved
     correctly. ⛔ **Do not report the system as having failed verification**, and do not tell the
     bootcamper to re-run the load — nothing is wrong with it. Fix the records per Step 2's
     constraints (the usual cause is a nickname, an initial, or an omitted feature that Step 2
     forbids) and re-run this step if the module's other checks all passed.
   - **The engine's explanation does not account for the difference**, or `why_*` itself errors —
     then this is a real finding. Report fail with expected versus actual, include the `why_*` output,
     and suggest re-running the load or confirming the synthetic data file loaded completely.

   ⚠️ **This check is reported separately from the other checks**, which are install checks. A
   mismatch the engine explains must not turn the module's overall result into a failure.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "results_validation": {"status": "passed|expectation_mismatch|failed", "entities": <count>, "matches_verified": <count>, "engine_explanation": "<the why_* match key and feature scores, on a mismatch>"}
    }
  }
}
```

⛔ **This check has THREE outcomes, and `expectation_mismatch` is the one the prose above
defines** (INV-229): the counts differed and the engine's own `why_*` output accounts for it, so
**the install is working and the prediction was wrong**. Recording that as `failed` is the false
report this step exists to prevent, and recording it as `passed` hides a mismatch worth telling the
bootcamper about — so neither of the two other values is available for it. Carry the engine's
explanation into `engine_explanation`: Step 9 reports it, and it is the most interesting thing the
module produces. `failed` is reserved for the case where the explanation does **not** account for
the difference, or `why_*` itself errored.

### Step 8: Database Operations

Verify read, write, and search operations against the Senzing database. Each operation has a
30-second timeout. Perform all operations through generated Senzing SDK code (via
`get_sdk_reference` + `sdk_guide`), never direct SQL against `database/G2C.db`.

1. **Verify write count:**
   - Confirm the record count returned by the Senzing engine matches the synthetic record count
     established during data loading (Step 6).
2. **Verify read by entity ID:**
   - Retrieve the merge-cluster entity (from Step 7) by its entity ID.
   - Confirm the response contains at least: the entity ID, one constituent record key (data
     source and record ID pair), and one name attribute from the original synthetic input.
3. **Verify search by attributes:**
   - Perform a search-by-attributes query using name and address attributes from one of the
     synthetic records.
   - Confirm the expected entity appears in the search results.
4. **If all operations succeed within 30 seconds each:** report pass with operations tested.
5. **If any operation fails or times out:** report fail identifying which operation failed
   (write, read, or search), the error received, and a Fix_Instruction referencing database
   configuration from Module 2.

**Checkpoint:** write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "database_operations": {"status": "passed|failed", "ops_tested": ["write", "read", "search"]}
    }
  }
}
```

**Agent behavior:** after Step 8 completes, proceed to Phase 2 (Report and Close) without asking
whether the bootcamper wants to continue: load `phase2-report-close.md`. That phase records System
Verification, purges the synthetic `VERIFY` data, and asks the single transition question to the next
selected module. When the **Truth Set visualization** is selected (`truthset_visualization` in
`selected_modules`; always true in Core), that next module is the separate, standalone Truth Set
visualization module (`../module-03b-truthset-visualization/`) — a first-class module (INV-086/INV-087)
that opens with its own module-start apparatus, then acquires and loads the Senzing Truth Set itself
and visualizes it. When it is not selected, the next module is Data collection.

## Success Criteria

System Verification is successfully complete when ALL of the following are true:

- Every installation checkpoint entry reports "passed" status (`mcp_connectivity`,
  `engine_initialization`, `sdk_initialization`, `code_generation`, `build_compilation`,
  `data_source_registration`, `data_loading`, `database_operations`).
- The `results_validation` checkpoint entry is reported separately and is not required to be
  "passed": `passed` and `expectation_mismatch` both complete the module, and only `failed` (a
  mismatch the engine's explanation does not account for) blocks it (INV-229, Step 7).
- The Verification Report is persisted to `config/bootcamp_progress.json` with a valid ISO 8601
  timestamp.
- The synthetic verification records are purged from the database (zero `VERIFY` entities remain).
- The gate 3→4 status is updated to "completed".
- The `## System verification` recap section is appended to `docs/bootcamp_recap.md` (the
  consolidated recap replaced the separate `docs/bootcamp_journal.md`; the narrative lives in the
  section's `### End-of-Module Summary` subsection).

(The Truth Set visualization module — run next when selected — owns its own `web_service`/`web_page`
checks, standalone snapshot, web-service termination, Truth Set purge, and `## Truth Set
visualization` recap section; see `../module-03b-truthset-visualization/`.)
