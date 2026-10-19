# Bootcamp Packaging Workflow (available at any time)

The bootcamper can package their bootcamp at any point: onboarding, any module, or after
graduation (the INV-254 any-time-flow precedent this follows). The result is **one zip
archive under `backups/packages/`** that they can archive, move to another machine, or
hand to a colleague.

⛔ **The plugin writes the archive and stops.** It never uploads, emails, attaches or opens
an issue with it (INV-135) — the same rule the feedback flow follows. Moving the file off
the machine is the bootcamper's action, and the closing summary names the path so they can.

⚠️ **This is not the revisit bundle, and it does not replace it.** Graduation Step 6 writes
`backups/revisit/` **in place** (INV-094), which is a save point on *this* machine. This
flow makes that portable, and reuses it rather than duplicating it.

Reached by the `the package-bootcamp skill` command. ⚠️ **There is no hook for this flow** — unlike
`notes.md`, whose `userPromptSubmitted` clause is real, nothing intercepts prompts on packaging
vocabulary. So **recognize these as a request for it and offer the command**: "back up the
bootcamp", "archive this", "move this to another machine", "zip it up", "send this to my
colleague". Recognizing them is the guide's job, not a hook's. Follow `ground-rules.md`: one 👉
question per yielding turn (INV-251), and the turn ends on it.

## Step 1: Get the real size before asking anything

⛔ **Run the dry run first. The question below quotes a measured size, never an estimate.**

```bash
python3 "${PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile share --dry-run
python3 "${PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile transfer --dry-run
```

(Skill-relative fallback `../../scripts/package_bootcamp.py` per INV-252, exactly as every
other bundled script is invoked — INV-185.)

Each prints the manifest on stdout and a `size:` line on stderr, and **writes nothing**.
Read the two `size:` figures; they are what the question needs. If either run exits
non-zero saying nothing is packageable yet, say so plainly — the bootcamp has not produced
artifacts yet — and do not ask the question.

⚠️ **If a dry run reports a size above 2 GB it prints a warning naming that.** Relay it:
recommend option 1, or note that the database backup is what makes option 2 large.

## Step 2: Ask what should travel

Pin this verbatim (INV-051/INV-056), substituting the two measured sizes, and end the turn
on it:

👉 **What should the package contain? Reply with a number:**

1. **Results to share** — your recap PDF, keepsake documents, visualizations and
   `production/` project (~<n> MB). No database, no source data, no credentials.
2. **Everything to continue elsewhere** — the above plus your database backup, config
   and mappings, so you can pick the bootcamp back up on another machine (~<n> MB).
3. **Cancel.**

*(Internal: end the turn on this question and wait.)*

⛔ **Option 3 writes nothing at all.** Acknowledge and return the bootcamper to exactly
where they left off.

## Step 3: For option 2, make sure a database backup exists

⛔ **(INV-094, INV-048) If `backups/revisit/` does not exist, run the shared procedure — do NOT
write a second SQLite-vs-PostgreSQL branch.** Follow `../graduation/database-backup.md`, the one
implementation, into `backups/revisit/database/`. That file carries the `database_type`
lookup, the do-not-guess rule for an indeterminate value, both engine branches and the
warn-and-continue rule.

**If the backup cannot be produced**, warn and continue: package what exists and say in
the closing summary that the archive carries no database and why. Never refuse to package
over it.

## Step 4: Write it

```bash
python3 "${PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile <share|transfer>
```

The script does the rest, and its guarantees are worth knowing because they are what make
the archive safe to hand over:

- **One top-level directory**, so extraction never scatters files into the recipient's
  working directory.
- **`OPEN_ME_FIRST.md`** at its root — what this is, the bootcamper's business problem in one
  line, what is included, what is excluded **and why**. It says to open the recap PDF first and
  (transfer only) points at `docs/REVISIT_BOOTCAMP.md` for the restore commands **only when the
  manifest's `included` list carries that file**; otherwise it says plainly which part is
  missing and what to do instead.
- **`PACKAGE_MANIFEST.json`** — profile, plugin version, date, `modules_completed`, every
  included path with SHA-256 and size, the exclusion rules applied, and every path skipped.
  ⚠️ A recipient must be able to tell what is **missing** without guessing; that is what
  the exclusion half is for.
- **Never packaged, either profile:** `.env`, `licenses/`, `config/license.json`,
  `data/raw/` (the bootcamper's own source data), `data/temp/`, `logs/`, `.git/`, caches
  and virtualenvs, and `backups/packages/` itself.
- **Content-scanned, every member, regardless of extension:** a member whose bytes match an
  INV-109 secret pattern — a PEM private key, an AWS access-key ID, a Senzing license payload —
  is excluded and **named** in the manifest. ⛔ **There is no file-type allowlist**, and there was
  one until 2026-08-26: it carried `.md`/`.py`/`.json` and not `.pem`, `.key` or the empty
  extension, so a `server.pem` and an extensionless `id_rsa` were packaged while the same key in
  a `.py` was excluded. A member that cannot be **read** is also excluded and named — nothing
  unexamined is packaged.
- **Symlinks resolved, then compared:** a member resolving outside the project root is
  skipped and named (the INV-200 rule).
- **Verified before it is announced:** `testzip()` re-opens the finished archive and a
  `.sha256` sidecar is written before the success line prints. Never tell the bootcamper an
  archive exists without that (INV-067's discipline) — they may not discover otherwise
  until they are on the machine that no longer has the original.

## Step 5: Tell them where it is

Report the path, the size and the digest from the script's own output — not from memory —
and say plainly that they move it themselves. If anything was excluded that they might
expect (a database on the `share` profile, a file the secret scan caught), name it here
rather than leaving it to the manifest alone.

Then return the bootcamper to exactly where they left off.
