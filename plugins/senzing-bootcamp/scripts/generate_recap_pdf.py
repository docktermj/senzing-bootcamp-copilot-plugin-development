#!/usr/bin/env python3
"""Render the bootcamp recap Markdown into a professional recap PDF.

Reads ``docs/bootcamp_recap.md`` and writes ``docs/bootcamp_recap.pdf``.

A valid PDF is ALWAYS produced, via a tiered strategy:

1. Rich renderer using ``fpdf2`` when it is importable: a designed cover page
   plus one section per completed module, each carrying its four labeled
   sub-sections (Information Shared, Questions & Responses, Actions Taken,
   End-of-Module Summary; legacy "Journal" is accepted as an alias).
2. Stdlib-only fallback writer when ``fpdf2`` is absent: a plainer but valid,
   paginated PDF rendered from the same parsed content, with no third-party
   dependency.

The script is dependency-light: its only optional sibling import is ``brand_tokens``
(the shared Senzing brand palette that ships next to it in ``scripts/``), and it
falls back to an inlined copy of those values if that module is unavailable — so it
still works when bundled inside the GitHub Copilot plugin and invoked from a bootcamp
working directory, and always produces a valid PDF.

Success signal (matches the graduation skill's contract): on success it prints
a line beginning ``PDF generated:`` and exits 0. Any other outcome means no PDF
was written.

Required input structure. This is NOT a general-purpose Markdown renderer: it
reads the bootcamp recap structure specifically —

    # <Recap title>
    **Bootcamper:** <name>          <- preamble "**Key:** value" meta lines

    ## <Module name> — <date>       <- one H2 section per completed module
    ### Information Shared          <- content lives under these H3 headings
    ### Questions & Responses
    ### Actions Taken
    ### End-of-Module Summary       <- carries three labeled blocks (INV-103):
    **What you accomplished:** …       What you accomplished, Files produced,
    **Files produced:** …              Why it matters. A block the recap does not
    **Why it matters:** …              record renders as "(not recorded)" rather
                                       than vanishing, and `--check` reports it.

Body text is kept only when it sits under an H3 sub-heading of a module section
(see ``parse_recap``), so a document whose H2 sections have no recognized
sub-headings renders as headings with empty bodies. To keep that from shipping
as a plausible-looking but empty deliverable, the input is audited **before**
rendering and two outcomes are distinguished:

* **Incomplete but recognizable** (e.g. one module missing a sub-section) —
  warn on stderr, render, exit 0. Graduation is non-blocking, so an imperfect
  recap still produces its PDF.
* **Not a recap, or catastrophic content loss** (no module sections, no section
  carrying any recognized sub-section, or content retention below
  ``MIN_CONTENT_RETENTION``) — write the reason to stderr, print no
  ``PDF generated:`` line, write no PDF, and exit non-zero. Here an empty
  deliverable would be worse than none.

Every successful render also reports a content-retention figure, so silent
truncation is visible without extracting the PDF's text.

Usage:
    python3 generate_recap_pdf.py [--input docs/bootcamp_recap.md]
                                  [--output docs/bootcamp_recap.pdf]
                                  [--check]

``--check`` verifies, without rendering, that every module section in the
recap carries the required labeled sub-sections and exits non-zero if any are
missing.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_INPUT = "docs/bootcamp_recap.md"
DEFAULT_OUTPUT = "docs/bootcamp_recap.pdf"

# The labeled sub-sections a complete per-module recap section carries. The
# graduation recap requirement names Information Shared, Questions &
# Responses, Actions Taken, and End-of-Module Summary (INV-103; it replaced the
# former "Journal"). "Actions Taken" / "Action Taken" and legacy "Journal" /
# "End-of-Module Summary" are accepted as aliases on parse (see _normalize_heading).
REQUIRED_SECTIONS = [
    "Information Shared",
    "Questions & Responses",
    "Actions Taken",
    "End-of-Module Summary",
]

# The labeled blocks the End-of-Module Summary must carry (INV-103, persisting the
# bootcamper-facing epilog of INV-032 into the keepsake). "Bootcamper's takeaway" is
# deliberately absent: it is optional and omitted when the bootcamper gave none.
#
# These are checked and rendered, not merely documented. INV-103 has required them since
# 2026-07-23 and `--check` validated only the *heading*, so a summary written as a prose
# paragraph — no labels at all — passed as "Recap complete" and reached the keepsake with
# the three blocks simply absent. Nothing downstream could see it: the heading was there,
# retention was ~100%, and the PDF looked fine.
END_SUMMARY_BLOCKS = [
    "What you accomplished",
    "Files produced",
    "Why it matters",
]

# Shown on the Certificate of Completion (INV-100) when the recap carries no
# bootcamper name. Both renderers reach it through `_cert_fields`; `main()` warns
# on stderr whenever it is used (INV-113) — a certificate is the one artifact
# where a placeholder name is immediately visible and permanently wrong, so the
# substitution must never be silent.
CERTIFICATE_NAME_PLACEHOLDER = "Bootcamper"

# Fence markers the durability hooks (INV-059) wrap their folded checkpoint in.
# They must match `scripts/recap_checkpoint.py`; a block still present at render
# time means a module was never finalized (module-completion step 2d).
RECAP_CHECKPOINT_START = "<!-- RECAP-CHECKPOINT:START -->"
RECAP_CHECKPOINT_END = "<!-- RECAP-CHECKPOINT:END -->"

# Fence markers graduation wraps the Bootcamper's own notes in (INV-258).
#
# ⛔ THE FENCE IS THE DISCRIMINATOR, NOT THE HEADING TEXT. Every `## ` heading in a recap
# is parsed as a module (`parse_recap`), so a notes section recognized by its *title*
# would be one renamed module away from being mis-parsed — and a Bootcamper's private
# note is then one heading away from being cited on their Certificate of Completion.
# The block is lifted out of the source before module parsing begins, so no `## ` inside
# it can ever reach `Recap.modules`.
BOOTCAMP_NOTES_START = "<!-- BOOTCAMP-NOTES:START -->"
BOOTCAMP_NOTES_END = "<!-- BOOTCAMP-NOTES:END -->"

#: Default heading for the notes section when the folded block carries none.
BOOTCAMP_NOTES_TITLE = "Notes, Ideas and Questions"

# Recap image references: `![alt](path)` on a line of its own.
# An embedded screenshot: ``![alt](path)`` alone on its line.
#
# The list marker is optional because `module-completion.md` tells the guide to add
# screenshots *to* **Actions Taken**, which is a bulleted list — so following that
# instruction literally yields ``- ![alt](path)``. Anchored matching then saw none of
# them, and a recap of 8 captured screenshots embedded 0 at exit 0, with `--check`
# reporting "captured 8, referenced 0" — which reads as *the guide forgot to embed
# them*, the one thing that had not happened (measured 2026-08-14). Accepting the
# marker is what makes recaps already written this way render.
IMAGE_LINE_RE = re.compile(r"^(?:[-*+]\s+)?!\[(.*?)\]\((.+?)\)$")

# A URL rather than a local file. Remote images are NEVER fetched (offline, INV-081).
IMAGE_URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")

# Where a relative recap image path is resolved from, and what happened to each
# image. Set by `main()` (via `set_image_context`) before rendering.
#
# The recap's image paths are written **relative to the recap document** — that is
# what every Markdown renderer expects, and what graduation Step 1a instructs — so
# the recap's own directory is the base, NOT the process working directory. The
# generator is normally invoked from the project root, where `Path.cwd()` made
# `visualizations/x.png` resolve to `<project>/visualizations/x.png` while the file
# sits at `<project>/docs/visualizations/x.png`; every image was silently dropped and
# the success line still reported ~99% of characters rendered, because the characters
# did render. `Path.cwd()` is kept as a second candidate so an invocation that already
# worked keeps working.
#
# Outcomes are keyed by the path as written, because the fpdf2 renderer builds the
# document twice (a measure pass for TOC page numbers, then the real one) and so
# reaches every image twice: two visits to one image must count once and report once.
_IMAGE_BASE_DIRS: List[Path] = []
_IMAGE_OUTCOMES: Dict[str, str] = {}

# Minimum share of the input's content-bearing characters that must survive into
# the parsed recap. Below this the input is treated as "not a recap" rather than
# "an imperfect recap" and no PDF is written (see the module docstring).
#
# Calibration: the shipped reference recap
# (docs/examples/bootcamp_recap.example.md) retains ~99%, because a well-formed
# recap keeps essentially everything except blank lines and `---` separators. A
# document with H2 headings but no recognized H3 sub-headings retains ~19%, since
# only the headings survive. 0.60 sits far from both, so ordinary slack (a stray
# lead line under an H2) never trips it, while real content loss always does.
MIN_CONTENT_RETENTION = 0.60


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
@dataclass
class ModuleSection:
    """One recap section: a name-based ``## <Name> — <date>`` block (legacy
    ``## Module N: ...`` headers are also parsed). ``number`` is None for
    name-based headers."""

    number: Optional[int]
    title: str
    date: str = ""
    # Ordered (heading, [lines]) sub-sections under ### headings.
    subsections: List[Tuple[str, List[str]]] = field(default_factory=list)

    def subsection(self, name: str) -> Optional[List[str]]:
        target = _normalize_heading(name)
        for heading, lines in self.subsections:
            if _normalize_heading(heading) == target:
                return lines
        return None

    def missing_required(self) -> List[str]:
        present = {_normalize_heading(h) for h, _ in self.subsections}
        missing = []
        for req in REQUIRED_SECTIONS:
            if _normalize_heading(req) not in present:
                missing.append(req)
        return missing

    def missing_summary_blocks(self) -> List[str]:
        """Which of ``END_SUMMARY_BLOCKS`` the End-of-Module Summary does not carry.

        All three when the subsection is absent or empty — that is literally what is
        missing — and none for a legacy ``### Journal`` section, whose alias INV-103
        tolerates precisely because Journal predates the three blocks. Callers decide what
        to do about a gap: `verify_recap` reports it, the renderers show the block as
        "(not recorded)" rather than letting it vanish.
        """
        for heading, lines in self.subsections:
            if _normalize_heading(heading) != _normalize_heading(REQUIRED_SECTIONS[3]):
                continue
            if _is_legacy_journal(heading):
                return []
            present = {_summary_block_label(line) for line in lines}
            return [
                block
                for block in END_SUMMARY_BLOCKS
                if _normalize_heading(block) not in present
            ]
        return list(END_SUMMARY_BLOCKS)


@dataclass
class NoteEntry:
    """One note the Bootcamper captured during the run (INV-257).

    ``body`` is **their** words. ``elaboration`` is the bootcamp's expansion and
    ``context`` is machine-composed, so both are kept in their own fields and rendered
    under their own labels — never folded into ``body``. This is a keepsake with their
    name on the certificate; a paragraph they did not write, indistinguishable from one
    they did, is the plugin putting words in their mouth permanently.
    """

    title: str
    type: str = ""
    captured: str = ""
    module: str = ""
    body: List[str] = field(default_factory=list)
    context: str = ""
    elaboration: str = ""


@dataclass
class NotesSection:
    """The Bootcamper's notes, folded into the recap at graduation.

    Deliberately NOT a ``ModuleSection``: it is never a module, so it never reaches the
    certificate's module citation (INV-100), either renderer's cover module list, or the
    four-subsection completeness check (INV-103).
    """

    title: str = BOOTCAMP_NOTES_TITLE
    entries: List[NoteEntry] = field(default_factory=list)
    #: Source characters this section actually accounted for — the stripped length of
    #: every line the parser assigned to the title or to an entry.
    #:
    #: ⚠️ Counted at PARSE time rather than recomputed from the fields, and the difference
    #: is load-bearing. `**Captured:** <value>` is 14 characters of label the renderer
    #: draws as a stamp rather than as literal markup; summing the field values instead
    #: undercounts every note by its label overhead, so retention falls a little further
    #: with each note the Bootcamper writes. Lines the parser could NOT place stay
    #: uncounted, so a note that fails to parse still shows up as content loss — which is
    #: the whole point of the retention figure (INV-110).
    source_chars: int = 0

    def __bool__(self) -> bool:
        """Falsey when empty, so ``if recap.notes`` means "there is something to render".

        An empty notes section on a keepsake is worse than an absent one, and every
        render/TOC/pagination site below gates on exactly this.
        """
        return bool(self.entries)


@dataclass
class Recap:
    title: str
    meta: List[Tuple[str, str]]  # ("Bootcamper", "Ada"), ...
    modules: List[ModuleSection]
    # Defaulted so every existing construction site and test keeps working unchanged.
    notes: Optional[NotesSection] = None


# The suffix the durability hooks leave on a folded-but-unfinalized section, in place of
# the timestamp module-completion writes when it finalizes (INV-059). It is a status, not
# part of the module's name, so it belongs in the date slot like a timestamp does.
_STATUS_SUFFIX_RE = re.compile(r"^in\s+progress$", re.IGNORECASE)


def _split_title_date(rest: str) -> Tuple[str, str]:
    """Split ``Name — 2026-07-15T10:05:00-05:00`` into (name, date).

    Splits on an em dash or hyphen separator when the right side is either a
    date/timestamp (begins with 4 digits) **or** the ``in progress`` status marker the
    durability hooks leave on a section they folded but never finalized. Otherwise the
    whole string is the title, so a module name that legitimately contains " — " is not
    mangled.

    ⚠️ **Why ``in progress`` has to split too.** Before this, that suffix stayed glued to
    the title, and one stale title caused two distinct defects (2026-07-29 dry run):

    * the Certificate of Completion joins module titles and *fits* the joined string
      (INV-156), so the em dash rode into a width measurement and killed the entire fpdf2
      render — the keepsake silently degraded to the stdlib renderer; and
    * ``--check --expect-modules`` compares against the title, so the module read as
      absent while the very same run validated its subsections by name — ``--check``
      reported one section as both found and *"has no recap section at all"*, which sends
      graduation to backfill a section that is already there (INV-157 warns against
      exactly that).

    Recognizing the marker the plugin itself produces is narrower, and safer, than
    loosening the date test.
    """
    for sep in (" — ", " – ", " - "):
        if sep in rest:
            left, right = rest.rsplit(sep, 1)
            tail = right.strip()
            if re.match(r"^\d{4}\b", tail) or _STATUS_SUFFIX_RE.match(tail):
                return left.strip(), tail
    return rest.strip(), ""


# --- Inter-item spacing in the long bullet lists -------------------------------- #
# These three lists are the substance of the recap — what was taught, what was done,
# what was achieved per module — and they carry its longest bullets. A bullet ends with
# a `multi_cell` at line height 5.5 and no trailing gap, so the space between two
# separate items equals the space between a wrapped item's own lines, and multi-line
# items run together. A small gap between items (never after the last) fixes it.
_ITEM_GAP_MM = 2.4
_ITEM_GAP_PT = 3.0

# Bullet lists are spaced BY DEFAULT (inverted 2026-07-31 — see below). Where the gap
# falls is decided **structurally**, by indentation, not by a list of names:
#
#     - **Q:** a question          <- no gap; its answer belongs with it
#       - **R:** the answer        <- gap; the next question starts a new pair
#     - **Q:** the next question
#
# "Emit a gap when the next content-bearing bullet is TOP-LEVEL" keeps a response with
# its question *and* separates one Q/R pair from the next, with no name to keep in sync.
#
# ⚠️ This replaced an opt-in tuple of three subsection/label names, and the names were
# themselves the defect: a list added or renamed later was silently unspaced, and
# "Files produced" was excluded on the stated belief that it was "a short reference list
# of one-line paths". `bootcamp-onboarding/module-completion.md` requires every entry to
# be a path **plus** a "— what it is" gloss, so in real recaps that list runs 5-12 items
# at 110-188 characters — the very case the gap exists for, and the one list where it was
# switched off. The exclusion looked right because it was reasoned from the list's
# *title* rather than from what the template makes its items contain.
#
# These opt-outs are the escape hatch, deliberately empty: the structural rule already
# covers both cases the original opt-in list was protecting. Add a name here only when a
# list must stay tight *between* top-level items — and say why.
_UNSPACED_SUBSECTIONS: Tuple[str, ...] = ()

# Compared through _block_label, so a `**Label:**` block inside a subsection can opt out
# without silencing the whole subsection.
_UNSPACED_LABELS: Tuple[str, ...] = ()

# Labels whose value always starts on its own line, left-aligned to the page margin,
# rather than continuing inline after the bold label. "Why it matters" is a short label
# but its value can run several sentences; rendered inline, the wrapped continuation
# hangs indented under wherever the label happened to end (a few characters different
# per module), which reads as ragged and off-margin rather than as a normal paragraph.
_NEW_LINE_LABELS = ("why it matters",)

# Both former exclusions are gone, and neither needed a name in the end (2026-07-31):
# * "Questions & Responses" — the concern was real (spacing every bullet would tear each
#   answer away from its question) but it only ever applied to the *indented* `- **R:**`
#   sub-bullets. The top-level `- **Q:**` items wanted the gap all along, and the
#   structural rule gives exactly that: a response stays attached to its question, and
#   one Q/R pair is separated from the next.
# * "Files produced" — excluded as "a short reference list of paths", which
#   `module-completion.md` contradicts: it templates every entry as
#   `` - `{path}` — {what it is} `` and requires the gloss, so real recaps run 5-12
#   items at 110-188 characters. It is also the recap's index, so it was the worst list
#   to render as an undifferentiated block.


def _block_label(line: str) -> str:
    """The normalized `**Label:**` of a line, or "" when it carries none.

    Used to switch spacing **off** inside a subsection, via `_UNSPACED_LABELS`. It read
    the other way until 2026-07-31, when the default inverted: a labeled block that must
    stay tight between its top-level items is now the exception that has to be named,
    rather than every spaced list having to be.
    """
    m = re.match(r"^\s*\*\*(.+?):\*\*", line.strip())
    return _normalize_heading(m.group(1)) if m else ""


def _summary_block_label(line: str) -> str:
    """The normalized label a summary line carries, tolerant of how it was written.

    ``**Files produced:**`` is the canonical form the template shows and the normalizer
    enforces, but the recap is authored live during a bootcamp, and
    ``**Files produced**:``, ``- **Files produced:**`` and a bare ``Files produced:`` all
    carry the block just as well. A block that is present but *looks* different must never
    be reported as missing — a false "missing" sends graduation off to backfill content
    that is already there, or worse, to rewrite a finished section (INV-085).

    A label needs no colon when the line is *only* the label — `**Files produced**` above a
    bullet list, or `### Files produced` as a sub-heading. Both are ordinary Markdown and
    both carry the block. Requiring the colon reported them missing, and the renderer then
    printed "Files produced: (not recorded)" directly beneath the files that were there,
    while `--check` failed a complete recap and graduation was sent to backfill content it
    already had (INV-085). The colon-less form is matched only against the canonical labels
    exactly, so an arbitrary bold phrase still cannot pass for one.

    Deliberately separate from `_block_label`, whose narrower job is to switch list spacing
    on for a standalone label and which must therefore keep ignoring `- **Q:**` bullets.
    """
    text = re.sub(r"^\s*[-*+]\s+", "", line.strip())
    text = re.sub(r"^#{1,6}\s+", "", text)
    text = text.replace("**", "").replace("__", "").replace("*", "")
    m = re.match(r"^([A-Za-z][^:]{0,60}?)\s*:", text)
    if m:
        return _normalize_heading(m.group(1))
    bare = _normalize_heading(text)
    if bare in {_normalize_heading(block) for block in END_SUMMARY_BLOCKS}:
        return bare
    return ""


def _is_legacy_journal(heading: str) -> bool:
    """True for a ``### Journal`` heading — the pre-INV-103 name of the fourth subsection.

    It parses as an End-of-Module Summary (`_normalize_heading` aliases it), but a Journal
    was free narrative and was never required to carry the three labeled blocks, so a
    legacy recap must not be reported as incomplete or annotated as such.
    """
    return heading.strip().lower().rstrip(":") == "journal"


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[-*]\s+\S", line))


def _is_top_level_bullet(line: str) -> bool:
    """A bullet with NO leading whitespace, as opposed to any indented sub-bullet.

    ⚠️ **Deliberately a different threshold from the one used to *draw* the indent.**
    Both renderers give a bullet its extra visual indent only at `>= 4` leading spaces
    (`_render_line`'s `lead >= 4`, `_stdlib_subsection`'s `len(m.group(1)) >= 4`),
    because that is where a second visual level is wanted. Spacing asks a different
    question — "does this line belong with the one above it?" — and any indentation at
    all is the author saying yes.

    Being tolerant here is free and prevents a real regression. `module-completion.md`
    mandates four spaces for a response (`    - **R:** …`), but a recap written with two
    would, under a `>= 4` rule, have every answer torn away from its question — which is
    precisely the failure the original "never space Questions & Responses" exclusion
    existed to prevent. A genuine top-level list item never carries leading whitespace,
    so nothing is lost by treating every indented bullet as a continuation.
    """
    m = re.match(r"^(\s*)[-*]\s+\S", line)
    return bool(m) and not m.group(1)


def _next_nonblank_is_bullet(lines: List[str], index: int) -> bool:
    """True when the next content-bearing line after ``index`` is also a bullet.

    Gating on the *next* line keeps the gap strictly between items: it never trails the
    last bullet of a list, where the subsection's own spacing already applies.
    """
    for line in lines[index + 1 :]:
        if not line.strip():
            continue
        return _is_bullet(line)
    return False


def _still_in_list_item(line: str, was_in_item: bool) -> bool:
    """Whether, after this line, we are still inside a list item.

    A bullet opens one; a blank line closes it; an **indented non-bullet line is a
    soft-wrapped continuation** of the item above and keeps it open.

    ⚠️ The continuation case is why the inter-item gap is decided on this rather than on
    `_is_bullet` alone. Gating on the bullet line asks "is the *next source line* another
    item?", and for a bullet whose Markdown wraps across two source lines the answer is
    no — it is that same item's continuation — so such an item received **no gap at all**
    (found 2026-07-31; latent since the gap was introduced, and invisible because the
    shipped example recap writes every entry as one long source line and lets the
    renderer wrap it). The gap has to be emitted after an item's *last* source line.
    """
    if _is_bullet(line):
        return True
    if not line.strip():
        return False
    return was_in_item and line[:1].isspace()


def _next_nonblank_is_top_level_bullet(lines: List[str], index: int) -> bool:
    """True when the next content-bearing line is a **top-level** bullet.

    This is the whole spacing rule. Gating on the next line keeps the gap strictly
    between items (never after the last); requiring that line to be top-level keeps it
    strictly between *logical* items, so an indented response stays attached to the
    question above it while the following question is still separated from the pair.
    """
    for line in lines[index + 1 :]:
        if not line.strip():
            continue
        return _is_top_level_bullet(line)
    return False


def _is_table_row(line: str) -> bool:
    """True for a Markdown table row (``| cell | cell |``).

    Same rule as ``generate_discoveries_pdf.py`` uses, so the two generators
    classify a table identically (INV-142).
    """
    stripped = line.strip()
    return len(stripped) > 1 and stripped.startswith("|") and stripped.endswith("|")


def _table_run(lines: List[str], index: int) -> int:
    """How many consecutive lines starting at ``index`` form ONE table block.

    Consecutive pipe rows are one table, so a renderer can draw a real grid. A
    blank line ends the run, which keeps two adjacent tables separate rather than
    merging them into one grid whose middle row happens to be bold (INV-142).
    """
    end = index
    while end < len(lines) and _is_table_row(lines[end]):
        end += 1
    return end - index


def parse_table(text: str) -> Tuple[List[str], List[List[str]]]:
    """Split a Markdown table block into (header, rows).

    The ``|---|---|`` alignment row is dropped; it is presentation, not content.
    Ragged rows are padded or truncated to the header's column count so a
    malformed row cannot desynchronize the grid. An empty leading column is
    kept deliberately — a blank header over a real row-label column is common,
    and dropping the column would delete the values beneath it.

    Mirrors ``generate_discoveries_pdf.parse_table``; both are bound by INV-142,
    so they must behave the same on the same input.
    """
    rows_in = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parsed: List[List[str]] = []
    for line in rows_in:
        if re.fullmatch(r"\|[\s:|-]+\|", line):
            continue  # alignment row
        parsed.append([c.strip() for c in line.strip("|").split("|")])
    if not parsed:
        return [], []
    header, body = parsed[0], parsed[1:]
    width = len(header)
    body = [(row + [""] * width)[:width] for row in body]
    return header, body


def _normalize_heading(name: str) -> str:
    """Normalize a heading for tolerant comparison.

    ``Actions Taken`` and ``Action Taken`` compare equal; case and surrounding
    punctuation/whitespace are ignored.
    """
    n = name.strip().lower()
    n = n.rstrip(":").strip()
    n = re.sub(r"\s+", " ", n)
    if n == "action taken":
        n = "actions taken"
    if n == "journal":
        # Legacy alias: the fourth recap subsection was renamed
        # Journal → End-of-Module Summary (INV-103); older recaps still
        # render and pass --check via this alias.
        n = "end-of-module summary"
    return n


_NOTE_HEADING_RE = re.compile(r"^###\s+(.*)$")
_NOTE_LABEL_RE = re.compile(r"^\*\*(.+?):?\*\*:?\s*(.*)$")


def _parse_notes_block(inner: str) -> NotesSection:
    """Parse the inside of a BOOTCAMP-NOTES fence into a :class:`NotesSection`."""
    section = NotesSection()
    current: Optional[NoteEntry] = None

    def close() -> None:
        nonlocal current
        if current is not None:
            while current.body and not current.body[-1].strip():
                current.body.pop()
            while current.body and not current.body[0].strip():
                current.body.pop(0)
            section.entries.append(current)
        current = None

    def account(line: str) -> None:
        """Record a line as content this section carries into the PDF."""
        section.source_chars += len(line.strip())

    for raw in inner.splitlines():
        line = raw.rstrip("\n")
        h2 = re.match(r"^##\s+(.*)$", line)
        if h2 and current is None:
            title = h2.group(1).strip()
            if title:
                section.title = title
            account(line)
            continue
        h3 = _NOTE_HEADING_RE.match(line)
        if h3:
            close()
            heading = h3.group(1).strip()
            ntype, _, rest = heading.partition(":")
            if rest.strip():
                current = NoteEntry(title=rest.strip(), type=ntype.strip())
            else:
                current = NoteEntry(title=heading)
            account(line)
            continue
        if current is None:
            # Stray text between the fence and the first note. Deliberately NOT
            # accounted: it reaches no field and renders nowhere, so counting it would
            # hide exactly the content loss this figure exists to surface.
            continue
        label = _NOTE_LABEL_RE.match(line.strip())
        if label:
            key = _normalize_heading(label.group(1))
            val = label.group(2).strip()
            handled = True
            if key == "captured":
                current.captured = val
            elif key == "module":
                current.module = val
            elif key == "type":
                current.type = current.type or val
            elif key == "context":
                current.context = val
            elif key == "elaboration":
                current.elaboration = val
            else:
                handled = False
            if handled:
                account(line)
                continue
        current.body.append(line)
        account(line)

    close()
    return section


def _fence_spans(text: str, start_marker: str, end_marker: str):
    """Every WELL-FORMED ``(start, end_exclusive)`` fence span, and the strays skipped.

    ⛔ **(INV-288) A fence's span NEVER extends past the next START of its own type.** Both handlers
    used to locate their terminator with ``text.find(END, start)`` — the next END *anywhere*
    in the document — so a stray unterminated START annexed the region up to a later fence's
    terminator, and **every finalized module section in that region was discarded**.

    Measured 2026-09-01 on the shipped script, for both fences: a three-module recap parsed
    to two, with `## SDK setup` and its content gone. It was silent three ways — ``audit_recap``
    fired the *unfinalized-module* warning (true, and about something else), ``--expect-modules``
    checks presence and never absence, and ``_source_content_chars`` stripped the same region so
    the deleted module left the retention **denominator** too: 94% retention, no fatal, on a
    recap that had lost a module.

    A stray START is therefore skipped rather than paired: the caller leaves its block in
    place, the well-formed fence after it is still handled, and the module between them
    survives. Returns ``(spans, strays)`` so the caller can report the strays.
    """
    spans, strays = [], []
    pos = 0
    while True:
        start = text.find(start_marker, pos)
        if start == -1:
            break
        end = text.find(end_marker, start)
        if end == -1:
            break                      # genuinely unterminated — the caller's own policy
        nxt = text.find(start_marker, start + len(start_marker))
        if nxt != -1 and nxt < end:
            # This START's terminator belongs to a later block. Skip it; do not span both.
            strays.append(start)
            pos = nxt
            continue
        spans.append((start, end + len(end_marker)))
        pos = end + len(end_marker)
    return spans, strays


def stray_fence_markers(text: str):
    """Every stray (unterminated-but-followed-by-another) fence START in ``text``.

    Reported by :func:`audit_recap`: a stray marker means the recap is malformed in a way
    that leaves content in the document which the fence was supposed to lift — for the
    notes fence that is a Bootcamper's private note one heading away from the recap
    (INV-100), and the operator has to be told rather than have it silently rendered or
    silently deleted.
    """
    out = []
    for start_marker, end_marker in (
        (BOOTCAMP_NOTES_START, BOOTCAMP_NOTES_END),
    ) + tuple(DISCARDED_FENCES):
        _spans, strays = _fence_spans(text, start_marker, end_marker)
        out.extend((start_marker, i) for i in strays)
    return out


def _extract_notes_block(text: str) -> Tuple[str, Optional[NotesSection]]:
    """Lift the BOOTCAMP-NOTES fence out of ``text`` before any module parsing.

    Returns ``(text_without_the_block, notes_or_None)``. Removing it up front is what
    makes the fence — not the heading text — the discriminator: the ``## `` inside it
    never reaches the module loop, so no renamed module can collide with it and no note
    can be promoted to a module section.
    """
    spans, _strays = _fence_spans(text, BOOTCAMP_NOTES_START, BOOTCAMP_NOTES_END)
    if spans:
        # The first WELL-FORMED block. A stray START before it is left where it is — its
        # region is not annexed, so no finalized module between the two is deleted. The
        # stray is reported by `stray_fence_markers` rather than silently swallowed.
        start, end = spans[0]
        inner = text[start + len(BOOTCAMP_NOTES_START): end - len(BOOTCAMP_NOTES_END)]
        remainder = text[:start] + text[end:]
        notes = _parse_notes_block(inner)
        return remainder, (notes if notes.entries else None)

    start = text.find(BOOTCAMP_NOTES_START)
    if start == -1:
        return text, None
    # ⛔ An unterminated fence — a write truncated mid-fold — runs to end of text.
    # Graduation appends this block AFTER the last module section, so everything past
    # the opening marker is notes; treating the marker as absent instead would let
    # the notes heading be parsed as a module and put a Bootcamper's private note on
    # their Certificate of Completion (INV-100). Losing the fence must cost the
    # notes' formatting at worst, never the modules and never the certificate.
    # ⚠️ This is reached only when there is NO well-formed block anywhere — the
    # genuinely-truncated case the policy was written for. Where a later well-formed
    # fence exists, the branch above handles it and this end-of-text sweep is not used,
    # because sweeping would delete every module after the stray marker.
    inner = text[start + len(BOOTCAMP_NOTES_START):]
    notes = _parse_notes_block(inner)
    return text[:start], (notes if notes.entries else None)


#: Fenced blocks lifted out of the recap before module parsing and then DISCARDED.
#:
#: ⛔ The notes fence is not here because its content is KEPT — `_extract_notes_block`
#: parses it into a `NotesSection`. Everything in this tuple is transient working state
#: that must not reach `Recap.modules`, and the parse path iterates the tuple rather than
#: naming markers one at a time: adding a fence here is what brings it under the lift
#: (INV-246), so a third fenced block cannot repeat this defect by being overlooked.
#:
#: ⚠️ The checkpoint fence had the same exposure as the notes fence and none of the
#: protection. `recap_checkpoint.md`'s own interior uses `## ` headings (`## Where we are`,
#: `## Still to do`, …), the durability hooks fold it verbatim, and every `## ` in a recap
#: is parsed as a module — so a resumed session put five phantom "modules" beside the real
#: ones in the keepsake PDF. `audit_recap` warned, but the warning is non-fatal and the
#: block was never lifted, so the PDF rendered anyway (2026-08-26, plugin 0.5.2).
DISCARDED_FENCES: Tuple[Tuple[str, str], ...] = (
    (RECAP_CHECKPOINT_START, RECAP_CHECKPOINT_END),
)


def _strip_discarded_fences(text: str) -> str:
    """Lift every :data:`DISCARDED_FENCES` block out of ``text`` before module parsing.

    ⛔ An UNTERMINATED fence is left in place here, which is the opposite of what
    `_extract_notes_block` does — and the asymmetry is deliberate. Graduation appends the
    notes block *after* the last module, so running an unterminated notes fence to
    end-of-text costs at most the notes' formatting. The checkpoint is folded **mid-recap**,
    so truncating to end-of-text would delete the Bootcamper's real finalized modules. A
    phantom section that `audit_recap` already warns about is the lesser loss; deleting
    module content to avoid it is not a trade this may make.
    """
    for start_marker, end_marker in DISCARDED_FENCES:
        spans, _strays = _fence_spans(text, start_marker, end_marker)
        # Right to left, so an earlier span's indices stay valid after a later removal.
        for start, end in reversed(spans):
            text = text[:start] + text[end:]
    return text


#: A module section heading, used only to decide whether a lift would empty the recap.
_MODULE_HEADING_RE = re.compile(r"(?m)^##\s+\S")


def parse_recap(text: str) -> Recap:
    text, notes = _extract_notes_block(text)

    # ⛔ THE LIFT MUST NEVER EMPTY THE RECAP. A checkpoint fence contains only the
    # in-progress narrative — `recap_checkpoint.py`'s `_strip_block` says so outright:
    # "Completed `## {module}` sections carry no markers and are never touched." But a
    # malformed or mis-placed fence CAN enclose finalized sections, and discarding those
    # would delete the Bootcamper's real module content to avoid phantom headings — a
    # trade this must not make. Where stripping would remove every module heading from a
    # recap that had one, keep the unstripped text: the phantom sections then render and
    # `audit_recap` warns about the surviving block, which is the pre-existing behavior
    # and the lesser loss.
    stripped = _strip_discarded_fences(text)
    if _MODULE_HEADING_RE.search(stripped) or not _MODULE_HEADING_RE.search(text):
        text = stripped

    lines = text.splitlines()

    title = "Senzing Bootcamp Recap"
    meta: List[Tuple[str, str]] = []
    modules: List[ModuleSection] = []

    current_module: Optional[ModuleSection] = None
    current_sub: Optional[Tuple[str, List[str]]] = None
    seen_first_module = False

    generic_h2_re = re.compile(r"^##\s+(.*)$")
    _legacy_module_re = re.compile(r"^Module\s+(\d+)\s*[:\-—]?\s*(.*)$", re.IGNORECASE)
    h1_re = re.compile(r"^#\s+(.*)$")
    h3_re = re.compile(r"^###\s+(.*)$")
    meta_re = re.compile(r"^\*\*(.+?)\*\*:?\s*(.*)$")

    def close_sub() -> None:
        nonlocal current_sub
        if current_module is not None and current_sub is not None:
            current_module.subsections.append(current_sub)
        current_sub = None

    def close_module() -> None:
        nonlocal current_module
        close_sub()
        if current_module is not None:
            modules.append(current_module)
        current_module = None

    for raw in lines:
        line = raw.rstrip("\n")

        # An H2 heading starts a new recap section (one per module). Name-based
        # headers ("## Business problem — <date>") are the current form; legacy
        # numbered headers ("## Module 3: System Verification — <date>") are still
        # parsed for older recaps. ``number`` is None for name-based headers.
        h2 = generic_h2_re.match(line)
        if h2:
            close_module()
            header = h2.group(1).strip()
            legacy = _legacy_module_re.match(header)
            if legacy:
                num = int(legacy.group(1))
                rest = legacy.group(2).strip().lstrip(":-— ").strip()
                mtitle, date = _split_title_date(rest)
                current_module = ModuleSection(
                    number=num, title=mtitle or f"Module {num}", date=date
                )
            else:
                mtitle, date = _split_title_date(header)
                current_module = ModuleSection(number=None, title=mtitle, date=date)
            seen_first_module = True
            continue

        if current_module is not None:
            hm = h3_re.match(line)
            if hm:
                close_sub()
                current_sub = (hm.group(1).strip(), [])
                continue
            if line.strip() == "---":
                # Separator between modules; keep it out of content.
                continue
            if current_sub is not None:
                current_sub[1].append(line)
            continue

        # Preamble (before the first module section).
        if not seen_first_module:
            hm = h1_re.match(line)
            if hm:
                title = hm.group(1).strip()
                continue
            mm = meta_re.match(line)
            if mm:
                key = mm.group(1).strip().rstrip(":")
                val = mm.group(2).strip()
                if val:
                    meta.append((key, val))
                continue

    close_module()

    # Trim trailing blank lines inside each sub-section.
    for mod in modules:
        for _, content in mod.subsections:
            while content and not content[-1].strip():
                content.pop()
            while content and not content[0].strip():
                content.pop(0)

    return Recap(title=title, meta=meta, modules=modules, notes=notes)


# --------------------------------------------------------------------------- #
# Verification (--check and post-render round trip)
# --------------------------------------------------------------------------- #
def verify_recap(recap: Recap, expected_titles: Optional[List[str]] = None) -> List[str]:
    """Return a list of human-readable problems; empty means complete.

    When ``expected_titles`` is given (e.g. the module names from
    ``config/bootcamp_progress.json`` → ``modules_completed``), also flag any
    expected module that has no ``## `` section at all — not just missing
    subsections within the sections that happen to be present.
    """
    problems: List[str] = []
    if not recap.modules:
        problems.append("recap contains no module ('## …') sections")
    for mod in recap.modules:
        missing = mod.missing_required()
        label = f"Module {mod.number}" if mod.number else mod.title
        if missing:
            problems.append(f"{label} is missing: {', '.join(missing)}")
        # The blocks INV-103 requires *inside* the summary. Reported only when the
        # subsection itself is present — otherwise the line above already names the whole
        # gap, and saying it twice reads as two separate defects.
        if REQUIRED_SECTIONS[3] not in missing:
            gaps = mod.missing_summary_blocks()
            if gaps:
                problems.append(
                    f"{label}'s {REQUIRED_SECTIONS[3]} is missing its labeled "
                    f"block(s): {', '.join(gaps)}"
                )

    # A module appearing twice renders twice in the keepsake PDF. The usual cause
    # is a missed module-completion step 2d: the finalized '## {Name}' section was
    # appended while the durability hooks' folded checkpoint block — which carries
    # its own copy of that section — was left in place. INV-085 gives each
    # completed module *its own* section, singular.
    seen: set = set()
    reported: set = set()
    for mod in recap.modules:
        key = (mod.title or "").strip().lower()
        if not key:
            continue
        if key in seen and key not in reported:
            reported.add(key)
            problems.append(
                f"module '{mod.title}' has more than one recap section — it will "
                "render twice; keep the finalized section and remove the leftover "
                "RECAP-CHECKPOINT block (module-completion step 2d)"
            )
        seen.add(key)

    if expected_titles:
        present = {(m.title or "").strip().lower() for m in recap.modules}
        for title in expected_titles:
            norm = title.strip().lower()
            if norm and norm not in present:
                problems.append(f"expected module '{title}' has no recap section at all")
    return problems


def _source_content_chars(text: str) -> int:
    """Count content-bearing characters in the source Markdown.

    Blank lines and the ``---`` separators between module sections are excluded:
    the renderers legitimately drop them, so counting them would understate
    retention for a perfectly good recap.
    """
    # ⛔ A DISCARDED_FENCES block is lifted before module parsing, so its characters
    # CANNOT reach the PDF by design. Counting them in the denominator would measure the
    # lift's own effect as content loss — and on a resumed session, whose checkpoint is
    # large relative to a partly-written recap, that is enough to trip the
    # catastrophic-content-loss gate and block the PDF outright (INV-048 requires the
    # recap PDF to always be produced). Measured on a fixture: 42% retention, fatal,
    # where the block was the only thing "missing".
    text = _strip_discarded_fences(text)

    total = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "---":
            continue
        # Fence markers are structure, not content: the renderers drop them exactly as
        # they drop `---`, so counting them would understate retention on a recap whose
        # only difference is that the Bootcamper wrote something down. The checkpoint
        # markers are here for the UNTERMINATED case, where the block itself survives
        # the lift (see `_strip_discarded_fences`).
        if line in (BOOTCAMP_NOTES_START, BOOTCAMP_NOTES_END,
                    RECAP_CHECKPOINT_START, RECAP_CHECKPOINT_END):
            continue
        total += len(line)
    return total


def _rendered_content_chars(recap: Recap) -> int:
    """Count the characters a parsed recap actually carries into the PDF.

    Mirrors what both renderers draw: the title, the preamble meta pairs, and per
    module its title/date plus each sub-section's heading and body lines.
    """
    total = len(recap.title)
    for key, val in recap.meta:
        total += len(key) + len(val)
    for mod in recap.modules:
        total += len(mod.title) + len(mod.date)
        for heading, lines in mod.subsections:
            total += len(heading)
            total += sum(len(line.strip()) for line in lines if line.strip())
    # ⚠️ The notes section MUST be counted (INV-258). Omitting it makes the retention
    # figure fall with every note the Bootcamper writes — their own words counted
    # against them as content the PDF "lost" — and a long enough notes file crosses
    # MIN_CONTENT_RETENTION and makes the generator REFUSE to render their recap
    # (INV-110). The keepsake would be destroyed by the feature meant to enrich it.
    if recap.notes:
        total += recap.notes.source_chars
    return total


def set_image_context(recap_path: Path) -> None:
    """Set where relative recap image paths resolve from, and reset the tally.

    The recap document's own directory comes first: its `![alt](path)` targets are
    written relative to it (graduation Step 1a), so that is the only base under which
    the Markdown and the PDF agree. `Path.cwd()` follows as a fallback so an
    invocation that already resolved its images keeps working.
    """
    global _IMAGE_BASE_DIRS
    base_dirs = [recap_path.resolve().parent]
    cwd = Path.cwd().resolve()
    if cwd not in base_dirs:
        base_dirs.append(cwd)
    _IMAGE_BASE_DIRS = base_dirs
    _IMAGE_OUTCOMES.clear()


def resolve_recap_image(
    path: str, base_dirs: Optional[Sequence[Path]] = None
) -> Optional[Path]:
    """The first existing file a recap image reference resolves to, or ``None``.

    An absolute path is used as given. A relative one is tried under each base dir
    in order — the recap's directory, then the working directory.
    """
    if IMAGE_URL_RE.match(path):
        return None
    p = Path(path)
    if p.is_absolute():
        return p if p.is_file() else None
    for base in (base_dirs if base_dirs is not None else _IMAGE_BASE_DIRS) or [Path.cwd()]:
        candidate = base / p
        if candidate.is_file():
            return candidate
    return None


def recap_image_targets(source_text: str) -> List[str]:
    """Every ``![alt](path)`` target in the recap source, in document order.

    Read from the source rather than from render callbacks so the count of images
    the recap *references* is known even when the renderer embeds none — the stdlib
    fallback renders no images at all, and "embedded 0 of 0" would misreport a recap
    that references six.
    """
    targets: List[str] = []
    for line in source_text.splitlines():
        match = IMAGE_LINE_RE.match(line.strip())
        if match:
            targets.append(match.group(2).strip())
    return targets


def unresolvable_image_targets(
    source_text: str, base_dirs: Optional[Sequence[Path]] = None
) -> List[str]:
    """Recap image references that resolve to no file (remote URLs excluded).

    Used by ``--check`` so a lost screenshot is reported at the step that can still
    fix it, rather than discovered by counting image objects in the finished PDF.
    """
    missing: List[str] = []
    for target in recap_image_targets(source_text):
        if IMAGE_URL_RE.match(target):
            continue
        if resolve_recap_image(target, base_dirs) is None and target not in missing:
            missing.append(target)
    return missing


def _record_image_outcome(path: str, outcome: str) -> None:
    """Record what happened to one image, once, and report anything but success.

    Keyed by the path as written: the fpdf2 renderer builds the document twice, so
    each image is reached twice and must be counted and reported once.
    """
    if path in _IMAGE_OUTCOMES:
        return
    _IMAGE_OUTCOMES[path] = outcome
    if outcome == "embedded":
        return
    if outcome == "remote":
        sys.stderr.write(
            f"skipped image (remote URL, never fetched): {path}\n"
        )
        return
    if outcome == "missing":
        tried = ", ".join(str(base) for base in _IMAGE_BASE_DIRS) or str(Path.cwd())
        sys.stderr.write(
            f"skipped image (not found): {path} — looked in: {tried}\n"
        )
        return
    sys.stderr.write(f"skipped image ({outcome}): {path}\n")


def image_embed_note(referenced: int) -> str:
    """``embedded N of M images`` for the success line.

    The character-retention figure cannot see a dropped image — the characters do
    render — so a recap that lost every screenshot still reported ~99%. This is the
    figure that makes the loss visible (INV-110).

    ⛔ **This measures embedding, not coverage.** ``referenced`` counts the ``![](…)``
    links in the recap being rendered, so the denominator comes from the same file as
    the numerator: a recap that only ever referenced four of six captured tabs reads
    ``embedded 4 of 4 images``. Use ``tab_coverage_note`` for the coverage question —
    it takes its denominator from capture's sidecar manifest, which is external.
    """
    embedded = sum(1 for outcome in _IMAGE_OUTCOMES.values() if outcome == "embedded")
    return f"embedded {embedded} of {referenced} images"


# --- Tab coverage, measured against an external denominator ------------------
#
# `capture_screenshots.py` writes `<name>-tabs.json` beside the PNGs recording how many
# tabs it actually captured. That is the only number in the system that does not come
# from the recap Markdown, so it is the only one that can detect a tab which was
# captured and then never referenced.

TAB_MANIFEST_GLOBS = ("*-tabs.json", "*/*-tabs.json")


def find_tab_manifests(base_dirs: Optional[Sequence[Path]] = None) -> List[dict]:
    """Load every capture manifest reachable from the recap's image bases.

    Globs one level down as well as at the top, because the recap lives in ``docs/``
    while its PNGs (and their manifests) live in ``docs/visualizations/``. The
    subdirectory is found by shape rather than by name, so a project that keeps them
    elsewhere still works.

    A manifest that cannot be read or parsed is skipped and reported — never fatal,
    and never silently treated as "no tabs expected", which would turn a corrupt file
    into a clean bill of health.
    """
    manifests: List[dict] = []
    seen: set = set()
    for base in (base_dirs if base_dirs is not None else _IMAGE_BASE_DIRS) or [Path.cwd()]:
        for pattern in TAB_MANIFEST_GLOBS:
            try:
                candidates = sorted(Path(base).glob(pattern))
            except OSError:
                continue
            for path in candidates:
                key = path.resolve()
                if key in seen:
                    continue
                seen.add(key)
                try:
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                except (OSError, ValueError) as exc:
                    sys.stderr.write(
                        f"unreadable tab manifest {path} ({exc}); tab coverage cannot "
                        "be checked from it\n"
                    )
                    continue
                if isinstance(data, dict) and isinstance(data.get("captured"), list):
                    data["_path"] = str(path)
                    manifests.append(data)
    return manifests


# --- The expected-visualization denominator (INV-271) -----------------------
#
# `tab_coverage_problems` answers "did every captured tab reach the recap?" for each
# manifest it is given, and `find_tab_manifests` supplies the manifests that exist. So
# its denominator is *the set of captures that happened*: a module that captured nothing
# contributes no manifest, no denominator, and no shortfall anything can see.
#
# ⛔ That is INV-193's own failure shape, one level out. INV-193 moved the completeness
# denominator off the artifact being measured and onto the manifest; the manifest is
# external to the recap, but the SET of manifests is still derived from whatever capture
# happened to produce. On 2026-08-25 the check reported "6 of 6 captured tabs reached the
# recap" -- a clean pass -- while the whole Module 7 application, built over the
# Bootcamper's own resolved data, had been captured not at all. The keepsake illustrated
# the bootcamp with pictures of the sample dataset.
#
# The fix is a denominator that does not come from the manifests: the modules that ran.
# `config/bootcamp_progress.json` records `modules_completed`, and each visualizing module
# is specified to build one named visualization. Below is that mapping; a module absent
# from it produces no visualization and contributes nothing to expect.

# ⛔ The KEYS are module name tokens owned elsewhere: the registry is
# `skills/bootcamp-preparation/SKILL.md`'s module table, and
# `skills/bootcamp-onboarding/module-completion.md` is what writes a module's token into
# `modules_completed` at its close. This map is therefore a COPY, and a copy that goes stale
# fails silently -- `read_completed_modules()` degrades in the under-reporting direction, so a
# key no module writes any more produces no error, just a tab-coverage figure that reads clean
# with a whole visualization missing. `tests/test_expected_visualization_denominator.py` pins it
# from both ends: `TheMappingKeysMatchTheTokenRegistry` against the registry table, and
# `test_the_mapping_covers_both_visualizing_modules` against the map's own content (a valid key
# mapped to the wrong visualization name is invisible to the first).
MODULE_VISUALIZATIONS = {
    # module name token in `modules_completed` -> the `{name}` its capture step uses
    "truthset_visualization": "truthset_verification",
    "query_visualize_discover": "results_visualization",
}

DEFAULT_PROGRESS = Path("config") / "bootcamp_progress.json"


def read_completed_modules(path=DEFAULT_PROGRESS) -> List[str]:
    """The ``modules_completed`` list from the progress JSON, or [] if unreadable.

    Any read or parse problem yields [] rather than raising: a missing progress file
    must degrade to "nothing expected" and leave the pre-existing per-manifest checks
    exactly as they were, never break the render (INV-048). Returning [] is safe in the
    honest direction -- it can only under-report, and the caller says so when it does.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    completed = data.get("modules_completed")
    if not isinstance(completed, list):
        return []
    return [item for item in completed if isinstance(item, str)]


