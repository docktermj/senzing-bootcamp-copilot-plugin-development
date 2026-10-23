# Module 1 Copilot Turn Protocol

This Copilot host adaptation makes the Module 1 turn boundaries explicit. Follow it together
with `../skills/bootcamp-onboarding/ground-rules.md` and the numbered phase instructions; it
does not change the parent curriculum or its pinned questions.

## Module start

Before presenting any Module 1 step, read both `config/bootcamp_progress.json` and
`config/bootcamp_preferences.yaml`. Build the journey map from the exact ordered
`selected_modules` value in the preferences file; do not assume the full Core path when a
selection is present. Then deliver the complete module start apparatus in this order:

1. Name-only module start banner.
2. Journey map showing the selected modules, in order, by name, with the current module marked.
3. Before/after framing.
4. Brief numbered overview of this module's steps.
5. Honest range-based time estimate that explicitly says it varies with workstation power,
   business-scenario complexity, data volume, and required downloads or installation.
6. Best-value model and effort recommendation, compared per the ground rules.

Do not omit an item or replace this with only a banner or a generic introduction. If a model or
effort switch is required, end the turn with only that prescribed question and wait. Otherwise,
continue to the first applicable numbered step in this same response.

## Senzing claims

Before composing a response that contains a Senzing-specific claim, obtain the supporting
information from an applicable Senzing MCP tool in that same turn. A result from an earlier turn
does not ground a new claim. This applies to explanations, summaries, recaps, and generated
documents as well as direct answers. If a lookup returns no relevant support, do not fill the
gap from memory; state only what the tool did establish or say that the published material did
not cover the question.

Before each MCP call, satisfy every required argument in that tool's live schema. In particular,
`get_sample_data` requires `dataset`: use `dataset='list'` to discover available datasets, or
the exact dataset name to retrieve one. Never issue an incomplete call; after a tool error,
retry with valid arguments or use another documented source before making a claim.

## Yielding turns

For every step that asks a pinned 👉 question:

- Put the acknowledgment, explanation, sourced material, and answer options before the question.
- Render the pinned question verbatim exactly once. It is the final user-visible content in the
  turn; do not repeat it, paraphrase it, or add a post-question note, summary, or invitation.
- Complete any silent checkpoint writes after rendering it, then wait for the bootcamper.

If a host continuation is needed, use the one pending question specified by the current skill
step, exactly once. Never add a second closing question or repeat one already rendered.
Do not narrate that you are waiting, announce that a question will not be repeated, or add any
other text after the question and its answer options. The tool call itself is the wait.

## Stakeholder summary timing

Do not create or update `docs/stakeholder_summary_module1.md` before the bootcamper confirms
Step 15. After confirmation, execute Step 16 once, then continue the non-yielding completion
work and end at the single Module 2 transition question specified by Step 17.
