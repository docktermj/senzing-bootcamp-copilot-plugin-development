# Truth Set Visualization, Phase 2: Report and Close

Continues from Phase 1 (`phase1-visualization.md`). Follow `../bootcamp-onboarding/ground-rules.md`;
`🛑`/`⛔` are internal directives, never rendered.

> **Pre-advancement verification (agent self-check, internal directive):**
>
> Before offering to advance to the next module or marking this module complete, the agent MUST
> verify BOTH the checkpoints and the artifact on disk:
>
> - In `config/bootcamp_progress.json`: `truthset_visualization.checks.web_service.status` =
>   `"passed"` and `truthset_visualization.checks.web_page.status` = `"passed"`.
> - **The visualization artifact actually exists on disk:** the standalone snapshot written by the
>   visualization server (`docs/visualizations/truthset_verification.html`) is present and non-empty. This is
>   the hard guarantee that the visualization always happened; a checkpoint alone is not sufficient.
> - **The snapshot reflects the loaded Truth Set, not an empty template:** the visualization
>   server's build-only run (Phase 1, 2.2) MUST have built the entity model from a non-empty record
>   set (`records_total > 0`), consistent with the Truth Set record count loaded in Step 1
>   (1.2). A snapshot built from zero records is a blank page and does NOT satisfy INV-077.
>
> - **The snapshot agrees with the app the bootcamper saw:** its tab set matches the running
>   server's current tab set. Both are generated from the same source, so this is a cheap textual
>   comparison — count and compare the tab identifiers in the saved HTML against the server's.
>   ⛔ **Match on `id="tab-<name>"` — that is the marker the identifiers are written with**, and the
>   set is the six of INV-155 (`tab-graph`, `tab-stats`, `tab-matchkeys`, `tab-features`,
>   `tab-overlap`, `tab-probe`). ⛔ **A comparison that finds ZERO identifiers on both sides has not
>   passed — it has not run (INV-265).** On a dry run the first attempt matched `data-tab="…"`, found none in
>   either file, and reported "tab sets match: True"; `data-tab` appears **nowhere** in the
>   generated app. So assert a non-zero count on both sides before comparing them, and treat an
>   empty match as a broken check rather than agreement — a check that passes by comparing nothing
>   certifies exactly what it never looked at. A genuine
>   divergence means the visualization changed after the snapshot was built (Phase 1, 2.4b) and the
>   snapshot was never rebuilt.
>
> If the checkpoints are missing OR the snapshot file does not exist OR the snapshot was built from
> zero records, the agent MUST execute Steps 1–2 immediately (load `phase1-visualization.md`) and run
> the visualization server's build-only snapshot step (2.2) — whose `--records` file
> (`src/system_verification/truthset_data.jsonl`) matches the Truth Set loaded in Step 1
> (1.2) — so the artifact exists AND is non-empty. Do NOT offer advancement. Do NOT ask the
> module-transition question. Do NOT save progress. Produce the visualization first.
>
> If only the **tab sets diverge**, rebuild the snapshot via 2.2 while the data and server are still
> up, then re-verify. If the rebuild is not possible, warn the bootcamper that the saved copy shows
> an earlier version of the app and say how it differs — never let the recap claim a change the
> keepsake does not carry. This warning does not block module completion.

## Step 3: Visualization completeness check