def expected_visualizations(completed: Sequence[str]) -> List[str]:
    """The visualization names the modules that ran were specified to build."""
    names = []
    for module in completed:
        name = MODULE_VISUALIZATIONS.get(module)
        if name and name not in names:
            names.append(name)
    return sorted(names)


def manifest_names(manifests: Sequence[dict]) -> set:
    """Every visualization a manifest accounts for.

    Prefers the manifest's own ``name`` field and falls back to the filename stem, so a
    manifest written by an older capture that predates that field still counts.
    """
    names = set()
    for manifest in manifests:
        name = manifest.get("name")
        if isinstance(name, str) and name:
            names.add(name)
            continue
        path = manifest.get("_path")
        if isinstance(path, str) and path:
            stem = Path(path).name
            if stem.endswith("-tabs.json"):
                names.add(stem[: -len("-tabs.json")])
    return names


def missing_visualization_reports(
    expected: Sequence[str], manifests: Sequence[dict]
) -> List[str]:
    """One report per expected visualization that has no manifest.

    Phrased as an UNRUN check, not a failure: nothing here is evidence the tabs were
    never captured, only that coverage for them cannot be measured. Graduation is
    non-blocking (INV-048), so the requirement is that the shortfall is stated -- by
    name, with the module that owed it, and with the remedy -- never that graduation
    refuses (INV-163, INV-193, INV-265).
    """
    present = manifest_names(manifests)
    owed = {name: module for module, name in MODULE_VISUALIZATIONS.items()}
    reports = []
    for name in expected:
        if name in present:
            continue
        module = owed.get(name, "an unrecorded module")
        reports.append(
            f"tab-coverage check for '{name}' — the '{module}' module ran (it is in "
            f"modules_completed) and is specified to build this visualization, but no "
            f"{name}-tabs.json was found beside the recap's images. Coverage for it has "
            f"NOT been measured — this is not a pass, and the per-manifest figure below "
            f"cannot see it because its denominator is the manifests that exist. "
            f"Remedy while the artifacts are still on disk: re-start the app and re-run "
            f"capture_screenshots.py --url http://localhost:<port> --name {name}, then "
            f"re-embed (the backfill path), rather than shipping a recap that pictures "
            f"the sample dataset in place of the Bootcamper's own results."
        )
    return reports


