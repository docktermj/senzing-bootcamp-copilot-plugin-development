# Module 1, Phase 1: Discovery (steps 1–6)

Discovery and gap-filling. Follow the ground rules. `🛑`/`⛔` are internal directives: do not
render them; signal a stop by ending the turn on the single 👉 question and waiting.

## 1. Data privacy reminder (statement, no question — NON-YIELDING)

"Before we proceed, a quick reminder about data privacy. We'll be working with potentially
sensitive data. Please ensure you have permission to use it, and consider anonymizing any PII
for testing. We'll set up proper security measures as we go."

⛔ **This step is non-yielding: it does not get a turn of its own.** Present it in the same turn as
Step 2 and let Step 2's 👉 end that turn — a turn ending here would end with **zero** 👉, which
INV-225 forbids, and presenting it alone is not what "advance exactly one step at a time" asks for
(`../bootcamp-onboarding/ground-rules.md` → the 👉 protocol). This is also the step the post-nudge
sequence lands on: on **no** to the model/effort switch, the reply turn carries this reminder and
ends on Step 2's question.

**Checkpoint:** write step 1 — but as one write with Step 2's at the end of the shared turn, not two
writes inside it.

## 2. Offer the design pattern gallery (separate question)

👉 **Would you like to see examples of common business problems that entity resolution can solve?**

**Checkpoint:** write step 2.

## 3. If they want patterns

Present an entity-resolution design-pattern gallery over the recognized use-case categories, giving
for each: the problem it solves, the goal, typical data sources, business value. Fill those four from
**`search_docs` content returned on the turn the gallery is presented** — never from memory, and
never from an earlier turn's results. This is **presentation freshness**
(`../bootcamp-onboarding/ground-rules.md` → "MCP-first invariant"): the gallery carries an MCP
attribution line, and the attribution is only truthful for what a tool produced this turn. "Already
retrieved a few turns ago" does not satisfy it. (The full pattern gallery is a
later porting phase; that is why this step retrieves rather than reads from a shipped catalog.)

⛔ **(INV-212) Query by the document's own title or heading, not by the category label or a generic
phrase.** This is the step's real work, and one generic query is not it: the documentation's own
words are industry terms, so "entity resolution use cases" reaches about four categories and leaves
the rest looking uncovered when they are not. Two
routes carry most of the material. Everything from here to the end of this step **is** the retrieval
strategy INV-212 requires — the vocabulary, the documents that hold the material, the queries that
return confidently wrong content, and what to do with a topic the searches do not reach. Each
measured route names what it returned and at what rank (INV-291):

- **Business value, for nearly every category** — `search_docs(query='Estimated Annual Cost of
  Mismatched Identity Records')` returns the *"Estimated Annual Cost of Mismatched Identity
  Records"* table of `economic-cost-mismatched-identity-data.md` at **rank 1** (MCP server 1.37.16,
  docs index 2026-09-29 22:00 UTC, measured 2026-10-01). The table quantifies ten sectors, and the
  document's appendix breaks several sectors into ER-attributable typologies. **Cite the figures as
  returned by `search_docs`, never from this file** — the numbers live in the document, so a
  revision changes them in one place.

  ⚠️ **A sector-worded query reaches the document but not the table.** On the same measurement,
  `'total economic cost mismatched identity data by sector'` returned the document's intro at
  rank 1 and its *"Remaining Sectors"* section at rank 2, with the table only at rank 3. Use the
  table's own heading.

  ⚠️ **Two of the ten rows are "All Sectors" rows, and one of them is the row most bootcamper
  scenarios actually need.** Lead with **`All Sectors: Cross-Industry Data Quality`** whenever the
  scenario has **no clear industry vertical** — generic duplication across internal systems, which is
  the common case — because it is the table's largest domain and was previously unnamed here, so the
  gallery's most reusable figure went unreached. The other is
  **`All Sectors: Marketing, Sales & CRM`**. The remaining eight rows are Government, Financial
  Services, Supply Chain & Procurement, Insurance, Rest of Economy *(indicative)*, Healthcare,
  Retail & E-Commerce, and Telecommunications. (Non-exhaustive as a guide to *which row to read* —
  the table is the authority on its own contents.)

  ⛔ **Sanctions & trade compliance is NOT a row — do not look for one.** It is a sub-line inside
  **Rest of Economy**, described in the document's *"Remaining Sectors"* section alongside state &
  local government and residual sectors, with full derivations in the appendix. Looking for it among
  the rows sends the guide hunting something that does not exist. (Row list, the two "All Sectors"
  rows and the Remaining-Sectors placement all re-verified live: `search_docs` on MCP server
  **1.32.9**, docs indexed 2026-08-11 20:52 UTC, **2026-08-14**. The document's own totals line reads
  "Expanded Estimate (all 10 sectors)", so "ten sectors" is right.)
