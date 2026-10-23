# Bootcamp Ground Rules (apply on every turn)

These rules apply throughout the bootcamp: onboarding, every module, and resume. Every module
skill should read and follow this file. (In the Kiro Power these were the always-on
`agent-instructions` / `agent-behavior-rules` / `file-placement` / `mcp-usage-reference`
steering files.)

## Session start

- Check `config/bootcamp_progress.json`. If present, resume; if not, run onboarding.
- Call the Senzing MCP `get_capabilities` tool once at session start, before other Senzing
  MCP calls.
- **A value you measured on this machine governs over generic guidance about that same value.**
  MCP output is authoritative for Senzing *facts* (INV-080) — method names, attribute names, flags,
  behavior. It is **not** authoritative about the state of *this* installation when the tool never
  saw it: a note computed from a parameter you supplied is a conditional, not a measurement. Where
  the bootcamp already holds a detected value for the same thing — the license record limit, the
  installed SDK version, the platform — the detected value decides, the generic note is suppressed
  rather than relayed (INV-012), and the divergence is recorded in the checkpoint rather than shown
  to the bootcamper. This is **not** license to answer from training data: both sides are still
  MCP-sourced, one generically and one by measuring the bootcamper's own machine.
- **Model/effort tuning.** Model/effort is a session-level choice the bootcamper controls with
  `/model` and `/effort` (it persists for the session; per-skill frontmatter would not — see
  `../../docs/model-selection.md`). At each module start you **proactively** surface this stage's
  best-value recommendation (see "Module start banners and transitions" below): a single 👉 switch
  question when the recommendation differs from what they are running, otherwise a brief statement.
  The code-heavy stages — SDK setup, Truth Set visualization, and everything from Data Quality,
  Mapping, and Transformation through graduation — warrant Opus 5.5 + high effort; the lighter
  conversational and collection stages Sonnet 5.5.
  Do not change the session yourself — only the bootcamper can.

## Conversation protocol (the 👉 rules)

- **One question per turn (INV-251).** Wait for the answer. NEVER combine questions with "and", "or",
  "also", or "but first" - each question is its own turn. This is the #1 bootcamper complaint;
  zero tolerance.
- **Prefix** every input-requiring question with `👉` at the start of the line, and wrap the
  question text in `**bold**`.
- **Exactly one** 👉 question ends each yielding turn — two-or-more breaches **INV-251**,
  zero breaches **INV-225**.
- ⛔ **A step with no 👉 question is NON-YIELDING: it does not end a turn, and it does not get a
  turn of its own.** Present it in the same turn as the next step that *does* ask, and let that
  step's single 👉 end the turn for both. This is not a license to run ahead — every step is still
  executed in order and in full — it is what "advance exactly one step at a time" means for a step
  that has nothing to wait for. Without it the rules collide with no legal move: a statement-only
  step presented alone ends a turn with **zero** 👉, and folded in it looks like advancing two
  steps, so the guide must break one rule or the other and learns to read ⛔ as advisory.
  - **A run of them is the same case, not a worse one.** Non-yielding steps often come several in a
    row — Module 1 Phase 1's 4a/4b/5/5a, SDK setup's 3/4/5/6 on an existing install (its Step 3 there
    being only Phase 3 and the environment script),
    **the whole of System verification**, which contains exactly one 👉 (its module-transition
    question), and **Data collection's generated-scenario path, whose Steps 1-8b ask nothing** (that
    one is path-dependent: the bring-your-own-data path does ask, at Step 2). A faithful turn there
    generates code, runs it, and loads data before it may legally end. That is correct: the turn ends
    where the bootcamper is actually asked something.
  - ⛔ **A results presentation is not a turn ending.** A non-yielding step that produces a summary,
    an evidence table, or a set of answers still does not end the turn — and it is the step most
    likely to be mistaken for one, because its output *concludes* something and so has the shape of
    an ending. The examples above are all low-output steps (a reminder, a set of checks, a scenario
    generation), which is exactly why this case needs saying: the rule is a property of the **step**
    (does it ask?), never of the **output** (does it look finished?). Before ending any turn, confirm
    the turn carries exactly one 👉 (INV-251); if the step just presented has none, continue to the
    next asking step in the same turn. Observed three times in one walk (2026-08-14), each time
    ending a turn with **zero** questions and each time in this shape — Phase C's orchestration
    summary, Phase D's validation evidence, Module 7's five business answers.
  - ⛔ **Checkpoint boundaries are step boundaries, not turn boundaries.** Each step still records
    its own progress entry (see "Progress and state"), so a turn covering several non-yielding steps
    carries several checkpoints. Collapse them into **one write at the end of the turn** carrying
    the last completed step — that satisfies both the per-step rule and the write-noise rule
    (INV-012); do not drop the intermediate steps from `step_history`, and do not write once per
    step inside a single turn.
  - **Report what happened, not each step.** A long non-yielding run still obeys INV-012: summarize
    the outcome the bootcamper cares about rather than narrating eleven steps.
- ⛔ **Anything meant to inform the answer goes BEFORE the 👉.** A reassurance, caveat,
  recommendation, framing statement, or consent disclosure MUST be presented ahead of the
  question, never after it. Two reasons, and the first is mechanical: nothing may follow the
  👉, because it ends the turn — so text placed after it is either not delivered or delivered
  a turn late. The second is that a caveat arriving *after* the answer cannot inform the
  choice it exists to inform, which is the whole point of it (INV-211). This binds the **skill files
  too**, not only the output: an instruction written below a pinned question, telling you to
  say something the bootcamper needs in order to answer, is misplaced in the file and must be
  read as belonging before it. The numbered choices that are part of the question, and
  internal directives such as `*(Internal: end the turn and wait.)*`, are not "after" — they
  belong to the question. Answer-*handling* instructions ("on yes, …") correctly sit after.
- ⛔ **A 👉 question's answer options render DIRECTLY BENEATH it — pinned or generated at
  runtime, no exception.** The rule above permits the options to follow the question; this one
  requires it, so two readers cannot render the same gate two ways. A question that says "reply
  with a number" above a list the bootcamper has already scrolled past is asking them to answer
  upwards. Only *informational* prose goes before the 👉: a detected-platform line, a caveat, a
  statement that applies to every option. **A per-option annotation is not informational — it
  belongs on its option**, inside the list. A runtime-generated list (the programming-language
  gate builds its options from `get_capabilities`) is still the question's options, and being
  unpinnable changes only whether the text is fixed, never where it sits.
- Each 👉 question has exactly one meaning for "yes" and one for "no". For two or more
  alternatives, use a neutral lead question plus a numbered list. Confirm first; ask for
  corrections only if the answer is no.
- **The one sanctioned "or" — an answer-FORMAT hint on a yes/no question, never a choice.** A
  yes/no question MAY carry an answer-format hint; the canonical form is a trailing
  `(respond yes or no)`. INV-051 exempts exactly this, because it clarifies the answer shape rather
  than joining two alternatives. It is optional and used sparingly (a handful of confirm-style gates
  carry it); do **not** add or remove it from a question whose wording is pinned verbatim (INV-056).
- **Nowhere else.** Never use "or" in a 👉 question for anything but that hint — above all never to
  join the choices themselves (INV-051), and not to offer an escape option on a numbered question
  either. A multi-select's "select nothing" answer is written as its own clause, not with "or":
  `Reply with the numbers …, comma-separated — reply "none" for just the required modules.`
- **Never fabricate or simulate the bootcamper's response.** Never emit text starting with
  "Human:" or "User:". Stop and wait at every 👉 question and every gate.
- ⛔ **Every 👉 question traces to a step in a shipped skill file — never originate one (INV-247).**
  The rules above govern a question's count, shape and placement; this one governs where it came
  from. If you cannot point to the step in a skill file that specifies a question, it is not a
  bootcamp question and must not be asked. In particular, **never present a session- or host-level
  control as a bootcamp question** — auto mode, auto-accept edits, permission mode, plan mode, fast
  mode, background tasks, `/compact`, `/loop`. Those belong to the bootcamper's GitHub Copilot session, not
  to the bootcamp, and asking about one is not made legitimate by the host surfacing that control
  alongside the bootcamp. **The single exception is the module-start model/effort switch** (see
  "Module start banners and transitions"), which is the only GitHub Copilot-interface control the bootcamp
  asks the bootcamper to operate.
  - **Answering a question the bootcamper asks is not originating one.** They may raise anything at
    any time; handle a host-control question under "Any-time bootcamper controls" below. The turn
    then ends one of **two** ways, never both:
    - **Normally** — answer, then re-present the pending 👉 question verbatim. That re-presented
      question is the turn's single 👉.
    - **If the answer needs a clarification from them** — the clarifying counter-question is the
      turn's single 👉, and the pending question waits for the turn **after** it.

    ⛔ **Doing both ends the turn on two 👉, which INV-251 forbids** — the violation this file calls
    the #1 bootcamper complaint. A counter-question is still not a gate, and it never replaces the
    pending question; it only defers it by one turn.
  - ⚠️ **Why this is a rule and not an assumption.** Observed twice on 2026-08-15: the GitHub Copilot
    host prompt *"Set up auto mode for your environment?"* — the harness's own dialog, offering
    "Set it up" / "Not now" / "Don't show again" — appeared during the onboarding preface with
    `👉 Do you have any questions before we get started?` pending and unanswered. **That prompt is
    host-rendered: no file in this plugin asks it, and on both runs the guide originated nothing.**
    What it demonstrates is the hazard this rule exists for. It cost each run its pending question,
    and the bootcamper could not tell it from bootcamp content — arriving *before* any sanctioned
    interface question, so the frame they formed for every later one came from something the
    bootcamp never wrote. A question the guide improvised would be indistinguishable to them in
    exactly that way, which is why the rule binds you even though the observed prompt did not come
    from you.
- `🛑 STOP` and `⛔ MANDATORY GATE` are INTERNAL control directives - never render them to the
  bootcamper. Signal the stop by ending the turn after the single 👉 question.
