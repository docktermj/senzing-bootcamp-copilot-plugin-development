# Module 6, Phase D: Validation (steps 21–28)

Continues from Phase B (single source) or Phase C (multi-source). Follow the ground rules;
`🛑`/`⛔` are internal control directives. Entity queries use SDK code generated via
`generate_scaffold` / `get_sdk_reference`, never direct SQL against `database/G2C.db`. Counts
and stats come from `reporting_guide` — **name the topic**:
`reporting_guide(topic='evaluation', language='<chosen_language>')` for the single-pass export
statistics this phase needs, `reporting_guide(topic='export', language='<chosen_language>')` for
extraction patterns.

⚠️ **`topic='reports'` is not this bootcamp's route.** Its SQL targets an analytical data mart
(`sz_dm_entity`, `sz_dm_record`, `sz_dm_relation`, `sz_dm_report`) that the bootcamp never builds —
the tool says so itself, in that response's own `data_mart_framing.warnings[0]`: *"This is NOT a
Senzing product and NOT part of the Senzing SDK. It does not exist out of the box. The sz_dm_ prefix
makes it LOOK like an official Senzing product; it is not — the prefix is only used in this
example."* (verified on MCP server 1.37.14, 2026-09-28).
It is the production-reporting answer, not the evaluation one, so asking for it here returns
well-formed SQL that cannot run against a single-database SQLite workspace. If you are already
looking at that response, the usable subset is its `Validation:` patterns, which run against
**exported entity JSON** rather than the data mart.

## Single-source validation (always)

## 21. Validate match accuracy

Review the entity resolution results:

- Query a sample of known records (SDK method `get_entity_by_record_id`) to check how they
  resolved
- Look for expected matches, are records that should match resolving to the same entity?
- Look for false positives, are unrelated records being incorrectly merged?
- Look for false negatives, are records that should match resolving to separate entities?
- If match accuracy is poor, revisit data quality (Module 5) or mapping before proceeding

Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')` to
generate SDK code that retrieves sample entities for review. Use
`get_sdk_reference(topic='parameters', filter='why_entities', version='current')` to explain why
records matched. (There is no direct entity-query MCP tool, entity lookup and why-matched are
done through generated SDK code.)

**Checkpoint:** write step 21.

## 22. Run basic UAT for single-source

Validate that the loaded data meets business expectations:

- Verify record counts, does the number of loaded records match expectations? (Use
  `reporting_guide(topic='evaluation', language='<chosen_language>')` for counts — not `topic='reports'`; see the header note.)
- Spot-check entity resolution, pick 5–10 known entities and confirm they resolved correctly
- Document any issues found in `docs/uat_results.md`
- If critical issues are found, fix and reload before proceeding

**Checkpoint:** write step 22.

## Cross-source validation (conditional, 2+ sources loaded)

Only present steps 23–27 when the bootcamper has loaded 2 or more data sources. For
single-source bootcampers, skip directly to step 28 (Document results).

## 23. Validate cross-source results

Validate: record counts match expectations, cross-source entities exist, no unexpected data
loss, error logs clean. Use `reporting_guide(topic='graph', language='<chosen_language>', version='current')` for
network-graph patterns.

⛔ **Before treating a low or zero cross-source entity count as a finding about the data, read how
the data was selected.** If Module 4 reduced any source, `config/data_sources.yaml` records the
sampling method and the reason for it. A **random** slice of 2+ sources removes cross-source overlap
by construction — one bootcamp got zero cross-source matches from a load reporting 1,147 records,
no errors, redo drained and 94–100% quality — so a near-zero count there is an artifact of the
sample, not a property of the sources, and the remedy is an overlap-preserving re-sample (Module 4
→ "Sampling rule"), not a mapping change. Say which it is; never report "Senzing found no
cross-source matches" without checking this first.

Sample 15–25 entities that contain records from multiple data sources and verify they represent
the same real-world person or organization. Check cross-source matches and spot-check
single-source entities to confirm no cross-source matches were missed.

This is validation work only — do **not** produce a visualization here. All results and
cross-source relationship visualization is offered once, in Module 7 (Query, Visualize and
Discover), where it is delivered as tabs of the single interactive app (Entity Graph — including
its relationship-subgraph mode — and Cross-Source) rather than a separate static page (INV-104). Module 6 no longer offers a
cross-source visualization, to avoid a duplicate/misplaced offer.

**Checkpoint:** write step 23.

## 24. Validate cross-source results quality

Use `reporting_guide(topic='evaluation', language='<chosen_language>', version='current')` for the 4-point ER evaluation
framework and `reporting_guide(topic='quality', language='<chosen_language>', version='current')` for precision/recall
metrics.

Validate: match accuracy (query known records via the generated SDK code / SDK method
`get_entity_by_record_id`), false positives (incorrect merges), false negatives (missed
matches), data completeness. If accuracy is poor, revisit Module 5 mapping.

**Checkpoint:** write step 24.

⛔ **Steps 21–24 ask nothing, so this turn does not end here** — validation results and evidence
tables are the output most likely to be mistaken for a turn ending, because they conclude something
(`ground-rules.md` → "A results presentation is not a turn ending", INV-225). Continue in the same turn to
the next step that actually asks.

## 25. Execute UAT with business users

