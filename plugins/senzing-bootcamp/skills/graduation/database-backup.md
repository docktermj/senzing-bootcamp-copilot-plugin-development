# Database backup procedure (shared by two callers)

⛔ **This file is the ONE implementation of "back up the resolved repository". Two callers cite it;
neither reimplements it.**

- `SKILL.md` Step 6a, writing the INV-094 revisit bundle at graduation.
- `../bootcamp-onboarding/packaging.md`, when the `transfer` profile is asked for and
  `backups/revisit/` does not exist yet — the flow runs at any point in the bootcamp, so it can be
  reached before graduation has ever run.

⚠️ **Why it was factored out rather than copied.** The indeterminate-`database_type` branch below is
subtle, and getting it wrong means either no backup at all or `pg_dump` aimed at a SQLite file. A
second copy is precisely the drift this repo writes tests to prevent, and the backup is the whole
point of the bundle: INV-094 requires exactly one of the two branches to have run.

## The procedure

Back up the resolved repository so it can be restored later. Read **`database_type`**
(`sqlite`/`postgresql`) from pre-checks and the connection from `config/engine_config.json`.

⛔ **When `database_type` is indeterminate, do not guess a branch** — determine the engine from
`config/engine_config.json`'s connection string instead (and note the missing key per pre-check 3).
Picking the wrong branch here means either no backup or `pg_dump` against a SQLite file.

- **SQLite:** copy the repository file into `backups/revisit/database/` (e.g.
  `cp database/G2C.db backups/revisit/database/G2C.db`).
- **PostgreSQL:** run `pg_dump` of the Senzing database to
  `backups/revisit/database/senzing.dump`, writing the file with `-f`:
  `pg_dump -U <user> -d <db> -Fc -f backups/revisit/database/senzing.dump`.
  When the database runs in a Docker container, dump inside the container and copy the file out,
  because `-f` there writes into the container's filesystem:
  1. `docker exec <container> pg_dump -U <user> -d <db> -Fc -f /tmp/senzing.dump`
  2. `docker cp <container>:/tmp/senzing.dump backups/revisit/database/senzing.dump`
  3. `docker exec <container> rm /tmp/senzing.dump`

  Confirm the exact user / database / container from `config/engine_config.json` (and the recorded
  container, when container-lifecycle tracking is present); **never invent credentials.**
  ⛔ **(INV-166, INV-001) Never write the dump with a `>` redirection**, in any shell: under
  Windows PowerShell 5.1 `>` re-encodes the binary dump as text, and the damage stays silent until
  a restore. The backup
  exists only once `backups/revisit/database/senzing.dump` is on the host and non-empty; a failed
  `docker cp`, or a missing or empty file, means the backup could not be produced (below).

**If the backup cannot be produced** (tool missing, database unreachable), warn and continue — the
rest of the bundle still saves, and graduation is non-blocking (INV-048). The packaging flow reports
the same way: it says the archive carries no database and why, rather than refusing to package.

## Restore

Record the exact **restore** command wherever this backup is described — `SKILL.md` Step 6c's return
guide (`docs/REVISIT_BOOTCAMP.md`), which a `transfer` archive carries, and its `OPEN_ME_FIRST.md`
points at, only when the guide was packaged; a backup packaged without it gets the step below
in `OPEN_ME_FIRST.md` itself:

- **SQLite** — copy the file back to `database/`.
- **PostgreSQL** — into a fresh database, with the file named by an argument, never a `<`
  redirection (Windows PowerShell 5.1 rejects `<`): `pg_restore -U <user> -d <db> <file>` for this
  custom-format dump, or `psql -U <user> -d <db> -f <file>` for a plain dump. When the database runs
  in a Docker container, copy the file in first and restore it from the path inside the container:
  `docker cp <file> <container>:/tmp/senzing.dump`, then
  `docker exec <container> pg_restore -U <user> -d <db> /tmp/senzing.dump` (or
  `docker exec <container> psql -U <user> -d <db> -f /tmp/senzing.dump` for a plain dump).

These commands are written for every shell but are unverified on Windows: no test runs them there.