- **Problem, goal and typical sources** — the Senzing use-cases page (Customer 360, Fraud
  Detection), the USCIS fraud case study, the MDM integration FAQ (Vendor MDM: free resolution vs
  forced separation via a Trusted ID), and the non-person-entity-types FAQ (asset, claim and
  vehicle linking).

  - **The use-cases page, Customer 360** — `search_docs(query='Senzing use cases Customer 360')`
    returns the *"Customer 360°"* section of *"Senzing Use Cases"*
    (`senzing.com/entity-resolution-use-cases/`) at **rank 1** (MCP server 1.37.16, docs index
    2026-09-29 22:00 UTC, measured 2026-10-01).
  - **The use-cases page, Fraud Detection** — `search_docs(query='Senzing use cases Fraud
    Detection')` returns the *"Fraud Detection"* section of *"Senzing Use Cases"* at **rank 1**
    (MCP server 1.37.16, docs index 2026-09-29 22:00 UTC, measured 2026-10-01).

    ⚠️ **Rank 2 of both is the same page's bare link stub** (`[Read More](/customer-360/)` and
    `[Read More](/risk-fraud-detection)`, under *"Explore More Senzing Use Cases"*). That is a
    miss, not a second source: read the rank-1 section, which states the category's goal in a
    sentence before its link.
  - **The USCIS fraud case study** — `search_docs(query='USCIS Improves Fraud Analytics with
    Senzing Entity Resolution')` returns *"USCIS Improves Fraud Analytics with Senzing Entity
    Resolution"* (the case-study page) at **rank 1** (MCP server 1.37.16, docs index 2026-09-29
    22:00 UTC, measured 2026-10-01), and ranks 2 and 3 are the same page's *"USCIS Selected
    Senzing Entity Resolution for Fraud Detection"* and *"USCIS Project Goals"* sections. The
    case-study PDF is indexed separately under the title *"CASE STUDY"*.
  - **The MDM integration FAQ** — `search_docs(query='How does Senzing integrate with MDM
    (Master Data Management) systems?', category='faq')` returns *"How does Senzing integrate
    with MDM (Master Data Management) systems?"* at **rank 1** (MCP server 1.37.16, docs index
    2026-09-29 22:00 UTC, measured 2026-10-01). It names the two integration styles, free
    resolution and forced separation via a Trusted ID. Without the `category`, the FAQ is still
    rank 1 and the server article *"MDM Integration Patterns with Senzing"* is rank 2.
  - **The non-person-entity-types FAQ** — `search_docs(query='Adding Non-Person Entity Types to
    Senzing', category='faq')` returns *"Adding Non-Person Entity Types to Senzing"*
    (`non-person-entity-types-faq.md`) at **rank 1** (MCP server 1.37.16, docs index 2026-09-29
    22:00 UTC, measured 2026-10-01).

    ⚠️ **Rank 2 is a different document, and looser queries put it first:** the FAQ *"Can I use
    Senzing for product matching, vehicle matching, or other non-person entities?"*. Its caution,
    that this needs work with Senzing R&D, concerns **matching** non-person entities to each other.
    This pattern is about **linking** people and organizations to assets, claims and vehicles,
    which is what the non-person-entity-types FAQ describes. Do not let that caution drop the
    pattern.