⛔ **Branch on scenario provenance first — never ask a bootcamper to convene business users for a
business case the bootcamp invented (INV-006/INV-012).** Read `docs/business_problem.md`: if it carries the
bootcamp-generated marker `> 🤖 Bootcamp-generated business case` (the Business Case Offer was
accepted in Module 1), or otherwise records no real stakeholders, take 25a. Otherwise take 25b.

### 25a. Bootcamp-generated scenario (marker present, or no real stakeholders recorded)

There are no business users to involve, so **do not ask** the involvement question
(INV-006/INV-012). State briefly that the scenario is bootcamp-generated and that you will
self-direct the UAT, then spot-check 5–10 cross-source entities, document the findings in
`docs/uat_results.md`, and proceed to step 26.

⛔ **This branch correctly ends with NO 👉 question, and must stay that way.** Do not borrow 25b's
question to balance the two branches — manufacturing a question here breaches INV-006 in the
opposite direction. This step is not a turn ending on this path: continue in the same turn to the
next step that actually asks (`ground-rules.md` → "A results presentation is not a turn ending",
INV-225).

### 25b. Real business problem with real stakeholders

**Only when `docs/business_problem.md` records real stakeholders and carries no
`> 🤖 Bootcamp-generated business case` marker** — offer to involve business users. Pin the
question verbatim (INV-056):

👉 **Would you like to involve business users in testing the cross-source results?** (respond yes or no)

*(Internal: end the turn on this question and wait.)*

- **Yes:** share cross-source match examples, collect feedback, document in
  `docs/uat_results.md`.
- **No:** spot-check 5–10 cross-source entities and document findings in `docs/uat_results.md`.

**Checkpoint:** write step 25.

## 26. Get stakeholder sign-off

Create `docs/results_validation.md` with match-quality metrics (true/false positive/negative
rates) and business validation results (test cases passed, issues, resolution plan).

**Checkpoint:** write step 26.

## 27. Document validation results

Save all findings to `docs/results_validation.md`: total records loaded, entities created,
cross-source match rate, UAT results, stakeholder feedback/sign-off status. This becomes the
validation baseline before Module 7.

Update `docs/loading_strategy.md` with: final load order and rationale, per-source statistics,
cross-source match summary, issues and resolutions, recommendations for future loads.

⛔ **The per-source statistics written here are reconciled figures or they are labeled as
unreconciled — never bare numbers.** (INV-243/INV-245) This document outlives the session and is
read as the record of what was loaded, so an unchecked count written into it is the hardest of all
these sites to correct later: nothing downstream re-derives it, and by the time anyone doubts it
the load is long finished.

⛔ (INV-245) **There are four reconciliation outcomes to write here, not two** —
`phaseB-load-first-source.md` Step 7's two-stage reconciliation, the canonical statement; do not
restate it here (INV-300). What this document adds is how each is written. A source recorded
`expected_delta` is written as a **reconciled** result carrying its figures and every chain step
with the record it cites (the `sample:` block, a subset record, the mapping specification) — never
as a failure, and never as a bare matching count. A source recorded `unexplained_delta` is written with every figure from its
`issues` entry and labeled **unverified** — not as a failure, since every record it was given
loaded, and not as a pass, since its gap to the collected file has no cited cause. A load that
legitimately changed the record count is the visible consequence of a sampling or mapping decision,
and this document is the place a Bootcamper will look for it a month later; recording it as
`failed` tells them a clean load broke, and recording it as a plain pass hides that anything happened
at all.

**Checkpoint:** write step 27.

## Document results and complete (always)

## 28. Document results

Record the validation findings:

- Save validation results to `docs/results_validation.md`
- Include: total records loaded, entities created, match rate, any issues found and their
  resolution
- This becomes the baseline for comparison

The entity counts, match statistics and sample resolved entities are the **Merge Statistics** tab of
the app offered in the **Query, Visualize and Discover** module (Module 7, Step 3c — the consolidated
visualization gate), where all results visualization lives — Module 6 does not offer it, to avoid a
duplicate offer. Module 6 offers **no** visualization at all: the cross-source relationship view
(step 23) is also delivered in Module 7's single interactive app (INV-104), as its **Entity Graph**
tab (including its "Show only entities with relationships" mode) and its **Cross-Source** tab
(INV-155), not as a separate Module 6 page.

**Checkpoint:** write step 28.

## Recovery from failed load

If loading fails partway through:

1. **Check what loaded**, query known RECORD_IDs (via generated SDK code) to see if they exist.
2. **Decide, wipe and restart vs. resume:**
   - **Wipe and restart:** restore from the `database/G2C.db` backup, fix the issue, re-run.
   - **Resume:** modify the loading program to skip already-loaded records.
3. **If the database is corrupted**, restore from backup. If no backup, delete
   `database/G2C.db` and re-run the Module 2 config.
4. **Common causes:** disk full, out of memory, invalid records, network timeout.

(The Kiro backup/restore helper `scripts/restore_project.py` is a later porting phase; restore
from your own `database/G2C.db` backup for now.)

### Multi-source recovery (Phase C)

If a source fails during orchestration, present three options:

1. **Skip and continue:** mark it failed, continue with remaining sources.
2. **Retry after fix:** pause, fix the issue, retry the failed source.
3. **Restore and restart:** restore from backup, fix, restart orchestration.

## Match-key audit (run before the iterate-vs-proceed gate)

