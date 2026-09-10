# Draft — central server, thin clients (enterprise)

Status: **exploratory**. No spec cut from this yet. Target shape, in the
user's words: *host one shared MCP server, employee machines call into it
as clients, no `git` on the client*. Agent-side edits arrive over MCP;
the human-side versioning contract is **undecided** — options and a
recommendation in Part 4.

## Part 0 — the one decision everything else hangs off

> **Where does the source of truth for a context source live: the
> employee's disk, or the server?**

Every other question here is downstream of that one, and answering it
late is what makes this kind of migration expensive. Three combinations
exist; only two are coherent.

| Truth lives on | Agent writes via central MCP | Human edits | Verdict |
| --- | --- | --- | --- |
| **Server** | writes the central store directly | through a client that reads/writes the central store | Coherent. One store, one committer, no sync. |
| **Client disk** | must be pushed *down* to the laptop | local, watched locally | Coherent only with bidirectional sync + conflict resolution. Hardest thing in this document. |
| Both, unsynchronized | — | — | Incoherent. Two writers, no merge, silent divergence. |

Today's design is squarely "client disk", because the MCP server does
plain filesystem I/O on the same box as the watcher. Centralizing the
MCP server without moving the truth is the incoherent third row unless
sync is built. **Recommendation: move the truth to the server.** It is
more work up front and considerably less work forever after — it also
makes "no `git` on the client" fall out for free rather than being
engineered.

## Part 1 — what actually breaks when the server moves

Not a rewrite, but not a deployment change either. Each of these is
single-machine by construction today:

1. **File identity is an inode.** `locations (st_ino, st_dev PK, …)` —
   spec 003/006. Inode numbers are meaningful only on the filesystem
   that issued them. Across 200 laptops they collide freely and mean
   nothing. This is the deepest change in the list: identity has to
   become server-issued (`context_id` as the real PK) with
   `(tenant, device, logical_path)` as the lookup key, and `st_ino/st_dev`
   demoted to a *client-local* hint used only by a sync agent to detect
   local renames.
2. **The MCP server writes the local filesystem.** `write_file` is
   `open()` + write. Centrally, it has to write the server's content
   store instead — MCP becomes a content API over logical paths, not a
   filesystem proxy. Tool signatures survive; their implementation does
   not.
3. **Versioning is triggered by a local watchdog.** No local observer,
   no events, no versions. Whatever replaces it (Part 4) is the human
   path's entire design.
4. **Scope lives in a per-machine `config.yaml`.** Enterprise policy has
   to be central and per-tenant, and the MCP elicitation flow (spec
   013/§6.3) currently *persists an approval into that local file*. A
   remote server persisting scope means one user's approval widens scope
   for whoever shares that tenant — a real authorization decision, not a
   port of existing behavior.
5. **Actor attribution is a 5s-TTL hint in a shared SQLite file.** It
   works because the MCP server and the daemon share one disk and one
   clock. Neither holds across a network. Centrally this gets *easier*,
   not harder: the writer is authenticated at the API boundary, so the
   actor is known at write time and the hint table disappears for the
   MCP path (it stays only if a client-side watcher path survives).
6. **Auth is one shared `X-API-Key`, no caller identity** (spec 018, and
   already flagged as a known gap in ARCHITECTURE §8). Attribution that
   an auditor can trust needs per-user identity — SSO/OIDC for humans,
   service tokens for agents.
7. **SQLite + local git subprocess.** Fine for one machine, questionable
   for N concurrent tenants. The existing 30s lock/4s git bounds (specs
   036-038) were sized for a single-user box; they need re-deriving
   against real concurrency, and SQLite likely needs to become Postgres
   for identity/scope while git stays the content store.

What *doesn't* break, and is worth saying explicitly: the git mirror
model, `audit.py`, the diff/history read surface, the versioning gate,
and rollback all stay as they are. They were already server-shaped.

## Part 2 — target topology

```
Employee machine (no git, no repo)          Central server (one deployment)
┌──────────────────────────────┐            ┌──────────────────────────────────┐
│ AI agent (Claude/Codex/…)    │            │ MCP server (streamable HTTP)     │
│   └─ MCP over HTTPS ─────────┼───────────▶│   auth: per-user token / SSO     │
│                              │            │   ├─ scope policy (central)      │
│ Human editor                 │            │   ├─ content store               │
│   └─ client (Part 4) ────────┼───────────▶│   ├─ versioning engine           │
│                              │            │   ├─ git mirrors (server-only)   │
│ Browser (history/diff UI)    │───────────▶│   └─ Postgres: identity + audit  │
└──────────────────────────────┘            │ HTTP API /v1/* (read + write)    │
                                            └──────────────────────────────────┘
```