⛔ **Two category names are homonym traps that return confidently WRONG content, not nothing** —
which is worse, because a wrong-looking result invites a re-query and a plausible one does not:

- **Supply Chain** — BM25 matches "chains" and the software sense; see the measured example at
  `phase2-document-confirm.md` → Step 14. Query the sector line instead.
- **Data Migration** — returns the **V3→V4 SDK migration** (`sz_dbupgrade`, `sz_configupgrade`,
  the Java/Python migration guides), which has nothing to do with a business use case. This is the
  one recognized category with no business-use-case material; treat it as unreached below rather
  than presenting SDK-upgrade steps as a pattern.

**When a query misses, re-query with the documentation's own vocabulary before concluding the
material is uncovered.** The rule and the reason it matters are stated in full at
[`../module-00-entity-resolution-concepts/concepts.md`](../module-00-entity-resolution-concepts/concepts.md)
→ "Hard rule: facts come from MCP, not memory". Do not restate that reasoning here — follow it (INV-300).

⛔ **A bare link stub is not content.** The use-cases page returns several categories as nothing but
`[Read More](/risk-fraud-detection)`. A stub is the shape most likely to be mistaken for coverage;
it supplies none of the four attributes.

⛔ **Never fill a category's detail from training data (INV-080).** For any category the searches do
not reach, name it as available and say you can look it up on request — do not invent its problem,
goal, sources or value. The gallery presents the categories the searches actually reached; it does
not promise all ten, and a short sourced gallery plus an honest offer is the correct outcome, not a
failure of this step. Fabricated detail here is especially costly because the attribution line below
then presents it as Senzing-sourced.

Because this content is MCP-sourced, make that visible so the bootcamper can trust it is real,
not fabricated: add a brief inline attribution to the gallery — e.g. a one-line "*Sourced from
Senzing docs via the MCP server.*" note (or a per-item "(via Senzing docs)") — per the
visible-attribution convention in `../bootcamp-onboarding/ground-rules.md`. Keep it lightweight,
honor verbosity (suppress it at the `minimal` preset), and attribute to the MCP server only what
an MCP tool actually produced.

👉 **Do any of these patterns match your situation?**

If they pick one, use it as a template — and ⛔ **pre-fill it from the `search_docs` response that
supplied that gallery entry, never from what you know about the pattern (INV-080/INV-212).** The
source types come from that entry's **typical sources** attribute, which the gallery already
retrieved (see "Problem, goal and typical sources" above); the matching criteria come from the same
entry's problem and goal wording. If the entry you presented did not carry typical sources — a
`[Read More]` stub supplies none of the four attributes — **re-query with the documentation's own
vocabulary before pre-filling anything**, and if it is still unreached, say so and ask the
bootcamper for their sources rather than proposing a plausible list.

⚠️ **This is the step where invention is least visible.** A pattern's typical sources are exactly
the kind of detail that reads right when invented — "CRM, billing, support tickets" is plausible for
almost any pattern — and Step 3 has already told the bootcamper the gallery is Senzing-sourced, so a
guessed pre-fill inherits that attribution.

If none fit, they can accept the Business Case Offer in Step 4.

**Checkpoint:** write step 3.

## 4. Discovery prompt: three selectable paths

First state a one-line recommendation (a statement, not part of the lead question; honor
verbosity — suppress it at the `minimal` preset), then present the neutral lead question and the
numbered choices, ending the turn on the 👉:

For the most relevant bootcamp, I recommend describing your own business problem if you have one —
you'll work through *your* real data. If you don't, I can generate a realistic scenario instead.

👉 **How would you like to define the business problem? Reply with a number:**

1. **Describe a real business case** — tell me about the problem you're solving: what data you
   have, where it comes from, and what success looks like.
