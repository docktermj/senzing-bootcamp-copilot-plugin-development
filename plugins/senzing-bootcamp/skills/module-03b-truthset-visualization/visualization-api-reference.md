# Truth Set Visualization: API Reference

> **Language note (INV-090):** the API endpoints and JSON response shapes below are the contract to
> implement in the Bootcamper's chosen language. `search_builder.py` / `graph_builder.py` are the
> **Python reference implementation's** internal module names — not required file names for your
> implementation.

**Purpose:** full API response schemas and the `search_builder.py` enrichment specification for
the Truth Set visualization web service. This is reference material, loaded on demand from
`phase1-visualization.md` (Step 2). See that file for the executable generation and verification
steps.

All endpoint data derives from Senzing SDK methods (`export_json_entity_report`,
`get_entity_by_entity_id`, `search_by_attributes`, `find_network_by_entity_id`,
`why_records`, `why_record_in_entity`, `how_entity_by_entity_id`). These are SDK
methods, not MCP tools; generate the SDK code for them via `get_sdk_reference` + `sdk_guide`, and
confirm exact method and flag names via the Senzing MCP server. Never query `database/G2C.db`
with SQL.

## API Endpoints

The server SHALL expose these endpoints:

**`GET /api/stats`:** Aggregate entity resolution statistics

```json
{
  "records_total": 510,
  "entities_total": 395,
  "multi_record_entities": 87,
  "cross_source_entities": 42,
  "relationships_total": 156,
  "data_sources_total": 3,
  "histogram": {"1": 308, "2": 65, "3": 17, "4+": 5},
  "bucket_entities": {
    "1": [{"entity_id": 10, "entity_name": "Alice Johnson", "record_count": 1}],
    "2": [{"entity_id": 1, "entity_name": "Robert Smith", "record_count": 2}],
    "3": [], "4+": []
  },
  "sample_entities": [
    {"entity_id": 1, "entity_name": "Robert Smith", "record_count": 3, "data_sources": ["CUSTOMERS", "REFERENCE"]}
  ]
}
```

Required fields: `records_total`, `entities_total`, `multi_record_entities`,
`cross_source_entities`, `relationships_total`, `data_sources_total`, `histogram`,
`bucket_entities`, `sample_entities`. The `histogram`
maps record-count buckets (1, 2, 3, 4+) to entity counts; `bucket_entities` maps the same buckets
to the entities in each (each `{entity_id, entity_name, record_count}`) so the histogram bars are
clickable and drill down to the entities in a bucket. Implementations MAY cap each bucket list
(the reference caps at 200 per bucket); the `histogram` counts remain authoritative.
`sample_entities` is the multi-record entities in descending record-count order (the reference caps
the list at 10), each `{entity_id, entity_name, record_count, data_sources}` — the largest resolved
entities, shown beneath the histogram on the same tab.
`data_sources_total` is the count of distinct data-source codes across all entities; the client
uses it to decide whether the **Cross-Source** tab applies (it needs 2+ sources).

**`GET /api/graph`:** Entity nodes and relationship edges

```json
{
  "nodes": [
    {"entity_id": 1, "entity_name": "Robert Smith", "record_count": 3, "data_sources": ["CUSTOMERS", "REFERENCE"], "records": [{"data_source": "CUSTOMERS", "record_id": "1001"}]}
  ],
  "edges": [
    {"source_entity_id": 1, "target_entity_id": 2, "match_key": "+NAME+ADDRESS", "relationship_type": "possible_match"}
  ]
}
```

Each node: `entity_id`, `entity_name`, `record_count`, `data_sources`, `records`. Each edge:
`source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`. The payload also carries
`total` (every entity in the datastore), `capped` (whether the node cap applied) and
**`related_total`**: the number of distinct entities in the **whole datastore** with at least one
relationship — the distinct endpoints of every edge, counted **before** the cap, and present whether
or not the cap applies. See "The graph payload is bounded, and says so".

**`relationship_type` vocabulary (enumerated).** `relationship_type` MUST be one of the values
below — a closed set, so the legend and the edge styling cannot drift apart. Derive it from the
Senzing relationship fields, which `get_sdk_reference(topic='response_schemas')` documents on
`RELATED_ENTITIES[]` as `MATCH_LEVEL_CODE` (values `POSSIBLY_SAME`, `POSSIBLY_RELATED`),
`IS_DISCLOSED` (1 when the relationship was disclosed in the source data) and `IS_AMBIGUOUS`
(verified 2026-07-25 — re-verify rather than trusting this table):

| `relationship_type` | Derived from | Bootcamper-facing label |
|---|---|---|
| `possibly_same` | `MATCH_LEVEL_CODE == "POSSIBLY_SAME"` | "possibly the same entity" |
| `possibly_related` | `MATCH_LEVEL_CODE == "POSSIBLY_RELATED"` | "possibly related" |
| `disclosed` | `IS_DISCLOSED == 1` (takes precedence over the match level) | "disclosed relationship" |
| `ambiguous` | `IS_AMBIGUOUS == 1` | "ambiguous" |

Emit the label alongside the code so the legend text and the edge data share one source. Do not
invent additional values: an unrecognized relationship falls back to `possibly_related` rather than
creating a new type the legend does not know about.

> `source_entity_id`/`target_entity_id` are the unchanged API contract; mapping to D3's
> `source`/`target` is a client-side concern handled in `drawGraph` (see the edge-mapping
> requirement in Step 2 of `phase1-visualization.md`).

**Edge discovery.** The example JSON above shows the edge shape only; it does not imply edges come
from an export. ⚠️ **Whether an export carries `RELATED_ENTITIES` depends on the flag set — dump one
row and check before building edges from it, because reading edges from a row that lacks the key
yields an empty `edges` array and no error.**

- With `SZ_EXPORT_DEFAULT_FLAGS` it **does**: `reporting_guide(topic='evaluation', language='<chosen_language>')` documents each
  exported row as carrying `RESOLVED_ENTITY` *and* `RELATED_ENTITIES[]` (with `ENTITY_ID`,
  `MATCH_LEVEL_CODE`, `MATCH_KEY`, `ERRULE_CODE`, `RECORD_SUMMARY[]`), and its worked pattern derives
  relationship statistics in a single export pass (verified 2026-07-28; a live SDK 4.3.3 run agreed).
  If you build edges this way, **deduplicate `(min_id, max_id)` pairs** — that same guidance notes
  each relationship appears in *both* entities' `RELATED_ENTITIES`, so an un-deduplicated edge list
  draws every relationship twice.
- With a flag set assembled from `SZ_ENTITY_INCLUDE_*` members instead, a bootcamp session on the
  same SDK version got rows with **no `RELATED_ENTITIES` key at all**. `SZ_ENTITY_INCLUDE_ALL_RELATIONS`
  and its members — `SZ_ENTITY_INCLUDE_RELATED_ENTITY_NAME`, `_RELATED_RECORD_SUMMARY`,
  `_RELATED_MATCHING_INFO`, `_RELATED_RECORD_DATA`, `_RELATED_RECORD_TYPES` — do **not** list the
  export methods in their `applies_to`, which is why composing an export's flags out of those alone
  is the case that loses relationships. Confirm with
  `get_sdk_reference(topic='flags', filter='SZ_ENTITY_INCLUDE_ALL_RELATIONS')`, which returns the
  whole family in one reply.
- ⚠️ **`SZ_INCLUDE_MATCH_KEY_DETAILS` is the exception in that same reply — it *does* apply to
  export.** Its `applies_to` names `export_json_entity_report` and `export_csv_entity_report`
  alongside the entity, `why_*`, `how_entity_by_entity_id`, `find_path_*` and `find_network_*`
  methods (verified on MCP server 1.32.8, docs indexed 2026-08-11 13:35 UTC, 2026-08-11). So
  match-key detail **is** available on an export. It also carries `depends_on`
  (`SZ_ENTITY_INCLUDE_ALL_RELATIONS`, or one of the individual relations flags), so it produces
  output only when the export's flag set already includes relationships — a dependency, not an
  exclusion. ⛔ **Read each row's own `applies_to`, never the response as one group.** This flag is
  returned by the `SZ_ENTITY_INCLUDE_ALL_RELATIONS` filter *because* it depends on those flags, and
  that adjacency is precisely what makes its longer `applies_to` easy to miss.

So an export **is** a legitimate edge source when its rows carry the key, and the per-entity and
network methods below remain correct and are the fallback when they do not.
`graph_builder.py` MAY discover relationships from a detail-carrying export (dump one row first), or
through a **per-entity or network** method:

- **`find_network_by_entity_id`:** for multi-record/related entities, retrieve the relationship
  network and derive edges from the returned links. (Note the Python binding takes a plain
  `List[int]` of entity IDs, not an entity-IDs JSON document.)
- **`get_entity_by_entity_id` / `get_entity_by_record_id`:** per entity, with
  `SZ_ENTITY_INCLUDE_ALL_RELATIONS` (or `SZ_ENTITY_DEFAULT_FLAGS`, which contains it), then build
  edges from each entity's `RELATED_ENTITIES[]`.

`SZ_EXPORT_INCLUDE_ALL_HAVING_RELATIONSHIPS` is a **row filter** — it selects which entities appear
in an export, not what relationship detail each row carries — so it does not substitute for either
of the above.

⛔ If the resulting `edges` array is empty, treat it as a probable reader failure before reporting
"no relationships" (INV-115): confirm against the load summary's relationship count, and say the
edges could not be read rather than rendering a graph that implies there were none.

Map each discovered relationship to an `Edge`: `match_key` is taken from the Senzing
relationship's match-key string and `relationship_type` reflects the relationship kind (e.g.,
possible match / disclosed / discovered). De-duplicate edges and create an edge only between
entities that both appear in the node set above.

> Confirm the exact Senzing flag/method names via the Senzing MCP server (`search_docs` /
> `sdk_guide` / `get_sdk_reference`) when generating code; do not assert them from training data.
> Refer to the MCP server by name only; no URL.

**`GET /api/merges`:** Multi-record entities with constituent records

```json
{
  "entities": [
    {
      "entity_id": 1, "entity_name": "Robert Smith", "record_count": 2,
      "data_sources": ["CUSTOMERS", "REFERENCE"],
      "records": [
        {"data_source": "CUSTOMERS", "record_id": "1001", "match_key": ""},
        {"data_source": "REFERENCE", "record_id": "2001", "match_key": "+NAME+ADDRESS"}
      ]
    }
  ]
}
```

Each entity: `entity_id`, `entity_name`, `record_count`, `data_sources`, `records`. Each record:
`data_source`, `record_id`, `match_key`. Only entities with 2+ records are returned.

⛔ **`match_key` lives on the RECORD, not on the entity — one home, and this is it.** It is the key
that pulled *that* record into the entity, which is the more informative placement and the one the
Match Keys tab reads. **An empty string is normal, not missing data:** the entity's seed record
joined nothing, so it has no key. Render an empty value as "seed record" or omit the chip — never as
a blank field, which reads as a defect (INV-115).

