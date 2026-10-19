# Module 7, Phase 2b: Discover, Part B (step 4d)

Follow the ground rules. `🛑`/`⛔` are internal directives, never render them; signal a stop by
ending the turn on the single 👉 question and waiting. On load, read
`config/bootcamp_progress.json` and check which 4x sub-steps are already checkpointed under
`module_7_query.steps`. Resume from the first incomplete step; do not re-run completed
demonstrations.

Load this file after completing steps 4a–4c in `phase2-discover.md`. When complete, return to
`phase1-query-visualize.md` for the Query Completeness Gate.

**No direct SQL and no fabricated methods (see SKILL.md):** `find_network` and `find_path` are
SDK methods, not MCP tools. Generate the SDK code, sourcing flags and signatures from
`get_sdk_reference` and network/path patterns from `reporting_guide(topic='graph', language='<chosen_language>')`. Never
query `database/G2C.db` tables directly.

## Step 4d: Discover (continued)

### Step 4d: Relationship network exploration

Demonstrate relationship-network exploration using entities identified in step 4a that have
disclosed relationships or shared attributes. This teaches the bootcamper how to explore
connections between entities using `find_network` and `find_path`.

1. **Entity selection:** use entities from step 4a with disclosed relationships or shared
   attributes. State which and why: "I'll use Entities [ID1], [ID2], and [ID3], which have
   disclosed relationships or shared attributes. These give us a connected set of entities to
   explore as a network."