Confirm that `config/bootcamp_progress.json` contains BOTH `web_service` and `web_page` checkpoint
entries under `truthset_visualization.checks` (this module's own checks). If either entry is missing
or has `"status": "failed"`:

- If missing: STOP. Do not close the module. Return to Phase 1 and execute Steps 1–2 fully by loading
  `phase1-visualization.md`.
- If failed: note the failure and proceed (failed is different from skipped/missing; it means the
  step was attempted).

## Step 4: Cleanup

Terminate the web service and purge the Truth Set data from the database.

⛔ **Ask the teardown gate first — do not proceed to the steps below until the bootcamper says
yes.** Per the server-lifetime contract in `visualization-api-reference.md` → "Server lifetime",
present this pinned question verbatim (INV-056) and end the turn on it:

⛔ **State what they are agreeing to FIRST, in the same turn but above the question, so the yes is
informed:** the live URL goes dead, the Truth Set records are removed from the database (exploring
further means reloading them), and the saved snapshot at
`docs/visualizations/truthset_verification.html` keeps every tab that renders from embedded data but
**not** the live `why`/`how`/`search` actions. This precedes the 👉 because nothing may follow it —
the question ends the turn — and because a disclosure arriving after the answer cannot inform it
(`../bootcamp-onboarding/ground-rules.md` → the 👉 protocol). The teardown is irreversible, so an
uninformed yes here is the costliest kind.

> 👉 **Ready for me to stop the visualization server and clean up the Truth Set data?**

*(Internal: end the turn on this question and wait.)*

**On "no" or "not yet":** leave the server running and the data in place, tell the bootcamper it is
still at its URL, and wait for their go-ahead. Do not re-ask on a loop.

⛔ **The Step 2.5 tour question does not authorize this.** "Are you ready to continue?" asks whether
the bootcamper is done with the guided tour; this asks whether an irreversible teardown may proceed.
They are different questions, so asking this one is **not** an INV-006 violation — INV-006 forbids
re-asking the same question, not asking a different one about a consequence the first never
mentioned. Do not reintroduce a "no separate confirmation gate" shortcut here.

⛔ **Order matters: everything that needs the data or the server happens BEFORE the purge, and the
purge is the LAST action of this module.** Once the Truth Set records are gone the snapshot cannot be
rebuilt and the live server cannot be re-served, so a missed rebuild or a missed capture becomes
permanent. Work through 1–4 in order; do not hoist the purge.

1. **Rebuild the snapshot if it is stale.** If the visualization changed after the snapshot was built
   (Phase 1, 2.4b) — or if Step 3's tab-set comparison flagged a divergence — re-run the build-only
   snapshot step **now**, while the records are still loaded. This is the last moment it is possible.

2. **Capture any missing screenshots from the live server.** Per
   `../bootcamp-onboarding/module-completion.md` → "Capturing visualization screenshots", the
   Search / Probe tab can only show real results against the running engine, so capture it here
   rather than from the static snapshot. Best-effort and non-blocking.

3. **Terminate the web service** — by process id, per `visualization-api-reference.md` → "Server
   lifetime" → "Identifying the server process":
   - Send a termination signal to the **pid recorded in Phase 1 (2.3)**, in
     `truthset_visualization.checks.web_service.pid`.
   - **Fall back to the port whenever the pid does not stop the server — a missing pid is only
     one of the two cases.** The other is a pid that *is* recorded, whose kill **exits 0**, and
     whose port stays bound: the recorded value was a subshell rather than the server (see
     `phase1-visualization.md` 2.3). Treat "the recorded pid is gone but the port still answers"
     exactly like "no pid was recorded" — the same port lookup resolves both, and this is the case
     that actually occurred on a dry run. Find the listener by
     the recorded port: `lsof -ti:<port>` on Linux/macOS,
     `Get-NetTCPConnection -LocalPort <port> | Select-Object -ExpandProperty OwningProcess` in
     PowerShell.
   - ⛔ **On the `docker` path both of those are host-shell routes and the container has neither
     tool (INV-223 still governs: terminate by pid, confirm the port)** — no `procps`, no `lsof`. Signal through the shell builtin
     (`docker exec <container> sh -c 'kill <pid>'`) using the pid INV-223 required the launch to
     record, and probe the port with `python3`, never with `lsof`. **The kill's exit status is not evidence the server stopped; the port is.** Full rule
     and the reason, stated once (INV-300):
     `visualization-api-reference.md` → "Server lifetime" → "Identifying the server process".
   - ⛔ **Never `pkill -f <script name>`** (or any other command-line pattern match). The pattern
     appears in the matching command's own command line, so it signals the invoking shell: on a dry
     run this killed the shell mid-teardown with exit code 144, leaving the records loaded, the
     purge below unrun, and the failure looking like the purge had crashed. The server is also
     built in the bootcamper's chosen language (INV-090), so in general there is no script name to
     match.
   - **Confirm the port is free** rather than assuming it: poll it for up to 5 seconds and stop as
     soon as nothing is listening. If it is still bound after 5 seconds, force-stop the process,
     re-check, and if it is *still* bound warn the bootcamper that the port may need manual release.
   - ⛔ Do not start step 4 until the port is confirmed free or the bootcamper has been warned — the
     purge is irreversible, and running it on the assumption that teardown succeeded is how a failed
     kill gets attributed to the purge.

4. **Purge the Truth Set data from the database** (the module's final action):
   - Remove the Truth Set records loaded in Phase 1 (CUSTOMERS/REFERENCE/WATCHLIST, or the CORD
     substitute's codes) from the Senzing database, using generated Senzing SDK code (via
     `get_sdk_reference` + `sdk_guide`); never direct SQL against `database/G2C.db`.
   - After purge, verify zero Truth Set entities remain while preserving any other database state.
   - If the purge fails: report a fail status identifying which records could not be removed, with a
     Fix_Instruction advising the bootcamper to re-run cleanup or manually reset the database.

5. **Retain visualization artifacts:** the standalone snapshot
   (`docs/visualizations/truthset_verification.html`), the generated visualization server under
   `src/server/` (when the chosen language is not Python), and any generated load/registration code
   under `src/system_verification/` remain in place for reference.

**Checkpoint:** write to `config/bootcamp_progress.json`.

## Step 5: Module Close

Complete this module using the standard **Module Completion** process in
`../bootcamp-onboarding/module-completion.md`. Record it as a first-class module in the order the
bootcamper experienced it (immediately after System verification), so it does not depend on
graduation's reconcile backfill (INV-085/INV-086/INV-087):

1. **Update progress state.** Add `truthset_visualization` to `modules_completed` (a module name
   token, not a number), placed after `system_verification`. Set `current_module` to the next module
   in `selected_modules` and `current_step` to `null`. All idempotent (do not duplicate).
2. **Append the recap section** to `docs/bootcamp_recap.md`, name-based and append-only (INV-085):
   `## Truth Set visualization — {timestamp}` with the four subsections (Information Shared,
   Questions & Responses, Actions Taken, End-of-Module Summary): capture the Truth Set acquisition/load, the
   interactive visualization and standalone snapshot, and — if screenshots were captured — the
   embedded `![…](visualizations/…png)` image(s) in Actions Taken — the path is relative to
   `docs/bootcamp_recap.md`, so `visualizations/…` and never `docs/visualizations/…` (INV-161;
   the recap already lives in `docs/`, so a `docs/`-prefixed path resolves to `docs/docs/…` and
   embeds nothing). Then save this module's B-roll entry under `truthset_visualization`, per
   `module-completion.md` 2e, listing the same screenshots by their project-relative
   `docs/visualizations/…` paths.
3. **Present the completion line + end-of-module summary** (INV-032):
   `✅ Module complete: Truth Set visualization` and its four-part summary, per `module-completion.md`
   Step 3. (This module's module-start banner/journey/before-after/step-overview were already shown at
   its module start in Phase 1, so only its close is presented here.)
4. **Transition to the next module:** ask the single transition question (once), then on an
   affirmative reply **(INV-272) acknowledge it in one short visible line naming that module before invoking
   its skill** (the ground rules' acknowledge clause and
   `../bootcamp-onboarding/module-completion.md` Step 4 own the ordering — a skill invocation and its
   file reads emit nothing the bootcamper can see), then produce the next module's start banner,
   journey map, before/after framing, and step overview per the ground rules.

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)*

**Checkpoint:** write to `config/bootcamp_progress.json`.

**Success indicator:** ✅ The standalone snapshot exists (built from a non-empty Truth Set) + the
live app served its endpoints + the web service is terminated + the Truth Set data is purged +
`truthset_visualization` is recorded in `modules_completed` with its own recap section.