Every mapping gate the bootcamp runs before this point is **static, single-source, and
structural** — the analyzer, the verbatim check, the routing report, the quality score. None of
them evaluates *meaning*. So a whole defect class survives them: two source fields that measure
different things mapped to the same Senzing feature.

(Those gates also have blind spots of their own, so a finding from one is not automatically a defect
in the mapping. The verbatim check in particular **harvests source *values* only**, so it reports any
emitted value it cannot harvest — a **boolean** source value, or a value derived from a source **field
name** rather than a field value — however that value was emitted (server 1.32.2, verified
2026-07-29). If a violation list came into this module unresolved for one of those reasons, it is a
checker limitation and not a mapping error; see
`../module-05-data-quality-mapping/phase2-data-mapping.md` → the verbatim-check block, which also
covers what to record. Numeric source values used to fail this way and **no longer do** — that was
fixed upstream in 1.32.2 — so do not carry forward a numeric exemption from an older run without
re-running the check.) Senzing is then told a conflict exists where
none does, and it **suppresses legitimate merges**. All gates green, matches quietly lost.

This is the reading that catches it. It also matches the Senzing reporting guidance directly —
`reporting_guide(topic='quality', language='<chosen_language>')`'s anti-patterns say *"Only checking aggregate statistics for
quality … Aggregate stats hide errors. Always sample and manually review specific entities"* —
which is exactly the gap the UAT percentages below leave open.