- **Transport**: FastMCP already supports streamable HTTP, so the stdio
  server becomes a remote one without rewriting the tools. Clients
  configure a URL instead of a command — strictly simpler than today's
  per-runner launch commands.
- **`git` is server-side only**, which is the stated requirement and
  falls out of moving the truth rather than needing work.
- **Tenancy**: one repo tree per tenant, hard-partitioned at the API
  boundary, never by path convention alone.

## Part 3 — the agent path (settled, low risk)

Central MCP with authenticated callers is the easy half:

- `read/write/create/delete/move_file` keep their signatures. Paths
  become logical (`team-docs/onboarding.md`), not OS paths — which also
  removes the Windows/POSIX path-normalization surface (ARCHITECTURE §2)
  from the client entirely.
- `expected_version` optimistic concurrency (spec 021) becomes *more*
  valuable, not less: multiple employees' agents now genuinely race on
  the same file, which on one laptop they rarely did. The conflict
  response already carries `current_version`, so agents can retry
  correctly today.
- Attribution: the authenticated principal *is* the actor. Better than
  the hint handoff, and unforgeable.
- Scope: enforced server-side against central policy. Elicitation still
  works over a remote transport, but see Part 1(4) — who an approval
  binds is a policy decision to make deliberately.

## Part 4 — the human path (undecided; four options)

The requirement that makes this hard: today a human edits a file in
their normal editor and it is versioned with **zero user action**. That
property is the product. Every option below trades against it.

### Option A — thin sync client on the laptop (no git)

A small `ctx client` daemon keeps the local watchdog, but instead of
committing locally it streams content to the server, which commits.

- Keeps the zero-action property exactly.
- No git, no repo, no SQLite on the client — it ships bytes and paths.
- **Cost**: still an install per machine (MDM territory in an
  enterprise), and if agents also write centrally you are back to the
  hard row of Part 0 — server→client push and conflict resolution.
  Viable if you accept **server-authoritative, client-follows** (local
  file is overwritten from the server on conflict, local loss surfaced
  as a conflict version rather than merged).

### Option B — sources already live in a shared store; the server watches it

No client at all. Context sources live in SharePoint/Google Drive/S3/a
network share; the server polls or subscribes to change notifications
and versions what it sees. The `locations.provider` column already
anticipates non-local providers.

