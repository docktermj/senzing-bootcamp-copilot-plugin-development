"""At full scale the Entity Graph opens fitted, paints the strokes its data sets, and the snapshot
answers for every entity it offers -- checked in a browser, and by Module 7 on the Bootcamper's data.

#883, from a graduation retrospective on 10,000 source keys (5,742 entities, the graph capped at
1,500 nodes). Two defects were still on main, and both passed every check the 84-entity Truth Set
can run:

* **No initial fit.** ``fitToExtent()`` ran only in the capture render (``?capture=1``). The app and
  the snapshot opened at scale 1 with most of a 1,500-node layout outside a narrow pane, and the
  fit's ``Math.max(0.05, …)`` clamp would have left a graph wider than twenty panes unfitted even
  where it did run.
* **Stylesheet over data.** ``.edge line{stroke:var(--line);stroke-width:1.5px}`` overrode the
  per-relationship-type ``stroke`` / ``stroke-width`` attributes, because an SVG presentation
  attribute loses to any CSS rule: every relationship edge painted gray. ``.node circle`` did the
  same to the per-source outlines, so the 7th and later sources all painted white. The DOM
  attributes read correctly throughout, which is why ``test_source_encoding_renders_distinctly``
  (it reads attributes) never saw it: only the **computed** style does.

What is pinned, and how:

* **Browser half** (skips where no headless Chrome/Chromium/Edge is found, as
  ``test_settle_signal_is_reported.py`` does). The page is the shipped snapshot -- or the live
  server's page, served by the real handler -- with ``capture_screenshots._scale_check_page``
  injected: animation frames are routed through ``setTimeout``, which headless virtual time
  advances, so the page's OWN interactive layout runs to its OWN first settle (INV-298) instead of
  the synchronous capture render. Every scenario reads the same in-page measurements Module 7's
  ``--verify-scale`` uses, and every acceptance assertion has a negative control: the same page
  with the pre-#883 code restored must fail it.
* **Structural half** (runs everywhere): the zoom floor follows the fit, the first settle fits once
  and only when the reader has not moved the view, no stylesheet rule sets a stroke on an
  unscoped ``.edge line`` / ``.node circle`` (with the restored rules as negative controls), the
  verifier's verdicts and its no-browser exit, the contract's two rules, and Module 7's check.

The model past the cap is the #675 fixture (``test_snapshot_records_beyond_the_graph_cap.py``),
extended with relationships of three types, eight more sources (so strokes are assigned) and long
names and match keys (so labels are wider than their nodes and the Match Keys gutter is tested).

Stdlib only; the scripts are loaded by path, never imported from ``plugins/`` as a package
(INV-108).

Run:  python3 -m unittest discover -s tools/bootcamp-transform/tests -v
"""
import contextlib
import importlib.util
import io
import inspect
import os
import re
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

TESTS = Path(__file__).resolve().parent
REPO_ROOT = TESTS.parents[2]
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
CAPTURE = PLUGIN / "scripts" / "capture_screenshots.py"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CONTRACT = PLUGIN / "skills" / "module-03b-truthset-visualization" / "visualization-api-reference.md"
MODULE_07 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
import test_snapshot_records_beyond_the_graph_cap as CAPPED  # noqa: E402  (the #675 fixture)

VIZ = CAPPED.VIZ


def load_capture():
    spec = importlib.util.spec_from_file_location("cap_scale_mod", CAPTURE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cap_scale_mod"] = module
    spec.loader.exec_module(module)
    return module


CAP = load_capture()
SOURCE = SERVER.read_text(encoding="utf-8")


def has_browser():
    return CAP._chrome_exe() is not None


# --- fixtures ---------------------------------------------------------------------------------

EXTRA_SOURCES = tuple("SRC_%02d" % i for i in range(1, 9))
RTYPES = ("POSSIBLY_SAME", "POSSIBLY_RELATED", "DISCLOSED")
LONG_KEY = "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY+LEI_NUMBER"
LONG_KEY_2 = "+NAME+ADDRESS+NATIONAL_ID+OTHER_ID+REGISTRATION_DATE+REGISTRATION_COUNTRY+DUNS_NUMBER"


def long_name(i):
    return "ACME HOLDINGS INTERNATIONAL %04d" % i


def relate(model, pairs):
    for n, (a, b) in enumerate(pairs):
        model.edges[(a, b)] = {"match_key": "+NAME+ADDRESS", "relationship_type": RTYPES[n % len(RTYPES)]}


def scale_model():
    """The #675 model past the cap, plus relationships, eight more sources and long text."""
    model = CAPPED.model_past_the_cap()
    for i, src in enumerate(EXTRA_SOURCES):
        eid = 2001 + i
        model.entities[eid] = CAPPED.entity(
            eid, [src], [CAPPED.record(src, "x%d" % eid, LONG_KEY), CAPPED.record(src, "y%d" % eid, LONG_KEY_2)])
        node = model.entities[i + 1]
        node["data_sources"] = sorted(set(node["data_sources"] + [src]))
        node["records"].append(CAPPED.record(src, "scale%d" % i, LONG_KEY))
        node["record_count"] = len(node["records"])
    for i in range(1, 31):
        model.entities[i]["entity_name"] = long_name(i)
    relate(model, [(i, i + 1) for i in range(1, 30)] + [(2001 + i, 1 + i) for i in range(8)])
    model.records_total = sum(e["record_count"] for e in model.entities.values())
    return model


def small_model(count=40, related=True):
    """Uncapped, below the label threshold, nine sources so the 7th+ carry an assigned stroke."""
    model = VIZ.Model()
    sources = ("SRC_A",) + EXTRA_SOURCES
    for i in range(1, count + 1):
        src = sources[i % len(sources)]
        model.entities[i] = CAPPED.entity(
            i, [src], [CAPPED.record(src, "r%d" % i, "+NAME"), CAPPED.record(src, "s%d" % i, "+NAME+ADDRESS")])
        model.entities[i]["entity_name"] = long_name(i)
    if related:
        relate(model, [(i, i + 1) for i in range(1, count)])
    model.records_total = sum(e["record_count"] for e in model.entities.values())
    return model


def snapshot_html(model):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "snapshot.html")
        # engine=None, as the #675 file does: the snapshot build must not need one (INV-077).
        with contextlib.redirect_stderr(io.StringIO()):
            VIZ.write_snapshot(model, None, 0, "Scale", out, port=9001, dataset="the loaded data")
        return Path(out).read_text(encoding="utf-8")