2. **Flag and response-shape lookup:** before generating the `find_network` or `find_path` calls,
   look up available flags **and the response structure** (the narrowing parameter is `filter`,
   not `method`):
   - `get_sdk_reference(topic='flags', filter='find_network')` and
     `get_sdk_reference(topic='response_schemas', filter='find_network')` for network exploration.
   - `get_sdk_reference(topic='flags', filter='find_path')` and
     `get_sdk_reference(topic='response_schemas', filter='find_path')` for path finding.

   ⛔ **Look up the response structure before writing any code that parses the response — never
   infer field names from an example snippet** (INV-115).

   ⚠️ **That lookup reaches inside a link element — and neither the array name nor the
   endpoint names are the ones you would guess.** For each graph method `response_schemas`
   returns **that method's own** outer arrays **and** each link element's own fields
   (re-verified on MCP server 1.32.2, docs indexed 2026-07-29 11:11 UTC, 2026-07-31).
   **The two documents differ in exactly one key — the array you index by.** `find_path`
   returns its edges under **`ENTITY_PATH_LINKS[]`**; `find_network` returns them under
   **`ENTITY_NETWORK_LINKS[]`**. Everything else matches **across the two documents**: both carry
   `ENTITIES[]` and `ENTITY_PATHS[]` with the same sub-fields (`START_ENTITY_ID`, `END_ENTITY_ID`,
   `ENTITIES[]`), and **both link elements carry the same seven fields**, which is what makes the
   array name the one difference a shared parser misses. ⛔ **That is a claim about the two
   DOCUMENTS and nothing more — it does not mean the endpoint convention is uniform.** See the
   within-response trap below, which this sentence would otherwise talk you out of noticing.
   `find_network` returning `ENTITY_PATHS[]` is the sharpest edge of it — seeing "PATH" in a
   network response is not evidence that `ENTITY_PATH_LINKS[]` is there.
   **The matching-info flags are paired, not shared:** `SZ_FIND_PATH_INCLUDE_MATCHING_INFO`
   has `applies_to` of the two `find_path_*` methods, `SZ_FIND_NETWORK_INCLUDE_MATCHING_INFO`
   of the two `find_network_*` methods, and each default composite carries its own. So
   **neither the flags nor the parser can be carried from one of these calls to the other** —
   do it and you get a path whose entity names render while every edge prints
   `(link detail not returned)`, which reads as a path with no relationship detail rather than
   as two wrong names at once (INV-148). Route: `get_sdk_reference(topic='response_schemas',
   filter='find_path')` and the same with `filter='find_network'` (server 1.32.2, docs indexed
   2026-07-29 11:11 UTC, verified 2026-07-31). Dump one raw link element and read
   its keys anyway before writing the parser. Do **not** assume a link's two
   endpoints use the `ENTITY_ID` / `RELATED_ENTITY_ID` pairing that related-entity records use:
   two sessions found both endpoints blank under those names while `MATCH_KEY` rendered fine, and
   a live dump on SDK 4.3.3 found them under **`MIN_ENTITY_ID` / `MAX_ENTITY_ID`** (normalized
   low-to-high) — which is what the schema now documents too. Those keys are recorded in
   `../module-03b-truthset-visualization/visualization-api-reference.md` → "MCP-confirmed response
   paths"; they were dump-only when first recorded, so they are MCP-confirmed names rather than an
   unverified caution. **Run the lookup and dump anyway** — its coverage grows, this entry is proof of
   that, and the dumped element remains the authority for what your installation returns (INV-080).
   An empty or shallow result is still coverage, not a failed call — do not retry it (INV-149).

   ⛔ **The second wrong endpoint guess, and the worse one: ONE `find_network` response uses two
   different endpoint conventions.**

   | Array in that one response | Endpoint keys |
   |---|---|
   | `ENTITY_PATHS[]` | `START_ENTITY_ID` / `END_ENTITY_ID` — **directed** |
   | `ENTITY_NETWORK_LINKS[]` | `MIN_ENTITY_ID` / `MAX_ENTITY_ID` — **undirected**, normalized low-to-high |

   (Re-verified on MCP server 1.32.9, 2026-08-17, via `get_sdk_reference(topic='response_schemas',
   filter='find_network', language='java')`.)

   ⚠️ **`START_`/`END_` is the natural wrong guess precisely BECAUSE the sibling array in the same
   response uses it** — unlike the `ENTITY_ID`/`RELATED_ENTITY_ID` guess above, which comes from a
   different call's shape. The reason for the split is what makes it stick: **a link is an unordered
   pair, a path is directed**, so a link normalizes its endpoints and a path preserves its
   direction. Read the endpoint names off a link element, never off a path.

   Observed cost: all **38 edges** of a corporate hierarchy printed `null -> null`, with no error —
   and a silently empty edge list is indistinguishable from *"this data has no relationships"*, which
   is the wrong conclusion to hand an analyst in the capability the fraud-detection pattern leans on
   hardest.

   ⛔ (INV-080) **Per-record source values come from the entity call itself, with the right flag
   OR-ed in.** `RECORDS[].JSON_DATA` needs `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA`, which
   `SZ_ENTITY_DEFAULT_FLAGS` omits. Without it those paths render blank for every record, and the fix
   is the flag, not a switch to `get_record`. For the mapped attributes instead, use
   `RECORDS[].FEATURES.<TYPE>[].ATTRIBUTES.*` with `SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS`. The
   two routes, their paths and the flags' `applies_to` are in the same reference section.

   ⛔ **If some fields of a row populate and others come back blank, suspect the blank ones' names
   — not the data.** A half-populated row reads as a real result precisely because part of it
   worked, which makes it more deceptive than an empty one (INV-115).

   ⛔ **Confirm the ARGUMENT types before writing the call — and note you may already have
   them.** `get_sdk_reference` returns a `method_signatures` block whenever `filter` names a
   method, under **any** topic, so the signature is already in the `flags` or
   `response_schemas` response you just read (verified on MCP server 1.32.2, 2026-07-30).
   Where you hold neither, ask directly:
   `get_sdk_reference(topic='parameters', filter='find_network_by_entity_id')`. Read the one for
   the bootcamper's language: cross-language documentation is **not** authoritative for the
   shape you pass, and it is wrong for Python here.

   For **Python**, both graph methods take native collections, not an entity-IDs JSON document:

   ```text
   find_network_by_entity_id(entity_ids: List[int], max_degrees: int,
                             build_out_degrees: int, build_out_max_entities: int, flags: int)
   find_path_by_entity_id(start_entity_id: int, end_entity_id: int, max_degrees: int, ...)
   ```

   So pass `[300418, 501752, 500174]` — **not**
   `json.dumps({"ENTITIES": [{"ENTITY_ID": 300418}, ...]})`, which the flags documentation and the
   Java/C# signatures imply and which raises
   `SzSdkError: value {"ENTITIES": [...]} has type str, should be a list of int(s)`. (Credit to
   the SDK: that error names the expected signature outright, so recovery is immediate — but the
   round trip is avoidable.)

   For any other language, confirm the shape for that binding with
   `get_sdk_reference(topic='parameters', filter='<method>', language='<chosen_language>')` rather
   than copying Python's or another language's form (INV-002 — this module is language-agnostic;
   only the *known-divergent* case is spelled out). Only where that topic does not answer for the
   binding, fall back to the installed binding itself: its own reference, `help()`, or equivalent
   introspection (INV-132).

   Select flags appropriate for relationship exploration and explain each: "I'm using [flag] so
   we can see [what it provides]." For example: "I'm using [relationship detail flag] so we can
   see the full attribute information for each entity in the network. This helps us understand
   what connects them."
