"""A standalone snapshot offers an entity, then answers "no such entity" for its Records.

The snapshot embeds `graph` **capped** at ``GRAPH_NODE_CAP`` (1500) and embeds `merges` and
every aggregate drill-down list on their own terms. The Records shim indexed
``__DATA__.graph.nodes`` and nothing else, so an entity the page itself still offered — through
the "Show all merged entities" browse, a histogram bucket, a cross-source cell, a match-key row
or the largest-entities list — came back as
``{"entity_id": "1501", "error": "not found: no such entity"}`` whenever the cap had dropped
its node. Browsable and then denied, with no cap stated anywhere in the denial (#675).

⚠️ **The Truth Set (84 entities) never reaches the cap**, so no Module 3b walk can see this; it
appears only on a bootcamper's own data in Module 7. Hence a fixture built past the cap on
purpose, with entities that are reachable through each retained surface *and* ranked out of the
graph payload.

What is pinned:

* Every entity a retained snapshot surface offers resolves offline, whether or not the graph
  cap kept its node — the records index is built from that whole census, not from `graph.nodes`.
* The caps themselves are unchanged: the graph still renders at most ``GRAPH_NODE_CAP`` nodes
  and says it is capped, and the 200-per-list aggregate caps and their flags still hold. The
  repair is to the lookup denominator, never to what is shown.
* No record array is embedded twice: the index carries only entities whose records no other
  embedded surface already carries.
* The live-only `why` / `how` / `search` disclosures are untouched.

The lookup is exercised by **transcribing the shipped shim** into ``resolve()`` below rather
than running a browser or a JS engine: the guarantee is which surfaces the index is built from,
and neither is available on every machine that runs this suite (INV-052/INV-066).
``TheShimIndexesEveryRetainedSurface`` pins the transcription against the shipped source, so the
two cannot drift apart silently.

Run:  python3 -m unittest discover -s tools/bootcamp-transform/tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"
CONTRACT = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
    / "module-03b-truthset-visualization" / "visualization-api-reference.md"
)


def load():
    spec = importlib.util.spec_from_file_location("viz_records_index_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_records_index_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load()
SOURCE = SERVER.read_text(encoding="utf-8")

#: The entities placed past the cap, and the retained surface each one is reachable through.
#: Every one of them is ranked out of the graph payload (single source, or fewer records than
#: the entities that fill the cap), which is precisely the case the old index could not answer.
BEYOND_THE_CAP = {
    1501: 'the "Show all merged entities" browse, and the largest-entities list',
    1502: "the records-per-entity histogram's 1-record bucket",
    1503: "the +SSN match-key row",
    1504: "the Cross-Source diagonal cell for source C",
    1505: "the Cross-Source A x C cell",
}


def record(data_source, record_id, match_key=""):
    return {"data_source": data_source, "record_id": record_id, "match_key": match_key}


def entity(entity_id, sources, records):
    return {
        "entity_id": entity_id,
        "entity_name": "Entity %d" % entity_id,
        "record_count": len(records),
        "data_sources": sorted(set(sources)),
        "records": records,
    }


def model_past_the_cap():
    """A model with ``GRAPH_NODE_CAP`` + 5 entities, the five ranked out of the graph."""
    model = VIZ.Model()
    for i in range(1, VIZ.GRAPH_NODE_CAP + 1):
        # Two sources and two records, so these fill the cap: graph() ranks by source span
        # first, then connectivity, then record count.
        model.entities[i] = entity(
            i, ["A", "B"], [record("A", "a%d" % i), record("B", "b%d" % i, "+NAME+ADDRESS")]
        )
    model.entities[1501] = entity(
        1501, ["A"],
        [record("A", "m1"), record("A", "m2", "+NAME"), record("A", "m3", "+NAME")],
    )
    model.entities[1502] = entity(1502, ["A"], [record("A", "s1")])
    model.entities[1503] = entity(1503, ["A"], [record("A", "k1", "+SSN")])
    model.entities[1504] = entity(1504, ["C"], [record("C", "c1")])
    model.entities[1505] = entity(1505, ["A", "C"], [record("C", "x1")])
    model.records_total = sum(e["record_count"] for e in model.entities.values())
    return model


# --- transcription of the shipped shim -----------------------------------------------------

#: The payload paths ``__recordsFor`` folds into ``__RECS__``, in the order it folds them.
#: Pinned against the shipped source by TheShimIndexesEveryRetainedSurface.
SHIM_SOURCES = (("graph", "nodes"), ("merges", "entities"), ("records_index",))


def resolve(payload, entity_id):
    """`__recordsFor(id)` in Python: index every shim source, then look the id up."""
    index = {}
    for path in SHIM_SOURCES:
        value = payload
        for key in path:
            value = (value or {}).get(key)
        for node in value or []:
            if node.get("entity_id") is None:
                continue
            index[str(node["entity_id"])] = {
                "entity_id": node["entity_id"],
                "entity_name": node.get("entity_name"),
                "records": node.get("records") or [],
            }
    return index.get(
        str(entity_id), {"entity_id": entity_id, "error": "not found: no such entity"}
    )


class TheFixtureExceedsTheGraphNodeCap(unittest.TestCase):
    """Without this the rest of the file proves nothing: the defect needs a dropped node."""

    @classmethod
    def setUpClass(cls):
        cls.model = model_past_the_cap()
        cls.payload = VIZ._snapshot_payload(cls.model)
        cls.node_ids = {n["entity_id"] for n in cls.payload["graph"]["nodes"]}

    def test_the_graph_payload_is_capped(self):
        self.assertTrue(self.payload["graph"]["capped"])
        self.assertEqual(VIZ.GRAPH_NODE_CAP, len(self.payload["graph"]["nodes"]))
        self.assertEqual(len(self.model.entities), self.payload["graph"]["total"])

    def test_the_entities_under_test_are_absent_from_the_graph(self):
        for eid, where in BEYOND_THE_CAP.items():
            with self.subTest(entity=eid, reachable_through=where):
                self.assertNotIn(eid, self.node_ids)

    def test_each_one_is_still_offered_by_a_retained_surface(self):
        reachable = VIZ._snapshot_reachable_entity_ids(self.payload)
        for eid, where in BEYOND_THE_CAP.items():
            with self.subTest(entity=eid, reachable_through=where):
                self.assertIn(eid, reachable)


class RecordsResolveBeyondTheCap(unittest.TestCase):
    """The acceptance criterion: a reachable entity omitted from graph.nodes has records."""

    @classmethod
    def setUpClass(cls):
        cls.model = model_past_the_cap()
        cls.payload = VIZ._snapshot_payload(cls.model)

    def test_every_entity_past_the_cap_resolves(self):
        for eid, where in BEYOND_THE_CAP.items():
            with self.subTest(entity=eid, reachable_through=where):
                answer = resolve(self.payload, eid)
                self.assertNotIn("error", answer)
                self.assertEqual(
                    self.model.entities[eid]["records"], answer["records"]
                )
                self.assertEqual(self.model.entities[eid]["entity_name"], answer["entity_name"])

    def test_the_merge_browse_resolves_the_whole_merges_payload(self):
        """"Show all merged entities" lists every multi-record entity, uncapped."""
        for ent in self.payload["merges"]["entities"]:
            answer = resolve(self.payload, ent["entity_id"])
            self.assertNotIn("error", answer, "merge browsing offered %s" % ent["entity_id"])

    def test_every_aggregate_drill_down_resolves(self):
        stats, overlap, mk = (
            self.payload["stats"], self.payload["overlap"], self.payload["matchkeys"]
        )
        drilldowns = {
            "bucket_entities": stats["bucket_entities"],
            "cell_entities": overlap["cell_entities"],
            "match_key_entities": mk["match_key_entities"],
        }
        for surface, lists in drilldowns.items():
            for key, entities in lists.items():
                for ent in entities:
                    with self.subTest(surface=surface, key=key, entity=ent["entity_id"]):
                        self.assertNotIn("error", resolve(self.payload, ent["entity_id"]))
        for ent in stats["sample_entities"]:
            with self.subTest(surface="sample_entities", entity=ent["entity_id"]):
                self.assertNotIn("error", resolve(self.payload, ent["entity_id"]))

    def test_every_reachable_entity_resolves(self):
        unresolved = sorted(
            eid for eid in VIZ._snapshot_reachable_entity_ids(self.payload)
            if resolve(self.payload, eid).get("error")
        )
        self.assertEqual([], unresolved)

    def test_an_entity_no_surface_offers_is_still_reported_as_not_found(self):
        """Honesty in the other direction: the index is not a license to invent entities."""
        answer = resolve(self.payload, 999999)
        self.assertEqual("not found: no such entity", answer["error"])

    def test_without_the_index_the_defect_returns(self):
        """Negative control: the index, not the fixture, is what repairs the lookup."""
        graph_only = dict(self.payload, records_index=[])
        denied = sorted(
            eid for eid in BEYOND_THE_CAP
            if resolve(graph_only, eid).get("error") == "not found: no such entity"
        )
        # 1501 is carried by `merges`, which the old shim also ignored; the four aggregate-only
        # entities are the ones only the index can answer.
        self.assertEqual([1502, 1503, 1504, 1505], denied)


class TheShimIndexesEveryRetainedSurface(unittest.TestCase):
    """Pins `resolve()` above against the shim the snapshot actually ships."""

    @classmethod
    def setUpClass(cls):
        body = SOURCE[SOURCE.index('"function __recordsFor(id){'):]
        cls.body = body[: body.index('"window.fetch=function(u)')]

    def test_it_folds_in_exactly_the_transcribed_sources(self):
        folded = re.findall(r"__DATA__\.(\w+)(?:\|\|\{\}\)\.(\w+))?", self.body)
        self.assertEqual(
            [tuple(part for part in pair if part) for pair in folded], list(SHIM_SOURCES)
        )

    def test_each_source_is_indexed_by_the_one_adder(self):
        self.assertEqual(len(SHIM_SOURCES), self.body.count(".forEach(add);"))

    def test_an_unknown_id_still_answers_not_found(self):
        self.assertIn("error:'not found: no such entity'", self.body)

    def test_the_graph_is_no_longer_the_only_source(self):
        """The shape of the defect: one surface indexed, several surfaces offered."""
        self.assertIn("__DATA__.merges", self.body)
        self.assertIn("__DATA__.records_index", self.body)


class TheCapsAreRetained(unittest.TestCase):
    """The repair is to the lookup, never to what the snapshot shows or claims."""

    @classmethod
    def setUpClass(cls):
        cls.model = model_past_the_cap()
        cls.payload = VIZ._snapshot_payload(cls.model)

    def test_the_graph_still_renders_at_most_the_cap(self):
        self.assertEqual(VIZ.GRAPH_NODE_CAP, len(self.payload["graph"]["nodes"]))
        self.assertTrue(self.payload["graph"]["capped"])

    def test_the_aggregate_lists_still_cap_and_still_say_so(self):
        self.assertEqual(200, len(self.payload["stats"]["bucket_entities"]["2"]))
        self.assertEqual(VIZ.GRAPH_NODE_CAP, self.payload["stats"]["histogram"]["2"])
        self.assertTrue(self.payload["overlap"]["cell_capped"])
        self.assertTrue(self.payload["matchkeys"]["entities_capped"])

    def test_no_browsable_entity_was_removed_to_reach_the_fix(self):
        """The forbidden shortcut: shrinking the surfaces until the lookup agrees."""
        self.assertEqual(
            sorted(e["entity_id"] for e in self.model.entities.values() if e["record_count"] > 1),
            sorted(e["entity_id"] for e in self.payload["merges"]["entities"]),
        )

    def test_the_index_carries_no_records_another_surface_already_carries(self):
        """The reason the old shim indexed the graph: embedding records twice is the cost."""
        inline = {n["entity_id"] for n in self.payload["graph"]["nodes"]}
        inline |= {e["entity_id"] for e in self.payload["merges"]["entities"]}
        indexed = {e["entity_id"] for e in self.payload["records_index"]}
        self.assertEqual(set(), inline & indexed)

    def test_the_index_is_deterministic(self):
        """A re-rendered snapshot must not disagree with the one it replaces."""
        again = VIZ._snapshot_payload(model_past_the_cap())
        self.assertEqual(
            [e["entity_id"] for e in self.payload["records_index"]],
            [e["entity_id"] for e in again["records_index"]],
        )

    def test_the_index_entries_are_the_endpoint_shape(self):
        """`/api/records` answers {entity_id, entity_name, records} — so does the index."""
        for entry in self.payload["records_index"]:
            self.assertEqual(
                {"entity_id", "entity_name", "records"}, set(entry),
            )
            self.assertEqual(self.model.records(entry["entity_id"]), entry)


class TheSnapshotFileCarriesTheIndex(unittest.TestCase):
    """End to end: the written file embeds the index, and its JSON is parseable."""

    @classmethod
    def setUpClass(cls):
        cls.model = model_past_the_cap()
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "snapshot.html")
            # engine=None: the snapshot build must not need one (INV-077), and the probe
            # body falls back to the merge data when no search can run. Its per-example
            # notice is captured rather than printed: this fixture has 1,501 merged
            # entities and none of them is searchable here, so the suite's own log would
            # otherwise carry 1,501 lines about a deliberate absence.
            with contextlib.redirect_stderr(io.StringIO()):
                VIZ.write_snapshot(
                    cls.model, None, 0, "T", out, port=9001, dataset="the loaded data"
                )
            cls.html = Path(out).read_text(encoding="utf-8")

    def test_the_embedded_payload_carries_the_index(self):
        blob = self.html[self.html.index("const __DATA__=") + len("const __DATA__="):]
        data = json.loads(blob[: blob.index(";var __RECS__=null;")])
        self.assertIn("records_index", data)
        indexed = {e["entity_id"] for e in data["records_index"]}
        self.assertTrue({1502, 1503, 1504, 1505} <= indexed)
        for eid in BEYOND_THE_CAP:
            with self.subTest(entity=eid):
                self.assertNotIn("error", resolve(data, eid))

    def test_the_live_only_disclosures_survive(self):
        self.assertIn(
            "Why/How explanations run only against the live visualization server", self.html
        )
        self.assertIn("This is a saved snapshot, so live search is disabled", self.html)
        self.assertIn("if(p==='search')", self.html)


class TheContractStatesTheRule(unittest.TestCase):
    """The any-language contract, not only the reference implementation (INV-002)."""

    @classmethod
    def setUpClass(cls):
        cls.text = re.sub(r"\s+", " ", CONTRACT.read_text(encoding="utf-8"))

    def test_it_says_the_index_covers_every_offered_entity(self):
        self.assertRegex(
            self.text,
            r"(?i)MUST cover every entity the snapshot still offers.*?"
            r"not only the entities the graph node cap kept",
        )

    def test_it_forbids_the_graph_payload_as_the_denominator(self):
        self.assertIn("graph node cap", self.text)


if __name__ == "__main__":
    unittest.main()
