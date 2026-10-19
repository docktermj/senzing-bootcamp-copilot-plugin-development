# Module 3, Phase 2: Report and Close (steps 9–11)

Continues from Phase 1 (`phase1-verification.md`). Follow `../bootcamp-onboarding/ground-rules.md`;
`🛑`/`⛔` are internal directives, never rendered. This closes **System Verification** only; the Truth
Set visualization is a separate, standalone module that runs next when selected and has its own close.

## Step 9: Verification Report Generation

Generate a structured summary of the System Verification checks.

1. Compile the results from the System Verification checkpoint entries — the installation checks
   (`mcp_connectivity`, `engine_initialization`, `sdk_initialization`, `code_generation`,
   `build_compilation`, `data_source_registration`, `data_loading`, `database_operations`) and,
   reported separately, `results_validation` — into a single Verification Report.
   (The Truth Set visualization is a separate, standalone module; its `web_service`/`web_page`
   checks and the visualization artifact belong to that module's own close, not this report.)

2. For each check, record:
   - Status — `passed` or `failed` for the **installation checks**; `results_validation`
     additionally takes `expectation_mismatch` (INV-229)
   - Duration in milliseconds (where applicable)
   - Any relevant metadata (record counts, entity counts, file paths, ports)

   ⛔ **(INV-229) The installation checks decide this module's verdict; `results_validation` does
   not.** It is the one check that compares the engine against **a prediction this guide made**
   (`phase1-verification.md` Step 7), so its mismatch means either the engine is wrong *or* the
   expectation was — and Step 7 has already told them apart by asking the engine why. An
   `expectation_mismatch` there means **the install is working**; pooling it with the install checks
   is what would tell a bootcamper their working system failed, at the end of the module whose
   entire purpose is to tell them it works.

3. **If all the installation checks passed:** display a success banner — including when
   `results_validation` is `expectation_mismatch`, because the environment *is* verified:

   ```text
   ╔══════════════════════════════════════════════════════════╗
   ║  ✅ SYSTEM VERIFICATION COMPLETE                         ║
   ║                                                          ║
   ║  Your environment is verified and ready for subsequent   ║
   ║  modules.                                                ║
   ║                                                          ║
   ║  Nothing for you to do here — you're all set to          ║
   ║  continue.                                               ║
   ╚══════════════════════════════════════════════════════════╝
   ```

   ⛔ **(INV-229) The banner does not claim "all checks passed"** — it claims what the install checks
   establish, which is that the environment works. It is displayed unchanged on an
   `expectation_mismatch`, so the wording must stay true in that case.

   **Report `results_validation` beneath the banner, on its own line, always** — it is the one
   check the banner does not speak for:

   - `passed` → "Results validation: passed — {n} entities, as predicted."
   - `expectation_mismatch` → say the install is fine **and** what actually happened: the expected
     and actual entity counts, and the engine's own explanation from `engine_explanation` (the match
     key and feature scores `why_*` returned). Frame it as the interesting result it is — the engine
     made a defensible call the prediction did not anticipate — and ⛔ **never as something for the
     bootcamper to fix or re-run.** Step 7 has already decided this is not a failure.
   - `failed` → the install-check failure path below applies; Step 7 reaches this only when the
     engine's explanation does **not** account for the difference.

4. **If ANY of the installation checks failed** (or `results_validation` is `failed`, which
   Step 7 reserves for an unexplained mismatch): display a failure summary listing each failed check
   with its Fix_Instructions:

   ```text
   ⚠️  SYSTEM VERIFICATION: FAILURES DETECTED

   Failed checks:
   • <check_name>: <error_summary>
     Fix: <Fix_Instruction>

   Please resolve the issues above and re-run system verification.
   ```

   ⛔ **An `expectation_mismatch` MUST NOT appear here.** There is nothing to resolve and nothing to
   re-run: this banner would tell a bootcamper with a working install to redo the module that just
   proved it works (INV-229).

5. **Persist the report** to `config/bootcamp_progress.json` with the following structure:

   ```json
   {
     "module_3_verification": {
       "timestamp": "<ISO 8601 timestamp>",
       "status": "passed|failed",
       "checks": {
         "mcp_connectivity": {"status": "passed|failed", "duration_ms": 0},
         "engine_initialization": {"status": "passed|failed"},
         "sdk_initialization": {"status": "passed|failed", "duration_ms": 0},
         "code_generation": {"status": "passed|failed", "file": "verify_pipeline.[ext]"},
         "build_compilation": {"status": "passed|failed", "duration_ms": 0},
         "data_source_registration": {"status": "passed|failed", "sources_registered": ["VERIFY"]},
         "data_loading": {"status": "passed|failed", "records_loaded": 0},
         "results_validation": {"status": "passed|expectation_mismatch|failed", "entities": 0, "matches_verified": 0, "engine_explanation": ""},
         "database_operations": {"status": "passed|failed", "ops_tested": ["write", "read", "search"]}
       },
       "fix_instructions": []
     }
   }
   ```

   - The `timestamp` field SHALL use ISO 8601 format (e.g., `2026-05-13T10:30:00Z`).
   - The `fix_instructions` array SHALL contain one entry per failed check, each with the check
     name and remediation text. ⛔ **An `expectation_mismatch` contributes NO entry** — there is
     nothing to remediate.
   - If verification was interrupted, mark unexecuted checks as `"status": "skipped"`.
   - ⛔ **The module-level `status` is set from the installation checks only** (INV-229). A
     healthy install MUST NOT be recorded as a failed module because a prediction was wrong:
     graduation and the resume bundle read this file rather than the prose above, so a wrong value
     here outlives the module.
   - On an `expectation_mismatch`, `engine_explanation` carries the match key and feature scores
     `why_*` returned (`phase1-verification.md` Step 7). It is what makes the outcome checkable
     later; an empty string with a mismatch status is an incomplete record.

   Verification runs against synthetic data that is deterministic **by construction** (Step 2), so
   there is no external Truth Set provenance to record for System Verification.