- Genuinely zero-install, zero-git, zero-sync on the client.
- One store, single writer story, matches Part 0's recommendation.
- **Cost**: only covers sources that already live there (a file on
  someone's Desktop is invisible), polling latency, and one connector
  per provider to build and maintain.

### Option C — explicit checkpoint

No watching for humans. A version is cut when someone asks: `ctx save`,
a "Save version" button in an editor plugin, or a CI/pre-commit-style
hook.

- Trivial to build, works everywhere, no daemon, no connector.
- **Cost**: it discards the zero-action property — the exact failure the
  project exists to prevent ("nothing tracks its version"). As the
  *only* mechanism, weak. As a complement, cheap and worth having
  regardless.

### Option D — web/editor client as the primary human surface

Humans edit through a thin client that reads and writes the central
store directly (browser editor, or an editor extension talking to the
API). Local files stop being the truth.

- Perfectly coherent with Part 0, identical write path to the agent's,
  attribution and scope free.
- **Cost**: it changes how people work, which is the most expensive kind
  of cost and the least under engineering's control.

### Suggested combination

**B as the strategic answer, C shipped alongside it immediately, A only
for populations that demonstrably need local files, D later if a UI is
built anyway for history/diff.** Reasoning: B is the only option that is
both zero-install and coherent with a server-authoritative truth; C is
days of work and covers B's blind spot (local-only files) without
building sync; A is where sync complexity lives, so it should be a
deliberate, scoped concession rather than the default. Deciding B-vs-A
early matters more than deciding it correctly — they diverge in the
identity model (Part 1(1)), and that is the change you cannot cheaply
redo.

Open question worth answering before committing: **what fraction of real
context sources already live in a shared store?** If it's most of them, B
is obvious. If it's a minority, A's cost may be unavoidable and should be
budgeted rather than discovered.

## Part 4.5 — what enterprises actually trace today (market evidence)

Researched to settle the B-vs-A question. Findings, and what each one
implies:

**1. The tracing standard exists and is not ours to invent.**
OpenTelemetry's GenAI semantic conventions (CNCF-backed, GenAI SIG) now
cover agent orchestration, MCP tool calling and content capture — a
shared vocabulary of ~17 operation names and ~61 `gen_ai.*` attributes,
with a span tree of `invoke_agent` → `chat` / `execute_tool`. Still
*Development* status as of mid-2026, but already consumed by Google
Cloud, AWS, Azure and Datadog.
→ **Implication**: chrono-ctx should *emit into* that pipeline, not ship
a rival audit format. A central server that speaks OTLP lands in the
backend the customer already pays for.

**2. Per-employee agent telemetry is already solved — for the agent.**
Claude Code emits OTel metrics and events for token usage, sessions,
code edits, tool calls and cost, with org-wide config pushed through a
managed settings file; AWS ships a purpose-built "Coding Agent Insights"
console for it. GitHub Copilot Enterprise has an agent-sessions view,
`actor:Copilot` audit-log events, and audit streaming to a SIEM. Cursor
exposes audit logs through its Admin API on the Enterprise plan.
→ **Implication**: nobody needs chrono-ctx to count tokens or list tool
calls. That market is closed.

**3. All of it stops at the agent's activity — none of it tracks what
the document became.** Copilot's docs say plainly that the audit log
does *not* include client session data. Cursor's log is governance
events (logins, roles, MCP config changes, hooks), not content. And the
provenance literature names the gap directly: git says who committed,
what changed and when, but not which agent, model, context, tools or
human approval produced it — arguing for standardized AI attribution
metadata in commits, analogous to `Signed-off-by`, and for capturing a
**compact receipt, not the entire movie**.
→ **Implication**: this is exactly chrono-ctx's surface, and it is
complementary rather than competitive. It also hands us a cheap, already
-legible output format: a provenance receipt per version (actor, model,
session, tool, approval) as a commit trailer.

**4. MCP gateways have become the default enterprise control plane**,
precisely because MCP itself carries no authn/authz, audit, rate limits
or cost control.
→ **Implication**: a central chrono-ctx MCP server is swimming with the
current, and Part 5's auth/audit list is table stakes the whole category
already converged on — not speculative scope.

**5. DLP — the closest mature analogue — converged on hybrid, in a
specific order.** Agentless API integrations into SaaS stores first
(scan at rest, retroactive classification), endpoint agents second for
the last mile, because *cloud-side inspection misses activity that never
traverses the corporate network* and AI tools increasingly run locally
on employee devices.
→ **Implication**: this is the direct answer to B-vs-A. It is not a
choice; it is a sequence, and the industry has already run the
experiment.

### What this settles

**B first, A later as an opt-in last-mile — and A is the
differentiator, not the fallback.** The central/agentless path covers
the bulk, matches where governance tooling already sits, and is the only
one that is zero-install. But a purely central design inherits the exact
blind spot every vendor above has (nothing sees local content), and that
blind spot is the one thing this project is uniquely positioned to
close. So A stops being a concession to legacy workflows and becomes the
paid tier — provided it ships *after* B, not instead of it.

Two consequences for the phases in Part 6: the identity refactor
(phase 1) must keep a device dimension rather than assuming
server-only truth, since A is now planned rather than merely possible;
and an OTLP exporter plus the provenance-receipt format belong in phase
3 alongside the remote MCP transport, where they are nearly free.

Sources: [OTel GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/),
[GenAI/MCP semconv](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions),
[Claude Code monitoring](https://code.claude.com/docs/en/monitoring-usage),
[CloudWatch Coding Agent Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/coding-agents-claude-code.html),
[Copilot agent audit events](https://docs.github.com/en/copilot/reference/enterprise-administrators/agentic-audit-log-events),
[Cursor audit logs](https://www.monad.com/blog/cursor-audit-logs-whats-emitted-and-detection-opportunities),
[AI code provenance](https://medium.com/toward-next-ai/ai-code-provenance-workflow-track-what-coding-agents-changed-before-it-ships-02cd387cbba3),
[agent detection census](https://arxiv.org/pdf/2606.24429),
[MCP gateways](https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp),
[agent-based vs agentless DLP](https://www.cyberhaven.com/infosec-essentials/agent-vs-agentless-dlp).

## Part 5 — enterprise concerns not yet in the codebase

- **AuthN/AuthZ**: OIDC/SSO for humans, service tokens for agents,
  per-tenant RBAC. Replaces the single shared `X-API-Key` (spec 018).
- **Write routes on the HTTP API**: `/v1/*` is read-only today by
  design; the central model needs an authenticated write surface, which
  is a fail-closed boundary to design as carefully as the MCP guardrail.
- **Audit export**: the value proposition for a compliance buyer.
  `audit.py` has the data; it needs a tamper-evident, exportable,
  retention-policy'd surface.
- **Storage growth**: N tenants × M sources of full-content git mirrors.
  See the existing [mirror-storage-optimization
  plan](mirror-storage-optimization-plan.md) — it stops being an
  optimization and becomes a requirement.
- **Availability**: today a crash inconveniences one person. Centrally
  it stops everyone's versioning. Backup/restore of git mirrors + DB,
  and a client-side behavior for "server unreachable" (queue locally? fail
  the agent's write? Option A's daemon makes this a real design
  question).
- **Rate limits and per-call bounds**: specs 036-038's numbers were
  derived for one user on one box. Re-derive under concurrency.
- **Data residency / encryption at rest**: context sources are the
  customer's documents. Table stakes for the buyer this targets.

## Part 6 — staging

Part 4.5 settled the human path (B first, A later as the paid last mile),
so the phases below are a sequence rather than a set of options. Each is
useful shipped alone.

| Phase | What | Unblocks / why here |
| --- | --- | --- |
| **0** | Single-machine product stays exactly as it is | It is the whole install story today and the only thing with users. Nothing below regresses it. |
| **1** | **Identity refactor** — server-issued `context_id` as the real PK, `(tenant, device, logical_path)` as lookup, `st_ino/st_dev` demoted to a client-local rename hint | Required by every path. Keeps the **device dimension** because phase 5 is now planned, not hypothetical. The change that gets more expensive the longer it waits. |
| **2** | **Per-caller identity + authenticated write API** — real principals (SSO/OIDC for humans, service tokens for agents), write routes on `/v1/*`, per-tenant partitioning | Kills the shared-`X-API-Key` gap (spec 018) and removes the actor-hint table's reason to exist on the MCP path. |
| **3** | **Remote MCP + telemetry** — streamable HTTP transport, central scope policy, **collector-first OTLP exporter and provenance receipt (Part 7)** | Agent path fully centralized and shippable. Telemetry belongs here because HTTP transport is what makes trace-context propagation work at all, and the span boundary already exists (Part 7). |
| **4** | **Option B connectors** — SharePoint/Drive/S3/network share providers, server-side watch or poll | The zero-install human path. `locations.provider` already anticipates it. |
| **5** | **Option A thin client** — endpoint agent, no git, server-authoritative | The last mile and the differentiator. After B on purpose: it is where sync complexity lives. |
| **6** | **Enterprise surface** — audit export, admin UI, retention, quotas, residency | Sells the above. |

Parallel, any time: **Option C** (`ctx save` explicit checkpoint). Days
of work, no dependency on any phase, and it covers B's blind spot until
phase 5 exists.

Phases 1-3 were already worth starting before the human path was
decided; they are now unambiguously the critical path.

## Part 7 — emitting into existing tracing systems

The design constraint from Part 4.5(1): **do not invent an audit
format**. The enterprise already runs a collector and already pays for a
backend. chrono-ctx's job is to arrive there speaking the vocabulary
they already parse, carrying the one thing nothing else has — what the
document became.

### 7.1 The instrumentation already exists

`_logged_tool` (spec 038) wraps every MCP tool and already computes
exactly what a span needs: operation name, target path, status, and
elapsed time, with a `try/except` that marks failures. It writes those
four fields to a text file.

So this is a **sink swap, not new instrumentation** — the span
boundaries are drawn and the failure path is already handled. The same
is true of the bounded waits: spec 036-038 put measurement points at the
lock acquire, each git call, and the actor-hint DB connect, which is
precisely the set worth exporting as histograms.

### 7.2 Span model

chrono-ctx is the MCP *server*, so it emits the **server side** of the
tool call. The agent (Claude Code, Codex, …) already emits the client
side under the GenAI conventions' `execute_tool` span.

```
invoke_agent                    (emitted by the agent — not ours)
└─ execute_tool  write_file     (client side — not ours)
   └─ chrono_ctx.tool write_file        ← ours: the whole MCP call
      ├─ chrono_ctx.scope_check         ← guardrail; elicitation if any
      ├─ chrono_ctx.store_write         ← content store write
      └─ chrono_ctx.version_commit      ← versioning gate + git commit
         ├─ lock wait (histogram)
         └─ git call ×N (histogram)
```

Attributes, following GenAI/MCP semconv where one exists and namespacing
the rest under `chrono_ctx.*`. The `gen_ai.*`/`mcp.*` rows are the only
vocabulary-sensitive ones (§7.7); every `chrono_ctx.*` row passes
through every backend untouched:

| Attribute | Source | Note |
| --- | --- | --- |
| `mcp.tool.name` / `gen_ai.tool.name` | `func.__name__` | already in `_logged_tool` |
| `chrono_ctx.path` | logical path | **path only** |
| `chrono_ctx.context_id` | phase 1 identity | stable across renames |
| `chrono_ctx.rev` | git rev of the version cut | the join key to history |
| `chrono_ctx.status` | `result["status"]` | `ok` / `conflict` / `denied` / `error` |
| `chrono_ctx.expected_version` | spec 021 | present only on optimistic writes |
| `chrono_ctx.actor` | authenticated principal (phase 2) | replaces the hint |
| `chrono_ctx.scope_decision` | guardrail | `in_scope` / `elicited_ok` / `denied` / `timeout` |
| `chrono_ctx.tenant` | phase 2 | |

**Never** file content, never tool arguments beyond the path — the same
rule spec 038 already enforces for `data/mcp.log`. The GenAI conventions
make content capture opt-in and default-off; here it is not offered at
all, because the content *is* the customer's documents and it is already
stored, versioned, in the mirror.

### 7.3 Trace context propagation — and why HTTP transport matters

For our spans to appear as children of the agent's trace rather than as
orphans, a `traceparent` has to reach us. Over **streamable HTTP** that
is an ordinary W3C header and works with off-the-shelf propagators —
another concrete argument for the central topology over stdio. Over
**stdio** there is no transport header; MCP's `_meta` request field is
the candidate carrier and the conventions covering it are still moving.

Design accordingly: extract `traceparent` if present, otherwise start a
root trace and correlate by attributes. Never fail a call over
telemetry.

### 7.4 Metrics

Cheap, and they map onto bounds that already exist:

- `chrono_ctx.tool.duration` (histogram, by tool + status)
- `chrono_ctx.lock.wait` (histogram) — against `LOCK_TIMEOUT = 30s`
- `chrono_ctx.git.duration` (histogram, by subcommand) — against
  `GIT_TIMEOUT = 4s`
- `chrono_ctx.versions.committed` / `.conflicts` / `.scope_denied`
  (counters)

The first three make the spec 036-038 budget observable in production
instead of only in `scripts/live_contention_test.py`.

### 7.5 The provenance receipt

Part 4.5(3): git records who/what/when but not which agent, model,
context, tools or approval — and the ask is a **compact receipt, not the
entire movie**. The mirror commit message is the natural carrier, in
`Signed-off-by`-style trailers:

```
ctx: write_file docs/onboarding.md

Ctx-Actor: agent:svc-claude-code/u:alice@corp
Ctx-Model: claude-opus-5
Ctx-Session: 3975b915-ad09-4949-a4e7-0d3c631e90d8
Ctx-Tool: write_file
Ctx-Scope: elicited_ok
Ctx-Trace: 4bf92f3577b34da6a3ce929d0e0e4736
```

`Ctx-Trace` is the load-bearing one: it makes the version history and
the agent trace in the customer's existing backend mutually
navigable — click a version, land on the trace that produced it; see a
suspicious agent run, land on the exact bytes it wrote. Neither system
has both halves today, and the trailer costs a string.

### 7.6 Configuration, packaging, and where traces go

Standard OTel environment variables, so an operator configures this the
way they configure everything else — `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_SERVICE_NAME`, `OTEL_SDK_DISABLED`.
**Default off**, with `data/mcp.log` unchanged as the always-there local
fallback, so the single-machine product gains nothing to configure and
nothing to break.

**Topology: collector-first.** chrono-ctx exports OTLP/HTTP to **one**
endpoint and knows nothing about who reads it. That endpoint is normally
an OTel Collector the customer already runs; the Collector owns fan-out
and any per-vendor attribute transforms (`transform`/`attributes`
processors). Adding a backend is then a collector config change, never a
chrono-ctx release. Direct-to-vendor without a collector stays possible
for anything that accepts `gen_ai.*` — same two env vars, no code path,
no branch.

**Dependency decision — settled (AGENTS.md §7 signed off 2026-09-10):**
`opentelemetry-sdk` + `opentelemetry-exporter-otlp-proto-http` as an
**optional extra** (`pip install chrono-ctx[otel]`), imported lazily and
only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set. Core install stays
dependency-identical; the single-machine product pays nothing for a
server feature it doesn't use.

Two alternatives considered and rejected: the same packages as hard
dependencies (simpler code, but every single-machine user pays for it);
a hand-rolled OTLP/HTTP JSON POST with zero dependencies (cheap to
start, but we'd own batching/retry/backpressure — exactly the code the
SDK exists to not write twice).

If the extra isn't installed and an endpoint is configured anyway, log a
single WARNING at startup and continue unexported — never fail the
server over an optional feature (same fail-open posture as spec 038's
`_set_actor_hint`).

### 7.7 One emission, many backends

Can a single emission path serve opentelemetry-sdk, Langfuse and
LangSmith at once? **Yes — transport is uniform, vocabulary is not, and
for this project the split barely touches us.**

Uniform across all three: OTLP/HTTP as the wire format (JSON and
protobuf), the trace/span model, W3C context propagation, every
`chrono_ctx.*` attribute, and the `Ctx-Trace` receipt trailer (§7.5).

Not uniform: three competing vocabularies — OTel GenAI, OpenLLMetry
(Traceloop), OpenInference (Arize). **But every attribute they disagree
about is LLM-specific — prompts, completions, token counts, model
names — and chrono-ctx emits none of them.** Our spans carry tool name,
path, rev, status, actor and scope decision; all but the first live in a
private namespace that every backend stores as an ordinary span
attribute. So the disagreement covers the two `gen_ai.*`/`mcp.*` rows in
§7.2's table and nothing else, which a collector transform settles in
config. This is uniformity that an LLM SDK genuinely cannot have and we
can.

Per backend, as of 2026-09:

| Backend | Endpoint | Vocabulary | Caveat |
| --- | --- | --- | --- |
| **Langfuse** | `/api/public/otel/v1/traces` (JSON + protobuf) | accepts `gen_ai.*`, OpenLLMetry, OpenInference | legacy ingestion API sunsets on Langfuse Cloud 2026-11-16; GenAI semconv v1.37+ moved prompts/completions to span *events* while Langfuse still reads input/output from attributes, so those fields come out null — irrelevant here, we emit neither |
| **LangSmith** | `api.smith.langchain.com/otel` | OpenLLMetry today; GenAI semconv stated as planned | needs a collector transform, or `langsmith-collector-proxy` |
| **Datadog / CloudWatch / SigNoz / Grafana** | native OTLP | `gen_ai.*` | no transform |

**Non-goal: vendor SDKs in this repo.** Three dependencies, three auth
models, three lifecycles to keep working, and an AGENTS.md §7
conversation each — to replace a mapping the collector expresses in
config. The exporter stays exactly one thing: OTLP.

The same reasoning is why the vocabulary split is tolerable rather than
a risk to design around: our value is `chrono_ctx.*` plus the receipt,
so a future semconv revision costs a collector transform, not a
chrono-ctx release.

Sources: [Langfuse OTel](https://langfuse.com/integrations/native/opentelemetry),
[Langfuse input/output on semconv v1.37+](https://github.com/langfuse/langfuse/issues/12657),
[LangSmith OTel tracing](https://docs.langchain.com/langsmith/trace-with-opentelemetry),
[langsmith-collector-proxy](https://github.com/langchain-ai/langsmith-collector-proxy),
[OpenInference semconv](https://arize.com/docs/ax/concepts/otel-openinference/semantic-conventions).

## Non-goals / open questions

- Not proposing to keep the local single-machine mode working
  identically forever. It should stay the default for individual users
  (it is the whole install story today), but "one codebase, two
  topologies" is a real maintenance cost worth naming rather than
  assuming away.
- Postgres-vs-SQLite is stated as a likely need, not a decision — it
  depends on concurrency targets nobody has set yet.
- Merge semantics are deliberately excluded. Every option above is
  last-writer-wins with optimistic-concurrency conflict detection, which
  is what ships today. Real merging is a separate project.
- Whether the versioning similarity gate should be per-tenant
  configurable. Probably yes; not sized here.
