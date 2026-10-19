#!/usr/bin/env python3
"""Render the data-discoveries Markdown into a PDF deliverable.

Reads ``docs/bootcamp_data_discoveries.md`` and writes
``docs/bootcamp_data_discoveries.pdf``.

This is the **sibling** of ``generate_recap_pdf.py``, not a replacement for it.
That script is deliberately recap-shaped: it keeps body text only when it sits
under one of four recognized ``### `` sub-headings, so aiming it at a
discoveries document produced a valid-but-nearly-empty PDF. Rather than
generalize a parser whose strictness is load-bearing for the recap, this script
renders a general Markdown subset and reuses the recap generator's low-level PDF
plumbing (page writer, wrapping, escaping) so there is exactly one hand-rolled
PDF writer in the plugin.

Supported Markdown: an H1 title, ``**Key:** value`` preamble meta lines, H2/H3
headings, ``-``/``*`` bullets at two indent levels, ``**Label:** text`` lines,
fenced code blocks (rendered verbatim), Markdown tables (rendered as a real
grid of rows and columns), and paragraphs. Everything content-bearing is rendered — that is the
point of the audit below.

A valid PDF is ALWAYS produced when the input is sound, via the same tiered
strategy as the recap generator:

1. ``fpdf2`` when importable — a designed cover plus flowing sections.
2. A stdlib-only writer when it is absent. The reporting bootcamper had none of
   ``pandoc``, ``wkhtmltopdf``, ``weasyprint``, ``reportlab`` or ``fpdf2``
   installed, so the fallback is the common case, not an edge case.

Per INV-110 the input is audited **before** rendering and two outcomes are
distinguished:

* **Incomplete but recognizable** (some required sections missing) — warn on
  stderr, render, exit 0. A partial findings document still has value.
* **Not a discoveries document, or catastrophic content loss** (no headings at
  all, none of the required sections present, or content retention below
  ``MIN_CONTENT_RETENTION``) — write the reason to stderr, print no
  ``PDF generated:`` line, write no PDF, and exit non-zero.

Success signal: on success it prints a line beginning ``PDF generated:`` and
exits 0. Any other outcome means no PDF was written.

Usage:
    python3 generate_discoveries_pdf.py [--input docs/bootcamp_data_discoveries.md]
                                        [--output docs/bootcamp_data_discoveries.pdf]
                                        [--check]

``--check`` audits without rendering and exits non-zero if the document would
not render usefully.

Copying this script elsewhere: it imports the shared PDF plumbing from
``generate_recap_pdf.py`` (expected next to this script) and the palette from
``brand_tokens.py``. Copy **all three** together; a lone copy either fails loudly
on the first import or falls back to the inlined palette, and says so on stderr
(INV-111).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# The recap generator ships in this same directory. Reuse its PDF plumbing
# rather than carrying a second copy of a hand-rolled page writer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from generate_recap_pdf import (  # noqa: E402
        _md_inline_to_text,
        _pdf_escape,
        _safe,
        _wrap,
        _write_pdf,
        dropped_character_warning,
    )
except ImportError as exc:  # pragma: no cover - a broken install, not a data case
    sys.stderr.write(
        "Cannot import the shared PDF helpers from generate_recap_pdf.py "
        f"(expected next to this script): {exc}\n"
    )
    raise SystemExit(2)

# Inlined fallback palette, in ONE named place so it is both testable and unduplicated.
# It must stay equal to the values `brand_tokens` derives (INV-107's property, which names
# only `senzing_viz_server.py` and `generate_recap_pdf.py`; this generator has the same
# fallback-drift surface and `tests/test_brand_sync.py` now asserts it here too). It was
# previously written out twice, once per `except` branch — two copies of the same literals
# is the drift surface, not a safeguard.
_FALLBACK_RGB = {
    "EMBER": (245, 120, 38),
    "DARK_INK": (24, 22, 15),
    "BODY_INK": (74, 70, 64),
    "WARM_LINE": (229, 223, 211),
}


def _use_fallback_palette():
    return (
        _FALLBACK_RGB["EMBER"],
        _FALLBACK_RGB["DARK_INK"],
        _FALLBACK_RGB["BODY_INK"],
        _FALLBACK_RGB["WARM_LINE"],
    )


try:
    import brand_tokens  # type: ignore

    EMBER = brand_tokens.hex_to_rgb(brand_tokens.EMBER_CORE)
    DARK_INK = brand_tokens.hex_to_rgb(brand_tokens.DARK_INK)
    BODY_INK = brand_tokens.hex_to_rgb(brand_tokens.BODY_INK)
    WARM_LINE = brand_tokens.hex_to_rgb(brand_tokens.WARM_LINE)
except ModuleNotFoundError:  # pragma: no cover - falls back to inlined brand values
    # INV-111: a degraded path is never inferred from silence. The two branches stay
    # distinct because they are different failures — say which occurred, since a
    # project-local copy of this script without brand_tokens.py beside it is easy to
    # create by accident, and "present but unusable" points somewhere else entirely.
    sys.stderr.write(
        f"brand_tokens.py not importable from {Path(__file__).resolve().parent} "
        "(copy it next to this script); using the inlined brand palette.\n"
    )
    EMBER, DARK_INK, BODY_INK, WARM_LINE = _use_fallback_palette()
except Exception as exc:  # pragma: no cover - present but unusable
    sys.stderr.write(
        f"brand_tokens.py present but unusable ({exc}); using the inlined brand palette.\n"
    )
    EMBER, DARK_INK, BODY_INK, WARM_LINE = _use_fallback_palette()

# Header-row fill for rendered tables. Derived from the warm line color so the
# grid stays inside the brand palette rather than introducing a new tone.
TABLE_HEAD_FILL = tuple(min(255, c + 12) for c in WARM_LINE)

# The two document-specific strings on the cover. Named because they are the ONLY part
# of the layout engine that is not document-agnostic — everything else (section styling,
# tables, typography) carries nothing discoveries-specific. Rendering another document
# without overriding these puts "What Senzing found in your data" on its cover, which on
# a stakeholder-facing keepsake is worse than no cover line at all.
COVER_TITLE_FALLBACK = "Data Discoveries"
COVER_SUBTITLE = "What Senzing found in your data"

DEFAULT_INPUT = "docs/bootcamp_data_discoveries.md"
DEFAULT_OUTPUT = "docs/bootcamp_data_discoveries.pdf"

# The findings a complete discoveries document carries. Matched case- and
# punctuation-insensitively against H2 headings, so a document may word them
# more naturally ("What Senzing did NOT find, and why") and still match.
REQUIRED_SECTIONS = [
    "headline numbers",
    "merges and match keys",
    "review queue",
    "why and how",
    "relationship networks",
    "what was not found",
]

# Minimum share of the input's content-bearing characters that must survive into
# the parsed document. This renderer keeps essentially everything that is not a
# blank line or a horizontal rule, so a sound document retains ~99%. A value far
# below that means the input is not what this script parses.
MIN_CONTENT_RETENTION = 0.60


@dataclass
class Block:
    """One renderable unit of the document."""

    kind: str  # h2 | h3 | bullet | subbullet | label | code | table | text
    text: str
    label: str = ""


@dataclass
class Discoveries:
    title: str = ""
    # Cover strings, overridable per document. Empty means "use the defaults", so the
    # discoveries path is unaffected and the two renderers cannot drift on this.
    subtitle: str = ""
    meta: List[Tuple[str, str]] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)

    def headings(self) -> List[str]:
        return [b.text for b in self.blocks if b.kind in ("h2", "h3")]


# Vertical separation between consecutive blocks — a blank line's worth, so that
# neither consecutive paragraphs nor consecutive list items merge into one
# undifferentiated run of text. Sized to roughly one body line so it reads as a
# paragraph break rather than mere padding.
ITEM_GAP_MM = 3.6
ITEM_GAP_PT = 5.0

_LIST_KINDS = ("bullet", "subbullet")


# Block kinds that read as prose and therefore need a blank line after them, so
# consecutive paragraphs do not merge into one wall of text. Headings bring
# their own leading space; a code or table block delimits itself against prose
# but NOT against another one of its own kind (see `_needs_item_gap`).
_PROSE_KINDS = ("text", "label")


def _needs_item_gap(blocks: List[Block], index: int) -> bool:
    """True when block ``index`` should be followed by a blank line's space.

    Two cases, both about keeping author-intended boundaries visible:

    * **List items** — a gap between consecutive items, so a multi-line bullet
      cannot blend into the next one (its wrapped lines sit at the same
      spacing otherwise).
    * **Paragraphs** — a gap after prose that is followed by more prose, a
      list, or a table. Without it, separate paragraphs render as one
      continuous block and the author's structure is lost.

    Gating on the *next* block keeps the gap strictly **between** things: it
    never trails the last item before a heading, which already brings its own
    leading space.
    """
    kind = blocks[index].kind
    nxt = blocks[index + 1] if index + 1 < len(blocks) else None
    if nxt is None or nxt.kind in ("h2", "h3"):
        return False
    if kind in _LIST_KINDS:
        return nxt.kind in _LIST_KINDS or nxt.kind in _PROSE_KINDS
    # `label` needs no carve-out: the parser absorbs a soft-wrapped continuation
    # into the label block itself, so a `text` block after one is a genuinely new
    # paragraph and takes a gap like any other. Suppressing the gap here was the
    # workaround for that split, and it hid a real paragraph boundary.
    if kind in _PROSE_KINDS:
        return nxt.kind in _PROSE_KINDS + _LIST_KINDS + ("code", "table")
    if kind in ("code", "table"):
        # Including code/table in the follow-set matters: two adjacent tables
        # drawn with no gap share an edge and read as ONE grid whose middle row
        # happens to be bold — the second table's header. The parser separates
        # them correctly; only the spacing hid it.
        return nxt.kind in _PROSE_KINDS + _LIST_KINDS + ("code", "table")
    return False


def _normalize(text: str) -> str:
    """Lowercase, strip Markdown emphasis and punctuation, collapse spaces."""
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


# Specific long-form "**Label:** paragraph" callouts that always break to their own
# line (label, then a blank-line gap, then an indented body) rather than continuing
# inline after the label. Deliberately an allowlist, not every `label` block: a short
# label like "**Cross-source overlap:** ..." reads fine inline with its wrapped
# continuation, and forcing every label onto its own line would put a blank line
# mid-sentence for those (see TestParagraphsAreSeparated in tests/test_discoveries_pdf.py).
_NEW_LINE_LABELS = ("near miss the one that teaches more", "measurement")


def parse_discoveries(text: str) -> Discoveries:
    doc = Discoveries()
    in_code = False
    in_preamble = True
    paragraph: List[str] = []
    last_was_table = False
    # A "**Label:** text" line opens a paragraph that plain following lines
    # continue, exactly as an unlabeled paragraph does. Holding the block here
    # lets those lines be absorbed into it instead of becoming a second block —
    # a split that put a blank line into the middle of a sentence.
    open_label: List[Block] = []

    def flush_paragraph() -> None:
        open_label.clear()
        if paragraph:
            doc.blocks.append(Block("text", " ".join(paragraph).strip()))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        # Only an *immediately* adjacent pipe row continues the current table.
        # Reset first and let the table branch re-arm it, so that any other
        # line — including the blank line between two consecutive tables, which
        # returns early — separates them.
        prev_was_table = last_was_table
        last_was_table = False

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = not in_code
            continue
        if in_code:
            # Verbatim: match keys, JSON fragments and entity IDs live here.
            doc.blocks.append(Block("code", line))
            continue

        if not stripped or stripped == "---":
            flush_paragraph()
            continue

        if stripped.startswith("# ") and not doc.title:
            doc.title = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            in_preamble = False
            doc.blocks.append(Block("h2", stripped[3:].strip()))
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            in_preamble = False
            doc.blocks.append(Block("h3", stripped[4:].strip()))
            continue

        # Preamble "**Key:** value" lines become document metadata.
        meta = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", stripped)
        if meta and in_preamble and not stripped.startswith(("-", "*")):
            doc.meta.append((meta.group(1).strip(), meta.group(2).strip()))
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            # Consecutive pipe rows form ONE table block, so the renderer can
            # draw a real grid. Emitting one block per row (as this did before)
            # forces every renderer to fall back to verbatim pipe text, which
            # is what reached the deliverable: a Markdown table printed as
            # source rather than rows and columns.
            flush_paragraph()
            if prev_was_table and doc.blocks and doc.blocks[-1].kind == "table":
                doc.blocks[-1].text += "\n" + stripped
            else:
                doc.blocks.append(Block("table", stripped))
            last_was_table = True
            continue

        bullet = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if bullet:
            flush_paragraph()
            kind = "subbullet" if len(bullet.group(1)) >= 2 else "bullet"
            body = bullet.group(2).strip()
            lm = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", body)
            if lm:
                doc.blocks.append(Block(kind, lm.group(2).strip(), lm.group(1).strip()))
            else:
                doc.blocks.append(Block(kind, body))
            continue

        lm = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", stripped)
        if lm:
            flush_paragraph()
            block = Block("label", lm.group(2).strip(), lm.group(1).strip())
            doc.blocks.append(block)
            open_label.append(block)
            continue

        # A plain line directly under a label continues that label's paragraph.
        if open_label and not paragraph:
            open_label[0].text = (open_label[0].text + " " + stripped).strip()
            continue

        paragraph.append(stripped)

    flush_paragraph()
    return doc


def _source_content_chars(text: str) -> int:
    """Content-bearing characters in the source, ignoring blanks and rules."""
    total = 0
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped == "---" or stripped.startswith("```"):
            continue
        total += len(stripped)
    return total


def _rendered_content_chars(doc: Discoveries) -> int:
    total = len(doc.title)
    for key, value in doc.meta:
        total += len(key) + len(value)
    for block in doc.blocks:
        total += len(block.text.strip()) + len(block.label)
    return total


@dataclass
class DiscoveriesAudit:
    ok: bool
    fatal: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    retention: float = 0.0
    missing_sections: List[str] = field(default_factory=list)
    # How many of the *expected* sections were found, against how many were expected.
    # Reported instead of deriving the denominator from REQUIRED_SECTIONS, which is
    # only the default: with --require-sections the constant is not the yardstick.
    sections_present: int = 0
    sections_expected: int = 0


def audit_discoveries(
    doc: Discoveries,
    source: str,
    required_sections: Optional[Sequence[str]] = None,
) -> DiscoveriesAudit:
    """Decide whether this document can render as a useful deliverable.

    Mirrors the recap generator's two-outcome contract (INV-110): an imperfect
    document still renders; a document this script cannot meaningfully parse
    does not, because an empty deliverable is worse than none.

    ``required_sections`` defaults to ``REQUIRED_SECTIONS`` — the discoveries
    document's own headings — so an unparameterized call behaves exactly as before.
    Pass a different list to render another document in the same house style, or an
    empty list to skip the section check entirely.

    ⚠️ **The section check is not the guard that stops this being pointed at
    unrelated Markdown** — the retention floor is, and it is not affected by this
    parameter. The section list only says *which* document this is expected to be.
    """
    required = list(REQUIRED_SECTIONS if required_sections is None else required_sections)
    fatal: List[str] = []
    warnings: List[str] = []

    source_chars = _source_content_chars(source)
    rendered_chars = _rendered_content_chars(doc)
    retention = (rendered_chars / source_chars) if source_chars else 0.0

    normalized = [_normalize(h) for h in doc.headings()]
    missing = [
        wanted
        for wanted in required
        if not any(_normalize(wanted) in heading for heading in normalized)
    ]
    present = len(required) - len(missing)

    if not doc.blocks:
        fatal.append("the document has no content-bearing lines")
    elif not doc.headings():
        fatal.append("the document has no '## ' sections")
    elif required and present == 0:
        fatal.append(
            "none of the required sections is present "
            f"(looked for: {', '.join(required)})"
        )

    if source_chars and retention < MIN_CONTENT_RETENTION:
        fatal.append(
            f"content retention {retention:.0%} is below the "
            f"{MIN_CONTENT_RETENTION:.0%} minimum — most of the input would be dropped"
        )

    if missing and present:
        warnings.append(
            "missing sections: " + ", ".join(missing) + " — rendering anyway"
        )

    return DiscoveriesAudit(
        ok=not fatal,
        fatal=fatal,
        warnings=warnings,
        retention=retention,
        missing_sections=missing,
        sections_present=present,
        sections_expected=len(required),
    )


def render_with_fpdf2(doc: Discoveries, output: Path) -> bool:
    try:
        from fpdf import FPDF  # type: ignore
    except ModuleNotFoundError:
        return False
    except Exception as exc:  # a broken install is worth reporting, not hiding
        sys.stderr.write(f"fpdf2 present but unusable ({exc}); using the stdlib renderer.\n")
        return False

    try:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()
        epw = pdf.w - pdf.l_margin - pdf.r_margin

        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*DARK_INK)
        _full_width(pdf, epw, 10, _safe(doc.title or COVER_TITLE_FALLBACK))
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*EMBER)
        _full_width(pdf, epw, 7, _safe(doc.subtitle or COVER_SUBTITLE))
        pdf.ln(2)

        pdf.set_text_color(*BODY_INK)
        pdf.set_font("Helvetica", "", 10.5)
        for key, value in doc.meta:
            _full_width(pdf, epw, 5.5, _safe(f"{key}: {_md_inline_to_text(value)}"))
        if doc.meta:
            pdf.ln(3)

        for index, block in enumerate(doc.blocks):
            _render_block_fpdf2(pdf, epw, block)
            if _needs_item_gap(doc.blocks, index):
                pdf.ln(ITEM_GAP_MM)

        _ensure_parent(output)
        pdf.output(str(output))
        return True
    except Exception as exc:
        sys.stderr.write(f"fpdf2 rendering failed ({exc}); using the stdlib renderer.\n")
        return False


def parse_table(text: str) -> Tuple[List[str], List[List[str]]]:
    """Split a Markdown table block into (header, rows).

    The ``|---|---|`` alignment row is dropped; it is presentation, not content.
    Ragged rows are padded or truncated to the header's column count so a
    malformed row cannot desynchronize the grid.

    **An empty leading column is kept, deliberately.** A table written
    ``| | Entity | Name |`` has a blank *header* over a real row-label column;
    dropping the column would delete the ``1``/``2`` beneath it. Only a wholly
    empty column could be dropped safely, and telling the two apart requires
    scanning every row to discard something whose worst case is a narrow empty
    cell — a poor trade against silently losing a column that carries data.
    Faithful to the source is the rule here (cf. INV-110).
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parsed: List[List[str]] = []
    for line in lines:
        if re.fullmatch(r"\|[\s:|-]+\|", line):
            continue  # alignment row
        cells = [c.strip() for c in line.strip("|").split("|")]
        parsed.append(cells)
    if not parsed:
        return [], []
    header, body = parsed[0], parsed[1:]
    width = len(header)
    body = [(row + [""] * width)[:width] for row in body]
    return header, body