⚠️ **Record fields are `data_source`, `record_id`, `match_key` — and no more, by design.** The
entity model is built with `SZ_ENTITY_DEFAULT_FLAGS`, and that composite **excludes**
`SZ_ENTITY_INCLUDE_RECORD_FEATURES` and `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` (measured against the
SDK's own flag constants, Senzing 4.3.4, 2026-08-14). So a record's name, address and phone are
**not in the response** at these flags — they are entity-level features, not record-level ones. A
server that reports per-record names without adding those flags is inventing them.

**To enrich the Records panel (optional, and not required by this contract):** add
`SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS` — then each record carries `FEATURES.NAME[].FEAT_DESC`,
`FEATURES.ADDRESS[].FEAT_DESC` and `FEATURES.PHONE[].FEAT_DESC` — and/or
`SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` for the record as it was loaded. `SZ_ENTITY_INCLUDE_RECORD_FEATURES`
is **not** that flag: its `response_paths` is `RECORDS[].FEATURE_IDS[]`, feature ids without their
descriptions (`get_sdk_reference(topic='flags', filter='SZ_ENTITY_INCLUDE_RECORD_FEATURES')`, MCP
server 1.37.14, 2026-09-28). Confirm the paths against
`get_sdk_reference(topic='response_schemas', filter='get_entity_by_record_id')` rather than from
here (INV-080). ⚠️ Weigh it at scale first: this payload is **embedded in the standalone snapshot**
(INV-070), and Query, Visualize and Discover points the same app at the Bootcamper's full dataset,
so per-record features multiply the keepsake's size by the record count. Defaults stay lean for that
reason, and the composite is the right choice for exploration (the server's own production caution
notwithstanding — see Module 7).

**`GET /api/search`:** Search entities with enriched resolution reasoning

⛔ **Search MUST try `NAME_ORG`, not `NAME_FULL` alone.** Per the Senzing Entity Specification
(Name > Feature: NAME — confirm via `search_docs`), `NAME_ORG` is the organization name attribute
and `NAME_FULL` is the "single-field name when type (person vs org) is unknown"; the specification's
rule is *"use `NAME_ORG` for organizations; use `NAME_FULL` only when the type is unknown or only a
single field exists"*. An organization name sent as `NAME_FULL` matches **nothing**, and returns no
error — so a `NAME_FULL`-only search silently fails for every organization in the data. On a
half-organization dataset that is half the population unsearchable: `"ABSOLUTE DENTAL"` returned 0
results while a person name returned a hit immediately. Build the attribute document per attribute
and try `NAME_FULL`, then `NAME_ORG` when the first yields nothing (or send both and merge by
`ENTITY_ID`). This binds a server in **any** language (INV-002/INV-090), not only the bundled Python
reference — the defect propagated into a generated query program precisely because it lived in the
reference implementation and in no written rule.

An attribute that **errors** is retried past, not returned on (INV-190). "Yields nothing" covers a
failed attempt as well as an empty one: a search call that raises on `NAME_FULL` MUST still try
`NAME_ORG`, because the attribute that failed is the one that could not have matched an
organization anyway. Report an error only once every attribute has been attempted and none
produced a result, and name which ones failed. Do not write the guard as "has anything matched so
far" — that is true on the *first* attribute by construction, so the fallback is foreclosed on
exactly the attempt it exists to follow (the bundled reference shipped that bug).

The response MUST report which attributes were searched (`attributes_tried`), and an empty result
MUST be rendered as "no entity matched a `NAME_FULL` then `NAME_ORG` search for X" — never as "not
in the data" (INV-115). An empty result set is indistinguishable from absence otherwise, so a
bootcamper concludes their load failed rather than that the query was wrong.

```json
{
  "results": [
    {
      "entity_id": 1,
      "entity_name": "Robert Smith",
      "record_count": 3,
      "data_sources": ["CUSTOMERS", "REFERENCE"],
      "match_keys": {
        "entity_level": "+NAME+DOB+PHONE",
        "per_record": ["+NAME+DOB", "+PHONE", "+NAME+ADDRESS"]
      },
      "feature_scores": [
        {"feature": "NAME", "score": 97, "label": "CLOSE"},
        {"feature": "DOB", "score": 100, "label": "SAME"},
        {"feature": "PHONE", "score": 100, "label": "SAME"}
      ],
      "resolution_rules": [
        {"data_source": "CUSTOMERS", "record_id": "1001", "rule": "CNAME_CFF_CEXCL"},
        {"data_source": "REFERENCE", "record_id": "2001", "rule": "CNAME_CFF"}
      ],
      "enrichment_error": null
    }
  ],
  "query": {
    "name": "Robert Smith",
    "address": null,
    "phone": null,
    "email": null
  }
}
```

Each result includes the base fields (`entity_id`, `entity_name`, `record_count`,
`data_sources`) plus enrichment fields:

| Field | Type | Description |
|-------|------|-------------|
| `match_keys.entity_level` | `string \| null` | The overall match key string for the entity |
| `match_keys.per_record` | `list[string]` | Per-record match key strings (empty list for single-record entities) |
| `feature_scores` | `list[object]` | Each entry: `feature` (string), `score` (int 0-100), `label` (string) |
| `resolution_rules` | `list[object]` | Each entry: `data_source` (string), `record_id` (string), `rule` (string) |
| `enrichment_error` | `string \| null` | Non-null if `get_entity_by_entity_id` failed; contains exception type + message |

**Error case response:** when enrichment fails for a specific entity, return the basic result
with null enrichment fields and an `enrichment_error` string:

```json
{
  "entity_id": 5,
  "entity_name": "Jane Doe",
  "record_count": 2,
  "data_sources": ["WATCHLIST"],
  "match_keys": null,
  "feature_scores": null,
  "resolution_rules": null,
  "enrichment_error": "SzError: Entity 5 not found in repository"
}
```

**Single-record entity response:** when an entity has only one record (no inter-record
resolution occurred), return an empty `per_record` list and empty `resolution_rules` list:

```json
{
  "entity_id": 10,
  "entity_name": "Alice Johnson",
  "record_count": 1,
  "data_sources": ["CUSTOMERS"],
  "match_keys": {
    "entity_level": "+NAME",
    "per_record": []
  },
  "feature_scores": [
    {"feature": "NAME", "score": 95, "label": "CLOSE"}
  ],
  "resolution_rules": [],
  "enrichment_error": null
}
```

> ⛔ **The JSON payloads below illustrate SHAPE, not field names (INV-115).** They are examples,
> not authority. Before writing any code that parses an SDK response, call
> `get_sdk_reference(topic='response_schemas', filter='<method>')`; for nesting deeper than that
> topic documents, dump one raw response and read it. A wrong field name does not raise — it
> yields `None` and renders blank, so the output reads as "Senzing found nothing" rather than a
> bug. Three such mistakes shipped silently in one bootcamp before anyone noticed.
>
> **MCP-confirmed response paths** (verified 2026-07-25 against `get_sdk_reference` and
> `search_docs`; re-verify rather than trusting this list):
>
> | Method | Confirmed paths |
> |---|---|
> | `get_entity_by_entity_id` / `get_entity_by_record_id` | `RESOLVED_ENTITY.ENTITY_ID`, `.ENTITY_NAME`, `.FEATURES`, `.RECORD_SUMMARY`, `.RECORDS[]` with `.DATA_SOURCE` / `.RECORD_ID` / `.MATCH_KEY` / `.MATCH_LEVEL_CODE` / `.ERRULE_CODE`; `RELATED_ENTITIES[]` with `.ENTITY_ID` / `.MATCH_LEVEL_CODE` / `.MATCH_KEY` / `.IS_DISCLOSED` / `.IS_AMBIGUOUS` |
> | `why_entities` / `why_records` / `why_record_in_entity` | `WHY_RESULTS[]`, `ENTITIES[]` — and the `MATCH_INFO` interior is documented too: `.CANDIDATE_KEYS.<KEY_TYPE>[]`, `.FEATURE_SCORES.<FAMILY>[]`, `.WHY_KEY_DETAILS.CONFIRMATIONS[]`, `.MATCH_LEVEL_CODE`, `.WHY_ERRULE_CODE`, `.WHY_KEY` (re-verified on MCP server 1.32.8, docs indexed 2026-08-11 13:35 UTC, 2026-08-11 — partial, ask for the full `fields[]`) |
> | `how_entity_by_entity_id` | `HOW_RESULTS.RESOLUTION_STEPS[]`, `HOW_RESULTS.FINAL_STATE`. ⛔ **A step's two sides are `VIRTUAL_ENTITY_1` / `VIRTUAL_ENTITY_2`** — *objects*, each with `.VIRTUAL_ENTITY_ID` and `.MEMBER_RECORDS[]` (`.INTERNAL_ID`, `.RECORDS[].DATA_SOURCE` / `.RECORD_ID`). The similar `INBOUND_VIRTUAL_ENTITY_ID` is a **string ID** on the step, paired with `RESULT_VIRTUAL_ENTITY_ID`; **no `CANDIDATE_VIRTUAL_ENTITY` exists at any depth**. The `INBOUND_`/`CANDIDATE_` pairing is real but lives one level deeper as `INBOUND_FEAT_DESC` / `CANDIDATE_FEAT_DESC` under `MATCH_INFO.FEATURE_SCORES.<FAMILY>[]` and `MATCH_INFO.MATCH_KEY_DETAILS.CONFIRMATIONS[]` — generalizing it up to the step level lands on a key that exists at the wrong type, so the lookup appears to confirm it and the parser renders every step blank (re-verified on MCP server 1.32.9, 2026-08-17) |
> | `search_by_attributes` | `RESOLVED_ENTITIES[]` (each carries `MATCH_INFO` and `ENTITY`) |
> | `find_path_*` | `ENTITY_PATHS[]`, `ENTITIES[]`, **`ENTITY_PATH_LINKS[]`** — *not* `ENTITY_NETWORK_LINKS[]`; each link element carries the **same seven fields** as the network row below (re-verified on MCP server 1.32.2, docs indexed 2026-07-29 11:11 UTC, 2026-07-31). The element fields are identical and only the array name differs, so a parser carried over from `find_network` returns every edge blank |
> | `ENTITY_PATHS[]` (in **both** `find_path_*` and `find_network_*`) | `START_ENTITY_ID`, `END_ENTITY_ID`, `ENTITIES[]` — three fields, and the endpoints are **directed**. ⛔ **A `find_network` response therefore carries TWO endpoint conventions at once:** paths are `START_`/`END_`, links are `MIN_`/`MAX_` (undirected, normalized low-to-high). A link is an unordered pair and a path is not, which is the reason — and `START_`/`END_` is the natural wrong guess for a link precisely because the sibling array in the same response uses it. Reading path endpoint names off a link element printed **38 edges as `null -> null` with no error** (re-verified on MCP server 1.32.9, 2026-08-17, `get_sdk_reference(topic='response_schemas', filter='find_network', language='java')`) |
> | `find_network_*` | `ENTITY_PATHS[]`, `ENTITIES[]`, `ENTITY_NETWORK_LINKS[]`; each link element (**now documented by `response_schemas` — re-verified on MCP server 1.32.2, 2026-07-30 — and corroborated by a dump on SDK 4.3.3, 2026-07-28**) carries `MIN_ENTITY_ID` / `MAX_ENTITY_ID` (endpoints, normalized low-to-high), `MATCH_LEVEL_CODE`, `MATCH_KEY`, `ERRULE_CODE`, `IS_DISCLOSED`, `IS_AMBIGUOUS` |
> | `get_record` | `DATA_SOURCE`, `RECORD_ID`, `JSON_DATA.*` under `SZ_RECORD_DEFAULT_FLAGS` — one record by key; entity-family calls return `JSON_DATA` too when its flag is added (see below) |
>
> ⛔ (INV-080) **`JSON_DATA` needs `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` OR-ed in, and
> `SZ_ENTITY_DEFAULT_FLAGS` omits it.** `get_sdk_reference(topic='flags',
> filter='SZ_ENTITY_INCLUDE_RECORD_JSON_DATA')` lists the entity family in that flag's `applies_to`
> (`get_entity_by_entity_id`, `get_entity_by_record_id`, `search_by_attributes`, `why_*`,
> `find_path_*`, `find_network_*`, as well as `get_record`), with
> `response_paths: ["RESOLVED_ENTITY.RECORDS[].JSON_DATA"]`. Read `applies_to` there rather than from
> this list. So on an entity call, a blank `JSON_DATA` means the flag is missing, not that the route is
> wrong: add the flag, don't switch to `get_record`. (Through server 1.32.2 the flag's `applies_to`
> was `["get_record"]` alone, and this section said so; the server has since widened it.)
>
> **For per-record source values, one entity-family call is enough — pick the flag for the shape you
> need.** Both are documented under `get_sdk_reference(topic='response_schemas',
> filter='get_entity_by_entity_id')`, each gated on its flag:
>
> - **The raw record as loaded:** `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` →
>   `RESOLVED_ENTITY.RECORDS[].JSON_DATA`, with source values under `JSON_DATA.FEATURES[]` (e.g.
>   `JSON_DATA.FEATURES[].ADDR_CITY`, `.NAME_FIRST`, `.DATE_OF_BIRTH`).
> - **The mapped attributes per feature:** `SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS` →
>   `RESOLVED_ENTITY.RECORDS[].FEATURES.<TYPE>[].ATTRIBUTES.*` (e.g.
>   `FEATURES.ADDRESS[].ATTRIBUTES.ADDR_CITY`, `FEATURES.NAME[].ATTRIBUTES.NAME_FIRST`,
>   `FEATURES.DOB[].ATTRIBUTES.DATE_OF_BIRTH`), plus `RECORDS[].UNMAPPED_DATA.*` under
>   `SZ_ENTITY_INCLUDE_RECORD_UNMAPPED_DATA`.
>
> These are the **mapped** attributes per feature, not the raw record as loaded, so choose by what the
> viewer shows. The example paths were checked against MCP server 1.37.14 on 2026-09-28; they are
> illustrations, and a dump of one element still decides (INV-115). `get_record` stays the call for
> one record fetched by its key.
>
> **Watch this asymmetry — it is a silent-blank trap.** With `SZ_INCLUDE_MATCH_KEY_DETAILS`, the
> match-key breakdown sits under a **differently named key** depending on the call: `why_*` puts a
> **`WHY_KEY_DETAILS`** object inside `MATCH_INFO`, while `how_entity_by_entity_id` puts a
> **`MATCH_KEY_DETAILS`** object inside each resolution step's `MATCH_INFO`. Both contain
> `CONFIRMATIONS` (and optionally `DENIALS`). Reusing one parser for both silently yields nothing.
>
> ⚠️ **They differ in POPULATION as well as in name, so one being empty is not evidence the other
> parser is wrong.** They are separate documented paths for separate calls
> (`get_sdk_reference(topic='response_schemas', filter='why_entities', language='python')` returns
> both, server **1.33.0, 2026-08-21**), and on a 2026-08-18 run every `why_records` call returned
> `WHY_KEY_DETAILS` with an **empty** `CONFIRMATIONS[]` while `how_entity`'s
> `MATCH_KEY_DETAILS.CONFIRMATIONS[]` populated **on the same entity** (observation-only —
> whether a given rule produces confirmations is a live-engine fact no MCP route reports).
> Fall back to `FEATURE_SCORES`, which carries the same evidence.
>
> ⚠️ **The "with the flag" in that sentence is load-bearing on a why call, and this file was right
> about it when Module 7 was not.** Module 7 briefly forbade the flag on why calls, claiming the
> breakdown was there without it; on **SDK 4.3.4** `WHY_KEY_DETAILS` was **absent** until the flag
> (plus a relations flag) was passed, and absent again without it on **4.3.2** — observation-only,
> 2026-08-16 (INV-080/INV-149). The server now documents the requirement, and the observation above agrees
> with it: `get_sdk_reference(topic='response_schemas', filter='why_entities')` lists
> `WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS` with `requires_flags:
> ["SZ_INCLUDE_MATCH_KEY_DETAILS"]` (server **1.35.3**, 2026-09-01). ⚠️ **The `flags` topic alone
> does not say so** — that flag's `response_paths` names only `RELATED_ENTITIES[].MATCH_KEY_DETAILS`
> — so read `response_schemas` before concluding a field is attributed to nothing. So pass the flag,
> and still check the keys you actually got.
>
> **Both are documented — look them up rather than dumping first.**
> `get_sdk_reference(topic='response_schemas', filter='why_entities')` returns the `data[]` entry
> whose `id` is `why_entities`, and its `fields[]` array carries `path` and `field_type` for the
> whole `MATCH_INFO` interior: `WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS.CONFIRMATIONS[]` with
> `FTYPE_CODE`, `TOKEN`, `SOURCE`, `SCORE`, `SCORE_BUCKET`, `SCORE_BEHAVIOR`, the
> `CANDIDATE_FEAT_*` / `INBOUND_FEAT_*` pairs and `ADDITIONAL_SCORES.*`; and `FEATURE_SCORES` per
> feature family — `.NAME[]`, `.ADDRESS[]`, `.DOB[]`, `.PHONE[]`, `.RECORD_TYPE[]` — each with its
> own element fields. (Re-verified on MCP server 1.32.8, docs indexed 2026-08-11 13:35 UTC,
> 2026-08-11. The same entry covers `why_records` and `why_record_in_entity`, per its `methods[]`;
> `why_search` is a **separate** document with its own `SEARCH_REQUEST` and `SEARCH_STATISTICS`.)
> Dump a raw response when the lookup does not reach something, or to confirm what *this*
> installation actually returned (INV-080/INV-149) — that is the fallback now, not the first move.
> Do not copy field names from any prior implementation, this file included.
>
> **The link elements are documented now — and their endpoint names are still the trap.**
> Re-verified on MCP server 1.32.2, 2026-07-30: `get_sdk_reference(topic='response_schemas',
> filter='find_network')` returns the three arrays above **and** each `ENTITY_NETWORK_LINKS[]`
> element's own fields (`MIN_ENTITY_ID`, `MAX_ENTITY_ID`, `MATCH_KEY`, `MATCH_LEVEL_CODE`,
> `ERRULE_CODE`, `IS_AMBIGUOUS`, `IS_DISCLOSED`). (Through 2026-07-26 it documented only the
> arrays, describing `ENTITY_NETWORK_LINKS[]` as "Network link details between entities" with no
> element fields; that gap is closed, so the lookup no longer leaves you guessing.) Dump one raw
> link element and read its keys before writing the parser anyway (INV-115) — the schema tells you
> what the method documents, the dump tells you what *your* installation returned.
>
> ⚠️ **Do not assume a link's endpoints are keyed the way related-entity records are.** Two bootcamp
> sessions now agree: parsing `ENTITY_NETWORK_LINKS` entries with the `ENTITY_ID` /
> `RELATED_ENTITY_ID` pairing used elsewhere yields `None` for **both** endpoints while `MATCH_KEY`
> renders correctly, and the endpoints are instead carried under normalized low-to-high keys. A live
> dump on SDK 4.3.3 (2026-07-28) gave the element's full key set, now recorded in the table above:
> `MIN_ENTITY_ID`, `MAX_ENTITY_ID`, `MATCH_LEVEL_CODE`, `MATCH_KEY`, `ERRULE_CODE`, `IS_DISCLOSED`,
> `IS_AMBIGUOUS`.
>
> **That list is now MCP-confirmed.** When it was first recorded it was dump-only, so it was carried
> as an unverified caution rather than as names to code against. Re-checked on **MCP server 1.32.2,
> 2026-07-30**: `get_sdk_reference(topic='response_schemas', filter='find_network')` now returns the
> element fields itself — `ENTITY_NETWORK_LINKS[].MIN_ENTITY_ID`, `.MAX_ENTITY_ID`, `.MATCH_KEY`,
> `.MATCH_LEVEL_CODE`, `.ERRULE_CODE`, `.IS_AMBIGUOUS`, `.IS_DISCLOSED`, plus
> `ENTITIES[].RESOLVED_ENTITY.*` and `ENTITY_PATHS[].*`. So these are authoritative names, and the
> 2026-07-28 dump is corroboration rather than the only evidence.
>
> **Do the lookup anyway, and still dump before rendering.** The names being MCP-backed changes their
> standing, not the discipline: run `response_schemas` for the method you are about to parse (it is
> the authority, and its coverage grows — this entry is proof), then dump one element and use what is
> actually there. A mismatch means the shape moved and this table is stale — report it rather than
> coding around it (INV-115/INV-149).
>
> ⛔ **A partially populated row is a wrong field name, not partial data.** This is the shape the
> above failure takes: `MATCH_KEY` renders, both endpoints are blank, and the row looks like a
> relationship Senzing could not fully describe. An all-blank row invites suspicion; a half-populated
> one does not, because the fields that *did* populate signal that the parse worked. When some fields
> of a parsed record populate and others do not, suspect the blank ones' names first (INV-115) and
> confirm against a dumped response before rendering.
>
> **Methods with no `response_schemas` entry at all.** `get_sdk_reference(topic='response_schemas',
> filter='get_stats')` returns an empty `data` array beside a populated `method_signatures`
> (`get_stats() -> str`; MCP server 1.37.14, 2026-09-28) — the lookup is not failing, the coverage is
> simply absent for a method that still returns a JSON document. An empty result is the expected
> outcome for those, not an error to retry: dump the response and read the shape from it. This
> server's coverage grows — `get_version` and `get_license`, once this paragraph's examples, are now
> documented — so re-run the lookup rather than quoting which methods lack an entry.