def tab_coverage_problems(source_text: str, manifests: Sequence[dict]) -> List[str]:
    """Captured tabs that never reached the recap, named by slug.

    This is the check `embedded N of M images` structurally cannot perform: it compares
    what capture recorded against what the recap references.
    """
    referenced = {Path(target).name for target in recap_image_targets(source_text)}
    problems: List[str] = []
    for manifest in manifests:
        missing = [
            entry
            for entry in manifest["captured"]
            if isinstance(entry, dict) and entry.get("file") not in referenced
        ]
        if not missing:
            continue
        slugs = ", ".join(
            str(entry.get("slug") or entry.get("tab") or entry.get("file"))
            for entry in missing
        )
        name = manifest.get("name") or Path(str(manifest.get("_path", ""))).name
        problems.append(
            f"visualization {name!r}: {len(missing)} captured tab(s) are missing from "
            f"the recap — {slugs} (captured {len(manifest['captured'])}, referenced "
            f"{len(manifest['captured']) - len(missing)}; source: "
            f"{manifest.get('_path', 'tab manifest')})"
        )
    return problems


def manifest_undercount_problems(manifests: Sequence[dict]) -> List[str]:
    """Manifests describing fewer captures than there are PNGs beside them.

    ⛔ **This is the denominator the manifest cannot supply about itself.** The manifest is
    the only number in the system that does not come from the recap Markdown, which is
    exactly why a truncated one is undetectable from the consumer side: there is no second
    figure to check it against. The PNGs are that second figure, and they are the one
    record a truncating manifest write cannot destroy — the earlier images stay on disk.

    The reported sequence: six tabs captured, one re-captured on its own because its query
    matched nothing, and the manifest rewritten from scratch as ``captured_count: 1``.
    Coverage then passes on a 1-of-1 denominator — and would pass just as cheerfully with
    five of the six images lost. `write_manifest` now merges rather than replaces, but this
    check is what notices when that merge is bypassed, skipped, or undone by a later edit;
    it also catches any other cause of an undercount, not just the re-capture path.
    """
    problems: List[str] = []
    for manifest in manifests:
        source = manifest.get("_path")
        name = manifest.get("name")
        if not source or not name:
            continue
        directory = Path(str(source)).parent
        try:
            pngs = sorted(directory.glob(f"{name}-*.png"))
        except OSError:
            continue
        if not pngs:
            continue
        captured = len([e for e in manifest.get("captured", []) if isinstance(e, dict)])
        if captured >= len(pngs):
            continue
        problems.append(
            f"visualization {name!r}: the tab manifest records {captured} captured tab(s) "
            f"but {len(pngs)} {name}-*.png file(s) sit beside it — the manifest "
            "undercounts, so the coverage check above is measuring against a denominator "
            "smaller than what was actually captured (a targeted re-capture that replaced "
            f"the manifest is the usual cause; source: {source})"
        )
    return problems


def tab_coverage_note(source_text: str, manifests: Sequence[dict]) -> str:
    """``N of M captured tabs`` — empty when no manifest exists.

    Deliberately worded so it cannot be mistaken for the Markdown-derived count that
    sits beside it in the success line.
    """
    if not manifests:
        return ""
    referenced = {Path(target).name for target in recap_image_targets(source_text)}
    captured = [
        entry
        for manifest in manifests
        for entry in manifest["captured"]
        if isinstance(entry, dict)
    ]
    if not captured:
        return ""
    present = sum(1 for entry in captured if entry.get("file") in referenced)
    return f"{present} of {len(captured)} captured tabs reached the recap"


@dataclass
class RecapAudit:
    """A parsed recap's problems, split by severity.

    ``fatal`` means the input is not a recap, or rendering it would silently drop
    most of its content — an empty deliverable would be worse than none, so no
    PDF is written. ``warnings`` means an imperfect but recognizable recap:
    render it and continue, because graduation is non-blocking.
    """

    fatal: List[str]
    warnings: List[str]
    source_chars: int
    rendered_chars: int

    @property
    def retention(self) -> float:
        if self.source_chars <= 0:
            return 0.0
        return self.rendered_chars / self.source_chars

    def retention_note(self) -> str:
        return (
            f"rendered {self.rendered_chars} of {self.source_chars} "
            f"source characters ({self.retention:.0%})"
        )


def audit_recap(
    recap: Recap,
    source_text: str,
    expected_titles: Optional[List[str]] = None,
) -> RecapAudit:
    """Classify a parsed recap's problems by severity.

    Builds on :func:`verify_recap` — which stays the ``--check`` contract and
    reports per-section completeness — and adds the two content-loss checks a
    per-section list cannot express: an input with no recap sections at all, and
    one whose sections carry no recognized sub-sections (so the parser keeps
    their headings and discards their bodies).
    """
    warnings = verify_recap(recap, expected_titles)

    # A surviving checkpoint block means a module was never finalized: the
    # durability hooks (INV-059) fence their fold in these markers, and
    # module-completion step 2d removes the block once the finalized section is
    # appended. The markers themselves are HTML comments, so the renderers drop
    # them silently — which is exactly why their presence has to be reported here
    # rather than left to be noticed in the PDF.
    if RECAP_CHECKPOINT_START in source_text or RECAP_CHECKPOINT_END in source_text:
        warnings.append(
            f"recap still contains a {RECAP_CHECKPOINT_START} … "
            f"{RECAP_CHECKPOINT_END} block — a module was folded by the "
            "durability hooks but never finalized (module-completion step 2d)"
        )

    # ⛔ A stray fence START — one whose terminator belongs to a LATER block — is reported
    # by name. It is not the same condition as the surviving-block warning above, and
    # saying so matters: the stray's region is deliberately NOT annexed (annexing it
    # deleted finalized modules), so its content stays in the document, and for the notes
    # fence that is a Bootcamper's private note one heading away from the recap (INV-100).
    # Neither silently deleting it nor silently rendering it is acceptable; naming it is.
    for marker, index in stray_fence_markers(source_text):
        warnings.append(
            "stray %s at offset %d — its closing marker belongs to a later block, so the "
            "region was left in place rather than removed (removing it would delete any "
            "finalized module section between the two). Repair the recap's fences."
            % (marker, index)
        )

    source_chars = _source_content_chars(source_text)
    rendered_chars = _rendered_content_chars(recap)
    retention = (rendered_chars / source_chars) if source_chars > 0 else 0.0

    fatal: List[str] = []
    if not recap.modules:
        fatal.append(
            "input does not look like a bootcamp recap: no "
            "'## <Module name>' sections found"
        )
    else:
        bodyless = sum(1 for mod in recap.modules if not mod.subsections)
        if bodyless == len(recap.modules):
            fatal.append(
                f"input does not look like a bootcamp recap: 0 of "
                f"{len(recap.modules)} '##' sections carry any recognized "
                f"sub-section (expected one or more of: "
                f"{', '.join(REQUIRED_SECTIONS)})"
            )

    if source_chars > 0 and retention < MIN_CONTENT_RETENTION:
        fatal.append(
            f"catastrophic content loss: only {retention:.0%} of the input's "
            f"content would reach the PDF (minimum "
            f"{MIN_CONTENT_RETENTION:.0%}) — body text is kept only under a "
            f"module section's '### ' sub-headings"
        )

    return RecapAudit(
        fatal=fatal,
        warnings=warnings,
        source_chars=source_chars,
        rendered_chars=rendered_chars,
    )


# --------------------------------------------------------------------------- #
# Rich renderer (fpdf2)
# --------------------------------------------------------------------------- #
# Senzing "Obsidian & Ember" brand palette, sourced from the shared brand tokens that
# ship alongside this script (`brand_tokens.py`) so the recap PDF matches the Truth-Set
# visualization. Falls back to an inlined copy of the same values if that module is
# unavailable, so a valid PDF is still always produced (INV-048/INV-066).
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Fallback palette (RGB), used only if brand_tokens is unavailable. Named at module
# scope so tests/test_brand_sync.py can assert it stays equal to the brand_tokens
# values — the two copies would otherwise drift silently (INV-048/INV-066).
_FALLBACK_RGB = {
    "NAVY": (24, 22, 15), "BLUE": (245, 120, 38), "SLATE": (74, 70, 64),
    "LIGHT": (250, 248, 243), "ACCENT": (255, 78, 31), "INK": (24, 22, 15),
    "GREEN": (29, 158, 117), "LINE": (229, 223, 211), "AMBER": (240, 146, 10),
}


def _use_fallback_palette():
    """The nine fallback colors in assignment order, in ONE place (INV-184).

    Both `except` branches below need them, and nine assignment lines written out per
    branch is the drift surface — a tenth token added to one branch and not the other
    is exactly the silent divergence `_FALLBACK_RGB` was named at module scope to
    prevent. Mirrors `generate_discoveries_pdf.py`'s helper of the same name.
    """
    return (
        _FALLBACK_RGB["NAVY"],
        _FALLBACK_RGB["BLUE"],
        _FALLBACK_RGB["SLATE"],
        _FALLBACK_RGB["LIGHT"],
        _FALLBACK_RGB["ACCENT"],
        _FALLBACK_RGB["INK"],
        _FALLBACK_RGB["GREEN"],
        _FALLBACK_RGB["LINE"],
        _FALLBACK_RGB["AMBER"],
    )


try:
    import brand_tokens as _bt

    _h2rgb = _bt.hex_to_rgb
    NAVY = _h2rgb(_bt.DEEP)          # dark cover band / summary accent
    BLUE = _h2rgb(_bt.EMBER_CORE)    # primary accent
    SLATE = _h2rgb(_bt.BODY_INK)     # body text
    LIGHT = _h2rgb(_bt.WARM_OFF_WHITE)  # warm off-white fills
    ACCENT = _h2rgb(_bt.EMBER_HOT)   # hot ember accent / rules
    INK = _h2rgb(_bt.DARK_INK)       # headline ink
    GREEN = _h2rgb(_bt.SIGNAL_GREEN)  # resolved/done sections only
    LINE = _h2rgb(_bt.WARM_LINE)     # warm divider/rule (never cold gray)
    AMBER = _h2rgb(_bt.EMBER_GRAD_END)  # warm end of the brand's ember gradient
