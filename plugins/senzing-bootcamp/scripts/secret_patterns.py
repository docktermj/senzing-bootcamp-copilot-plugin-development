"""The one definition of what counts as a secret in a file the plugin handles (INV-109).

`write-gate.py` blocks a *write* whose content matches these; `package_bootcamp.py` excludes a
*member* whose content matches them. Two consumers, one rule -- so a pattern added for one is
available to the other, and neither can quietly protect less than the other.

⚠️ **`write-gate.py` keeps its own inline copy on purpose, and a test pins the two equal.** It is a
`preToolUse` security control: an ImportError there does not degrade to "no secret scan", it
degrades to a hook that cannot run at all, on every write in the bootcamp. The plugin already has
this exact shape for `brand_tokens.py`, whose palette is inlined into two generators with
`tests/test_brand_sync.py` asserting the copies stay equal; `tests/test_secret_patterns_are_shared.py`
does the same job here. Import this module from anything that is *not* the write gate.

The three patterns, and why each is written the way it is:

- **PEM private keys** -- the armor line, with the optional algorithm word, so `BEGIN PRIVATE KEY`
  and `BEGIN RSA PRIVATE KEY` both match.
- **AWS access-key IDs** -- `AKIA` plus exactly 16 uppercase-alphanumeric characters.
- **Senzing license payloads** -- the documented `AQAAAD` prefix plus at least 16 base64
  characters. ⛔ The long tail is load-bearing: without it the pattern fires on prose that merely
  mentions `AQAAAD` and on `.lic` file *paths*, which would make the gate block documentation about
  licenses and the packager exclude the guidance describing them.

Stdlib only.
"""
import re

#: Source of truth. Kept as one alternation string so a consumer can compile it with its own flags
#: and so the equality test against `write-gate.py` compares one value rather than a list order.
SECRET_PATTERN = (
    r"BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"
    r"|AKIA[0-9A-Z]{16}"
    r"|AQAAAD[A-Za-z0-9+/=]{16,}"
)

#: Human-readable names, in the same order as the alternation, for manifests and messages. A
#: reader told only "excluded: matched a secret pattern" cannot tell a key from a license blob.
SECRET_PATTERN_NAMES = (
    "PEM private key",
    "AWS access-key ID",
    "Senzing license payload",
)

_COMPILED = re.compile(SECRET_PATTERN)


def find_secret(text):
    """The name of the first secret class `text` matches, or None.

    Returns the *class* rather than the matched bytes on purpose: the caller reports this into a
    manifest that the Bootcamper may hand to someone else, and echoing the matched secret there
    would defeat the exclusion that produced the message.
    """
    match = _COMPILED.search(text)
    if not match:
        return None
    matched = match.group(0)
    if matched.startswith("AKIA"):
        return SECRET_PATTERN_NAMES[1]
    if matched.startswith("AQAAAD"):
        return SECRET_PATTERN_NAMES[2]
    return SECRET_PATTERN_NAMES[0]
