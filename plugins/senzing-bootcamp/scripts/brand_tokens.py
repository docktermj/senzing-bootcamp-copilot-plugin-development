"""Senzing brand tokens — the single, shipped source of truth for visual styling.

Extracted from the Senzing "Obsidian & Ember" style reference
(`resources/senzing-style-reference.pdf`, a maintainer asset that is NOT shipped
with the plugin). The generators that produce bootcamper-facing visual
deliverables — the Truth-Set visualization web app / snapshot
(`senzing_viz_server.py`) and the recap PDF (`generate_recap_pdf.py`) —
consume these tokens so every artifact shares one look and feel, rather than each
hardcoding its own ad hoc palette.

Both consumers import this module from their own directory (it ships alongside
them in `scripts/`) and fall back to an inlined copy of these same values if the
import ever fails, so they never depend on the PDF at runtime and keep working
even in isolation (mirrors the vendored-D3 offline fallback).

Style-guide key rules encoded here:
- Dark backgrounds are Obsidian/Deep, never pure black.
- The accent is the ember family (ember-core on light, ember-hot as the hotter
  tone), never a flat unrelated orange/red.
- Signal green is reserved for live/resolved states — never decorative. It is NOT
  used for categorical data-source node colors.
- Light sections are warm off-white, never cold gray.
- Body text is softer than headline ink; headlines are strongest.
"""
import warnings

# --- Core dark palette ----------------------------------------------------- #
OBSIDIAN = "#0F0D0C"          # global dark background
DEEP = "#18160F"             # nav & cards on dark; also dark ink on light
SURFACE_DARK = "#201E16"     # elevated surface on dark

# --- Ember accent ---------------------------------------------------------- #
EMBER_HOT = "#FF4E1F"        # section labels on dark; hotter accent tone
EMBER_CORE = "#F57826"       # headlines/accent on light; primary accent
EMBER_GRAD_START = "#FF4E1F"  # button/grad-text gradient start
EMBER_GRAD_END = "#F0920A"   # button/grad-text gradient end
EMBER_SOFT = "#FDEEE3"       # derived: light ember tint for chips/pills on light

# --- Reserved signal color (live/resolved states ONLY, never decorative) --- #
SIGNAL_GREEN = "#1D9E75"

# --- Light palette (body sections) ----------------------------------------- #
WHITE = "#FFFFFF"            # light section background
WARM_OFF_WHITE = "#FAF8F3"   # warm off-white (never cold gray)
DARK_INK = "#18160F"         # headlines on light
BODY_INK = "#4A4640"         # body text on light (softer than headline ink)
WARM_LINE = "#E5DFD3"        # derived: warm border/divider on light sections

# On-dark text conventions (headlines pure white; body 60% white).
TEXT_ON_DARK = "#FFFFFF"
MUTED_ON_DARK = "rgba(255,255,255,0.6)"
CARD_BORDER_ON_DARK = "rgba(255,255,255,0.08)"

# --- Typography ------------------------------------------------------------ #
# The guide specifies Roboto (Google Fonts). To stay offline-safe (INV-081 — no
# network at render time) we prefer Roboto when the OS has it and fall back to
# system sans; we do NOT @import a web font. The recap PDF uses fpdf2's built-in
# Helvetica as an offline, dependency-free stand-in (embedding a Roboto TTF would
# add a shipped-asset dependency the "always produces a PDF" guarantee avoids).
FONT_STACK = "Roboto, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
CODE_FONT_STACK = "'Fira Code', 'Courier New', Courier, monospace"
PDF_FONT = "Helvetica"

# --- Categorical data-source node colors (functional data-viz) ------------- #
# The style guide does not define data-source colors; categorical distinctness
# matters here ("where appropriate" latitude). The primary source is anchored to
# ember; signal green is deliberately excluded (reserved). Kept brand-harmonious.
#
# ⛔ SOURCE_COLORS holds **preferred** assignments only — it is NOT the full map.
# These are the Truth Set's source names, and no bootcamper uses them for their own
# data, by definition. A name-keyed lookup therefore collapses every real data source
# to one fallback color, which is worst exactly where cross-source structure is the
# thing worth seeing. Assign colors from the sources actually present, via
# `color_for_sources()`.
SOURCE_COLORS = {
    "CUSTOMERS": EMBER_CORE,
    "REFERENCE": "#3B6EA5",
    "WATCHLIST": "#C8922A",
}
FALLBACK_COLORS = ["#8b5cf6", "#ec4899", "#0ea5e9", "#a3a34a", "#ef4444", "#14b8a6"]