def _render_table_fpdf2(pdf, epw: float, block: Block) -> None:
    """Draw a Markdown table as an actual grid of rows and columns.

    Column widths are proportional to the longest cell in each column, so a
    narrow count column does not get the same width as a long match key, and
    every column keeps a floor so nothing collapses to a sliver.
    """
    header, rows = parse_table(block.text)
    if not header:
        return

    plain_header = [_safe(_md_inline_to_text(c)) for c in header]
    plain_rows = [[_safe(_md_inline_to_text(c)) for c in row] for row in rows]

    # Proportional widths from the longest cell per column, with a floor and a
    # cap so one very long cell cannot squeeze the others out.
    spans = []
    for index in range(len(plain_header)):
        longest = max(
            [len(plain_header[index])] + [len(r[index]) for r in plain_rows] or [1]
        )
        spans.append(min(max(longest, 6), 60))
    total = float(sum(spans)) or 1.0
    widths = [epw * (span / total) for span in spans]

    line_h = 4.6
    pdf.set_draw_color(*WARM_LINE)
    pdf.set_line_width(0.15)

    def emit_row(cells: List[str], is_header: bool) -> None:
        pdf.set_font("Helvetica", "B" if is_header else "", 8.5)
        # Height = tallest wrapped cell in this row.
        heights = []
        for width, cell in zip(widths, cells):
            lines = pdf.multi_cell(
                width, line_h, cell or " ", dry_run=True, output="LINES", border=0
            )
            heights.append(max(len(lines), 1) * line_h)
        row_h = max(heights)

        if pdf.will_page_break(row_h):
            pdf.add_page()
            # Repeat the header on the new page so a split table stays readable.
            if not is_header:
                emit_row(plain_header, True)
                # That call left the font bold and the fill armed for a header
                # row; restore this row's own style, or the first body row after
                # every page break renders as a second header.
                pdf.set_font("Helvetica", "", 8.5)

        x0, y0 = pdf.l_margin, pdf.get_y()
        if is_header:
            pdf.set_fill_color(*TABLE_HEAD_FILL)
            pdf.set_text_color(*DARK_INK)
        else:
            pdf.set_text_color(*BODY_INK)

        x = x0
        for width, cell in zip(widths, cells):
            pdf.set_xy(x, y0)
            pdf.multi_cell(
                width, line_h, cell or " ", border=1, align="L",
                fill=is_header, max_line_height=line_h,
                new_x="RIGHT", new_y="TOP",
            )
            # multi_cell only advances by its own wrapped height, so pad the
            # cell out to the row height and keep the grid square.
            drawn = max(
                len(pdf.multi_cell(width, line_h, cell or " ", dry_run=True,
                                   output="LINES", border=0)),
                1,
            ) * line_h
            if drawn < row_h:
                # One call, styled by row type — the recap generator's mirror of this
                # function (INV-142) does exactly this. Stroking first and then
                # re-drawing headers with "FD" painted the same rectangle twice.
                pdf.rect(x, y0 + drawn, width, row_h - drawn,
                         style="FD" if is_header else "D")
            x += width
        pdf.set_xy(x0, y0 + row_h)

    emit_row(plain_header, True)
    for row in plain_rows:
        emit_row(row, False)
    pdf.set_text_color(*BODY_INK)