#: Pre-#883 code, restored into an otherwise-shipped page. Each must make an assertion fail.
OLD_EDGE_RULE = (".edge line:not([stroke]){", ".edge line{")
OLD_NODE_RULE = (".node circle:not([stroke]){", ".node circle{")
OLD_ALWAYS_REFIT = ("if(!fitted&&!readerMoved)fitToExtent();", "fitToExtent();")
OLD_IGNORES_READER = ("if(!fitted&&!readerMoved)fitToExtent();", "if(!fitted)fitToExtent();")
OLD_NO_FIRST_FIT = ("if(!fitted&&!readerMoved)fitToExtent();", "")
OLD_CLAMPED_FIT = ("const k=Math.min(4,0.94*Math.min(W/w,H/h));",
                   "const k=Math.min(4,Math.max(0.05,0.94*Math.min(W/w,H/h)));")
OLD_GRAPH_ONLY_SHIM = ("(((__DATA__.merges||{}).entities)||[]).forEach(add);"
                       "((__DATA__.records_index)||[]).forEach(add);}", "}")


def mutate(page, change):
    old, new = change
    if page.count(old) != 1:
        raise AssertionError("the negative control no longer finds %r in the page" % old)
    return page.replace(old, new)


# --- the in-page scenario driver -------------------------------------------------------------

PRELUDE = r"""<script>
var S=__szScale;
function T(){var t=d3.zoomTransform(S.graphSvg());return [t.k,t.x,t.y];}
function wheel(dy){var s=S.graphSvg(),r=s.getBoundingClientRect();
  s.dispatchEvent(new WheelEvent("wheel",{deltaY:dy,deltaMode:0,clientX:r.left+r.width/2,
    clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));}
function drag(){var c=S.graphSvg().querySelector("circle"),r=c.getBoundingClientRect(),
  x=r.left+r.width/2,y=r.top+r.height/2;
  function ev(t,tg,dx){tg.dispatchEvent(new MouseEvent(t,{clientX:x+dx,clientY:y+dx,button:0,
    buttons:1,bubbles:true,cancelable:true,view:window}));}
  ev("mousedown",c,0);ev("mousemove",window,40);ev("mouseup",window,40);}
async function go(body){try{S.stamp(await body());}catch(e){S.stamp({error:String(e&&e.stack||e)});}}
</script>
"""


def scenario(page, body):
    return PRELUDE + "<script>go(async function(){" + body + "});</script>"


def run(chrome, tmp, name, page, script=None):
    """Load `page` with the measurements injected (and `script`, else the full check)."""
    patched = CAP._scale_check_page(page, run=script is None)
    if script is not None:
        patched = patched.replace("</body>", script + "</body>", 1)
    path = Path(tmp) / name
    path.write_text(patched, encoding="utf-8")
    report = CAP._parse_scale_report(CAP._scale_dom(chrome, str(path)))
    if report is None:
        raise AssertionError("the page never stamped a result: the injected script did not finish")
    if report.get("error"):
        raise AssertionError("the injected script raised: " + report["error"])
    return report


def rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "rgb(%d, %d, %d)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def px(value):
    return "%gpx" % float(value)


def same(a, b, tol=1e-6):
    return all(abs(x - y) <= tol * max(1.0, abs(x), abs(y)) for x, y in zip(a, b))


# ============================================================================================
# Browser half
# ============================================================================================