6. **If all the installation checks passed:** proceed to Step 10 (Cleanup) — including when
   `results_validation` is `expectation_mismatch`.
7. **If any installation check failed** (or `results_validation` is `failed`): do NOT proceed to
   cleanup. Advise the bootcamper to fix the issues and re-run System verification from the
   beginning.

   ⛔ **Cleanup MUST NOT be gated on an `expectation_mismatch`.** Step 10 is the only place the
   synthetic `VERIFY` records are purged, and INV-131 makes that teardown the module's last action —
   skipping it leaves them in the database on the way into the next module, which is a real cost paid
   for a prediction that was merely wrong.

**Checkpoint:** write step 9 to `config/bootcamp_progress.json`.

## Step 10: Cleanup

Clean up the synthetic verification data from the database. System Verification starts no web service,
so there is nothing to terminate here (any web service belongs to the separate Truth Set
visualization module, which stops its own at its close).

1. **Display the test-only artifact message:**

   ```text
   ℹ️  All files in src/system_verification/ are test-only artifacts.
      Real project work begins in subsequent modules.
      These files are retained for reference.
   ```

2. **Purge verification data from the database:**
   - Remove the synthetic `VERIFY` records loaded in Phase 1 from the Senzing database, using
     generated Senzing SDK code (via `get_sdk_reference` + `sdk_guide`); never direct SQL against
     `database/G2C.db`.
   - After purge, verify zero `VERIFY` entities remain while preserving any other database state.
   - If the purge fails: report a fail status identifying which records could not be removed.
     Provide a Fix_Instruction advising the bootcamper to re-run cleanup or manually reset the
     database.

3. **Retain verification artifacts:** all generated files in `src/system_verification/` remain in
   place for reference.

**Checkpoint:** write step 10 to `config/bootcamp_progress.json`.

## Step 11: Module Close

Complete **System Verification** using the standard **Module Completion** process in
`../bootcamp-onboarding/module-completion.md`. This module records only itself; the Truth Set
visualization is a separate, standalone module that records itself at its own close
(INV-085/INV-086/INV-087):

1. **Update progress state.** Add `system_verification` to `modules_completed` (a module name token,
   not a number). Set gate 3→4 status to "completed", `current_module` to the next module in
   `selected_modules`, and `current_step` to `null`. All idempotent (do not duplicate).
2. **Append the recap section** to `docs/bootcamp_recap.md`, name-based and append-only (INV-085):
   `## System verification — {timestamp}` (Information Shared, Questions & Responses, Actions Taken,
   End-of-Module Summary) — capture **what each check actually returned** against the synthetic
   `VERIFY` data: the installation checks with their status, and results validation with its
   outcome. On an `expectation_mismatch`, record the expected and actual entity counts **and** the
   engine's explanation, and state that the install was verified. The narrative goes in the
   `### End-of-Module Summary` subsection (the consolidated recap replaces the separate journal file).

   ⛔ **Never write that every check passed unconditionally** (INV-229) — no "all checks passed"
   line that counts `results_validation` among them. This is the keepsake, so a sentence that is
   false on the `expectation_mismatch` path is false permanently — and the mismatch
   is the more interesting record of the two: it is the engine explaining a real resolution decision
   on the bootcamper's own machine.

   Then save this module's B-roll entry under `system_verification`, per `module-completion.md`
   2e.
3. **Present the completion line + end-of-module summary** (INV-032): `✅ Module complete: System
   verification` and its four-part summary, per `module-completion.md` Step 3.
4. **Transition to the next module:** ask the single transition question; on an affirmative reply,
   **(INV-272) acknowledge it in one short visible line naming that module before invoking its skill** (the
   ground rules' acknowledge clause and `../bootcamp-onboarding/module-completion.md` Step 4 own the
   ordering — a skill invocation and its file reads emit nothing the bootcamper can see), then
   produce the next module's start banner, journey map, before/after framing, and step overview per
   the ground rules. (When the Truth Set visualization is selected, the next module is it; otherwise
   it is Data collection.)

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)*

**Checkpoint:** write step 11 to `config/bootcamp_progress.json`.

**Success indicator:** ✅ System verification passed or explicitly skipped by the bootcamper. The
installation checks passed, with results validation reported separately + database purged of the
synthetic `VERIFY` data + `system_verification` completion recorded in the progress file and
recap. (The visualization checks `web_service`/`web_page`, the Truth Set purge, and web-service
termination belong to the separate Truth Set visualization module's close.)
