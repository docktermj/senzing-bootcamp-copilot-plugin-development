#!/usr/bin/env python3
"""Render any bootcamp Markdown document as a PDF in the house style.

This is a thin alias for ``generate_discoveries_pdf.py``, which despite its name is a
**general** styled-Markdown renderer: its layout engine — cover page, section styling,
tables, typography — contains nothing specific to the discoveries document. Only its
default `--require-sections` list is discoveries-shaped, and that is now a parameter.

It exists for findability. Someone looking for "how do I render a document in the house
style" will not guess `generate_discoveries_pdf.py`, and for a while that meant an
otherwise generic renderer was usable for exactly one file. The script was **not** renamed
because its name is referenced from the module-07 skill, the specs and the tests, and a
rename would break every one of those addresses for a cosmetic gain.

Usage — identical to the script it wraps::

    python3 "${PLUGIN_ROOT}/scripts/generate_document_pdf.py" \
        --input docs/business_problem.md \
        --output docs/business_problem.pdf \
        --require-sections "the problem;why it matters;success criteria" \
        --subtitle "The problem this bootcamp set out to solve"

⛔ **Pass `--subtitle`.** The cover subtitle otherwise defaults to the discoveries line,
"What Senzing found in your data", which is wrong on any other document's cover.

⛔ **Pass `--require-sections` naming that document's own H2 headings.** Omitting it
applies the *discoveries* defaults and the document will be refused. `--no-section-check`
skips the check entirely; prefer naming the sections, because the check is what catches a
document that silently lost its structure.

⚠️ The section list is not what stops this rendering unrelated Markdown — the content
retention floor is, and neither flag relaxes it (INV-110).

Success signal, exit codes, defaults, renderer tiering (fpdf2 then stdlib) and character
handling are whatever `generate_discoveries_pdf.py` does. The one thing this file supplies is
its own `--help` description, the first line of this docstring, passed to the wrapped `main`.
It parses no arguments and renders nothing itself, so the two can never drift.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from generate_discoveries_pdf import main  # noqa: E402
except ImportError as exc:  # pragma: no cover - a broken install, not a data case
    sys.stderr.write(
        "Cannot import generate_discoveries_pdf.py (expected next to this script): "
        f"{exc}\n"
    )
    raise SystemExit(2)

if __name__ == "__main__":
    raise SystemExit(main(description=__doc__.splitlines()[0]))
