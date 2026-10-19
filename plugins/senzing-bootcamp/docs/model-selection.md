# Model & effort selection (maintainer notes)

This is a maintainer/developer reference — it does not ship as bootcamper-facing
content. It records which plugin components can carry a model/effort override,
the scope of those overrides, and a best-value model evaluation for each skill,
so the analysis is not re-investigated.

**The headline:** a skill's `model:`/`effort:` override is **turn-scoped**, so
for this interactive, multi-turn plugin the **session** model/effort — not
per-skill frontmatter — is the lever that actually governs the experience.

## Which components can carry a model/effort override

A model/effort override only means anything for components that actually invoke
GitHub Copilot. `type: command` hooks and the scripts they run are deterministic
programs and never "run under a model."

| Component | Model? | Effort? | How / scope |
|---|:---:|:---:|---|
| Skills (`SKILL.md` frontmatter) | ✅ | ✅ | `model:` + `effort:` (`low`/`medium`/`high`/`xhigh`/`max`). **Turn-scoped.** |
| Slash commands (`.md` frontmatter) | ✅ | ❌ | `model:`; no effort field |
| Subagents (`agents/*.md`) | ✅ | ✅ | `model:` (`inherit` default) + `effort:`; persists for the subagent's whole run |
| Command hooks (`type: command`) | ❌ | ❌ | Deterministic program; only reads session effort via `no portable effort setting` |
| Prompt hooks (`type: prompt`) | ✅ | ❌ | `model:` in hook config |
| Agent hooks (`type: agent`) | ➖ | ➖ | Inherits the spawned subagent's `model:`/`effort:` |
| Scripts (run by hooks/commands) | ❌ | ❌ | Not model-executed |

## Skill overrides are turn-scoped (the load-bearing constraint)

From the GitHub Copilot skills docs:

> The override applies for the rest of the current turn and is not saved to
> settings; the session model resumes on your next prompt.

The bootcamp skills are **interactive and multi-turn** — every step ends by
yielding to the bootcamper after one 👉 question, so each following step arrives
as a *new user prompt* and the override **resets** to the session model/effort. A
`model:` on a module skill therefore governs only the module-start turn, not the
whole module.

Consequences:

- The reliable lever for the bootcamp is the **session** model/effort.
- Per-skill `model:` frontmatter on an interactive skill gives a false sense of
  cross-turn control — avoid it.
- Sustained per-skill model control exists only via `context: fork` (the skill
  runs in a subagent that holds its own `model:`/`effort:` for its whole run) —
  but that moves the work into an isolated subagent, which is wrong for skills
  that must converse with the bootcamper turn-by-turn.

## Model tiers (for "best value")

Approximate positioning (verify current pricing/availability before relying on
the numbers — see the staleness note below):

| Model | Tier | ~Price (in/out per MTok) | Adaptive thinking | Notes |
|---|---|---|:---:|---|
| Fable 5.1 (`copilot-fable-5-1`) | Top | ~$10 / ~$50 | Always on | Most capable; for demanding reasoning and long-horizon agentic work; slower; ~2.5× Opus cost |
| Opus 5.5 (`copilot-opus-5-5`) | High | ~$4 / ~$20 | Always on | Long-running agentic coding and knowledge work; the general-purpose default |
| Sonnet 5.5 (`copilot-sonnet-5-5`) | Mid | ~$2 / ~$10 | Yes | Speed/cost/capability sweet spot |
| Haiku 4.5 (`copilot-haiku-4-5`) | Budget | ~$1 / ~$5 | **No** | Fastest; no adaptive thinking |

> **Point-in-time data — re-verify before relying on it.** Model names, IDs, and
> prices above are a snapshot, **last verified 2026-10-01** against
> `platform.copilot.com/docs/en/about-copilot/models/overview`. They go stale whenever
> a new model ships. That happened between the previous check (2026-07-25) and
> this one: Fable 5.1, Opus 5.5 and Sonnet 5.5 superseded Fable 5 (`copilot-fable-5`),
> Opus 5 (`copilot-opus-5`) and Sonnet 5 (`copilot-sonnet-5`), which that page now
> lists as legacy, and the per-stage table lagged them. Prices moved with them,
> against the figures recorded at the 2026-07-25 check (not re-verified today):
> Opus 5.5 is cheaper than Opus 5 (~$5 / ~$25, the price Opus 5 had inherited from
> Opus 4.8), and Sonnet 5.5 cheaper than Sonnet 5 (~$3 / ~$15), while Fable 5.1
> lists the price recorded for Fable 5. Re-verify names, IDs, and pricing against current GitHub Copilot
> documentation rather than trusting this table. This note is the only place in
> the shipped plugin that may name a superseded model, and only to explain the
> supersession; `tests/test_model_guidance_sync.py` exempts this block and nothing
> else in the file.