except ModuleNotFoundError:  # defensive fallback — kept in sync via tests/test_brand_sync.py
    # INV-111: a degraded path is never inferred from silence. The two branches stay
    # distinct because they are different failures — say which occurred, since a
    # project-local copy of this script without brand_tokens.py beside it is easy to
    # create by accident, and "present but unusable" points somewhere else entirely.
    # The recap PDF is the Bootcamper's keepsake; it renders either way (INV-048), but
    # a keepsake printed in the fallback palette must not be indistinguishable from one
    # printed in the brand's.
    sys.stderr.write(
        f"brand_tokens.py not importable from {Path(__file__).resolve().parent} "
        "(copy it next to this script); using the inlined brand palette.\n"
    )
    NAVY, BLUE, SLATE, LIGHT, ACCENT, INK, GREEN, LINE, AMBER = _use_fallback_palette()
except Exception as exc:  # present but unusable
    sys.stderr.write(
        f"brand_tokens.py present but unusable ({exc}); using the inlined brand palette.\n"
    )
    NAVY, BLUE, SLATE, LIGHT, ACCENT, INK, GREEN, LINE, AMBER = _use_fallback_palette()

# Header-row fill for rendered tables. Derived from the warm line color so the
# header reads as a band rather than a second body row, and so it cannot drift
# from the brand palette (INV-081/INV-107) — it is not a new token.
TABLE_HEAD_FILL = tuple(min(255, c + 12) for c in LINE)

# Muted warm gray for the certificate's small-caps labels, where body ink reads too
# loud and a cold gray fights the ember band. Derived by blending body ink toward the
# warm off-white — the same "derive, never invent" rule TABLE_HEAD_FILL follows
# (INV-081): it is not a new brand token.
MUTED = tuple(round(s + (l - s) * 0.48) for s, l in zip(SLATE, LIGHT))

# Per-section accent colors for the module page tabs/headings.
_SECTION_ACCENT = {
    "information shared": BLUE,
    "questions & responses": ACCENT,
    "actions taken": GREEN,
    "end-of-module summary": NAVY,
}

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _section_accent(name: str) -> Tuple[int, int, int]:
    """Return the accent color for a module sub-section (default navy)."""
    return _SECTION_ACCENT.get(_normalize_heading(name), NAVY)


def _format_date(date: str) -> str:
    """Format an ISO ``YYYY-MM-DD`` date as ``Month D, YYYY``; pass others through."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", date.strip())
    if not m:
        return date
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= month <= 12:
        return date
    return f"{_MONTHS[month - 1]} {day}, {year}"


def _md_inline_to_text(s: str) -> str:
    """Strip the small subset of inline Markdown we emit, for plain text."""
    # Reduce an embedded image ![alt](path) to its alt text — used as a caption
    # by renderers that cannot embed the image (e.g. the stdlib fallback).
    s = re.sub(r"!\[(.*?)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s


# fpdf2's core fonts (Helvetica) only cover Latin-1 (ISO-8859-1). Map the
# common typographic characters the recap may contain to ASCII, then drop any
# remaining out-of-range character, so the rich renderer never raises.
_UNICODE_MAP = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "•": "-",
    "…": "...",
    "→": "->",
    "↔": "<->",
    "←": "<-",
    "⇒": "=>",
    "↑": "^",
    "↓": "v",
    "⚠": "!",
    "\ufe0f": "",  # variation selector-16, trails emoji like the warning sign
    # Comparison, currency and spacing characters a bootcamper's own
    # discoveries document carries but the plugin's templates never emit — so
    # scanning the templates could not find them. Each rendered as "?" until mapped.
    "≈": "~",
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
    "∞": "infinity",
    "€": "EUR",
    "™": "(TM)",
    "‑": "-",  # non-breaking hyphen
    "​": "",  # zero-width space
    "✅": "[done]",
    "✓": "[x]",
    "⛔": "",
    "\U0001f6d1": "",
    "\U0001f393": "",
    "\U0001f680": "",
    "\U0001f4c4": "",
    "\U0001f3c6": "",
}


# Latin letters with no NFKD decomposition — a stroke or bar is part of the glyph, not a
# combining mark — so folding by decomposition alone deletes them. Dropping the first
# letter of "Łukasz" is not a lesser rendering, it is a different name.
_LATIN_FOLD = {
    "Ł": "L", "ł": "l", "Đ": "D", "đ": "d", "Ħ": "H", "ħ": "h", "Ŧ": "T", "ŧ": "t",
    "Ŋ": "N", "ŋ": "n", "Œ": "OE", "œ": "oe", "Ə": "E", "ə": "e", "ı": "i", "ſ": "s",
    "Ɨ": "I", "ɨ": "i", "Ƶ": "Z", "ƶ": "z", "Ǥ": "G", "ǥ": "g", "Ɖ": "D", "ɗ": "d",
}


# Characters `_fold_to_latin1` could not represent at all, mapped to an excerpt of the
# first passage each was found in. INV-143 permits dropping them; what it does not permit
# is doing so silently, and until this collector existed the warn half of that contract
# was implemented for the certificate name only. A Cyrillic organization name in a
# discoveries document rendered as `"- "` at exit 0 with `content retained: 96%` — the
# retention figure cannot see it, because retention is measured over parsed *source*
# characters before `_safe` runs at render time.
#
# Keyed by character, so the record is idempotent: the fpdf2 renderer runs two passes and
# may then fall back to the stdlib writer, so counting occurrences would report two or
# three times the real loss. Distinct characters and distinct passages are stable however
# many times the same content is rendered.
_DROPPED_CHARACTERS: Dict[str, str] = {}

# Excerpt length kept short: it exists to locate the passage, not to reproduce it.
_DROP_EXCERPT_CHARS = 60

# Enough names to identify what was lost without turning one warning into a wall of text
# for a document written entirely in another script.
_DROP_NAMES_SHOWN = 8


# The one dropped character that is expected, harmless, and has no available remedy.
#
# Module 1 Step 11 writes `> \U0001f916 Bootcamp-generated business case` under the title of
# `docs/business_problem.md` on every run that accepts the Business Case Offer -- the common
# Core path -- and graduation Step 5b renders that file as a keepsake PDF. ROBOT FACE has no
# Latin-1 core-font glyph, so it is dropped, and NEITHER branch of the warning's guidance
# applies: the marker does not name an entity, and it is not the subject of its passage. It is
# a machine-readable flag that four shipped files match on, read from the MARKDOWN and never
# from the PDF, so its loss from the page costs nothing and there is no correct action to take.
#
# A guaranteed warning with no correct response is what teaches that warnings are ignorable,
# which is the cost this suppresses.
#
# ⛔ Scoped to this exact line, deliberately (INV-266). The character is still DROPPED from the page --
# only the tally entry is skipped -- and a ROBOT FACE anywhere else in the document still
# warns, because the guard is the passage, not the character. `tests/test_recap_pdf_guard.py`
# pins both directions.
_EXPECTED_DROP_PASSAGE = "> \U0001f916 Bootcamp-generated business case"
_EXPECTED_DROP_CHAR = "\U0001f916"


def _is_expected_marker_drop(ch: str, excerpt: str) -> bool:
    """True only for ROBOT FACE in the generated-scenario marker line itself."""
    if ch != _EXPECTED_DROP_CHAR:
        return False
    return excerpt.startswith(_EXPECTED_DROP_PASSAGE)


def _record_dropped_character(ch: str, context: str) -> None:
    """Remember one character `_fold_to_latin1` had to drop, and where it was."""
    if ch in _DROPPED_CHARACTERS:
        return
    excerpt = re.sub(r"\s+", " ", context).strip()
    # Checked BEFORE truncation, against the full normalized passage: the marker is 45
    # characters and _DROP_EXCERPT_CHARS is 60, so truncation would not currently reach it,
    # but a shorter excerpt cap later must not silently widen what this exempts.
    if _is_expected_marker_drop(ch, excerpt):
        return
    if len(excerpt) > _DROP_EXCERPT_CHARS:
        excerpt = excerpt[:_DROP_EXCERPT_CHARS].rstrip() + "..."
    _DROPPED_CHARACTERS[ch] = excerpt


def reset_dropped_characters() -> None:
    """Clear the collector. For tests and for callers that render more than one document."""
    _DROPPED_CHARACTERS.clear()


def _describe_dropped(ch: str) -> str:
    """A character's Unicode name, or its code point when it has none."""
    import unicodedata

    return unicodedata.name(ch, None) or "U+%04X" % ord(ch)


def dropped_character_warning() -> Optional[str]:
    """One aggregated ``WARNING:`` line for everything dropped this run, else ``None``.

    ⚠️ ASCII by construction. The dropped characters are reported by Unicode NAME, and the
    locating excerpt is backslash-escaped — never echoed raw. A Windows console in a legacy
    code page cannot display the very characters that were dropped (see `ground-rules.md`
    -> "Windows and PowerShell"), so printing them would corrupt the warning itself and
    reproduce the defect it exists to report.

    Non-blocking by design: the caller writes this to stderr and still ships the PDF
    (INV-048/INV-052/INV-066). Silent loss is the defect; refusing to render is not the fix.
    """
    if not _DROPPED_CHARACTERS:
        return None
    names = [_describe_dropped(ch) for ch in _DROPPED_CHARACTERS]
    shown = ", ".join(names[:_DROP_NAMES_SHOWN])
    if len(names) > _DROP_NAMES_SHOWN:
        shown += f", and {len(names) - _DROP_NAMES_SHOWN} more"
    first_char = next(iter(_DROPPED_CHARACTERS))
    where = _DROPPED_CHARACTERS[first_char].encode("ascii", "backslashreplace").decode("ascii")
    return (
        f"WARNING: {len(_DROPPED_CHARACTERS)} distinct character(s) in "
        f"{len(set(_DROPPED_CHARACTERS.values()))} passage(s) cannot be rendered by this "
        f"PDF's built-in fonts and were dropped from the page: {shown}. "
        f'First affected passage: "{where}". The PDF was still written and the content is '
        f"otherwise intact, but those characters are GONE from it: check the page before "
        f"sharing it. Which fix applies depends on what the dropped text WAS. "
        f"(a) If it NAMES an entity: use that entity's verified Latin-script name or alias "
        f"instead of its non-Latin primary name, especially inside fenced/monospace blocks -- "
        f"and never substitute a guess for a name you have not verified. "
        f"(b) If the dropped text IS the subject rather than a label -- a field value the "
        f"passage is about, with no Latin-script equivalent to substitute -- do NOT remove it: "
        f"keep it verbatim and add an ASCII description of it alongside, so the page still "
        f"carries the meaning. "
        f"Either way, use ASCII connectors (| and v) in ASCII diagrams.\n"
    )


def _fold_to_latin1(s: str) -> str:
    """Best-effort ASCII fold of characters `_UNICODE_MAP` does not cover.

    Latin-script letters carrying marks the core fonts lack — `ā ő ș ğ ẹ` — decompose under
    NFKD into a base letter plus combining marks; dropping the marks leaves a readable
    letter. `_LATIN_FOLD` covers the ones that do not decompose.

    Characters from a non-Latin script (CJK, Cyrillic, Arabic, Hebrew, Greek, Devanagari,
    Thai) are **dropped**, which INV-143 permits, never encoded as `?`, which it forbids.
    They are deliberately not transliterated: a transliteration table would serve one
    script and still drop the rest, and how a name should be spelled in Latin script is
    the Bootcamper's call, not a lookup table's — Владимир is Vladimir, Wladimir or
    Volodymyr depending on whose name it is. So the generator drops, warns, and INV-113's
    pinned question asks the one person who knows.
    """
    import unicodedata

    out = []
    for ch in unicodedata.normalize("NFKD", s):
        if unicodedata.combining(ch):
            continue
        if ch in _LATIN_FOLD:
            out.append(_LATIN_FOLD[ch])
            continue
        try:
            ch.encode("latin-1")
        except UnicodeEncodeError:
            # The only branch that loses content outright, and therefore the only one
            # recorded. The two above are deliberate, readable approximations INV-143
            # asks for — a stripped combining mark leaves its base letter (`ā` -> `a`)
            # and `_LATIN_FOLD` supplies a replacement — so reporting them would fire on
            # every ordinary accented European name and bury the real losses.
            _record_dropped_character(ch, s)
            continue
        out.append(ch)
    return "".join(out)


def _safe(s: str) -> str:
    """Return a string safe for fpdf2's Latin-1 core fonts.

    ⚠️ Never lets a character become `?`. `.encode("latin-1", "replace")` did, and `?` is
    itself encodable, so every encoding check passed while the page was wrong (INV-143) —
    a Bootcamper named 李明 had `??` printed on their Certificate of Completion, silently,
    at exit 0. Names come from `git config user.name` (INV-134), so non-Latin-1 text
    reaches the deliverable by the most ordinary route there is.

    Characters that cannot be folded are dropped. That can empty a string, so callers who
    print an identity — the certificate — MUST check printability rather than assume
    (`recap_certificate_name_unprintable`) and warn instead of shipping a blank.
    """
    for uni, rep in _UNICODE_MAP.items():
        s = s.replace(uni, rep)
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return _fold_to_latin1(s)


def _width(pdf, text: str) -> float:
    """Measure `text` the way it will actually be drawn — i.e. through `_safe` first.

    ⚠️ **Measurement is as font-sensitive as rendering.** fpdf2's `get_string_width`
    calls the same `normalize_text` as its text writers, so it raises
    `FPDFUnicodeEncodingException` on exactly the characters `_safe` exists to fold. Every
    *write* went through `_safe`; none of the five *measurements* did, so an em dash in a
    module title killed the whole fpdf2 render and the recap silently fell back to the
    stdlib renderer — losing real tables (INV-142) and the branded certificate (INV-156)
    from the Bootcamper's keepsake, at exit 0, with only a `renderer: stdlib` line to say
    so. Found by the 2026-07-29 dry run; `tests/test_recap_pdf_font_safety.py` passed
    throughout because it covered the write path only.

    Measuring the folded string is also the *correct* width: it is the string that gets
    drawn, so any fitting decision made from it (certificate module list, cover chips,
    env-block gutter) matches what lands on the page.

    Use this instead of `pdf.get_string_width` everywhere.
    """
    return pdf.get_string_width(_safe(text))


def _unrepresentable(text: str) -> List[str]:
    """The distinct characters `_safe` cannot represent, in order of appearance.

    Reported rather than silently dropped: a deliverable that quietly loses characters is
    the failure `?` used to make visible in the worst possible way (INV-143/INV-111).
    """
    lost: List[str] = []
    for ch in text:
        if ch in lost or ch.isspace():
            continue
        if _safe(ch) == "" and ch.strip():
            lost.append(ch)
    return lost


def _logo_info() -> Optional[Tuple[str, int, int]]:
    """Return (path, width_px, height_px) for the Senzing logo shipped beside this
    script (``senzing_logo_light.png`` — the light wordmark for dark backgrounds),
    or None when it is absent, in which case the cover falls back to a drawn badge
    so a valid PDF is always produced (INV-048/INV-066)."""
    path = Path(__file__).resolve().parent / "senzing_logo_light.png"
    try:
        with path.open("rb") as fh:
            head = fh.read(26)
    except OSError:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
        w, h = struct.unpack(">II", head[16:24])
        if w and h:
            return str(path), w, h
    return None


# Memo for `_wordmark_on_light`: the fpdf2 path renders every page twice (a measure
# pass and a real pass), so an un-memoized recolor would run the pixel work twice for
# one PDF. A list, not a dict — there is exactly one wordmark.
_WORDMARK_ON_LIGHT: List[object] = []


def _wordmark_on_light():
    """The Senzing wordmark recolored for a light background, or None.

    Only the *light* wordmark ships (``senzing_logo_light.png`` — white letterforms
    with the ember "z", drawn for the cover's dark band). The certificate is printed on
    a white card, where that asset is invisible except for the "z", so its white
    letterforms are repainted in the brand's dark ink here rather than shipping a second
    PNG that would drift from the first one silently.

    Pillow is an fpdf2 dependency, so it is present wherever fpdf2 can embed an image at
    all; any failure returns None and the caller draws the wordmark as text instead, so a
    valid PDF is still always produced (INV-048/INV-066).
    """
    if _WORDMARK_ON_LIGHT:
        return _WORDMARK_ON_LIGHT[0] or None
    image = None
    info = _logo_info()
    if info:
        try:
            from PIL import Image, ImageChops  # type: ignore

            source = Image.open(info[0]).convert("RGBA")
            red, green, blue, alpha = source.split()
            # Repaint only the near-white letterforms; the ember "z" must survive, so
            # the mask is min(r, g, b) > 200 rather than "any pixel".
            darkest = ImageChops.darker(ImageChops.darker(red, green), blue)
            mask = darkest.point(lambda v: 255 if v > 200 else 0)
            color = Image.merge("RGB", (red, green, blue))
            color.paste(Image.new("RGB", source.size, tuple(INK)), mask=mask)
            # Recolor RGB only and re-attach the original alpha: pasting an opaque RGBA
            # patch instead turns every transparent white pixel opaque, which prints the
            # wordmark as a solid dark block — and the mask covers the whole canvas,
            # because transparent pixels are white too.
            image = Image.merge("RGBA", (*color.split(), alpha))
            # The asset is padded canvas; the certificate positions the *ink*, so crop to
            # it and let the caller take the aspect ratio from the crop.
            box = alpha.getbbox()
            if box:
                image = image.crop(box)
            # The asset is ~4200 px wide and the certificate prints it at 41 mm — 2500 dpi.
            # fpdf2 re-encodes a PIL image (it cannot pass the original PNG bytes through),
            # so the full-resolution wordmark adds ~80 KB to a keepsake PDF for resolution
            # no printer resolves. 1000 px is still 600 dpi at that size.
            if image.size[0] > 1000:
                scale = 1000.0 / image.size[0]
                image = image.resize(
                    (1000, max(1, round(image.size[1] * scale))), Image.LANCZOS
                )
        except Exception:  # Pillow absent, unreadable asset, or an API change.
            image = None
    _WORDMARK_ON_LIGHT.append(image)
    return image


def render_with_fpdf2(recap: Recap, output: Path) -> bool:
    try:
        from fpdf import FPDF  # type: ignore
    except ModuleNotFoundError:
        # Not installed for THIS interpreter — the common, expected case. Naming
        # the interpreter turns the most confusing variant (fpdf2 installed into a
        # venv, script run with a different python3) from silence into a legible
        # message, instead of looking like "fpdf2 is absent from this machine".
        sys.stderr.write(
            f"fpdf2 is not installed for {sys.executable}; "
            "falling back to the stdlib renderer.\n"
        )
        return False
    except Exception as exc:
        # Present but unusable: broken build, ABI mismatch, partial install.
        # Distinct from the above because the remedy is different (reinstall or
        # repair, not install).
        sys.stderr.write(
            f"fpdf2 is installed for {sys.executable} but could not be "
            f"imported: {exc.__class__.__name__}: {exc}; "
            "falling back to the stdlib renderer.\n"
        )
        return False

    class RecapPDF(FPDF):
        # Bottom-anchored content lives in footer(), which is exempt from the auto
        # page-break, so it can never spawn a spurious blank page. Page 1 (the
        # cover) carries the credit line; every later page shows its page number.
        def footer(self) -> None:
            # The landscape certificate page suppresses the page-number footer.
            if getattr(self, "suppress_footer", False):
                return
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*SLATE)
            if self.page_no() == 1:
                self.cell(
                    0, 6, "Generated by the Senzing Bootcamp GitHub Copilot plugin", align="C"
                )
            else:
                self.cell(0, 6, str(self.page_no()), align="C")

    def new_pdf():
        pdf = RecapPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        return pdf

    try:
        # Two-pass render. The measure pass renders the exact same content — the
        # TOC with placeholder page numbers, an identical layout — and records each
        # module's real start page; the final pass then renders the TOC with those
        # numbers. Because both passes paginate identically, the numbers are
        # correct. This is deterministic and avoids fpdf2's insert_toc_placeholder
        # 2-pass render, which duplicated ("ghosted") text in the field report.
        # ⚠️ Both passes MUST render the notes page. Rendering it in one and not the
        # other shifts every page number the TOC reports after it (INV-258).
        measure = new_pdf()
        epw = measure.w - measure.l_margin - measure.r_margin
        _render_cover(measure, epw, recap)
        if recap.modules:
            _render_toc(measure, epw, recap, None, None)
        starts = [_render_module_page(measure, epw, mod) for mod in recap.modules]
        notes_start = (
            _render_notes_page(measure, epw, recap.notes) if recap.notes else None
        )
        _render_certificate(measure, recap)

        pdf = new_pdf()
        _render_cover(pdf, epw, recap)
        if recap.modules:
            _render_toc(pdf, epw, recap, starts, notes_start)
        for mod in recap.modules:
            _render_module_page(pdf, epw, mod)
        if recap.notes:
            _render_notes_page(pdf, epw, recap.notes)
        _render_certificate(pdf, recap)

        _ensure_parent(output)
        pdf.output(str(output))
        return output.exists() and output.stat().st_size > 0
    except Exception as exc:  # pragma: no cover - defensive
        sys.stderr.write(f"fpdf2 render failed: {exc}\n")
        return False