def _full_width(pdf, width: float, height: float, text: str, indent: float = 0.0) -> None:
    """``multi_cell`` that always starts at the left margin (plus ``indent``).

    fpdf2's ``multi_cell`` defaults to ``new_x=RIGHT``, leaving the cursor at the
    right margin — measured at x = 200 mm on a 210 mm page after a full-width call.
    A following ``multi_cell(epw, ...)`` then draws from 200 mm across the full
    width: entirely off-sheet, rendering as blank space with no error raised and no
    effect on the content-retention figure, because the text *is* in the content
    stream — merely positioned outside the page box.

    Every full-width write goes through here so a new block kind cannot be added
    without inheriting the reset. Do NOT use this for text that must continue on the
    current line (a bullet's body after its prefix and bold label) — that path sets x
    itself.
    """
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(width, height, text)


def _render_block_fpdf2(pdf, epw: float, block: Block) -> None:
    if block.kind == "h2":
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*EMBER)
        _full_width(pdf, epw, 7.5, _safe(_md_inline_to_text(block.text)))
        pdf.set_draw_color(*WARM_LINE)
        y = pdf.get_y() + 1
        pdf.line(pdf.l_margin, y, pdf.l_margin + epw, y)
        pdf.ln(3)
        return
    if block.kind == "h3":
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*DARK_INK)
        _full_width(pdf, epw, 6, _safe(_md_inline_to_text(block.text)))
        pdf.ln(1)
        return

    pdf.set_text_color(*BODY_INK)
    if block.kind == "code":
        pdf.set_font("Courier", "", 9)
        _full_width(pdf, epw, 4.6, _safe(block.text) or " ")
        return
    if block.kind == "table":
        _render_table_fpdf2(pdf, epw, block)
        return

    indent = 0.0
    prefix = ""
    if block.kind == "bullet":
        indent, prefix = 6.0, "-  "
    elif block.kind == "subbullet":
        indent, prefix = 12.0, "-  "

    pdf.set_x(pdf.l_margin + indent)
    if prefix:
        pdf.set_font("Helvetica", "", 10.5)
        pdf.cell(6, 5.5, prefix)
    # A long-form "**Label:** paragraph" callout named in _NEW_LINE_LABELS always
    # breaks to its own line: the label, a blank-line gap, then the body indented to
    # match bullet text (6 mm list indent + the 6 mm bullet cell = 12 mm) -- never
    # hanging-indented under wherever the label happened to end. Short labels (not in
    # the allowlist) keep the existing inline-with-wrap behavior below.
    force_new_line = block.kind == "label" and _normalize(block.label) in _NEW_LINE_LABELS
    if block.label:
        pdf.set_font("Helvetica", "B", 10.5)
        if force_new_line:
            pdf.multi_cell(epw - indent, 5.5, _safe(block.label + ":"))
            pdf.ln(4.8)
            indent += 12.0
            pdf.set_x(pdf.l_margin + indent)
        else:
            label = _safe(block.label + ": ")
            pdf.cell(pdf.get_string_width(label) + 1, 5.5, label)
    pdf.set_font("Helvetica", "", 10.5)
    remaining = epw - (pdf.get_x() - pdf.l_margin)
    # A long bold label leaves a narrow column, and every wrapped line then stacks in
    # it beside a large empty gutter. A bare 20 mm floor is an order of magnitude too
    # low to catch that: ~60 mm of a 190 mm line clears it comfortably and still reads
    # as a ribbon. Break once the label has eaten half the width, continuing at a
    # modest hanging indent — short labels still render inline, which reads well.
    if not force_new_line and remaining < max(20.0, epw * 0.5):
        indent = min(indent + 6.0, epw - 20.0)
        remaining = epw - indent
        pdf.ln(5.5)
        pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(remaining, 5.5, _safe(_md_inline_to_text(block.text)) or " ")