3. **find_network demonstration:** call `find_network` with a set of related entity IDs (at
   least 2–3 of the entities with relationships from step 4a). Present the resulting network
   structure:
   - **Which entities are connected:** list each entity and its connections, with entity IDs
     and brief identifying information (name, data source).
   - **What attributes they share:** for each connection, explain the common attributes —
     shared addresses, phone numbers, names, or other features that create the link.
   - **Degrees of separation:** show how many hops separate each pair. "Entity A is directly
     connected to Entity B (1 degree), and Entity B connects to Entity C (so A and C are 2
     degrees apart)."

   Present this as a clear textual network diagram or structured list so the bootcamper can
   follow the connections.
4. **find_path demonstration:** demonstrate `find_path` between two indirectly connected
   entities (2+ degrees of separation if available). On address-dense data almost every candidate
   pair is directly linked, so do not pick pairs at random. **Find a 2+ degree pair with the hub
   method:**
   1. Take the entity with the most relationships from step 4a — the **hub**.
   2. Pick two of its neighbors that are **not related to each other**: neither appears among the
      other's related entities.
   3. Confirm with `find_path`: a shortest path of **2 or more degrees** means the pair is good. Set
      the degree limit high enough to return a 2-degree path, taking the parameter's name and type
      for the bootcamper's binding from `get_sdk_reference` (the signature above), never from
      another language.
   4. If the pair turns out to be directly linked, try another pair of the hub's neighbors, then
      the next hub (the entity with the next-most relationships). A hub with fewer than two
      neighbors is skipped. **Stop after three hubs.**

   **If no 2+ degree pair is found after three hubs,** demonstrate `find_path` on a directly
   linked (1-degree) pair instead, and say plainly that this data has no path of 2+ degrees to
   show: "In your data, every pair I checked is directly connected, so there's no path of 2 or
   more degrees to show. Here is `find_path` on a direct connection instead." In that case, leave
   out the "these aren't directly connected" line below.

   Show the shortest path of relationships:
   - State which two entities and why: "Let's find the shortest path between Entity [ID1] and
     Entity [ID2]. These aren't directly connected, so we'll see the intermediate entities
     that link them."
   - Present each step in the path: Entity A → Entity B → Entity C, with the connecting
     attributes at each hop.
   - Explain what the path reveals about the relationship between the two endpoints.