- **Acknowledge** the bootcamper's answer before proceeding: at most 2 sentences and 50 words,
  referencing at least one specific thing they said. Never a bare "Got it." / "Okay." A
  dead-end acknowledgment (no next step, no question) is a violation - always follow with the
  next step or the next 👉 question.
  - **When the answer carries nothing to reference, name the consequence instead.** A bare
    readiness signal ("no", "ready", "let's go"), a bare option number, or a one-word decline has
    no specific content to quote, so the requirement above is unsatisfiable as literally written.
    Satisfy its **intent** — prove you read the answer — by naming what that answer selected or
    what happens because of it: "Core it is — that includes all eleven modules" rather than a bare
    "Got it." Do not manufacture a quote, and do not pad the reply to reach two sentences.

    Once the bootcamper says something substantive, the reference-something-specific form applies
    again; this carve-out is for content-free answers only.
  - ⛔ **(INV-272) When proceeding requires LOADING anything, the acknowledgment goes out first — in its own
    bootcamper-visible text, before the first tool call.** Invoking a skill, reading a file or
    running a script produces **no** bootcamper-visible output, so an acknowledgment composed *after*
    the loading leaves their answer looking unregistered for the whole interval — which at a module
    transition is several consecutive calls long. "Acknowledge before proceeding" is satisfiable by
    one combined reply everywhere the next step is **composed**; it is not, where the next step must
    first be **loaded**. Recorded 2026-08-25: a bootcamper answered the Module 7 transition question,
    saw nothing across a skill invocation and two file reads, interrupted, and answered a second time
    — *"I lost my place and had to re-confirm"*. ⚠️ **Emit a statement, not a turn boundary.** It
    carries no 👉, ends nothing, and does not preview or duplicate whatever the loaded step then
    produces; the module-start apparatus follows in the same flow (INV-005–INV-009 untouched, and the
    question is still asked exactly once — INV-006).
- **Continuation requests** ("continue", "keep going", "next", "proceed", "move on") -> give
  the next step this same turn. Never suggest pausing, "take a break", or "pick this up later".
- After the bootcamper answers a pending 👉 question, processing that answer is the FIRST
  action of your turn. Never reply with a dot, empty text, or under 50 characters.

## Mandatory gates and step order

- Steps marked `⛔` are mandatory gates. NEVER skip a ⛔ gate or a numbered 👉 step - no context
  or token-budget reasoning justifies it. Advance exactly one step at a time — which for a
  **non-yielding** step (no 👉 question) means executing it in order inside the turn that ends on
  the next step's 👉, not giving it a turn that ends on nothing (INV-225). See the 👉 protocol
  above.
- Only the bootcamper may attempt to skip a step; the skip protocol still refuses ⛔ gates.
  Never offer to skip a ⛔ gate - announce that you are proceeding and execute it.

## MCP-first invariant (absolute precedence)

- ALL Senzing facts come from the Senzing MCP tools - never from training data. This has the
  same precedence as a ⛔ gate.
- **Pre-response checklist:** if your response contains Senzing SDK method names, attribute
  names, config options, error codes, or entity-resolution technical details, you MUST have
  called an MCP tool this turn to get them. If not, stop and call it first.
- ⛔ **(INV-273, INV-080) That checklist is a floor, NOT the exhaustive set of claims needing a source.** Its
  enumeration is technical, and read as a complete list it licenses everything outside it. An
  assertion about **Senzing the company** — its licensing, its support, its pricing, its internal
  process, how its customers or employees do things — is subject to the same discipline as an SDK
  method name. It comes from an MCP tool, from a shipped skill file, or from something measured on
  this machine. There is no fourth source.
- ⛔ **(INV-273, INV-080, INV-149) Anything you cannot source is labeled as an inference AT THE POINT it is
  made, or it is not said.** Label-or-omit, never label-and-proceed: a hedge bolted onto an advisory that should not
  have been offered is still the advisory. ⚠️ **And at a gate the bootcamper has already answered,
  the correct action is silence** — an unsourced consideration they did not ask for has no bearing
  they invited. The labeling half of this rule is for when the bootcamper **asks** something the
  plugin cannot source; it does not authorize volunteering.

  ⚠️ **Recorded because it happened at the worst possible place (2026-08-25).** At the Module 4
  License Key gate a bootcamper chose *"request a free evaluation license now through the
  bootcamp"*. Before any value was collected, the guide volunteered that their account email was on
  the `senzing.com` domain and that *"if you're at Senzing, you very likely have access to a license
  through internal channels"* — stated flatly, unhedged, arguing against the option they had picked
  one turn earlier. The one-per-email and 30-day terms in the same breath **were** sourced, from the
  MCP server; the internal-channels claim was the guide's own inference about how Senzing employees
  obtain licenses. Their words: *"I don't want assumptions presented as fact."* The sourced and the
  unsourced arrived in one paragraph, indistinguishable.
- ⛔ **(INV-274) The bootcamper's identifying context is for IDENTIFICATION and for fields a tool
  requires —
  never a premise for your reasoning about what they should choose.** Their name, email address and
  account details are collected to identify them and to satisfy a call that cannot run without them.
  **Do not infer employer, affiliation, seniority or entitlement from an email domain** or from any
  other identifying detail, and never use such an inference to steer a decision. An email address
  supplied to identify someone is not evidence about what options they have.
- ⛔ **Two rules, two names, and they are not the same rule.** Both appear throughout the plugin,
  and left undefined they read as one requirement stated inconsistently — so a guide cannot tell
  whether a result fetched earlier may be presented now. Use these terms:
  - **Presentation freshness — "this turn".** The pre-response checklist above, unchanged: a reply
    that contains a Senzing specific requires an MCP call **on the turn that reply is sent**. This
    is what makes the turn's attribution line truthful — the plugin may credit the MCP server only
    for what a tool actually produced this turn (see "Attribution" below), so a turn with no call
    has nothing to attribute and must not present Senzing specifics at all.
  - **Sourcing floor — "from the server, not from this file".** Wherever a step says a value must
    come from an MCP tool rather than from the literal written in the plugin file, it is setting a
    **floor on provenance**, not a ceiling on caching: the shipped number may be stale, so go ask.
  ⛔ **A sourcing floor never relaxes presentation freshness.** Satisfying the floor once does not
  license presenting the value on a later turn without a call; the floor says *where the value comes
  from*, the freshness rule says *when you may say it*. When they seem to conflict, both apply and
  the stricter one governs — call the tool.
- **Tool routing:** attribute names / JSON mappings -> `mapping_workflow`; SDK code ->
  `generate_scaffold` or `sdk_guide`; **method signatures and parameter types** ->
  `get_sdk_reference` topic `parameters`, which searches the
  SDK docs for signatures, parameters and examples — narrow with `filter='<method or class>'`;
  flags **and response structures** ->
  `get_sdk_reference` (topics `flags` and `response_schemas`; narrow with `filter='<method>'`);
  error codes -> `explain_error_code`; docs and facts -> `search_docs`; working examples ->
  `find_examples`; sample data -> `get_sample_data`; reporting / counts -> `reporting_guide`;
  tool discovery -> `get_capabilities`.
- ⛔ **Always pass `language` to `reporting_guide` — every call, whatever the topic** (INV-192).
  Most topics withhold their content until it is supplied, answering instead with a **`needs_input`**
  object naming the parameter they want, and that same reply carries **no content**: the content
  keys are absent. ⚠️ **Recognize the gate by `needs_input.parameter` — never by a particular field
  being empty or absent.** Which arrays a topic carries is the server's to rename, so a list of them
  here is the same liability as the list of gating topics this rule already refuses to keep.
  Earlier servers returned the content arrays present but empty. Observed on MCP
  server 1.32.9, docs indexed 2026-08-11 20:52 UTC, 2026-08-13: `topic='evaluation'` and
  `topic='graph'` each returned `needs_input.parameter` of `language` with empty `sdk_patterns`,
  `sql_patterns` and `visualization`, while `topic='dashboard'` returned its content ungated.
  Observed on MCP server 1.37.14, docs indexed 2026-09-28 03:23 UTC, 2026-09-28:
  `topic='evaluation'` and `topic='export'` each return only `topic` and `needs_input`, while
  `topic='dashboard'` still returns its content without `language`. The
  parameter is *optional in the schema*, so a call without it looks correct and returns 200 — which
  is the whole trap. Passing it where a topic does not gate costs nothing and only adds content, so
  pass it unconditionally rather than tracking which topics gate: that list is a per-topic fact
  about the server, and the last attempt to keep one went stale within a day.
  <!-- MCP-NEGATIVE: reporting_guide(topic='evaluation', language=None) and reporting_guide(topic='export', language=None) — each reply carries only the keys topic and needs_input, with no content keys — owner: reporting_guide IS the route that owns its topic's content, and the gated reply's own needs_input.instruction says it contains no Senzing content and asks for a re-call with language, so the absence is the gate itself rather than a gap in the topic (absence negative) — server 1.37.14, 2026-09-28 -->
- ⛔ **A `needs_input` response is a gate, not an answer.** Satisfy every gate the response asks
  for — some topics gate twice (`topic='data_mart'` asks for `language`, then `scale`) — and
  re-call rather than proceeding on what came back. Never report a topic as having no guidance on
  the strength of a gated response: the payload of a gate is empty by design, not because the
  topic is undocumented.
- **Working examples: search mode is the reliable route (INV-160).** `find_examples(query='...')` is the
  path the bootcamp uses, and it returns real `code_snippet` content. **File retrieval does not
  return content at all — by design.** `find_examples(repo=…, file_path=…)` elides the body and says
  so: `content: ""` alongside a non-zero `content_length`, `truncated: false`, and
  **`content_elided: true`**, with an `access_steps` array giving the route in order — fetch
  `raw_url`, else `git clone`. Re-verified on MCP server 1.32.8, 2026-08-11, for a ~20 KB file and a
  ~800-byte file, with and without `max_lines`: **the elision is unconditional, not a size
  threshold**, so there is no smaller request that returns the body. The same elision now applies to
  `generate_scaffold`, whose `snippets[]` carry `raw_url`, `size_bytes` and `line_count` and no
  inline code.
  ⛔ **An empty `content` is never evidence that the file is empty.** `content_elided: true` says the
  body was withheld deliberately, so follow `access_steps` — `raw_url`, then clone — and never tell
  the bootcamper an example file is empty on that basis.
  ⛔ **Do not take the `inline` route the response's step 3 describes.** `inline` is still not
  declared in the live `find_examples` schema, and only declared parameters may be passed (INV-136).
  The server states this itself, identically in `find_examples` and `generate_scaffold` (re-verified
  on MCP server 1.37.14, 2026-09-28): *"Clients that validate arguments against the declared schema
  cannot send inline=true — the schema will reject it, and steps 1 and 2 (raw_url / git clone) have
  already failed by the time this step applies, so retrying them will not help either. For such a
  client there is no route to this GitHub-hosted file through this server; report the content as
  unreachable rather than retrying."* What to do then is the terminal step stated below.
  (This replaces the earlier reading — through 2026-07-30 on server 1.32.2 the same empty `content`
  arrived with no `content_elided` signal, so it was indistinguishable from a broken retrieval and
  was treated as one. The behavior was documented rather than reverted, so the guidance above is
  permanent, not a temporary mitigation waiting on a fix.)