1. **Read the match keys** from the loaded results using generated SDK code (never direct SQL
   against `database/G2C.db`). Per `get_sdk_reference(topic='response_schemas')` there are
   **two reads, and they need two different methods** — confirm both via MCP rather than from
   this file (a sourcing floor):

   | What | Where | How to obtain it |
   |---|---|---|
   | Per-record match keys | `RESOLVED_ENTITY.RECORDS[].MATCH_KEY` | a bulk export (`export_json_entity_report`) is fine |
   | Relationship match keys | `RELATED_ENTITIES[].MATCH_KEY` | the same export **when its rows carry `RELATED_ENTITIES`** — dump one row to check; otherwise **per-entity** `get_entity_by_entity_id` / `get_entity_by_record_id`, or `find_network_by_entity_id` |

   ⚠️ **Whether an export carries `RELATED_ENTITIES` depends on the flag set, not on the method — so
   dump one row and route on what you see.** Do not assume either answer:

   - `reporting_guide(topic='evaluation', language='<chosen_language>')` documents the export-with-defaults case directly
     (verified 2026-07-28): *"Use `export_json_entity_report` with `SZ_EXPORT_DEFAULT_FLAGS` … Each
     exported row is a JSON object containing `RESOLVED_ENTITY` … **and `RELATED_ENTITIES[]`** (with
     `ENTITY_ID`, `MATCH_LEVEL_CODE`, `MATCH_KEY`, `ERRULE_CODE`, `RECORD_SUMMARY[]`)"*, and its
     worked `export_with_stats` pattern computes relationship categories in a **single pass over the
     export**. A live run on SDK 4.3.3 with `SZ_EXPORT_DEFAULT_FLAGS` confirmed it: the first row's
     top-level keys were `[RESOLVED_ENTITY, RELATED_ENTITIES]`.
   - A different bootcamp session, on the same SDK version, assembled its flags from
     `SZ_ENTITY_INCLUDE_*` members and got rows with **no `RELATED_ENTITIES` key at all** and no
     error. Both observations are real; the flag set is the variable. Note that the
     relationship-detail flags (`SZ_ENTITY_INCLUDE_ALL_RELATIONS` and its members) do **not** list
     the export methods in their `applies_to`, which is why composing a flag set out of those alone
     is the case that comes back without relationships — but that does not make the export incapable,
     because `SZ_EXPORT_DEFAULT_FLAGS` is itself an export-family flag documented as matching *"the
     normal entity defaults"*, and those defaults include the relationship-inclusion members.

   **So: start from `SZ_EXPORT_DEFAULT_FLAGS`, dump one row, and read its top-level keys before you
   choose a reader.** `RELATED_ENTITIES` present → do both reads in one export pass.
   `RELATED_ENTITIES` absent → keep the per-record read on the export and use a per-entity reader
   (or `find_network_by_entity_id`) for the relationship half. Never write the audit as if the answer
   were settled in either direction (INV-115/INV-149: the dumped row is the authority).

   ⚠️ **If you do read relationships from the export, deduplicate.** Per
   `reporting_guide(topic='evaluation', language='<chosen_language>')`: *"Each relationship appears in BOTH entities'
   `RELATED_ENTITIES` — deduplicate by sorting `(min_id, max_id)` pairs and using a set."* Skipping
   this double-counts every relationship, which inflates a suppressor share rather than emptying it —
   a wrong number that still looks plausible. The same guidance notes export iteration is
   O(all entities): fine at bootcamp scale, and the reason the single-pass form is worth having
   instead of one call per entity.

   The two export flag families also do different jobs. `SZ_EXPORT_INCLUDE_*` selects **which
   entities** appear as rows (`..._POSSIBLY_SAME`, `..._DISCLOSED`, `..._ALL_HAVING_RELATIONSHIPS`
   — all row filters). It does **not** select what detail a row carries: an export flagged with
   only those succeeds and yields rows containing nothing but `ENTITY_ID`. The Senzing reporting
   guidance names this as an anti-pattern — *"Exporting without proper flags … Use
   `SZ_EXPORT_DEFAULT_FLAGS` or specify exactly which flags you need. Missing flags means missing
   data in your reports."* — so start from `SZ_EXPORT_DEFAULT_FLAGS` and add row filters, rather
   than OR-ing row filters alone.

   ⚠️ **Confirm a composite exists on *your* binding before using it.** `SZ_EXPORT_ALL_FLAGS` is
   documented for the export methods, but it comes from the Java SDK's flag enum and is **absent
   from the Python binding's `SzEngineFlags`** in 4.3.3 (`AttributeError`). Flag *names* are not
   uniformly available across bindings, so confirm the name for the bootcamper's language instead
   of copying it from cross-language documentation, and ask MCP first.
   `get_sdk_reference(topic='flags', filter='<method>', language='<chosen_language>')` lists the
   flags documented for the method, but it does not narrow that list by binding: with
   `language='python'` it still returns `SZ_EXPORT_ALL_FLAGS`, and only its `source_file`
   (`fallback:java-sdk-SzFlag-enum`) shows the Java origin (MCP server 1.37.16, 2026-09-30). For
   availability, search the binding's own flag reference, naming its flag class:
   `search_docs(query='<binding flag class> <flag name>')`. For Python,
   `search_docs(query='senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS')` returns the
   `SzEngineFlags` member list, which has no `SZ_EXPORT_ALL_FLAGS`. A query that names only the
   flag can rank another binding's class first, so if the top hits document a different
   binding's flags, re-query with your binding's class or module name rather than reading their
   list as yours. Only where neither route answers, fall back to introspecting the installed
   binding (`dir(SzEngineFlags)`) (INV-132).
   <!-- MCP-NEGATIVE: get_sdk_reference(topic='flags', filter='export_json_entity_report', language='python') — the flag list is not narrowed by binding: SZ_EXPORT_ALL_FLAGS is still listed, its entry identical without the language argument, and only its source_file (fallback:java-sdk-SzFlag-enum) shows the Java origin; language narrows method_signatures only — owner: search_docs(query='senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS') IS the route that carries a binding's own flag reference, and returns the Python SzEngineFlags member list, so availability is answered there rather than absent (routing negative) — server 1.37.16, 2026-09-30 -->
   <!-- MCP-NEGATIVE: search_docs(query='senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS') — the Python SzEngineFlags member list has no SZ_EXPORT_ALL_FLAGS: the alphabetical list runs from SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES directly to SZ_EXPORT_DEFAULT_FLAGS — owner: search_docs IS the corpus route that serves the Python SDK reference (garage.senzing.com/sz-sdk-python/senzing.html, section szengineflags), so its member list is the answer rather than a miss (absence negative) — server 1.37.16, 2026-09-30 -->

   A worked expression for a detail-carrying export in Python — start here rather than assembling
   row filters and hoping:

   ```python
   from senzing import SzEngineFlags

   # SZ_EXPORT_DEFAULT_FLAGS carries the per-entity detail; add row filters only to widen
   # WHICH entities appear. Re-confirm both names via MCP rather than from this file (INV-080; a sourcing floor) — this is a
   # worked example, not a substitute for the lookup.
   flags = (
       SzEngineFlags.SZ_EXPORT_DEFAULT_FLAGS
       | SzEngineFlags.SZ_EXPORT_INCLUDE_ALL_ENTITIES
   )
   handle = sz_engine.export_json_entity_report(flags)
   try:
       row = sz_engine.fetch_next(handle)   # dump this ONE row and read it before parsing
       print(row)
   finally:
       sz_engine.close_export_report(handle)   # close_export_report, not close_export
   ```

   Before parsing the whole reader output, **dump one raw row** and confirm the fields the parser
   expects are actually present (INV-115). This is the check that turns "4,587 rows exported
   successfully, all containing only `ENTITY_ID`" from a wasted validation pass into one line of
   output — and it is the same check that decides which reader the relationship half needs, above.
   Print the row's **top-level keys**, not just the row, so the `RELATED_ENTITIES` question is
   answered explicitly rather than by eyeballing a wall of JSON:

   ```python
   first = json.loads(row)
   print("top-level keys:", sorted(first))
   print("carries RELATED_ENTITIES:", "RELATED_ENTITIES" in first)
   ```