2. **Adopt a design pattern** (if you picked one in Step 3) — how does it apply: what data, from
   where, and what does success look like?
3. **I don't have my own data — generate a scenario for me** — I'll create a realistic,
   multi-source scenario so you can complete the full bootcamp (the Business Case Offer).

*(Internal: end the turn on this 👉 choice and wait. Do NOT generate a scenario before the
bootcamper explicitly accepts option 3.)*

**Checkpoint:** write step 4.

### 4a. Business Case Offer: acceptance handling (branch)

- **Accepted:** generate a complete scenario in-session: a non-empty problem description,
  exactly one use-case category from the recognized set (Customer 360, Fraud Detection, Data
  Migration, Compliance, Marketing, Healthcare, Supply Chain, KYC, Insurance, Vendor MDM), and
  a non-empty definition of success. If a pattern was picked in Step 3, the category must match
  it. Decide CORD vs. synthetic data per Step 4b. **Validate invariants** before recording: at
  least two distinctly named data sources, each with ≥1 record; the data carries **cross-source
  mapping divergence** — at least two sources describing the same feature in **different shapes**
  (one a single name field, another parsed components; one a free-text address, another parts), so
  the mapping module has real per-source work to do. ⛔ **Do not state this as "at least one
  transformation".** That wording produced a reversal: a joined name is a **direct** mapping to
  `NAME_FULL` under the Entity Specification, not a field awaiting a split, so a scenario built to
  satisfy "a transformation" on the strength of a joined name satisfies nothing and encodes a plan
  the specification does not call for. If a genuine value-level transformation is wanted, name a
  kind the specification actually asks for — date normalization, code or value standardization,
  composing a `RECORD_ID` — rather than leaving it unqualified. ⚠️ **Do not record what any field
  maps to here either:** the specification is not read until Data Quality, Mapping, and
  Transformation. The scenario is **quality-varied** — it promises missing and off-pattern values,
  spanning bands rather than being uniformly clean, which is what Data collection then generates and
  what makes the quality gate reachable (INV-239); category is in the recognized set; problem and
  success are non-empty. On
  success, record artifacts in Phase 2 Step 11 (write `docs/business_problem.md` with the
  generated marker, and each source into `config/data_sources.yaml`), then continue at Step 5.
- ⛔ **(INV-277) Size the generated scenario to about 10,000 records unless the Bootcamper asks for
  more,
  and if they do, say what it costs BEFORE generating it.** The step above validates the
  scenario's *shape* — category, sources, mapping divergence, quality variation — and nothing
  validates its *size*, so an unbounded scenario is the default rather than a choice. The cost is
  not paid here: it is paid in **Data collection**, **Data processing** and
  **Query, Visualize and Discover**, where the data is collected, loaded, redo-drained and
  queried, by which point the decision is many steps behind and expensive to reverse.
  - **When they ask for more, state it in one line and then generate what they asked for** — e.g.
    *"That will make Data collection and Data processing take noticeably longer."* ⛔ **This is a
    statement, not a 👉 question** (INV-251), and it is **not** a re-ask of a settled choice
    (INV-006). Their answer stands; they are owed the trade-off, not a gate.
  - ⛔ **Do not state a wall-clock figure or a records-per-second rate.** Load time depends on the
    workstation, the database and the chosen language, none of which this module knows, and a
    number invented here is one the run will contradict. Name the modules that absorb the cost
    instead.
  - ⛔ **Do not tie the ceiling to the license limit at this step.** Nothing has measured the
    license yet and INV-093 forbids a license prompt here, so the ceiling is about how long the
    bootcamp takes — which is knowable now — never about capacity, which is not.
- **Declined:** continue with their own description (Path 1/2); do not generate a scenario.
- **Generation failed / invariants violated:** tell the bootcamper it couldn't complete, fall
  back to their own description, no generated `docs/business_problem.md`.

*(The Kiro helper `business_case_offer.py` encodes these invariants; the script port is a later
phase: validate them directly for now.)*