**`GET /api/why?entity_id=<id>`:** Explain WHY the records in an entity resolved together

Backed by `why_records` (comparing two of the entity's constituent records) or, for a
single-record entity, `why_record_in_entity`. Use the `SZ_WHY_RECORDS_DEFAULT_FLAGS` /
`SZ_WHY_RECORD_IN_ENTITY_DEFAULT_FLAGS` group (these include `SZ_INCLUDE_FEATURE_SCORES`; add
`SZ_INCLUDE_MATCH_KEY_DETAILS` for match-key breakdowns) — confirm exact method/flag names **and
the response structure** via the Senzing MCP server (`get_sdk_reference`, topics `flags` and
`response_schemas`).

```json
{
  "entity_id": 1,
  "mode": "why_records",
  "result": {"WHY_RESULTS": ["..."], "ENTITIES": ["..."]}
}
```

`result` is the SDK `why_*` response JSON verbatim. On failure, return
`{"entity_id": <id>, "error": "<type>: <message>"}` (not a 500), so one entity's failure never
breaks the tab.

**`GET /api/how?entity_id=<id>`:** Explain HOW an entity was constructed from its records

Backed by `how_entity_by_entity_id`. ⛔ **(INV-080, INV-115) `SZ_HOW_ENTITY_DEFAULT_FLAGS` alone will NOT return the
match-key breakdown — add `SZ_INCLUDE_MATCH_KEY_DETAILS` with a relations flag if the renderer shows
it** (the same addition the `/api/why` entry above already makes on the why side). The server is
explicit that the default is not enough: `SZ_HOW_ENTITY_DEFAULT_FLAGS` is `SZ_INCLUDE_FEATURE_SCORES`
alone, `response_paths` `HOW_RESULTS.RESOLUTION_STEPS[]`, and `SZ_INCLUDE_MATCH_KEY_DETAILS` lists
`how_entity_by_entity_id` in `applies_to` with `depends_on` one of the five relations flags
(`get_sdk_reference(topic='flags', filter='SZ_INCLUDE_FEATURE_SCORES', language='python')` and
`filter='SZ_INCLUDE_MATCH_KEY_DETAILS'`, server **1.33.0**, 2026-08-26). Confirm both, and the
response structure, via the MCP server. ⚠️ **Treat the breakdown as conditional and fall back to
`FEATURE_SCORES`** — see the asymmetry note above for what the server does and does not attribute to
this flag on a how response, and never render an empty section.

```json
{
  "entity_id": 1,
  "result": {"HOW_RESULTS": {"RESOLUTION_STEPS": ["..."], "FINAL_STATE": {"VIRTUAL_ENTITIES": ["..."]}}}
}
```

`result` is the SDK response JSON verbatim: `HOW_RESULTS.RESOLUTION_STEPS[]` are the construction
steps, and `FINAL_STATE.VIRTUAL_ENTITIES[]` describes the **final state**, which may hold **more than
one** virtual entity. It is not a description of one resolved entity, with or without steps. On
failure, return `{"entity_id": <id>, "error": "..."}`.

⚠️ **(INV-330) The final state is unsettled when either of two signs is present:**
`HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION` is non-zero (an integer), or
`HOW_RESULTS.FINAL_STATE.VIRTUAL_ENTITIES[]` has more than one element. Either one alone is enough,
and nothing documents whether the two always go together. Observed 2026-09-25 on Senzing SDK 4.4.1
(SQLite): both signs on entities that the entity lookup and the export reported as one entity,
with the redo queue empty. The How rendering below says so rather than presenting such an entity as
built into one. Attach no meaning to `NEED_REEVALUATION` and offer no fix for it: the server gives the
field a type and no definition (INV-080/INV-149).
<!-- MCP-NEGATIVE: search_docs(query='NEED_REEVALUATION how entity final state') — no indexed document defines NEED_REEVALUATION or says what sets or clears it; the only hits are the how flags page's example payload, which shows "NEED_REEVALUATION": 0 — owner: get_sdk_reference(topic='response_schemas', filter='how_entity_by_entity_id') IS the route that owns the how response's fields, and it lists HOW_RESULTS.FINAL_STATE.NEED_REEVALUATION as an integer with no description (absence negative) — server 1.37.13, 2026-09-26 -->

**`GET /api/dashboard`: REMOVED.** Its content is served by `/api/stats`, which carries the same
`histogram` and headline counts plus the `sample_entities` list that was this endpoint's only
unique content. Do NOT implement it, and do not add a separate "Results Dashboard" tab — see
"De-duplication (required)" below.

**`GET /api/records?entity_id=<id>`:** The constituent records of one entity

```json
{
  "entity_id": 1,
  "entity_name": "Robert Smith",
  "records": [
    {"data_source": "CUSTOMERS", "record_id": "1001", "name": "Robert Smith", "address": "123 Main St", "phone": "555-0100", "identifiers": {"SSN": "123-45-6789"}}
  ]
}
```

Backs the **Records** action everywhere an entity is shown (see "Per-entity actions" below),
including single-record entities — unlike `/api/merges`, which returns only multi-record entities.
Each record carries the same fields `/api/merges` uses — `data_source`, `record_id`, `match_key` —
and the two endpoints MUST return **the same record objects**, not merely the same field names: they
read one model, so a divergence between them is a bug in the server rather than a choice. On failure
return `{"entity_id": <id>, "error": "<type>: <message>"}`
with HTTP 200, so one entity's failure never breaks the tab.

Unlike `why`/`how`, this endpoint's data MUST also be **embedded in the standalone snapshot**, so
the Records action works offline — it needs no engine call at view time, only the record data
already gathered when the model was built.

**`GET /api/overlap`:** Cross-source overlap matrix — how many resolved entities each pair of data
sources shares

```json
{
  "sources": ["CUSTOMERS", "REFERENCE", "WATCHLIST"],
  "matrix": [[395, 42, 12], [42, 210, 8], [12, 8, 95]],
  "cell_entities": {
    "0,1": [{"entity_id": 1, "entity_name": "Robert Smith", "record_count": 3}],
    "0,0": [{"entity_id": 7, "entity_name": "Alice Johnson", "record_count": 1}]
  },
  "cell_capped": false
}
```

`sources` is the sorted distinct data-source codes; `matrix` is a square `len(sources)` ×
`len(sources)` grid where `matrix[i][j]` (i≠j) is the number of resolved entities containing
records from **both** `sources[i]` and `sources[j]`, and the diagonal `matrix[i][i]` is the number
of entities present in `sources[i]`. Symmetric. Backs the **Cross-Source** heatmap tab (shown only
when `data_sources_total` ≥ 2).

`cell_entities` maps each cell to the entities it counts, keyed `"i,j"` with `i <= j` (the matrix is
symmetric, so store each pair once and have the client normalize the key). Each entry is
`{entity_id, entity_name, record_count}` — the same shape as `bucket_entities` on `/api/stats`, so
one drill-down renderer serves both. Implementations MAY cap each cell list (the reference caps at
200); `cell_capped` is true when any cell was capped, and the client MUST surface that so the cap is
never silent. `matrix` counts remain authoritative.

**`GET /api/matchkeys`:** Match-key frequency — which feature combinations drove resolutions

```json
{
  "match_keys": [{"match_key": "+NAME+ADDRESS", "count": 128}, {"match_key": "+NAME+DOB", "count": 74}],
  "distinct": 11,
  "capped": false,
  "match_key_entities": {
    "+NAME+ADDRESS": [{"entity_id": 1, "entity_name": "Robert Smith", "record_count": 3}]
  },
  "entities_capped": false
}
```

`match_keys` is the per-record match keys aggregated across all resolved entities, most frequent
first (the reference returns the top 20); `distinct` is the total number of distinct match keys and
`capped` is true when `distinct` exceeds the returned list length. Backs the **Match Keys** tab
(shown only when multi-record entities exist). Per-record match keys come from the entity's records
(the default entity flags' record-matching info); the seed record's match key is typically empty
and is excluded.

`match_key_entities` maps each returned match key to the entities carrying it, each
`{entity_id, entity_name, record_count}` — the same shape as `bucket_entities` and `cell_entities`,
so the one drill-down renderer serves all three. Implementations MAY cap each list (the reference
caps at 200); `entities_capped` is true when any list was capped and the client MUST surface it.
`count` remains authoritative.

**`GET /api/features`:** Feature-score distribution across a capped sample of multi-record entities

```json
{
  "features": [
    {"feature": "NAME", "buckets": {"SAME": 40, "CLOSE": 22, "LIKELY": 5}},
    {"feature": "DOB", "buckets": {"SAME": 30, "PLAUSIBLE": 3}}
  ],
  "sampled": 40,
  "multi_record_total": 87,
  "capped": true
}
```

`features` aggregates, per feature, the count of each Senzing score bucket (`SAME`, `CLOSE`,
`PLUS`, `LIKELY`, `PLAUSIBLE`, `UNLIKELY`, `NO_CHANCE`) observed by calling `why_records` over a
**capped** sample of multi-record entities (the reference caps at 40 to bound build cost). `sampled`
is the number of entities actually aggregated, `multi_record_total` the number available, and
`capped` is true when a cap was hit — the client MUST surface the sample size so the cap is never
silent. Computation is guarded: any `why_records` failure skips that entity and never blocks the
model or snapshot build (INV-077); when nothing could be sampled, `features` is `[]` and the tab is
hidden or shows a note. Backs the **Feature Scores** tab (shown only when multi-record entities
exist). Live-only: because it needs the engine, the static snapshot embeds whatever was computed at
build time (or an empty distribution).

**Where these surface in the UI (tabs).** The app is a **single consolidated, tabbed artifact** —
it is the one visualization Module 7 offers for results, so there are no separate static
visualization pages. Every tab is populated from the endpoints above; tabs whose data is absent are
not shown:

| Tab | Endpoint(s) | Shown when |
|-----|-------------|-----------|
| **Entity Graph** (default) | `/api/graph`, `/api/records`, `/api/why`, `/api/how` | always — force-directed graph of the entity population, with a **"Show only entities with relationships"** mode toggle (shown only when `relationships_total` > 0) that switches to the relationship subgraph with edges colored and dashed by `relationship_type` and a click-to-filter relationship legend; also the cross-source entity-relationship view (subsumes the former `multi_source_results.html`). **Above 400 entities that toggle defaults ON** — see "Defaults at production scale" below |
| **Merge Statistics** | `/api/stats`, `/api/records`, `/api/why`, `/api/how` | always — records-per-entity histogram (this **is** the entity-size distribution) with clickable bars drilling down via `bucket_entities`, plus the largest resolved entities from `sample_entities` |
| **Match Keys** | `/api/matchkeys`, `/api/records`, `/api/why`, `/api/how` | multi-record entities exist — clickable rows drilling down via `match_key_entities` |
| **Feature Scores** | `/api/features` | multi-record entities exist |
| **Cross-Source** | `/api/overlap`, `/api/records`, `/api/why`, `/api/how` | 2+ data sources (`data_sources_total` ≥ 2) — clickable cells drilling down via `cell_entities` |
| **Search / Probe** | `/api/search`, `/api/merges`, `/api/records`, `/api/why`, `/api/how` | always — with pre-verified example-query chips and a **"Show all merged entities"** button that lists every multi-record entity with no query (the one capability the former Record Merges tab uniquely had) |

**De-duplication (required).** Do NOT add a tab whose content is derivable from another tab's
endpoint. When two candidate tabs share their aggregates, **they are one tab.** Applying that test:

- The entity-size distribution is the **Merge Statistics** histogram — not a second tab.
- The cross-source entity-relationship view / former `multi_source_results.html` is the **Entity
  Graph** tab.
- There is **no "Results Dashboard" tab.** Its headline counts and histogram came from the same
  aggregates as `/api/stats`, and its only unique content — the largest resolved entities — is now
  `sample_entities` on that endpoint, rendered beneath the Merge Statistics histogram. Two tabs
  showing one histogram read as redundant, not complementary.
- There is **no "Relationship Network" tab.** This reverses an earlier ruling here that it *was*
  distinct: the related-entity subgraph is a filtered view of **Entity Graph's own** `/api/graph`
  data, so by this rule they are one tab. What made it look distinct — the relationship-type edge
  coloring/dashing and the click-to-filter legend — is preserved as Entity Graph's
  "Show only entities with relationships" mode, so nothing was lost by folding it in.
- There is **no "Record Merges" tab.** For any entity present in both, Search / Probe's per-entity
  result is a strict **superset**: Record Merges showed entity name, record count and one
  entity-level match key; Search / Probe shows all of that plus per-record match keys and feature
  scores. Its one unique capability was browsing *all* merged entities with no query, which is now
  the "Show all merged entities" button on that tab — so the removal is lossless rather than a
  trade. `/api/merges` is retained: the example-query chips and that button both read it.

### Defaults at production scale (required)

Every visual default here was chosen against the Truth Set's 84 entities, and Module 7 points this
same app at the bootcamper's own data — routinely thousands. These defaults do **not** survive that
and are therefore contract, not implementation detail:

**1. Every truncated label must stay distinguishable — whatever it labels.** Wherever a label is
shortened to fit, **no two rendered labels may be identical unless their underlying values are
identical**, and the untruncated value must be reachable on hover (`<title>` or the surface's
equivalent tooltip). This is the general requirement; item 2 is its match-key application, and it
binds every truncated label equally — entity names on graph nodes, source codes in a legend, any
future chart. Two entities named `ACME HOLDINGS INTERNATIONAL LLC` and
`ACME HOLDINGS INTERNATIONAL INC` share their first 27 characters, so a head-only cut renders both
identically; company names sharing a long prefix are routine rather than exotic, and roughly half a
real dataset can be organizations (INV-164). Compare the **fitted** strings, not the source values,
and disambiguate any pair that collides while its values differ — the Python reference appends a
positional suffix. Truncation must never remove the leading characters. Implement this in whatever
language the server is written in (INV-002/INV-090): it is stated here because a rule that lives only
in the Python reference reaches no generated server, which is exactly how the `NAME_FULL` search
defect shipped (INV-164).

**2. Match-key labels must stay distinguishable.** Real match keys run to 70+ characters
(`+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY+LEI_NUMBER`). A fixed
label gutter with right-anchored text pushes the **head** of each key off the left edge, so the
highest bars all render as the same trailing fragment and cannot be told apart — counts correct,
labels useless, chart looking fine. Required behavior:

- Size the label gutter from the longest key present, up to a cap, before truncating anything.
- **Middle-ellipsize** (`+NAME+ADDRESS+NATIONAL_ID+…RATION_COUNTRY+LEI_NUMBER`); never trim from the
  left. Right-truncation alone is **not** sufficient: match keys are `+A+B+C…` sequences that
  commonly share a long prefix and differ only in the final segment, so head-only truncation renders
  the top bars identically — the same unreadable chart, failing from the other end. Keeping both
  ends distinguishes keys that differ at either.
- Guarantee that **no two rendered labels are identical unless their keys are identical** — that is
  the testable property; the exact ellipsis strategy is not. Middle-ellipsis reduces collisions but
  does **not** guarantee this: two keys sharing a long head *and* a long tail, differing only in the
  elided middle, still render identically. So compare the fitted labels and disambiguate any that
  collide while their keys differ (the Python reference appends a positional suffix); the full key
  stays reachable on hover regardless.
- Expose the full, untruncated key on hover (`<title>` or equivalent), on both the bar and its label.

**3. The entity graph must open on something readable.** Hiding labels does not thin 4,464 edges;
at that density the graph conveys shape only, with no practical way to locate an entity. Required:
**above 400 entities, Entity Graph opens on the relationship subgraph** rather than the full
population, provided a subgraph exists (`relationships_total` > 0). The toggle still switches both
ways, a bootcamper's explicit choice is never overridden, and an inline note states both counts —
"Showing the N entities that have relationships, of M total" — for the same reason the label note
exists: otherwise a default reads as the data.

When the graph payload is **capped** (`capped` is true), the shown counts are a part of the
datastore, so every Entity Graph note says so with exact counts and none offers "all" (INV-154):

- **Relationship mode:** "Showing N of the R entities that have relationships — the graph is capped
  at C of M entities.", where N is the relationship-bearing entities shown, R is `related_total`, C
  the nodes in the payload and M is `total`. No "show them all" clause.
- **Relationship mode, none shown:** when no shown entity has a relationship, "None of the R
  entities with relationships are among the C shown." — never "No relationships between entities
  were found in this data.", which is true only of an uncapped payload.
- **Full population:** "Showing C of M entities — the graph is capped; entities spanning the most
  sources are kept first." Shown whenever `capped` is true, independent of the 400-entity threshold.

When `capped` is false the notes are the uncapped wording above, unchanged.

State the threshold as a number so every language implementation (INV-090) picks the same behavior.
Re-check these against the bootcamper's **actual** scale, not the Truth Set: both defects pass every
check 84 entities can run.

### Tab identifiers and deep-linking (required)

Tab ids are **contract**, not an implementation detail: the recap screenshot helper selects a tab by
id, so a server in any language (INV-090) must use these exact ids and expose the two hooks below.

**The row order below is also the order the app presents its tabs, left to right, and therefore the
order screenshots are embedded in the recap** (INV-155 fixes the six-tab set and this order;
INV-147 binds the recap's embedding to it) — by `module-completion.md`'s capture step and by
graduation's orphaned-screenshot backfill alike. Both cite this table (INV-300) rather than restating the
list, so changing a tab's position here changes it everywhere. The recap is a walkthrough of the
app; images in capture or append order cannot be lined up against the interface.

⛔ **(INV-124) The `Section id` and `Nav button id` columns are the capture's hooks, and they bind
the server in whichever language it is generated.** The recap capture activates a tab by finding
`tab-<id>` and `navbtn-<id>` and calling a page-scope `activate(<id>)`, and deep-links with
`?tab=<id>` / `?q=<text>` — so a generated server that renders the right tabs under different ids
produces a recap with no screenshots. This is the one place these ids are normative; every other
file cites this table.

| Tab | Id | Section id | Nav button id | Screenshot slug |
|---|---|---|---|---|
| Entity Graph | `graph` | `tab-graph` | `navbtn-graph` | `entity-graph` |
| Relationship Network — **REMOVED** | `network` | `tab-network` | `navbtn-network` | `relationship-network` |
| Record Merges — **REMOVED** | `merges` | `tab-merges` | `navbtn-merges` | `record-merges` |
| Merge Statistics | `stats` | `tab-stats` | `navbtn-stats` | `merge-statistics` |
| Match Keys | `matchkeys` | `tab-matchkeys` | `navbtn-matchkeys` | `match-keys` |
| Feature Scores | `features` | `tab-features` | `navbtn-features` | `feature-scores` |
| Cross-Source | `overlap` | `tab-overlap` | `navbtn-overlap` | `cross-source` |
| Search / Probe | `probe` | `tab-probe` | `navbtn-probe` | `search-probe` |

The two **REMOVED** rows are retained as reserved identifiers, not as tabs to build: a current app
MUST NOT serve them. They stay listed so the recap screenshot helper still recognizes them when
pointed at a snapshot saved by an earlier, eight-tab run, and so nothing reuses those ids for a
different view.

The app MUST provide:

- **`activate(<id>)`** — a page-scope function that shows that tab. The screenshot helper injects a
  call to it into a temp copy of the standalone snapshot (falling back to clicking
  `#navbtn-<id>`), which is how a tab is captured with no browser-automation dependency.

  ⛔ **`activate()` MUST be idempotent: called for the tab that is already active, it MUST
  return without redrawing (INV-171).** Redrawing rebuilds the tab, and for a tab whose layout
  *animates* — the Entity Graph's force simulation — that restarts the animation from
  scratch. Mid-capture that yields a screenshot of every node collapsed in a corner: a
  valid PNG, at exit 0, of a graph that looks like it found nothing (47 KB where 227 KB
  was expected), which then reaches the recap with a caption describing the graph the
  image does not show. Both capture routes trigger it — the injected `activate('<tab>')`
  and `?tab=<id>` deep-linking, since deep-linking calls `activate()` too — so the guard
  belongs in `activate()` itself rather than in either caller. It also stops a user's
  click on the already-active nav button from restarting the layout.
- **`?tab=<id>` / `?q=<text>` deep-linking** — applied at the end of `init()`, after the async
  data load and `buildNav()` have settled. `?tab=` activates that tab when it is applicable and
  present; `?q=` fills the search box and runs the search, defaulting the tab to `probe` when `q` is
  given without `tab`. This makes any view of the app a shareable URL, and it is what lets the live
  Search / Probe tab be captured showing **real results** rather than an empty box.

Deep-linking MUST be tolerant: an unknown or non-applicable `tab` value leaves the default tab
active rather than erroring or blanking the page.

⛔ **The snapshot's own text MUST NOT hardcode a port or name a dataset the caller did not
supply.** The standalone snapshot is the retained keepsake, so anything it asserts about the
environment ships permanently. Derive the URL it prints from the **parsed `--port`**, and take the
dataset wording from the caller — defaulting to neutral wording ("the loaded data") rather than
naming the Truth Set. One code path serves the Truth Set in its own module and the bootcamper's own
data in Query, Visualize and Discover: a snapshot that says "this Truth Set" on a `--port 9001` run
tells the reader to open a port nothing is listening on **and** mislabels their data, silently, in
the artifact they keep.

**So the server MUST accept the dataset wording as an argument** — in whatever form your language's
CLI takes (the Python reference spells it `--dataset`; INV-090 leaves the spelling to you) — and the
**caller MUST pass it**: Truth Set visualization passes "the Senzing Truth Set", Query, Visualize and
Discover passes wording describing the Bootcamper's own sources. Accepting it and defaulting to
neutral wording is only half the requirement; a snapshot that could have been labeled and was not
is a vaguer keepsake than the data warranted.

Headline counts belong in the page-level summary strip and appear **once**. A tab MUST NOT repeat
them in its own summary sentence.

## Per-entity actions (required everywhere)

Every place an entity is shown with actions gets the **same three buttons, in this order — never a
subset**:

| Action | Calls | Shows |
|---|---|---|
| **Records** | `/api/records?entity_id=` | the entity's constituent records |
| **Why?** | `/api/why?entity_id=` | why the records resolved together |
| **How?** | `/api/how?entity_id=` | how the entity was constructed |

That set applies to: the Entity Graph node detail (in either mode), the merged-entity cards on
Search / Probe, the Merge Statistics bucket drill-down **and** its `sample_entities` list, the
Cross-Source cell drill-down, the Match Keys row drill-down, and Search / Probe results. Implement
it as **one shared renderer** invoked from every surface — the failure mode this prevents is real:
the buttons were added per-code-path, so each new entity surface silently shipped with a different
subset, and bootcampers reported the gaps one tab at a time.

**Drill-down on every aggregate view.** Every aggregate is clickable and opens the underlying
entities with the action set above: histogram bars (`bucket_entities`), Cross-Source cells
(`cell_entities`), Match Keys rows (`match_key_entities`). All three payloads share one entity
shape, so one drill-down renderer serves all three. An aggregate that shows a count but cannot be
opened is a dead end and is not acceptable.

**No redundant inline record listings.** Where an entity list offers the Records action, it MUST
NOT also print the constituent records inline (INV-221). The "Show all merged entities" cards on Search /
Probe show entity name, record count,
and match key plus the actions — nothing more. Showing the same records twice is clutter, and it
reads as unfinished once "click Records to see records" is the established pattern everywhere else.

> ⚠️ **Implementation pitfall — `onclick` + JSON serialization.** When building `onclick="..."`
> attributes by string concatenation, never embed serialized-JSON output (which is double-quoted)
> inside a double-quoted HTML attribute: the browser truncates the attribute at the first embedded
> quote and the handler silently never fires. This bug is easy to miss because calling the same
> function directly from the browser console works fine, which masks the failure. Escape the payload
> for the attribute context, or attach handlers programmatically instead of inlining them. This is
> language-agnostic front-end JavaScript, not a quirk of any one implementation.

Each Search / Probe result — searched or listed via "Show all merged entities" — carries **Why?**
and **How?** actions that call
`/api/why` and `/api/how` and render the explanation (match keys, feature scores, construction
steps) in a modal.

⛔ **(INV-330) How? when the final state is unsettled.** When either sign in the `/api/how` entry above is
present, the How explanation MUST show a visible **unsettled-state notice** that names the sign or
signs present with the values the response carries (only the one that fired, when only one did), and
MUST NOT claim one entity: no "built this entity in N step(s)" verdict and no "resolved directly into
one entity" sentence.

- **With steps:** the steps still render; the notice replaces the step-count verdict.
- **With no steps:** each element of `FINAL_STATE.VIRTUAL_ENTITIES[]` renders as **its own group** of
  records, never pooled into one list.
- **What the notice says:** only what the response shows. It gives `NEED_REEVALUATION` no meaning
  and offers no fix. Data-sourced text in the notice and the groups is escaped per "Escaping
  data-sourced strings" below.
- **With neither sign, or no `FINAL_STATE` in the response:** render as for any other entity, and
  assume nothing.

## Rendering contract

These are requirements, not suggestions. This module is the bootcamp's "wow moment" — the surface
whose whole purpose is a strong first impression — so the quality bar below is the **default every
implementation ships**, not something a bootcamper has to ask for one improvement at a time.

### Escaping data-sourced strings (required — security)

⛔ **Every string that reaches the page from the loaded data MUST be escaped for the context it is
written into.** Entity names, data-source codes, record IDs, match keys, resolution rules and feature
descriptions all originate in the Bootcamper's records, so none of them can be treated as trusted
markup. This is a **stored** injection surface, not a reflected one: the standalone snapshot is
saved, kept, and shared, so anything injected persists in the artifact the Bootcamper hands to
someone else.

Two contexts, two rules:

1. **Values embedded in an inline `<script>` block** — the snapshot inlines the whole entity model
   this way. Serializing with your language's plain JSON writer is **not sufficient**: JSON does not
   escape `<`, so a value containing the literal `</script>` closes the script element early and the
   browser parses what follows as markup. Escape `<`, `>` and `&` as their `\uXXXX` JSON escapes
   (`\u003c`, `\u003e`, `\u0026`) after serializing. The result is still valid JSON and the parsed
   data is byte-identical, so nothing downstream changes.
2. **Values written into rendered HTML** — entity cards, tooltips, legends, table cells, modal
   bodies. Escape `&`, `<` and `>` (and quotes in attribute position) before insertion, or use an
   API that treats the value as text rather than markup.

Live `/api/*` responses served as `application/json` are **exempt** — they are not an HTML-embed
surface.

*Reference implementation (Python):* `senzing_viz_server.py` provides `_script_json()` for case 1 and
`_esc_html()` for case 2 — the latter escapes `&`, `<`, `>` **and both quote characters**, so one
helper is safe in text and attribute position alike. Those are the names in the bundled reference,
**not** the requirement — implement the equivalent for your language (INV-090). ⛔ **Whatever you
implement, cover the quotes.** Until 2026-07-30 the reference escaped only the three, matching case 2's
text half while this very paragraph promised the attribute half: every call site happened to be a text
node, so nothing rendered wrong, and an implementer modeling the helper rather than the rule would
have inherited an attribute-position hole with no symptom to find it by (the INV-164 pattern — a
divergence between the reference and the written rule reaches generated code). A server that skips
this ships a stored-XSS vector in a shared keepsake, which is why it is a ⛔ and not a nicety
(INV-106).

### Offline rendering (required)

The live page and the standalone snapshot MUST both render with **no network access**: inline the
vendored D3 asset rather than fetching from a CDN, and embed every payload the snapshot needs. A
snapshot that reaches for a CDN is broken in exactly the air-gapped and proxy-restricted settings
where it matters most (INV-091). See `phase1-visualization.md` → "Render offline" for the vendored
asset's location.

⛔ **(INV-091) When the vendored asset is missing or unreadable, refuse to render.** The server MUST
fail visibly, with an error that names the missing asset (`d3.v7.min.js`), and MUST write no page or
snapshot. It MUST NOT fall back to the `d3js.org` CDN or any other network source for D3: a page that
loads D3 from the network is the broken snapshot this section describes, reached silently. The
bundled reference checks for the asset before any settings or engine work and exits non-zero;
implement the equivalent for your language (INV-090).

### Why? / How? — plain language first, raw JSON behind a twistie

The API returns the SDK response verbatim; that is about *availability*, not about what the UI
renders. Dumping `JSON.stringify` output into a `<pre>` block satisfies the letter of "verbatim"
and defeats the entire purpose of the feature, which exists to make Senzing's reasoning legible.

- **Why?** renders match level, match key, and resolution rule, then a per-feature table:
  feature · this record · compared-to record · score · bucket.
- **How?** renders a numbered, step-by-step merge narrative ("Step 1: record A from CUSTOMERS
  established the entity. Step 2: record B was added because …"), and an unsettled final state gets
  the notice described under "How? when the final state is unsettled" above.
- **Score buckets render as color-coded badges**, mapped from the buckets this contract already
  enumerates for `/api/features`: `SAME`/`CLOSE` → positive, `PLUS`/`LIKELY`/`PLAUSIBLE` → caution,
  `UNLIKELY`/`NO_CHANCE` → negative. Use `brand_tokens`' `SIGNAL_GREEN` for the positive bucket —
  that is exactly its reserved "resolved state" meaning (INV-081) — and define the caution and
  negative colors **once, as named constants in one place**, since the brand palette deliberately
  does not supply status colors. Never scatter hex literals through the render code.
  **Never rely on color alone** — keep the bucket name as text, so the badge survives a monochrome
  recap screenshot and is readable without color vision.
- **The raw SDK response stays available but collapsed**, behind a `<details>`/twistie that is
  closed by default. Available on demand; never the default view.
- Parse these responses against `get_sdk_reference(topic='response_schemas')`, never from the
  illustrative payloads above (INV-115). A summary view makes a wrong field name *harder* to spot,
  because it becomes a blank cell rather than visibly-absent JSON.

### Modal chrome

Entity-detail dialogs (Records / Why? / How?) are a primary "wow moment" surface and get the same
visual care as the headline tabs: a real header bar (title plus a close control) visually separated
from the body, deliberate spacing and typographic hierarchy, and a subtle entrance transition.
Palette and type come from `${PLUGIN_ROOT}/scripts/brand_tokens.py` (INV-081; skill-relative
fallback `../../scripts/brand_tokens.py`, INV-252) — the brand tokens apply *inside* the
modal, not only to the app shell. A functionally-correct but visually plain dialog undersells the
moment.

### Graph rendering — labels, scale, and legends

Applies to **Entity Graph** in both of its modes.

**Node colors follow "Coloring graph nodes" (INV-259)**, under "Server lifetime" below: what a node's
color is keyed on, how the palette is allocated, and what the legend names. The bullets here do not
restate it (INV-300).

- **Independent label toggles.** Separate show/hide controls for **node** (entity name) labels and
  **edge** (match key / relationship type) labels. Two independent dials, not one combined control,
  so a bootcamper can declutter for an overview pass or drill into detail without switching tabs.
- **Scale-dependent defaults.** Label visibility defaults by graph size, not to a fixed value: both
  label sets default **off above ~150 nodes** and on below it. State the threshold in the
  implementation so every language build behaves the same (INV-154 — a legibility default is a
  function of the rendered data's scale, and its threshold is stated as a number in this contract).
- **Say why they started off.** When labels default off, show a short inline note ("Labels hidden —
  3,986 entities; use the toggles above to show them"). Without it, a label-less graph reads as
  broken rather than as a deliberate default.
- **Legible labels when shown.** On-canvas node labels MUST avoid unreadable overlap — a
  collision/overlap-avoidance pass, truncation, or zoom-gated labels (INV-153 governs what any
  truncation you choose must preserve: no two rendered labels may be identical unless their values
  are, checked on the **fitted** strings). A hover-only tooltip does
  **not** satisfy this: the complaint it addresses is being unable to tell which records matched
  without hovering every node in turn.
- **Node labels are painted AFTER every node (required — INV-002/INV-090/INV-104).** Emit all node
  labels in their own layer, drawn after the whole node layer, so no node marker can ever paint over
  another node's text. ⛔ **(INV-002/INV-090/INV-104) The natural structure is the defective one:** binding one group per
  datum and appending marker-then-text inside it emits marker,text,marker,text — so a later node's
  marker covers an earlier node's label, and every string is still present in the DOM while glyphs
  are missing from the image. Observed on the **smallest possible graph, 2 entities**: an 18-character
  entity name rendered with its leading characters behind the neighboring marker. ⚠️ Offsetting a label by its
  own marker's size is necessary but **not** sufficient and was never the cause — a node does not
  occlude its own label; its neighbor does.
- **A screenshot MUST come from a CAPTURE-ORIENTED render, not the interactive one (required —
  INV-002/INV-090/INV-299).** Honor `?capture=1` by (a) driving the layout to completion
  **synchronously** — advance the physics in a loop rather than waiting on animation frames —
  (b) **fitting** the finished layout inside the viewport, and (c) **suppressing on-canvas labels**
  above a capture ceiling *lower* than the interactive one. ⛔ **(INV-299) All three, or none: each masks
  the next.** Measured 2026-09-03 on the 85-entity Truth Set — the animation path advanced **5 of the
  ~300 ticks** the layout needs at every budget from 5 s to 300 s, because a headless browser's
  virtual time does not advance animation frames; settling alone then pushed **most nodes
  off-canvas**, because centering bounds nothing; and fitting alone rendered a 10 px label at
  **2–3 px**. ⚠️ **Leave the interactive view alone** — a real browser advances animation frames
  normally, so a reader opening the app or the standalone snapshot already gets a settled layout,
  and applying the capture's label ceiling there would degrade a view they can zoom and toggle.
  ⚠️ **Suppress both label sets through your own auto-off mechanism**, not a bespoke hide on the
  name layer: the interactive ceiling governs entity names *and* match keys together, and reusing
  it keeps the on-screen toggles honest about what was actually drawn.
- **An animated view MUST expose a settled signal, and the capture MUST wait on it (required —
  INV-002/INV-090/INV-298).** Remove `data-graph-settled` from the document element when a layout
  **begins**, and set it to `1` when that layout has reached its **final positions** — immediately
  where there is nothing to lay out, so a waiter on an empty graph is never left waiting. A
  screenshot of an animated view is taken **after that signal**, never on a time budget alone, and
  a capture that proceeds without it MUST say so (INV-129). ⛔ **A deadline is not a settle
  guarantee, and a longer one is not a better guarantee.** Measured 2026-09-03 on the 85-entity
  Truth Set: five captures at a 30 s budget and five at 120 s produced the *same* image while five
  at 300 s produced **two**, and real time barely moved (0.6 s → 0.7 s) because virtual time
  advances as fast as the page allows. ⚠️ **Expose it as a DOM attribute, not a JavaScript
  variable.** The Python reference held its simulation in a top-level `let`, which never reaches
  `window`, so nothing outside the page's own script could observe it — an attribute is
  observable by any driver in any language, which is the whole point of putting the rule here.
- **Collision must account for the label's extent, not just the marker (required).** Size the
  collision/overlap pass from the rendered label as well as the marker, and apply it **only while
  labels are actually shown** — inflating it for text nobody renders over-separates a
  production-scale layout for no benefit. Measured on Senzing 4.4.0, 4 records → 2 entities,
  1440×900: with the marker alone the minimum distance from a marker to a *neighbor's* glyphs was
  **3 px**; accounting for label width it was **55.7 px** at the settled budget. ⚠️ Expect the
  layout to take longer to settle once labels influence it — verify at the budget your capture
  actually uses rather than assuming the pre-change settling time still applies.
- **Whatever hides labels must follow them into the new layer (required).** If labels default off
  above a node-count threshold, the mechanism that hides them MUST target the layer they are now
  in. A selector or predicate left pointing at the old per-node structure leaves every label
  rendered at exactly the scale the threshold exists for, and nothing fails loudly.
- **Legends are generated FROM the data, and filter it.** Build each legend from the values actually
  present in the rendered set — the `relationship_type` values on the drawn edges, the data sources
  on the drawn nodes. A legend entry can then never exist without matching marks, which is what
  makes "the legend shows three colors that appear nowhere in the graph" structurally impossible.
  Clicking a legend entry filters the view to that type/source and toggles back; show the active
  filter state and a per-entry count. Pair color with a non-color distinction (e.g. line style per
  relationship type) so the encoding survives a monochrome screenshot.
  - ⛔ **A legend count's LABEL is a claim about its denominator — name the denominator the code
    actually uses.** The per-source rows on the Entity Graph count **participation**: every entity
    drawing on that source, cross-source entities included. Label that block **"Entities per
    source:"**, never "Single-source:". The shipped reference carried the wrong label and the numbers
    were individually correct, which is why nothing caught it — on a two-source run the block read
    `CRM_CUSTOMERS 65` and `WEBSTORE_ACCOUNTS 70` against **121** entities of which **14** spanned
    both (`65 + 70 − 14 = 121`); the true single-source figures were 51 and 56, and every figure on
    screen agreed with every other, so the only wrong thing was the word above them.
  - ⛔ **Do not "fix" it by recomputing the counts.** The whole row is participation-shaped: the
    tooltip filters the *source*, the click handler keeps a node when **any** of its sources is still
    on, and the swatch is the per-source color while a cross-source entity is drawn in its own
    combination color. Recomputing to true single-source figures would agree with the label and
    disagree with all three — three changes to avoid one.
  - **State the overlap, because two adjacent blocks read as a partition.** With a combination block
    headed "entities in more than one source have their own color", the per-source block needs one
    clause saying an entity in several sources is counted in **each** of its sources' rows. Without
    it the pair reads as disjoint and the cross-source entities look double-counted or absent.
  - **Label the per-source block whether or not combination rows exist.** In the reference this
    heading sat inside the combinations branch, so it vanished on single-source runs — where the
    label is accidentally correct — and appeared only where participation and single-source diverge,
    which is exactly the run the module exists to demonstrate.
- **Data-source colors are ASSIGNED FROM the sources present, never from a name-keyed palette.**
  Build the source→color map at model-build time from the data-source codes actually loaded. A map
  keyed by source *name* is not acceptable: the shipped palette names the Truth Set's sources
  (`CUSTOMERS`, `REFERENCE`, `WATCHLIST`), and **no bootcamper uses those names for their own data,
  by definition** — so a name-keyed lookup drops every real source to one identical fallback color
  and reduces the payoff module's centerpiece to a monochrome hairball. It fails silently: a graph
  renders, just uninformative, and a bootcamper who did not build the server cannot tell a bad
  default from genuinely unclustered data.

  Requirements: Truth Set names keep their preferred assignment (so the Truth Set view is
  unchanged); every other source takes the next unclaimed palette entry, so two sources never
  collide; assignment is **deterministic** (sort the codes) so a rebuilt snapshot or a re-captured
  screenshot still matches the recap prose describing it; when there are more sources than palette
  entries, vary a second visual channel (e.g. node stroke) rather than silently reusing a color; and
  the reserved signal green is never assigned as a categorical color. The Python reference implements
  this as `brand_tokens.color_for_sources()`.

  ⛔ **Count the channels as RENDERED, not as assigned — the distinctness requirement (INV-127) is
  about what the browser draws.** Every draw site must key on a property that reaches the canvas. A
  wrap counter does not: it decides *whether* a second channel appears and *which* value it takes,
  and two sources with different counters can still be drawn identically. That is what happened in
  the Python reference — six fills × three stroke colors read as more than enough, the renderer
  applied a stroke only when the counter was non-zero, and the actual space was 6 × 4 = **24**
  rendered appearances. The returned map stayed collision-free at any size because each entry
  carried a distinct counter, so nothing looked wrong; the 25th source simply came out identical to
  the 7th, in the graph *and* in the legend.

  So, whatever channels you choose:

  - **Define the rendered key** — for a node that is `(fill, stroke when a stroke is actually drawn,
    stroke width, dash)` — and make it unique per present source. Test it at a size past your
    capacity, not just past the palette: a check at "palette + 3" passes on an encoding that
    collides at 25.
  - **The legend swatch and the mark MUST derive from the same expression**, so they cannot disagree
    about a source. Deriving them separately is how a legend ends up describing an appearance the
    graph does not have.
  - **State the capacity and do not exceed it silently.** An acknowledged ceiling with a warning is
    defensible; a silent collision is not. The Python reference reports its capacity as
    `brand_tokens.SOURCE_ENCODING_CAPACITY` (currently 210: six fills × seven rendered stroke states
    × five fill-lightness steps) and warns past it.
- **Init-state note.** An unchecked toggle fires no change event, so apply its render state
  explicitly at load — do not rely on the event handler to establish the initial view.

> **Scale principle (general).** Any default chosen while developing against the Truth Set MUST be
> reviewed for its behavior at 100× scale. Module 7 reuses this same app over the bootcamper's real
> data (`../module-07-query-visualize-discover/phase1-query-visualize.md`), which is usually far
> larger — a default tuned to 84 entities produced an unreadable hairball at 3,986, in the module
> meant to showcase results, and the bootcamper cannot tell a bad default from bad data.

### Search / Probe — pre-verified example queries

The Search / Probe tab MUST ship a small set of example queries as clickable chips that both fill
the search box **and** run the search on click. They are generated per-dataset from the loaded data
and **verified live to return at least one match** before being offered — a hint that returns
nothing is worse than no hint. Never present a bare search box: a bootcamper exploring a Truth Set
they did not build has no idea what a good demo query looks like, and a failed first search is a
poor first impression of the product.

⛔ **"Verified" means the query was actually run and returned a hit — not that it was derived from
real data.** Deriving a chip from a real merged entity's name is *not* verification: every chip
named after an **organization** was a real entity and still returned nothing, because search tried
`NAME_FULL` only (see `/api/search` above). So verify each candidate through **the same search path
the click will take**, keep only those that return at least one result, and drop the rest with a
reported reason (stderr for a build-time/snapshot example, `console.warn` for a live chip) — never
ship a chip that finds nothing. This check is also the cheapest guard against the search defect
returning: a chip that stops matching is a search regression announcing itself.

**Distinguish "no data returned" from "rendered empty" (INV-115).** Where the UI renders a parsed
field — a feature-score table, a match key, a resolution step — an absent or blank value MUST be
labeled as such ("no feature scores returned for this entity"), never rendered as an empty row,
empty cell, or bare punctuation. A wrong field name and genuinely empty data look identical
otherwise, and the wrong-field case is the far likelier of the two. This is what makes the failure
visible to whoever is looking at the screen; it is the defense that survives a future field rename,
and it matters more once a plain-language summary replaces the raw JSON, because a mis-named field
becomes a blank cell rather than visibly-absent JSON. The Merge Statistics histogram bars are clickable (driven by `bucket_entities`),
listing the entities in each bucket and linking each to its **How?** explanation.

**Static snapshot degradation:** the standalone snapshot has no live backend, so `why`/`how` and
live `search` are unavailable there — those actions show a note directing the viewer to the live
server. Everything else renders **offline** because the snapshot embeds `stats`, `graph`, `merges`,
`records`, `overlap`, `matchkeys`, and `features` — so the Entity Graph (both modes, since the
relationship subgraph is filtered from the same embedded `graph` payload), Merge Statistics (with
bucket drill-down and the largest-entities list), Match Keys (with row drill-down), Feature Scores,
and Cross-Source (with cell drill-down) tabs all work with no network access. `merges` stays embedded
because Search / Probe's "Show all merged entities" browse reads it, so **that browse works offline**
— which is what keeps the removed Record Merges tab's no-query capability available in the keepsake,
not only in the live app. The snapshot's Search / Probe body MUST therefore include the
`#probe-btns` container even though it has no live search box; without it the browse has nowhere to
render and the snapshot silently loses the capability. The example-query **chips** are live-only by
design — they drive the search box, which a static file does not have — so they are suppressed
there rather than shipped as dead controls. **The Records action works offline too**, because `records` is embedded: it needs no
engine call at view time, unlike `why`/`how`. The Feature Scores tab shows whatever was computed
(capped) at build time. (`dashboard` is no longer embedded — the endpoint was removed and its
content folded into `stats`.)

**Error response (all endpoints):** HTTP 500 with `{"error": "<description>"}` on SDK failure.
Exception: `why`/`how` return a `200` with an `error` field per the shapes above so one entity's
failure never breaks the tab.

## Server lifetime (required in every module that starts one)

⛔ **A visualization server, once started, stays up until the bootcamper has explicitly approved
teardown.** Agent-side verification — API probes, endpoint checks, screenshot capture for the recap
— is a *preliminary* step that runs **while the server keeps running**. It is never the end of the
interaction, and it MUST NOT stop the server. The bootcamper explores *after* the agent verifies,
not instead of it.

INV-131 governs the ordering half: irreversible teardown is the module's **last** action, after
every step that needs the running service — endpoint verification and live-server screenshot
capture are named in it. The explicit-approval half is the teardown gate below, pinned per INV-056.

The sequence in every module that starts a server is therefore:

1. Start the server and verify it (agent-side; server stays up).
2. Hand the URL to the bootcamper and let them explore at their own pace.
3. Ask the teardown gate below, and only then clean up.

⛔ **(INV-001, INV-002) On macOS, start the server as a DIRECT CHILD of the shell that sourced the
env script — never through `nohup`, `env`, or a nested `bash -c`.** macOS System Integrity Protection strips `DYLD_*`
out of the environment whenever a **protected** binary execs a child, and `/usr/bin/nohup`,
`/usr/bin/env` and `/bin/bash` are all protected. The variable is set correctly in the parent shell
and simply does not survive the wrapper. Demonstrated on Darwin 25.5.0 arm64, 2026-08-25
(environment observation, INV-080/INV-149):

```text
$ echo $DYLD_LIBRARY_PATH              -> /opt/homebrew/opt/senzing/er/lib:...
$ bash -c 'echo $DYLD_LIBRARY_PATH'    -> (empty)
$ nohup bash -c '...'                  -> (empty)
```

- ⚠️ **The symptom points away from the cause.** It surfaces as
  `java.lang.UnsatisfiedLinkError: no Sz in java.library.path` from a **backgrounded** process whose
  parent shell has the variable set — so the obvious response is to add `-Djava.library.path=…`,
  **which does not fix it**. `../module-02-sdk-setup/SKILL.md` → "MCP Java scaffolds may need a JSON
  library the install does not provide" states why a JVM flag cannot repair a dynamic-linker search
  path after the process has started; follow it there rather than re-deriving it (INV-183, INV-300).
- ⚠️ **Foreground programs work throughout, which is what makes this confusing.** They are direct
  children of the shell that exported the variable, so nothing is stripped. The failure appears only
  when a process is backgrounded or wrapped — exactly what starting a server is.
- ⚠️ **Silent on Linux and Windows**, where `DYLD_*` does not exist. That is why it is stated here,
  in the contract every platform reads, rather than behind a macOS branch a Linux reader skips
  (INV-001). The JVM error above is illustration; the rule is about the launcher, not the language
  (INV-002).

### Coloring graph nodes (required — behavior, in every language, INV-259)

⛔ **A node is colored by its whole source set — never by one member of it (INV-259).** The key is the
entity's data sources, sorted and joined (`GLEIF|LEI`, not `GLEIF`), so a cross-source entity is
visually distinct from every single-source entity. **Fill, stroke and stroke width all derive from
that key**; leaving any one of the three reading the first source keeps a partial version of the
same misencoding.

⚠️ **Where an entity has one source the key degenerates to that source code**, so single-source
entities are unchanged. That is the compatibility guarantee — and it is why this defect survived:
on the Truth Set most entities sit in one source, so "first source" *is* the entity's source and
the encoding looks correct at that scale.

**The failure it prevents:** a real run rendered **1,951 cross-source entities in the single-source
`GLEIF` color**, with a legend implying they were GLEIF-only. Nothing looked broken — the graph
drew, the legend populated, every count was right, and the headline result of the bootcamp was
invisible in the tab built to show it.

⛔ **The palette MUST be allocated in a single pass over the full key set** (INV-259) — every source and every
combination together, one call. Two calls each restart at the top of the palette and reproduce the
collision this fixes; that is the error made while repairing it by hand, not a hypothetical.

**The legend MUST name each combination** it colors (INV-259), labeled as a combination and counted over the
nodes actually drawn. A color a viewer cannot name is not an improvement over the wrong color.

#### The encoding self-check (required — behavior, in every language)

⛔ **(INV-270) The graph endpoint MUST expose a self-check, and the build step MUST run it before capture.**
The rule above is stated three times across this bootcamp and was still re-implemented wrong in a
generated Java app on 2026-08-25 — colored from `data_sources[0]`, with 294 of 5,619 cross-source
entities rendered as single-source. Prose did not prevent that. A check that fails will.

**What to expose.** Alongside `total` and `capped`, the graph payload carries the number of distinct
**sorted source-set keys** over the nodes it emits — the same keys the client computes to color them:

```text
encoding_check: {
  distinct_source_set_keys: <int>,     # distinct sorted, joined source sets over emitted nodes
  source_set_keys: [<string>, …],      # e.g. ["CUSTOMERS", "CUSTOMERS|REFERENCE", "WATCHLIST"]
  combination_keys: [<string>, …],     # the subset containing the join separator
  status: "ok" | "not_exercised",
  detail: <string>
}
```

**What to verify.** The number of **combination rows the legend names** — one per multi-source
color — MUST equal `len(combination_keys)`. That equality is false exactly when a node is colored by
one member of its set: first-source coloring collapses every combination onto a single-source key,
so the legend names **0** combination rows against **N** combination keys. Both numbers are already
computed in order to draw the graph, so the check costs nothing. Read it off the **source** legend —
the relationship legend has no source-color rows, so counting it compares the wrong thing.

⛔ **Count combination rows only, never every legend row (INV-270, corrected 2026-09-25).** The
legend also names one per-source row per source, counting every entity that source participates
in. Those rows are not source-set keys, so the legend's total exceeds `distinct_source_set_keys`
whenever a source appears in view only inside combinations — routine once the node cap cuts a
source's unrelated single-source entities. Observed on a Bootcamper's data: 9,820 entities capped to
1,500, `OFAC`'s 4 single-source entities cut, 8 source-set keys against 9 legend rows, every node
correctly colored. Comparing totals there stops a correct capture.

⚠️ **No combination key in view means the check was NOT exercised — report that, never "passed"
(INV-265).** With no cross-source entity among the emitted nodes — one registered data source, or
several that share no entity — the comparison cannot fail, and reporting a pass would be reporting
agreement from a match that could not disagree. Say "not exercised — no cross-source entity in view"
and move on.

⛔ **That is NOT the Truth Set's case — this module is a genuine test site for INV-259.** The Truth
Set registers **three** data sources and resolves entities spanning them, so the comparison is live
here and a real `ok`/mismatch verdict is what this module should produce
(`get_sample_data(dataset='truthset', source='list')` → CUSTOMERS, REFERENCE, WATCHLIST, 159
records; server 1.33.0, 2026-08-28). A `not_exercised` result **in this module is itself a signal** —
fewer sources loaded than expected — not a routine outcome to move past. The single-source case
belongs to System verification's synthetic `VERIFY` data, and to a bootcamper who loads exactly one
source. ⚠️ Observation, not a server fact: one full 159-record load on 2026-08-27 emitted **7**
distinct source-set keys, **4** of them combinations, over 84 entities — first-source coloring would
have collapsed those four and left the legend naming 0 combination rows against 4, which is the
mismatch this check exists to catch.

⛔ **On a mismatch, stop and fix the encoding before capturing screenshots (INV-259).** The screenshots become
a permanent keepsake in the recap and the production project; capturing first means shipping the
wrong picture and discovering it afterwards, which is what happened.

### The graph payload is bounded, and says so (required)

The graph endpoint MUST cap the nodes it emits and carry **`total`**, whether a cap was applied
(**`capped`**), and **`related_total`** — the distinct endpoints of every edge in the whole datastore,
counted before the cap — so the UI can state what it is showing rather than implying it is
everything. The capped note wording is in "Defaults at production scale" item 3. Rank candidates by
**source span first** — entities spanning most sources are the ones worth seeing — then by
connectivity, then deterministically, so a re-rendered snapshot does not disagree with the recap
prose describing it. ⚠️ This is about the **size and portability** of the payload and the
self-contained snapshot, which embeds it whole; the *legibility* half is already handled by the
scale-aware subgraph default below, and the client filtering what it draws does not bound what the
server ships.

### Binding the port (required — behavior, in every language, INV-260)

⛔ **Bind the LOOPBACK interface explicitly — `127.0.0.1` — never the wildcard address (INV-260).** In Java
that is `new InetSocketAddress("127.0.0.1", port)`, not `new InetSocketAddress(port)`; in Node
`server.listen(port, "127.0.0.1")`; in C# a loopback `IPAddress.Loopback` endpoint. The idiomatic
one-argument form in most languages is a **wildcard** bind, so this is the rule an otherwise faithful
port of the reference will get wrong by writing the shorter thing.

⚠️ **The reason is not tidiness, and an implementer who "simplifies" it back reintroduces a defect
that cannot be seen.** A wildcard bind does **not** collide with an existing loopback listener on the
same port — both binds succeed, two processes listen on one port, and either may answer a localhost
request. Observed on macOS, 2026-08-17: a three-week-old `VizServer` from an unrelated project held
`127.0.0.1:8080`, the bootcamp's server bound `*:8080` successfully, and the first `/api/stats` probe
happened to reach the new one. Had the browser reached the other, the Bootcamper would have been
shown **a stranger's dataset under their own project's title**, with every number on the page
someone else's and the keepsake screenshots capturing it. A loopback bind is also the correct
security posture for a server holding the Bootcamper's resolved data — a second reason not to leave
it to the language's default.

⛔ **A successful bind is NOT proof the port was free (INV-260).** Any guidance that treats a port conflict as
a *bind failure* is describing only one of the two cases. A failure stops the step; this succeeds and
produces nondeterministic results, which is strictly worse.

### Confirming the server that answers is yours (required — INV-260)

⛔ **After binding and before handing the URL to the Bootcamper, probe `/api/stats` and confirm the
responder is the server just started (INV-260).** Mint a **nonce** at startup — any value unique to this
process — expose it on `/api/stats`, and compare. ⚠️ **Compare the nonce, not the record count:** two
runs of the same project agree on record count, so a count check passes in exactly the case where a
stale listener is most likely to be the Bootcamper's own earlier server.

**On disagreement, STOP and report the conflict** — the port, and both servers' identifying figures —
and do not hand over the URL. ⛔ It must not degrade to a warning printed above a working-looking
link: the entire failure mode is that everything looks fine, so a message the Bootcamper scrolls past
is the same as no message.

⚠️ **The probe is required even though the bind rule above is followed, because they cover opposite
directions.** A loopback bind makes a colliding *loopback* listener fail cleanly; it does nothing
when the pre-existing listener is itself **wildcard**-bound — then your loopback bind is the one that
succeeds alongside it. Only asking which server answered covers both. Socket coexistence rules differ
across platforms, so the probe, not the bind, is what must hold on Linux, macOS and Windows alike.

### Identifying the server process (required)

⛔ **Capture the server's process id at launch and record it in the checkpoint beside the port.**
(INV-223.) A server that can be started but not *named* can only be stopped by guessing, and every
guess available is worse than the handle you threw away. Recording it costs one variable at launch:

| Shell | Handle |
|---|---|
| POSIX shells (Linux, macOS, Git Bash, WSL) | `$!` immediately after backgrounding with `&` |
| PowerShell (Windows) | `$proc = Start-Process … -PassThru`, then `$proc.Id` |

⛔ **In a POSIX shell, `$!` names the server only when the server is the *sole* backgrounded
command on its line.** Written `A && B &` — the shape any prerequisite invites, and this bootcamp
requires the project env sourced before anything that touches the Senzing library — the `&` binds
to the whole `&&` list: the shell backgrounds a **subshell**, `$!` is that subshell, and the server
is its child with a different pid. Source the env as its own statement, then background only the
server. Measured on bash: composed with `&&`, `kill <recorded pid>` exits 0, the subshell dies, and
the port stays bound by the still-running server. PowerShell is unaffected — `-PassThru` returns
the process object, not a shell job.

The port is already recorded (INV-172) — record the pid in the same checkpoint object, so a resumed
session can still stop what a previous one started.

⛔ **Never identify the server by matching its command line — `pkill -f <script name>` and its
equivalents are unsafe here.** The pattern you match on appears in the *matching command's own*
command line, so the kill signals the shell that issued it. Observed on a dry run 2026-08-13: `pkill
-f senzing_viz_server.py` terminated the invoking shell with exit code 144 part-way through
teardown, leaving the records still loaded and the purge unrun — and the failure presented as the
purge crashing, not as the kill hitting the wrong target. A name-based match is also wrong in
principle for this bootcamp: the server is written in the Bootcamper's chosen language (INV-090), so
there is no script name to match on in general, and a second bootcamp running in another directory
would match too.

**Terminate by pid; fall back to the port, never to the name.** The fallback covers **two** cases,
and only the first is obvious: the recorded pid is *missing* (a session resumed across the change, or
a server someone else started), or the recorded pid is *wrong* — it terminated successfully and the
port is still bound. A wrong pid is the worse of the two precisely because it presents as presence:
nothing looks like it needs a fallback. ⛔ **So the exit condition is the port, never the kill's
status** — poll the port after signaling, and if it still answers, run the port lookup as though no
pid had been recorded at all. Look the listener up by the
port that *is* recorded: `lsof -ti:<port>` (Linux/macOS) or `Get-NetTCPConnection -LocalPort <port> |
Select-Object -ExpandProperty OwningProcess` (PowerShell). The port is bound by exactly the process
serving it, which is the property the command line lacks.

⛔ **On the `docker` path both routes above are host-shell routes, and the container has neither
tool — while the command-line match stays forbidden for its own reason, unsoftened by any tool
being absent.** The bootcamp's own container follows the `linux_apt` steps inside a Debian slim
image (`module-02-sdk-setup/SKILL.md` → the `docker` path), which ships no `procps` and no `lsof`,
so every process-identification binary those routes reach for is **never** present inside it, and
MUST NOT be reached for there — `ps`, `pkill` and `lsof` alike. A run that reached for the forbidden match in a container got
`exec: "…": executable file not found in $PATH`, and **the Bootcamper had already been told the
server would be stopped while it kept serving** — found only when the port was probed and still
answered 200. Two faults are live at once: the wrong identification route, and no tool to run it
with. Fixing only the second would leave a working command that signals the invoking shell.

Use the two things a Debian slim container is guaranteed to have — a POSIX shell, and the `python3`
the SDK install brings in:

- **Record the pid from inside the container, and know which namespace it belongs to.** A server
  started with `docker exec <container> …` yields a **container-namespace** pid, which is the only
  kind `docker exec … kill` can signal; a host pid from `docker run` identifies the *container*, not
  the server inside it, and signaling it stops the whole container. Capture the pid in the same
  namespace the teardown will signal in, and record which one it is beside the port (INV-223 requires
  the pid and port in one checkpoint object; this says the pid needs its namespace to be usable).
- **Signal the recorded pid through the shell's builtin**, not through a `kill` binary:
  `docker exec <container> sh -c 'kill <pid>'`. `kill` is a shell builtin, so this needs no
  `procps`; `/bin/kill` is a `procps` binary and is not there. The pid is the one INV-223 requires
  the launch to have recorded.
- **Probe the port with `python3`**, since `lsof` is absent: a short `socket` connect against the
  port, run with `docker exec <container> python3 -c …`. `python3` is present because the SDK
  install put it there, and this is the same probe the host path makes with `lsof` — the same
  question asked by the only tool available.

⚠️ **`procps` is deliberately NOT added to the container build.** It would be a package installed
into the Bootcamper's image for the convenience of one teardown step, when the shell builtin and
`python3` already answer both questions — and every package added to that image is one more thing
that can fail during Module 2's install phase, which is the module with the most ways to go wrong
already. If a later change needs `ps` output for its own reasons, that is the change that should
argue for the package.

**Never treat the kill's own exit status as evidence the server stopped.** `docker exec … kill`
reports whether the *signal was delivered*, not whether the process died and released the port — a
server mid-request can take the signal and keep the socket briefly, and a wrong pid exits non-zero
for a reason that looks identical to a server that was never running. This is the same
verify-the-artifact-not-the-exit-code discipline INV-129 requires of a rendered deliverable and
INV-218 requires of an install, applied to a process: **the port answering or not answering is the
observation; the exit code is not.**

**Confirm the port is free before continuing, rather than waiting a fixed interval.** Poll the port
until nothing is listening, up to 5 seconds; then force-stop and re-check. Treat *the port being
free* as the exit condition — a sleep asserts nothing, and any step that follows teardown (a data
purge above all) then runs on an assumption instead of an observation.

**When teardown cannot confirm, say so plainly and do not claim the server stopped.** If the port
still answers after the force-stop and re-check, tell the Bootcamper exactly that — the port, that
something is still listening on it, and that the records may still be loaded — then continue without
the purge rather than purging on an unverified stop. ⛔ **A teardown that reports success while the
port answers is worse than one that reports failure (INV-223).** the Bootcamper walks away believing their
machine is clean, and INV-131 makes teardown the last action of the module, so nothing downstream
will notice. Where the container is the host for the server, name the `docker exec` form that was
tried, so the Bootcamper can see what was attempted rather than only that it failed (INV-111).

**The teardown gate.** Before stopping the server — and before any data purge that accompanies it —
ask a pinned question (INV-056) and end the turn on it. The gate MUST name **exactly** what is
about to happen in that module and nothing more, because the consequences differ.

⛔ **First, state what they are consenting to — this precedes the question, never follows it**
(`../bootcamp-onboarding/ground-rules.md` → anything meant to inform the answer goes before the 👉;
nothing may follow it, since it ends the turn). Say that the live URL goes dead, and that the
standalone snapshot preserves every tab rendering from embedded data but **not** the live
`why`/`how`/`search` actions, which need the running engine (see "Static snapshot degradation"
above). **A yes given without that is not an informed yes** — and here the consent authorizes an
irreversible teardown, so a disclosure arriving after the answer is worth nothing at all.

Then ask the gate that matches the module:

- Where teardown stops the server **and** removes data (Truth Set visualization, whose records are
  scaffolding): say both. → 👉 **Ready for me to stop the visualization server and clean up the Truth Set data?**
- Where teardown stops **only** the server (any module pointed at the bootcamper's own loaded data):
  say only that, and say the data stays. → 👉 **Ready for me to stop the visualization server?**

⛔ Never ask a vague "and clean up" in a module that has no purge — the bootcamper's own loaded
data is needed downstream (recap, graduation), and a gate that sounds like it authorizes deleting it
either frightens them or licenses a destructive step the module never intended.

⛔ **This is not an INV-006 violation.** INV-006 forbids re-asking *the same* question. An earlier
"are you ready to continue?" or "done with the tour?" asks whether the bootcamper is ready to move
on in the module; this asks whether an **irreversible** action may proceed. They are different
questions with different consequences, and the second MUST be asked on its own. Never cite INV-006
as a reason to skip it.

**On "no" or "not yet":** acknowledge, leave the server running, and continue with whatever comes
next. Do not re-ask on a loop — INV-006 *does* apply to this gate — and proceed with teardown when
the bootcamper says they are done.

**Never design the flow so a restart request is the normal path.** Restarting on request is fine,
but a bootcamper should not have to ask for a server to come back that they never agreed to stop.
(This mirrors the Docker container lifecycle handling: containers are stopped, not removed, and are
surfaced on resume — the same principle that a bootcamper never loses access to something they were
using.)

## search_builder.py: Entity Enrichment Specification

The `search_builder.py` module SHALL implement the following enrichment behavior:

**Enrichment flow:**

1. Call `search_by_attributes` with the query parameters to get matching entities.
2. For each matched entity (up to a maximum of 10), call `get_entity_by_entity_id` to retrieve
   full resolution detail.
3. Extract match keys, feature scores, and resolution rules from the entity detail response.
4. Return enriched results combining basic search info with resolution reasoning.

**Enrichment cap:** enrichment is capped at 10 entities maximum. If a search returns more than 10
matching entities, only the first 10 are enriched with resolution detail. Remaining entities
(positions 11+) are returned as basic search results with null values for `match_keys`,
`feature_scores`, and `resolution_rules`.

**Extraction functions:**

| Function | Input | Output |
|----------|-------|--------|
| `_extract_match_keys(entity_detail)` | Full entity detail JSON | `{"entity_level": "+NAME+DOB", "per_record": ["+NAME+DOB", "+PHONE"]}`: entity-level match key string + list of per-record match key strings |
| `_extract_feature_scores(search_match_info)` | Search match comparison info | `[{"feature": "NAME", "score": 97, "label": "CLOSE"}, ...]`: feature name, numeric percentage (0-100), classification label |
| `_extract_resolution_rules(entity_detail)` | Full entity detail JSON | `[{"data_source": "CUSTOMERS", "record_id": "1001", "rule": "CNAME_CFF_CEXCL"}, ...]`: per-record data source, record ID, and resolution rule string |

**Graceful degradation:** if `get_entity_by_entity_id` raises any exception for a specific
entity, the search builder SHALL return the basic search result for that entity with:

- `match_keys`: null
- `feature_scores`: null
- `resolution_rules`: null
- `enrichment_error`: a non-empty string containing the exception type and message (e.g.,
  `"SzError: Entity 5 not found in repository"`)

One entity's enrichment failure SHALL NOT prevent enrichment of the remaining entities.