def render_with_stdlib(doc: Discoveries, output: Path) -> bool:
    """Write a valid, paginated PDF using only the standard library."""
    try:
        page_w, page_h = 595.0, 842.0  # A4 in points
        margin = 54.0
        line_h = 14.0
        max_width_chars = 92

        tokens: List[Tuple[str, str, float, float]] = []

        def add(text: str, font: str = "F1", size: float = 10.5, indent: float = 0.0) -> None:
            # Mirrors the recap generator's stdlib path: sanitize at the token boundary so
            # `_pdf_escape` only ever sees Latin-1 and never substitutes (INV-143). Both
            # writers share `_pdf_escape`, so both need this — it is not enough to fix one.
            tokens.append((_safe(text), font, size, indent))

        def add_wrapped(text: str, font: str, size: float, indent: float) -> None:
            width = max(20, max_width_chars - int(indent / 6))
            # Sanitize before wrapping: `_wrap` counts characters and transliteration can
            # change the count ("∞" -> "infinity").
            for chunk in _wrap(_safe(text), width):
                add(chunk, font, size, indent)

        def add_gap(points: float) -> None:
            """Advance by an exact number of points, below the line-height floor.

            An ordinary empty token still costs a full ``line_h``; an inter-item gap
            needs to be smaller than a line or it reads as a paragraph break.
            """
            tokens.append(("", "GAP", points, 0.0))

        add(doc.title or COVER_TITLE_FALLBACK, "F2", 20, 0)
        add(doc.subtitle or COVER_SUBTITLE, "F1", 12, 0)
        add("", "F1", 6, 0)
        for key, value in doc.meta:
            add_wrapped(f"{key}: {_md_inline_to_text(value)}", "F1", 11, 0)
        if doc.meta:
            add("", "F1", 6, 0)

        for index, block in enumerate(doc.blocks):
            if block.kind == "h2":
                add("", "F1", 6, 0)
                add_wrapped(_md_inline_to_text(block.text), "F2", 14, 0)
                continue
            if block.kind == "h3":
                add("", "F1", 3, 0)
                add_wrapped(_md_inline_to_text(block.text), "F2", 11.5, 0)
                continue
            if block.kind == "code":
                add(block.text[:max_width_chars], "F1", 9, 12)
                continue
            if block.kind == "table":
                # No grid primitives in the stdlib writer, so lay the table out
                # as space-padded monospace columns. Still rows and columns —
                # not the raw pipe source the parser was handed.
                header, rows = parse_table(block.text)
                if not header:
                    continue
                cols = [[_md_inline_to_text(c) for c in header]] + [
                    [_md_inline_to_text(c) for c in r] for r in rows
                ]
                widths = [
                    min(max(len(row[i]) for row in cols), 46)
                    for i in range(len(header))
                ]
                for row_index, row in enumerate(cols):
                    line = "  ".join(
                        cell[:w].ljust(w) for cell, w in zip(row, widths)
                    ).rstrip()
                    # F3 is monospace. Space-padding a PROPORTIONAL face produces
                    # ragged pseudo-columns, which is not the aligned monospace
                    # rendering INV-142 permits as the lesser path.
                    add(line[:max_width_chars], "F3", 9, 12)
                    if row_index == 0:
                        rule = "  ".join("-" * w for w in widths)
                        add(rule[:max_width_chars], "F3", 9, 12)
                continue
            indent = 12.0 if block.kind == "bullet" else 24.0 if block.kind == "subbullet" else 0.0
            body = _md_inline_to_text(block.text)
            if block.label:
                body = f"{block.label}: {body}".rstrip(": ")
            if block.kind in ("bullet", "subbullet"):
                body = "- " + body
            add_wrapped(body, "F1", 10.5, indent)
            # Mirror the fpdf2 path's inter-item gap so the two renderers do not drift.
            if _needs_item_gap(doc.blocks, index):
                add_gap(ITEM_GAP_PT)

        pages: List[str] = []
        current: List[str] = []
        y = page_h - margin

        def flush_page() -> None:
            if current:
                pages.append("\n".join(current))
                current.clear()

        for text, font, size, indent in tokens:
            # A "GAP" token is pure vertical space; it never emits a font reference.
            advance = size if font == "GAP" else max(line_h, size + 3.5)
            if y < margin + advance:
                flush_page()
                y = page_h - margin
            if text:
                current.append(
                    f"BT /{font} {size} Tf {margin + indent} {y} Td "
                    f"({_pdf_escape(text)}) Tj ET"
                )
            y -= advance
        flush_page()

        if not pages:
            pages = [""]
        _ensure_parent(output)
        _write_pdf(output, pages, [(page_w, page_h)] * len(pages))
        return True
    except Exception as exc:
        sys.stderr.write(f"Stdlib PDF rendering failed: {exc}\n")
        return False


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[List[str]] = None, description: Optional[str] = None) -> int:
    # `description` lets the generate_document_pdf.py alias introduce itself in its own words
    # in --help without building a parser of its own; None keeps this script's own first line.
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if description is None else description
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="audit the input without rendering; non-zero exit if it would not render usefully",
    )
    parser.add_argument(
        "--require-sections",
        default=None,
        metavar="A;B;C",
        help="semicolon-separated section names this document must carry, replacing the "
        "discoveries defaults. Semicolons rather than commas because section names "
        "contain commas ('merges and match keys', 'why and how'). Matched the same way "
        "as the defaults: case- and punctuation-insensitively against H2 headings.",
    )
    parser.add_argument(
        "--subtitle",
        default=None,
        help="cover subtitle. Defaults to the discoveries line; override it for any other "
        "document, or a stakeholder-facing keepsake ships with the wrong one.",
    )
    parser.add_argument(
        "--no-section-check",
        action="store_true",
        help="skip the section check entirely. The content-retention floor still applies "
        "and is what actually prevents rendering unrelated Markdown.",
    )
    args = parser.parse_args(argv)

    # Omitting both flags leaves the discoveries behavior byte-for-byte unchanged.
    if args.no_section_check:
        required_sections: Optional[List[str]] = []
    elif args.require_sections is not None:
        required_sections = [
            s.strip() for s in args.require_sections.split(";") if s.strip()
        ]
        if not required_sections:
            sys.stderr.write(
                "--require-sections was given but names no sections; pass "
                "--no-section-check if that is what you meant.\n"
            )
            return 1
    else:
        required_sections = None

    source_path = Path(args.input)
    if not source_path.exists():
        sys.stderr.write(f"Input not found: {source_path}\n")
        return 1
    try:
        source = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # Exists but is not UTF-8 — an editor that saves cp1252/ANSI is the usual cause.
        # Refuse with a message the guide can relay rather than a traceback, and write no
        # PDF (INV-110). Do NOT re-read with errors="replace": the document is the
        # bootcamper's, and silently mangling their text is not ours to do.
        sys.stderr.write(
            f"Input is not valid UTF-8: {source_path} ({exc}). No PDF written. "
            f"Re-save it as UTF-8 and run this again.\n"
        )
        return 1

    doc = parse_discoveries(source)
    if args.subtitle is not None:
        doc.subtitle = args.subtitle
    audit = audit_discoveries(doc, source, required_sections)

    for warning in audit.warnings:
        sys.stderr.write(f"Warning: {warning}\n")

    if not audit.ok:
        sys.stderr.write(
            f"Refusing to render {source_path}: " + "; ".join(audit.fatal) + "\n"
        )
        sys.stderr.write(
            "No PDF was written. Fix the document and re-run — an empty "
            "deliverable is worse than none.\n"
        )
        return 1

    if args.check:
        sys.stdout.write(
            f"OK: {source_path} would render "
            f"({audit.retention:.0%} of its content, "
            f"{audit.sections_present}/{audit.sections_expected} "
            f"expected sections present).\n"
        )
        return 0

    output = Path(args.output)
    for renderer, name in ((render_with_fpdf2, "fpdf2"), (render_with_stdlib, "stdlib")):
        if renderer(doc, output):
            # Characters the built-in fonts could not render were dropped from the page.
            # Reported once, after the renderer that succeeded has been through the whole
            # document, and BEFORE the success line so it cannot be mistaken for noise
            # following a clean result. `content retained` cannot catch this: it is
            # measured over parsed source characters, before `_safe` runs at render time,
            # which is why a Cyrillic organization name vanished at "retained: 96%".
            dropped = dropped_character_warning()
            if dropped:
                sys.stderr.write(dropped)
            sys.stdout.write(
                f"PDF generated: {output} (renderer: {name}, "
                f"content retained: {audit.retention:.0%})\n"
            )
            return 0

    sys.stderr.write("Failed to generate a PDF by any strategy.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
