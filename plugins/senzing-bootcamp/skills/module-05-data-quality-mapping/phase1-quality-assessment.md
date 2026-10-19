# Module 5, Phase 1: Quality Assessment (steps 1–7)

Verify data sources against the Entity Specification. Follow the ground rules. `🛑`/`⛔` are
internal directives: do not render them; signal a stop by ending the turn on the single 👉
question and waiting.

## 1. List the agreed-upon data sources

Recap what the bootcamper actually brought into this module. **`config/data_sources.yaml` is the
list** — Data collection registers every source it acquired there, with its counts and provenance.
Read `docs/business_problem.md` for the **why**: the business context that motivated each source,
which is what makes the recap worth reading.

⛔ **Do not take the source list from `docs/business_problem.md`.** That file records what was
*discussed* in Discover the Business Problem, before Data collection ran. `config/data_sources.yaml`
is the registry INV-203 gates: a source is recorded there only after its fetch returned 2xx **and**
its measured record count matched, so it is the only list that says what was actually collected. The two routinely differ —
Data collection is exactly where a bootcamper substitutes a CORD dataset for data they cannot share
— and this module processes what is in `data/raw/`, not what was once intended. Where the two lists
differ, say so in one line rather than silently preferring either: "we talked about X; what you
collected is Y."

**Checkpoint:** write step 1 to `config/bootcamp_progress.json`.

## 2. Confirm the source files are present

⛔ **Do not ask the bootcamper to place files here by default.** This module's prerequisite is
"Module 4 complete (data sources collected, files in `data/raw/`)" — Data collection is a required
module that runs immediately before this one, so asking for what it already fetched is a question
the bootcamp does not need to ask (INV-006/INV-012). Worse, a bootcamper who takes it literally may
re-fetch, which on a CORD source is a second download and a live rate-limit hazard
(`cord-download-rate-limit-is-saved-as-data`, INV-203).

**Verify instead.** For each source registered in `config/data_sources.yaml`:

- confirm its file exists at the recorded path under `data/raw/`;
- confirm its record count still matches the count recorded at collection (INV-203 wrote both);
- report what you found — one line per source, not a wall of output (INV-012).

**Ask only in the two cases where there is genuinely nothing to verify:**

- a source is registered but its file is **missing**; or
- the registry is **empty** — the bring-your-own-data path, which is real and supported: a
  bootcamper whose data cannot leave their machine reaches this module with nothing collected.

In either case, ask for what is missing in a single 👉 question, naming the forms that work:

- CSV files (first 10-20 rows)
- JSON samples
- Database schema with sample values
- Screenshots of data tables
- Text descriptions of fields and data types

**Checkpoint:** write step 2.

## 3. Understand the Senzing Generic Entity Specification

Call `download_resource(filename="senzing_entity_specification.md")` to **locate** the current
Senzing Generic Entity Specification.

⛔ **The response is a listing, not the document.** Verified on server **1.32.9, 2026-08-14**: the
call returns `mode: "url"` and a `resources` array whose entry carries `filename`, `size_bytes` and
a `url` — and **no content**. There is nothing in the response to "save", so a guide that writes the
response itself to the canonical path leaves Steps 4, 5, 5a and 6 reading attribute names out of a
file that has none — and because a file still exists at the expected path, the failure is silent.
`download_resource` is the third MCP tool with this shape; `ground-rules.md` → "Three tools answer
with a listing" states the rule once for all three (INV-234).

**Retrieve it in two steps:**

1. **Fetch the `url`** the response gave you, using the HTTP client idiomatic to this bootcamp's
   chosen language (INV-002) — not a hard-coded `curl`, which is not present on every supported
   platform (INV-001).
2. **Save the body** to the single canonical copy at
   `docs/reference/senzing_entity_specification.md` (do not create duplicate copies elsewhere), then
   **check the saved file's size against the response's `size_bytes`** before using it. Compare
   with the figure in **this** response, never one remembered from an earlier run: the file changes
   on the server's schedule, so a size written down goes stale silently (INV-080). A
   truncated fetch, or a saved error page, is caught here in one comparison instead of surfacing in
   Step 4 as attribute names that are merely absent. (INV-228's count-check discipline, applied to a
   resource fetch rather than a dataset.)
3. ⛔ **(INV-115) Read the attribute names out of the FIRST COLUMN of the feature tables as PLAIN
   TEXT — they are not backticked in this document, and a catalog built by scanning for backticked
   tokens silently under-collects by roughly four fifths.** Verified against the served document on
   server **1.33.0**, 2026-08-28. `NAME_ORG`, `ADDR_LINE1` and `PHONE_NUMBER` appear plain and are
   **never** backticked anywhere in the file, so a backtick-tuned parse reports three of the
   commonest attributes in the specification as unrecognized — which is the cheap way to tell a
   broken parse from a real absence.
   - ⚠️ **The same names render the other way through a different route, which is what makes this a
     trap rather than a typo.** `search_docs(query='entity specification attribute names feature
     tables NAME_ORG ADDR_LINE1 PHONE_NUMBER', category='data_mapping')` returns those same tables
     with the names **backticked** (`` `OTHER_ID_TYPE` ``): its top hit is the specification's
     *Entities, features and attributes* section, and reading past the first hit reaches *Name >
     Feature: NAME* with its attribute table. A parse tuned on a `search_docs` excerpt
     works there and under-collects here — and this saved document is what Step 4 reads.
   - ⛔ **(INV-080) Do not pin an attribute count in this file** — whatever the document holds today, a figure
     written into shipped prose is one nobody re-measures, and it goes stale silently because it
     keeps reading authoritative. Confirm the parse against the saved copy instead: a catalog
     missing `NAME_ORG` is a parse failure, not a specification change.

⚠️ **If the URL fetch fails, `inline=true` is the sanctioned fallback for this tool — and for this
tool only.** `download_resource`'s declared schema carries `filename`, `filenames`, `inline`,
`offset` and `version`, so INV-136 permits `inline` here, and the resource's own `on_failure` names it: *"Fallback:
call download_resource with this filename and inline=true."* Use it only **after** the URL fetch
fails — the parameter's own description says to try the default `inline=false` first — and expect it
to cost context. This is the **opposite** of
the rule for `generate_scaffold` and `find_examples`, whose schemas do not declare `inline` at all,
so passing it there is a call that cannot work. The difference is not about the word `inline`; it is
about what each tool's schema declares (INV-136).

⛔ **(INV-234) The inline reply carries the file in bounded chunks, not in one response, so put it back together before Step 4 reads it.**
The reply's shape is stated once in `ground-rules.md` → "Three tools answer with a listing"
(INV-300); this is the one step that assembles a file from it:

1. Call `download_resource(filename="senzing_entity_specification.md", inline=true)`. Request the
   file on its own, with `filename`: a batch (`filenames`) leaves out a file too large for one
   chunk and lists it under `oversize`.
2. Write the reply's `content` to the canonical copy, `docs/reference/senzing_entity_specification.md`,
   as UTF-8 with the text unchanged (no line-ending conversion). **Ignore the reply's `dest`** and
   its instruction to save there: it names a `/tmp` path, which is not the canonical copy and does
   not exist on Windows (INV-001).
3. While the latest reply says `truncated: true`, call again with `offset` set to its `next_offset`,
   and **append** that reply's `content` to the same file, in order. Stop at the reply that says
   `truncated: false` (or carries no `next_offset`).
4. **Check the assembled file against `total_chars`** before using it. This is the inline route's
   counterpart of the `size_bytes` check above, and it catches a dropped or repeated chunk.
   ⚠️ Despite its name, `total_chars` counts the file's **UTF-8 bytes**, and so do the offsets:
   verified on server **1.37.15, 2026-09-29**, where `total_chars` equaled the URL route's
   `size_bytes`, and a chunk decoded to fewer characters than the offsets it spanned, because the
   file holds non-ASCII text such as em dashes. So compare the saved file's **size in bytes** with
   `total_chars`; a character count comes out short and fails a correct assembly.

⚠️ **For a single lookup, `search_docs` is cheaper than paging.** It serves the Entity
Specification already split by section, so one attribute or feature is one `search_docs` call
naming it, with `category='data_mapping'`. It does not replace the saved copy: Steps 4, 5, 5a and 6 read the file, so paging stays the
fallback for fetching it.

**How to consult it: targeted lookup, never end to end.** The file is large: its size is the
response's `size_bytes` (or `total_chars` inline), not a figure written here (INV-080). Look up the
specific feature or attribute in question — grep for the attribute code, or open the single section
that covers it. Do **not** read it front to back. `mapping_workflow` says so itself, at both its
step 2 and step 3 (verbatim, server 1.32.9, 2026-08-14): *"Do NOT attempt to read it end-to-end —
that is unnecessary and will overflow limited context windows."* That overflow costs the Bootcamper
the rest of their session, not merely some tokens.