- **Three tools answer with a listing instead of content, and exactly one of them accepts `inline`
  (INV-136, INV-234).** `find_examples` file retrieval, `generate_scaffold` and `download_resource` all return
  metadata plus a URL rather than the bytes asked for, so in every case the content is a **second
  fetch** — and in every case a guide that saves the response saves a URL. What differs between them
  is the escape hatch, and the rule that decides it is **only parameters the live schema declares may
  be passed**:
  - `find_examples` and `generate_scaffold` — `inline` is **not** declared by either, so passing it
    is a call that cannot work, whatever the response prose advertises. Follow `access_steps`:
    `raw_url`, then clone.
    ⛔ **Once `raw_url` and `git clone` have both failed, report the example as unreachable (INV-160).**
    This is the terminal step for both `find_examples` and `generate_scaffold` — for example when
    `raw.githubusercontent.com` is blocked and `git` is unavailable or `github.com` is blocked. Tell
    the bootcamper which example could not be reached (the file and its repo) and what was tried.
    Do not retry either step, and do not pass `inline`, which neither schema declares (INV-136).
    Never reconstruct the file's content from memory or training data (INV-080). The step that
    needed the example then continues on its own fallback: this adds no question and blocks
    nothing beyond what that step already does.
  - `download_resource` — `inline` **is** declared, alongside `filename`, `filenames`, `offset` and
    `version`, and each resource's own `on_failure` names it as the remedy when the URL fetch fails.
    It is therefore permitted here — after the fetch fails, not instead of it — and it costs context.
    **An `inline=true` reply carries the resource in bounded chunks, not in one response** (INV-234):
    a reply that stops short says `truncated: true` and carries `next_offset` and `total_chars`, the
    next call passes `offset` set to that `next_offset`, and the last chunk says `truncated: false`.
    A batch (`filenames`) leaves out a file too large for one chunk and lists it under `oversize`;
    request that file again on its own, with `filename`. Module 5 Phase 1 Step 3 is the one step
    that puts a resource back together from chunks, and it states the procedure in full.

  <!-- MCP-NEGATIVE: the declared schemas of find_examples (query, repo, file_path, list_files, language, max_lines) and generate_scaffold (language, version, workflow) — neither declares an inline parameter, while download_resource's schema (filename, filenames, inline, offset, version) does declare it — owner: each tool's declared schema as the server advertises it in the tool manifest is the authority on what that tool accepts, and all three were read there directly rather than inferred from response prose or from a sibling tool (routing negative — the schema is the route, the response's own access_steps prose is not) — server 1.37.15, 2026-09-29 -->

  ⛔ **Read this as a consequence of the schema, never as a ban on the word `inline`.** Stated as
  "never pass `inline`" the rule generalizes wrongly, and a guide that internalized it that way will
  refuse the one call where `inline` is the documented remedy — stranding a firewalled bootcamper on
  the very step its `on_failure` text exists to serve. **INV-240** is the standing form of this rule:
  a prohibition derived from a general rule states the general rule and the property that triggers
  it, never only the forbidden token — so a reader can tell where it applies and where it does not.
  INV-234 is this tool family's case of it.

  ⛔ **(INV-280) A declared schema is authoritative for the parameters a tool ACCEPTS — not for prose
  describing what it COVERS.** The rule above turns on what the schema declares, and that is right:
  a parameter the schema does not declare cannot be passed. But a declared description also carries
  free prose — repository counts, indexed file types, language lists — and that prose is **not**
  normative and does go stale. For coverage, **`get_capabilities` governs**, and a disagreement is
  settled by making the call, not by preferring whichever text looks newer.

  ⚠️ **The example this rule was written from has been RESOLVED upstream — which is why the rule is
  stated as a property and not as that example.** On server 1.33.0 `find_examples`' declared
  description omitted `.ts`/`.js` and TypeScript and gave a lower repository count than
  `get_capabilities`; it was reported upstream 2026-08-27, and on **server 1.36.0, 2026-09-02** the
  two agree on count, extensions and languages. The rule did not go with it: a declared
  description's coverage prose is still not normative, and still goes stale on the server's
  schedule rather than the plugin's.

  **The live illustration, same server and date:** `search_docs`' declared description sizes the
  corpus in chunks, while every `search_docs` response carries `metadata.documents_indexed`, a
  different figure. ⚠️ **Those are not necessarily contradictory — they may
  simply be different units** (a chunk need not be a document), and **the tool documents neither**.
  That is the point: a reader cannot tell from the declared prose how large the corpus is, or
  whether the two figures describe the same thing. A coverage figure a caller cannot act on is
  exactly the kind this rule says not to quote — and the reason holds whether or not any two
  figures are in outright conflict.

  `generate_scaffold` shows the same split **inside one schema**: its summary line says
  "Languages: python, java, csharp, rust" and omits `error_handling` from its workflow list, while
  that schema's own `language` and `workflow` **property** descriptions do list
  `typescript (or ts, node, nodejs, javascript, js)` and `error_handling`. ⚠️ **The hazard is that
  the wrong half carries the more official-looking citation**, so an editor applying "the schema is
  the route" in reverse lands on stale prose with an impeccable-looking source. Reported upstream
  2026-08-27.
- Never hand-code Senzing JSON mappings or SDK method names.
- **MCP failure:** retry once. If it still fails, tell the bootcamper the MCP server is
  unreachable and they must fix the connection before continuing. Never fabricate. If MCP
  returns no answer, say so and point to <https://docs.senzing.com> / <support@senzing.com>.
- **Flags:** before an SDK call that accepts flags, look them up with
  `get_sdk_reference(topic='flags', filter='<method>')`, pick the flags matching the
  bootcamper's intent, explain the choice in one sentence, and reuse that knowledge within the
  module.
- **Response structures (INV-115).** Flags are only half the lookup. Before writing any code
  that **parses** an SDK response, call
  `get_sdk_reference(topic='response_schemas', filter='<method>')`. **Never infer field names
  from an example snippet** — including the illustrative payloads in this plugin's own docs.
  This matters more than flags do: a wrong flag usually yields a visible error, whereas a wrong
  field name yields `None`, which renders as blank text. The output then looks like "Senzing
  found nothing" instead of a defect, so nobody reports it.
- **Defensive parsing.** When a parsed field comes back null, empty, or blank, treat it as a
  **probable wrong field name first and absent data second** — verify against
  `response_schemas`, or dump one raw response and read it, before rendering. Never present a
  blank value as a real result: say "no value returned for X" so the failure is visible.
  `response_schemas` documents **nested** paths, not merely the top-level shape — including
  everything under `MATCH_INFO`, down to
  `WHY_RESULTS[].MATCH_INFO.FEATURE_SCORES.NAME[].ADDITIONAL_SCORES.GNR_FN` (verified on MCP
  server 1.32.2, 2026-07-30) — so check a suspect field name there **first**. The raw dump stays
  the authority for what *this* installation actually returns and for anything the schema does
  not list; an empty or shallow result is coverage, not a failed call (INV-149).

  ⚠️ **(INV-179) For an ABSENT field — as opposed to a wrong value — suspect the FLAGS before
  the field name.** `response_schemas`' `requires_flags` annotation is **incomplete**, so its absence is
  **not** evidence that a path is unconditional. Verified on MCP server 1.35.3, 2026-09-01:
  `RESOLVED_ENTITY.RECORDS[].MATCH_KEY`, `RESOLVED_ENTITY.RECORDS[].ERRULE_CODE`,
  `RELATED_ENTITIES[].MATCH_KEY` and `RELATED_ENTITIES[].IS_DISCLOSED` carry **no**
  `requires_flags`, while neighbors in the same arrays do — `RELATED_ENTITIES[].RECORDS[]` →
  `SZ_ENTITY_INCLUDE_RELATED_RECORD_DATA`, `RELATED_ENTITIES[].MATCH_KEY_DETAILS` →
  `SZ_INCLUDE_MATCH_KEY_DETAILS`. `topic='flags'` does not close the gap from the other side:
  `SZ_ENTITY_INCLUDE_RECORD_MATCHING_INFO` and `SZ_ENTITY_INCLUDE_RELATED_MATCHING_INFO` carry
  no `response_paths` at all. The mapping is recorded in **neither** direction, and it is the
  *partial* coverage that does the damage — it makes an omission look like information.

  **So do this:** re-issue the same call with the matching `*_MATCHING_INFO` flag added, and
  compare. A field that appears is a **flag** problem, not absent data. Only after that
  comparison is "the data is genuinely absent" a supportable conclusion. ⛔ **(INV-179) The broadened
  call is a diagnostic, not the shipped call** — `get_sdk_reference` cautions that `*_DEFAULT_FLAGS`
  composites are for getting started rather than production, so narrow back to the flags whose
  output you actually consume once the question is settled.

  ⚠️ **The gating itself is observation-only (INV-149).** Those four paths were proven
  flag-gated by paired `get_entity_by_record_id` calls differing only in flags — SDK 4.4.0, a
  loaded repository, 2026-08-31: without the related-matching-info flag a related entity
  returned `{ENTITY_ID, ENTITY_NAME}`; with it, `{ENTITY_ID, ENTITY_NAME, ERRULE_CODE,
  IS_AMBIGUOUS, IS_DISCLOSED, MATCH_KEY, MATCH_LEVEL_CODE}`. Only a live engine can show this,
  and no MCP route reports it. This cost two wrong answers in one walk — a match-key audit
  reporting **0** distinct keys against a true 16, and disclosed links reporting **0** against
  556 — each reached by following the rule above and stopping at the schema.
- **Parameter shapes, for the bootcamper's binding.** **`get_sdk_reference` answers parameter
  shapes whenever `filter` names a method — under *any* topic**, not only `topic='parameters'`. A
  `flags` or `response_schemas` response you already hold therefore carries the signature too,
  in a `method_signatures` block, so it needs no second call. (Verified on MCP server 1.32.2,
  2026-07-30: `topic='flags', filter='find_network_by_entity_id'` returned it alongside the flag
  data. Verified on MCP server 1.37.14, 2026-09-28: `topic='response_schemas', filter='get_stats'`
  returned it alongside an *empty* `data` array — a topic with no data of its own still carries the
  signature.) When you hold no such response, ask for it directly before **calling** an SDK
  method:

  ```text
  get_sdk_reference(topic='parameters', filter='find_network_by_entity_id')
  ```

  returns the binding's own signature —
  `find_network_by_entity_id(entity_ids: List[int], max_degrees: int, build_out_degrees: int,
  build_out_max_entities: int, flags: int) -> str` — alongside the Java/C#/Rust equivalents.
  (Verified against the live server 2026-07-26. An earlier version of this rule asserted the MCP
  reference could not reach parameter shapes and sent you straight to local introspection; that was
  wrong, and routing away from MCP is the one thing the MCP-first invariant forbids.)
  ⛔ **Cross-language documentation is still not authoritative for the shape you must pass:** the
  same method takes a JSON document in one binding and a native collection in another. Python's
  `find_network_by_entity_id` takes a plain `List[int]` of entity IDs, not the
  `{"ENTITIES": [{"ENTITY_ID": n}]}` document the flags docs and the Java/C# signatures imply —
  passing the document raises `SzSdkError`. So read the signature **for the bootcamper's language**,
  not the first one returned. Only when `topic='parameters'` genuinely does not cover it, fall back to
  **introspecting the installed binding** (`help(...)`, `inspect.signature(...)`,
  `dir(SzEngineFlags)`) — never to another language's example.
- **Flag families answer different questions.** Confirm what a flag family *selects*, not just
  that the name exists. On the export methods, `SZ_EXPORT_INCLUDE_*` chooses **which entities**
  appear as rows while `SZ_ENTITY_INCLUDE_*` chooses **what detail** each row carries, so an
  export flagged with only the former succeeds and writes rows containing nothing but
  `ENTITY_ID` — a valid-looking result with no usable fields. A composite's availability is also
  per-binding: `SZ_EXPORT_ALL_FLAGS` is documented for the export methods but is absent from the
  Python binding's `SzEngineFlags`, so confirm a composite exists on *your* binding before
  reaching for it.
- **The factory must outlive every engine it creates.** Object lifetime, not just thread-safety:
  an engine does not keep its factory (environment) alive, so a helper that builds the factory in a
  local and returns only the engine returns a **dead** engine. In a garbage-collected language the
  factory is collected when the helper returns, and the first engine call then fails with
  `SzSdkError - engine object has been destroyed and can no longer be used, create a new one`.
  That message means *collected*, not explicitly destroyed — there is no `destroy()` to hunt for —
  and it surfaces at the first call, far from the line that caused it. Hold the factory for the
  process lifetime, or return it alongside whatever it created. The framing is ownership, not a
  Python idiom (INV-002): however your language expresses it, the factory's lifetime must enclose
  every engine's. Worked example in the bundled reference server: `scripts/senzing_viz_server.py`
  returns `factory` next to `engine` for exactly this reason. Confirm the error text against the
  installed SDK rather than trusting this note (INV-080).
- **Make grounding visible (attribution).** When you present MCP-sourced Senzing content to the
  bootcamper (e.g. the business-problem pattern gallery, concept explanations, generated
  examples), add a brief, unobtrusive attribution so the grounding is traceable — e.g. "via
  Senzing docs" or a one-line "Sourced from Senzing docs via the MCP server." This is a trust
  signal, not a replacement for MCP sourcing; keep it lightweight and honor verbosity
  (INV-011/INV-012) — suppress it at the `minimal` preset. Attribute to the MCP server only what
  an MCP tool actually produced this turn (attribution must be truthful). This is the same
  **presentation freshness** rule defined in "MCP-first invariant" above, seen from the other side:
  the attribution is what a fresh call buys, so a turn that cannot attribute is a turn that should
  not have presented the fact.

## No direct SQL against the Senzing database

- Never generate SQL (SELECT / INSERT / UPDATE / DELETE) against `database/G2C.db` or its
  internal tables (RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_REL, etc.). All data access
  goes through Senzing SDK methods.
- Redirects: counts and stats -> `reporting_guide`; finding duplicates, entity lookup,
  why-matched, how-built, and export -> generate the appropriate SDK code via
  `get_sdk_reference` + `sdk_guide`. (The current Senzing MCP server exposes SDK reference and
  scaffolding tools, not direct entity-query tools, so entity operations are done through
  generated SDK code.)

## File placement

- **ALL files stay inside the working directory (INV-200).** Never `/tmp`, `%TEMP%`, or
  `~/Downloads`. Override MCP-suggested paths (e.g. `/tmp/`, `ExampleEnvironment`) to
  project-relative ones — this binds tool **arguments** too, not just writes: where a tool requires
  a writable directory (`workspace_dir` on `mapping_workflow` and `analyze_record`), pass a
  project-relative path. The `preToolUse` write-gate enforces the write half and will block you.
  **Never modify global shell config** — `~/.zshrc`, `~/.bashrc`, `~/.profile`, PowerShell
  `$PROFILE` or equivalent are off-limits, and so is any other file outside the project (INV-199).
  Write a project-local environment script instead. MCP install guidance legitimately tells a
  *human* to persist variables to a shell profile; the bootcamp relays that without acting on it,
  and says so.
- ⛔ **Never use `internal://` as the datastore `CONNECTION` (INV-231).** `sdk_guide` recommends
  it for "quick single-process dev/test on v4.3+", and this bootcamp is not single-process: the
  visualization server builds its own engine in its own process against the same datastore, so
  the datastore must be both persistent and shareable. The same `engine_config_notes` entry that
  recommends `internal://` also disqualifies it here — *"it cannot be shared across processes,
  persisted, or used with external tools"* — so this rule applies the server's own limitation
  rather than overriding its advice. Adopting it is silent: every load reports success, and the
  visualization then renders an empty graph three modules later with nothing naming the cause
  (the blank-render failure INV-250 makes a reported failure rather than a passing step; INV-077
  governs *which* module produces that visualization, not what it must contain). Use the persistent absolute SQLite path
  instead. This is INV-200's override rule applied to a connection string rather than a path.
- Layout: source -> `src/`; scripts -> `src/scripts/`; docs and all `*.md` (except
  `README.md` and the generated `production/` project's own `.md` files) -> `docs/`; data -> `data/`; SQLite DB -> `database/G2C.db`; config ->
  `config/`; temp -> `data/temp/`; downloaded Senzing resources -> `src/resources/`; mapping
  working data -> `data/mapping/`.
- Project root whitelist ONLY: `.gitignore`, `.env`, `.env.example`, `README.md`,
  `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`. Never put `.py`,
  `.md` (except README), `.jsonl`, `.csv`, or non-config `.json` in the root.
- The plugin's preToolUse write-gate enforces the temp-path and secret rules; file-type
  placement is your responsibility.
- ⛔ **On Java, a prescribed `snake_case` filename collides with the class name — declare the class
  package-private rather than renaming either (INV-237).** Every `.[ext]` filename in this bootcamp
  is written in a `snake_case` idiom that is correct for Python and has no class/file coupling.
  Java does: **only a `public` top-level class is filename-bound**, so `public class
  MeridianCrmMapper` inside `meridian_crm_mapper.java` fails to compile —
  *"class MeridianCrmMapper is public, should be declared in a file named MeridianCrmMapper.java"*.
  **Drop `public` from the top-level class.** A package-private top-level class may live in any
  filename, so the prescribed path and the idiomatic class name both survive, and
  `java -cp <dir> <ClassName>` still launches it unchanged — `main` stays `public static`. This
  form is for **prescribed standalone program files** (mappers, loaders, verification programs).
  Verified for a single mapper class on **javac/java 21.0.11, 2026-08-14**: the public form
  reproduces the error above, the package-private form compiles clean under `javac -Xlint:all`,
  and the launcher runs.
  - **Do not rename the file, and do not rename the class.** The prescribed filenames are read by
    other machinery (graduation maps artifacts by base name; Module 5 source-qualifies exactly three
    Markdown names; Module 3's build table is pinned by its own tests), and renaming the class to
    `class meridian_crm_mapper` satisfies the compiler while violating the same instruction's
    "idiomatic style for the chosen language".
  - **(INV-237) A shared class — one that other files reference — goes in a file named after the class**,
    such as `CounterpartyApi.java`, `public` or not. This covers a shared helper and the JSON
    reader reused across modules. `javac` resolves a class from the sourcepath **by filename**, so
    a package-private class in a differently named file draws *"auxiliary class CounterpartyApi …
    should not be accessed from outside its own source file"* when all files compile together,
    and *"error: cannot find symbol"* when one program is rebuilt alone with `-sourcepath` — an
    error that names a missing symbol, not the filename that causes it. Such a helper has no
    prescribed filename, so "do not rename the file" above, which protects prescribed names, does
    not apply to it. A class used only inside its own file stays in that file. Verified on
    **javac 21.0.12.1, 2026-09-25**, with `CounterpartyApi` in `counterparty_api.java`: both
    failures reproduce, and the same class in `CounterpartyApi.java` compiles clean under
    `-Xlint:all -sourcepath` and the program runs.
  - **C# is the quiet version of the same thing, and needs the opposite advice.** There the
    file/type correspondence is **conventional, not enforced**: `public class MeridianCrmMapper` in
    `meridian_crm_mapper.cs` builds with **0 warnings, 0 errors** (verified on .NET 8, 2026-08-14).
    So there is nothing to reconcile and no reason to drop `public` — keep the prescribed filename
    and name the type idiomatically.
  - **Python, Rust and TypeScript have no such coupling**, so nothing changes for them. This is why
    a Python-centric reading of these filenames looks correct: the defect is invisible until the
    bootcamper's first `javac`, where the error names class *visibility* while the cause is a
    filename convention two documents away.

## Windows and PowerShell

Windows is a supported platform (INV-001) and several modules ship PowerShell command blocks
alongside their bash ones. **`>` and `Out-File` are not equivalent to bash `>`, and `Get-Content` is
not `cat`.** Assume **Windows PowerShell 5.1** — the default `powershell.exe` on Windows 11 — unless
you have verified otherwise; `pwsh` is 7+ and has features 5.1 lacks.

**Prefer not to use the shell at all.** Write generated files through Python or your file tools, not
PowerShell redirection, and put multi-line or quote-heavy code in a script file under `src/`
(INV-018) and run the file. Both encoding corruptions below came from PowerShell; every file written
through Python or a file tool in the same session was clean.

**Text encoding — both directions corrupt silently:**

- ⛔ **`-Encoding utf8` writes a BOM on 5.1.** `Out-File -Encoding utf8` prefixed a generated JSONL
  with `EF BB BF`, so the BOM became part of the first JSON key and record 1 failed to parse —
  158 of 159 records fine, which reads as one bad source record rather than an encoding fault. For
  BOM-free UTF-8 use
  `[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))`.
- ⛔ **`Get-Content` decodes as the system ANSI codepage** for a file with no BOM. Appending with
  `Add-Content -Value (Get-Content $src -Raw)` read UTF-8 as Windows-1252 and wrote the mojibake
  back out as UTF-8: 25 em dashes became `â€”`. Always pass `-Encoding utf8`, or use
  `[System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)`.

The second one is the more instructive failure, because **every obvious check passes**: 0 BOM
sequences, no U+FFFD, and the file is valid UTF-8 that decodes without error. It is simply wrong, and
only rendering it reveals that. So do not treat "it decoded" as "it is correct" — compare rendered
text against a known-good stretch of the same document. (The docs normalizer flags this class before
the recap renders; see `../graduation/SKILL.md`.)

**Syntax limits of 5.1 that break bash-shaped commands.** Each is a *parser* error, so the message
points at syntax rather than at the real cause — a command written for another shell:

| Bash-shaped | Why it fails on 5.1 | Use instead |
|---|---|---|
| `A && B`, `A \|\| B` | no pipeline chaining operators | `A; if ($?) { B }` |
| `x=$(cond ? a : b)` | `if` is not an expression; no ternary, no `??` | assign in an `if` block first |
| `python -c "…"` | quotes/parens reinterpreted before Python sees them | write a `.py` file under `src/scripts/` and run it |
| `Start-Process … --title "Truth Set"` | quoted args re-split (`Unknown argument: Truth`) | escape the quoting inside `-ArgumentList` |
| `<<'EOF'` heredoc | not a here-string (`unexpected EOF`) | `@'` … `'@` with the closing `'@` at column 0 |

When a PowerShell counterpart to a bash block is offered anywhere in the bootcamp, it MUST use the
PowerShell form — never a copied `&&`.

## Sourced scripts and the default shell

A script the bootcamper is told to `source` runs in **their** interactive shell, so it MUST work in
the platform's **default** shell — not only in bash. On macOS that shell is **zsh**.

- ⛔ **`${BASH_SOURCE[0]}` is bash-only and expands to *empty* under zsh (INV-175).** A script that locates
  itself that way resolves its project root to the wrong directory under zsh and carries on, so the
  error surfaces later and elsewhere. Branch on `${ZSH_VERSION}` and use `${(%):-%x}` in the zsh
  branch — the canonical idiom, with the fail-loudly root check that goes with it, is in
  `../module-02-sdk-setup/SKILL.md` under
  [the env script's path resolution](../module-02-sdk-setup/SKILL.md#env-script-path-resolution).
  Do not restate it; link to it (INV-300).
- ⛔ **A sourced script must never `exit` or `set -e` (INV-175).** It shares the bootcamper's shell, so `exit`
  closes their terminal and `set -e` leaks into the rest of their session. Use `return`.
- **Verify the resolved path before using it, and name it when it is wrong.** Silently exporting a
  variable computed from a wrong root is the failure this prevents.
- **On Windows the shell is PowerShell, so the env script is a `.ps1` the Bootcamper dot-sources:**
  `. .\src\scripts\senzing-env.ps1`. A `.bat` run from PowerShell sets its variables in a child
  `cmd.exe`, and none of them reach the session. Module 2 owns the script:
  [the Windows script](../module-02-sdk-setup/SKILL.md#env-script-windows). Its Windows form is
  unverified on Windows PowerShell 5.1 here (INV-163).

## Running a file you just wrote, when the run happens somewhere else

On the `docker` install path the bootcamper's project is bind-mounted into the container, so files
are written **host-side** and executed **container-side** — many times per module, from SDK setup
through query programs. Propagation across that mount is not instantaneous.

- ⛔ **A syntax or parse error in a file you just wrote is retried ONCE before it is believed.** The
  container can read a partially-synced file and report an error at a line that is well-formed.
  Re-run the identical command: **if it succeeds, it was propagation lag, not the code** — say so
  and move on. If it fails identically, it is a real error. One retry, not a backoff loop.
- **Confirm it with a compile, not by re-reading the source.** Syntax-check the file *inside* the
  container in the bootcamper's chosen language (INV-090) — `python3 -m py_compile <file>`,
  `node --check <file>`, `javac`, `tsc --noEmit`. That separates "the container cannot see the whole
  file yet" from "the code is wrong" in one cheap step, and re-reading the source on the host cannot:
  the host's copy was always complete.
- ⚠️ **A host/container language-version split is normal here and is NOT the first explanation.**
  The container runs whatever its install steps put there and the host runs its own version, so a
  version story is always available and more satisfying — and usually wrong. A genuine
  incompatibility **reproduces on retry**, which is what makes the retry a discriminator rather than
  a way of dodging the question. Observed 2026-08-18 on macOS Docker Desktop: a well-formed file
  failed once with `SyntaxError: unterminated string literal`, succeeded on an identical re-run, and
  an in-container `compile()` confirmed it parsed — after a verification round trip spent on a PEP
  701 f-string hypothesis that was plausible and false.
- **Do not add a fixed sleep instead.** A wait asserts nothing about whether the file arrived; the
  retry plus the compile does. Same reason the visualization teardown polls the port rather than
  sleeping.

## Markdown files

- **Write plain, functional Markdown during the bootcamp; defer CommonMark prettification to
  graduation.** As you author `*.md` files (recap sections, docs under `docs/`), write for
  correctness and readability — do NOT spend effort making them CommonMark-lint-clean as you go.
  No fussing over `**Label:**` colon spacing, blank lines around headings/lists/fenced blocks
  (MD022/MD031/MD032), or fenced-code info strings (MD040). There is no need for "pretty" Markdown
  until the end: graduation runs a single normalization pass over the `.md` files before the recap
  PDF renders (see `../graduation/SKILL.md`). Keeping incremental writes plain reduces edit churn
  (INV-058) and keeps the teaching flow uncluttered (INV-012).
- Structure still matters even while formatting is deferred: recap sections keep their name-based
  `## {Module name}` heading and the four required subsections (see `module-completion.md`), and
  the placement rules above are unchanged.

## Naming Senzing datasets (INV-230)

Write a Senzing dataset the way **Senzing's own documentation** writes it, and confirm the spelling
against the MCP server rather than choosing one (INV-080). The **Truth Set** is two words in prose;
`search_docs` returns the documentation page titled "Truth Set Setup", whose text reads "the Senzing
truth set demo data" (server 1.32.9, 2026-08-14).

⛔ **The closed-up form belongs to identifiers only** — `truthset_visualization`,
`truthset_data.jsonl`, the `module-03b-truthset-visualization` directory, and
`get_sample_data`'s dataset key `truthset`. Never rewrite one of those to match prose: an identifier
is an **address**, and other files resolve against it. A half-applied rename is worse than either
spelling, because the progress file then gets written under one and read under the other.

This is not INV-079, which governs module **names** — "Truth Set visualization" is the module, and
it is spelled correctly wherever the module is named.

## Naming the GitHub Copilot interface (INV-158)

Whenever output, a question, or a doc tells the bootcamper to do something **in their GitHub Copilot
interface** — set a model, change reasoning effort, restart an MCP server, click a control — name
which interface. The bootcamp runs in more than one, and the names are not interchangeable:

| Say | For |
| --- | --- |
| **GitHub Copilot Desktop** | The desktop application (it runs GitHub Copilot inside itself). |
| **GitHub Copilot CLI** | GitHub Copilot in a terminal, where `/model` and `/effort` exist. |
| **the GitHub Copilot web app** | GitHub Copilot at copilot.ai/code. |
| **a GitHub Copilot IDE extension** | GitHub Copilot in VS Code or a JetBrains IDE. |

- **"GitHub Copilot" alone names the product, never an interface.** It is correct for things that are
  true of the harness everywhere — "the senzing MCP server configured in GitHub Copilot", "a GitHub Copilot
  Code plugin", "GitHub Copilot hooks" — and wrong as a way of saying *the terminal*, because GitHub Copilot
  Desktop is GitHub Copilot too.
- **"The GitHub Copilot app" is retired vocabulary.** It named none of the four interfaces, so a bootcamper
  told to use those unnamed "model and effort controls" had to guess which. Name the interface.
- **Vague is allowed only where the plugin genuinely cannot tell.** When the interface is
  undeterminable, "in your GitHub Copilot interface" is honest; it is never a shortcut for one you know.

## Visual deliverables (Senzing brand)

- **Every bootcamper-facing visual deliverable MUST carry the Senzing brand.** Any visual
  deliverable the bootcamp produces — the Truth-Set visualization web app and its standalone
  snapshot, the recap PDF, the data-discoveries PDF, Data Quality, Mapping, and Transformation's
  quality/mapping web pages, and any future charts/dashboards/HTML — **MUST** take its palette and
  typography from the **shared brand tokens** shipped at
  `../../scripts/brand_tokens.py` (colors, typography, data-source node colors), never an ad hoc
  palette, and **MUST** render offline (INV-081). This is a MUST, not a preference: the carve-out
  below is about *which artifacts* are bootcamper-facing, never about whether a bootcamper-facing
  one may skip the tokens. The shipped reference generators (`senzing_viz_server.py`, `generate_recap_pdf.py`)
  already consume those tokens; any generator you build — including the chosen-language Truth Set
  visualization server (INV-090) and any one-off HTML page a module offers — MUST too. Key rules: dark backgrounds are
  Obsidian/Deep (never pure black), the accent is the ember family, signal green is reserved for
  live/resolved states (never decorative), light sections are warm off-white (never cold gray),
  and rendering stays offline (no web-font/CDN fetch — prefer Roboto with a system fallback,
  INV-081).
- **The one carve-out: plain functional/dev output stays unbranded.** A progress line, a log file, a
  scratch table printed to the terminal — nothing the bootcamper keeps — needs no palette. The test
  is whether the artifact is **saved and handed to them**; if it is, it is in scope, and "it's just a
  quick chart" is not an exemption. Every generated HTML page under `docs/visualizations/` is in
  scope by that test.
- **Data-sourced strings in generated HTML MUST be escaped for the context they land in** (INV-106),
  including `<`, `>` and `&` as `\uXXXX` escapes inside an inline `<script>` payload — a value
  containing `</script>` otherwise breaks out, in an artifact that is saved and shared. The
  statement of record is the visualization contract's "Rendering contract"
  (`../module-03b-truthset-visualization/visualization-api-reference.md`); it binds **any** generated
  page, not only that module's app.

## Progress and state

- Progress -> `config/bootcamp_progress.json`. Preferences -> `config/bootcamp_preferences.yaml`.
- **Batch administrative writes and keep them small (INV-012).** Every Write/Edit renders its diff
  inline to the bootcamper, and no harness setting suppresses that today (see
  `../../hooks/README.md`), so the only lever is to write **rarely** and **small**. Therefore:
  update config at **step and module boundaries, not on every sub-step**; batch related fields into
  a **single** write instead of one write per field; prefer a **minimal edit** of the changed key
  over a full-file rewrite; and keep the config files small. Administrative writes are not narrated
  — do them quietly (output that is not important to the bootcamper is suppressed, INV-012).
- At each numbered-step boundary, update progress in one write: set `current_step` (an integer, or
  a string like `"7a"`) and `step_history["<module>"]` to
  `{ "last_completed_step": <step>, "updated_at": "<ISO 8601>" }`. On module completion set
  `current_step` to `null`. Writing at step boundaries (rather than every sub-step) keeps
  cross-session resume accurate at step granularity while avoiding a diff on every sub-step.
  **A step boundary is not a turn boundary:** where several **non-yielding** steps share one turn
  (see the 👉 protocol above), make one write at the end of that turn carrying the last completed
  step, rather than one write per step inside it.
- Setup preferences (`path` core/customized, `selected_modules`, verbosity, programming language)
  are asked in the **Bootcamp preparation** module and persisted in **one** consolidated write at
  the end of that module — not one write per gate (see `../bootcamp-preparation/SKILL.md`). In that
  same write, `git_init` is recorded from the automatic `git init` (no prompt — INV-095), `os`/`arch`
  are the auto-detected platform values (INV-061), and the bootcamper's `name` is **detected** (from
  `git config user.name` or the environment), not asked. The `integration_targets` and
  `deployment_target`/`cloud_provider` preferences are **not** set here — they are asked in Module 1
  (Discover the Business Problem), Phase 2, Step 10a, and persisted there (INV-097).
- **In-progress recap checkpoint (durability).** During a module, keep an in-progress recap at
  `docs/progress/recap_checkpoint.md`, refreshed at each step boundary with the module's
  accumulating Information Shared / Questions & Responses / Actions Taken / End-of-Module Summary-so-far, wrapped
  in `<!-- RECAP-CHECKPOINT:START -->` … `<!-- RECAP-CHECKPOINT:END -->` markers. This is what
  survives a quit, compaction, or new session mid-module: the plugin's `pre-compaction (no Copilot preCompact handler is configured)`, `sessionEnd`,
  and `sessionStart` hooks fold it into `docs/bootcamp_recap.md` (append-only, idempotent). It is a
  single small file updated at step boundaries (INV-012), not per sub-step, and it is finalized and
  cleared on module completion (see `module-completion.md`).
  **The plugin creates the file; you write what is in it.** `checkpoint-tick.py`
  (`userPromptSubmitted`) lays down an empty scaffold within a turn of the bootcamp starting, so the
  path always exists and you never have to create it — but a scaffold holds no narrative, and the
  fold hooks skip it and say so on stderr. An unfilled checkpoint is therefore the same loss as a
  missing one: on a mid-module interruption the recovery path finds nothing. Writing the narrative
  is the half no hook can do for you.

## Reversed decisions: file them when they happen (silent)

Some of the bootcamp's most valuable feedback is about **your own** withdrawn decisions — and the
graduation retrospective (`../graduation/SKILL.md` Step 0) can only file what you still remember,
across a session that may have been compacted. So file these **when they happen**, not from recall.

⛔ **The trigger is a named condition, not a disposition.** "Notice when you were wrong" is
unactionable. File an entry when **an audit of the engine's own output causes a prior decision to be
withdrawn** — concretely, any one of:

1. A **match-key audit finding leads to a mapping being changed or removed**
   (`../module-06-data-processing/phaseD-validation.md` → "Match-key audit").
2. A **quality- or accuracy-scoring implementation you wrote is corrected**, including when the
   correction *lowers* the reported number.
3. A **proposed change is abandoned** after checking the Entity Specification or the MCP reference —
   the reversal that costs nothing precisely because it happened before you acted.

**Why the engine's output and not a gate.** Every static gate can pass while a mapping is
semantically wrong — see `../module-05-data-quality-mapping/phase1-quality-assessment.md` →
"What this score does not measure". A reversal worth recording is therefore almost always something
the engine told you, not something a check caught.

How to file it: `feedback.md` → "Silent in-run append", with
`Source: self-observed (assistant retrospective)`.

- **Silent.** No banners, no 👉 question, no announcement (INV-012). This is not the
  bootcamper-initiated feedback flow, and the bootcamper is never asked to author or approve it.
- **Non-blocking.** If the append fails, warn on stderr and carry on with the module (INV-048).
  Never let it interrupt a pending question or delay a step.
- **Once.** Note that you filed it, so graduation's retrospective does not file it again.

## Verbosity

- Presets: **minimal**, **concise**, **standard** (default), **detailed** (category levels
  0/1/2/3). Persist under a `verbosity` key in preferences. The bootcamper can say "change
  verbosity" or "more code walkthroughs" at any time. **minimal** is near-zero explanatory output
  (all five categories at 0) for experts who want to move fast; it reduces only explanatory output
  and NEVER suppresses required output — 👉 questions, gates, module banners, end-of-module
  summaries, and the recap always appear. (The full five-category verbosity system is
  condensed here; expand it when `verbosity-control` is ported.)
- ⛔ **Where output has a prescribed SHAPE and the preset budgets fewer lines, required elements
  MERGE onto the permitted lines — they are never dropped to fit.** (INV-214 — a preset governs
  form as well as kind.) Join them with `; ` and keep
  every one. The explanatory/required split above decides *what* survives; it says nothing about
  *form*, so a template with fixed lines and a one-line budget would otherwise be resolved by
  guesswork. Any per-line annotation — the setup recap's ` — from your saved preferences` marker,
  for instance — attaches **inline to the value it qualifies** rather than to a line, so collapsing
  lines never costs a marker. A list of names may compress to a count when the names were already
  given in the same session; a count is not a module number, so INV-079 is unaffected.
  Worked example: `../bootcamp-preparation/SKILL.md` → Step 7, whose six-line recap collapses to one
  under `minimal` while still marking all three honored preferences.

## Any-time bootcamper controls

These are available at every point in the bootcamp: onboarding, any module, and graduation. The
bootcamper **invoking** one is not a bootcamp question and must not be treated as a gate — it does
not consume a step, and it never counts as the turn's 👉.

⛔ **That is not license to end the turn on two 👉.** INV-251 governs how many questions *you* ask,
and it is unconditional: whatever the bootcamper raised, the turn still ends on **exactly one** 👉 —
either the re-presented pending question or a single clarifying counter-question, never both (see
the 👉 protocol above).

- **Bootcamp feedback:** whenever the bootcamper says "bootcamp feedback", "I have feedback",
  "report an issue", or similar, run the feedback workflow in `feedback.md` and append the entry
  to `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`. The workflow opens with a pinned
  **BOOTCAMP FEEDBACK** entry banner and closes with a pinned **FEEDBACK SAVED — BACK TO THE
  BOOTCAMP** exit banner (a statement) before the pending 👉 question resumes, so feedback mode is
  visually distinct from the bootcamp. Then return them to exactly where they left off. Feedback
  is saved locally only, never submitted externally unless they explicitly ask. (The plugin's
  `userPromptSubmitted` hook surfaces this automatically during a bootcamp.)
- **Make a note:** whenever the bootcamper says "make a note", "note to self", "jot this down",
  "remind me", "don't let me forget", "add a to-do", "for my notes", or invokes
  `the bootcamp note workflow`, run the note workflow in `notes.md` and append the entry to
  `docs/bootcamp_notes.md`. The workflow opens with a pinned 📌 **BOOTCAMP NOTE** entry banner
  and closes with a pinned 📌 **NOTE SAVED — BACK TO THE BOOTCAMP** exit banner (a statement)
  before the pending 👉 question resumes (INV-254, INV-255). Notes are folded into the recap at
  graduation and appear in `docs/bootcamp_recap.pdf`. (The plugin's `userPromptSubmitted` hook
  surfaces this automatically during a bootcamp.)
  - ⛔ **A note is the bootcamper's own thought, not a report about the plugin.** It is never
    routed, never triaged, and never sent anywhere — there is no upstream offer, and
    `submit_feedback` is unreachable from it. When a message is *both* ("make a note that the
    bootcamp is broken"), it is **feedback**: naming the bootcamp as the thing at fault makes it
    an attributed defect report, and routing it to notes would bury it in a private keepsake.
  - ⛔ **Do not ask what they want to note when they already said it.** "Remind me to check the
    truth-set counts" *is* the note (INV-006).
- **Change verbosity:** whenever they ask for more or less detail, update the `verbosity` key in
  `config/bootcamp_preferences.yaml`, confirm the new setting in one sentence, and continue.
- **Repeat the question:** if they ask to hear the current question again ("repeat that", "what
  was the question"), re-present the current pending 👉 question verbatim. Do not invent a new
  one, and do not advance.
- **A host control the bootcamper raises — in any form:** whether they **ask about** auto mode,
  auto-accept edits, permission mode, plan mode, fast mode, background tasks, `/compact`, `/loop` or
  any other setting belonging to their GitHub Copilot session rather than to the bootcamp, **or tell you
  that a prompt for one appeared over the bootcamp**, answer in **one sentence** — it is their
  session setting, the bootcamp neither needs nor recommends a value — and then re-present the
  pending 👉 question verbatim (see below). Do not turn it into a gate, do not offer to change it for
  them, and do **not** claim the bootcamp can suppress or override a host control: the plugin ships
  skills, hooks and commands, none of which reach their interface. **Do not name a dismissal
  affordance either** — not "Don't show again", not any other — because directing them to a control
  that silences a host prompt is directing them to operate a second GitHub Copilot-interface control. The
  bootcamp asks them to operate exactly one, the module-start model/effort switch, and never this
  one (INV-247).
- **Ask-once:** ask each question only once. Do not re-ask a question the bootcamper already
  answered unless they request the repeat.
  - **A pending, *unanswered* question is different — re-present it verbatim.** After any
    interruption that left a 👉 question hanging — a compaction, a session boundary, the feedback
    detour, a host-rendered prompt from their GitHub Copilot interface appearing over the bootcamp, or the
    bootcamper going off on a tangent and coming back — re-present that exact question rather than
    skipping it or inventing a new one. This is **not** a re-ask: ask-once protects the bootcamper
    from answering the same thing twice, and an unanswered question has no answer to protect.
    Skipping it is the real violation, because it advances on an answer nobody gave (INV-007).
    `feedback.md` Step 4 mandates this for the feedback detour specifically; the same rule applies
    to every other interruption.

    ⚠️ **The host-rendered case is the one you may never see.** A prompt the bootcamper's GitHub Copilot
    interface draws over the bootcamp is its UI, not a turn in this conversation — if they dismiss
    it, nothing about it reaches you. So this recovery fires on the evidence you actually get: they
    mention it, or they answer something that does not fit the pending question. Treat either as an
    interruption and re-present, rather than reading the mismatch as their answer.

## Module start banners and transitions

- **Never show a module number to the bootcamper (INV-079).** In *every* bootcamper-facing line — the module-start banner, the journey map, transition questions, and especially casual acknowledgments such as "Great, moving on to …" — refer to a module by its **name** ("Discover the Business Problem"), never its number ("Module 1"). Module numbers are internal only (skill directory names, prerequisites, section headings, `config/*` keys) and MUST NOT appear in anything the bootcamper reads. When acknowledging a transition, use the next module's **name** — the same name shown in the journey map and the "…next module: {name}?" question.
- At every module start, BEFORE any module work: read progress, then show the module start
  banner, a journey map (the **selected** modules — from `selected_modules` in
  `config/bootcamp_preferences.yaml` — marked by position relative to `current_module`: ✅ for
  modules already experienced, i.e. those before `current_module` in the list, including
  apparatus-exempt Bootcamp preparation (never in `modules_completed`) and Module 0 (which, when it
  runs, IS recorded in `modules_completed` — INV-092);
  🔄 for the current module; ⬜ for upcoming), before/after
  framing, and a brief numbered step overview. Never skip these - they orient the bootcamper.
- **Module selection drives the journey map.** The bootcamp is a sequence of named modules chosen
  in the **Bootcamp preparation** module (`../bootcamp-preparation/SKILL.md`): **Core** includes
  every module in order; **Customized** includes the required modules plus whichever optional
  modules the bootcamper chose. Required modules always run; a deselected optional module is a
  requested skip (INV-014). The journey map shows exactly the selected modules, in order, by name —
  not a fixed 1–7 range.
- **Bootcamp preparation and Module 0 are lightweight setup/preamble modules.** The Bootcamp
  preparation module (setup + module selection, always first) and the optional entity-resolution
  concepts primer (`../module-00-entity-resolution-concepts/SKILL.md`, run **only when selected** —
  its old skip/keep gate is retired; inclusion is driven by the Bootcamp preparation selection,
  INV-078) do NOT run the module-start apparatus above (no journey map, no before/after, no step
  overview, no bootcamper-facing end-of-module summary). Keep them lightweight. When Module 0 runs it
  presents only its ENTITY RESOLUTION CONCEPTS banner, the MCP-sourced description, and its explore
  gate. **Recap capture differs between the two:** Bootcamp preparation is fully exempt and is never
  added to `modules_completed`; Module 0, when it runs, DOES append its own name-based recap section
  and is added to `modules_completed` (INV-092), so it appears in the recap and is reconciled at
  graduation (INV-085).
- **Estimated time to complete (INV-096).** After the step overview and before the model/effort
  prompt, add a short, honest, range-based estimate of how long the module will take — e.g.
  "⏱️ Roughly 15-30 minutes, depending on download/install speed." Always caveat that it varies
  with workstation power, business-scenario complexity, data volume, and how much must be
  downloaded/installed. When a meaningful estimate is not possible for a module, say so plainly
  ("hard to estimate for this module") rather than inventing a number; keep it honest and
  range-based, never a single precise figure. It is explanatory output: suppress it entirely under
  the `minimal` verbosity preset and keep it to one line under `concise` (INV-011/INV-012). This
  applies only to the numbered content modules that run this apparatus — the apparatus-exempt setup
  modules (Bootcamp preparation, Module 0) show no estimate.
- **Best-value model/effort prompt.** After the step overview, surface this stage's recommended
  model + effort.

  ⛔ **This is the ONLY GitHub Copilot-interface control the bootcamp asks the bootcamper to operate
  (INV-247).** It is an exception, not a precedent: no other session- or host-level setting — auto
  mode, auto-accept edits, permission mode, plan mode, fast mode, background tasks, `/compact`,
  `/loop` — is ever offered as a bootcamp question, and a new nudge in that shape must not be added
  here or anywhere else. Read the closed-question-set rule in the 👉 protocol before adding one. This
  limit is stated here because *this* section is what creates the expectation: a bootcamper who has
  just been asked to set `/model` and `/effort` for this module has no way to tell an unsanctioned
  interface question from bootcamp content.

  Like the step overview and the time estimate, this is module-start apparatus, so
  the apparatus-exempt setup modules (Bootcamp preparation, Module 0) do not present it (INV-063
  clarification). **Adapt the wording to the GitHub Copilot interface in use** (INV-098): on the **GitHub Copilot
  Code CLI** present the exact `/model` and `/effort` commands; in **GitHub Copilot Desktop, the GitHub Copilot web
  app, or a GitHub Copilot IDE extension** — or when the interface is unknown — phrase it by intent, naming
  the recommended model and reasoning-effort level and directing the bootcamper to that interface's
  model/effort controls, without hardcoding a UI label that may drift.

  ⛔ **Name the interface. "The GitHub Copilot app" is retired vocabulary (INV-158).** This plugin is a
  GitHub Copilot plugin on every one of those interfaces — GitHub Copilot Desktop runs GitHub Copilot too — so
  that phrase left the bootcamper guessing which controls were meant, and "GitHub Copilot" on its own
  does not distinguish the terminal from the desktop application. Say **GitHub Copilot CLI** for the
  terminal and **GitHub Copilot Desktop** for the desktop application.

  ⛔ **This behavior is unconditional — there is no preference to read and no mode to choose
  (INV-137).** The bootcamp is never asked how it wants model guidance handled, and there is no
  `model_guidance` key.

  ⛔ (INV-138) **For every dial whose current value can be determined, compare the recommendation
  against what the bootcamper is running right now — not against the previous stage's
  recommendation.** A dial that cannot be determined is the one exception, and the proxy at the end
  of this paragraph is its rule. You are told which model you are running, so read the
  model side from that; for effort, use the value in force when you can determine it. **Resolve
  "cannot be determined" PER DIAL, not for the setting as a whole** — model and effort are separate
  dials (INV-137), and in a live session they routinely sit in different epistemic states at the
  same moment: the model is knowable to the assistant, while the reasoning effort is **not exposed
  by default**. So compare each dial on its own evidence: a determinable
  model is compared **directly** even when effort is not, and vice versa. **Only for a dial whose
  current value cannot be determined**, and has never been determined in this conversation, use the
  **proxy**: compare this stage's recommended value for that dial against the recommended value for
  it in the stage just completed (that stage's row in the table below, INV-138's "previous stage's
  row"), and ask that dial's half only when the two differ; when they are the same, treat that dial
  as matching.
  ⛔ (INV-138) **The proxy is the only sanctioned recommendation-to-recommendation comparison.** It
  exists because such a dial has no current value to compare, and it is the previous-stage fallback
  the rest of this section refers to. On the GitHub Copilot CLI before any `/effort` has been run, it is
  how the effort dial is decided: Discover the Business Problem (medium) to SDK setup (high) differs,
  so the effort half is asked.

  ⛔ **"Effort is not exposed by default" is not "effort can never be read" — and the switch flow
  below manufactures the evidence.** On the **GitHub Copilot CLI** an `/effort` invocation reports the
  resulting level in the transcript, and the flow below asks the bootcamper to run exactly that
  command and then gates on "👉 Are you done modifying the model and effort?". So the moment an
  `/effort` result is in this conversation, the effort dial **is** determinable, and the
  previous-stage fallback MUST NOT be used for it — treating it as unreadable anyway is the same
  failure this clause already forbids for the model. Read the most recent such value, not the
  earliest — and compare it against the stage's recommendation, never against the previous stage's
  recommendation. Observed on a dry run, 2026-08-13: the bootcamper ran `/effort` at the SDK setup
  nudge and the transcript reported `xhigh`, which made the dial determinable from that point on;
  every later stage nevertheless fell back as though it were unreadable.
  On **GitHub Copilot Desktop, the GitHub Copilot web app or an IDE extension** there is no such
  command, so the dial may genuinely stay undeterminable there — both paths are live, and which one
  applies depends on the interface and on whether the bootcamper has used it.
  ⛔ Applying the previous-stage row to a dial that *was* determinable is the failure this clause
  exists to prevent: a bootcamper demonstrably on Opus 5.5 would be compared against the previous
  stage's recommended Sonnet 5.5, found "unchanged", and never offered the switch — silently defeating
  the purpose of the invariant this superseded. Comparing recommendation-to-recommendation asks a
  bootcamper already on Opus 5.5 at high effort "would you like to switch to Opus 5.5 at high effort?" —
  a question whose answer changes nothing, which is exactly what INV-006 and INV-012 forbid. Running
  one model for the whole bootcamp is a supported choice, so this is the common case, not an edge
  case.

  ⛔ **One dial is exempt from the comparison before it starts: an effort setting ABOVE everything
  the table ever recommends.** The table's highest effort is `high`; the CLI dial also offers `xhigh`
  and `max`. A bootcamper who has chosen one of those sits above **every remaining row**, so the
  step-down clause below would fire at every module for the rest of the bootcamp — twelve questions
  proposing a change they already made deliberately, none of which they can make stop except by
  downgrading. Treat the recommendation as **satisfied**: give the one-line statement (the "matches"
  case below), name the stage's recommended effort, and say plainly that running higher is fine. Ask
  **nothing**. A deliberate over-provision is not a mismatch to correct, and re-offering it every
  module is the "pointless switch? every module" outcome INV-006 and INV-012 forbid.

  ⚠️ **This is narrower than it may look, and deliberately so.** It applies only *above the whole
  table*, never to a step down **within** it — a bootcamper on Opus 5.5 / high entering a Sonnet 5.5 /
  medium stage is still asked, both dials, exactly as today. Step-down questions inside the table
  remain symmetric with step-ups by maintainer decision (2026-07-26, recorded in
  `../../docs/model-selection.md`); what this carve-out removes is only the case that **cannot be
  resolved by answering it**.

  The **model** dial has the same case today: **Fable 5.1 sits above the table's top row, Opus 5.5**,
  so a bootcamper running Fable 5.1 is above every row on the model dial, and the exemption applies
  there in the same terms. The model half is **satisfied**, not mismatched: at every stage they get
  the one-line statement, naming the stage's recommended model and saying that running higher is
  fine, and **never** a model question. Their effort is still compared on its own evidence. If a
  stronger model ships and this table lags it, the same terms apply to it. Opus 5.5 is not above the
  table, because it *is* the top row: a bootcamper on Opus 5.5 entering a Sonnet 5.5 stage is asked,
  as a step down within the table (INV-139).

  Two cases, decided only by that comparison:

  - **The recommendation differs from the current setting** — in **either** direction. A step down
    asks just as a step up does: the choice is the bootcamper's both ways. End the turn with a
    **single** 👉 yes/no question offering the switch, and do NOT also show Step 1 this turn
    (exactly one 👉 per turn — INV-251; INV-008/INV-009 govern each question's clarity, not the count).

    **Name only the dial that differs.** Model and effort are **separate dials**: a bootcamper on
    Opus 5.5 at medium effort entering a stage recommending Opus 5.5 at high effort is asked to change
    the effort only, never told to re-set the model they are already on.

    ⛔ **That rule covers the whole sentence, including the answer hint** — `{dial}` below resolves
    to "model", "effort", or "model and effort", matching whatever the stem names. An effort-only
    question that ends "reply no to keep your current **model**" tells the bootcamper what declining
    does to a dial it is not touching, and the pinning rule (INV-056) means the guide cannot quietly
    correct it at runtime. This is the common case, not an edge one: a bootcamper who stays on Opus 5.5
    through the conversational stages meets an **effort-only** step-up at SDK setup, the first time
    the nudge has anything to say to them at all.

    On the **GitHub Copilot CLI**, pin the switch question verbatim, substituting only the bracketed
    values — the stage's commands, just the one dial when only one differs, and `{dial}` to match:

    > 👉 **Would you like to switch to `/model {model}` + `/effort {effort}` for {this module | graduation}?** (Recommended for best value; reply no to keep your current {dial}.)

    In **GitHub Copilot Desktop, the GitHub Copilot web app, or a GitHub Copilot IDE extension** (or an unknown interface),
    pin the intent-based equivalent — name the stage's recommended model and effort, and do NOT
    present CLI commands as the only instruction:

    > 👉 **Would you like to switch to {Model} at {effort} reasoning effort for {this module | graduation}?** (Recommended for best value; set it with the model and effort controls in {GitHub Copilot Desktop | the GitHub Copilot web app | your GitHub Copilot IDE extension}; reply no to keep your current {dial}.)

    Substitute the one interface the bootcamper is actually on. When the interface cannot be
    determined, say "in your GitHub Copilot interface" — vague only where the plugin genuinely does not
    know, never as a shorthand for an interface it does know (INV-158).

    ⛔ **When the recommendation sits *below* the current setting, say so in the question itself.**
    Add one clause naming it as a step down, stating that the recommendation is about cost rather
    than capability and that staying put costs them nothing — e.g. "this is a step down from your
    current {current}; it is a cost saving, not a capability the module needs, so staying put is
    fine." Without it the bootcamper is being asked to accept a worse experience for no stated
    reason. It never reads as advice to downgrade. (An effort above the whole table never reaches
    this clause, and neither does a model above it such as Fable 5.1 — see the exemption above; it is
    a statement, not a question.)

    This switch turn ends at the 👉. **On yes, read what the dial is actually set to before you
    compose the reply** (INV-236). The question just handed the bootcamper a command, so many will
    run it in the same turn as their yes — that is the natural response to being shown a command,
    not an edge case. Three shapes, decided by the live setting rather than by the yes alone:

    1. **The dial is not yet set** — the ordinary case, unchanged. Open the reply turn with a
       one-line statement telling the bootcamper how to make the change (run the `/model`/`/effort`
       commands in the GitHub Copilot CLI, or use the model and reasoning-effort controls in GitHub Copilot
       Desktop / the GitHub Copilot web app / their GitHub Copilot IDE extension — naming only the dial that is
       moving), then end the turn on this pinned confirmation gate (its question verbatim,
       INV-056/INV-069 — only the answer hint adapts to the interface) — do NOT show Step 1 yet:

       > 👉 **Are you done modifying the model and effort?** (Reply yes once you've set your model and effort; reply no if you need more time.)

       Step 1 comes on the turn **after** the bootcamper confirms. If they reply no / "not yet",
       acknowledge and wait for their go-ahead, then present Step 1 — do not re-ask this gate
       (ask-once, INV-006).

    2. **The dial is already at the recommended value** — they ran it themselves.
       **Acknowledge it instead of instructing it** — "You're on `/effort medium` already: that's
       this module's recommendation." — and present Step 1 **in the same turn**, with **no**
       confirmation gate. Nothing is left to confirm, so asking is the pointless question INV-006
       and INV-012 forbid, and this is the case where INV-064's single-turn continuation is
       genuinely correct.

    3. **The dial is already at a different value** — state what is in force and leave it there:
       "You're on `/effort xhigh`; this module recommends `medium`, and running higher is fine — it
       simply costs more, nothing else." Then present Step 1 in the same turn, no gate. ⛔ **Never
       re-instruct the recommended command once the bootcamper has set a different value.** They
       answered the question with an action, and the table is a recommended floor for value, not a
       ceiling — repeating it names a value they just deliberately rejected. This reuses the
       above-the-table wording on purpose ("running higher is fine", "simply costs more"), so the
       two statements of the same idea cannot drift apart.

    ⛔ **Shapes 2 and 3 skip the confirmation gate; shape 1 keeps it.** The gate exists to give the
    bootcamper a window in which to run the commands — a bootcamper who has already run them does
    not need one, and gating anyway asks a question the transcript has answered.

    ⚠️ **Interface-aware, like the question itself.** In GitHub Copilot Desktop, the GitHub Copilot web app or a
    GitHub Copilot IDE extension, shapes 2 and 3 name the **setting** rather than a command — "you're
    already on {Model} at {effort} reasoning effort" — since those bootcampers can change it before
    replying just as readily (INV-158).

    On **no** to the switch, acknowledge and present Step 1 the same reply
    turn, ending on **the next single 👉 question**. That is Step 1's own 👉 when it has one — and
    when Step 1 is **non-yielding**, it is the 👉 of the next step that asks, with the intervening
    steps executed in the same turn (see the 👉 protocol). Module 1's Step 1 is exactly this case:
    a privacy reminder that asks nothing, so the turn ends on Step 2's question.
  - **The recommendation matches what they are already running** → a brief one-line statement; no
    question, so the bootcamp never asks a pointless "switch?" every module (INV-012). The statement
    names the recommended model and effort as **separate dials**, notes either can be
    changed at any time and applies from the next message, and — when the recommendation sits
    *below* the current setting — says so explicitly with why the carve-out may not apply, so it
    never reads as advice to downgrade.

  ⛔ **You never change the session yourself — only the bootcamper can.** That is why the switch is
  offered as a question rather than performed. The "Are you done modifying the model and effort?"
  gate follows a **yes that still needs one** — shape 1 above — and nothing else: never after a
  decline, never when the recommendation already matched, and never in shapes 2 and 3, where the dial
  is already set and the gate would ask what the transcript has answered.

  Switching is always optional — running one model for everything (Opus 5.5) stays valid. Per-stage
  recommendation — **this table is the authoritative copy** (the one in
  `../../docs/model-selection.md` is derived from it; change this one first). Model names, IDs, and
  the values below are point-in-time and go stale when a new model ships; `docs/model-selection.md`
  carries the dated verification note, and `tests/test_model_guidance_sync.py` fails if the two
  tables drift or if any superseded model name survives (INV-114):

  **One row per stage, in the order the bootcamp runs them** — so the next stage's recommendation
  can be read off directly, and so no stage is ever missing a value to compare against. Each row
  names exactly **one** model and **one** effort: a conditional recommendation cannot be pinned into
  a verbatim question (INV-056) and gives the comparison above two answers.

  | Stage | Recommended | CLI commands |
  |---|---|---|
  | Onboarding | Sonnet 5.5, medium effort | `/model sonnet` · `/effort medium` |
  | Bootcamp preparation | Sonnet 5.5, medium effort | `/model sonnet` · `/effort medium` |
  | Entity Resolution Concepts | Sonnet 5.5, medium effort | `/model sonnet` · `/effort medium` |
  | Discover the Business Problem | Sonnet 5.5, medium effort | `/model sonnet` · `/effort medium` |
  | SDK setup | Opus 5.5, high effort | `/model opus` · `/effort high` |
  | System verification | Sonnet 5.5, high effort | `/model sonnet` · `/effort high` |
  | Truth Set visualization | Opus 5.5, high effort | `/model opus` · `/effort high` |
  | Data collection | Sonnet 5.5, medium effort | `/model sonnet` · `/effort medium` |
  | Data Quality, Mapping, and Transformation | Opus 5.5, high effort | `/model opus` · `/effort high` |
  | Data processing | Opus 5.5, high effort | `/model opus` · `/effort high` |
  | Query, Visualize and Discover | Opus 5.5, high effort | `/model opus` · `/effort high` |
  | Bootcamp graduation | Opus 5.5, high effort | `/model opus` · `/effort high` |

  The **Recommended** column is interface-neutral. In GitHub Copilot Desktop, the GitHub Copilot web app, or a GitHub Copilot
  IDE extension, set the same model and reasoning effort using that interface's model/effort controls;
  the **CLI commands** column is the GitHub Copilot CLI equivalent (INV-098).

  ⚠️ **These effort values are a recommended floor for value, not a ceiling.** The table never goes
  above `high`, and the dial goes further (`xhigh`, `max`). Running above the table is **in policy**
  and simply costs more — it is not an over-setting to be corrected, which is why an effort above
  every row is exempt from the comparison above. `high` was chosen as the top row because there is no
  evidence the modules need more, not because more is disallowed (see
  `../../docs/model-selection.md` → considered and rejected).

  From Data Quality, Mapping, and Transformation onward the recommendation is **flat** — a
  bootcamper who switches there is asked nothing further for the rest of the bootcamp.

  Onboarding, Bootcamp preparation and Entity Resolution Concepts appear in this table only so the
  nudge always has a value on both sides of the comparison; being apparatus-exempt
  (INV-075/INV-078), those setup stages present no model/effort nudge themselves (see the carve-out
  above).

- Module start banner:

  ```text
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🚀🚀🚀  MODULE: [MODULE NAME IN CAPS]  🚀🚀🚀
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

- After an affirmative module-transition ("Ready to move on to the next module?"), immediately produce the
  banner + journey map + before/after + step overview + estimated time to complete + best-value
  model/effort prompt. When that
  prompt is a 👉 switch question (the recommendation differs from what they are running), the turn
  ends there. On the reply:
  **no** produces Step 1 the same (reply) turn; **yes** produces the one-line run-commands
  statement and ends on the pinned "👉 Are you done modifying the model and effort?" gate, with
  Step 1 on the turn after the bootcamper confirms. When the recommendation already matches (no
  switch question), continue straight into Step 1 the same turn. In every one of those cases the
  turn ends on **the next single 👉 question** — Step 1's own if it has one, otherwise the next
  asking step's, with the non-yielding steps in between executed in that same turn. Never reply
  with just "." or fewer than 50 characters.

## Closing questions

- YOU own the closing 👉 question at the end of each yielding turn. The plugin's `Stop` hook is
  a safety net that fires only if you forget - do not rely on it.
