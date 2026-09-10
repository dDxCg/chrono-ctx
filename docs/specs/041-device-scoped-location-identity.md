# 041 — device-scoped location identity

## Context

From [enterprise-central-server-plan.md](../agents/draft/enterprise-central-server-plan.md)
Part 1(1) and Part 6 phase 1, decided 2026-09-10: do the identity
refactor now, as a real PK change, rather than deferring it to whenever
a central Postgres exists — designing it twice costs more than doing it
once, even paid slightly early.

`locations` identifies a tracked file by `(st_ino, st_dev)` — a
filesystem inode pair, meaningful only on the filesystem that issued it.
Every lookup today (`_check_existed_location`, `_get_context_id_by_location`,
`_sync_location`, `sync_source_status`) assumes exactly one filesystem's
worth of inodes ever lands in this table. That is true of every
deployment today (one SQLite file per single-machine install) but stops
being true the moment rows from more than one device can reach the same
store — Option A's thin client (draft §4), or any future centralized
identity table. Two devices can and will reuse the same inode number for
unrelated files.

## Scope

**In**
- `locations.device_id`: a new column, part of the primary key —
  `PRIMARY KEY (device_id, st_ino, st_dev)`.
- `utils/helper.get_device_id()`: a stable per-installation identity —
  a UUID generated once, persisted at `anchored("data/device_id")`, read
  back on every later call (this process and every future one against
  the same `PROJECT_ROOT`). No server round-trip — phase 3 (remote MCP)
  can later have the server *adopt* a device's locally-generated id;
  minting it server-side is a phase-3-or-later concern, not this one.
- Migration for existing installs: SQLite can't `ALTER TABLE` a primary
  key in place, and `CREATE TABLE IF NOT EXISTS` is a silent no-op
  against a table that already exists in the old shape. `init_db()`
  detects the pre-041 `locations` shape (`PRAGMA table_info` missing
  `device_id`) and drops the table before `schema.sql` recreates it in
  the new shape.
- Every `locations` lookup/write in `versioning.py` gains `device_id` in
  its `WHERE`/`INSERT`, scoped to `get_device_id()`.

**Out**
- `contexts`/`versions` tables — unaffected, no `st_ino`/`st_dev`
  coupling to begin with.
- Server-issued device identity, or any multi-device *merge* of
  `locations` rows into one store — that's what this refactor makes
  possible later (phase 2/3), not something this spec does.
- Cross-device rename/move detection (a file physically copied from one
  machine to another). `st_ino`/`st_dev` was never able to detect that
  even on one device across a *copy* (only a *move*); this spec doesn't
  change what identity signal exists, only scopes it correctly to the
  device that produced it.
- Backfilling old `locations` rows into the new shape. See "existing-row
  impact" below — the table is deliberately rebuilt empty, not migrated
  row-by-row.

## Existing-row impact (AGENTS.md §4)

`locations` is re-derivable bookkeeping, not user content: it maps an
inode to a `context_id` so a later filesystem event can find "this file
already has history." The actual history lives in the git mirror,
keyed by *path*, independent of this table (`resolve_mirror_location()`
never consults `locations`/`context_id`). Rebuilding `locations` empty
on upgrade means: the next event for an already-tracked file finds no
existing `context_id`, re-enters through `created_handle`'s "first time
seeing this location" path, and gets a *new* `context_id` — but writes
into the *same* git mirror path it always did, so its commit history is
unaffected and continuous. The only real-world symptom is one
`contexts` row becoming orphaned (unreferenced by any current
`locations` row) per previously-tracked file — cosmetic, not a
correctness or data-loss issue.

## Acceptance criteria

- AC-1. A fresh (never-initialized) database: `schema.sql` creates
  `locations` with a `device_id` column and
  `PRIMARY KEY (device_id, st_ino, st_dev)`.
- AC-2. `get_device_id()` returns the same value across repeated calls
  in one process, and across a fresh process reading the same
  `data/device_id` file (persistence survives restart).
- AC-3. `init_db()` against a database whose `locations` table is in
  the pre-041 shape (no `device_id` column) does not raise; afterward,
  `PRAGMA table_info(locations)` shows the new shape.
- AC-4. After that migration, `contexts` and `versions` are unaffected
  (any pre-existing rows in them survive) — only `locations` is rebuilt.
- AC-5. Two `_append_context` calls for the *same* `(st_ino, st_dev)`
  but under two different `device_id`s (simulated via monkeypatching
  `get_device_id`) are treated as two distinct, unrelated locations —
  each gets its own row, neither lookup finds the other's.

## Error cases

- EC-1. `init_db()` against a fresh database (no `locations` table at
  all yet): the migration check is a no-op — `PRAGMA table_info` on a
  nonexistent table returns no rows, which must not be misread as "old
  shape, needs migration."

## Contracts

```python
# utils/helper.py
def get_device_id() -> str:
    """Stable per-installation device identity (spec 041). Generated
    once, persisted at anchored("data/device_id"); cached in-process
    after the first call."""

# vcs/services/db.py
def init_db(db_handler: DBHandler) -> None:
    """Unchanged signature. Now migrates a pre-041 `locations` table
    (drop + let schema.sql recreate) before applying schema.sql."""
```

## Non-goals / open questions

- Whether `device_id` should ever be exposed to the user (e.g. `ctx
  device show`). Not needed until Option A's thin client makes "which
  of my devices wrote this" a question a person actually asks.
- Whether `pending_actor_hints` needs the same treatment. No —
  it's keyed by `location` (a path string), which is already
  device-ambiguous the same way `locations.location` is, but its 5s TTL
  makes any confusion window self-healing on its own; not touched here.