2. **Tabulate the suppressors — into THREE buckets, each with its own denominator.** In a match key,
   `+` means the feature **contributed** to the match and `-` means it **detracted** (MCP-confirmed
   via `response_schemas` on `RESOLVED_ENTITY.RECORDS[].MATCH_KEY`, whose description reads
   *"Features that matched: + means contributed, - means detracted"* — server **1.36.0**,
   2026-09-02).

   **Split each key into signed features by this rule, in this order.** The obvious split on `+`/`-`
   misreads disclosed-relationship keys, and the relationship bucket is exactly where they appear.
   One rule serves all three buckets:

   1. Remove each parenthesized role, `(...)` including its contents, **first**, so role text such
      as `CO-OWNER` or `OWNS 60%` cannot yield features.
   2. **A backslash makes the next character part of the name.** This covers `\-` inside a domain
      name, and would cover any other escaped character the same way.
   3. **Split on the unescaped `+` and `-`.** Each feature takes the sign that precedes it, and only
      `-` features are counted as suppressors.
   4. **Report feature names with the escape removed** (`OPEN-SANCTIONS`, not `OPEN\-SANCTIONS`).

   Worked example: `+ADDRESS+OPEN\-SANCTIONS(ACTING FOR OR ON BEHALF OF:)-DOB-TAX_ID` →
   `+ADDRESS`, `+OPEN-SANCTIONS`, `-DOB`, `-TAX_ID` — **two** suppressors. Split on every `-`
   instead, and `SANCTIONS(ACTING FOR OR ON BEHALF OF:)` is counted as a suppressed feature.

   The role notation is documented in the Senzing MCP server article *"MATCH_KEY / WHY_KEY
   Direction Notation for Disclosed Relationships"*, which defines the `(ROLE:)`, `(:ROLE)` and
   `(ROLE:ROLE)` forms; counting suppressors needs only their removal, not their direction. A
   dashed domain breaks the naive split for the reason the Entity Specification's *Feature:
   REL_ANCHOR* gives: *"Use a domain code without dashes to avoid confusion in downstream match key
   parsing."* (both from `search_docs(query='MATCH_KEY disclosed relationship REL_POINTER role in
   match key')`, server **1.37.13**, docs index 2026-09-24 18:45 UTC). The `\-` form itself is an
   **engine-side observation**: 2026-09-25, a four-source load (GLEIF, ICIJ, OFAC, OPEN-SANCTIONS;
   455 disclosed relationships), SDK version not recorded.

   Count the features appearing with a leading `-`, ranked by frequency, and split them **both**
   ways step 1 already reads them:

   | Bucket | Read from | What a `-FEATURE` there means |
   |---|---|---|
   | single-source per-record | `RESOLVED_ENTITY.RECORDS[]`, entity's own sources all equal | records in one source merged **despite** the feature disagreeing |
   | cross-source per-record | `RESOLVED_ENTITY.RECORDS[]`, entity spans 2+ sources | records from different sources merged **despite** it disagreeing — the mapping signal |
   | relationship | `RELATED_ENTITIES[]` | Senzing **declined to merge** these entities **because** it disagreed |

   ⛔ **(INV-264) The per-record and relationship buckets mean OPPOSITE things, so pooling them
   yields a number that is neither** — and a band or share that means nothing MUST NOT route
   anyone into remediation. A per-record suppressor is an over-merge signal — the records were
   joined anyway. A relationship suppressor is the engine exercising restraint — it is what
   *should* happen when a feature genuinely conflicts, and on ambiguous data it is the correct
   outcome rather than a defect. The server draws the same line: `RELATED_ENTITIES[]` is documented
   as *"Entities related to but **not resolved into** this one"*, and its `MATCH_KEY` carries the
   vaguer description *"Features that matched/did not match"* rather than the per-record path's
   contributed/detracted wording (both from the same `response_schemas` lookup, server **1.36.0**,
   2026-09-02).

   **Report each bucket against its own total** — a relationship share against relationship
   comparisons, a per-record share against per-record comparisons. Mixing the denominators is how a
   57.4%-of-relationships figure presents as 19.5% of everything (observed 2026-09-02 on SDK 4.4.0,
   build 4.4.0.26242: 1,758 `-DOB` suppressors, **zero** of them per-record).

   ⚠️ **Deduplicate the relationship bucket** — every relationship appears in both entities'
   `RELATED_ENTITIES`, so sort each `(min_id, max_id)` pair into a set first. Step 1 states this for
   the read; it applies again to the count.

   ⚠️ **Two structured fields can replace string-matching the key, where the reader can see them.**
   `RELATED_ENTITIES[].IS_AMBIGUOUS` is documented as *"1 if ambiguous relationship, 0 otherwise"*,
   and `RELATED_ENTITIES[].MATCH_KEY_DETAILS` carries a `DENIALS[]` array beside its
   `CONFIRMATIONS[]` — the structured form of detracted-versus-contributed. `MATCH_KEY_DETAILS`
   `requires_flags: [SZ_INCLUDE_MATCH_KEY_DETAILS]`, which itself `depends_on` a relations flag, so
   treat the breakdown as conditional and fall back to parsing the key when it is absent (same
   lookup, server **1.36.0**, 2026-09-02).
3. ⛔ **An empty cross-source suppressor list is a plumbing failure until proven otherwise.**
   "No suppressors found" and "this reader cannot answer the question" render identically — a
   clean result — so never report the first without ruling out the second. Before making any
   "no cross-source suppressors" statement, prove the reader can see relationships at all:

   - Take one entity known to have a relationship (any entity with a `POSSIBLY_SAME` /
     `POSSIBLY_RELATED` link, or use the relationship count you already have from the load
     summary). If the loaded data genuinely has **zero** relationships, say that instead — the
     question does not arise.
   - Confirm the reader returns a **non-empty** `RELATED_ENTITIES` for it. When the reader is the
     export, the row dump in step 1 has already answered this for the whole pass — one check, not one
     per entity — so this costs nothing; it is still required, because a reader that sees the key but
     parses it under the wrong name fails exactly as silently.

   If that check fails, report **"the audit could not read relationship match keys"** and name the
   reason. Never render it as "no suppressors were found" (INV-115: a blank parsed field is a
   probable wrong reader before it is real absent data).