For a protocol-heavy (⛔ gates, INV-056 pinned wording, one-👉-per-turn),
MCP-first teaching plugin, Haiku's lack of adaptive thinking is a real risk of
gate/format slips, and Fable's premium buys little the workloads here need.

## Per-skill best-value evaluation

Best value = the capability the workload needs, at the lowest tier that meets it.

**Re-assessed 2026-07-26.** The original 2026-07-16 evaluation was never re-read against the modules
as they later became, and two rows had gone stale under them. Rows whose value changed are marked
**↑**.

| Skill | Workload | Best value | Rationale |
|---|---|:---:|---|
| `bootcamp-onboarding` | Gated preface, exact-wording gates, preference capture | Sonnet 5.5, medium | Protocol adherence needs adaptive thinking + strong instruction-following; no heavy code → Opus overkill, Haiku risky |
| `bootcamp-preparation` | Setup preferences: verbosity, language, Core-vs-Customized path, module selection | Sonnet 5.5, medium | Same workload class as onboarding — pinned questions and recorded answers, no code. The choices steer every later module, so instruction-following matters more than raw capability |
| `module-00-entity-resolution-concepts` | Concepts teaching, Q&A, knowledge check | Sonnet 5.5, medium | Conversational teaching, no code |
| `module-01-business-problem` | Discovery conversation, document the problem | Sonnet 5.5, medium | Conversation-led, light technical |
| `module-02-sdk-setup` | Cross-platform install, license/engine/DB config, build-from-source recovery | Opus 5.5, high | Largest skill, most error-prone, platform-specific; install/config errors are high-cost |
| `module-03-system-verification` | Verify end-to-end, write and run the first real SDK code, report | Sonnet 5.5, **high** ↑ | Not "run / check / report": it writes the first working SDK code against the installed engine, and the 2026-07-26 export-flag defect was filed against this module. Sonnet fits the volume; the reasoning load justifies high effort |
| `module-03b-truthset-visualization` | **Build** a visualization server in the chosen language, load Truth Set, visualize | **Opus 5.5, high** ↑ | Rated "mostly run / render" before INV-090 made the module *generate* the server: tab ids and deep-linking (INV-124), script-payload escaping (INV-106), offline vendoring (INV-091), brand tokens (INV-081). The largest code-generation artifact before graduation, and historically the most defect-prone |
| `module-04-data-collection` | Gather sources into `data/raw/` | Sonnet 5.5, medium | Data wrangling + light code; genuinely the lightest technical module |
| `module-05-data-quality-mapping` | Quality scoring + mapping to the Entity Spec via `mapping_workflow` | Opus 5.5, high | Mapping correctness drives resolution quality — the technical crux |
| `module-06-data-processing` | Load mapped data (SDK), validate, redo drain, export | **Opus 5.5, high** ↑ | Was "Sonnet 5.5 (Opus if bespoke load code)" — a conditional the module-start nudge cannot resolve or pin (INV-056). Its failures are the silent kind: export flag families yielding rows with only `ENTITY_ID`, a redo drain that never terminates, the threading cutover |
| `module-07-query-visualize-discover` | Query SDK code, build the results app, discovery, deliverable | **Opus 5.5, high** ↑ | Was the lightest setting in the table, and is where the silent-wrongness defects land: three of the 2026-07-26 self-observed entries plus INV-115's originating incident. Wrong field names render blank instead of raising — the failure mode least tolerant of a speed-tuned setting |
| `graduation` | Recap reconcile, PDF, production project (code/config/docs), report | Opus 5.5, high | Crown-jewel deliverable; production code/config correctness matters most |