**Checkpoint:** write step 4a.

### 4b. CORD sourcing for the generated scenario (via MCP)

Treat the Senzing MCP server as the ONLY source of CORD facts: never training data. Call
`get_sample_data` and/or `search_docs(query='CORD datasets: names, contents, and availability
for entity resolution scenarios')` (its top hit is *Collections Of Relatable Data (CORDs)* →
"What Is a CORD?") to learn which datasets exist and what they contain. Present
values exactly as returned. Wait up to 30s; retry once.

⛔ **`truthset` is NOT eligible to back a generated scenario, for two independent reasons.**
It is the most inviting choice — smallest, already used elsewhere in the bootcamp, and its
description says it is for quickstarts — so rule it out explicitly rather than leaving it to
judgment:

1. **It is pre-mapped**, so it can never satisfy Step 4a's mapping-complexity invariant. The
   disqualifying word is the server's own: `get_capabilities` describes it as *"the Senzing demo
   truth set: CUSTOMERS, REFERENCE, WATCHLIST — small, **pre-mapped**, used in quickstarts"*
   (server 1.32.9, re-verified 2026-08-14). A scenario built on it passes every other check in
   this step and leaves Data Quality, Mapping, and Transformation with nothing to transform.
2. **Truth Set visualization already runs on it**, so a scenario backed by it collapses two
   modules onto one dataset.

**The eligible collections and what they are shaped like** — take the dataset names, source lists
and counts from `get_sample_data` at runtime, never from here (INV-080); this is a note about
*domain fit*, which the response does not judge for you (all four confirmed present on server
1.32.9, 2026-08-14):

| Dataset | Shaped like | Fit |
|---|---|---|
| `las-vegas` | risk, ownership and licensing data (the widest source set) | eligible |
| `london` | sanctions and corporate-registry data | eligible |
| `moscow` | sanctions and ownership data, non-Roman script | eligible |
| `truthset` | the pre-mapped demo truth set | **ineligible — see above** |

⚠️ **For the customer-facing categories, `synthesized` is the EXPECTED outcome, not a failure.**
The recognized set in Step 4a includes Customer 360, Marketing and Vendor MDM, and all three
eligible collections are risk / sanctions / ownership data — so for those categories no CORD
dataset fits, and synthesizing is the correct answer rather than giving up. Customer 360 is the
most likely pick of all, being the pattern gallery's most relatable entry. Say so to the
bootcamper in those terms; do not present it as a fallback, and do not stretch a sanctions
collection to cover a customer-360 problem in order to reach the `cord` branch.