4. **Report a high-share suppressor as a FINDING, never a pass/fail (INV-264) — and ask the question
   that fits the bucket.** Name the feature, its share, and **which bucket** it came from; the two
   buckets need different questions because they describe opposite behavior:

   - **Cross-source per-record** — records merged despite the feature disagreeing. Ask the
     bootcamper to check **whether the two sources' fields for that feature genuinely measure the
     same thing**. (This is the original wording and it is correct for this bucket.)
   - **Relationship** — Senzing declined to merge because the feature disagreed. Do **not** ask the
     measure-the-same-thing question here; nothing is mis-mapped by the engine refusing a conflict.
     Ask instead **which feature raised these pairs as candidates, and whether it is distinguishing
     enough to be doing that work** — a high relationship-suppressor share usually means some
     *other* feature is being treated as more identifying than it is (an email two people share, a
     phone on a household, a role account).

   ⛔ **(INV-264)** This must not become an automatic gate: a suppressor is often entirely
   legitimate (two records really do disagree), and a hard failure here would produce false alarms and train
   bootcampers to dismiss the signal — which would cost more than the check gains.
   ⛔ **(INV-264) A relationship-bucket finding is not evidence of poor match accuracy** — see the
   gate below.
5. **Carry the outcome into the decision gate below**, alongside the UAT numbers. The audit has
   **three** outcomes, not two — finding, no finding, and could-not-measure — and the gate must be
   told which one it got.
6. **If a finding here causes a mapping to change or be withdrawn, file it as bootcamp feedback
   before moving on** — silently, per `../bootcamp-onboarding/ground-rules.md` → "Reversed decisions:
   file them when they happen". This is the first and most important of that rule's three triggers,
   and this is the step that fires it: the audit read the engine's own output and overturned a
   decision every static gate had passed. Filing it here rather than at graduation is the whole
   point — by then the reasoning may have been compacted away, leaving only the corrected mapping
   and no record of what was wrong with the original or how it was caught. No banner, no question,
   never blocking (INV-012/INV-048).

> **Worked example.** In one bootcamp, `EFX_YREST` ("year established") and `FilingDate`
> (incorporation filing date) were both mapped to `REGISTRATION_DATE`. A business usually operates
> before it incorporates, so the two disagreed on up to 676 records and `-REGISTRATION_DATE`
> appeared on nearly every cross-source match key. All five static gates passed; the quality score
> was 86.3%. Routing one field to payload instead — no other change — took cross-source merges from
> 1 to 4 and links from 160 to 170. The signal was there the whole time; nothing was reading it.

## How-state audit (run before the iterate-vs-proceed gate)

Runs on **both** paths — single-source and multi-source — right after the match-key audit, on the
same export (INV-334). It answers a question nothing else in this phase asks: is each multi-record entity's
**construction history** one the engine itself reports as settled? A drained redo queue is not that
signal. Observed 2026-09-25 (SDK 4.4.1, SQLite, one load process per source, redo drained to an
empty queue): three GLEIF + OFAC + OPEN-SANCTIONS entities the export reported as clean 5- and
3-record entities came back from `how_entity` with `FINAL_STATE.NEED_REEVALUATION` = 1 and **two**
virtual entities — two groups of records that no resolution step joined. The spot-check, the ratio
and the stats all passed them. That observation is **observation-only** (INV-080/INV-149): it says
what one run returned, not what the flag means.

1. **Take every entity with 2 or more records from the export already read** in the match-key
   audit's step 1 — an entity whose `RESOLVED_ENTITY.RECORDS[]` has two or more elements. **No
   sampling.** Call that total **M**. One `how_entity` call per entity, through generated SDK code
   (never direct SQL against `database/G2C.db`).