5. **Network structure explanation:**
   - **How entities connect through shared attributes:** "Entities in Senzing connect through
     shared features, when two entities share an address, phone number, or other attribute,
     that creates a relationship link between them."
   - **What relationship types mean:** explain disclosed relationships (explicitly stated in
     source data, like 'spouse' or 'employer') versus discovered relationships (inferred from
     shared attributes like a common address).
   - **How to interpret degrees of separation:** "Degrees of separation tell you how many
     entity-to-entity hops connect two entities. Direct connections are 1 degree; connections
     through an intermediary are 2 degrees, and so on."
6. **Practical use cases:**
   - **Fraud ring detection:** "find_network reveals clusters of connected entities that share
     attributes. This is how investigators discover fraud rings where multiple identities
     share addresses, phones, or other features."
   - **Supply chain analysis:** "Tracing entity connections helps identify hidden relationships
     between suppliers, intermediaries, and end customers in complex supply chains."
   - **Beneficial ownership tracing:** "find_path can trace the chain of relationships from a
     company to its ultimate beneficial owners through intermediate entities."
   - **Customer household grouping:** "find_network identifies entities that share a household
     address, helping group related customers for marketing or risk assessment."
7. **Graceful fallback (no relationships in data):** if the bootcamper's data contains no entity
   relationships or disclosed connections (as determined in step 4a), do NOT attempt the live
   demonstration. Instead:
   - State: "Your data doesn't contain disclosed relationships, so I'll explain what this would
     look like with connected data."
   - Describe what `find_network` returns when entities are connected: a graph structure with
     entity nodes, relationship edges, shared attributes at each connection, and degrees of
     separation.
   - Describe what `find_path` returns: an ordered list of entities forming the shortest path
     between two endpoints, with the connecting attributes at each hop.
   - Explain the SDK methods conceptually so the bootcamper understands how to use them with
     relationship-rich data.
   - Write step 4d status as `"skipped"` with reason `"no_relationships"` in the checkpoint.
8. **Transition:** relationship-network exploration is the final Discover demonstration. After
   presenting it (or the fallback above), end the turn on this single question:

   👉 **Would you like to continue to module completion now?**

   *(Internal: end the turn on this question and wait.)* The Discover phase is complete either
   way — proceed to Discover phase completion below, then return to `phase1-query-visualize.md`
   for the Query Completeness Gate.

**Checkpoint:** write step 4d under `module_7_query.steps.4d`:

- If relationships were demonstrated: `{"status": "completed"}`.
- If no relationships exist in data: `{"status": "skipped", "reason": "no_relationships"}`.

Include the `reason` field only when the step is skipped. Also set top-level `current_step` to
`"4d"`.

### Discover phase completion

After step 4d is complete (or after any early exit), update the top-level `discover_phase`
status in `config/bootcamp_progress.json` under `module_7_query`:

- Set `"discover_phase": "completed"` when all steps 4a–4d have been checkpointed (whether
  completed or individually skipped due to data limitations).
- Set `"discover_phase": "skipped"` when the bootcamper declines the Discover phase at the
  opt-in prompt or exits early at any transition point.

(The former step 4e — data-specific visualization suggestions — are now tabs of the Phase 1
step-3c visualization app (Match Keys, Feature Scores, Cross-Source, and Entity Graph's
relationship mode) and are
no longer part of the Discover phase.)

The full checkpoint structure in `config/bootcamp_progress.json` is:

```json
{
  "module_7_query": {
    "steps": {
      "4a": {"status": "completed", "patterns_found": {"multi_record": 5, "cross_source": 3, "relationships": 2}},
      "4b": {"status": "completed", "entity_demonstrated": 1234},
      "4c": {"status": "completed", "entity_demonstrated": 5678},
      "4d": {"status": "completed"}
    },
    "discover_phase": "completed"
  }
}
```

After updating the `discover_phase` status, return to `phase1-query-visualize.md` for the Query
Completeness Gate.

**Success:** Discover phase completed (or explicitly skipped), data patterns analyzed, why/how
analysis demonstrated, and relationship networks explored. (Data-specific visualization
suggestions are offered separately at the Phase 1 step-3c visualization gate.)