Considered and rejected, so they are not re-litigated: **Sonnet 5.5 / high for Truth Set
visualization** (cheaper, and the contract is explicit — but the module generates a complete app in
an unconstrained language; maintainer settled on Opus 5.5 / high, 2026-07-26); **`xhigh` for
graduation** (no evidence `high` is insufficient, and a third value on the dial adds a change point
and a vocabulary the rest of the table does not use); and **flattening the table to reduce prompts**
(the assignment should describe the work — prompt volume is a detection problem, solved by comparing
against the bootcamper's actual setting).

## Module-start commands (the nudge)

`ground-rules.md` → "Module start banners and transitions" surfaces this per-stage recommendation
at the start of each module (and `graduation/SKILL.md` at the graduation banner). Switching is
optional; the session-level model/effort persists for the session (unlike per-skill frontmatter),
and the guide never changes it — only the bootcamper can.

**How it is surfaced is not configurable** (INV-137). The bootcamper is never asked, there is no
`model_guidance` preference, and the behavior depends only on whether the recommendation differs
from **what the bootcamper is currently running** — not from the previous stage's recommendation.
That distinction is the whole point: a bootcamper who runs Opus 5.5 / high throughout (a supported
choice, see below) was previously asked to "switch to Opus 5.5 / high" three times while already on
it. Where a dial's current value cannot be determined, and has never been determined in this
conversation, use the **proxy** — **per dial**, and only while it really cannot be read: compare
this stage's recommended value for that dial against the recommended value for it in the stage just
completed (that stage's row, INV-138's "previous stage's row"), and ask that dial's half only when
the two differ. The proxy is the **only** sanctioned recommendation-to-recommendation comparison; a
dial that can be determined is always compared against what the bootcamper is running. On the CLI
before any `/effort` has been run, Discover the Business Problem (medium) to SDK setup (high)
differs, so the effort half is asked. Reasoning effort is not exposed by default, which is not the
same as unreadable: on the GitHub Copilot CLI an `/effort` invocation reports the resulting level in
the transcript, and the nudge's own switch flow asks the bootcamper to run exactly that command. So
once an `/effort` result is in the conversation the effort dial is determinable, the most recent
such value is the one compared, and the proxy must not be used for it. (On GitHub Copilot Desktop, the web
app and IDE extensions there is no such command, so the dial may genuinely stay undeterminable; both
paths are live.)

| At a module or graduation start | Behavior | Extra turns |
|---|---|---|
| The recommendation **differs** from the current setting — in **either** direction | A single 👉 switch question, its own turn, naming only the dial that differs — **in the answer hint too**, which resolves to "model", "effort", or "model and effort" rather than always saying "model"; on **yes**, the reply reads the dial first (INV-236) — if it is not yet set, a one-line run-commands statement then the pinned "Are you done modifying the model and effort?" gate before the first step; if the bootcamper has already set it (the question names a command, so this is common), the reply states what is in force, skips the gate, and the first step lands the same turn, never re-instructing a value they have already moved past; on **no**, the first step lands the same turn. A recommendation *below* the current setting is flagged as a step down **in the question**, stating it is a cost saving rather than a capability the module needs. | up to 2 |
| The recommendation **matches** what they are already running | A concise one-line statement — model and effort named as separate dials, either changeable at any time from the next message, and a recommendation *below* the current setting flagged explicitly so it never reads as advice to downgrade. | 0 |
| A dial is **above every row** in the table: effort `xhigh` or `max`, or the model Fable 5.1 | Treated as satisfied for that dial: the one-line statement, naming the stage's recommendation and saying that running higher is fine. No question — the step-down clause would otherwise fire at every remaining module, and answering it cannot make it stop. Fable 5.1 sits above the table's top row, Opus 5.5, so a bootcamper on Fable 5.1 gets the statement on the model dial at every stage, never a model question; their effort is still compared on its own evidence. | 0 |

The pause is **symmetric**: downgrades ask exactly as upgrades do (maintainer decision, 2026-07-26,
reaffirmed 2026-10-01). Concretely, a bootcamper on Opus 5.5 entering a Sonnet 5.5 stage is **asked**,
and the question flags it as a step down (INV-139): Opus 5.5 is the table's top row, not above it, so
the above-the-table case does not apply.
Making a step down a statement instead of a question was considered — running heavier than
recommended is never harmful, only more expensive — and rejected: the choice is the bootcamper's in
both directions.

An earlier design made this a three-mode `model_guidance` preference (`advisory` / `off` /
`prompt`) chosen in Bootcamp preparation. That question and preference are **retired**: INV-137
supersedes INV-119 and INV-120 and restores the unconditional INV-063/INV-069 behavior. A stale
`model_guidance` key in an old preferences file is ignored, not honored. The confirmation gate
follows a **yes** to the switch and nothing else.

> **`ground-rules.md` is the authoritative copy of this table; the copy below is derived.**
> `ground-rules.md` is the file the guide actually loads at module start, so the operational values
> must live there — a nudge that first had to fetch this maintainer doc could silently misfire, and
> INV-063 mandates the nudge. Change `ground-rules.md` first, then mirror it here.
>
> The two are not kept in sync by hand: `tests/test_model_guidance_sync.py` asserts they are
> identical row for row, that no superseded model name or ID appears in any shipped or
> user-facing doc, and that this file carries a dated verification note (INV-114). Editing one
> table without the other fails the suite.

The nudge adapts to the GitHub Copilot interface in use (INV-098): the **Recommended** column is
interface-neutral; the **CLI commands** column is the GitHub Copilot CLI equivalent. In GitHub Copilot Desktop,
the GitHub Copilot web app, or a GitHub Copilot IDE extension, the same model and reasoning effort are set via that
interface's model/effort controls rather than the slash commands. Each is named explicitly, because
the retired "the GitHub Copilot app" did not say which controls were meant (INV-158).

**One row per stage, in the order the bootcamp runs them** — so the next stage's recommendation can
be read off directly, and so no stage is ever missing a value to compare against. Each row names
exactly one model and one effort: a conditional cell cannot be pinned into a verbatim question
(INV-056) and gives the comparison two answers.

⚠️ **The effort values are a recommended floor for value, not a ceiling.** The table stops at `high`;
the dial continues to `xhigh` and `max`. Running above the table is in policy and simply costs more.
That matters to the nudge: an effort above **every** row is exempt from the comparison and produces a
statement rather than a question, because otherwise the step-down clause fires at every remaining
module and cannot be resolved by answering it. The exemption is confined to *above the whole table* —
step downs **within** it stay symmetric with step-ups, per the 2026-07-26 decision below.

Every stage the bootcamp can run has **exactly one** row here, including the apparatus-exempt setup
stages that present no nudge themselves — INV-140, so the INV-138 comparison always has a defined
value to compare against.

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

## Recommendation

Because skill overrides reset per prompt, realize the evaluation through the
**session** model — not per-skill frontmatter:

- **Value-optimized (the `README.md` default):** run the session on **Sonnet 5.5**,
  and switch the session up to **Opus 5.5** for the correctness-critical stretches —
  SDK setup, Truth Set visualization, and the whole back half from Data Quality,
  Mapping, and Transformation through graduation, which is flat at Opus 5.5 / high.
  Switch mid-session with `/model copilot-opus-5-5` and back with
  `/model copilot-sonnet-5-5`. **Haiku 4.5** is not recommended for any
  bootcamper-facing skill (protocol risk); **Fable 5.1** is not the value pick here.
- **Simplest (one model, no switching):** run the whole session on
  **Opus 5.5 + `--effort high`**. Zero-friction — one strong model for everything
  — at the cost of over-paying on the lighter conversational modules.

## Optional lever: invoking-turn-only effort

`effort:` frontmatter on the heaviest single-turn skills (`graduation`,
`module-02-sdk-setup`, `module-05-data-quality-mapping`) will bump reasoning on
the turn that *invokes* the skill, then reset like any skill override. It is a
minor, honest tuning knob — if added, it must be understood (and labeled in the
frontmatter's vicinity) as **invoking-turn-only**, not a module-wide setting. It
is intentionally **not** wired today, to avoid implying persistence the mechanism
does not provide.

## Sources

- Skills model/effort scope: `code.copilot.com/docs/en/skills.md` (frontmatter reference).
- Subagents model/effort: `code.copilot.com/docs/en/sub-agents.md`.
- Hooks: `code.copilot.com/docs/en/hooks.md`.
- Model positioning/pricing: `platform.copilot.com/docs/en/about-copilot/models/overview`.
