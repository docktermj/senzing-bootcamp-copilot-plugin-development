from __future__ import annotations

import re
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[3] / "site/index.html"


class CopyButtonTests(unittest.TestCase):
    def test_cli_command_boxes_have_copy_buttons_except_output(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        start = html.index('<article class="card" id="cli">')
        card = html[start:html.index("</article>", start)]
        boxes = re.findall(
            r'<div class="cmd">\s*<p class="cmd__label">([^<]*)</p>(.*?)</pre>',
            card, flags=re.S)
        self.assertGreaterEqual(len(boxes), 2)
        for label, body in boxes:
            has_button = 'class="cmd__copy"' in body
            self.assertEqual(has_button, label != "Output", label)


if __name__ == "__main__":
    unittest.main()