2. **Take the method name, argument type and flag spelling from `get_sdk_reference` for the
   Bootcamper's binding** — `get_sdk_reference(topic='parameters', filter='how_entity',
   language='<chosen_language>')`. The name differs per binding (the response's own `warnings`
   say so: `how_entity_by_entity_id` in Python, `howEntity` in Java, `HowEntity` in C#), so never
   copy one binding's name into another. Use the method's default flags.
3. ⛔ **(INV-115) Dump ONE `how_entity` response and read where `FINAL_STATE` sits before
   parsing all M of them.** `get_sdk_reference(topic='response_schemas', filter='how_entity_by_entity_id')`
   documents `HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION` (integer) and
   `HOW_RESULTS.FINAL_STATE.VIRTUAL_ENTITIES[]` (array), with no `requires_flags` on either. The
   flags route's `SZ_HOW_ENTITY_DEFAULT_FLAGS` entry lists only `HOW_RESULTS.RESOLUTION_STEPS[]` as
   its response path (both lookups: server **1.37.13**, 2026-09-27), while the 2026-09-25 run
   returned `FINAL_STATE` under the default flags — the two do not fully agree, so the dumped
   response is the authority (INV-149/INV-169). If an entity's response lacks `FINAL_STATE`, that
   entity was **not measured**: count it under "could not measure", never as settled (INV-115: a
   blank parsed field is a probable wrong reader before it is real absent data).
4. **Flag an entity when EITHER sign is present, and name which sign fired** — `NEED_REEVALUATION`
   non-zero, or `VIRTUAL_ENTITIES[]` with more than one element. One sign alone is enough. No route
   documents whether the two always go together, so record each entity's sign or signs rather than
   inferring one from the other.
5. **Report "checked N of M"** — N is the number of entities whose `how_entity` call completed and
   whose response carried `FINAL_STATE`. A failed call does not abort the audit; count it as not
   checked and continue with the rest.
6. **The meaning of `NEED_REEVALUATION` is not documented, so the audit reports and offers no fix.**
   It does not suggest a re-evaluation call, a reload, or any other remedy, and it claims nothing
   about what set the flag or what would clear it. The Bootcamper hears the finding; what to do
   about it waits on a Senzing route that documents it.
   <!-- MCP-NEGATIVE: search_docs(query='NEED_REEVALUATION how entity final state') and search_docs(query='reevaluate entity when to call reevaluation needed') — no indexed document defines HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION or says what sets or clears it; the first query reaches the field only inside the how-flags page's example payload, which shows "NEED_REEVALUATION": 0, and the second returns re-evaluation code snippets, flag constants and a config-change FAQ, none naming the field — owner: get_sdk_reference(topic='response_schemas', filter='how_entity_by_entity_id') IS the route that would carry a field description, and it lists NEED_REEVALUATION as an integer with no description; search_docs is the prose owner, and both were asked (absence negative, INV-194) — server 1.37.13, 2026-09-27 -->

**Four outcomes — the match-key audit's three, plus one for an empty population. State which one
applies:**

- **Finding** — name each unsettled entity (entity ID and its leading name) and the sign or signs it
  showed, with "checked N of M".
- **No finding** — every one of the M entities was checked and none showed either sign.
  ⛔ **(INV-163) Never report "no finding" unless N equals M** — "none unsettled among those checked"
  and "none unsettled" read identically, and only the second is a clean result: an entity whose
  response never arrived is not an entity with nothing to report.
- **Nothing to check** — M is 0: the export holds no entity with 2 or more records. Report
  "checked 0 of 0" and **nothing to check**. ⛔ **(INV-265) With M = 0 the outcome is never "no finding"** —
  the audit's input is empty, and "no finding" is its clean result. A reader that parses
  `RESOLVED_ENTITY.RECORDS[]` under the wrong name also finds zero multi-record entities (INV-115),
  so prove the export was read before saying the question does not arise, as the match-key audit
  does for relationships (its step 3). Report **nothing to check** only when **both** hold:
  - the export returned **at least one entity**; and
  - the lengths of `RESOLVED_ENTITY.RECORDS[]`, summed across the whole export, **equal the total
    records loaded** that step 28 wrote to `docs/results_validation.md`. `RECORDS[]` is the
    *"individual records that constitute the entity"*
    (`get_sdk_reference(topic='response_schemas', filter='export_json_entity_report')`), and
    `reporting_guide(topic='evaluation', language='<chosen_language>')` counts a load's records by
    summing them across the export (both: server **1.37.15**, 2026-09-29). A sum that differs means
    the reader and the load disagree, so M cannot be trusted either way.

  If either fails, the outcome is **could not measure**, naming which condition failed: zero
  entities exported, or the record sum beside the records loaded, with both figures. A load that
  reports records but exports no entities is a reader or flag problem, not an empty population.
- **Could not measure** — some or all calls did not complete, or their responses carried no
  `FINAL_STATE`, or M is 0 and a **nothing to check** condition failed. Say how many were not
  checked ("checked N of M"), and still report any finding among the N that were.
  ⛔ **Never collapse a partial run into "no finding" (INV-163).**

⛔ **The outcome never blocks (INV-117, INV-264)** — it is carried into the decision gate below as a
finding, exactly as the match-key audit's is, and it does not by itself choose the gate's branch;
**nothing to check** does not move the gate either.

**Record it in `docs/results_validation.md`**, which step 28 already wrote (steps 26–27 as well,
on the multi-source path). Append a `## How-state audit` section carrying the outcome, "checked N
of M", and the count of unsettled entities —
⛔ **(INV-265) including zero: write "0 unsettled" rather than omitting the section**, since an
absent section and a clean result would otherwise read alike — then list each flagged entity with
its sign or signs. That rule is for **no finding**. For **nothing to check**, still write the
section, carrying the outcome and "checked 0 of 0", but **omit the "0 unsettled" line**: no entity
was checked, and a zero count there would read as a clean audit (INV-265). Wherever a flagged
entity's record count appears elsewhere in that document (the entity statistics, a spot-check table, a business-result
table), mark it **unconfirmed by the engine's construction history** and point to this section:
the export's count and the engine's history disagree, and the document must not present the count
as settled (INV-245).

This audit asks nothing, so continue in the same turn to the gate below (INV-225).

## Iterate vs. proceed decision gate

Route on the UAT / match-accuracy results, **and present the match-key audit outcome alongside
them** — the percentages alone cannot see a suppressor problem, so a bootcamper choosing between
iterating and proceeding needs both. A high-share cross-source suppressor is the strongest reason
to choose "iterate now" even when the numbers look acceptable.