**The scope of its authority is this phase.** Within Phase 1 the specification is the reference for
attribute names, types and structures — Steps 4, 5, 5a and 6 all compare against it. From
`mapping_workflow` step 2 onward the workflow delivers its own **distilled inline mapping
reference** (the feature catalog, the identifier-classification workflow, and the exact attribute
keys), and *that* is the working reference for the mapping phase; the tool states the file "is
available only as an optional deep-dive" for an edge case the inline reference does not cover. Phase
2 already cites the inline reference — relay this rather than leaving a guide holding two references
with no basis for preferring either.

⚠️ **Two copies on disk is expected, and is not a breach of the rule above.** `mapping_workflow`
step 1's own `resources` list writes `senzing_entity_specification.md` into the workflow's
`workspace_dir` — `data/mapping/`, per INV-136 — verified on server 1.32.9, 2026-08-14. That is the
tool's copy for the mapping phase; `docs/reference/senzing_entity_specification.md` is this phase's
canonical copy. The no-duplicates rule governs copies **the guide** makes; it is not violated by the
tool populating its own workspace. Do not delete either, and do not re-fetch to reconcile them.

**Checkpoint:** write step 3.

## 4. Compare each data source with the Entity Specification

Using the Entity Specification retrieved in Step 3 as the reference, compare each data source's
fields against the specification's attribute names. For each data source provided:

- Identify which fields map directly to attributes defined in the Entity Specification.
- Identify fields that need transformation (e.g., combining or splitting fields to match the
  specification's expected structure).
- Identify fields with non-standard names that correspond to attributes in the Entity
  Specification.
- Note any missing critical fields defined in the Entity Specification.
- Check if `DATA_SOURCE` and `RECORD_ID` are present or can be derived.

**Checkpoint:** write step 4.

## 5. Categorize each data source

(Using the Entity Specification retrieved in Step 3 as the source of truth for what constitutes
compliant attribute names.)

- **Entity Specification-compliant:** Data already uses attribute names and structures that
  match the Entity Specification. CORD sources (the already-Senzing-ready fast-path class) are
  **eligible to be considered** for the fast-path (Step 5a, offered only for `provenance: cord`);
  Step 5a decides, and its sub-step 5 is the one statement of the conditions the skip is offered
  on (INV-300) — a CORD source carrying fields that resolve to no specification attribute
  goes through mapping like any other (INV-198). Do not route a source past mapping from this
  categorization; that is Step 5a's call. Other compliant sources, including non-CORD data that
  looks Senzing-ready, continue to Phase 2, which confirms compliance and records lineage before
  loading.
- **Needs mapping:** Data uses different field names or structures than those defined in the
  Entity Specification. Continue to Phase 2 (data mapping).
- **Needs enrichment:** Data is missing critical attributes. Discuss with the user whether
  additional data sources can provide the missing information.

**Checkpoint:** write step 5.

## 5a. Senzing-readiness check and fast-path offer (CORD sources only)

For each source where `provenance` is `cord` in `config/data_sources.yaml` (that is, a source
obtained via the `get_sample_data` MCP tool in Module 4):

1. **Obtain the Senzing schema definition:** Reuse the Senzing Generic Entity Specification
   already retrieved in Step 3: do not download it again. From that same MCP-sourced
   specification, extract the list of required top-level structural indicators for a
   Senzing-loadable record (e.g., presence of a FEATURES array, DATA_SOURCE, RECORD_ID).

   ⛔ **Loadable is a wider test than "has a FEATURES array".** The same specification states that
   the older shape — "a flat JSON structure with a separate sub-list for each feature that had
   multiple values" — is **still supported**. Treat **both** forms as Senzing-ready:

   - the recommended **`FEATURES` array**; or
   - the legacy **flat structure**: feature attributes at the record root
     (`BUSINESS_NAME_ORG`, `RECORD_TYPE`, …), with a per-feature root sub-list (`NAMES`,
     `ADDRESSES`, `IDENTIFIERS`) wherever a feature repeats. A source with no repeating feature is
     in this shape with no sub-list at all — flat root attributes only.

   **CORD ships both, so neither may be assumed.** Verified live —
   `get_sample_data(dataset='london', source='GLOBALDATA')` returns a `FEATURES` array (with the
   raw source columns alongside it at the record root), while
   `get_sample_data(dataset='las-vegas', source='PPP_LOANS')` returns flat root attributes
   (`BUSINESS_NAME_ORG`, `RECORD_TYPE`, `BUSINESS_ADDR_*`) and no `FEATURES` array at all
   (MCP server 1.32.9, re-verified 2026-08-14). Requiring `FEATURES` alone classifies the legacy-shaped sources as not-ready and
   sends data that already loads and resolves through a mapping phase it does not need. Sample the
   actual records rather than assuming a dataset's shape, and confirm the still-supported statement
   from the specification you retrieved (INV-080), not from this file.

2. **Perform the structural check: will it load?** Examine up to 100 sample records from the
   source file. For each record, verify:

   - The record is valid JSON.
   - The record contains the structural indicators identified from the Entity Specification
     (top-level keys, array structures).
   - DATA_SOURCE and RECORD_ID are present or derivable.

   If ALL sampled records pass, classify as **structurally loadable**. If ANY sampled record
   fails, classify as not structurally loadable. (The Kiro `check_cord_readiness.py` helper is a
   later porting phase; perform the check directly against the sampled records for now.)

   ⛔ **This is the entry condition, not the fast-path condition.** Structurally loadable means the
   engine will accept the record; it does not mean every field in it has been decided about. Step 3
   below answers that second question, and the offer in step 5 is gated on this check **and** on
   two more: step 3 (fully mapped) and step 3a (zero type/name candidates). Classifying a
   partially-mapped source as ready on this test alone is what let a source with eleven
   undispositioned columns skip the module (see step 3).

   **A stronger check, when the engine is available: ask Senzing how it reads the record.** The
   structural test above confirms the *shape*; it cannot tell you whether an attribute name will
   actually participate in matching. `getRecordPreview` returns Senzing's own interpretation of a
   record **without loading it**, which answers that directly — and it beats reading field names
   against the specification by eye. Obtain the call for the bootcamper's binding from MCP
   (`get_sdk_reference(topic='parameters', filter='getRecordPreview')`; the method name and argument
   types differ per binding — INV-132) rather than writing it from memory.

   ⛔ **Preview requires the record's `DATA_SOURCE` code to be registered first, even though it
   writes nothing.** This is counter-intuitive and it is why the check fails where it is most natural
   to run: registration belongs to the loading phase, so a readiness check reaching for preview
   before registration gets

   ```text
   SENZ2207|Data source code [<CODE>] does not exist
   ```

   The prerequisite is **not** documented on the method — **still true, re-verified 2026-08-11 on
   MCP server 1.32.8** (first observed 2026-07-30 on 1.32.2):
   `get_sdk_reference(topic='parameters', filter='getRecordPreview')` returns one signature per
   binding — `get_record_preview(record_definition: str, flags: int = …) -> str` in Python — with no
   mention of it.
   (The same call also returns `get_record`, which the filter matches too; that is a second
   *method*, not a second overload.) So the order is: register the source code(s) — taking the
   registration code from `sdk_guide(topic='configure')`, never hand-written (INV-080) — then preview.
   Registration is idempotent and the loading phase needs it anyway, so doing it here costs nothing.

   On `SENZ2207`, call `explain_error_code('SENZ2207')` first as always (INV-080): unlike some codes,
   its own resolution steps *do* name the fix — register the code, confirm the registered list, mind
   that codes are case-sensitive and conventionally UPPERCASE, and reinitialize afterwards — so do not
   restate them here, just follow them.

   **Optional and non-blocking.** If the engine is not available, or registration has not happened
   and you would rather not do it at this point, skip the preview and keep the structural check
   (INV-048). Say which check ran, so `senzing_loadable` never implies a stronger test than was
   performed. The prerequisite applies wherever a preview-based check is used, not only to the CORD
   sources this step covers.

3. **Perform the coverage check: is every field actually decided about?** Structurally loadable
   answers *will it load*. This answers *is there anything left to map* — and they are not the same
   question. Over the same sampled records, partition every root key into three sets:

   - **structural keys** — `DATA_SOURCE`, `RECORD_ID`, `RECORD_TYPE`, `FEATURES`, and any root
     sub-list **whose contents resolve to Entity Specification attributes** (`NAMES`, `ADDRESSES`,
     `IDENTIFIERS`, …);
   - **specification attributes** — keys that resolve to an attribute in the Entity Specification
     you retrieved in Step 3 (the same copy step 1 above reuses — do not download it again);
   - **unrecognized keys** — everything else, *including the contents of any root array whose
     contained keys do not resolve*.

   ⛔ **(INV-294) A root array is a per-feature sub-list only if its CONTENTS are spec attributes — decide it
   by looking inside, never by the key's shape.** The structural set above is closed, and the `…`
   continues a list of *examples of the test*, not an invitation to add members by resemblance:
   plural, uppercase and an array-of-objects is exactly what an unrecognized array looks like too.
   **So partition one level down as well** — for every root key holding an array of objects, run the
   same three-way test on the contained keys, and count an unresolved contained key as an
   unrecognized key of the source.

   ⚠️ **The worked case, measured live.** `get_sample_data(dataset='las-vegas', source='GLEIF')`
   returns four root arrays that look alike. Three are genuine sub-lists — `COUNTRIES` holds
   `REGISTRATION_COUNTRY`, `DATES` holds `REGISTRATION_DATE`, `RELATIONSHIPS` holds
   `REL_ANCHOR_*`/`REL_POINTER_*`, and all resolve. The fourth, **`RISKS`, holds `TOPIC`, which is
   not a Senzing attribute at all** — 547 of the source's 1,952 records carry it, and `TOPIC` appears
   in no feature table of the Entity Specification (both re-verified on MCP server **1.35.1**,
   2026-09-01). Filed as structural, its undispositioned contents are invisible, and a source whose
   only unmapped content sits inside such an array reaches step 5 with **zero** unrecognized keys —
   the fast path is offered, and the module is skipped with real fields undecided. That is the
   failure the ⛔ two paragraphs down already forbids, arriving one level up: at the **container**
   rather than at the leaf.

   ⛔ **Do not resolve the second set by exact string match against the attribute catalog.** A
   catalog attribute can arrive carrying a leading label, and an exact match reports it as
   unrecognized — which would route a genuinely fully-mapped source into mapping, the pointless work
   the fast-path exists to remove. This is not hypothetical: `get_sample_data(dataset='las-vegas',
   source='PPP_LOANS')` ships `BUSINESS_NAME_ORG` and `BUSINESS_ADDR_LINE1`/`CITY`/`STATE`/
   `POSTAL_CODE`, while the specification's catalog names the attributes `NAME_ORG` and
   `ADDR_LINE1`/`ADDR_CITY`/… (Entity Specification, *Feature: NAME*; and *Usage types and payload
   (optional attributes)*, which defines a usage type as "a short label that distinguishes multiple
   instances of the same feature on one entity" — both confirmed via
   `search_docs(query='usage type distinguishes multiple instances payload optional attributes',
   category='data_mapping')` for the usage-type half and
   `search_docs(query='NAME_FULL NAME_ORG parsed person name single field', category='data_mapping')` for
   *Feature: NAME*, MCP server 1.32.8, docs index 2026-08-11; both queries re-verified as top hits
   on 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-04). Resolve each
   key against the specification you hold, and where a key is a catalog attribute carrying such a
   label, count it as a specification attribute. ⛔ The label **encoding** on a flat attribute name
   is an observed shape, not something the indexed specification states — so where you cannot
   resolve a key with confidence, treat it as unrecognized and let step 6 name it, or use the
   optional `getRecordPreview` check above to ask Senzing directly how it reads the record.

   **The threshold is a count, not a proportion: zero unrecognized keys, or no fast-path offer.**
   Recorded here with its reasoning, because it is a decision and not an obvious default:

   - **Why not a percentage.** A proportion has to be tuned against how wide the source happens to
     be. `PPP_LOANS` is 11 unrecognized of 19 keys and any threshold catches it; a source with one
     undecided column in thirty passes an 80%-coverage rule while still hiding a decision from the
     bootcamper. The number of columns nobody decided about is the thing that matters, and it does
     not get less important because the record is wide.
   - **Why `payload`-worthy columns are NOT excluded from the count.** They cannot be: from the
     record alone, a column the publisher deliberately kept as payload and a column nobody
     dispositioned look identical — both are a non-catalog key at the root, and even
     `getRecordPreview` only reports which features Senzing read, never what the publisher intended.
     So they are not counted as *unmapped*; they are counted as **undecided**, and they are routed
     to the step that decides them. `payload` is one of the five dispositions
     `mapping_workflow` step 3 assigns (`feature`, `payload`, `ignore`, `derived`, `extract` —
     confirmed against the live tool schema, MCP server 1.32.8, 2026-08-11), so a payload-heavy
     source loses nothing by going through mapping: mapping is where "this is payload" is actually
     recorded, rather than assumed by a gate that cannot see intent.
   - **Why this does not re-introduce pointless work.** A genuinely fully-mapped source — the
     `truthset` class the fast-path was built for — has zero unrecognized keys and still fast-paths
     with no extra question. Nothing changed for it.

3a. **Perform the type/name check: are any PERSON-typed records named like organizations?** Run
   Step 6's type/name check over every record of this source now (the canonical statement is Step
   6's "Type/name check" — INV-300), and keep its count and candidate names for Step 6 to report.
   ⛔ (INV-198) **One or more candidates means no fast-path offer, even for a source that is
   structurally loadable and fully mapped.** (INV-335) The offer skips the mapping phase, which is where a
   retype is applied, so it would send the source to loading with its record types undecided.
   Route it through sub-step 6 instead. Zero candidates, or zero PERSON-typed records, changes
   nothing: the offer proceeds on sub-steps 2 and 3 alone.

4. **Record the result:** In `config/data_sources.yaml`, set the source's `senzing_loadable` and
   `fully_mapped` fields to `true` or `false`, record `unmapped_fields` as the sorted list of
   unrecognized keys (an empty list when `fully_mapped` is `true`), and update `updated_at`.

   *(These replace the single `senzing_ready` field, which recorded only the structural test while
   the offer was presented on it. On a resumed bootcamp whose registry still carries
   `senzing_ready`, read it as `senzing_loadable` and treat `fully_mapped` as unknown — re-run
   step 3 rather than inferring it, since the old field never measured coverage.)*

5. **If structurally loadable, fully mapped AND free of type/name candidates: present the fast-path offer.**
   It is offered only when sub-step 3a also found **zero** type/name candidates; a source with one
   or more goes to sub-step 6. State the coverage figure, so skipping is an informed choice rather
   than a silent default:

   👉 **Your CORD source [SOURCE_NAME] is already in Senzing-loadable form, and all [N] of its fields resolve to the Senzing Entity Specification — there is nothing left to map. Would you like to skip the mapping phase and proceed directly to loading in the Data processing module?**

   *(The wording holds for both supported shapes — the structural check covers a `FEATURES` array
   and the still-supported per-feature sub-lists alike.)*

   *(Internal: end the turn on this question and wait.)*

   - **If confirmed:** Set `mapping_status: complete` and `fast_pathed: true` in the registry.
     Keep `file_path` pointing at the original `data/raw/` file. Record a data-lineage entry
     (see below). Route the source to Module 6.
   - **If declined:** Continue through the normal quality assessment and mapping workflow for
     this source.

6. **If structurally loadable but NOT fully mapped: route to mapping, and name the columns.** Do
   **not** present the fast-path offer — there is something to map, and the whole point of this
   module is doing it. Say so in one statement (no 👉 question; the routing is not a choice):

   > "[SOURCE_NAME] will load as-is, but [N] of its fields aren't Senzing Entity Specification
   > attributes — [list them] — so nothing has been decided about them yet. We'll map this one, and
   > those fields are the exercise: some will become features, some payload, some ignored."

   Name every unrecognized column. A count alone tells the bootcamper a decision exists without
   telling them what it is about. For `PPP_LOANS` those columns are `Business_Type`, `CD`,
   `DateApproved`, `JobsReported`, `Lender`, `Loan_Range`, `NAICS_Code`, `NonProfit`, `OwnedBy`,
   `OwnedByRaceEthnicity`, `OwnedByVeteran` — eleven real decisions the fast-path used to skip.

   **This branch also takes a source that sub-step 3a held back**: one with type/name candidates,
   even when it is fully mapped. Its statement names the candidate count, after any unrecognized
   fields when it has those too:

   > "[SOURCE_NAME] will load as-is, but [N] of its [M] PERSON-typed records have names that end
   > like an organization's, so their record type needs a decision. We'll look at them in the
   > quality assessment next, and map this one."

7. **If NOT structurally loadable or MCP unavailable:** Continue through the normal quality
   assessment and mapping workflow. Do NOT present the fast-path offer.

8. **Non-CORD sources:** Skip this step entirely. Never present the fast-path offer for sources
   with provenance other than `cord`.

9. **After every source has been classified: if ALL of them were fully pre-mapped, say so and
   offer mapping practice.** Never route the bootcamper past this module's core skill in silence —
   they came to learn mapping, and a run where every source fast-pathed teaches none of it. This
   fires only when no selected source reached step 6.

   > "Every source you selected was already fully mapped to the Senzing Entity Specification, so
   > the mapping exercise has nothing to work on. That's a real property of this data, not a
   > shortcut — but it does mean you'd finish the bootcamp without writing a mapping."

   👉 **Would you like to add a raw, unmapped source so you get the mapping practice? Reply with a number:**

   1. Yes — a raw variant of the same data.
   2. Yes — a raw sample from the free-data catalog (`https://github.com/docktermj/senzing-bootcamp-free-data`).
   3. No — continue without a mapping exercise.

   *(Internal: end the turn on this question and wait.)*

   - **Options 1-2:** return to Module 4's data-collection flow to acquire the source, register it
     with `provenance` other than `cord`, then run this module normally on it. Its caveats apply
     — for the free-data catalog, give the ICIJ note in Module 4 before recommending that sample.
   - **Option 3:** continue. Record the choice so graduation can state that no mapping was
     authored, rather than leaving the recap silent about it.

**Fast-path data-lineage entry:** Record a lineage entry ONLY for a source that was explicitly
fast-pathed (the bootcamper confirmed the offer above). Never record one for a source that went
through normal mapping or that was never offered the fast-path. Add the entry to the
`transformations` section of `docs/mapping/data_lineage.yaml`, keyed by the source's
DATA_SOURCE name. Because no transformation occurred, the entry records the original `data/raw/`
file as both input and output with equal record counts:

```yaml
transformations:
  CORD_LAS_VEGAS:
    source_file: data/raw/cord-las-vegas.jsonl
    transformation_script: null  # No transformation: fast-pathed
    output_file: data/raw/cord-las-vegas.jsonl  # Same file
    records_in: 8421
    records_out: 8421
    records_rejected: 0
    quality_score: null  # Quality assessment skipped
    fast_pathed: true
    fast_path_reason: "CORD source structurally loadable, fully mapped (no unrecognized fields) and with zero type/name candidates"
```

**Invariants:** every fast-path lineage entry MUST satisfy: `source_file == output_file` (the
original `data/raw/` file, unchanged); `records_in == records_out`; `records_rejected: 0`;
`transformation_script: null`; `fast_pathed: true`.

**Non-blocking:** If writing the data-lineage entry fails, allow the fast-path to proceed
anyway: route the source to Module 6 and log the lineage failure so it can be retried later. A
lineage write failure MUST NOT block the fast-path.

**Checkpoint:** write step 5a.

## 6. Assess data quality and apply thresholds

For each data source, compute a quality score based on field completeness, format consistency,
and duplicate rate.

⛔ **Compute it this way — the number routes a gate banded to the percentage point, so two guides
must reach the same figure.** The bands below (≥80 / 70-79 / <70) were precise while the arithmetic
feeding them was never written down, which meant the score was reproducible only by accident:

```text
quality_score = 0.70 × completeness + 0.25 × format_consistency + 0.05 × (100 − duplicate_rate)
```

**Why duplicates barely count.** Completeness and format consistency are things the bootcamper can
act on before mapping — a missing field stays missing, a malformed date stays malformed. A high
duplicate rate is **not a defect to remediate**: resolving duplicate records is what Senzing is for,
and this module runs *before* it has had the chance. Weighting duplicates heavily would send a
bootcamper to "fix" the very condition that makes their data worth resolving. It stays in the score
at 0.05 so a pathological source still registers, and it is **reported in full** regardless of its
weight.

- **completeness (0-100)** — the mean, across records, of the share of **applicable** fields that
  are present in that record, using the presence test defined below and per-`RECORD_TYPE`
  applicability (INV-174).

  **Which fields count — stated positively, because a raw source is this module's central case.** A
  source field enters the denominator when **any** of these is true:

  - **Step 4 identified an Entity Specification counterpart for it.** Step 4 runs immediately before
    this one and does exactly that comparison, so the set is read off its output rather than
    re-derived here. On a raw source this is where the whole denominator comes from.
  - it is already **dispositioned in mapping** (`feature`, `payload`, `extract`); or
  - it is a **structural key** — `DATA_SOURCE`, `RECORD_ID`.

  ⚠️ **Step 5a uses "resolves to" in a narrower sense, and reading that sense here breaks the
  score.** Step 5a asks whether the **key itself** is a catalog attribute, allowing for a leading
  label (`BUSINESS_NAME_ORG` → `NAME_ORG`) — a question about an already-Senzing-ready source. This
  step asks whether a field **has a counterpart** — a question about a raw source, where no key is a
  catalog attribute yet. Same words, two different questions. Read Step 5a's sense here and a fully
  raw source has **zero** countable fields, so the number that gates this module is undefined on the
  module's most common input. Do not change Step 5a: it is correct for what it asks.

  **The exclusion stands, narrowed to what it is for.** A source column with **no** counterpart
  **and** no disposition stays out of the denominator — scoring a source down for work this module
  has not done yet is the false-alarm shape INV-174 records. What must **not** be excluded is a
  column whose counterpart Step 4 has just identified.

  **Worked example — a fully raw source, nothing dispositioned yet:**

  ```text
  full_name     -> NAME_FULL       counterpart identified at Step 4  -> counts
  phone         -> PHONE_NUMBER    counterpart identified at Step 4  -> counts
  created_date  -> (none)          no counterpart, no disposition    -> does NOT count

  denominator = 2 applicable fields per record (plus structural keys) — not 3, and not 0
  ```

  ⛔ **An empty denominator means completeness is UNDEFINED. Never report 0/0 as 0% (INV-238).** A
  source where no column has any counterpart and nothing is dispositioned yields 0/0. Say completeness
  is undefined, give the one-line reason, and route that source to **"Needs enrichment"** (Step 5's
  third category) instead of emitting a score. Reporting 0% instead computes
  `0.25 × format_consistency + 0.05 × (100 − duplicate_rate)`, which lands under 70 and routes the
  gate to "Recommend fixing before mapping" on **arithmetic rather than evidence** — a source with
  nothing to measure is not a source measured as bad, and the bootcamper would be sent to remediate a
  quality problem the number does not demonstrate.

  (On a real source this mattered: `PPP_LOANS` scored 100% on its 8 resolving fields and
  94.4% averaged over all 19 root keys.)

- **format_consistency (0-100)** — the share of populated values that match their field's dominant
  observed pattern (date shape, postal-code shape, casing of a coded value). Report the fields that
  drag it down; a single malformed field is more actionable than the aggregate.
- **duplicate_rate (0-100)** — the share of records whose `(DATA_SOURCE, RECORD_ID)` pair is not
  unique. ⛔ **Compute it on that pair, never on whole-row equality** (INV-180): re-sending the same
  pair *replaces* a record rather than adding one, so identical rows under distinct keys are two
  records and identical keys are one. Row-level duplicate counting measures something Senzing does
  not do.

**Worked example** — 1,000 records; applicable fields present on 96% of them on average; 3% of
populated values off-pattern; 10 records share a `RECORD_ID` with another (1%):

```text
0.70 × 96  +  0.25 × 97  +  0.05 × (100 − 1)   =  67.2 + 24.25 + 4.95  =  96.4  ->  ✅ (≥80)
```

Round to one decimal and state the three inputs alongside the total, so the bootcamper can see
which dimension moved it.

⛔ **Define "present" this way — do not re-invent it.** Completeness feeds the score that gates this
module, so the presence test is part of the measurement, not an implementation detail. A field value
is **present** unless it is:

- absent — the key is missing from the record — or `null`;
- an empty or whitespace-only string;
- an empty container (a list, dict, set or tuple of length 0);
- a container whose every element is itself empty by these rules (e.g. `[""]`, `[{}]`, `[null]`).

Everything else is present. Two consequences to get right:

- **`false`, `0` and `0.0` count as PRESENT.** They are values, not absences. A truthiness test
  (`if value:`) is wrong: it silently reports real data as missing.
- **Presence is a property of the VALUE, never of the key.** Testing "does the record have this
  field?" reports 100% coverage for a field that is an empty array in every record — which is
  exactly how one bootcamp reported `IDENTIFIER_LIST` coverage as **100%** when the true figure was
  **0%**, on the field family that supplies exclusive identifiers, feeding the number straight into
  the mapping decision.

⛔ **Sanity-check any 0% or 100% figure before it routes the gate.** A field family reporting
*exactly* full or *exactly* zero coverage across every record is the signature of a presence test
measuring the wrong thing. Print one sample value for that field and confirm the figure against it
before reporting. Treat a suspiciously uniform result as a probable measurement failure first and a
real finding second — the same discipline INV-115 applies to blank parsed SDK fields, applied here to
profiling.

⛔ **Measure completeness PER RECORD against the features that apply to that record's
`RECORD_TYPE` — never as one average per feature across the whole source.** A feature that does not
apply to a record is not missing data, and averaging it in penalizes the source for data that could
not exist.

⛔ **A GROUP score is not evidence that two sources share an ATTRIBUTE, and MUST NOT be read as a
cross-source join prediction.** Completeness for a grouped family — the Entity Specification's
*Identifiers* section groups identifiers such as `NATIONAL_ID`, `PASSPORT`, `TAX_ID` and
`LEI_NUMBER`; `TRUSTED_ID` is not one of them, and is filed under its own *Trusted ID* heading
(verified via `search_docs(query='Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature group',
category='data_mapping')`, server 1.32.9, 2026-08-17; query re-verified on 1.37.19, docs index
2026-10-02 18:46 UTC, 2026-10-04, returning the *Identifiers* feature sections, *Identifiers >
Feature: TAX_ID* and *Identifiers > Feature: NATIONAL_ID*; the same measurement served
*Identifiers > Feature: PASSPORT*, *Identifiers > Feature: LEI_NUMBER* and *Trusted ID > Feature:
TRUSTED_ID*) — counts the group
as present when **any** member is populated. That is the right answer to *does this record carry an
identifier at all*. It is not evidence for *will these two sources join*, because a join needs
presence-of-**same**, not presence-of-any.

⚠️ **The guards above all protect the number's accuracy; this one protects its interpretation, and
that is a different failure.** Two sources both scored **IDENTIFIER 100%**, and the evaluation report
named them the highest-confidence cross-source pair, "both carrying LEI". One carried **2,375** LEI
values; the other carried **one**, across 137 records — its identifiers were national IDs and
passports. Exactly one LEI value was shared in the whole dataset: the prediction was wrong by ~38x on
the attribute it named, and nothing disproved it until **after loading**, when the match keys showed
LEI in a single match key. ⛔ **The 0%/100% sanity-check above does not catch this**: it fires on a
suspiciously uniform figure as a probable *measurement* failure, and here the 100% was entirely real
— so a guide following that instruction confirms the number and proceeds with the wrong inference
intact.

**So, before naming any expected cross-source pair:** count the **distinct values shared on the named
attribute**, not the group scores. The profiling pass already holds the values, so this is cheap. If
that count was not run, write the pair as a *candidate, overlap unmeasured* — a
prediction is still useful, but an unmarked one is what did the damage.

This is not a corner case. Mixed person/organization sources are the norm in KYC, AML, sanctions
screening, vendor MDM and beneficial-ownership work — several of this bootcamp's headline use cases.
One sanctions list with **NAME and ADDRESS on 100% of records** scored **52% completeness / 69%
overall** — squarely in "recommend fixing before mapping" below — because person-oriented features
(DOB at 32%, and others like passport and gender) were averaged across a source where **71 of 110
records are ORGANIZATIONS**. Rescoring each record against the features applicable to its own type
gave **97%**. Trusting the first figure would have sent the bootcamper to remediate data with nothing
wrong with it.

**Derive applicability from the Entity Specification, not from a list in this file.** The
specification states the type in its own wording, so `search_docs(query='what features to map',
category='data_mapping')` answers it directly in the specification's *What features to map*
section — read the feature's description and section heading:

| What the specification says | Applies to |
|---|---|
| `DOB` — "**Person** date of birth" | PERSON |
| `NATIONALITY` / `CITIZENSHIP` / `PLACE_OF_BIRTH` — "**Person** …" | PERSON |
| `NAME` (person) — "Personal names… `NAME_FIRST`, `NAME_LAST`" | PERSON |
| `REGISTRATION_DATE` / `REGISTRATION_COUNTRY` — section heading "**(organizations)**" | ORGANIZATION |
| `NAME` (organization) — "Organization legal or trade name… `NAME_ORG`" | ORGANIZATION |
| `ADDRESS`, `PHONE`, `EMAIL`, identifiers | either — do not exclude these |

(Verified against MCP server 1.37.14, docs indexed 2026-09-28 03:23 UTC, 2026-09-28. Re-read it for
the source you are assessing rather than trusting this table — it is an illustration of *how the
specification marks type*, not a substitute for asking, and it is deliberately partial: features not
listed here still have to be checked the same way, INV-080.)

**Records with no `RECORD_TYPE`.** The specification calls `RECORD_TYPE` *"Recommended"*, not
required, and says to leave it blank when the type is unknown — so a record may legitimately have
none. Score those against the features that apply to **any** type, and **report how many records were
scored that way**. A source where most records carry no `RECORD_TYPE` is itself a finding worth
raising (it also forgoes the cross-type resolution protection the specification says `RECORD_TYPE`
provides), and it must not be hidden inside an aggregate.

⛔ **Extend the uniformity sanity-check above with this case: a low completeness score on a source
whose NAME and ADDRESS coverage is high is a probable applicability error, not a data problem.**
Check the record-type mix before reporting the score or routing anyone to remediation (INV-264). The presence
rules above are unchanged — they decide whether a *value* is there; this decides whether the feature
belonged in the denominator at all.

⛔ **(INV-174, INV-264) Before reporting the score, print a per-`RECORD_TYPE` presence breakdown for
EVERY field you marked as applying to BOTH types — and treat a 100%/0% split as an applicability
error that stops the score.** No real field is present on every record of one type and none of the
other; that shape is the signature of a wrong applicability set, not a finding about the data. The
breakdown costs nothing — the profiling pass already holds both per-type counts.

⚠️ **This is a precondition, not another heuristic.** The check above fires *after* a low score
exists and keys on a NAME/ADDRESS pattern; this one runs *before* any score is reported and keys on
the applicability set itself, which is the input that was wrong. On 2026-08-25 four fields on a
72,799-record source were marked "both" while measuring 100% / 91.5% / 42.3% / 100% on
`ORGANIZATION` and **0%** on `PERSON` — the source's person records are officer and contact records
attached to a company, where a business address structurally cannot exist. The source scored 70.5%
and landed in the remediation band; corrected, it scores 85.7% and passes. ⛔ **(INV-174) The applicability
set is authored by hand per source, so getting it wrong is the default failure rather than an
unusual one** — which is why it needs a check by construction rather than an instruction to be careful.

Use these thresholds to guide the decision:

- **≥80% quality score** → Proceed to Phase 2 (mapping). Data quality is strong enough for
  meaningful entity resolution.
- **70-79% quality score** → Warn the user. Quality gaps exist: suggest specific fixes (fill
  nulls, standardize formats, deduplicate within source). Proceed to Phase 2 if the user
  accepts the risk, but document the quality gaps.
- **<70% quality score** → Strongly recommend fixing data quality before mapping. Entity
  resolution results will be poor. Help the user identify the biggest quality issues and create
  a remediation plan. Only proceed if the user explicitly chooses to continue.

**What this score does not measure.** It scores completeness, format consistency, and duplicate
rate — all *structural* properties of one source in isolation. It says nothing about whether a
field will be mapped to a feature that **means** the same thing, and nothing about how two sources
will interact once resolved. A source can score 86% and still carry a mapping that suppresses
legitimate merges. Present the number as "the data is clean enough to map", never as "the mapping
will be correct" — semantic correctness is only established after loading, by the match-key audit
in Data processing.

**If the field list itself looks implausible, this score is not yet meaningful.** The dynamic-key
sanity check (>~100 fields or >50 distinct field patterns — INV-118) runs on the `mapping_workflow`
profile in Phase 2 step 9, *after* this step, so on the first pass you will not have its verdict
here. Two consequences:

- **Now:** if the field list you compared against the Entity Specification in step 4 already looks
  implausibly wide, say so, treat this score as provisional, and expect step 9 to confirm it.
- **On return from Phase 2 step 9:** when that check trips, re-run this step after pre-processing
  and re-profiling rather than keeping the first score — a score averaged over hundreds of phantom
  fields is not meaningful, and it is this score that routes the gate below.

Present the assessment clearly:

```text
Data Quality Assessment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: CUSTOMERS_CRM
  Field completeness:  82%  (name: 99%, phone: 75%, email: 68%)
  Format consistency:  90%
  Duplicate rate:       3%
  Overall quality:     78%  ⚠ Acceptable — some gaps (see below)
  Type/name check:     0 of 4,210 PERSON-typed records are candidates

Source: VENDORS_LEGACY
  Field completeness:  45%  (name: 90%, phone: 20%, email: 15%)
  Format consistency:  55%
  Duplicate rate:      12%
  Overall quality:     42%  ⚠ Recommend fixing before mapping
  Type/name check:     3 of 12 PERSON-typed records are candidates (see below)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

⛔ **The status label MUST match the band above** — `✅` only at ≥80%, `⚠ Acceptable — some gaps`
at 70-79%, `⚠ Recommend fixing before mapping` below 70%. Derive the label from the computed score
rather than copying one from this example; a `✅` beside a 78% tells the bootcamper the gate said
"proceed" when it is about to ask them to choose.

> **Data source registry:** After computing the quality score, update the source's
> `quality_score` field in `config/data_sources.yaml` and set `updated_at`. If the score is
> below 70, add an `issues` list entry describing the quality concern.

<a id="type-name-check"></a>

### Type/name check: PERSON-typed records with organization names

⛔ (INV-300) **This is the canonical statement of the type/name check.** (INV-335) Step 5a sub-step 3a, Step
7's report and Phase 2 steps 10, 11, 13 and 18 point here and add only what their own site needs.

**Why it exists.** The Entity Specification says `RECORD_TYPE` *"prevents records of different
types from resolving"* (*Feature: RECORD_TYPE*, via `search_docs(query='RECORD_TYPE PERSON
ORGANIZATION prevent records of different types from resolving', category='data_mapping')`, MCP
server 1.37.14, docs index 2026-09-28). So a record typed PERSON that is really an organization
cannot merge with that organization's records in another source, however exactly the name and
address agree. Nothing above sees it, because every per-type guard trusts the type. On 2026-09-25,
26 of one CORD source's 31 PERSON-typed records had names ending `LLP`, `LP`, `PLC` or `LIMITED`.
That one conflict held apart 17 of the 50 cross-source possible-match pairs, and it was found only
after loading, when a near-miss was explained.

Run it over **every record** of each source, not a sample: the count is the source's own figure.

1. **Which records are tested.** Those whose `RECORD_TYPE` is `PERSON`: the record's own attribute
   on a Senzing-ready source, and on a raw source the field Step 4 matched to `RECORD_TYPE`. A
   source with no such field has zero PERSON-typed records.
2. **Which name is read.** Whichever name attribute the record carries: `NAME_FULL`, `NAME_ORG`, or
   the parsed person fields joined in order. That includes a name attribute carrying a leading
   label (the sense Step 5a's coverage check allows for) and the `NAME` objects inside a `FEATURES`
   array. On a raw source, read the field Step 4 matched to a name.
3. **The test.** A record is a **candidate** when its name's **final whole token** is on the list
   below: split on whitespace, trailing punctuation removed, compared case-insensitively. Only a
   whole final token counts, so `LIMITED EDITIONS SMITH` and `PHILIP` are not candidates.

   `LLP`, `LP`, `PLC`, `LIMITED`, `LTD`, `LLC`, `INC`, `CORP`, `CORPORATION`, `GMBH`

   ⚠️ **This suffix list is the plugin's own heuristic, not a Senzing fact (INV-080).** No MCP route
   serves one: `search_docs(query='organization name suffix tokens LLC LTD INC person or
   organization name classification')` returns the Entity Specification's NAME rules and libpostal
   scripts, none of them a suffix list (MCP server 1.37.14, docs index 2026-09-28). If a route
   serves one later, switch to it. The list is short on purpose. It leaves out tokens that are also
   surnames or name particles, because a false candidate costs the Bootcamper a question and a
   wrong retype costs a real person their matches.
4. **Report it for every source, as candidates.** Put the count in the assessment above, zero
   included (`Type/name check: 0 of 4,210 PERSON-typed records are candidates`). For a source with
   one or more, give the count out of the PERSON-typed total and up to ten candidate names, and say
   where they came from:

   > "[SOURCE_NAME]: [N] of [M] PERSON-typed records have a name that ends like an organization's,
   > for example [names]. These are candidates from a suffix test, not confirmed errors."

   With zero candidates, or zero PERSON-typed records, report the zero and ask nothing.
5. **Ask about each source with one or more candidates**, one source per turn:

   👉 **How should the mapping type the [N] candidate records in [SOURCE_NAME]? Reply with a number:**

   1. Retype them to ORGANIZATION, except any you name as a real person.
   2. Keep them as PERSON.

   *(Internal: end the turn on this question and wait.)*

   - **Option 1:** ask which candidates, if any, are real people, and take "none" as an answer.
     Every other candidate is retyped. Write the section below with the rule and those exceptions.
   - **Option 2:** write the section below with the cost stated, and change nothing else.
6. **Write the decision to `docs/mapping/{source_name}_mapper.md`**, under a `## Record Type
   Check` section. If the file does not exist yet, create it with its `# Mapping Specification:
   {SOURCE_NAME}` title and this section only. Phase 2 step 18 writes the rest of it and keeps this
   section as written.

   ```markdown
   ## Record Type Check

   - **Candidates:** [N] of [M] PERSON-typed records (suffix heuristic, Module 5 Phase 1 step 6)
   - **Decision:** Retype / Keep as-is
   - **Rule (retype):** a record whose `RECORD_TYPE` is `PERSON` and whose name's final whole
     token (trailing punctuation removed, case-insensitive) is one of [the list above] is emitted
     with `RECORD_TYPE` `ORGANIZATION`, and its name is mapped as `NAME_ORG` only, never as parsed
     person fields and never as `NAME_FULL`. The `NAME_ORG` value is the single name field's value
     as-is, or the parsed person fields joined with single spaces, in the order Module 5 Phase 1
     Step 6 sub-step 2 reads them. Exceptions, kept `PERSON`: [the names or RECORD_IDs given, or
     none]
   - **Cost (keep):** these [N] records stay `PERSON`, so they cannot merge with organization
     records in other sources. Such pairs stay possible matches, held apart by the record type.
   ```

   Write only the rule line for a retype and only the cost line for a keep. The name rule (INV-336)
   follows the Entity Specification's *Feature: NAME*: *"use `NAME_ORG` for organizations"*, and
   *"do not mix `NAME_ORG` with parsed person fields in the same object"* (the same suffix query
   above returns that section, MCP server 1.37.14, docs index 2026-09-28).

A source already checked in Step 5a sub-step 3a reuses that count and those names here. Do not run
the check again. Its report and question belong here, because Step 5a routes such a source on to
this step.

⛔ (INV-048) **The check reports and asks; it never blocks the module.** If it cannot run, for
example because no name attribute can be identified, say so in Step 7's report and continue.

⛔ (INV-173) **Never undo the Bootcamper's retype to turn a validation gate green.** If Phase 2's
verbatim check flags a retyped record's `NAME_ORG` joined from parsed name fields, follow that
step's exemption procedure (`phase2-data-mapping.md`, "What to do — in this order"): record the
derivation and its reason in the mapper notes, then proceed.

**Checkpoint:** write step 6.

**Visualization checkpoint:** Offer a visual of the quality assessment (coverage bars per
source, per-field completeness). Pin the offer verbatim:

> 👉 **Would you like a visual of the quality assessment (coverage bars and per-field completeness)?**

If the bootcamper accepts, generate a self-contained HTML page and save it to
`docs/visualizations/` (INV-070). (The full Visualization Protocol / `visualization-guide` is a later
porting phase; offer directly for now.)

⛔ **This page is a bootcamper-facing visual deliverable, so the four rules below bind it** — it is
saved, kept, and shareable, exactly like the Truth Set app's snapshot. See
`../bootcamp-onboarding/ground-rules.md` → "Visual deliverables (Senzing brand)" for the first two
and `../module-03b-truthset-visualization/visualization-api-reference.md` → "Rendering contract" for
the third; both are the statements of record, so read them rather than reconstructing the rules here.

1. **Brand tokens, not an ad hoc palette** (INV-081): take colors and typography from
   `${PLUGIN_ROOT}/scripts/brand_tokens.py` (skill-relative fallback
   `../../scripts/brand_tokens.py`, INV-252), degrading gracefully if the module cannot be
   imported.
2. **Renders offline** (INV-081/INV-091): **no CDN, no web font, no remote script.** If you need a
   charting library, inline the vendored `${PLUGIN_ROOT}/scripts/vendor/d3.v7.min.js`
   (skill-relative fallback `../../scripts/vendor/d3.v7.min.js`, INV-252); plain
   HTML/CSS bars need no library at all and are the better default here. A `<script src="https://…">`
   makes the page render blank on an air-gapped workstation — which Senzing evaluations frequently
   are — with no error anywhere.
3. **Escape every value that came from the data** (INV-106): field names, sample values and source
   names are the bootcamper's own strings. Escape them for the context they land in — HTML text,
   attribute, and, if you embed a JSON payload in an inline `<script>`, `<`, `>` and `&` as their
   `\uXXXX` escapes, since a value containing `</script>` otherwise breaks out of the script block in
   an artifact that gets kept and shared.
4. **Verify the rendered page, not the exit status** (INV-129): open it and confirm the bars and the
   per-field numbers actually drew. Best-effort and non-blocking, like every check in this module.

**Capture it for the recap, right after the page is written and verified.** Follow
`../bootcamp-onboarding/module-completion.md` → "Capturing visualization screenshots", using its
`--single` case: this page has no tabs, so it is one image, with `{name}` the page's file name
without `.html`. That section is the statement of record for the helper, its exit codes and the skip
rules (INV-300). Record the PNG path in the step-6 checkpoint, rewriting it in the same turn
(INV-146). It is embedded in this module's recap at module close.

## 7. Summarize findings and save the evaluation report

Create `docs/data_source_evaluation.md`:

```markdown
# Data Source Evaluation Report

**Date:** [Current date]
**Project:** [Project name]

## Summary
- Total data sources: [count]
- Entity Specification-compliant: [count]
- Needs mapping: [count]
- Needs enrichment: [count]

## Data Source Details

### Data Source 1: [Name]
**Status:** [Entity Specification-compliant / Needs mapping / Needs enrichment]
**Location:** `data/raw/[filename]`
**Records:** ~[count]
**Fields:** [count] columns

**Evaluation:**
- [Field analysis]
- [Entity Specification compliance notes]

**Reason:** [Why it needs mapping or is compliant]

**Record type check:** [N] of [M] PERSON-typed records are type/name candidates. Decision:
[Retype / Keep as-is / none needed]

**Next step:** [Phase 2 (mapping) / Data processing (loading)]

### Data Source 2: [Name]
[Same structure]

## Mapping Priority
1. [Data source] - [Reason for priority]
2. [Data source] - [Reason for priority]

## Cross-Source Outlook
- [Source A] × [Source B] — **[measured | candidate, overlap unmeasured]**
  - Shared attribute: [the named attribute, e.g. `LEI_NUMBER`]
  - Distinct values shared: [count] (of [A count] in A, [B count] in B)
```

Write the **Record type check** line for every source, zero included: `0 of [M]`, or `0 of 0` for a
source with no PERSON-typed records, with the decision `none needed`. A fast-pathed source gets the
line too, from Step 5a sub-step 3a. The count and the decision come from Step 6's type/name check,
the canonical statement (INV-300), and the decision is the one written to the source's mapper notes.

⛔ **Every named cross-source pair in this report carries one of two labels, and neither is
optional (INV-261).** `measured` requires a **distinct-value overlap count on the named attribute**; anything
else is `candidate, overlap unmeasured`. ⚠️ **A group completeness score is not a measurement for
this purpose** — see the ⛔ at the completeness definition above. Two sources at IDENTIFIER 100% were
once written up as the highest-confidence pair "both carrying LEI" when exactly **one** LEI value was
shared in the entire dataset; the group scores were correct and the inference was wrong by ~38x.

⚠️ **This report is a deliverable the Bootcamper keeps** — it is rendered to
`docs/data_source_evaluation.pdf` at graduation and it shapes the load-order rationale — so an
unmarked prediction reads as a finding long after the run. Nothing between writing it and loading
re-examines it. Never rank pairs by confidence on group coverage alone; where the overlap was not
counted, say so in the report rather than omitting the pair.

### Quality gate: iterate vs. proceed

After presenting the quality assessment, guide the user's decision.

**Where the score gates — 70-79% and below 70% — ask exactly one 👉 question to close the turn**,
except on a fixed dataset with nothing mechanical left to fix, which Step 7b continues without one.
At **≥80% there is no decision to make**: state the result and continue straight into Phase 2 in the
same turn, letting Phase 2's first step supply that turn's single 👉.

⛔ **Do not invent a gate question for the ≥80% branch.** "Your data is fine, shall we continue?" is
exactly the pointless question INV-012 forbids and INV-006 counts against the ask-once budget, and
improvising one breaches INV-056, which pins every gate question's wording precisely so it cannot
drift at runtime. The ≥80% branch is the common one for curated data — a CORD source routinely
scores there — so this is the path most runs take.

⛔ **(INV-345) On a `provenance: synthesized` source, disclose before the 👉 — those gaps are deliberate.**
Read `provenance` for this source from `config/data_sources.yaml`. When it is `synthesized`, Module
4's Step 2 was **required** to manufacture exactly these gaps (INV-239: *"missing values in non-key
fields, enough to put at least one source in the 70-79% band… That band opens the remediation
conversation, so it has to be reachable"*) — so this gate is firing as designed, and "improve the
data" means regenerating data the bootcamp authored minutes ago. Say so in one line **before** the
question, because anything meant to inform the answer goes before it
(`../bootcamp-onboarding/ground-rules.md` → the 👉 protocol):

> "One thing worth knowing before you choose: this source was generated for the bootcamp, and its
> gaps are deliberate — they were built in so this assessment would have something to find.
> Improving them means regenerating data we authored a few minutes ago. That is a fair choice, it
> is just not the same as fixing a real dataset."

Then present the applicable pinned question — the band's question below, or its no-progress variant
in Step 7b — **unchanged, with both options live** (INV-056).

⛔ **(INV-345) Never silently regenerate.** Rewriting the Bootcamper's data as the answer to a question they
were not told meant that is the failure this disclosure exists to prevent.

- **Quality ≥80%:** "Your data quality is strong. Let's continue to mapping." **(statement, no 👉;
  continue into Phase 2 this turn)**
- **Quality 70-79%** *(where mechanical work remains; with nothing mechanical left to fix, present
  this band's no-progress variant in Step 7b instead)*: "Your data quality is acceptable but has
  some gaps. You can continue to mapping now, or improve the weakest fields first."

  👉 **Your data quality is acceptable but has some gaps. What would you like to do? Reply with a number:**

  1. Improve the weakest fields first.
  2. Continue to mapping now.

- **Quality <70%** *(where mechanical work remains; with nothing mechanical left to fix, present
  this band's no-progress variant in Step 7b instead)*: "Your data quality needs attention before
  mapping will produce good results. I'd recommend focusing on [specific issues: e.g., filling
  missing phone numbers, standardizing address formats]."

  👉 **Your data quality needs attention before mapping will produce good results. What would you like to do? Reply with a number:**

  1. Work on improving the data first.
  2. Proceed anyway, knowing the results may be limited.

*(Internal: in the two gating branches, end the turn on the applicable question and wait — Step 7b's
fixed-dataset statement excepted, which continues into Phase 2. In the
≥80% branch no question applies — do not manufacture one; continue into Phase 2 this same turn and
end on its first 👉.)*

### 7a. The improve path — what option 1 means, in both gating bands

⛔ **(INV-284) This step is what the gate's first option executes.** Both gating bands offer to improve the
data first, and until this step existed the turn ended on the question with nothing to run: no
procedure, no re-score, no way back to the gate. A pinned question whose answer has no handling step
is the unsatisfiable-instruction shape that teaches a guide to read the surrounding ⛔ rules as
advisory, so treat this as executable, not advisory.

1. **Name the weakest fields from the score you already computed** — do not re-measure. Step 6's
   assessment already identifies them per field (e.g. *phone missing in 60% of records, address 44%,
   date of birth 34%*). Name the worst three with their figures, worst first.

2. **Split them by what can honestly be fixed here, and say which is which.** The score has three
   dimensions and they are not equally repairable:

   - ✅ **Fixable in this module — `format_consistency` and `duplicate_rate`** (0.25 and 0.05 of the
     score). These are mechanical: normalize the minority formats in a field to its dominant one
     (phone punctuation, date layout, casing, whitespace, state/country spellings) and resolve
     records whose `(DATA_SOURCE, RECORD_ID)` pair repeats, per Step 6's own definitions. Do this
     work **for** the Bootcamper rather than asking them to; it is deterministic and they can read
     the diff.
   - ⛔ **(INV-284) Not fixable here — `completeness`** (0.70 of the score, and usually what put the source in
     the band). **A missing value cannot be invented**, and offering to fill one is offering to
     fabricate data. Say that plainly. The honest route is a better export from the source system,
     or for a generated source a regeneration, which is Data collection's job. Name it, and say it
     is offered at the re-presented gate as Step 7b's return to Data collection, once nothing
     mechanical is left to fix. Its wording, its handling and where the bootcamp picks up are stated
     in Step 7b, not here (INV-300).

3. **Write the improved data as a NEW file; never overwrite what was collected.** Put it beside the
   original as `data/raw/<source>-improved.<ext>` and record the original `file_path` in the same
   entry so nothing is lost. `data/raw/` holds source data as received (INV-050), and the original
   stays exactly as received.

4. ⛔ **(INV-243) Update every registry field the new file changes — not just `file_path`.** The
   entry is a set of claims about the file it points at, and repointing it makes each of them a
   claim about the improved file. Re-measure and rewrite, in `config/data_sources.yaml`:

   - **`file_path`** → the improved file.
   - **`record_count`** → **re-counted from the improved file.** ⛔ **(INV-243) This is the one that does
     damage if it is skipped.** Resolving duplicates removes records, and Module 6 Phase B compares
     its loaded count against the `record_count` written here (INV-243) — so a stale figure reports
     a *correct* load as short by exactly the number of duplicates this step just removed, one
     module downstream of the cause. Say both figures to the Bootcamper when it changes, with the
     reason ("1,000 → 984 records; 16 duplicate `(DATA_SOURCE, RECORD_ID)` pairs resolved").
   - **`file_size_bytes`** → re-measured.
   - **`quality_score`** → the re-scored figure from step 5 below, once it is computed.
   - **`updated_at`** → the current ISO 8601 timestamp.

   ⛔ **(INV-203) Leave `expected_record_count`, `validation_status` and `validation_checks` describing the
   ORIGINAL fetch, and say in the entry that they do.** Those fields record that a *fetched* file
   arrived with a 2xx status and a count matching what the provider stated (INV-203); the improved
   file was derived here, not fetched, so re-pointing them at it would assert a check nobody ran.
   ⚠️ **`record_count` is the opposite case and must NOT be left alone for the same reason** — it is
   a measurement of the file, and the file changed, so leaving it stale is what makes the entry
   wrong rather than what keeps it honest.

5. **Re-score the source with Step 6's formula and re-present the gate with the new figure**, naming
   the before and after (e.g. *"75.1 → 79.4"*).

   ⛔ **Re-presenting the gate here is NOT an INV-006 repeat, and a guide must not suppress it as
   one.** INV-006 forbids re-asking a question already answered about the same state; the score has
   changed, so this is a new question about a new state, and the Bootcamper's earlier answer was
   about the old figure. Present whichever band's pinned question the **new** score selects — a
   source that crossed into ≥80% gets no question at all and continues into Phase 2 this turn. A
   pass that fixed everything leaves nothing mechanical, so the band's form is Step 7b's.

6. **When nothing was fixable, say so rather than looping.** If the gaps are entirely completeness,
   there is no mechanical work to do: say so, and never re-present an unchanged score as an
   improvement. Step 7b now applies; it states how the unchanged score is identified and what the
   gate offers instead (INV-284).

⚠️ **On a `provenance: synthesized` source this path is still available and still honest** — the
disclosure above has already told the Bootcamper the gaps are deliberate. Normalizing formats in
generated data is real work with a real re-score; if they ask to regenerate instead, that is Step
7b's return route, and it is their call to make with the disclosure in hand.

### 7b. Return to Data collection — when nothing mechanical is left to fix

⛔ **(INV-300) This is the canonical statement of the gate's no-progress variant and of the return
route it offers.** The gate above, Step 7a and Module 4's receiving branch point here; none of them
restates it.

**When it applies.** Check every time a gating band's question (70-79% or <70%) is about to be
presented: the first time, after a Step 7a pass that fixed everything, and after one that found
nothing. **Nothing mechanical is left to fix** when Step 6's measures for this source show
`format_consistency` at 100% **and** no repeated `(DATA_SOURCE, RECORD_ID)` pair, the only two
dimensions Step 7a step 2 calls fixable here, or when a Step 7a pass has just found nothing it
could fix. Then this step's form of the band replaces the band's question. Where mechanical work
remains, present the band's question above unchanged.

⛔ **(INV-284) Never offer an improvement option when nothing mechanical is left to fix.** Step 7a
would find nothing to do and hand back the same gate, so the option is a dead choice that loops.
Observed 2026-10-01: STORE_POS (synthesized) went 73.5 → 79.0 on format normalization, and the
Bootcamper then chose "Improve the weakest fields first" twice more with nothing left to improve.

**After a pass that found nothing, say first that the score is unchanged** (one statement line,
before the 👉): "The score is unchanged at [score]: there was nothing mechanical left to fix."

**Read `provenance` for this source from `config/data_sources.yaml`**; it selects the form.

**`synthesized`, `own` or `unknown` → the pinned no-progress variant (INV-056).** The synthesized-source
disclosure above still precedes it on a `synthesized` source. The question line is the band's own:

- **Quality 70-79%:** "Your data quality is acceptable but has some gaps. What is left is missing
  values, which this module cannot fill; a better export, or a regeneration of generated data, can."

  👉 **Your data quality is acceptable but has some gaps. What would you like to do? Reply with a number:**

  1. Return to Data collection for this source.
  2. Continue to mapping now.

- **Quality <70%:** "Your data quality needs attention before mapping will produce good results.
  What is left is missing values, which this module cannot fill; a better export, or a
  regeneration of generated data, can."

  👉 **Your data quality needs attention before mapping will produce good results. What would you like to do? Reply with a number:**

  1. Return to Data collection for this source.
  2. Proceed anyway, knowing the results may be limited.

*(Internal: end the turn on the applicable question and wait.)*

**`cord` or `free_data` → no return; a statement, and no 👉 at this gate.** Both are fixed datasets,
one from `get_sample_data` and one from the free-data catalog, so completeness cannot change and a
return would offer nothing (INV-012). Say the band's line, then continue into Phase 2 in the same
turn, letting Phase 2's first step supply that turn's 👉:

- **Quality 70-79%:** "Your data quality is acceptable but has some gaps. What is left is missing
  values, and this is a fixed dataset, so its completeness cannot change. Let's continue to
  mapping." **(statement, no 👉; continue into Phase 2 this turn)**
- **Quality <70%:** "Your data quality needs attention before mapping will produce good results.
  What is left is missing values, and this is a fixed dataset, so its completeness cannot change,
  and the results may be limited. Let's continue to mapping." **(statement, no 👉; continue into
  Phase 2 this turn)**

**Handling each option (INV-284).**

- **Option 2** is the band's own second option and is handled as it is there: continue into Phase 2
  this turn. Nothing is written for the return.
- **Option 1** runs the return route below. ⛔ **(INV-006) Option 1 IS the return route's pinned
  question: the answer is the go-ahead, so ask no second confirmation.** The same route runs when the
  Bootcamper asks, in their own words, for a regeneration or a new export of this source.

**The return route, for this source only:**

1. **Record the return in one quiet write** to `config/bootcamp_progress.json`: set `current_step`
   to `"7b"` and add

   ```json
   "collection_return": {
     "source": "<DATA_SOURCE>",
     "provenance": "synthesized | own | unknown",
     "from_band": "70-79 | <70",
     "resume_step": 6,
     "started_at": "<ISO 8601>"
   }
   ```

   with `resume_step` from the table below. ⛔ **(INV-284) `current_module` is not changed:** the
   Bootcamper stays in this module, and the key is what lets an interrupted return resume.

2. **Run Module 4's receiving branch** —
   [`../module-04-data-collection/SKILL.md`](../module-04-data-collection/SKILL.md#receiving-a-collection-return)
   Step 2 → "Receiving a `collection_return`", which says how each provenance is collected. Only the
   steps in this table run:

   | `provenance` | Module 4 steps that run | Module 5 resumes at |
   |---|---|---|
   | `synthesized` | Step 2's synthesized branch, regenerating this source only to `>=80` | **Step 6** (re-score): the schema is unchanged |
   | `own` | Step 2's provision question for this source, then Step 3 (verify) and Step 8 (tracking); Step 8a's volume check for this source only when the record count changed | **Step 4** (compare with the Entity Specification): a new export can change shape. Steps 5, 6 and the gate follow |
   | `unknown` | exactly as `own`; the answer sets `provenance` | **Step 4**, as `own` |

   ⛔ **(INV-284) Module 4's Step 9 does not run at all on a return:** no Module Completion, no
   second Module 4 recap section, no progress update and no transition question. Module Completion
   would move `current_module` past this module, and there is no module transition to ask about.

3. **Resume here.** When those steps finish, clear `collection_return` and set `current_step` to the
   resume step in one write, then continue at that step for this source. The gate is re-presented
   with the new score: ⛔ **(INV-284) that is a new state, NOT an INV-006 repeat**, so present
   whichever form the new score and this step's check select. At ≥80% there is no question.

4. **An interrupted return** resumes from `current_step: "7b"` with `collection_return` present:
   continue the return for the named source from the first Module 4 step not yet done, and do not
   re-present the gate, whose answer is already recorded.

**Success indicator:** ✅ All data sources categorized + `docs/data_source_evaluation.md`
created.

**Checkpoint:** write step 7.