- **Fitting CORD dataset returned** (one of the three eligible collections, matching the
  category's domain): back the scenario with it, provenance `cord`.
  - ⛔ **(INV-293) Say plainly that CORD is real data, here, in the turn that binds it.** This is the first
    moment the Bootcamper's scenario becomes real-people data, and Module 4's wording is several
    modules away. `get_sample_data`'s contract requires its caller to disclose it — real records,
    historical snapshots, evaluation rather than operational use — and the canonical sentences are
    in `../module-04-data-collection/SKILL.md` (Step 2's CORD block). A statement, never a 👉 — the bootcamp
    specifies no gate here (INV-247), and it would ask nothing they can act on (INV-012).
- **None fit** — including every case where the only apparent fit was `truthset`: synthetic data,
  provenance `synthesized`. Data collection generates the files for this provenance without asking
  again (`../module-04-data-collection/SKILL.md` → Step 2), so this branch is complete, not
  deferred.
- **Timeout/unreachable after one retry:** omit CORD facts, tell the bootcamper they're
  unavailable, use synthetic data (`synthesized`).

Either way the data must satisfy the Step 4a invariants.

**Checkpoint:** write step 4b.

## 5. Infer details from their response

Extract six categories: **A. Record types** (people/orgs/both); **B. Source count and names**;
**C. Problem category** (map to the recognized set); **D. Matching criteria** (attributes,
quality concerns); **E. Desired outcome** (format, frequency, integration); **F. Integration
targets** (specific software, pipeline mentions). Use "not yet determined" when unclear.

**Checkpoint:** write step 5.

### 5a. Record-count threshold check (compute-only — no license prompt here)

Compute the total record count across the mentioned sources and read `license_record_limit` from
`config/bootcamp_progress.json` (normally absent at this point):

⛔ **(INV-244, INV-278) `license_record_limit` is written ONLY from a measured license — never from a
Bootcamper statement.** Every step that writes it parses the record limit out of
`getLicense`/`get_license` against the installed SDK — SDK setup's Step 5a measures it as soon as
Step 4 has verified the SDK, and Module 4's Step 8a measures it again at the License-Key gate. A number the Bootcamper *tells* you — "our
POC license allows 100,000" — is a claim about a license that may never have been applied to this
install, and it does not go in this field, this session or any other. ⚠️ **The failure is a
suppressed warning, not a wrong number:** a `license_record_limit` above the dataset size
**suppresses** Module 4's Step 8a gate, the single volume-gated prompt in the whole bootcamp. On
2026-08-25 a stated 100,000 was written here against an install whose measured limit was **500**, on
a ~94,000-record scenario; the gate that exists to warn before hitting the cap mid-load would never
have fired. This is INV-244's rule reached from the other side — that invariant forbids reading
*absence* as "no license"; this forbids treating a *present but unmeasured* value as a measurement.

⛔ **(INV-278) Record a stated entitlement as `license_stated_limit` in
`config/bootcamp_preferences.yaml`, and say plainly that no gate reads it.** It is the Bootcamper's claim, worth keeping — it is why they
sized the scenario the way they did, and Module 4 can reconcile it against the measurement later —
but it is a *statement*, and it lives with the other stated preferences, in a different file from the
measured field so the two cannot be confused by proximity.

- **Present and > 0:** if the total exceeds it, the bootcamper will likely need a Senzing License
  Key — record `license_guidance_deferred: true` in `config/bootcamp_preferences.yaml`. Otherwise
  leave it unset. Either way, proceed to Step 6.
- **Present and = 0** (no cap): no license concern → proceed to Step 6.
- **Absent/null:** compare the total against the built-in evaluation capacity. ⛔ **Get that figure
  from the one route that carries it — do not ask "the MCP server" generally, and never use a
  remembered number.** It is in the `compatibility_notes` and `engine_config_notes` of
  `sdk_guide(topic='load', language='<chosen_language>', platform='<detected_platform>',
  record_count=<a value above the limit>)`; a `record_count` under the limit does not surface it.
  Re-ask it here rather than copying a figure from this file (INV-080). If the total exceeds the
  capacity, record `license_guidance_deferred: true`; otherwise leave it unset. Either way,
  proceed to Step 6.

  ⛔ **Two different Senzing licenses have two different capacities, and confusing them is the
  recorded failure.** The **built-in** one — active by default, no request needed — is the small
  figure this comparison needs. The **requestable** evaluation license, obtained via
  `submit_feedback(category='license_request')`, is far larger and is described in that tool's own
  description, which you may well have read earlier in the session for another reason. On
  2026-08-18 the larger figure was attributed to the built-in license here, the comparison passed
  when it should have failed, `license_guidance_deferred` was left unset, and Module 4's gate — the
  one thing that would have warned the Bootcamper before they hit the cap mid-load — never fired.
  ⛔ **Ask the route above; do not reason from the other license's number.**

  ⚠️ **This branch assumes the built-in capacity because nothing has measured the installed
  license yet, and that is deliberate rather than the INV-244 error.** ⛔ **Every step that writes
  `license_record_limit` writes only a MEASURED value** — none writes it from an assumption, a
  default, or a Bootcamper statement. So a value present here is always a measurement, and its
  absence still means *not yet measured* — not *no custom license*. ⚠️ **Do not reason from how many
  steps write it**; that number has been stated wrongly twice and is not what the conclusion rests
  on. The distinction that does matter here is ORDER, not the writer set: the first step that
  measures the license is SDK setup's Step 5a, and SDK setup has not run yet at this point in the
  bootcamp — so nothing can have put a figure in this field, and its absence here carries no
  information about the installed license. INV-093 forbids a license prompt at this
  point, and this step only sets a deferral flag for a later gate to resolve, so assuming the
  built-in figure is the correct conservative reading. Say so if it matters to the Bootcamper;
  never present it as a detected value.

⛔ **What this comparison decides.** Leaving `license_guidance_deferred` unset **suppresses**
Module 4's Step 8a License Key gate — the single volume-gated prompt in the whole bootcamp. Getting
this comparison wrong therefore removes the warning rather than producing a wrong one, which is why
the figure has to come from the route above and not from recall.

**The bootcamp does not ask about a Senzing License Key here.** The single, volume-gated License
Key prompt is presented once — at the start of Data collection (Module 4), after the actual data
volume is known and before any load — per INV-093. This step only records whether the anticipated
volume looks likely to exceed the limit, so Module 4's gate can pick it up (`license_guidance_deferred`).

**Checkpoint:** write step 5a to `config/bootcamp_progress.json`.

## 6. Confirm inferred details and fill gaps

Ask about only ONE undetermined item per turn; queue the rest for later turns. Don't re-ask
what they already covered.

### 6a. Present summary and confirm

"Based on what you've described: **Problem:** [...]; **Record types:** [...]; **Data sources:**
[...]; **Key attributes:** [...]; **Desired outcome:** [...]."

👉 **Does that summary capture your situation accurately?**

*(Internal: end the turn and wait.)* **Checkpoint:** write step 6a.

### 6b–6d. Ask only about "not yet determined" items, one per turn

- **6b (record types).** Options beneath the 👉, never on its line (`../bootcamp-onboarding/ground-rules.md`):

  > 👉 **Which records are you working with? Reply with a number:**
  >
  > 1. **People**
  > 2. **Organizations**
  > 3. **Both**

- **6c (source count).** 👉 **How many distinct data sources will we work with?**

- **6d (desired outcome).** ⛔ **(INV-286) This one is MULTI-select, and asking it as single-select loses a
  real answer.** A clean master list, an API over it and reports off it are **complements, not
  alternatives** — they are the three normal deliverables of the same project, and most
  organizations want more than one. Asked as a single-select on 2026-08-31, a Bootcamper answered
  *"1 and 3"*: cooperative, coherent, and unrecordable. Same wording shape as Bootcamp preparation's
  optional-module gate, so the plugin has one multi-select idiom rather than two:

  > 👉 **What does the end result look like? Reply with the numbers from the list below, comma-separated:**
  >
  > 1. **A clean master list**
  > 2. **An API**
  > 3. **Reports**
  > 4. **Something else**

  ⛔ **(INV-286) Record every option they choose, not the first.** The answer travels: Step 11's **Desired
  Output** section carries it into `docs/business_problem.md`, and Module 7 step 1 derives query
  requirements from that document — so narrowing "1 and 3" to "a clean master list" writes a
  requirement they did not give and steers a module they have not reached.

  ⚠️ **Leave 6b single-select.** Its **Both** option already covers its combinations, and record
  types are a closed three-way set rather than an open list.

*(Internal: end each turn on its question and wait; checkpoint after each.)* When no
undetermined items remain, Phase 1 is complete — proceed to Phase 2 (load
`phase2-document-confirm.md`).

(The software-integration and deployment-target questions are asked in **Phase 2, Step 10a** — after
the scenario is identified and before the problem statement is written (INV-097) — not here in
Phase 1 and not in Bootcamp preparation. Their answers are persisted to
`config/bootcamp_preferences.yaml` (`integration_targets`, `deployment_target`/`cloud_provider`)
and read from there by the problem statement (Phase 2) and by graduation.)