# Additional visual channels for a source beyond the first palette cycle, so a model with
# more sources than colors stays readable instead of silently reusing one (INV-127).
#
# ⛔ The channels are counted as RENDERED, not as returned. A stroke is drawn only when a
# stroke width is set, so "no stroke" is one state and the three stroke colors are three
# more — 4 rendered states, never 3. Counting the returned `stroke` string instead is how
# the capacity was overstated: 3 strokes x 6 fills reads as 18 combinations, the renderer
# drew 24, and the 25th source came out identical to the 7th while the returned dict still
# looked collision-free (every entry carried a distinct `cycle`, which never reaches the
# canvas as anything a reader can see).
SOURCE_STROKES = ["#FFFFFF", "#18160F", "#FAF8F3"]
SOURCE_STROKE_WIDTHS = [1.5, 3.0]
#: Lightness perturbation applied once the stroke states are exhausted: positive blends the
#: fill toward white, negative toward the deep ink. Index 0 is identity, so nothing changes
#: for a model small enough not to need it.
SOURCE_FILL_SHADES = [0.0, 0.30, -0.30, 0.55, -0.55]

#: Distinct rendered stroke states per fill: bare, plus every (stroke color, width) pair.
SOURCE_STROKE_STATES = 1 + len(SOURCE_STROKES) * len(SOURCE_STROKE_WIDTHS)
#: How many sources can be encoded distinctly. Stated so it can be asserted and reported
#: rather than discovered as a collision.
SOURCE_ENCODING_CAPACITY = (
    len(FALLBACK_COLORS) * SOURCE_STROKE_STATES * len(SOURCE_FILL_SHADES)
)


def shade_fill(fill, factor):
    """Blend `fill` toward white (factor > 0) or the deep ink (factor < 0).

    Deterministic and pure: the same fill and factor always give the same hex, so a
    re-rendered snapshot matches the screenshot the recap already describes.
    """
    if not factor:
        return fill
    target = WHITE if factor > 0 else DARK_INK
    weight = abs(factor)
    return "#%02X%02X%02X" % tuple(
        round(a + (b - a) * weight)
        for a, b in zip(hex_to_rgb(fill), hex_to_rgb(target))
    )


def color_for_sources(sources):
    """Map the data-source codes actually present to distinct colors.

    Truth Set names keep their preferred `SOURCE_COLORS` assignment; every other source
    takes the next `FALLBACK_COLORS` entry not already claimed by a preferred one, so two
    sources can never collide on the first cycle. `SIGNAL_GREEN` is never assigned — it is
    reserved for live/resolved states and is explicitly not a categorical color.

    Past the first cycle the encoding widens along three further channels, in order:
    stroke color, stroke width, then a lightness perturbation of the fill itself. That
    gives `SOURCE_ENCODING_CAPACITY` distinct **rendered** appearances — the key the
    browser actually draws being ``(fill, stroke when a width is set, width)``. Up to 24
    sources the rendered result is identical to the pre-widening behavior, which was
    correct at that scale; the widening only adds states past the point it stopped being.

    Beyond capacity a warning is issued rather than colliding silently: an acknowledged
    limit is defensible, an invisible one is not.

    Ordering is deterministic (sorted), so the same model yields the same legend on every
    rebuild — otherwise a re-rendered snapshot or a re-captured screenshot disagrees with
    the recap prose describing it.

    Returns ``{source_code: {"fill": "#RRGGBB", "stroke": "#RRGGBB",
    "stroke_width": float|None, "cycle": int}}``. `stroke_width` is None when no stroke is
    drawn, and it is what a renderer must key on — `cycle` says which wrap a source landed
    in, not whether anything is visible.
    """
    codes = sorted({str(s) for s in (sources or []) if str(s).strip()})
    preferred = {c: SOURCE_COLORS[c] for c in codes if c in SOURCE_COLORS}
    claimed = set(preferred.values())
    available = [c for c in FALLBACK_COLORS if c not in claimed] or list(FALLBACK_COLORS)

    fallback_count = len(codes) - len(preferred)
    if fallback_count > SOURCE_ENCODING_CAPACITY:
        warnings.warn(
            "color_for_sources: %d sources exceed the %d distinct encodings available; "
            "sources past that point repeat an earlier appearance"
            % (fallback_count, SOURCE_ENCODING_CAPACITY),
            stacklevel=2,
        )

    assigned = {}
    nth = 0
    for code in codes:
        if code in preferred:
            fill, cycle = preferred[code], 0
        else:
            fill = available[nth % len(available)]
            cycle = nth // len(available)
            shade = SOURCE_FILL_SHADES[
                (cycle // SOURCE_STROKE_STATES) % len(SOURCE_FILL_SHADES)
            ]
            fill = shade_fill(fill, shade)
            nth += 1
        slot = cycle % SOURCE_STROKE_STATES
        if slot == 0:
            # No stroke drawn. The color is still reported, so the returned shape is
            # unchanged for the common case, but `stroke_width` is None and that is what
            # decides whether anything appears.
            stroke, width = SOURCE_STROKES[0], None
        else:
            k = slot - 1
            stroke = SOURCE_STROKES[(k + 1) % len(SOURCE_STROKES)]
            width = SOURCE_STROKE_WIDTHS[k // len(SOURCE_STROKES)]
        assigned[code] = {
            "fill": fill,
            "stroke": stroke,
            "stroke_width": width,
            "cycle": cycle,
        }
    return assigned


def hex_to_rgb(value):
    """'#RRGGBB' -> (r, g, b) ints, for renderers that take RGB tuples (fpdf2)."""
    v = value.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