⛔ **(INV-264) Route match accuracy on the PER-RECORD bucket only. A relationship-bucket share,
however
large, MUST NOT by itself push the gate below the ≥90% branch.** This is INV-264 reaching the
**gate** rather than the report: the audit already reports a suppressor as a finding and never a
pass/fail, and that was not enough — a pooled share still routed the Bootcamper into remediation
one step later, which is the outcome that invariant forbids. The two buckets describe opposite
behavior (audit step 2), so a pooled figure routes on a number that means nothing: a high
relationship share means the engine *declined* to merge on a conflict, which is the outcome the
Bootcamper wants, and treating it as poor accuracy sends them back to re-map a mapping that was not
the problem. Observed 2026-09-02: pooled at 19.5% the gate took the `<80%` branch and recommended
returning to Data Quality, Mapping, and Transformation, while the per-record bucket was **zero** and
a ten-entity spot-check of merged entities was **10 of 10 clean**. Report the relationship finding
in full — it is real and worth acting on — but report it *alongside* strong numbers, not instead of
them.

State which of the audit's three outcomes applies; do **not** collapse the third into the second:

- **A finding** — name the suppressing feature, its share, and **which bucket** it came from.
- **No finding** — the audit ran and found nothing of concern.
- **Could not measure** — the relationship half of the audit did not execute (step 3). Say so
  plainly rather than letting silence imply a clean result: a gate decided on an unmeasured number
  is worse than a gate told the measurement failed. This still does not block (INV-117) — it is a
  third finding that routes, not a new blocker.

**Present the how-state audit's outcome beside the match-key audit's**, as its own line — finding,
no finding, nothing to check, or could not measure, with "checked N of M". A finding names the unsettled entities
and says their record counts are unconfirmed; it is reported on every branch below and does not
move the gate to a different branch (INV-117, INV-264), because no documented remedy exists to
iterate toward.

- **UAT ≥90% and match accuracy ≥90%:** state "Results look strong." and proceed to the module
  transition question. **If the audit produced a finding, say so in the same breath** — strong
  numbers plus a suppressing feature is exactly the case this audit exists to surface, and the
  bootcamper should hear it before moving on. ⚠️ **A zero per-record bucket with a large
  relationship bucket lands here**, and that is the intended routing, not a leak: the numbers are
  strong *and* the finding stands.
- **UAT <80%:** state "Results need improvement — I recommend going back to Data Quality, Mapping, and Transformation
  to refine the mapping." and proceed to the transition question.
- **UAT 80–89%:** results are mixed, so ask the bootcamper to decide with a single pinned question
  (neutral lead + numbered list, INV-051):

  👉 **Most tests pass but there are gaps. What would you like to do? Reply with a number:**

  1. Iterate now to improve the results before moving on.
  2. Move forward to the next module.

  *(Internal: end the turn on this question and wait.)*

## Stakeholder summary

After validation, always produce a one-page executive summary — no question (INV-012) —
following the Module 6 guidance, and save it to `docs/stakeholder_summary_module6.md`. Announce
it as a produced file in the end-of-module summary's "Files produced" list (INV-032). (The Kiro
`templates/stakeholder_summary.md` port is a later phase; compose the summary directly for now.)

## Success criteria

- ✅ Loading program generated with production-quality error handling, progress tracking, and
  statistics
- ✅ At least one data source fully loaded with error rate < 1%
- ✅ Redo queue drained after loading
- ✅ How-state audit run on every multi-record entity; unsettled entities named, zero recorded, or
  nothing to check stated, in `docs/results_validation.md`
- ✅ Loading statistics documented in `docs/loading_strategy.md`
- ✅ Match accuracy reviewed (sample entities checked for false positives/negatives)
- ✅ Results validation documented in `docs/results_validation.md`
- ✅ Loading program saved in `src/load/`

**Additional criteria when 2+ sources loaded:**

- ✅ All sources loaded (or failures documented) with error rate < 1% per source
- ✅ Dependencies respected, cross-source matches reviewed
- ✅ Orchestrator program saved in `src/load/orchestrator.[ext]`
- ✅ Cross-source match accuracy validated
- ✅ UAT executed, results in `docs/uat_results.md`
- ✅ Stakeholder sign-off obtained

## Advanced reading

- After completing Module 6, ask about record updates, deletions, entity re-evaluation, and redo
  processing, use `search_docs` and `get_sdk_reference` for current guidance for production
  systems where source data changes over time.
- For production systems that receive ongoing data, ask about incremental loading patterns, use
  `search_docs` and `generate_scaffold` for current guidance on adding new records to an existing
  database, processing redo records after incremental loads, and monitoring pipeline health.

(The Kiro multi-source reference `data-processing-reference.md` and the user reference
`docs/modules/MODULE_6_DATA_PROCESSING.md` are later porting phases.)

## Module completion and transition to Module 7

Follow the Decision Gate above to frame readiness. When results are ready, run the standard
**Module Completion** process in `../bootcamp-onboarding/module-completion.md` (update progress,
append the Module 6 recap section to `docs/bootcamp_recap.md`, and present the end-of-module
summary), then close the module:

👉 **Are you ready to move on to the next module: {next module name}?**

*(Internal: end the turn on this question and wait.)* On completion, set `current_step` to
`null` in `config/bootcamp_progress.json` and, on an affirmative reply, **(INV-272) acknowledge it in one short
visible line naming Module 7 before invoking its skill** — per the ground rules' acknowledge clause
and `../bootcamp-onboarding/module-completion.md` Step 4, which own the ordering — then produce the
Module 7 start banner, journey map, before/after framing, and step overview per the ground rules.

**Success indicator:** ✅ All data sources loaded + redo records processed + no critical errors +
entity resolution results validated + results documented in `docs/results_validation.md`.