@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheSnapshotPassesTheScaleCheckPastTheCap(unittest.TestCase):
    """Module 7's own check, run on a snapshot of a model past the cap, and on its defects."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.page = snapshot_html(scale_model())
        cls.report = run(cls.chrome, cls.tmp.name, "snapshot.html", cls.page)
        cls.checks = cls.report.get("checks") or {}

    def test_the_fixture_is_capped_and_the_check_ran(self):
        self.assertTrue(self.report.get("capped"), self.report)
        self.assertEqual(CAP.SCALE_EXIT_PASSED, CAP.scale_verdict(self.report)[0], self.report)

    def test_every_drawn_node_is_inside_a_480px_pane_in_both_modes(self):
        modes = self.checks["fit_in_pane"]["modes"]
        self.assertEqual({"all", "network"}, set(modes), "both modes must be measured")
        self.assertEqual(VIZ.GRAPH_NODE_CAP, modes["all"]["nodes"],
                         "the all-entities pass must measure every node the cap kept")
        self.assertGreater(modes["network"]["nodes"], 0)
        self.assertGreater(modes["network"]["labels"], 0,
                           "labels are drawn in relationship mode here, so their extent is measured")
        for mode, fit in modes.items():
            with self.subTest(mode=mode):
                self.assertEqual("passed", fit["status"], fit)
                self.assertLessEqual(fit["pane"][0], CAP.SCALE_PANE_PX)
                self.assertGreater(fit["pane"][0], CAP.SCALE_PANE_PX - 10)

    def test_relationship_edges_paint_their_type_colors(self):
        edges = self.checks["edge_colors"]
        self.assertEqual("passed", edges["status"], edges)
        self.assertGreater(edges["edges"]["checked"], 0)
        self.assertEqual(len(RTYPES), edges["edges"]["colors"])
        self.assertGreater(edges["outlines"]["checked"], 0,
                           "the 7th and later sources carry an assigned outline in this fixture")

    def test_an_outside_cap_entity_opens_its_records(self):
        records = self.checks["records_beyond_cap"]
        self.assertEqual("passed", records["status"], records)
        self.assertTrue(records["outside_cap_known"])
        self.assertTrue(records["checked"])
        drawn = {n["entity_name"] for n in VIZ._snapshot_payload(scale_model())["graph"]["nodes"]}
        for name in records["checked"]:
            with self.subTest(entity=name):
                self.assertNotIn(name, drawn, "a checked entity must be one the graph left out")

    def test_negative_control_the_old_edge_rule_fails_the_check(self):
        report = run(self.chrome, self.tmp.name, "old-edge.html", mutate(self.page, OLD_EDGE_RULE))
        self.assertEqual("failed", report["checks"]["edge_colors"]["status"])
        self.assertEqual(CAP.SCALE_EXIT_FAILED, CAP.scale_verdict(report)[0])

    def test_negative_control_no_first_fit_fails_the_check(self):
        report = run(self.chrome, self.tmp.name, "no-fit.html", mutate(self.page, OLD_NO_FIRST_FIT))
        self.assertEqual("failed", report["checks"]["fit_in_pane"]["status"])

    def test_negative_control_a_graph_only_records_index_fails_the_check(self):
        """#675's defect, restored: the browser check sees "not found" in the dialog."""
        report = run(self.chrome, self.tmp.name, "graph-only.html", mutate(self.page, OLD_GRAPH_ONLY_SHIM))
        self.assertEqual("failed", report["checks"]["records_beyond_cap"]["status"])


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheCommandModuleSevenRunsPasses(unittest.TestCase):
    """`capture_screenshots.py --html <snapshot> --verify-scale`, as Module 7 runs it."""

    def test_the_cli_exits_zero_and_names_every_check(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "results_visualization.html"
            snap.write_text(snapshot_html(scale_model()), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(CAPTURE), "--html", str(snap), "--verify-scale"],
                capture_output=True, text=True, timeout=900,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            for check in CAP.SCALE_CHECKS:
                with self.subTest(check=check):
                    self.assertRegex(proc.stdout, r"scale-check: %s\tpassed\t" % check)
            self.assertEqual([snap.name], sorted(os.listdir(tmp)),
                             "the check captures nothing and leaves no temp copy behind")


class _Live(ThreadingHTTPServer):
    daemon_threads = True


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheLiveAppPassesTheSameCheck(unittest.TestCase):
    """The live server's page and API, served by the real handler past the cap."""

    @classmethod
    def setUpClass(cls):
        model = scale_model()
        base = VIZ.make_handler(model, None, 0, None, "Scale")

        class Handler(base):
            def do_GET(self):
                if urlparse(self.path).path in ("/", "/index.html"):
                    page = CAP._scale_check_page(VIZ.render_page("Scale", sources=model.color_keys()))
                    return self._send(200, page, "text/html; charset=utf-8")
                return super().do_GET()

        cls.httpd = _Live(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        thread.start()
        cls.addClassCleanup(cls.httpd.server_close)
        cls.addClassCleanup(cls.httpd.shutdown)
        url = "http://127.0.0.1:%d/" % cls.httpd.server_address[1]
        cls.report = CAP._parse_scale_report(CAP._scale_dom(CAP._chrome_exe(), url)) or {}

    def test_the_live_app_is_capped_and_fitted_in_both_modes(self):
        self.assertTrue(self.report.get("capped"), self.report)
        fit = self.report["checks"]["fit_in_pane"]
        self.assertEqual({"all", "network"}, set(fit["modes"]))
        self.assertEqual("passed", fit["status"], fit)

    def test_the_live_app_paints_relationship_colors(self):
        self.assertEqual("passed", self.report["checks"]["edge_colors"]["status"],
                         self.report["checks"]["edge_colors"])

    def test_the_live_app_opens_an_outside_cap_entitys_records(self):
        self.assertEqual("passed", self.report["checks"]["records_beyond_cap"]["status"],
                         self.report["checks"]["records_beyond_cap"])


ZOOM_THEN_DRAG = """
await S.until(S.settled,60000);var o={};o.fitted=T();o.fit=S.fitReport().status;
wheel(-300);await S.sleep(200);o.zoomed=T();
drag();o.unsettled_by_drag=!S.settled();
o.resettled=await S.until(S.settled,60000);o.after_drag=T();
var row=document.querySelector("#graph-container .legend .row");
if(row){row.dispatchEvent(new MouseEvent("click",{bubbles:true}));await S.sleep(300);}
o.filtered=!!row;o.after_filter=T();o.settled_after_filter=S.settled();
o.redrawn=await S.redraw(function(){S.modeToggle().click();});o.toggled_fit=S.fitReport();
return o;"""

ZOOM_BEFORE_SETTLE = """
await S.until(function(){return S.graphSvg()&&!S.settled();},60000);
wheel(-300);await S.sleep(30);var o={zoomed:T(),before_settle:!S.settled()};
o.settled=await S.until(S.settled,60000);o.after=T();return o;"""

PIN_FAR = """
await S.until(function(){return S.graphSvg()&&graphSim;},60000);
var n=graphSim.nodes()[0],w=+S.graphSvg().getAttribute("width");n.fx=w/2+60000;n.fy=200;
await S.until(S.settled,60000);var o={fit:T(),report:S.fitReport()};
wheel(20000);await S.sleep(200);o.zoomed_out=T();return o;"""

NO_PIN = """
await S.until(S.settled,60000);var o={fit:T(),report:S.fitReport()};
wheel(20000);await S.sleep(200);o.zoomed_out=T();return o;"""

STROKES = """
await S.until(S.settled,60000);var o={};
function lines(){return Array.prototype.map.call(S.graphSvg().querySelectorAll(".edge line"),function(l){
  var cs=getComputedStyle(l);return [l.getAttribute("stroke"),cs.stroke,cs.strokeWidth];});}
var line=getComputedStyle(document.documentElement).getPropertyValue("--line").trim();
o.line=S.norm(line);o.all_edges=lines();
o.redrawn=await S.redraw(function(){S.modeToggle().click();});o.net_edges=lines();
o.nodes=Array.prototype.map.call(S.graphSvg().querySelectorAll("circle"),function(c){
  var d=d3.select(c.parentNode).datum(),cs=getComputedStyle(c);
  return [(d.data_sources||[]).slice().sort().join("|"),cs.stroke,cs.strokeWidth];});
return o;"""

MATCH_KEYS = """
await S.until(S.settled,60000);activate("matchkeys");await S.sleep(800);
var svg=document.querySelector("#tab-matchkeys svg"),p=svg.getBoundingClientRect(),o={left:p.left,labels:[]};
svg.querySelectorAll("text").forEach(function(t){var r=t.getBoundingClientRect();
  if(r.width>0)o.labels.push([t.textContent,r.left]);});return o;"""

SETTLED_ONLY = """
var ok=await S.until(S.settled,60000);var s=S.graphSvg();
return {settled:ok,svg:!!s,fit:s?T():null,report:s?S.fitReport():null};"""


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheFirstSettleFitsOnceAndThenTheViewIsTheReaders(unittest.TestCase):
    """Zoom, drag, filter and mode toggle, driven through the shipped page's own handlers."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.page = snapshot_html(small_model())
        cls.o = run(cls.chrome, cls.tmp.name, "zoom-drag.html", cls.page, scenario(cls.page, ZOOM_THEN_DRAG))

    def test_the_first_settle_fitted(self):
        self.assertEqual("passed", self.o["fit"])
        self.assertFalse(same(self.o["fitted"], [1, 0, 0]), "the first settle applied no fit")

    def test_zoom_then_drag_keeps_the_readers_transform(self):
        self.assertFalse(same(self.o["zoomed"], self.o["fitted"]), "the wheel did not zoom")
        self.assertTrue(self.o["unsettled_by_drag"], "the drag did not re-heat the layout")
        self.assertTrue(self.o["resettled"], "the layout never settled again after the drag")
        self.assertTrue(same(self.o["after_drag"], self.o["zoomed"]),
                        "the drag's settle refit the view: %s -> %s" % (self.o["zoomed"], self.o["after_drag"]))

    def test_the_legend_filter_never_refits(self):
        self.assertTrue(self.o["filtered"], "no source legend row to click")
        self.assertTrue(same(self.o["after_filter"], self.o["after_drag"]))
        self.assertTrue(self.o["settled_after_filter"])

    def test_a_mode_toggle_gets_its_own_first_fit(self):
        """The reader zoomed the previous layout; the redraw is a new one and fits."""
        self.assertTrue(self.o["redrawn"])
        self.assertEqual("passed", self.o["toggled_fit"]["status"], self.o["toggled_fit"])

    def test_negative_control_a_fit_on_every_settle_moves_the_view(self):
        o = run(self.chrome, self.tmp.name, "refit.html", mutate(self.page, OLD_ALWAYS_REFIT),
                scenario(self.page, ZOOM_THEN_DRAG))
        self.assertTrue(o["resettled"])
        self.assertFalse(same(o["after_drag"], o["zoomed"]),
                         "refitting on every settle went undetected, so the assertion above is vacuous")


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class AZoomBeforeTheFirstSettleCancelsThatFit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.page = snapshot_html(small_model())

    def test_the_settle_after_a_zoom_does_not_fit(self):
        o = run(self.chrome, self.tmp.name, "early.html", self.page, scenario(self.page, ZOOM_BEFORE_SETTLE))
        self.assertTrue(o["before_settle"], "the wheel landed after the settle, so nothing was tested")
        self.assertTrue(o["settled"])
        self.assertTrue(same(o["after"], o["zoomed"]), "%s -> %s" % (o["zoomed"], o["after"]))

    def test_negative_control_ignoring_the_reader_refits(self):
        o = run(self.chrome, self.tmp.name, "early-neg.html", mutate(self.page, OLD_IGNORES_READER),
                scenario(self.page, ZOOM_BEFORE_SETTLE))
        self.assertTrue(o["before_settle"])
        self.assertFalse(same(o["after"], o["zoomed"]))


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheZoomFloorFollowsTheFit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.page = snapshot_html(small_model())
        cls.far = run(cls.chrome, cls.tmp.name, "far.html", cls.page, scenario(cls.page, PIN_FAR))

    def test_a_fit_below_the_floor_is_applied_unclamped(self):
        self.assertLess(self.far["fit"][0], 0.05, self.far)
        self.assertEqual("passed", self.far["report"]["status"], self.far["report"])

    def test_the_lowered_floor_is_the_fit_scale(self):
        self.assertAlmostEqual(self.far["fit"][0], self.far["zoomed_out"][0], places=9)

    def test_the_floor_stays_when_the_fit_does_not_need_it(self):
        o = run(self.chrome, self.tmp.name, "near.html", self.page, scenario(self.page, NO_PIN))
        self.assertGreaterEqual(o["fit"][0], 0.05)
        self.assertEqual("passed", o["report"]["status"])
        self.assertAlmostEqual(0.05, o["zoomed_out"][0], places=9)

    def test_negative_control_the_old_clamp_leaves_nodes_outside(self):
        o = run(self.chrome, self.tmp.name, "clamp.html", mutate(self.page, OLD_CLAMPED_FIT),
                scenario(self.page, PIN_FAR))
        self.assertAlmostEqual(0.05, o["fit"][0], places=9)
        self.assertEqual("failed", o["report"]["status"])


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheStrokeTheDataSetsIsThePaintedStroke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.model = small_model()
        cls.assigned = VIZ.color_for_sources(cls.model.color_keys())
        cls.page = snapshot_html(cls.model)
        cls.o = run(cls.chrome, cls.tmp.name, "strokes.html", cls.page, scenario(cls.page, STROKES))

    def edge_problems(self, o):
        bad = [e for e in o["net_edges"] if e[1] != CAP_rgb(e[0]) or e[2] != "2px"]
        return bad

    def node_problems(self, o):
        bad = []
        for key, stroke, width in o["nodes"]:
            spec = self.assigned[key]
            want = (rgb(spec["stroke"]), px(spec["stroke_width"])) if spec.get("stroke_width") \
                else ("rgb(255, 255, 255)", "1.5px")
            if (stroke, width) != want:
                bad.append((key, stroke, width, want))
        return bad

    def test_relationship_edges_paint_their_type_color_at_2px(self):
        self.assertTrue(self.o["redrawn"])
        self.assertTrue(self.o["net_edges"])
        self.assertEqual([], self.edge_problems(self.o))
        self.assertEqual(len(RTYPES), len({e[1] for e in self.o["net_edges"]}))

    def test_full_population_edges_keep_the_default(self):
        self.assertTrue(self.o["all_edges"])
        for attr, stroke, width in self.o["all_edges"]:
            self.assertIsNone(attr)
            self.assertEqual((self.o["line"], "1.5px"), (stroke, width))

    def test_assigned_outlines_paint_and_the_first_six_stay_white(self):
        stroked = [k for k, _s, _w in self.o["nodes"] if self.assigned[k].get("stroke_width")]
        plain = [k for k, _s, _w in self.o["nodes"] if not self.assigned[k].get("stroke_width")]
        self.assertTrue(stroked, "no node of a 7th or later source was drawn")
        self.assertTrue(plain, "no node of the first six sources was drawn")
        self.assertEqual([], self.node_problems(self.o))

    def test_negative_control_the_old_edge_rule_fails(self):
        o = run(self.chrome, self.tmp.name, "edge-neg.html", mutate(self.page, OLD_EDGE_RULE),
                scenario(self.page, STROKES))
        self.assertTrue(self.edge_problems(o))

    def test_negative_control_the_old_node_rule_fails(self):
        o = run(self.chrome, self.tmp.name, "node-neg.html", mutate(self.page, OLD_NODE_RULE),
                scenario(self.page, STROKES))
        self.assertTrue(self.node_problems(o))


def CAP_rgb(color):
    """A stroke attribute as the browser serializes it (the renderer writes `#rrggbb`)."""
    return rgb(color) if color and color.startswith("#") else color


OLD_NODE_ONLY_EXTENT = ("hw=Math.max(r,halfLabel[d.id]||0)", "hw=r")


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class ADrawnLabelIsInsideThePaneToo(unittest.TestCase):
    """Labels wider than their nodes: the fit must take their measured width into the extent."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()
        cls.page = snapshot_html(small_model())

    def test_every_drawn_label_is_inside(self):
        o = run(self.chrome, self.tmp.name, "labels.html", self.page, scenario(self.page, SETTLED_ONLY))
        self.assertEqual(40, o["report"]["labels"], "labels are not drawn, so their extent is untested")
        self.assertEqual("passed", o["report"]["status"], o["report"])

    def test_negative_control_a_node_only_extent_lets_a_label_out(self):
        o = run(self.chrome, self.tmp.name, "labels-neg.html", mutate(self.page, OLD_NODE_ONLY_EXTENT),
                scenario(self.page, SETTLED_ONLY))
        self.assertGreater(o["report"]["outside_labels"], 0)


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheEdgeCases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = CAP._chrome_exe()

    def test_an_empty_graph_settles_with_nothing_to_fit(self):
        page = snapshot_html(VIZ.Model())
        o = run(self.chrome, self.tmp.name, "empty.html", page, scenario(page, SETTLED_ONLY))
        self.assertTrue(o["settled"])
        self.assertFalse(o["svg"])

    def test_a_single_node_fits_at_the_maximum_scale(self):
        """A short name, so the node and not its label sets the extent; a label wider than the
        pane at scale 4 would rightly fit below it."""
        model = small_model(count=1, related=False)
        model.entities[1]["entity_name"] = "Ann"
        page = snapshot_html(model)
        o = run(self.chrome, self.tmp.name, "one.html", page, scenario(page, SETTLED_ONLY))
        self.assertTrue(o["settled"])
        self.assertEqual(4, o["fit"][0])
        self.assertEqual("passed", o["report"]["status"])
        self.assertEqual(1, o["report"]["labels"])

    def test_no_match_key_label_starts_left_of_the_svg_at_full_scale(self):
        page = snapshot_html(scale_model())
        o = run(self.chrome, self.tmp.name, "mk.html", page, scenario(page, MATCH_KEYS))
        self.assertTrue(o["labels"], "the Match Keys chart drew no labels")
        self.assertTrue(any("NATIONAL_ID" in text or "…" in text for text, _left in o["labels"]),
                        "the long keys were not drawn, so the gutter was not exercised")
        late = [(t, left) for t, left in o["labels"] if left < o["left"] - 0.5]
        self.assertEqual([], late)


#: A snapshot no Python wrote: no d3, no reference class names, its own DOM and a native
#: `<dialog>`, carrying only the hooks the any-language contract fixes -- `tab-graph` /
#: `tab-probe` and a page-scope `activate()` (INV-124), `data-graph-settled` (INV-298), the
#: capped note's wording, the "Show only entities with relationships" toggle, the "Show all
#: merged entities" browse and the "Records" action. Its records are embedded, so it works
#: offline as a snapshot must. `__CSS__` and `__EDGE__` choose how the relationship
#: edge's stroke is set, for the precedence control. (Grafted from the race's approach A, #883.)
FOREIGN = """<!doctype html><html><head><meta charset="utf-8"><title>Foreign</title>
<style>body{margin:0;font-family:sans-serif}.tab{display:none}.tab.active{display:block}
#tab-graph{padding:10px}#pane{height:400px;border:1px solid #ccc}#pane svg{width:100%;height:100%}
__CSS__</style></head><body>
<nav><button id="navbtn-graph" onclick="activate('graph')">Entity Graph</button>
<button id="navbtn-probe" onclick="activate('probe')">Search / Probe</button></nav>
<section id="tab-graph" class="tab active"><p id="note"></p>
<label><input type="checkbox" id="mode" checked> Show only entities with relationships</label>
<div id="pane"></div></section>
<section id="tab-probe" class="tab"><h2>Search / Probe</h2>
<button id="browse">Show all merged entities</button><div id="cards"></div></section>
<dialog id="dlg"><header>Records <button id="dlg-close">Close</button></header><div id="dlg-body"></div></dialog>
<script>
var ENTITIES=[{id:1,name:"Alpha One",drawn:true,records:[["CRM","c1"],["ERP","e1"]]},
  {id:2,name:"Beta Two",drawn:true,records:[["CRM","c2"],["ERP","e2"]]},
  {id:7,name:"Gamma Seven",drawn:false,records:[["CRM","c7"],["WEB","w7"]]},
  {id:9,name:"Delta Nine",drawn:false,records:[["ERP","e9"],["WEB","w9"],["CRM","c9"]]}];
function activate(id){document.querySelectorAll(".tab").forEach(function(t){
  t.classList.toggle("active",t.id==="tab-"+id);});}
function draw(){var net=document.getElementById("mode").checked;
  document.documentElement.removeAttribute("data-graph-settled");
  document.getElementById("note").textContent=net
    ?"Showing 2 of the 4 entities that have relationships — the graph is capped at 2 of 4 entities."
    :"Showing 2 of 4 entities — the graph is capped; entities with relationships are kept first.";
  var pane=document.getElementById("pane"),w=pane.clientWidth;
  var svg='<svg xmlns="http://www.w3.org/2000/svg">';
  svg+=net?'<line x1="40" y1="40" x2="'+(w-40)+'" y2="40" __EDGE__></line>'
          :'<line x1="40" y1="40" x2="'+(w-40)+'" y2="40"></line>';
  svg+='<circle cx="40" cy="40" r="8"><title>Alpha One</title></circle>'
      +'<circle cx="'+(w-40)+'" cy="40" r="8"><title>Beta Two</title></circle></svg>';
  pane.innerHTML=svg;
  setTimeout(function(){document.documentElement.setAttribute("data-graph-settled","1");},100);}
document.getElementById("mode").addEventListener("change",draw);
document.getElementById("dlg-close").addEventListener("click",function(){document.getElementById("dlg").close();});
document.getElementById("browse").addEventListener("click",function(){
  var cards=document.getElementById("cards");cards.innerHTML="";
  ENTITIES.forEach(function(e){var card=document.createElement("div");
    card.innerHTML="<h4>"+e.name+"</h4><span>"+e.records.length+" records</span> ";
    var b=document.createElement("button");b.textContent="Records";
    b.addEventListener("click",function(){var d=document.getElementById("dlg");
      document.getElementById("dlg-body").textContent="Loading…";if(!d.open)d.showModal();
      setTimeout(function(){document.getElementById("dlg-body").textContent=e.name+": "
        +e.records.map(function(r){return r[0]+" "+r[1];}).join(", ");},50);});
    card.appendChild(b);cards.appendChild(card);});});
draw();
</script></body></html>"""


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheCheckerReadsAnyGeneratorsSnapshot(unittest.TestCase):
    """`--verify-scale` on a hand-written page with the contract's hooks and nothing of the
    reference's, through the CLI as Module 7 runs it: it passes on the hooks alone, and fails when
    its stylesheet beats its stroke attributes."""

    @staticmethod
    def verify(page):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "results_visualization.html"
            snap.write_text(page, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(CAPTURE), "--html", str(snap), "--verify-scale"],
                capture_output=True, text=True, timeout=900,
            )
        rows = dict(re.findall(r"^scale-check: (\S+)\t([^\t]*)\t", proc.stdout, re.M))
        return proc.returncode, rows, proc.stdout + proc.stderr

    @classmethod
    def setUpClass(cls):
        line_rule = "#tab-graph line{stroke:#999999;stroke-width:1px}"
        cls.good = cls.verify(FOREIGN.replace("__CSS__", line_rule).replace(
            "__EDGE__", 'style="stroke:#ff0000;stroke-width:2px"'))
        cls.bad = cls.verify(FOREIGN.replace("__CSS__", line_rule).replace(
            "__EDGE__", 'stroke="#ff0000" stroke-width="2"'))

    def test_a_foreign_snapshot_passes_on_the_contracts_hooks_alone(self):
        code, rows, out = self.good
        self.assertEqual(CAP.SCALE_EXIT_PASSED, code, out)
        self.assertEqual({c: CAP.SCALE_PASSED for c in CAP.SCALE_CHECKS}, rows, out)
        self.assertIn("2 of 2 entities outside the graph opened their records", out,
                      "only the two entities the graph left out are checked, and both open")

    def test_a_foreign_snapshot_whose_stylesheet_beats_its_attributes_fails(self):
        code, rows, out = self.bad
        self.assertEqual(CAP.SCALE_EXIT_FAILED, code, out)
        self.assertEqual(CAP.SCALE_FAILED, rows.get("edge_colors"), out)
        self.assertEqual(CAP.SCALE_PASSED, rows.get("fit_in_pane"), out)
        self.assertEqual(CAP.SCALE_PASSED, rows.get("records_beyond_cap"), out)


# ============================================================================================
# Structural half: runs everywhere
# ============================================================================================

def fit_body():
    start = SOURCE.index("function fitToExtent(){")
    return SOURCE[start:SOURCE.index("\n  }\n", start)]


def draw_graph_body():
    start = SOURCE.index("async function drawGraph(){")
    return SOURCE[start:SOURCE.index("\n}\n", start)]


class TheZoomFloorFollowsTheFitInTheSource(unittest.TestCase):

    def test_the_fit_is_not_clamped_at_the_floor(self):
        self.assertNotIn("Math.max(0.05", fit_body(),
                         "a fixed floor in the fit's scale leaves a wide graph unfitted (#883)")

    def test_the_fit_lowers_the_floor_only_when_it_needs_to(self):
        self.assertRegex(fit_body(), r"if\(k<zoomB\.scaleExtent\(\)\[0\]\)zoomB\.scaleExtent\(\[k,4\]\);")

    def test_the_readers_floor_is_still_0_05(self):
        self.assertIn("scaleExtent([0.05,4])", draw_graph_body())

    def test_a_drawn_labels_width_joins_the_extent(self):
        self.assertIn("getComputedTextLength", fit_body())
        self.assertIn("hide-node-labels", fit_body(),
                      "only while labels are drawn; reserving width for hidden text over-shrinks")


class TheFirstSettleFitsOnceInTheSource(unittest.TestCase):

    def test_the_end_handler_fits_once_unless_the_reader_moved(self):
        self.assertRegex(
            draw_graph_body(),
            r'sim\.on\("end",function\(\)\{\s*if\(!fitted&&!readerMoved\)fitToExtent\(\);\s*'
            r"fitted=true;\s*graphSettled\(true\);\}\);",
        )

    def test_only_a_readers_input_marks_the_view_as_theirs(self):
        self.assertRegex(draw_graph_body(), r"if\(ev\.sourceEvent\)readerMoved=true;")

    def test_the_flags_belong_to_one_layout(self):
        """Declared inside drawGraph, so a mode toggle's redraw starts unfitted."""
        body = draw_graph_body()
        self.assertIn("let readerMoved=false,fitted=false;", body)
        self.assertNotIn("let readerMoved", SOURCE.replace(body, ""))

    def test_the_fit_is_keyed_to_the_settle_and_never_a_timer(self):
        body = draw_graph_body()
        self.assertEqual(2, body.count("fitToExtent();"),
                         "called by the capture's settle and the first settle, nowhere else")
        self.assertNotRegex(body, r"setTimeout\([^;]*fitToExtent")

    def test_the_capture_marks_its_fit_as_the_first(self):
        start = SOURCE.index("  if(capture){")
        self.assertIn("fitted=true;", SOURCE[start:SOURCE.index("\n  }", start)])


RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def stylesheet():
    return re.search(r"<style>(.*?)</style>", VIZ.PAGE, re.S).group(1)


def data_stroke_overrides(css):
    """Selectors that set a stroke on EVERY `.edge line` / `.node circle`, data-set ones included."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    hits = []
    for selectors, body in RULE.findall(css):
        props = {part.split(":", 1)[0].strip() for part in body.split(";") if ":" in part}
        if not props & {"stroke", "stroke-width"}:
            continue
        for one in selectors.split(","):
            one = " ".join(one.split())
            if re.search(r"\.(?:edge line|node circle)$", one):
                hits.append(one)
    return hits


def default_rule(css, selector):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selectors, body in RULE.findall(css):
        if selector in [" ".join(s.split()) for s in selectors.split(",")]:
            return body
    return None


class NoStylesheetRuleOverridesADataStroke(unittest.TestCase):

    def test_the_shipped_stylesheet_has_none(self):
        self.assertEqual([], data_stroke_overrides(stylesheet()))

    def test_the_defaults_still_apply_where_the_data_sets_nothing(self):
        self.assertIn("stroke:var(--line)", default_rule(stylesheet(), ".edge line:not([stroke])") or "")
        self.assertIn("stroke:#fff", default_rule(stylesheet(), ".node circle:not([stroke])") or "")

    def test_negative_control_restoring_the_edge_rule_fails(self):
        self.assertEqual([".edge line"], data_stroke_overrides(mutate(stylesheet(), OLD_EDGE_RULE)))
        self.assertEqual([".edge line"], data_stroke_overrides(
            stylesheet() + ".edge line{stroke:var(--line);stroke-width:1.5px}"))

    def test_negative_control_restoring_the_node_rule_fails(self):
        self.assertEqual([".node circle"], data_stroke_overrides(mutate(stylesheet(), OLD_NODE_RULE)))
        self.assertEqual([".node circle"], data_stroke_overrides(
            stylesheet() + ".node circle{stroke:#fff;stroke-width:1.5px;cursor:pointer}"))

    def test_the_renderer_still_writes_the_data_strokes(self):
        body = draw_graph_body()
        self.assertIn('line.attr("stroke",function(d){return rcolor(d.rtype);}).attr("stroke-width",2)', body)
        self.assertIn('.attr("stroke",function(d){var k=srcKeyOf(d);return srcStrokeW(k)?srcStroke(k):null;})', body)


class TheVerifierIsGeneratorNeutral(unittest.TestCase):
    """The check reads only what the any-language contract fixes."""

    def test_frames_are_rerouted_before_any_page_script(self):
        page = CAP._scale_check_page(VIZ.render_page("x"))
        shim = page.index("window.requestAnimationFrame=")
        first_page_script = page.index("<script", page.index("</style>", shim))
        self.assertLess(shim, first_page_script)
        self.assertLess(page.index("window.__szScale"), page.index("</body>"))

    def test_it_uses_the_contract_hooks(self):
        js = CAP._SCALE_BODY + CAP._SCALE_RUN
        for hook in ("data-graph-settled", "tab-graph", "tab-probe", "activate", "the graph is capped",
                     "only entities with relationships", "show all merged entities", '"Records"'):
            with self.subTest(hook=hook):
                self.assertIn(hook.lower(), js.lower())

    def test_it_reads_no_reference_internal(self):
        js = CAP._SCALE_BODY + CAP._SCALE_RUN
        for internal in ("__DATA__", "graphSim", "fitToExtent", "zoomB", "__recordsFor"):
            with self.subTest(internal=internal):
                self.assertNotIn(internal, js)

    def test_it_checks_the_interactive_render_not_the_capture_render(self):
        for fn in (CAP._scale_dom, CAP.run_scale_check):
            with self.subTest(fn=fn.__name__):
                self.assertNotIn("capture", inspect.getsource(fn).replace("capture_output", ""))


class TheVerdictNeverReportsAnUnrunCheckAsPassed(unittest.TestCase):

    def report(self, **statuses):
        return {"capped": True, "checks": {c: {"status": statuses.get(c, "passed")} for c in CAP.SCALE_CHECKS}}

    def test_all_passed_is_zero(self):
        self.assertEqual(CAP.SCALE_EXIT_PASSED, CAP.scale_verdict(self.report())[0])

    def test_a_failure_is_one(self):
        self.assertEqual(CAP.SCALE_EXIT_FAILED,
                         CAP.scale_verdict(self.report(edge_colors="failed", fit_in_pane="not exercised"))[0])

    def test_not_exercised_is_three_not_zero(self):
        self.assertEqual(CAP.SCALE_EXIT_NOT_EXERCISED,
                         CAP.scale_verdict(self.report(records_beyond_cap="not exercised"))[0])

    def test_a_missing_check_is_not_exercised(self):
        report = self.report()
        del report["checks"]["fit_in_pane"]
        self.assertEqual(CAP.SCALE_EXIT_NOT_EXERCISED, CAP.scale_verdict(report)[0])

    def test_an_unsettled_page_is_not_a_pass(self):
        self.assertEqual(CAP.SCALE_EXIT_NOT_EXERCISED, CAP.scale_verdict({"error": "never settled"})[0])

    def test_an_uncapped_graph_owes_no_check_and_says_so(self):
        code, rows = CAP.scale_verdict({"capped": False})
        self.assertEqual(CAP.SCALE_EXIT_PASSED, code)
        self.assertEqual([("graph", "not capped")], [r[:2] for r in rows])

    def test_no_browser_is_skipped_for_every_check(self):
        saved = CAP._chrome_exe
        CAP._chrome_exe = lambda: None
        try:
            report = CAP.run_scale_check(Path(__file__))
        finally:
            CAP._chrome_exe = saved
        self.assertEqual(CAP.SCALE_SKIPPED, report["status"])
        code, rows = CAP.scale_verdict(report)
        self.assertEqual(CAP.SCALE_EXIT_SKIPPED, code)
        self.assertEqual(list(CAP.SCALE_CHECKS), [r[0] for r in rows])
        self.assertEqual({CAP.SCALE_SKIPPED}, {r[1] for r in rows})


class TheCommandLineWithoutABrowser(unittest.TestCase):

    def main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        saved = CAP._chrome_exe
        CAP._chrome_exe = lambda: None
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = CAP.main(argv)
        finally:
            CAP._chrome_exe = saved
        return code, out.getvalue(), err.getvalue()

    def test_no_browser_exits_two_and_says_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "results_visualization.html"
            snap.write_text("<html><body></body></html>", encoding="utf-8")
            code, out, err = self.main(["--html", str(snap), "--verify-scale"])
        self.assertEqual(CAP.SCALE_EXIT_SKIPPED, code)
        for check in CAP.SCALE_CHECKS:
            self.assertIn("scale-check: %s\tskipped" % check, out)
        self.assertNotIn("passed", out)
        self.assertIn("INV-163", err)

    def test_it_checks_a_saved_snapshot_only(self):
        self.assertEqual(1, self.main(["--url", "http://localhost:8080", "--verify-scale"])[0])
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "s.html"
            snap.write_text("<html></html>", encoding="utf-8")
            self.assertEqual(1, self.main(["--html", str(snap), "--verify-scale", "--tabs", "graph"])[0])


def flat(text):
    return re.sub(r"\s+", " ", text)


class TheContractStatesBothRulesAsBehavior(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = CONTRACT.read_text(encoding="utf-8")
        cls.flat = flat(cls.text)

    def section(self, anchor):
        start = self.text.index('<a id="%s"></a>' % anchor)
        stop = self.text.find("\n- ", start)
        return flat(self.text[start:stop])

    def test_the_initial_fit(self):
        fit = self.section("graph-initial-fit")
        for needle in (r"(?i)first settles, fit every drawn node inside the graph pane",
                       r"(?i)its label while labels are drawn", r"(?i)live app and in the standalone snapshot",
                       r"(?i)never to a timer", r"(?i)zoom floor follows the fit",
                       r"(?i)never refits", r"(?i)\*\*before\*\* the first settle keeps their view",
                       r"(?i)mode toggle .* gets its own first fit", r"(?i)legend filter .* never refits"):
            with self.subTest(needle=needle):
                self.assertRegex(fit, needle)

    def test_the_stroke_precedence(self):
        rule = self.section("stroke-precedence")
        for needle in (r"(?i)No stylesheet rule may override a stroke color or width",
                       r"(?i)presentation attribute .* loses to every matching CSS rule",
                       r"(?i)\*\*computed\*\* style", r"(?i)defaults still apply where the data sets nothing"):
            with self.subTest(needle=needle):
                self.assertRegex(rule, needle)

    def test_each_rule_is_stated_once_and_pointed_to(self):
        corpus = " ".join(flat(p.read_text(encoding="utf-8")) for p in PLUGIN.rglob("*.md"))
        self.assertEqual(1, corpus.count("The zoom floor follows the fit"))
        self.assertEqual(1, corpus.count("No stylesheet rule may override a stroke"))
        coloring = self.flat[self.flat.index("### Coloring graph nodes"):]
        coloring = coloring[:coloring.index("#### The encoding self-check")]
        self.assertIn("(#stroke-precedence) (INV-300)", coloring)

    def test_the_capture_carve_out_points_at_the_fit(self):
        self.assertIn("[the initial fit](#graph-initial-fit)", self.flat)


class ModuleSevenChecksTheSnapshotAtScale(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = MODULE_07.read_text(encoding="utf-8")
        start = cls.text.index('<a id="snapshot-scale-check"></a>')
        cls.check = cls.text[start:cls.text.index("asks the Bootcamper nothing (INV-012).", start)]
        cls.flat = flat(cls.check)

    def test_it_runs_the_bundled_helper_on_the_snapshot(self):
        self.assertIn("capture_screenshots.py", self.check)
        self.assertIn("--html docs/visualizations/results_visualization.html --verify-scale", self.check)
        self.assertIn("When the graph is capped", self.flat)

    def test_it_names_the_three_checks_the_helper_reports(self):
        for check in CAP.SCALE_CHECKS:
            with self.subTest(check=check):
                self.assertIn("`%s`" % check, self.check)
        self.assertIn("480 px", self.flat)

    def test_it_runs_before_the_capture(self):
        self.assertLess(self.text.index("](#snapshot-scale-check)"),
                        self.text.index("After generating it, capture screenshots"))

    def test_a_failure_rebuilds_and_checks_again(self):
        self.assertRegex(self.flat, r"\*\*1\*\*: a check failed\. .*rebuild the snapshot and run the check again")

    def test_no_browser_is_skipped_and_named_at_closing_never_passed(self):
        self.assertRegex(self.flat, r"\*\*2\*\*: skipped, no headless browser\..*name the skipped check at "
                                    r"closing \(INV-163\); never report it as passed")
        self.assertRegex(self.flat, r"\*\*3\*\*: a check could not be exercised")

    def test_it_points_at_the_contract_rather_than_restating_it(self):
        self.assertIn("stated once", self.flat)
        self.assertIn("INV-300", self.flat)
        self.assertNotIn("The zoom floor follows the fit", self.flat)

    def test_it_asks_the_bootcamper_nothing(self):
        self.assertNotIn("👉", self.check)


if __name__ == "__main__":
    unittest.main()
