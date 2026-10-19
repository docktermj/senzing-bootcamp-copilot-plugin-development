# Entity Resolution Concepts (Module 0 content)

Used by Module 0 (the optional entity-resolution concepts primer). Teach the core concept before
Module 1. This module runs only when "Entity Resolution Concepts" was selected during Bootcamp
preparation (its old skip/keep gate has been retired — see `SKILL.md`).

## Banner (show first)

Present this banner verbatim as the FIRST bootcamper-facing content of the primer, before the
description:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧭🧭🧭  ENTITY RESOLUTION CONCEPTS  🧭🧭🧭
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Hard rule: facts come from MCP, not memory

Before presenting, call the Senzing MCP `search_docs` tool for the Senzing-specific material.
Suggested queries:

- "What is entity resolution false negative false positive true match"
- "Senzing principle-based entity resolution approach"
- "entity resolution relationships disclosed discovered"
- "ambiguous matches invisible false positives"
- "Senzing differentiators real-time explainability attribution"
- "How does entity resolution work steps process"
- "entity resolution false positives false negatives accuracy"
- "difference between entity resolution and master data management"

⚠️ **Every entry here was MEASURED, one at a time, not composed.** Each was run against the live
index and kept only because it returns the material it is for. **Current measurement: MCP server
1.37.18, docs index 2026-10-02 11:23 UTC, measured 2026-10-02**, with every entry re-run on that
date. What each one returned:

| Query | Returns | Rank |
| --- | --- | --- |
| "What is entity resolution false negative false positive true match" | *"What Is Entity Resolution?"* (defines false negative and false positive) | 1 |
| "Senzing principle-based entity resolution approach" | *"Benefits of the Senzing Principle Based Approach"* | 1 |
| "entity resolution relationships disclosed discovered" | *"How Does Relationship Awareness Improve Entity Resolution?"* | 1 |
| "ambiguous matches invisible false positives" | *"What Are Ambiguous Matches and Invisible False Positives?"* | 1 |
| "Senzing differentiators real-time explainability attribution" | *"Senzing Explainability Functionality"* (why, why not, how) | 2 (read down the list: rank 1 is the same page's list of resource links) |
| "How does entity resolution work steps process" | *"How Does Entity Resolution Work?"* (the numbered pipeline) | 1 |
| "entity resolution false positives false negatives accuracy" | *"What Are Ambiguous Matches and Invisible False Positives?"* | 2 (read down the list: rank 1 is a Verisk case study) |
| "difference between entity resolution and master data management" | *"What Is the Difference Between Entity Resolution and Master Data Management (MDM)?"* | 1 |

`search_docs` is BM25, so a plausible-sounding phrase is not evidence of anything. **History: two
entries were wrong when they were checked** on MCP server 1.35.3, docs index 2026-09-01 11:58 UTC,
2026-09-01:

- *"entity resolution ambiguous match possible match"* returned **three Entity-Centric-Learning
  chunks and no ambiguous-match material at all** — the composed phrase loses to chunks with a
  denser concentration of `entity`/`resolution`/`match`. It was replaced with wording from the
  documentation's own section heading, which on that date returned *"What Are Ambiguous Matches and
  Invisible False Positives?"* at **rank 1** (94.7), with two further ambiguous-match sections
  behind it.
- *"entity resolution pipeline standardization blocking scoring clustering"* named five real
  pipeline stages and reached **none of them** — rank 1 was a customer case study, rank 2 the MCP
  server's own page. It was replaced; on that date the new query returned the *"How Does Entity
  Resolution Work?"* section at **rank 1** (108.7), which is the numbered pipeline itself.

⛔ **(INV-291) Both were found by running them, and neither was findable by reading them** — they are
well-formed, on-topic and use the right technical vocabulary. So if you change an entry here, **run
it first**, and if the index date above has moved, re-run every entry rather than trusting this
note. The false-positives entry is the standing example of a *good* result that still needs
reading: its rank 1 is a case study and the material it is for is at rank 2.

⛔ **Prefer these queries, and when a query returns nothing relevant, RE-QUERY with the
documentation's own phrasing before concluding the material is not covered.** (INV-212 — the
retrieval strategy belongs at the step, not just the tool's name; INV-194 — one tool's silence is
not evidence the server lacks the fact.) The list above is not
decoration: `search_docs` is BM25, so phrasing decides what comes back, and these are phrased the
way the indexed documentation is. A query you compose yourself can miss completely — one invented as
*"principles versus rules brittle maintenance ingest new data sources without experts"* latched onto
"data sources" and "ingest" and returned record-loading snippets and `add_record` flags, while the
suggested *"Senzing principle-based entity resolution approach"* returned the material immediately,
from two independent sources.

