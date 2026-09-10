# 040 — `Ctx-Actor` commit trailer on mirror-repo commits

## Context

From [enterprise-central-server-plan.md](../agents/draft/enterprise-central-server-plan.md)
§7.5 (the provenance receipt): git records who committed, what changed
and when, but nothing standardized answers "which agent/actor, in a
form a downstream tool can parse without regexing a free-text sentence."
Every mirror-repo commit already carries an actor in its *author* field
(`{name} <{name}@chrono-ctx.local>`, spec 007) and restates it in the
commit *message* as free text (`"modified docs/x.md via agent:<id>"`,
`versioning.py`) — but nothing marks that value as a structured,
machine-readable field the way `Signed-off-by:` does for DCO tooling.

This is the safe first slice of §7.5: a `Ctx-Actor:` trailer, built
from data every commit-producing call site in `versioning.py` already
has (`event.actor` via `_resolve_actor()`, or the fixed
`STARTUP_RECONCILE_ACTOR_LABEL` for the offline-reconcile path). No
schema change, no new plumbing, no dependency.

**Explicitly deferred**, and why: the draft's fuller trailer
(`Ctx-Model`, `Ctx-Session`, `Ctx-Tool`, `Ctx-Scope`, `Ctx-Trace`) needs
per-call MCP metadata to reach the watcher's async commit, which today
only has a path to travel through the 5s-TTL `pending_actor_hints`
table (spec 013) carrying a bare actor string. Part 1(5) of the draft
already marks that table as disappearing once phase 2 (per-caller
identity, authenticated at the API boundary) ships — building a second,
richer shuttle for it now would be thrown away by that same phase.
`Ctx-Trace` in particular needs the *watcher's* commit to correlate with
the *MCP call's* span, which are different processes on different
timelines; that correlation mechanism is its own design question, not
a free extension of this spec.

## Scope

**In**
- `vcs/services/versioning.py`: every call site that builds a git commit
  `message=` string gains a `Ctx-Actor: <actor>` trailer, appended after
  a blank line (git trailer convention) so the existing one-line summary
  stays the commit *subject* (`%s`) unchanged.
- Applies uniformly: `created_handle`/`_append_context`, `modified_handle`,
  `moved_handle` (all branches: same-repo move, cross-repo write+remove,
  out-of-scope remove), `deleted_handle`, `reconcile_dropped_sources`.

**Out**
- `Ctx-Model`/`Ctx-Session`/`Ctx-Tool`/`Ctx-Scope`/`Ctx-Trace` — see
  Context above.
- Any change to `git_store.py`. It already accepts an arbitrary
  `message` string from its callers; this spec only changes what
  `versioning.py` passes in.
- Any change to the commit *author* field (spec 007, unaffected).
- `audit.py`/CLI history output parsing the trailer back out — read-side
  consumption is a separate, later spec once there's a reason to parse
  it (e.g. an admin UI, or export).

## Acceptance criteria

- AC-1. A commit produced by `created_handle` has a message whose
  subject (`git log --format=%s`) is unchanged from today
  (`"created {relpath} via {actor_label}"`), and whose full message
  (`git log --format=%B`) also contains a line
  `Ctx-Actor: {actor_label}`.
- AC-2. Same for `modified_handle`.
- AC-3. Same for `moved_handle`'s same-repo branch (`git_store.move`).
- AC-4. Same for `moved_handle`'s cross-repo branch — both the
  destination-repo write commit and the source-repo remove commit each
  carry their own `Ctx-Actor:` trailer with the same actor.
- AC-5. Same for `moved_handle`'s out-of-scope branch (single remove
  commit).
- AC-6. Same for `deleted_handle`.
- AC-7. Same for `reconcile_dropped_sources`, with
  `Ctx-Actor: startup:reconcile`.

## Error cases

- EC-1. `event.actor` is `None` (no MCP hint, no CLI actor — the
  existing `"unknown:filesystem"` fallback path, spec 007): the trailer
  is still written, as `Ctx-Actor: unknown:filesystem` — never omitted,
  since a missing trailer would be indistinguishable from "trailer
  support doesn't exist yet" rather than "no actor was known."

## Contracts

```python
# vcs/services/versioning.py
def _with_actor_trailer(summary: str, actor_label: str) -> str:
    """summary\n\nCtx-Actor: {actor_label} - git's blank-line-separated
    trailer convention, so `%s` (subject) is unchanged and `%B` (full
    message) carries the structured field."""
```

Example resulting message body:

```
modified docs/onboarding.md via agent:3975b915-ad09-4949-a4e7-0d3c631e90d8

Ctx-Actor: agent:3975b915-ad09-4949-a4e7-0d3c631e90d8
```

## Non-goals / open questions

- Whether to also stop repeating the actor inside the free-text summary
  now that it's in the trailer. Left as-is: the summary line is what
  `git log --oneline`/existing tooling already reads, and shortening it
  is an unrelated readability change, not part of this spec's behavior.
- `Ctx-Trace` correlation mechanism (watcher-side commit ↔ MCP-side
  span) is real follow-up work, tracked in the draft's Part 6 staging
  rather than spec'd here.
