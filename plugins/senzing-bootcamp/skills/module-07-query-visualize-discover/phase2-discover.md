# Module 7, Phase 2a: Discover, Part A (steps 4a–4c)

Follow the ground rules. `🛑`/`⛔` are internal directives, never render them; signal a stop by
ending the turn on the single 👉 question and waiting. On load, read
`config/bootcamp_progress.json` and check which 4x sub-steps are already checkpointed under
`module_7_query.steps`. Resume from the first incomplete step; do not re-run completed
demonstrations.

Load this file when Phase 1 reaches step 4. When steps 4a–4c are complete, load
`phase2b-discover.md` for step 4d.

**No direct SQL and no fabricated methods (see SKILL.md):** every entity operation here
(`get_entity_by_record_id`, `why_records`, `why_entities`, `how_entity`) is generated SDK
code, source flags and signatures from `get_sdk_reference` and code patterns from
`reporting_guide(topic='entity_views', language='<chosen_language>')` / `sdk_guide`. These are SDK methods, not MCP
tools. Never query `database/G2C.db` tables directly.

## Step 4: Discover phase, advanced Senzing capabilities

The Discover phase introduces advanced Senzing capabilities using concrete examples from the
bootcamper's loaded data. It is opt-in, the bootcamper can decline or exit early at any
demonstration point.

### Introduction and opt-in

This opt-in is **independent of the visualization gate** in Phase 1 step 3c — ask it whether or
not the bootcamper chose additional visualizations there.

Present a brief introduction explaining what the Discover phase covers: why analysis
(understanding resolution decisions), how analysis (entity construction history), and
relationship networks (hidden connections). (Data-specific visualization suggestions are no
longer part of the Discover phase — they are offered at the Phase 1 step-3c visualization gate.)
Then ask whether to proceed.

👉 **Would you like to explore Senzing's advanced discover capabilities using examples from your own data?**

*(Internal: end the turn on this question and wait.)*

- **Declines:** write `discover_phase: "skipped"` to `config/bootcamp_progress.json` under
  `module_7_query` and return to `phase1-query-visualize.md` for the Query Completeness Gate.
- **Agrees:** write `discover_phase: "in_progress"` under `module_7_query` and continue to
  step 4a.

⛔ **Declining skips the walkthrough, not the findings.** This question governs whether the
bootcamper is *walked through* why/how/networks interactively. The data-discoveries deliverable
(`docs/bootcamp_data_discoveries.md` + `.pdf`) is produced on **every** path — including this
decline and both early exits below — at the convergence point in `phase1-query-visualize.md` →
"Data-discoveries deliverable". Do not present declining as giving up the findings, and do not
offer the deliverable as a consolation question; it is generated and announced either way. The two
halves have separate authorities: the interactive walkthrough is **offered** (INV-046 — a decline is
a requested skip), while `docs/bootcamp_data_discoveries.md`/`.pdf` is an **always-produced**
deliverable in INV-050's layout tree.

### Step 4a: Data pattern analysis

Analyze the bootcamper's loaded data to identify interesting entities for the Discover
demonstrations. Use the bootcamper's known record IDs, taken from the files Module 6 loaded: for
each source, read its `file_path` from `config/data_sources.yaml` (in `data/senzing-ready/` for a
mapped source, the original `data/raw/` file for a fast-pathed one) and take `DATA_SOURCE` and
`RECORD_ID` from its records.

1. **Identify multi-record entities (3+ records):** iterate over the loaded record IDs and, via
   generated SDK code, call `get_entity_by_record_id(data_source, record_id)` for each. Collect
   entities where `record_count >= 3`. These are candidates for the How Analysis demonstration
   (step 4c). Track the entity IDs and record counts.
2. **Identify cross-source entities:** from the multi-record entities in step 1, filter for
   entities whose constituent records originate from two or more distinct data sources. These
   are candidates for the Why Analysis demonstration (step 4b). An entity qualifies if its
   records array contains entries with different `DATA_SOURCE` values.