The hazard is the failure's **shape**, not the wasted call: **a query that misses looks exactly like
documentation that does not cover the topic.** The honest-seeming conclusion — "the docs are silent"
— leaves nothing to say under the MCP-only rule, or worse, makes a training-data fallback feel
justified on the grounds that MCP "had no answer". So treat an empty or off-topic result as a
**query** problem first: re-query using the documentation's own vocabulary, and only after that
report the material as uncovered.

Do NOT present hardcoded Senzing facts from training data. Every Senzing-specific claim must
come from `search_docs`. If asked for a source, cite "Senzing documentation via MCP".

**Verify substantive answers before presenting.** For any substantive entity-resolution claim you
give the bootcamper — especially answering a follow-up question or a knowledge-check question —
do not present the first `search_docs` result as-is: make a **second, confirming MCP call**
(a differently-phrased `search_docs`, or another MCP tool such as `get_sdk_reference`) to
cross-check the claim, and present it only once corroborated. If the two calls disagree or the
claim cannot be corroborated, say so and present only what the MCP server supports. This stays
MCP-only — never fall back to training data. Scope this to substantive claims, not conversational
replies.

## What to teach (not Senzing-proprietary, plain language — still MCP-sourced)

⛔ **"Not Senzing-proprietary" describes where the IDEA comes from. It is never an exemption from
the pre-response checklist (INV-080).** Everything below is an entity-resolution technical detail,
so `ground-rules.md`'s MCP-first rule applies to it exactly as it applies to the Senzing-specific
subsection beneath: a reply covering blocking, scoring, classification or clustering requires an
MCP call **on that turn**. The two labels sit on different axes — *attribution* (is this
proprietary to Senzing?) versus *sourcing* (is this a claim about how entity resolution works?) —
and only the second decides whether a call is needed. The heading used to read "generic concept",
which licensed this material as prose while the checklist required it be sourced; a guide taking
that at face value presents the pipeline from training data, and it will usually be roughly
right, which is exactly why nobody notices when it is not.

**Nothing is lost by requiring the call:** the material is fully retrievable, and the queries that
reach it are in the suggested list above — the requirement travels with its route, per INV-212
(measured on MCP server 1.37.18, docs index 2026-10-02 11:23 UTC, 2026-10-02). The route to *what
entity resolution is* is *"What is entity resolution false negative false positive true match"*,
which returns the *"What Is Entity Resolution?"* section of *"What Is Entity Resolution? How It
Works & Why It Matters."* at **rank 1**. The pipeline query returns the same document's *"How Does
Entity Resolution Work?"* at rank 1. One caveat on reading those results: for the false-positives
query the on-topic section is **not** the top hit — a Verisk case study outranks it — so read down
the list for *"What Are Ambiguous Matches and Invisible False Positives?"* rather than presenting
the first row.

- **What entity resolution is:** deciding whether different records refer to the *same
  real-world entity* (a person, organization, product, vessel or another entity type), then
  matching, relating, and deduplicating them.
- **Two failure modes:** false negatives (same entity split apart) and false positives
  (different entities merged). The documentation carries a sharper framing of the second worth
  using — an **ambiguous match** (a record that could legitimately belong to more than one
  entity) which most systems assign arbitrarily, producing an **invisible false positive** that
  "looks correct on inspection" and is undetectable until more information arrives; the
  well-designed behavior is to hold it as a *possible match* until a distinguishing attribute
  breaks the tie. Reached by the false-positives query above (`search_docs` →
  *"What Are Ambiguous Matches and Invisible False Positives?"*).
- **The conceptual pipeline:** ingestion/standardization -> candidate selection (blocking) ->
  comparison/scoring -> classification (match / no-match / possible-match) -> entity clustering.