# Run-environment (hardware/software) meta keys, recorded in the recap for
# provenance and rendered as a distinct "Run environment" block — never mixed into
# the identity card and never placed on the certificate face. Matched case-folded.
_ENV_KEYS = (
    "operating system",
    "python version",
    "language runtime",
    "senzing sdk",
    "database",
)


def _is_env_key(key: str) -> bool:
    return key.strip().lower().rstrip(":") in _ENV_KEYS


def _partition_meta(
    meta: List[Tuple[str, str]]
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Split header meta into (identity rows, run-environment rows).

    Identity rows (bootcamper, dates, language, path, plugin version) drive the cover
    card; environment rows render as their own block. The certificate does **not**
    consume this partition — it takes exactly the fields it prints via ``_cert_fields``
    and ``_cert_plugin_version``.
    """
    ident = [(k, v) for k, v in meta if not _is_env_key(k)]
    env = [(k, v) for k, v in meta if _is_env_key(k)]
    return ident, env


def _render_env_block(pdf, epw: float, env: List[Tuple[str, str]], top: float) -> None:
    """Render the recap-only 'Run environment' provenance block (fpdf2 path)."""
    if not env:
        return
    # If too close to the page bottom, start a fresh page so nothing draws off-page.
    if top > pdf.h - 50:
        pdf.add_page()
        top = pdf.t_margin
    pdf.set_xy(pdf.l_margin, top)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(epw, 8, "Run environment")
    pdf.ln(10)
    for key, val in env:
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(*SLATE)
        pdf.set_font("Helvetica", "B", 9)
        label = _safe(key.rstrip(":")) + ":  "
        lw = _width(pdf, label) + 1
        pdf.cell(lw, 6, label)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(epw - lw, 6, _safe(_md_inline_to_text(val)))


def _render_cover(pdf, epw: float, recap: Recap) -> None:
    pdf.add_page()
    # Navy header band with a gold accent rule.
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 78, style="F")
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 78, pdf.w, 3, style="F")

    # Senzing logo (the light wordmark for dark backgrounds) centered in the band.
    # Falls back to a drawn "SZ" ring if the shipped asset is missing, so the PDF
    # always renders (INV-048/INV-066).
    info = _logo_info()
    placed = False
    if info:
        logo_path, lw, lh = info
        try:
            logo_h = 20.0
            logo_w = logo_h * (lw / float(lh))
            max_w = pdf.w - 2 * pdf.l_margin
            if logo_w > max_w:
                logo_w, logo_h = max_w, max_w * (lh / float(lw))
            pdf.image(logo_path, x=(pdf.w - logo_w) / 2.0, y=15.0, w=logo_w, h=logo_h)
            placed = True
        except Exception:
            placed = False
    if not placed:
        cx, cy, r = pdf.w / 2.0, 22.0, 11.0
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(1.4)
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="D")
        pdf.set_line_width(0.2)
        pdf.set_xy(cx - r, cy - 4.5)
        pdf.set_text_color(*ACCENT)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(2 * r, 9, "SZ", align="C")

    # Sub-title inside the band (the Senzing logo above carries the brand name).
    pdf.set_xy(pdf.l_margin, 45)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(epw, 13, "Bootcamp", align="C")

    pdf.set_xy(pdf.l_margin, 90)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(epw, 12, "Completion Recap", align="C")

    pdf.set_xy(pdf.l_margin, 106)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(
        epw,
        7,
        "A record of everything you built and learned, module by module. "
        "Keep it, revisit it, and share it with your team.",
        align="C",
    )

    # Two-column labeled metadata card, driven by the recap's identity meta rows
    # (run-environment rows render as their own block below the module chips).
    ident, env = _partition_meta(recap.meta)
    rows = ident or [("Bootcamper", "Bootcamper")]
    card_x = pdf.l_margin + 15
    card_w = epw - 30
    col_w = card_w / 2.0
    y0 = 132.0
    per_col = (len(rows) + 1) // 2
    card_h = 9 + per_col * 16 + 3
    pdf.set_fill_color(*LIGHT)
    pdf.set_draw_color(*LINE)
    pdf.rect(card_x, y0, card_w, card_h, style="DF")
    for i, (key, val) in enumerate(rows):
        col, pos = i % 2, i // 2
        x = card_x + 10 + col * (col_w - 4)
        y = y0 + 8 + pos * 16
        pdf.set_xy(x, y)
        pdf.set_text_color(*SLATE)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_w - 14, 5, _safe(key.upper().rstrip(":")))
        pdf.set_xy(x, y + 5.5)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(col_w - 14, 7, _safe(_md_inline_to_text(val)))

    # "Modules in this recap" chips (one per module, flowed into rows).
    if recap.modules:
        yh = y0 + card_h + 12
        pdf.set_xy(pdf.l_margin, yh)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(epw, 8, "Modules in this recap")
        x = pdf.l_margin
        y = yh + 12
        pdf.set_font("Helvetica", "", 10)
        for mod in recap.modules:
            label = _clip(
                _safe(
                    f"{mod.number}. {mod.title}"
                    if mod.number is not None
                    else mod.title
                ),
                46,
            )
            w = _width(pdf, label) + 8
            if x + w > pdf.l_margin + epw:
                x = pdf.l_margin
                y += 11
            pdf.set_fill_color(*LIGHT)
            pdf.set_draw_color(*LINE)
            pdf.rect(x, y, w, 8.5, style="DF")
            pdf.set_xy(x, y)
            pdf.set_text_color(*INK)
            pdf.cell(w, 8.5, label, align="C")
            x += w + 4

    # Run-environment provenance block (recap-only, INV-012), below the chips.
    next_y = (y + 12) if recap.modules else (y0 + card_h + 12)
    _render_env_block(pdf, epw, env, next_y)


def _cert_fields(recap: Recap) -> Tuple[str, str, List[str]]:
    """Extract (bootcamper name, formatted date, module labels) for the certificate.

    The date prefers an explicit completion/graduation date (stamped into the recap
    header at graduation) over the bootcamp start date, so a bootcamp spanning multiple
    days shows the graduation date on the Certificate of Completion, not the start date.
    Falls back to the start date when no completion date was recorded.
    """
    name = ""
    started = ""
    completed = ""
    for key, val in recap.meta:
        k = key.strip().lower().rstrip(":")
        v = _md_inline_to_text(val).strip()
        if k in ("bootcamper", "name") and not name:
            name = v
        elif k in ("completed", "graduated", "completion date") and not completed:
            completed = v
        elif k in ("started", "date") and not started:
            started = v
    # Preferences outrank the recap header: they hold the Bootcamper's answer to the
    # INV-113 certificate-name question, while the header carries whatever was
    # auto-detected before that question was asked.
    name = _CERTIFICATE_NAME_OVERRIDE or name
    # Substitution is silent here on purpose: the fpdf2 renderer runs a measure
    # pass plus a real pass, so this helper is called twice per render. The
    # user-facing warning is emitted once from main() via
    # `recap_missing_certificate_name` / `recap_certificate_name_unprintable` instead.
    #
    # A name the core fonts cannot render — 李明, Владимир — folds to nothing (`_safe`), so
    # printing it would leave the recipient line blank. The placeholder is the same answer
    # as for an absent name, and main() warns so graduation can ask for a printable one
    # (INV-113).
    if name and not _safe(name).strip():
        name = ""
    name = name or CERTIFICATE_NAME_PLACEHOLDER
    raw_date = completed or started
    date = _format_date(raw_date) if raw_date else ""
    labels = [
        (f"{m.number}. {m.title}" if m.number is not None else m.title)
        for m in recap.modules
    ]
    return name, date, labels


def _cert_plugin_version(recap: Recap) -> str:
    """The plugin version for the certificate face, or "" when it is not recorded.

    The certificate is the page most likely to be detached from the rest of the recap —
    shared, printed, or attached to something on its own — so it has to be
    self-describing about which bootcamp produced it. Graduation already stamps
    ``**Plugin version:**`` into the recap header for the cover card; this reads the same
    row.

    Returns "" rather than a placeholder: an unknown version must be **omitted**, never
    printed as "v(unknown)" on a certificate.
    """
    for key, val in recap.meta:
        if key.strip().lower().rstrip(":") == "plugin version":
            return _md_inline_to_text(val).strip()
    return ""


def _cert_attribution(recap: Recap) -> List[str]:
    """The certificate's attribution: the issuer first, then the colophon.

    Line 0 is the issuer, set over the rule in the certificate's "ISSUED BY" block. Line
    1, when a plugin version was recorded, is the colophon at the foot of the card — the
    line INV-126 requires on the certificate face itself. Both renderers read this list,
    so neither can drift from the other on what the certificate claims.
    """
    lines = ["Senzing Bootcamp"]
    version = _cert_plugin_version(recap)
    if version:
        lines.append(f"Senzing Bootcamp GitHub Copilot plugin v{version.lstrip('v')}")
    return lines


# The certificate name the Bootcamper was actually asked for, when preferences carry
# one. Set by `main()` from `config/bootcamp_preferences.yaml`; "" means "not supplied".
#
# Graduation's pre-check judges the auto-detected name and, when it is not
# certificate-quality, asks the Bootcamper what to print and persists the answer as
# `name` in preferences (INV-113). The recap's `**Bootcamper:**` line was written by
# Bootcamp preparation at the *start* of the run, from the pre-detection value — so the
# recap and preferences disagree by design after the question is asked, and the answer is
# the newer of the two. Reading only the recap printed the rejected handle on a signed
# certificate at exit 0, with 99% content retention and no warning (INV-170).
_CERTIFICATE_NAME_OVERRIDE = ""

DEFAULT_PREFERENCES = Path("config") / "bootcamp_preferences.yaml"


def read_preferences_name(path=DEFAULT_PREFERENCES) -> str:
    """The top-level ``name:`` value from the preferences YAML, or "" if absent.

    Scanned line-by-line so no third-party parser is required (INV-052: python3 only) —
    the same approach `scripts/stop-nudge.py` uses on this file. Any read problem yields
    "" rather than raising: a missing or malformed preferences file must degrade to the
    recap's name, never break the render (INV-048).
    """
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line[:1] in (" ", "\t"):
                    continue  # nested key, not the top-level `name:`
                stripped = line.strip()
                if stripped.startswith("#") or ":" not in stripped:
                    continue
                key, _, value = stripped.partition(":")
                if key.strip() != "name":
                    continue
                value = value.split(" #", 1)[0].strip().strip("\"'")
                if value:
                    return value
    except (OSError, UnicodeDecodeError):
        pass
    return ""


def set_certificate_name_override(name: str) -> None:
    """Record the preferences-supplied certificate name (or "" to clear it)."""
    global _CERTIFICATE_NAME_OVERRIDE
    _CERTIFICATE_NAME_OVERRIDE = (name or "").strip()


def certificate_name(recap: Recap) -> str:
    """The name to print on the certificate: preferences first, then the recap.

    Preferences hold the Bootcamper's *answer* to the INV-113 question, so they outrank a
    value written before that question was asked.
    """
    return _CERTIFICATE_NAME_OVERRIDE or recap_certificate_name(recap)


def recap_missing_certificate_name(recap: Recap) -> bool:
    """True when the recap carries no bootcamper name for the certificate.

    The Certificate of Completion (INV-100) then renders
    ``CERTIFICATE_NAME_PLACEHOLDER``. Callers warn on this rather than letting a
    placeholder name ship silently — it is the one artifact where a wrong name is
    immediately visible and permanently wrong.
    """
    if _CERTIFICATE_NAME_OVERRIDE:
        return False  # preferences supplied the answer to the INV-113 question
    for key, val in recap.meta:
        k = key.strip().lower().rstrip(":")
        if k in ("bootcamper", "name") and _md_inline_to_text(val).strip():
            return False
    return True


def recap_certificate_name(recap: Recap) -> str:
    """The raw bootcamper name recorded in the recap header, or "" when absent."""
    for key, val in recap.meta:
        if key.strip().lower().rstrip(":") in ("bootcamper", "name"):
            value = _md_inline_to_text(val).strip()
            if value:
                return value
    return ""


def recap_certificate_name_unprintable(recap: Recap) -> Tuple[str, List[str]]:
    """(name, lost characters) when the recorded name cannot be printed as written.

    The core fonts are Latin-1, and `_safe` drops what it cannot fold, so a name in a
    non-Latin script survives as nothing. Callers warn: this is INV-113's condition — a
    name that is present but not certificate-quality — reached by a route INV-113's own
    wording ("missing, empty, or clearly not a display name") did not anticipate, and one
    that used to print as `??` (INV-143). Returns ("", []) when the name prints fine.
    """
    name = certificate_name(recap)  # the name that will actually print
    lost = _unrepresentable(name) if name else []
    return (name, lost) if lost else ("", [])


# --------------------------------------------------------------------------- #
# Certificate of Completion (INV-100) — layout
# --------------------------------------------------------------------------- #
# Scaled from the Senzing certificate template, `resources/certificate-of-completion.pdf`
# (a maintainer asset, not shipped with the plugin — like the style reference behind
# brand_tokens): a warm ember gradient band down the left edge, a white card bordered by
# an ember rule, then the Senzing wordmark, an eyebrow, the headline, the recipient, the
# citation, and a date / issuer signature row flanking an award seal.
#
# Every number below is millimeters on landscape A4 (297 × 210), measured off the
# template at 150 dpi and shifted to A4's slightly shorter page.
# `_stdlib_certificate_stream` converts the same constants to points, so both renderers
# put the same content in the same place (INV-066/INV-126) — change a number here and the
# fallback follows it.
_MM = 72.0 / 25.4          # one millimeter in PDF points, for the fallback's point space
_CERT_BAND_W = 65.0        # ember gradient band, full height down the left edge
_CERT_CARD_X = 21.0
_CERT_CARD_Y = 26.0
_CERT_CARD_W = 255.0
_CERT_CARD_H = 158.0
_CERT_BORDER = 1.3         # ember card border stroke
_CERT_CX = 148.5           # page center; every line on the certificate is centered on it
_CERT_TEXT_W = 175.0       # wrap width for the citation and the module list
_CERT_LIST_W = 227.0       # widest a line may run: the card less both signature insets
_CERT_RULE_W = 33.0        # short ember rule under the tagline
_CERT_SIG_RULE_W = 41.2    # signature rule under each of the two bottom blocks
_CERT_SIG_INSET = 14.0     # inset of each signature block from the card's edge
_CERT_SEAL_W = 21.7        # award seal, ribbon tails included
_CERT_SEAL_H = 28.0        # a shade under the template's 29.2, to clear the colophon
_CERT_MODULE_LINES = 3     # module list is capped, so it cannot reach the seal

# Baselines, in mm from the page top. Cap tops — not baselines — were measured from the
# template, so each value is that cap top plus 0.717 em of its own font size, which is
# where fpdf2's `text()` and the fallback's `Tm` both want the pen.
_CERT_Y_WORDMARK = 33.0    # top edge of the wordmark image, not a baseline
_CERT_Y_EYEBROW = 55.5
_CERT_Y_HEADLINE = 72.0
_CERT_Y_TAGLINE = 82.1
_CERT_Y_RULE = 89.3
_CERT_Y_PRESENTED = 101.9
_CERT_Y_NAME = 115.0
_CERT_Y_CITATION = 125.2
_CERT_Y_MODULES = 136.0
_CERT_Y_SEAL = 147.5       # top edge of the seal, not a baseline
_CERT_Y_SIG = 153.1
_CERT_Y_SIG_RULE = 158.4
_CERT_Y_SIG_LABEL = 165.6
# Under the seal's ribbon tails (which end at _CERT_Y_SEAL + _CERT_SEAL_H) and clear of
# the card border's stroke — see the ⚠️ note in `_render_certificate`.
_CERT_Y_COLOPHON = 181.0
_CERT_LEAD_CITATION = 4.9  # line pitch within the citation
_CERT_LEAD_MODULES = 4.2   # line pitch within the module list

# (size in points, fpdf2 font style, letterspacing in points) per line. Shared by both
# renderers; the letterspaced lines are the template's small caps and its recipient name.
_CERT_FONT = {
    "eyebrow": (16.0, "B", 1.5),
    "headline": (38.0, "B", 0.0),
    "tagline": (15.0, "", 0.0),
    "presented": (16.0, "", 1.9),
    "name": (34.0, "B", 2.0),
    "citation": (10.5, "", 0.0),
    "modules": (9.0, "", 0.0),
    "sig": (14.0, "B", 0.0),
    "label": (9.0, "", 1.0),
    "colophon": (7.5, "I", 0.0),
}

_CERT_HEADLINE = "Certificate of Completion"
_CERT_EYEBROW = "SENZING BOOTCAMP"
_CERT_TAGLINE = "Entity Resolution, from first principles to a production pipeline"
_CERT_PRESENTED = "THIS CERTIFICATE IS PROUDLY PRESENTED TO"
_CERT_DATE_LABEL = "DATE COMPLETED"
_CERT_ISSUER_LABEL = "ISSUED BY"
# The template's citation names "all 10 modules" and then describes the whole arc of the
# bootcamp. A bootcamper who completed four modules has not walked that arc, so the count
# is taken from the recap and the description is attached to *the bootcamp* rather than to
# what was completed — the modules actually completed are then named below it (INV-100).
_CERT_CITATION = (
    "for successfully completing {count} module{plural} of the Senzing Bootcamp — "
    "Senzing's guided path from defining the business problem to a working "
    "entity-resolution pipeline:"
)
_CERT_CITATION_NO_MODULES = (
    "for successfully completing the Senzing Bootcamp — Senzing's guided path from "
    "defining the business problem to a working entity-resolution pipeline."
)


def _cert_citation(labels: List[str]) -> str:
    """The citation paragraph, carrying the number of modules actually completed."""
    if not labels:
        return _CERT_CITATION_NO_MODULES
    return _CERT_CITATION.format(
        count=len(labels), plural="" if len(labels) == 1 else "s"
    )


def _cert_band_color(fraction: float) -> Tuple[int, int, int]:
    """Color of the gradient band at `fraction` of the way down the page.

    Ember at both ends, amber through the middle — the template's warm band, mirrored
    with the brand's own gradient pair (`EMBER_HOT`/`EMBER_GRAD_END`) instead of hexes
    sampled off the template, so the certificate cannot drift from the palette (INV-081).
    The exponent widens the amber plateau so the hot ember reads as an edge rather than
    as half the band, which is the template's balance.
    """
    mix = (1.0 - abs(2.0 * fraction - 1.0)) ** 0.45
    return tuple(round(a + (b - a) * mix) for a, b in zip(ACCENT, AMBER))


def _cert_seal_paths() -> Tuple[List[Tuple[float, float]], Tuple[float, float, float],
                                List[List[Tuple[float, float]]]]:
    """Geometry for the award seal: (scalloped ring, inner circle, ribbon tails).

    Returned rather than drawn so the fpdf2 renderer and the stdlib fallback stroke the
    same shape from one computation (INV-066) — one draws it with `polygon`/`ellipse`, the
    other with `m`/`l` path operators.

    The ring is a radius modulated by a cosine, `points` per turn: a wavy edge with
    rounded tips, which is the template's medal. (A union of `points` circles — the other
    obvious construction — gives deep round lobes and reads as a flower, not a medal.)
    """
    points = 14
    outer = _CERT_SEAL_W / 2.0
    wave = 1.15                 # tip-to-trough amplitude of the scalloped edge
    mid = outer - wave
    inner = 6.7                 # inner ring, 0.62 of the outer radius as in the template
    cx = _CERT_CX
    cy = _CERT_Y_SEAL + outer
    scallop: List[Tuple[float, float]] = []
    steps = points * 12         # 12 segments per scallop keeps the tips round in print
    for i in range(steps):
        turn = 2.0 * math.pi * i / steps        # 0 at the top, so a tip sits there
        radius = mid + wave * math.cos(points * turn)
        angle = turn - math.pi / 2.0
        scallop.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    # Two ribbon tails, splayed below the ring and tucked behind it (the ring is filled
    # white over their top edges), each ending in the V notch a cut ribbon has. Offsets
    # are the template's, measured from the seal box.
    top = _CERT_Y_SEAL + 19.5
    bottom = _CERT_Y_SEAL + _CERT_SEAL_H
    notch = bottom - 3.6
    left = cx - outer
    tails = [
        [(left + 3.5, top), (left + 9.5, top), (left + 9.2, bottom),
         (left + 4.8, notch), (left + 0.2, bottom)],
        [(left + 18.2, top), (left + 12.2, top), (left + 12.5, bottom),
         (left + 16.9, notch), (left + 21.5, bottom)],
    ]
    return scallop, (cx, cy, inner), tails


def _cert_text_width(pdf, text: str, size: float, style: str, spacing: float) -> float:
    """Width in mm of one certificate line, letterspacing included but not its trailing
    advance — fpdf2 counts spacing after the last glyph too, which would shift a centered
    line half a space to the left."""
    pdf.set_font("Helvetica", style, size)
    setter = getattr(pdf, "set_char_spacing", None)
    if setter:
        setter(spacing)
    width = _width(pdf, text)
    if setter:
        setter(0)
        if spacing:
            width -= spacing * 25.4 / 72.0
    return width


def _cert_line(pdf, key: str, text: str, y: float, color, cx: float = _CERT_CX,
               size: Optional[float] = None, max_w: float = 0.0) -> None:
    """Draw one centered certificate line with its baseline at `y` (mm).

    Centered here rather than with ``cell(align="C")`` because the template's positions
    were measured as cap tops, and `text()` takes a baseline — a cell would tie the line
    to a box height instead. Letterspacing is real (``set_char_spacing``), never spaces
    inserted between glyphs: a certificate gets searched and copied out of, and
    "M i c h a e l" is not a name. When `max_w` is given the size steps down until the
    line fits, so a long recipient name shrinks instead of running off the card.
    """
    base, style, spacing = _CERT_FONT[key]
    size = base if size is None else size
    text = _safe(text)
    width = _cert_text_width(pdf, text, size, style, spacing)
    while max_w and width > max_w and size > 12.0:
        size -= 1.0
        width = _cert_text_width(pdf, text, size, style, spacing)
    # Shrinking has a floor, so it alone does not bound the line: at 12 pt a ~78-character
    # name still ran off the card and off the page — content drawn outside the page box,
    # which no retention figure can see (INV-121). Clip once the floor is reached, against a
    # strictly decreasing budget: `_clip(s, n)` returns n + 2 characters, so looping on
    # `_clip(text, len(text) - 2)` never shortens anything and spins forever.
    if max_w and width > max_w:
        full, keep = text, len(text)
        while keep > 4:
            keep -= 2
            text = full[:keep].rstrip() + "..."
            width = _cert_text_width(pdf, text, size, style, spacing)
            if width <= max_w:
                break
    pdf.set_font("Helvetica", style, size)
    setter = getattr(pdf, "set_char_spacing", None)
    if setter and spacing:
        setter(spacing)
    pdf.set_text_color(*color)
    pdf.text(cx - width / 2.0, y, text)
    if setter and spacing:
        setter(0)


def _cert_wrap(pdf, key: str, text: str, max_w: float,
               size: Optional[float] = None) -> List[str]:
    """Wrap `text` to `max_w` mm in the font `key` renders in."""
    base, style, spacing = _CERT_FONT[key]
    size = base if size is None else size
    return _wrap_to_width(
        _safe(text),
        max_w,
        lambda s: _cert_text_width(pdf, s, size, style, spacing),
    )


def _cert_module_layout(labels: List[str], measure) -> Tuple[List[str], float]:
    """The module list as (lines, size), fitted to `_CERT_MODULE_LINES` lines.

    The list is the one variable-length block on a fixed page design, and the page has no
    room to grow: below it sit the seal and the signature row, and the auto page-break is
    off, so an overlong list would print *over* them rather than reflow.

    Fitting is ordered by what it costs the page. First the template's narrow measure at
    full size, which is what a normal bootcamp needs. Then the card's full usable width —
    less like the template, but it costs nothing that matters. Only then the type size.
    Truncation is last and effectively unreachable, because the modules completed are
    required content on this page (INV-100). `measure(text, size)` is the caller's, so
    both renderers fit the list identically (INV-066).
    """
    joined = " · ".join(labels)
    base = _CERT_FONT["modules"][0]
    attempts = [(_CERT_TEXT_W, base)]
    size = base
    while size >= 7.0:
        attempts.append((_CERT_LIST_W, size))
        size -= 0.5
    lines: List[str] = []
    for width, size in attempts:
        lines = _wrap_to_width(joined, width, lambda s: measure(s, size))
        if len(lines) <= _CERT_MODULE_LINES:
            return lines, size
    lines = lines[:_CERT_MODULE_LINES]
    lines[-1] = lines[-1].rstrip(" ·") + " ..."
    return lines, size


def _cert_backdrop(pdf, height: float) -> None:
    """The gradient band and the white card the certificate is printed on."""
    # Painted as strips because fpdf2's gradient helpers are a recent addition and this
    # has to render on whatever version is installed (INV-048/INV-066). Each strip
    # overlaps the next slightly so no hairline of white shows through at the seams.
    strips = 96
    for i in range(strips):
        pdf.set_fill_color(*_cert_band_color(i / (strips - 1.0)))
        pdf.rect(0, height * i / strips, _CERT_BAND_W, height / strips + 0.15, style="F")
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(_CERT_BORDER)
    pdf.rect(_CERT_CARD_X, _CERT_CARD_Y, _CERT_CARD_W, _CERT_CARD_H, style="DF")
    pdf.set_line_width(0.2)


def _cert_wordmark(pdf) -> None:
    """The Senzing wordmark at the top of the card, as an image when one is available."""
    image = _wordmark_on_light()
    if image is not None:
        height = 11.5
        width = height * (image.size[0] / float(image.size[1]))
        try:
            pdf.image(image, x=_CERT_CX - width / 2.0, y=_CERT_Y_WORDMARK,
                      w=width, h=height)
            return
        except Exception:
            pass  # fall through to the drawn wordmark
    # Fallback: set the wordmark as text, keeping the ember "z" that carries the brand.
    pdf.set_font("Helvetica", "B", 36)
    parts = [("Sen", INK), ("z", ACCENT), ("ing", INK)]
    widths = [_width(pdf, text) for text, _ in parts]
    x = _CERT_CX - sum(widths) / 2.0
    for (text, color), width in zip(parts, widths):
        pdf.set_text_color(*color)
        pdf.text(x, _CERT_Y_WORDMARK + 9.2, text)
        x += width


def _cert_seal(pdf) -> None:
    """The award seal between the two signature blocks."""
    scallop, (cx, cy, inner), tails = _cert_seal_paths()
    outline = getattr(pdf, "polygon", None)

    def stroke(points, style: str) -> None:
        if outline:
            outline(points, style=style)
            return
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            pdf.line(x1, y1, x2, y2)  # no fill without polygon(); the outline still reads

    pdf.set_draw_color(*ACCENT)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_line_width(0.45)
    for tail in tails:
        stroke(tail, "DF")
    stroke(scallop, "DF")  # filled, so it hides where the ribbon tails pass behind it
    pdf.ellipse(cx - inner, cy - inner, inner * 2.0, inner * 2.0, style="D")
    pdf.set_line_width(0.2)


def _cert_signature_block(pdf, cx: float, value: str, label: str) -> None:
    """One bottom block: a value over a rule, with its small-caps label beneath."""
    _cert_line(pdf, "sig", value, _CERT_Y_SIG, INK, cx=cx,
               max_w=_CERT_SIG_RULE_W + 18.0)
    pdf.set_draw_color(*INK)
    pdf.set_line_width(0.4)
    pdf.line(cx - _CERT_SIG_RULE_W / 2.0, _CERT_Y_SIG_RULE,
             cx + _CERT_SIG_RULE_W / 2.0, _CERT_Y_SIG_RULE)
    pdf.set_line_width(0.2)
    _cert_line(pdf, "label", label, _CERT_Y_SIG_LABEL, MUTED, cx=cx)


def _render_certificate(pdf, recap: Recap) -> None:
    """Final page: a landscape Certificate of Completion (INV-100).

    Rendered in landscape while every other page stays portrait; the page-number footer
    is suppressed for it. The layout follows the Senzing certificate template — see the
    geometry constants above — and its palette and typography come from the brand tokens
    (INV-081).
    """
    name, date, labels = _cert_fields(recap)
    # add_page first (so the previous page's footer renders normally), then suppress
    # the footer for this — the last — page, which fpdf2 emits at output().
    pdf.add_page(orientation="L")
    pdf.suppress_footer = True
    # The certificate is a fixed single-page design: disable the auto page-break so
    # bottom-anchored content cannot spill onto a spurious second landscape page.
    pdf.set_auto_page_break(False)

    _cert_backdrop(pdf, pdf.h)  # landscape A4 ≈ 297 × 210 mm
    _cert_wordmark(pdf)
    _cert_line(pdf, "eyebrow", _CERT_EYEBROW, _CERT_Y_EYEBROW, ACCENT)
    _cert_line(pdf, "headline", _CERT_HEADLINE, _CERT_Y_HEADLINE, ACCENT)
    _cert_line(pdf, "tagline", _CERT_TAGLINE, _CERT_Y_TAGLINE, INK)

    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.85)
    pdf.line(_CERT_CX - _CERT_RULE_W / 2.0, _CERT_Y_RULE,
             _CERT_CX + _CERT_RULE_W / 2.0, _CERT_Y_RULE)
    pdf.set_line_width(0.2)

    _cert_line(pdf, "presented", _CERT_PRESENTED, _CERT_Y_PRESENTED, MUTED)
    _cert_line(pdf, "name", name, _CERT_Y_NAME, INK, max_w=_CERT_LIST_W)

    y = _CERT_Y_CITATION
    for line in _cert_wrap(pdf, "citation", _cert_citation(labels), _CERT_TEXT_W):
        _cert_line(pdf, "citation", line, y, SLATE)
        y += _CERT_LEAD_CITATION
    if labels:
        # Anchored, not flowed from the citation: the module list has to start at a fixed
        # place so its own capped growth is the only thing that can move on this page.
        y = _CERT_Y_MODULES
        style, spacing = _CERT_FONT["modules"][1:]
        lines, size = _cert_module_layout(
            labels, lambda s, pt: _cert_text_width(pdf, s, pt, style, spacing)
        )
        for line in lines:
            _cert_line(pdf, "modules", line, y, SLATE, size=size)
            y += _CERT_LEAD_MODULES

    _cert_seal(pdf)
    if date:
        _cert_signature_block(
            pdf, _CERT_CARD_X + _CERT_SIG_INSET + _CERT_SIG_RULE_W / 2.0,
            date, _CERT_DATE_LABEL,
        )
    # ⚠️ Both attribution lines are bottom-anchored and must clear the card's ember
    # border, whose bottom edge is at _CERT_CARD_Y + _CERT_CARD_H: a line under it is
    # sliced in half by the stroke while text extraction still reports the string present
    # and correct (INV-126). Verify by rasterizing the page, never by pdftotext.
    attribution = _cert_attribution(recap)
    _cert_signature_block(
        pdf, _CERT_CARD_X + _CERT_CARD_W - _CERT_SIG_INSET - _CERT_SIG_RULE_W / 2.0,
        attribution[0], _CERT_ISSUER_LABEL,
    )
    for line in attribution[1:]:
        _cert_line(pdf, "colophon", line, _CERT_Y_COLOPHON, MUTED)
    # Leave suppress_footer set: this is the last page.


def _render_toc(pdf, epw: float, recap: Recap, starts: Optional[List[int]],
                notes_start: Optional[int] = None) -> None:
    """Render the table of contents. ``starts`` is None in the measure pass
    (placeholder page numbers, identical layout) and the real per-module start
    pages in the final pass, so both passes paginate identically."""
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 24, style="F")
    pdf.set_xy(pdf.l_margin, 7)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(epw, 9, "Contents")
    pdf.ln(24)
    pdf.ln(4)
    for i, mod in enumerate(recap.modules):
        label = (
            f"Module {mod.number}: {mod.title}"
            if mod.number is not None
            else mod.title
        )
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(epw - 16, 8, _clip(_safe(label), 66))
        pdf.set_text_color(*BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(16, 8, "" if starts is None else str(starts[i]), align="R")
        pdf.ln(8)

    # The notes row goes AFTER the module rows, mirroring where the page itself sits
    # (INV-258). It is a row in the contents, never a module: nothing else in this file
    # reads the TOC, so listing it here cannot leak it into the certificate or the cover.
    if recap.notes:
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(epw - 16, 8, _clip(_safe(recap.notes.title), 66))
        pdf.set_text_color(*BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(16, 8, "" if notes_start is None else str(notes_start), align="R")
        pdf.ln(8)


def _render_module_page(pdf, epw: float, mod) -> int:
    """Render one module onto a fresh page; return the page number it starts on."""
    pdf.add_page()
    start = pdf.page_no()
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, pdf.w, 24, style="F")
    pdf.set_xy(pdf.l_margin, 6)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    heading = (
        f"Module {mod.number}: {mod.title}" if mod.number is not None else mod.title
    )
    pdf.cell(epw, 9, _clip(_safe(heading), 62))
    if mod.date:
        pdf.set_xy(pdf.l_margin, 15)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(epw, 5, _safe(f"Completed {_format_date(mod.date)}"))
    pdf.ln(24)

    gaps = tuple(mod.missing_summary_blocks())
    for name in REQUIRED_SECTIONS:
        _render_subsection(
            pdf, epw, name, mod.subsection(name),
            gaps if name == REQUIRED_SECTIONS[3] else (),
        )

    # Any extra sub-sections (e.g. Duration) after the required set.
    for sub_h, content in mod.subsections:
        if _normalize_heading(sub_h) not in {
            _normalize_heading(r) for r in REQUIRED_SECTIONS
        }:
            _render_subsection(pdf, epw, sub_h, content)
    return start


def _render_notes_page(pdf, epw: float, notes: NotesSection) -> int:
    """Render the Bootcamper's notes onto a fresh page; return its start page.

    Styled like a module page but visibly its own thing — its own header band color and
    a heading that reads as the Bootcamper's rather than the bootcamp's — because this
    is the one section of the keepsake they wrote.
    """
    pdf.add_page()
    start = pdf.page_no()
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, pdf.w, 24, style="F")
    pdf.set_xy(pdf.l_margin, 6)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(epw, 9, _clip(_safe(notes.title), 62))
    pdf.set_xy(pdf.l_margin, 15)
    pdf.set_font("Helvetica", "", 9)
    count = len(notes.entries)
    pdf.cell(epw, 5, _safe(
        "In your own words — %d note%s captured during the bootcamp"
        % (count, "" if count == 1 else "s")))
    pdf.ln(24)

    for note in notes.entries:
        pdf.ln(3)
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 12)
        heading = f"{note.type}: {note.title}" if note.type else note.title
        pdf.multi_cell(epw, 6, _safe(heading))

        stamp = " · ".join(p for p in (note.captured, note.module) if p)
        if stamp:
            pdf.set_x(pdf.l_margin)
            pdf.set_text_color(*SLATE)
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.multi_cell(epw, 4.6, _safe(stamp))

        body = [line for line in note.body if line.strip()]
        if body:
            pdf.ln(0.8)
            pdf.set_x(pdf.l_margin)
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "", 10.5)
            for line in body:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(epw, 5.2, _safe(_md_inline_to_text(line.strip())))

        # ⛔ Context and Elaboration carry their own labels because neither is the
        # Bootcamper's writing (INV-257). The elaboration says whose words it is on the
        # page, not merely in the source, so the distinction survives printing.
        for label, value in (("Context", note.context),
                             ("Elaboration (written by the bootcamp)",
                              note.elaboration)):
            if not value:
                continue
            pdf.ln(0.8)
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_text_color(*SLATE)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.multi_cell(epw - 4, 4.6, _safe(label.upper()))
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(epw - 4, 4.8, _safe(_md_inline_to_text(value)))

        pdf.ln(2)
        pdf.set_draw_color(*LINE)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.l_margin + epw, y)
    return start


def _render_subsection(pdf, epw, name: str, content: Optional[List[str]],
                       missing_blocks: Tuple[str, ...] = ()) -> None:
    """Render one labeled subsection. ``missing_blocks`` names the End-of-Module Summary
    blocks the recap did not record; each is rendered as "(not recorded)" so the three
    blocks INV-103 requires are always *visible* on the page. A keepsake that silently
    omits them looks complete, which is how they went missing without anyone noticing."""
    from_missing = content is None
    pdf.ln(1)
    # Colored accent tab + matching heading color per sub-section.
    accent = _section_accent(name)
    y = pdf.get_y()
    pdf.set_fill_color(*accent)
    pdf.rect(pdf.l_margin, y + 0.5, 2.6, 7, style="F")
    pdf.set_xy(pdf.l_margin + 5.5, y)
    pdf.set_text_color(*accent)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(epw - 5.5, 8, _safe(name))
    pdf.ln(9)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 10.5)
    empty = from_missing or not any(l.strip() for l in content)
    if empty and not missing_blocks:
        pdf.set_text_color(*SLATE)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(epw, 6, "(not recorded)")
        pdf.ln(1)
        return
    unspaced_section = _normalize_heading(name) in _UNSPACED_SUBSECTIONS
    active_label = ""
    in_item = False
    index = 0
    while index < len(content or []):
        line = content[index]
        # A run of pipe rows is ONE table and is drawn as a grid (INV-142). It is
        # handled here rather than in _render_line because a table spans lines and
        # _render_line only ever sees one.
        run = _table_run(content, index)
        if run:
            _render_table_fpdf2(pdf, epw, "\n".join(content[index : index + run]))
            index += run
            in_item = False
            continue
        label = _block_label(line)
        if label:
            active_label = label
        _render_line(pdf, epw, line)
        in_item = _still_in_list_item(line, in_item)
        if in_item and not unspaced_section and active_label not in _UNSPACED_LABELS:
            if _next_nonblank_is_top_level_bullet(content, index):
                pdf.ln(_ITEM_GAP_MM)
        index += 1
    for block in missing_blocks:
        _render_line(pdf, epw, f"**{block}:** (not recorded)")
    pdf.ln(2)


def _is_empty_takeaway(text: str) -> bool:
    """True for a '**Bootcamper's takeaway:**' line with no real value (empty or "N/A").

    The takeaway is an optional field within the End-of-Module Summary subsection; when the
    bootcamper gave none, the line is omitted rather than rendered as an "N/A" placeholder.
    """
    m = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", text.strip())
    return bool(
        m
        and m.group(1).strip().lower() == "bootcamper's takeaway"
        and m.group(2).strip(" .").lower() in ("", "n/a", "none")
    )


def _render_image(pdf, epw, path: str, alt: str = "") -> None:
    """Embed a local visualization screenshot into the recap, best-effort and non-fatal.

    A missing/unreadable image, an fpdf2 build without image support, or a bad
    file is skipped — an optional decoration must never break the recap PDF
    (INV-048) — but the skip is recorded and reported, never silent (INV-111):
    the bootcamper's own screenshots are the most visual content in the keepsake,
    and losing them used to produce no error, no warning, and a success line
    reporting ~99% of characters rendered. Remote URLs are never fetched
    (offline — INV-081).
    """
    if IMAGE_URL_RE.match(path):
        _record_image_outcome(path, "remote")
        return  # never fetch a remote URL (offline guarantee)
    p = resolve_recap_image(path)
    if p is None:
        _record_image_outcome(path, "missing")
        return
    try:
        pdf.ln(1)
        pdf.set_x(pdf.l_margin)
        pdf.image(str(p), w=min(epw, 130.0))
        pdf.ln(1)
        if alt:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*SLATE)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 4.5, _safe(alt))
            pdf.set_text_color(*INK)
        pdf.ln(2)
    except Exception as exc:
        # Any embedding failure → skip the image, keep the PDF valid. Reported
        # rather than swallowed: "found but unusable" needs a different remedy
        # from "not found" (INV-111).
        _record_image_outcome(path, f"unreadable ({exc.__class__.__name__})")
        return
    _record_image_outcome(path, "embedded")


def _table_widths(header: List[str], rows: List[List[str]], epw: float) -> List[float]:
    """Column widths proportional to the longest cell per column.

    Each column keeps a floor so nothing collapses to a sliver, and a cap so one
    very long cell cannot squeeze the others out.
    """
    spans = []
    for index in range(len(header)):
        longest = max([len(header[index])] + [len(r[index]) for r in rows] or [1])
        spans.append(min(max(longest, 6), 60))
    total = float(sum(spans)) or 1.0
    return [epw * (span / total) for span in spans]


def _render_table_monospace(pdf, epw: float, header, rows) -> None:
    """Last-resort table rendering: aligned monospace columns, never pipe source.

    Reached only if the grid path raises (an old fpdf2 without ``will_page_break``,
    for instance). INV-142 permits aligned columns as a lesser rendering; it does
    NOT permit falling back to the Markdown source text.
    """
    widths = [min(max(len(r[i]) for r in [header] + rows), 46) for i in range(len(header))]
    pdf.set_font("Courier", "", 8.5)
    pdf.set_text_color(*INK)
    for row_index, row in enumerate([header] + rows):
        pdf.set_x(pdf.l_margin)
        text = "  ".join(c[:w].ljust(w) for c, w in zip(row, widths)).rstrip()
        pdf.multi_cell(epw, 4.6, _safe(text) or " ")
        if row_index == 0:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 4.6, "  ".join("-" * w for w in widths))
    pdf.set_font("Helvetica", "", 10.5)


def _render_table_fpdf2(pdf, epw: float, text: str) -> None:
    """Draw a Markdown table in a recap section as an actual grid (INV-142).

    Without this the pipe rows reached the keepsake PDF as source text — the
    ``|---|---|`` alignment row and all — while every success signal (exit 0,
    ``PDF generated:``, a high content-retention figure) reported success, because
    the characters *were* in the content stream, merely unreadable. The retention
    figure cannot see this: it counts characters, not whether they render as the
    construct they describe.

    Mirrors ``generate_discoveries_pdf._render_table_fpdf2``: bordered cells, a
    filled header band, the alignment row dropped, the header repeated after a
    page break (with the following body row restored to the body font), and short
    cells padded to the row height so the grid stays square.
    """
    header, rows = parse_table(text)
    if not header:
        return
    plain_header = [_safe(_md_inline_to_text(c)) for c in header]
    plain_rows = [[_safe(_md_inline_to_text(c)) for c in row] for row in rows]
    widths = _table_widths(plain_header, plain_rows, epw)
    line_h = 4.6

    pdf.ln(1)
    try:
        pdf.set_draw_color(*LINE)
        pdf.set_line_width(0.15)

        def cell_height(width: float, cell: str) -> float:
            lines = pdf.multi_cell(
                width, line_h, cell or " ", dry_run=True, output="LINES", border=0
            )
            return max(len(lines), 1) * line_h

        def emit_row(cells: List[str], is_header: bool) -> None:
            pdf.set_font("Helvetica", "B" if is_header else "", 8.5)
            row_h = max(cell_height(w, c) for w, c in zip(widths, cells))
            if pdf.will_page_break(row_h):
                pdf.add_page()
                if not is_header:
                    # Repeat the header on the new page, then restore THIS row's
                    # style — otherwise the first body row after every page break
                    # renders as a second header.
                    emit_row(plain_header, True)
                    pdf.set_font("Helvetica", "", 8.5)
            x0, y0 = pdf.l_margin, pdf.get_y()
            if is_header:
                pdf.set_fill_color(*TABLE_HEAD_FILL)
            pdf.set_text_color(*INK)
            x = x0
            for width, cell in zip(widths, cells):
                pdf.set_xy(x, y0)
                pdf.multi_cell(
                    width, line_h, cell or " ", border=1, align="L",
                    fill=is_header, max_line_height=line_h,
                    new_x="RIGHT", new_y="TOP",
                )
                drawn = cell_height(width, cell)
                if drawn < row_h:
                    pdf.rect(x, y0 + drawn, width, row_h - drawn,
                             style="FD" if is_header else "D")
                x += width
            pdf.set_xy(x0, y0 + row_h)

        emit_row(plain_header, True)
        for row in plain_rows:
            emit_row(row, False)
    except Exception:
        _render_table_monospace(pdf, epw, plain_header, plain_rows)
    # Separate two adjacent tables visibly, so they cannot read as one grid.
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_x(pdf.l_margin)
    pdf.ln(2)


def _render_line(pdf, epw, line: str) -> None:
    stripped = line.strip()
    if not stripped:
        pdf.ln(3)
        return
    if stripped.startswith("<!--") and stripped.endswith("-->"):
        return  # HTML comment (e.g. a maintainer note in the source): never rendered
    if _is_empty_takeaway(stripped):
        return
    # Embedded visualization screenshot: ![alt](path) on its own line.
    #
    # Uses IMAGE_LINE_RE rather than a second copy of the pattern: the counter
    # (`recap_image_targets`) and this renderer decide the same question, and when they
    # were written separately they could disagree about what an image line is. Checked
    # before the bullet branch below, so a bulleted image renders AS an image.
    img = IMAGE_LINE_RE.match(stripped)
    if img:
        _render_image(pdf, epw, img.group(2).strip(), img.group(1).strip())
        return
    indent = 0
    bullet = ""
    m = re.match(r"^(\s*)([-*])\s+(.*)$", line)
    if m:
        lead = len(m.group(1))
        indent = 6 + (6 if lead >= 4 else 0)
        bullet = "·  "  # middle dot (Latin-1 safe)
        stripped = m.group(3).strip()
    # Bold "Key:" prefix (e.g. **Q:**, **What we did:**).
    bold_prefix = ""
    bm = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", stripped)
    if bm:
        bold_prefix = _safe(bm.group(1) + ": ")
        stripped = bm.group(2).strip()
    stripped = _safe(_md_inline_to_text(stripped))
    x = pdf.l_margin + indent
    pdf.set_x(x)
    if bullet:
        pdf.set_font("Helvetica", "", 10.5)
        pdf.cell(6, 5.5, bullet)
        x = pdf.get_x()
    force_new_line = bool(bm) and _normalize_heading(bm.group(1)) in _NEW_LINE_LABELS
    if bold_prefix:
        pdf.set_font("Helvetica", "B", 10.5)
        if force_new_line:
            # Label on its own line; a blank-line gap, then the value starts fresh,
            # indented, below it -- never hanging-indented under wherever the label
            # happened to end.
            pdf.multi_cell(epw - indent, 5.5, _safe(bm.group(1) + ":"))
            pdf.ln(_ITEM_GAP_MM * 2)
            # 12 mm matches where bullet TEXT starts (6 mm list indent + the 6 mm
            # bullet-marker cell drawn above), so the paragraph lines up with the
            # bullets in "What you accomplished"/"Files produced" above it.
            indent += 12
            pdf.set_x(pdf.l_margin + indent)
        else:
            pdf.cell(_width(pdf, bold_prefix) + 1, 5.5, _safe(bold_prefix))
    pdf.set_font("Helvetica", "", 10.5)
    remaining = epw - (pdf.get_x() - pdf.l_margin)
    # A long bold label (e.g. a "**Q:**" carrying a full question) leaves a narrow
    # column, and every wrapped line then stacks in it beside a large empty gutter.
    # A bare 20 mm floor is an order of magnitude too low to catch that: ~60 mm of a
    # 190 mm line clears it and still reads as a ribbon. Break once the label has
    # eaten half the width; short labels still render inline, which reads well.
    if not force_new_line and remaining < max(20.0, epw * 0.5):
        indent = min(indent + 6, epw - 20)
        remaining = epw - indent
        pdf.ln(5.5)
        pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(remaining, 5.5, stripped if stripped else " ")


def _clip(s: str, n: int) -> str:
    """Truncate to ``n`` characters with an ASCII ellipsis.

    ⛔ **The ellipsis must stay ASCII.** Every call site is ``_clip(_safe(x), n)`` —
    ``_safe`` runs *first*, so anything ``_clip`` appends afterwards is never sanitized.
    A U+2026 "…" here therefore reached fpdf2's Latin-1 core font unescaped and raised
    ``Character "…" … outside the range of characters supported``, which
    ``render_with_fpdf2`` catches — so the only symptom was every affected bootcamper
    silently getting the plainer stdlib PDF instead of the designed one (INV-048).

    Found by the 2026-07-26 dry run on the cover's module chips (``_clip(..., 46)``).
    Today no real module title reaches that width: "Data Quality, Mapping, and
    Transformation" is the longest at 41 characters, ``_split_title_date`` splits a
    timestamp or the ``in progress`` marker off the title before the chip is built, and
    even a two-digit number prefix makes only 45 — so a realistic recap cannot exercise
    the path, and a unit test does. ``_UNICODE_MAP`` maps "…" to "..." already; the
    defect was purely the order of operations, which is why the fix is here rather than
    at the three call sites — an ASCII suffix cannot be got wrong.
    ``tests/test_recap_pdf_font_safety.py`` pins this.
    """
    return s if len(s) <= n else s[: n - 1] + "..."


# --------------------------------------------------------------------------- #
# Stdlib-only fallback renderer
# --------------------------------------------------------------------------- #
# Helvetica advance widths (1/1000 em) for the glyphs that actually move a centered line;
# everything else is within a hair of 556. This writer has no font metrics of its own, and
# the crude `len(text) * size * 0.52` it used before put the certificate's 38 pt headline
# 8 mm off center — visible on the page, invisible to text extraction.
_HELV_W = {
    " ": 278, "!": 278, '"': 355, "'": 191, "(": 333, ")": 333, "*": 389, ",": 278,
    "-": 333, ".": 278, "/": 278, ":": 278, ";": 278, "[": 278, "]": 278, "|": 260,
    "·": 278, "&": 667, "%": 889, "@": 1015,
    "c": 500, "f": 278, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "r": 333,
    "s": 500, "t": 278, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "C": 722, "D": 722, "F": 611, "G": 778, "H": 722, "I": 278, "J": 500, "K": 667,
    "L": 556, "M": 833, "N": 722, "O": 778, "Q": 778, "R": 722, "T": 611, "U": 722,
    "W": 944, "Z": 611,
}
# Helvetica-Bold runs ~8% wider than Helvetica across mixed-case text; one factor is
# accurate enough to center a line, and far more accurate than ignoring the difference.
_HELV_BOLD_FACTOR = 1.08


def _stdlib_width(text: str, size: float, bold: bool, spacing: float = 0.0) -> float:
    """Approximate width in points of `text` set in Helvetica at `size`."""
    units = sum(_HELV_W.get(ch, 556) for ch in text)
    width = units / 1000.0 * size * (_HELV_BOLD_FACTOR if bold else 1.0)
    return width + spacing * max(0, len(text) - 1)


def _stdlib_certificate_stream(recap: Recap, w: float, h: float) -> str:
    """Build a landscape Certificate of Completion content stream (stdlib fallback, INV-100).

    Follows the same template geometry as the fpdf2 renderer — same constants, same
    millimeter positions, converted to this writer's point space — so the fallback is a
    plainer *rendering* of one design rather than a second design (INV-066/INV-126). What
    it gives up: the wordmark is set as text instead of embedded, and italic degrades to
    regular, because this writer embeds neither images nor an oblique face.
    """
    name, date, labels = _cert_fields(recap)
    ops: List[str] = []

    def rgb(color, op: str) -> str:
        r, g, b = (c / 255.0 for c in color)
        return f"{r:.3f} {g:.3f} {b:.3f} {op}"

    def flip(mm: float) -> float:
        """A millimeter offset from the page top as a PDF point from the page bottom."""
        return h - mm * _MM

    def path(points, style: str, width: float, stroke_color=ACCENT) -> None:
        """Stroke (and optionally fill white) a closed polygon given in mm."""
        moves = [f"{x * _MM:.2f} {flip(y):.2f} {'m' if i == 0 else 'l'}"
                 for i, (x, y) in enumerate(points)]
        fill = "1 1 1 rg " if "F" in style else ""
        ops.append(
            f"{fill}{rgb(stroke_color, 'RG')} {width:.2f} w "
            + " ".join(moves)
            + (" h B" if "F" in style else " h S")
        )

    def rule(x1: float, x2: float, y: float, width: float, color) -> None:
        ops.append(
            f"{rgb(color, 'RG')} {width:.2f} w {x1 * _MM:.2f} {flip(y):.2f} m "
            f"{x2 * _MM:.2f} {flip(y):.2f} l S"
        )

    def line(key: str, text: str, y: float, color, cx: float = _CERT_CX,
             size: Optional[float] = None) -> None:
        base, style, spacing = _CERT_FONT[key]
        size = base if size is None else size
        # Sanitize BEFORE measuring. `_safe` can change length ("∞" -> "infinity"), so
        # measuring raw text and rendering sanitized text mis-centers the line — the same
        # desync the comment below describes for escaping, one step earlier.
        text = _safe(text)
        # Measure the text, escape only what is written: `_pdf_escape` turns "·" into the
        # 4-character sequence `\267`, so measuring after escaping mis-centers the line —
        # and escaping twice prints the escape itself.
        width = _stdlib_width(text, size, style == "B", spacing)
        text = _pdf_escape(text)
        x = cx * _MM - width / 2.0
        # Italic degrades to regular: this writer embeds no oblique face (INV-066's
        # "plainer but valid" rendering), and a fabricated slant is worse than none.
        font = "F2" if style == "B" else "F1"
        tc = f"{spacing:.2f} Tc " if spacing else ""
        ops.append(
            f"{rgb(color, 'rg')}\nBT /{font} {size:.1f} Tf {tc}"
            f"1 0 0 1 {x:.2f} {flip(y):.2f} Tm ({text}) Tj"
            + (" 0 Tc" if spacing else "")
            + " ET"
        )

    def wrap(key: str, text: str, size: Optional[float] = None) -> List[str]:
        base, style, spacing = _CERT_FONT[key]
        size = base if size is None else size
        return _wrap_to_width(
            # Sanitize before wrapping: line breaks chosen on raw text do not hold once a
            # character transliterates to a longer form.
            _safe(text),
            _CERT_TEXT_W * _MM,
            lambda s: _stdlib_width(s, size, style == "B", spacing),
        )

    # Gradient band, then the white card: the same two-layer backdrop the fpdf2
    # renderer paints, in the same place (INV-066).
    strips = 96
    strip_h = h / strips
    for i in range(strips):
        color = _cert_band_color(i / (strips - 1.0))
        ops.append(
            f"{rgb(color, 'rg')} 0 {h - (i + 1) * strip_h:.2f} "
            f"{_CERT_BAND_W * _MM:.2f} {strip_h + 0.4:.2f} re f"
        )
    ops.append(
        f"1 1 1 rg {rgb(ACCENT, 'RG')} {_CERT_BORDER * _MM:.2f} w "
        f"{_CERT_CARD_X * _MM:.2f} {flip(_CERT_CARD_Y + _CERT_CARD_H):.2f} "
        f"{_CERT_CARD_W * _MM:.2f} {_CERT_CARD_H * _MM:.2f} re B"
    )

    # Wordmark. No image support in this writer, so it is set as text — with the ember
    # "z" that carries the brand, exactly like the fpdf2 renderer's own fallback.
    parts = [("Sen", INK), ("z", ACCENT), ("ing", INK)]
    widths = [_stdlib_width(text, 36, True, 0.0) for text, _ in parts]
    x = _CERT_CX * _MM - sum(widths) / 2.0
    for (text, color), width in zip(parts, widths):
        ops.append(
            f"{rgb(color, 'rg')}\nBT /F2 36.0 Tf 1 0 0 1 {x:.2f} "
            f"{flip(_CERT_Y_WORDMARK + 9.2):.2f} Tm ({_pdf_escape(text)}) Tj ET"
        )
        x += width

    line("eyebrow", _CERT_EYEBROW, _CERT_Y_EYEBROW, ACCENT)
    line("headline", _CERT_HEADLINE, _CERT_Y_HEADLINE, ACCENT)
    line("tagline", _CERT_TAGLINE, _CERT_Y_TAGLINE, INK)
    rule(_CERT_CX - _CERT_RULE_W / 2.0, _CERT_CX + _CERT_RULE_W / 2.0,
         _CERT_Y_RULE, 0.85 * _MM, ACCENT)
    line("presented", _CERT_PRESENTED, _CERT_Y_PRESENTED, MUTED)
    line("name", name, _CERT_Y_NAME, INK)

    y = _CERT_Y_CITATION
    for chunk in wrap("citation", _cert_citation(labels)):
        line("citation", chunk, y, SLATE)
        y += _CERT_LEAD_CITATION
    if labels:
        y = _CERT_Y_MODULES
        style, spacing = _CERT_FONT["modules"][1:]
        chunks, size = _cert_module_layout(
            labels,
            lambda s, pt: _stdlib_width(s, pt, style == "B", spacing) / _MM,
        )
        for chunk in chunks:
            line("modules", chunk, y, SLATE, size=size)
            y += _CERT_LEAD_MODULES

    # Award seal, from the shared geometry so both renderers stroke one shape.
    scallop, (seal_cx, seal_cy, inner), tails = _cert_seal_paths()
    for tail in tails:
        path(tail, "DF", 0.45 * _MM)
    path(scallop, "DF", 0.45 * _MM)
    path(
        [(seal_cx + inner * math.cos(math.tau * i / 48),
          seal_cy + inner * math.sin(math.tau * i / 48)) for i in range(48)],
        "D", 0.45 * _MM,
    )

    def signature(cx: float, value: str, label: str) -> None:
        line("sig", value, _CERT_Y_SIG, INK, cx=cx)
        rule(cx - _CERT_SIG_RULE_W / 2.0, cx + _CERT_SIG_RULE_W / 2.0,
             _CERT_Y_SIG_RULE, 0.4 * _MM, INK)
        line("label", label, _CERT_Y_SIG_LABEL, MUTED, cx=cx)

    if date:
        signature(_CERT_CARD_X + _CERT_SIG_INSET + _CERT_SIG_RULE_W / 2.0,
                  date, _CERT_DATE_LABEL)
    # Attribution: the issuer over the "ISSUED BY" rule, then the version colophon at
    # the foot of the card — same content, same positions as the fpdf2 renderer, which is
    # what INV-126 requires of the fallback.
    attribution = _cert_attribution(recap)
    signature(_CERT_CARD_X + _CERT_CARD_W - _CERT_SIG_INSET - _CERT_SIG_RULE_W / 2.0,
              attribution[0], _CERT_ISSUER_LABEL)
    for text in attribution[1:]:
        line("colophon", text, _CERT_Y_COLOPHON, MUTED)
    return "\n".join(ops)


def render_with_stdlib(recap: Recap, output: Path) -> bool:
    """Write a valid, paginated PDF using only the standard library.

    Uses the built-in Helvetica/Helvetica-Bold fonts (no embedding needed) and
    a hand-rolled page/xref writer. Plainer than the fpdf2 output but a
    genuinely valid PDF carrying the same content.
    """
    try:
        page_w, page_h = 595.0, 842.0  # A4 in points
        margin = 54.0
        line_h = 14.0
        max_width_chars = 92  # conservative wrap for 10pt Helvetica

        # Build a flat list of (text, font, size, indent) render tokens.
        tokens: List[Tuple[str, str, float, float]] = []

        def add(text: str, font: str = "F1", size: float = 10.5, indent: float = 0.0) -> None:
            # The one choke point for stdlib text: sanitize here so `_pdf_escape` only ever
            # sees Latin-1 and never has to substitute (INV-143). `_safe` is idempotent, so
            # text already sanitized by `add_wrapped` passes through unchanged.
            tokens.append((_safe(text), font, size, indent))

        def add_wrapped(text: str, font: str, size: float, indent: float) -> None:
            width = max(20, max_width_chars - int(indent / 6))
            # Sanitize BEFORE wrapping — `_wrap` counts characters, and "∞" -> "infinity"
            # changes the count, so wrapping raw text yields lines that overrun once
            # rendered.
            for chunk in _wrap(_safe(text), width):
                add(chunk, font, size, indent)

        add(recap.title, "F2", 22, 0)
        add("Completion Recap", "F2", 14, 0)
        add("", "F1", 6, 0)
        ident, env = _partition_meta(recap.meta)
        for key, val in ident:
            add_wrapped(f"{key}: {_md_inline_to_text(val)}", "F1", 11, 0)
        completed = ", ".join(
            (f"Module {m.number}" if m.number is not None else m.title)
            for m in recap.modules
        )
        if completed:
            add("", "F1", 4, 0)
            add_wrapped(f"Modules completed: {completed}", "F1", 11, 0)
        if env:
            add("", "F1", 6, 0)
            add("Run environment", "F2", 12, 0)
            for key, val in env:
                add_wrapped(f"{key}: {_md_inline_to_text(val)}", "F1", 10, 6)

        for mod in recap.modules:
            add("", "F1", 10, 0)
            heading = (
                f"Module {mod.number}: {mod.title}"
                if mod.number is not None
                else mod.title
            )
            add_wrapped(heading, "F2", 15, 0)
            gaps = tuple(mod.missing_summary_blocks())
            for name in REQUIRED_SECTIONS:
                _stdlib_subsection(
                    add, add_wrapped, name, mod.subsection(name),
                    gaps if name == REQUIRED_SECTIONS[3] else (),
                )
            for h, content in mod.subsections:
                if _normalize_heading(h) not in {
                    _normalize_heading(r) for r in REQUIRED_SECTIONS
                }:
                    _stdlib_subsection(add, add_wrapped, h, content)

        # The Bootcamper's notes, after the last module and before the certificate —
        # which is appended as its own page below, so "after the module loop" here is
        # the same position the fpdf2 renderer uses (INV-066 parity, INV-258).
        if recap.notes:
            add("", "F1", 10, 0)
            add_wrapped(recap.notes.title, "F2", 15, 0)
            for note in recap.notes.entries:
                add("", "F1", 4, 0)
                heading = f"{note.type}: {note.title}" if note.type else note.title
                add_wrapped(heading, "F2", 12, 0)
                stamp = " - ".join(p for p in (note.captured, note.module) if p)
                if stamp:
                    add_wrapped(stamp, "F1", 9, 6)
                for line in note.body:
                    if line.strip():
                        add_wrapped(_md_inline_to_text(line.strip()), "F1", 10, 6)
                if note.context:
                    add_wrapped(f"Context: {_md_inline_to_text(note.context)}",
                                "F1", 9.5, 12)
                if note.elaboration:
                    add_wrapped(
                        "Elaboration (written by the bootcamp): "
                        f"{_md_inline_to_text(note.elaboration)}", "F1", 9.5, 12)

        # Paginate tokens into pages of content streams.
        pages: List[str] = []
        y = page_h - margin
        buf: List[str] = []

        def flush_page() -> None:
            if buf:
                pages.append("\n".join(buf))

        for text, font, size, indent in tokens:
            # A "GAP" token is pure vertical space of exactly `size` points; it emits no
            # text op, so it never references a font resource. Needed because an ordinary
            # empty token costs 0.6 of a line — too much for an inter-item gap.
            gap = font == "GAP"
            advance = size if gap else (line_h if text else line_h * 0.6)
            if y - advance < margin:
                flush_page()
                buf = []
                y = page_h - margin
            if not gap:
                esc = _pdf_escape(text)
                x = margin + indent
                buf.append(
                    f"BT /{font} {size:.1f} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm ({esc}) Tj ET"
                )
            y -= advance
        flush_page()
        if not pages:
            pages = [f"BT /F1 11 Tf 1 0 0 1 {margin} {page_h - margin} Tm (Bootcamp recap) Tj ET"]

        # Content pages are portrait; append the landscape Certificate of Completion (INV-100).
        page_sizes: List[Tuple[float, float]] = [(page_w, page_h)] * len(pages)
        cert_w, cert_h = page_h, page_w  # landscape A4
        pages.append(_stdlib_certificate_stream(recap, cert_w, cert_h))
        page_sizes.append((cert_w, cert_h))

        _ensure_parent(output)
        _write_pdf(output, pages, page_sizes)
        return output.exists() and output.stat().st_size > 0
    except Exception as exc:  # pragma: no cover - defensive
        sys.stderr.write(f"stdlib render failed: {exc}\n")
        return False


def _stdlib_table(add, text: str) -> None:
    """Lay a Markdown table out as space-padded monospace columns (INV-142).

    The stdlib writer has no grid primitives, so this is the sanctioned lesser
    rendering: still rows and columns, in the monospace F3 face so they actually
    line up — and never the pipe source the parser was handed. A rule under the
    header keeps the header distinguishable, and a blank line after the block keeps
    two adjacent tables from reading as one.
    """
    header, rows = parse_table(text)
    if not header:
        return
    cols = [[_md_inline_to_text(c) for c in header]] + [
        [_md_inline_to_text(c) for c in r] for r in rows
    ]
    widths = [min(max(len(row[i]) for row in cols), 40) for i in range(len(header))]
    # This writer does not wrap, so a row wider than the text column would run off
    # the page — the off-page failure INV-121 names, reached from the other
    # renderer. Clip to what fits: 8.5pt Courier is 5.1pt per character across a
    # 487pt text column, minus the 6pt indent.
    budget = int((595.0 - 2 * 54.0 - 6) / (8.5 * 0.6))
    add("", "F1", 3, 0)
    for row_index, row in enumerate(cols):
        line = "  ".join(c[:w].ljust(w) for c, w in zip(row, widths)).rstrip()
        add(line[:budget], "F3", 8.5, 6)
        if row_index == 0:
            add("  ".join("-" * w for w in widths)[:budget], "F3", 8.5, 6)
    add("", "F1", 3, 0)


def _stdlib_subsection(add, add_wrapped, name: str, content: Optional[List[str]],
                       missing_blocks: Tuple[str, ...] = ()) -> None:
    add("", "F1", 4, 0)
    add(name, "F2", 12, 0)
    empty = content is None or not any(l.strip() for l in content)
    if empty and not missing_blocks:
        add_wrapped("(not recorded)", "F1", 10, 6)
        return
    unspaced_section = _normalize_heading(name) in _UNSPACED_SUBSECTIONS
    active_label = ""
    in_item = False
    cursor = 0
    while cursor < len(content or []):
        index, line = cursor, content[cursor]
        # A table becomes aligned monospace columns here — there are no grid
        # primitives in this writer — but never the raw pipe source (INV-142).
        run = _table_run(content, index)
        if run:
            _stdlib_table(add, "\n".join(content[index : index + run]))
            cursor += run
            in_item = False
            continue
        cursor += 1
        s = line.strip()
        # Tracked before the skips below so a blank line still closes an item.
        in_item = _still_in_list_item(line, in_item)
        if not s:
            add("", "F1", 4, 0)
            continue
        if _is_empty_takeaway(s):
            continue
        if s.startswith("<!--") and s.endswith("-->"):
            continue  # HTML comment (e.g. a maintainer note): never rendered
        label = _block_label(line)
        if label:
            active_label = label
        indent = 6.0
        m = re.match(r"^(\s*)([-*])\s+(.*)$", line)
        if m:
            s = "- " + _md_inline_to_text(m.group(3).strip())
            indent = 12.0 if len(m.group(1)) >= 4 else 6.0
        else:
            s = _md_inline_to_text(s)
        add_wrapped(s, "F1", 10.5, indent)
        # Mirror the fpdf2 path's inter-item gap so the two renderers do not drift.
        if in_item and not unspaced_section and active_label not in _UNSPACED_LABELS:
            if _next_nonblank_is_top_level_bullet(content, index):
                add("", "GAP", _ITEM_GAP_PT, 0)
    for block in missing_blocks:
        add_wrapped(f"{block}: (not recorded)", "F1", 10.5, 6.0)


def _wrap_to_width(text: str, max_w: float, measure) -> List[str]:
    """Greedy word wrap on measured width, where `measure(str)` returns a width.

    Used by the certificate, whose lines are centered: a character-count wrap
    (``_wrap``) cannot center honestly, because "Illinois" and "MMMMMMMM" are the same
    number of characters and nowhere near the same width. Both renderers pass their own
    `measure`, so neither wraps the certificate differently from the other (INV-066).
    """
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if measure(candidate) <= max_w:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrap(text: str, width: int) -> List[str]:
    text = text.rstrip()
    if not text:
        return [""]
    words = text.split(" ")
    out: List[str] = []
    cur = ""
    for w in words:
        if len(w) > width:
            if cur:
                out.append(cur)
                cur = ""
            for i in range(0, len(w), width):
                out.append(w[i : i + width])
            continue
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def _pdf_escape(s: str) -> str:
    """Escape a string for a PDF `()` literal. ⛔ **Sanitize with `_safe` first.**

    This does PDF *syntax* only: escape `\\`, `(`, `)`, and emit `\\ooo` octal for the
    Latin-1 high range. It performs no transliteration.

    ⚠️ **It used to, and that was an INV-143 violation.** It carried its own inline
    substitution table of 9 entries — a subset of `_UNICODE_MAP`'s 33 — with a `"?"`
    default. The fpdf2 renderer normalizes through `_safe` and never reaches here, but the
    stdlib writers called this on raw text, so **24 of the 33 mapped characters rendered as
    `?`**: `≥ ≤ ≈ ≠ € ™ ∞ ← ↔ ⇒ ↑ ↓ ✅ ✓ ⚠` and the deliberately-dropped emoji. Silently, at
    exit 0, with a green retention figure — because `?` is one character replacing one, so
    retention is structurally unable to see it. INV-143 exists to forbid precisely that:
    "MUST NOT substitute `?` for a character it cannot encode".

    Two tables, one authoritative and one not, is the defect. There is now one:
    `_UNICODE_MAP` via `_safe`. Do not reintroduce a table here — restoring parity by hand
    is what drifted the first time.

    A character that still arrives unencodable is **dropped and recorded**, so
    `dropped_character_warning()` reports it (INV-111). Dropping is what INV-143 permits;
    substituting is what it forbids.
    """
    out = []
    for ch in s:
        o = ord(ch)
        if ch in "\\()":
            out.append("\\" + ch)
        elif 32 <= o < 127:
            out.append(ch)
        elif 160 <= o <= 255:
            out.append("\\%03o" % o)
        else:
            # Unreachable for `_safe`-sanitized text, which is every shipped caller.
            # Reached only if a caller forgets — and then the loss must be legible on
            # stderr rather than a `?` on a Bootcamper's keepsake.
            _record_dropped_character(ch, s)
    return "".join(out)


def _write_pdf(output: Path, pages: List[str], page_sizes: List[Tuple[float, float]]) -> None:
    """Write a valid PDF. ``page_sizes[i]`` is the (width, height) of page ``i`` in
    points, so pages can mix orientations (e.g. a landscape certificate)."""
    objects: List[bytes] = []

    def add_obj(body: bytes) -> int:
        objects.append(body)
        return len(objects)  # 1-based object number

    # Reserve: 1=Catalog, 2=Pages, fonts, then per-page (content, page).
    font_regular = add_obj(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    font_bold = add_obj(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )
    # F3 is monospace, for the one thing a proportional font cannot do: hold a
    # space-padded table's columns in line. Both stdlib table fallbacks (this
    # generator's and the discoveries generator's, which imports this writer) use
    # it — space-padding Helvetica produces ragged pseudo-columns, which is not the
    # "aligned monospace columns" INV-142 permits as the lesser rendering.
    font_mono = add_obj(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"
    )

    page_obj_nums: List[int] = []
    # We need the Pages object number ahead of the page objects; compute it.
    pages_obj_num = len(objects) + 1  # next object we will create is Pages
    add_obj(b"__PAGES_PLACEHOLDER__")

    for i, stream in enumerate(pages):
        pw, ph = page_sizes[i]
        data = stream.encode("latin-1", "replace")
        content_num = add_obj(
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(data), data)
        )
        page_num = add_obj(
            (
                "<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                "/Resources << /Font << /F1 %d 0 R /F2 %d 0 R /F3 %d 0 R >> >> "
                "/Contents %d 0 R >>"
                % (pages_obj_num, pw, ph, font_regular, font_bold, font_mono,
                   content_num)
            ).encode("latin-1")
        )
        page_obj_nums.append(page_num)

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects[pages_obj_num - 1] = (
        "<< /Type /Pages /Count %d /Kids [%s] >>" % (len(page_obj_nums), kids)
    ).encode("latin-1")

    catalog_num = add_obj(
        ("<< /Type /Catalog /Pages %d 0 R >>" % pages_obj_num).encode("latin-1")
    )

    # Serialize with xref.
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0] * (len(objects) + 1)
    for i, body in enumerate(objects, start=1):
        offsets[i] = len(out)
        out += ("%d 0 obj\n" % i).encode("latin-1")
        out += body if isinstance(body, bytes) else body.encode("latin-1")
        out += b"\nendobj\n"
    xref_pos = len(out)
    n = len(objects) + 1
    out += ("xref\n0 %d\n" % n).encode("latin-1")
    out += b"0000000000 65535 f \n"
    for i in range(1, n):
        out += ("%010d 00000 n \n" % offsets[i]).encode("latin-1")
    out += (
        "trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (n, catalog_num, xref_pos)
    ).encode("latin-1")

    output.write_bytes(bytes(out))


# --------------------------------------------------------------------------- #
# Helpers + entry point
# --------------------------------------------------------------------------- #
def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preferences",
        default=str(DEFAULT_PREFERENCES),
        help=(
            "Bootcamp preferences YAML. Its top-level `name:` is the certificate name "
            "the Bootcamper was asked for (INV-113) and outranks the recap header."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify required sections exist; do not render.",
    )
    parser.add_argument(
        "--expect-modules",
        default="",
        help=(
            "Semicolon-separated module names that MUST each have a section; "
            "flags a wholly-missing module. Semicolon (not comma) because some "
            "names contain commas, e.g. 'Query, Visualize and Discover'."
        ),
    )
    parser.add_argument(
        "--progress",
        default=str(DEFAULT_PROGRESS),
        help=(
            "Progress JSON whose `modules_completed` supplies the EXPECTED set of "
            "visualizations. This is the tab-coverage denominator that does not come "
            "from the manifests, so a module that captured nothing is still visible."
        ),
    )
    parser.add_argument(
        "--expect-visualizations",
        default=None,
        help=(
            "Comma-separated visualization names to expect, overriding --progress. "
            "Mainly for tests and for a run whose progress file is unavailable."
        ),
    )
    args = parser.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        sys.stderr.write(f"Recap not found: {inp}\n")
        return 1

    try:
        source_text = inp.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # Exists but is not UTF-8 — an editor that saves cp1252/ANSI is the usual cause.
        # Refuse with a message the guide can relay rather than a traceback, and write no
        # PDF (INV-110). Do NOT re-read with errors="replace": the recap is the
        # bootcamper's document, and silently mangling their text is not ours to do.
        sys.stderr.write(
            f"Recap is not valid UTF-8: {inp} ({exc}). No PDF written. "
            f"Re-save it as UTF-8 and run this again.\n"
        )
        return 1
    recap = parse_recap(source_text)
    expected = [s for s in (t.strip() for t in args.expect_modules.split(";")) if s]
    audit = audit_recap(recap, source_text, expected or None)

    # Resolve the recap's images against the recap's own directory, not the process
    # working directory — the paths are document-relative (graduation Step 1a).
    set_image_context(inp)
    referenced_images = recap_image_targets(source_text)

    if args.check:
        problems = audit.fatal + audit.warnings
        # An `![](...)` target that resolves to no file would be dropped from the
        # PDF; report it here, where it can still be fixed.
        problems = problems + [
            f"embedded image not found: {target} (relative to {inp.parent})"
            for target in unresolvable_image_targets(source_text)
        ]
        # A captured tab that never reached the recap is invisible to every check
        # above, because they all measure the recap against itself.
        manifests = find_tab_manifests()
        problems = problems + tab_coverage_problems(source_text, manifests)
        # …and whether the manifest those checks trust is itself complete.
        problems = problems + manifest_undercount_problems(manifests)
        if problems:
            for p in problems:
                sys.stderr.write(f"INCOMPLETE: {p}\n")
            sys.stderr.write(f"({audit.retention_note()})\n")
            return 1
        if not manifests:
            # A check that could not run is reported as skipped, never folded into a
            # pass (INV-163). Without a manifest there is no external denominator, so
            # "every captured tab reached the recap" is unverified, not true.
            sys.stderr.write(
                "SKIPPED: tab-coverage check — no capture manifest (<name>-tabs.json) "
                "was found beside the recap's images, so how many tabs were captured "
                "is unknown. The embedded-image count cannot answer this: its "
                "denominator comes from this same recap.\n"
            )
        # …and whether a visualization that SHOULD have a manifest has none. This branch
        # is the one the no-manifest branch above cannot reach: with some manifest
        # present it never fires, so a wholly uncaptured module passed silently.
        if args.expect_visualizations is not None:
            expected = [
                name.strip()
                for name in args.expect_visualizations.split(",")
                if name.strip()
            ]
        else:
            expected = expected_visualizations(read_completed_modules(Path(args.progress)))
        missing = missing_visualization_reports(expected, manifests)
        for report in missing:
            sys.stderr.write(f"SKIPPED: {report}\n")
        # ⛔ The coverage figure is WITHHELD while an expected visualization is
        # unaccounted for. Printing "6 of 6 captured tabs reached the recap" beside a
        # missing-manifest notice is exactly the reading that made the 2026-08-25 run
        # look clean: the sentence is true of the manifests that exist and false of the
        # bootcamp (INV-163, INV-193, INV-265).
        print(
            "Recap complete: all module sections carry the required subsections, "
            "and every End-of-Module Summary carries its labeled blocks."
            + (f" Tab coverage: {tab_coverage_note(source_text, manifests)}."
               if manifests and not missing else "")
            + (f" Tab coverage NOT reported: {len(missing)} expected visualization(s) "
               f"have no manifest (see SKIPPED above)." if missing else "")
        )
        return 0

    out = Path(args.output)

    # Audit BEFORE rendering. A structurally wrong input must never reach the
    # "PDF generated:" line, which is the graduation skill's success signal — a
    # valid-looking PDF with none of the content is the failure nobody checks.
    if audit.fatal:
        sys.stderr.write(f"ERROR: refusing to render {inp}\n")
        for problem in audit.fatal:
            sys.stderr.write(f"  - {problem}\n")
        sys.stderr.write(f"  ({audit.retention_note()})\n")
        sys.stderr.write(
            "This generator renders the bootcamp recap structure only "
            "('## <Module name>' sections whose body sits under '### " +
            REQUIRED_SECTIONS[0] + "' and its siblings); it is not a "
            "general-purpose Markdown renderer. No PDF was written.\n"
        )
        return 1

    # The certificate name the Bootcamper was asked for lives in preferences (INV-113);
    # the recap header carries whatever was auto-detected at the start of the run. Prefer
    # the answer, and say so when the two disagree — a silent divergence is what printed a
    # rejected handle on a signed certificate (INV-111).
    preferred_name = read_preferences_name(Path(args.preferences))
    set_certificate_name_override(preferred_name)
    header_name = recap_certificate_name(recap)
    if preferred_name and header_name and preferred_name != header_name:
        sys.stderr.write(
            f'NOTE: certificate name "{preferred_name}" from {args.preferences} '
            f'differs from "{header_name}" in {inp}; printing the preferences value '
            f'(it is the answer to the certificate-name question). Update the recap\'s '
            f'"**Bootcamper:**" line so both agree.\n'
        )

    # Input-quality warning, emitted once (the fpdf2 renderer itself runs two
    # passes). Never fatal: graduation is non-blocking and a certificate with a
    # placeholder name still beats no PDF — but it must not be silent.
    if recap_missing_certificate_name(recap):
        sys.stderr.write(
            f'WARNING: no bootcamper name found in {inp} or {args.preferences}; the '
            f'Certificate of Completion will read "{CERTIFICATE_NAME_PLACEHOLDER}". Add a '
            f'"**Bootcamper:** <name>" line to the recap preamble to fix it.\n'
        )
    else:
        # A recorded-but-unprintable name is the same defect with a worse failure mode: it
        # looks recorded, so nothing upstream asks about it (INV-113/INV-143).
        unprintable, lost = recap_certificate_name_unprintable(recap)
        if unprintable:
            printable = _safe(unprintable).strip()
            shown = printable or CERTIFICATE_NAME_PLACEHOLDER
            sys.stderr.write(
                f'WARNING: the bootcamper name "{unprintable}" in {inp} contains '
                f'{len(lost)} character(s) the recap PDF\'s built-in fonts cannot render '
                f'({" ".join(lost)}); the Certificate of Completion will read "{shown}". '
                f'Ask the bootcamper for the name to print (INV-113) and record it as '
                f'"**Bootcamper:** <name>".\n'
            )

    used = "fpdf2"
    ok = render_with_fpdf2(recap, out)
    if not ok:
        used = "stdlib"
        ok = render_with_stdlib(recap, out)

    if ok:
        # Characters the built-in fonts could not render were dropped from the page during
        # the render above. Reported here, once, for the whole run — after both fpdf2
        # passes (and any stdlib fallback) have been through the content, so nothing is
        # missed and nothing is counted twice. The certificate-name warning above covers
        # one field; this covers the body, which is where the loss was silent.
        dropped = dropped_character_warning()
        if dropped:
            sys.stderr.write(dropped)
        # Recognizable but imperfect: warn and still ship the PDF (never blocks;
        # graduation is non-blocking). Distinct from the fatal class above.
        if audit.warnings:
            sys.stderr.write(
                "WARNING: recap PDF generated but some sections are incomplete:\n"
            )
            for problem in audit.warnings:
                sys.stderr.write(f"  - {problem}\n")
        # Report retention on success too, so partial truncation is visible
        # without extracting the PDF's text — and the embedded-image count
        # alongside it, which retention structurally cannot see (INV-110).
        note = audit.retention_note()
        if referenced_images:
            note = f"{note}, {image_embed_note(len(referenced_images))}"
            if used == "stdlib":
                # The stdlib renderer embeds no images at all; say so rather than
                # letting "embedded 0 of 6" read as a lookup failure.
                note = f"{note} (the stdlib renderer embeds no images)"
        # Stated separately from the embedded count, and worded differently, because
        # conflating the two is the defect: the embedded count's denominator comes from
        # this recap, and this one's comes from capture's manifest.
        coverage = tab_coverage_note(source_text, find_tab_manifests())
        if coverage:
            note = f"{note}, {coverage}"
        print(f"PDF generated: {out} (renderer: {used}, {note})")
        return 0

    sys.stderr.write("Failed to generate a PDF by any strategy.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