3. **Identify entities with relationships:** check the entity responses for relationship data.
   Count every entity with **one or more relationships of any kind, disclosed or discovered**:
   disclosed relationships are stated in the source data (like 'employer'), discovered ones are
   inferred by Senzing from shared attributes (like a common address). Both kinds count, because
   step 4d demonstrates both, and data that has only discovered links would otherwise skip it.
   These entities are candidates for the relationship network demonstration in step 4d; keep
   each one's relationship count, since step 4d starts from the entity with the most. Use relationship
   flags that return both kinds when calling `get_entity_by_record_id` (look up the flag names via
   `get_sdk_reference(topic='flags', filter='get_entity_by_record_id')`), and read where the
   relationships sit in the response, and how a disclosed one is marked, via
   `get_sdk_reference(topic='response_schemas', filter='get_entity_by_record_id')` before counting
   them (INV-115).
4. **SDK flag usage:** explain your flag choices as you go. For example: "I'm using
   `get_entity_by_record_id` with relationship flags so we can see which entities connect to
   others. This helps me find good candidates for the relationship network demonstration."
5. **Present a summary:** "I found N large entities (3+ records), M cross-source matches
   (records from multiple data sources), and K entities with relationships in your data." List
   the most interesting candidates by entity ID with a brief reason (e.g. "Entity 1234 has 5
   records from 2 sources" or "Entity 5678 has 3 relationships, 1 disclosed and 2 discovered").
6. **Graceful fallback for limited data:** if fewer than 2 multi-record entities exist,
   explain: "Your data has limited resolution results, most records resolved as singletons
   (one record per entity). This is common with small or homogeneous datasets." Adapt the
   remaining demonstrations to whatever entities are available. If only single-record entities
   exist, use them to demonstrate the SDK methods while explaining what richer data would show.
   Skip demonstrations that require unavailable patterns (e.g. skip relationship networks if no
   relationships exist) and note which steps are skipped and why.

**Checkpoint:** write step 4a to `config/bootcamp_progress.json` under
`module_7_query.steps.4a`, using this structure:
`{"status": "completed", "patterns_found": {"multi_record": N, "cross_source": M, "relationships": K}}`
where N, M, and K are the actual counts of multi-record entities, cross-source entities, and
entities with relationships (disclosed or discovered) found. The `relationships` key keeps its name,
but K is a count of **entities**, not of clusters or of relationships. Also set top-level
`current_step` to `"4a"`.

### Step 4b: Why Analysis introduction

Demonstrate Why Analysis using a concrete cross-source entity identified in step 4a. This
teaches the bootcamper how Senzing explains its resolution decisions.

1. **Entity selection:** select a cross-source entity from step 4a, one whose records come
   from two or more distinct data sources. Use the specific record IDs to call `why_records`,
   or the entity IDs to call `why_entities`. Prefer `why_records` for the initial demonstration
   because it compares two specific source records, which is easier to follow. State what you
   are using: "I'll use Entity [ID], which contains records from [Source A] and [Source B] —
   let's see why Senzing decided these belong to the same real-world entity."
2. **SDK method introduction:** before generating the SDK call, briefly explain the two Why
   Analysis methods:
   - `why_records`: compares two specific source records and explains why they resolved
     together. Use when you know exactly which two records to compare.
   - `why_entities`: compares two resolved entities and explains why they are (or are not) the
     same. Use when investigating whether two entities should merge, or auditing a split.
3. **SDK flags and response shape:** generate the `why_records` (or `why_entities`) call,
   confirming flag names via `get_sdk_reference(topic='flags', filter='why_records')` and the
   response structure via `get_sdk_reference(topic='response_schemas', filter='why_records')`
   before writing anything that parses it (INV-115):
   - `SZ_INCLUDE_FEATURE_SCORES`: explain: "I'm using SZ_INCLUDE_FEATURE_SCORES so we can see
     the numeric similarity scores for each feature comparison. This tells us how closely each
     attribute matched between the two records." It is also what the method already defaults to:
     the server documents `SZ_WHY_RECORDS_DEFAULT_FLAGS` as equivalent to this flag alone
     (`get_sdk_reference(topic='flags', filter='why_records')`, server 1.32.9, 2026-08-14).
   - **The why-key breakdown is `WHY_KEY_DETAILS`.** It sits at
     `WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS` — an object whose `CONFIRMATIONS[]` entries each
     name the feature that contributed (`FTYPE_CODE`, `TOKEN`, `SOURCE`) with its `SCORE` and
     `SCORE_BUCKET`. That is the path to parse for step 5
     (`get_sdk_reference(topic='response_schemas', filter='why_records')`, server 1.32.9,
     2026-08-14).
   - ⛔ **Its two sibling scalars are renamed the same way: `WHY_KEY` and `WHY_ERRULE_CODE`.**
     `MATCH_INFO` on a why response carries exactly four scalar-or-object members —
     `MATCH_LEVEL_CODE`, `WHY_ERRULE_CODE`, `WHY_KEY` and `WHY_KEY_DETAILS` — beside
     `CANDIDATE_KEYS`, `DISCLOSED_RELATIONS` and `FEATURE_SCORES`. `MATCH_KEY` and `ERRULE_CODE` are
     the **entity-side** names, carried on `RESOLVED_ENTITY.RECORDS[]` and `RELATED_ENTITIES[]`
     instead. So the rename is the whole `MATCH_*` family, not just the details object: a parser
     carried across from `get_entity` or from an export reads all three fields off the wrong names
     and each one renders blank rather than raising
     (`get_sdk_reference(topic='response_schemas', filter='why_entities', language='python')`,
     server **1.33.0, 2026-08-21** — that enumeration is the complete member list it returned).
   - ⚠️ **`CONFIRMATIONS[]` has a third state, and it is neither of the two above: present and
     empty.** Observed on every `why_records` call of a 2026-08-18 run — rules `SNAME_SSTAB` and
     `SF1_PNAME_CFF`, `SZ_INCLUDE_FEATURE_SCORES` in force — while `how_entity`'s
     `MATCH_KEY_DETAILS.CONFIRMATIONS[]` populated on the same entity (observation-only,
     INV-080/INV-149: no MCP route reports whether a given rule produces confirmations).
     **An empty array is a data/rule outcome, not a flag problem and not a parse error** — do not add
     flags for it and do not re-verify a path `response_schemas` confirms. **Fall back to
     `FEATURE_SCORES`**, which carries the same evidence (the feature, its score, its bucket) and
     populated normally on that run, so step 5's demonstration completes instead of being abandoned.
     Say that this pair's match key has no per-feature confirmation detail *on this data* and show the
     feature scores — never *"no value returned"*, which reads as a failure, and never an empty
     section rendered as a result. ⚠️ **Do not reconcile this with the absent case below into one
     absolute** (INV-169): the two were seen under different data, rules and SDK builds, and both are
     recorded with their conditions.
   - ⛔ **`WHY_KEY_DETAILS` may need `SZ_INCLUDE_MATCH_KEY_DETAILS` to appear at all — pass it,
     with a relations flag.** Two separate things are known here and neither governs the other
     (INV-169); read both before choosing flags.

     **What the server documents** (server **1.35.3**, 2026-09-01): the field's requirement is
     in `response_schemas`, not in `flags`.
     `get_sdk_reference(topic='response_schemas', filter='why_entities')` lists
     `WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS` with
     `requires_flags: ["SZ_INCLUDE_MATCH_KEY_DETAILS"]`, and that flag's row documents the
     relations dependency in its description. ⚠️ **The `flags` topic alone still points elsewhere**:
     `SZ_INCLUDE_MATCH_KEY_DETAILS`' own `response_paths` names only
     `RELATED_ENTITIES[].MATCH_KEY_DETAILS`, the **related-entity** object — so checking only that
     topic leaves the why-side field looking unattributed. Read both topics before concluding a
     field is populated by nothing.

     ⚠️ **What was observed, engine-side — observation-only, not an MCP claim** (INV-080/INV-149):
     on **Senzing SDK 4.3.4**, `WHY_KEY_DETAILS` was **absent** from `WHY_RESULTS[].MATCH_INFO`
     with `SZ_INCLUDE_FEATURE_SCORES` alone and with `+ SZ_ENTITY_INCLUDE_ENTITY_NAME`, and
     **present** once `SZ_INCLUDE_MATCH_KEY_DETAILS | SZ_ENTITY_INCLUDE_ALL_RELATIONS` was added —
     returning `+NAME score 95 (CLOSE)` and `+ADDRESS score 100 (SAME)` in `CONFIRMATIONS[]`
     (2026-08-16). A second run on **SDK 4.3.2** also found it absent without the flag
     (`SZ_WHY_RECORDS_DEFAULT_FLAGS | SZ_ENTITY_INCLUDE_ENTITY_NAME`; the raw `MATCH_INFO` keys
     were `CANDIDATE_KEYS, DISCLOSED_RELATIONS, FEATURE_SCORES, MATCH_LEVEL_CODE, WHY_ERRULE_CODE,
     WHY_KEY`). ⛔ **This is NOT a version floor:** the with-flag arm was never run on 4.3.2, so
     the evidence is equally consistent with "the flag is required on both" and says nothing about
     a boundary. Do not write one.

     **So: pass `SZ_INCLUDE_MATCH_KEY_DETAILS` together with a relations flag** — its documented
     `depends_on` still holds — and treat the breakdown as conditional rather than guaranteed.

     ⚠️ **This corrects a directive that used to forbid the flag here**, on the grounds that the
     breakdown was "already there without it". That claim came from a measurement whose **two arms
     both passed the flag**, so the flag's contribution was never varied and never observed; a
     negative about a flag needs an arm in which that flag is **absent**. Following the old ⛔
     produced a why demonstration with no match-key breakdown at all, and — because every other
     analytical field rendered — it read as *"this SDK doesn't provide that detail"* rather than
     *"a flag is missing"*. That is INV-179's silent-blank shape, reached by obeying the step's own
     instruction.
   - ⛔ **Dump `MATCH_INFO`'s top-level keys before writing the parser, and never render an empty
     section.** Print the keys you actually got; if `WHY_KEY_DETAILS` is not among them, say so
     explicitly — *"match-key breakdown not returned by this SDK for these flags"* — and fall back
     to `FEATURE_SCORES`, which carries the same per-feature evidence and was fully populated in
     both runs above. An omitted section is indistinguishable from a feature the engine does not
     have; a stated absence is what turned this defect up in the first place.
   - ⚠️ **Confirm each flag's type, not only its name.** Where a binding takes a *collection* of
     flags, a composite constant may not belong to that collection's element type, and must then
     be passed as its members instead — `get_sdk_reference` lists those under `composite_members`
     (`SZ_ENTITY_INCLUDE_ALL_RELATIONS` is the four relation flags; server 1.32.9, 2026-08-14).
     Confirm the argument type with `get_sdk_reference(topic='parameters', filter='why_records',
     language='<chosen_language>')` alongside the names (INV-002, INV-132) — the parameters topic
     is the only route that reports a binding type; `topic='flags'` returns composites and single
     flags in the same shape and names no type (server 1.33.0, 2026-08-26). The full rule, with the
     worked Java example, is in `phase1-query-visualize.md` beside the composite-flag guidance.
     ⚠️ **Java carries both shapes under one name, and an earlier version of this note named the
     wrong one.** Verified against the installed `sz-sdk.jar` 2026-08-26 (`javap` + `javac`;
     observation-only, INV-080/INV-149): `whyRecords` takes `Set<SzFlag>`, and
     `SzFlag.SZ_ENTITY_INCLUDE_ALL_RELATIONS` is a `Set<SzFlag>` static field — **not** an enum
     constant — so it is merged with `addAll` rather than listed in `EnumSet.of`. The `long` bitmask
     of the same name lives in the *plural* class `SzFlags`, which cannot be passed to that argument
     at all. This note previously said "the composite is a `long` bitmask", which describes `SzFlags`
     and sends the reader to the class that does not fit the parameter.
4. **Plain-language explanation of the output:** after receiving the response, explain it
   covering three aspects:
   - **Features that matched:** list which features (NAME, ADDRESS, DOB, PHONE, etc.) were
     compared and which matched. "The NAME and ADDRESS features both matched between these
     records."
   - **Feature scores:** for each comparison, explain the numeric similarity score. "The name
     comparison scored 95 out of 100, meaning the names are very similar but not identical —
     because one record has 'Robert Smith' and the other has 'Bob Smith'." Explain the range
     (higher = more similar).
   - **Matching principle:** explain which principle applied to each comparison, exact match
     (identical values), close match (very similar, like name variants), or likely match
     (similar enough to contribute). "The name matched on a 'close match' principle because
     'Robert' and 'Bob' are recognized name variants."
5. **Match-key breakdown:** present the why-key string from
   `WHY_RESULTS[].MATCH_INFO.WHY_KEY` (e.g. `+NAME+ADDRESS`) and break it down, using the
   `WHY_KEY_DETAILS` confirmations from step 3 to say which feature produced each component:
   - Each `+FEATURE` component is a feature type that contributed positively to the resolution.
   - Explain each in context: "The `+NAME` means the name features matched strongly enough to
     contribute. The `+ADDRESS` means the address features also matched. Together these two
     matching features were sufficient for Senzing to resolve these records."
   - If the match key contains `-FEATURE` components (negative contributions), explain those
     too: "A `-` prefix means that feature did NOT match, but the other matching features were
     strong enough to override it."
6. **Practical use cases:** explain when Why Analysis is useful in practice:
   - **Auditing decisions:** "When a stakeholder asks 'why did you merge these two customer
     records?', why analysis gives the exact answer with scores and matching principles."
   - **Debugging unexpected merges:** "If two records merged that shouldn't have, why analysis
     shows exactly which features caused it, helping you decide whether to adjust configuration
     or add a data fix."
   - **Compliance reporting:** "For regulated industries (KYC, AML, patient matching), why
     analysis provides the auditable evidence trail showing how each resolution decision was
     made."
7. **Transition:**

   👉 **What would you like to do next? Reply with a number:**

   1. Continue to the next demonstration — How Analysis (seeing how this entity was built step by step).
   2. Proceed to module completion.

   *(Internal: end the turn on this question and wait.)* If the bootcamper chooses to exit,
   write `discover_phase: "skipped"` to `config/bootcamp_progress.json` and return to
   `phase1-query-visualize.md` for the Query Completeness Gate.

**Checkpoint:** write step 4b under `module_7_query.steps.4b`, using
`{"status": "completed", "entity_demonstrated": <entity_id>}` where `<entity_id>` is the numeric
entity ID used in the Why Analysis demonstration. Also set top-level `current_step` to `"4b"`.

### Step 4c: How Analysis introduction

Demonstrate How Analysis using a concrete multi-record entity (3+ records) identified in step
4a. This teaches the bootcamper how Senzing constructs entities over time as records are added.

1. **Entity selection:** select a multi-record entity with 3+ records from step 4a. State which
   entity and why: "I'll use Entity [ID], which has [N] records, enough construction steps to
   see a meaningful history of how Senzing built this entity over time."
2. **SDK flag and response shape:** generate the `how_entity` call with
   `SZ_INCLUDE_FEATURE_SCORES` **and** `SZ_INCLUDE_MATCH_KEY_DETAILS` **together with a
   relations flag** (confirm via `get_sdk_reference(topic='flags',
   filter='how_entity_by_entity_id')`), and look up the response structure via
   `get_sdk_reference(topic='response_schemas', filter='how_entity_by_entity_id')` before
   parsing it (INV-115). Explain: "I'm using
   SZ_INCLUDE_FEATURE_SCORES so we can see the scoring at each construction step. This shows
   how closely features matched each time a new record was added."

   ⛔ **(INV-115, INV-169) `SZ_INCLUDE_FEATURE_SCORES` alone is the method's DEFAULT and does not
   request the match-key breakdown — pass `SZ_INCLUDE_MATCH_KEY_DETAILS` with a relations flag if you
   intend to show it (INV-115, INV-169).** This step used to name feature scores alone while
   step 4b's `CONFIRMATIONS[]` caution pointed at `how_entity`'s
   `MATCH_KEY_DETAILS.CONFIRMATIONS[]` as the reason the how side is worth reaching for — an
   instruction and a cross-reference that did not meet. **What the server says, three routes,
   all re-verified on server 1.33.0, 2026-08-26:**

   - `get_sdk_reference(topic='response_schemas', filter='how_entity', language='python')`
     documents the path — `HOW_RESULTS.RESOLUTION_STEPS[].MATCH_INFO.MATCH_KEY_DETAILS`, with
     `CONFIRMATIONS[]` carrying `FTYPE_CODE`, `TOKEN`, `SOURCE`, `SCORE`, `SCORE_BUCKET` and
     the `INBOUND_`/`CANDIDATE_FEAT_*` members. The same response's Python signature reads
     `how_entity_by_entity_id(entity_id: int, flags: int = <SzEngineFlags.SZ_INCLUDE_FEATURE_SCORES: 67108864>)`,
     so feature scores alone **is** the default flag set.
   - `get_sdk_reference(topic='flags', filter='SZ_INCLUDE_FEATURE_SCORES', language='python')`
     returns `SZ_HOW_ENTITY_DEFAULT_FLAGS` as that one flag, `response_paths`
     `HOW_RESULTS.RESOLUTION_STEPS[]`; the bare flag's own `response_paths` are
     `RESOLVED_ENTITIES[]` and `SEARCH_STATISTICS[]`. Neither reaches the
     `MATCH_KEY_DETAILS` subtree, so the breakdown is a separate opt-in.
   - `get_sdk_reference(topic='flags', filter='SZ_INCLUDE_MATCH_KEY_DETAILS')` lists
     `how_entity_by_entity_id` in `applies_to` and `depends_on` one of the five relations
     flags — which is why the relations flag travels with it.

   ⚠️ **Those three do not fully agree, and none of them governs the others (INV-169).** The
   flag's `applies_to` names `how_entity_by_entity_id` and the how schema documents the path,
   yet that same flag entry's `response_paths` are `RELATED_ENTITIES[]` and
   `RESOLVED_ENTITY.*`, and its description reads *"each related entity includes a
   MATCH_KEY_DETAILS object"* — a shape `how_entity` does not return at all. **Record all
   three; reconcile none.** This is a gap on the server's side, not something the plugin can
   settle, and it is why the breakdown is **conditional** below rather than promised.

   ⚠️ **Two engine observations, side by side — both observation-only (INV-080/INV-149), and
   neither governs the other (INV-169).** No MCP route reports which flag set populated a
   given engine response.

   | Date | Method | Flags in force (a relations flag travels with the details flag) | Result — **observation-only**, INV-080/INV-149 |
   |---|---|---|---|
   | 2026-08-18 | `how_entity` | **not recorded** | `MATCH_KEY_DETAILS.CONFIRMATIONS[]` populated |
   | 2026-08-24 | `how_entity` | `SZ_INCLUDE_FEATURE_SCORES` alone | `MATCH_KEY_DETAILS` **absent** from `MATCH_INFO` (keys were `CANDIDATE_KEYS`, `ERRULE_CODE`, `FEATURE_SCORES`, `MATCH_KEY`) |
   | 2026-08-24 | `why_records` | `SZ_INCLUDE_MATCH_KEY_DETAILS \| SZ_ENTITY_INCLUDE_ALL_RELATIONS` | `WHY_KEY_DETAILS`, 3 confirmations |

   ⛔ **(INV-169) The 2026-08-18 row's flag set was never written down, so it is not evidence either
   way — and "it used to work without the flag" MUST NOT be written from it.** That would
   repeat exactly the error the why-side correction documents: a conclusion drawn from a
   matrix that never varied the relevant term. The rows are consistent with the flag being
   required on both methods, and that is the strongest statement the data supports. **Do not
   write a version floor or a flag floor.**

   ⚠️ **`SZ_ENTITY_INCLUDE_ALL_RELATIONS` is a composite** — where the binding takes a flag
   *collection* rather than a bitmask it is merged as its members rather than listed among
   them. Step 4b's note on this call's why-side sibling states the rule and
   `../module-07-query-visualize-discover/phase1-query-visualize.md` carries the worked
   example; do not duplicate it here.

   ⛔ **(INV-115, INV-179) The breakdown is CONDITIONAL — dump `MATCH_INFO`'s keys, and if `MATCH_KEY_DETAILS` is
   not among them say so in one line and render `FEATURE_SCORES` instead.** It carries the
   same per-feature evidence — the feature, its score, its bucket — and populated normally on
   both runs above. **Never render an empty section, and never print "no value returned"**:
   the first is indistinguishable from a feature the engine lacks, and the second reads as a
   failure. A stated absence is what turned this into a visible finding rather than a blank.

   ⛔ **(INV-115) The field is `MATCH_KEY_DETAILS` on the how side and `WHY_KEY_DETAILS` on the why
   side. Both spellings are correct on their own method; do not harmonize them.** Reusing one
   parser across both silently yields nothing.

   ⛔ **The two sides of a resolution step are `VIRTUAL_ENTITY_1` and `VIRTUAL_ENTITY_2`** —
   objects, each carrying `.VIRTUAL_ENTITY_ID` and `.MEMBER_RECORDS[].RECORDS[].{DATA_SOURCE,
   RECORD_ID}`. The similarly-named `INBOUND_VIRTUAL_ENTITY_ID` is a **string ID** on the step, not
   the object, and its partner is `RESULT_VIRTUAL_ENTITY_ID`. **There is no
   `CANDIDATE_VIRTUAL_ENTITY` at any depth.** (Verified via
   `get_sdk_reference(topic='response_schemas', filter='how_entity')`, server 1.32.9, 2026-08-17.)

   ⚠️ **Why the wrong pairing is reachable, and why the lookup above does not by itself prevent it.**
   `INBOUND_…`/`CANDIDATE_…` *is* a real pairing in this very response — one level deeper, inside
   `MATCH_INFO.FEATURE_SCORES.<FEATURE>[]`, as `INBOUND_FEAT_DESC` / `CANDIDATE_FEAT_DESC` (it
   recurs in one further `MATCH_INFO` sub-object; see this module's API reference). Generalizing
   that pairing **up** to the step level
   lands on `INBOUND_VIRTUAL_ENTITY_ID`, which exists, so the name is not obviously wrong; its
   invented partner `CANDIDATE_VIRTUAL_ENTITY` simply returns nothing. A parser built that way raises
   no error and renders every step as `? joined ?` while the rule and match key beside them populate
   correctly — the failure is silent and looks like missing data rather than a wrong key.

   ⛔ **So a name-level lookup is not enough here: read the returned paths' TYPES, or dump one raw
   step.** A wholly invented key is caught by the first lookup; a key that appears in the schema at a
   different depth and type survives it. This is INV-115's dump-before-parse rule at the one place
   where skipping the dump is most tempting, because the lookup appears to have confirmed the name.
3. **Chronological narrative presentation:** present the How Analysis output as a chronological
   narrative of the entity's construction history:
   - each step where a new record was added,
   - which features caused the merge at that step,
   - the feature scores at each step.

   Use a narrative format: "Step 1: Record A from [Source] was the first record, it
   established the entity. Step 2: Record B from [Source] was added because [features matched
   with scores]. Step 3: Record C from [Source] was added because [features matched with
   scores]." Walk through each step so the bootcamper can follow the entity's growth from a
   single record to its current multi-record state.

   ⚠️ **Read `HOW_RESULTS.FINAL_STATE` in the same response before narrating (INV-115):** if
   `NEED_REEVALUATION` is non-zero or `VIRTUAL_ENTITIES[]` has more than one element, say so,
   name the sign, and point to Data processing's How-state audit (INV-334)
   (`../module-06-data-processing/phaseD-validation.md` → "How-state audit") rather than
   presenting the history as one settled construction.
4. **Why-vs-How comparison:** explain the difference:
   - **Why Analysis:** compares two specific records or entities and explains the current
     resolution decision, "why are these together right now?"
   - **How Analysis:** shows the full construction history of one entity, the chronological
     sequence of merges as records were added.

   Analogy: "Why is like asking 'why are these two people in the same room?', How is like
   watching the security camera footage of everyone entering the room in order."
5. **Practical use cases:**
   - **Understanding entity growth over time:** "How analysis lets you see the timeline of an
     entity's construction, when each record was added and what triggered each merge."
   - **Investigating over-merging:** "If an entity has too many records merged into it, how
     analysis shows exactly where the chain of merges went wrong, which step introduced the
     problematic record."
   - **Data stewardship:** "When deciding whether to split an entity, how analysis shows the
     merge sequence so you can identify the weakest link in the chain and make an informed split
     decision."
6. **Transition:**

   👉 **What would you like to do next? Reply with a number:**

   1. Continue to the next demonstration — Relationship Networks (exploring how entities connect to each other).
   2. Proceed to module completion.

   *(Internal: end the turn on this question and wait.)* If the bootcamper chooses to exit,
   write `discover_phase: "skipped"` to `config/bootcamp_progress.json` and return to
   `phase1-query-visualize.md` for the Query Completeness Gate.

**Checkpoint:** write step 4c under `module_7_query.steps.4c`, using
`{"status": "completed", "entity_demonstrated": <entity_id>}` where `<entity_id>` is the numeric
entity ID used in the How Analysis demonstration. Also set top-level `current_step` to `"4c"`.

---

**Next:** load `phase2b-discover.md` for step 4d (relationship networks) and Discover Phase
Completion.