- **Disclosed vs. discovered relationships.**
- **What it produces:** matched records grouped into unified entities, and relationships tracked
  between those entities. Reached by the pipeline query above (*"How Does Entity Resolution
  Work?"*, rank 1: its clustering step and the paragraph after the numbered list). Do **not** call
  a resolved entity a *golden record*: the documentation uses that term for a master data
  management function (deciding which attribute values survive when records merge), which it
  places beyond entity resolution. Reached by the MDM query above (*"What Is the Difference Between
  Entity Resolution and Master Data Management (MDM)?"*, rank 1); read down that list to rank 3,
  the FAQ answer to the same question, for ER as the deduplicated foundation an MDM program builds
  on. Rank 2 is a different FAQ, *"How does Senzing integrate with MDM (Master Data Management)
  systems?"*, so don't stop there.

### How Senzing handles it (pull specifics from MCP)

Cover, using `search_docs` results: principle-based matching (frequency, exclusivity,
stability); pre-configured for people and organizations; differentiators (real-time, no model
training required, explainability, scalability).

⛔ **Use `"Senzing principle-based entity resolution approach"` for this, and do NOT compose a query
from the words "frequency exclusivity stability" (INV-212 — the retrieval strategy belongs at the
step, and a step that names an outcome without a route leaves the guide to invent one).** The suggested query returns *"What is Principle
Based Entity Resolution?"* → *"Benefits of the Senzing Principle Based Approach"*, which is primer
altitude and carries the idea plainly — principles are "based on the expected behaviors of entity
attributes", with the worked contrast that SSNs "typically point to only one person" while dates of
birth "are shared by many people".

⚠️ **The obvious self-composed query lands at the wrong altitude.**
`search_docs('Senzing principles frequency exclusivity stability attribute behavior')` returns the
**A1ES behavior-code** material as its top hits (verified server 1.33.0, docs index 2026-08-20
17:33 UTC, 2026-08-23): an FAQ on composite behavior codes, then ~8 KB of `addFeature`,
`sz_configtool`, `FTYPE_FREQ`/`FTYPE_EXCL`/`FTYPE_STAB` and stewardship guidance aimed at someone
customizing an engine configuration. It is not wrong — it does name all three dimensions — but it is
**configuration guidance, not primer material**, and presenting it here buries a simple idea under
`MDM_ID` and `A1ES`. This is the self-composed-query hazard the hard rule above describes, with a
measured instance: use the three words to *explain* the concept, never as the query.

## Invite questions/discussion (before the knowledge check)

After the primer above and **before** the optional knowledge-check offer below, give the
bootcamper space to clarify or discuss the concepts first. Briefly invite them to ask anything
about entity resolution — offer a couple of example prompts to lower the barrier:

- "How does Senzing match records without rules?"
- "What's the difference between matching and relating?"

Then end the turn on this single, pinned 👉 question, asked **verbatim** (INV-056):

> 👉 **Do you have any questions about entity resolution before we continue?**

It is a single yes/no with exactly one meaning each (INV-008), no "or"-joined choices (INV-051,
INV-009): "yes" means "I have something to ask or discuss", "no" means "nothing right now, continue".
**Presenting it is MANDATORY (INV-005/INV-056/INV-112)**; what "never blocks" means is that the
bootcamper's *answer* never holds up progress — not that the question may be skipped.

- On **yes**, or an actual question: answer it via `search_docs`, **verified with a second confirming
  MCP call** (see "Verify substantive answers" above), present it, then invite more using the
  **follow-up** variant below — not the first-ask wording. Stay MCP-only — never fall back to
  training data.

  > 👉 **Do you have any other questions about entity resolution before we continue?**

  ⛔ **Use the follow-up wording every time after the first answer, and keep using it for each
  further question.** It is pinned verbatim for the same reason the first-ask is (INV-056), and the
  only difference is the word **other**. Re-issuing the *first-ask* string immediately after
  answering someone reads as though their question did not register — and paraphrasing on the fly is
  not the alternative, because INV-056 fixes both wordings. This mirrors how the preface handles the
  same moment (`../bootcamp-onboarding/onboarding-flow.md` step 4: *"ask once more whether they have
  other questions"*); Module 0 now says it with a pinned string instead of leaving it to improvisation.
- On **no** ("no", "not now", "let's continue"): acknowledge briefly and proceed to the optional
  knowledge-check offer below.

This invitation is issued **once**, here (INV-006). The later exploration/readiness gate remains the
place to keep exploring before moving on, so do not re-issue this same "any questions?" invitation
there.

## Optional knowledge check (offer before the readiness gate)

After the primer and before the mandatory exploration gate below, offer an optional short
knowledge check. It reinforces the concepts and drives curiosity.

⛔ **Presenting this question is MANDATORY (INV-005/INV-056/INV-112) — ask it, verbatim, every time
this module runs.** Taking the knowledge check is what is optional. "Optional" and "never blocks"
describe the bootcamper's **answer**, not whether you ask: declining is free and costs them nothing,
but skipping the question is a violation, not a shortcut. Do **not** collapse it into the mandatory
readiness gate that follows — they are two separate questions on two separate turns.

Give a one-line encouragement ("It may help you understand entity resolution better — worth a
try!"), then end the turn on this single, pinned 👉 question, asked **verbatim** (INV-056):

> 👉 **Would you like a few quick questions to help the concepts stick?**

It is a single yes/no with exactly one meaning each (INV-008), no "or"-joined choices (INV-051,
INV-009).

⛔ **Offer the benefit, never the assessment.** The words "quiz", "test" and "evaluation" make
people recoil from an exercise they would otherwise take, and this question reaches **every**
bootcamper who runs this module (INV-112) — so a small deterrent applies universally. The sentence
above names what they get (the concepts sticking), not what is being measured, which is what the
module already says the exercise is *for* two paragraphs up. ⛔ Do not soften it further into
ambiguity: "Would you like to explore the concepts further?" is friendly and unanswerable, and INV-008
requires the bootcamper to know exactly what they are agreeing to. ⛔ Do not adapt the wording to how
the bootcamper seems to be doing — INV-112 pins one sentence for every run.

On **decline** ("no", "skip", "not now"): acknowledge briefly and proceed to the mandatory
exploration gate below.

On **accept** ("yes", "sure", "let's try"), run the knowledge check under these rules:

- Ask a **short** series (about 3-5) of entity-resolution questions, **one 👉 question per turn**
  (INV-251), evaluating the bootcamper's answer each turn before asking the next.
- **Start at moderate difficulty** — not the easiest tier — and keep it conceptual (matching vs.
  relating, false positives/negatives, why principle-based beats hand-written rules, disclosed vs.
  discovered relationships), not trivia.
- **Source and verify every question and its correct answer via the MCP server**, exactly as the
  "facts come from MCP" and "verify substantive answers" rules above require — never draw a
  question from facts in training data.
- **The bootcamper can exit at any time** — "stop", "exit", "done", "skip the rest", or a
  readiness signal ends the knowledge check immediately, no penalty; acknowledge and proceed to
  the gate.
- **Ask every item as a numbered multiple-choice question.** An item is a 👉 question offering
  two or more choices, so INV-051 applies: a neutral lead question followed by a **numbered list**,
  choices never joined with "or". Do **not** pose open-ended items ("explain why principle-based
  matching beats hand-written rules") — however good the question, it fits neither INV-051's
  numbered shape nor INV-008's single-meaning-answer requirement, and it makes "was that correct?"
  a judgment call instead of a fact. Keep the *thinking* conceptual and the *answer format*
  closed.
- ⛔ **When the answer is wrong, say so — and re-teach.** This is the highest-value moment in the
  knowledge check, and it is the one a guide optimizing for encouragement gets wrong. Do all three:
  1. **Name it as incorrect, plainly and kindly.** Never "good thinking!" over a wrong answer, and
     never let the correction be so soft the bootcamper cannot tell they missed it. False praise
     here teaches the wrong concept.
  2. **Explain why the chosen option is wrong, then re-teach the concept** — not just "the answer
     was 2." Say what the option they picked actually describes, since a plausible distractor is
     usually a *neighboring* real concept, and that confusion is the thing worth fixing.
  3. **Move on to the next item; do not re-ask the same one.** The point is understanding, not a
     score, and re-asking after supplying the answer tests nothing. Keep the remaining items at
     the same difficulty — a miss is not a reason to get easier, and this is a learning module,
     not an assessment.

  Ground the re-teaching in the same MCP source the question came from; never patch a wrong answer
  from training data (INV-080).
- When the series finishes (or the bootcamper exits), give a one-line encouraging wrap-up and
  proceed to the mandatory exploration gate below. The wrap-up never reports a score or a pass/fail
  — nothing in this module is graded.

The knowledge check never replaces the mandatory exploration/readiness gate; that gate is always
presented after it (or after a decline).

## Mandatory exploration gate (internal)

The bootcamper was already invited to ask questions before the knowledge check, so do **not**
re-issue that same "any questions?" invitation with a fresh list of example prompts here
(INV-006). In one line,
simply remind them they can still ask anything about entity resolution and should say so when
they're ready to move on.

Then end the turn on this single 👉 question, asked **verbatim**, and wait:

> 👉 **Are you ready to move on to the next module: Discover the Business Problem?**

The wording is pinned so it stays compliant: it is a single yes/no where "yes" (or any readiness
signal) means "yes, move on to the next module (Discover the Business Problem)" and "no" means
"no, keep exploring" — exactly one
meaning each (INV-008), with no "or"-joined choices (INV-051, INV-009). Do not paraphrase it into
an either/or (e.g. "…or shall we move on?"), which would give "yes" two meanings. This is a ⛔
gate (internal - do not render the `⛔`/`🛑` glyphs). Do not advance until the bootcamper is ready.

- **Follow-up question** (contains "?", asks for explanation): research it via `search_docs`,
  **verify the answer with a second confirming MCP call** (see "Verify substantive answers"
  above) before presenting it, then re-present the pinned gate question. Do NOT advance.
- **Readiness signal** ("ready", "let's go", "continue", "next", "yes"): hand off to Module 1
  (`SKILL.md`, "Hand off to Module 1"). Do not re-present the primer or the gate.
- **Not ready** ("no", "not yet", "wait"): acknowledge, invite another entity-resolution question
  or topic, and re-present the pinned gate question. Do NOT advance.
- **Ambiguous:** treat as a follow-up.
- **`search_docs` empty or failing:** tell the bootcamper no docs were found, suggest a
  rephrase, and re-present the pinned gate question.
