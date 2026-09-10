# 039 — OTel span emission for MCP tool calls

## Context

From [enterprise-central-server-plan.md](../agents/draft/enterprise-central-server-plan.md)
§7 (span model) and §7.6 (dependency decision, settled 2026-09-10):
`opentelemetry-sdk` ships as an **optional extra**
(`chrono-ctx[otel]`), default off, `data/mcp.log` unchanged as the
always-there local fallback.

`_logged_tool` (spec 038) already computes exactly what a span needs —
operation name, target path, status, elapsed time — for every MCP tool
call, with a `try/except` that marks failures. This spec swaps that
computation into an additional sink (an OTel span) rather than adding
new instrumentation; the file log stays exactly as it is.

Scope is deliberately the first slice of §7's design: span emission for
the five MCP tools only. Out of scope for this spec (left for later
specs, listed in the draft): the `Ctx-Trace` commit trailer (§7.5,
touches `git_store.py`, a separate call path), metrics/histograms
(§7.4), and `traceparent` propagation over remote transport (§7.3 —
today's transport is stdio, so there is no inbound header to extract
yet).

## Scope

**In**
- New `app/mcp/telemetry.py`: lazy OTel SDK init, gated on
  `OTEL_EXPORTER_OTLP_ENDPOINT` being set. When unset, tracing is a
  true no-op (the SDK's own `NoOpTracer`) — no OTLP import, no
  background export thread.
- `pyproject.toml`: `[project.optional-dependencies] otel` with
  `opentelemetry-sdk` and `opentelemetry-exporter-otlp-proto-http`.
  Added to `dev` too, so `uv sync --extra dev` covers the tests below
  without a separate `--extra otel` step.
- `_logged_tool` (`app/mcp/server.py`) wraps each call in a span named
  after the tool, with `chrono_ctx.path`/`mcp.tool.name` set on start,
  `chrono_ctx.status` set from the result, and the span marked as an
  error (not just logged) on an unhandled exception — mirroring exactly
  what the existing log lines already record, so no new data is
  captured, only a second sink for the same facts.
- Missing-package + configured-endpoint case (`chrono-ctx[otel]` not
  installed but `OTEL_EXPORTER_OTLP_ENDPOINT` is set): one WARNING at
  startup, server continues unexported — same fail-open posture as
  spec 038's `_set_actor_hint`.

**Out**
- The `Ctx-Trace` provenance receipt / commit trailers (§7.5) — a
  `git_store.py` change, separate spec.
- Metrics/histograms (§7.4).
- `traceparent` extraction from an inbound request (§7.3) — no remote
  transport exists yet to carry one.
- Any vendor-specific code path (Langfuse/LangSmith). Collector-first
  topology (§7.6/§7.7) means this spec never branches on backend.
- Changing `data/mcp.log`'s format or content in any way.

## Acceptance criteria

- AC-1. With `OTEL_EXPORTER_OTLP_ENDPOINT` unset, no OTel span exporter
  is constructed and no network call is attempted — importing
  `app.mcp.telemetry` and calling a tool does not require the `otel`
  extra to be installed.
- AC-2. With `OTEL_EXPORTER_OTLP_ENDPOINT` set and the `otel` extra
  installed, a successful tool call produces exactly one span whose
  name is the tool's function name, carrying `chrono_ctx.path` (or
  `chrono_ctx.src`/`chrono_ctx.dst` for `move_file`) and
  `chrono_ctx.status` matching the returned `status` field.
- AC-3. When the wrapped call raises, the span is recorded as an error
  (`span.record_exception` + error status) before the exception
  propagates — the exception itself is still raised unchanged (no
  behavior change to callers).
- AC-4. `data/mcp.log`'s entry/exit lines (spec 038 AC-2) are
  byte-for-byte unaffected by whether OTel is configured — same
  content whether `OTEL_EXPORTER_OTLP_ENDPOINT` is set or not.
- AC-5. `OTEL_EXPORTER_OTLP_ENDPOINT` set but the `otel` extra not
  importable: server startup logs one WARNING naming the missing
  package and continues; tool calls still succeed (span emission is
  silently skipped, not raised).

## Error cases

- EC-1. The OTLP exporter itself failing (endpoint unreachable, TLS
  error, timeout) must never fail or delay the MCP tool call — spans
  are batched/exported asynchronously by the SDK's own
  `BatchSpanProcessor`, off the request path.

## Contracts

```python
# app/mcp/telemetry.py
def get_tracer() -> "opentelemetry.trace.Tracer":
    """Returns a real tracer if OTEL_EXPORTER_OTLP_ENDPOINT is set and
    the otel extra is importable; otherwise OTel's own no-op tracer.
    Never raises."""

# app/mcp/server.py — _logged_tool gains span creation around the
# existing try/except; no signature changes to any @mcp.tool().
```

## Non-goals / open questions

- Whether `OTEL_SERVICE_NAME`/`OTEL_EXPORTER_OTLP_HEADERS` need
  chrono-ctx-specific defaults, or the SDK's own env-var handling is
  sufficient. Assumed sufficient (draft §7.6) — revisit only if a real
  deployment needs otherwise.
- Whether the daemon's own operations (independent of MCP) should also
  emit spans. Out of scope — MCP is the synchronous, human/agent-facing
  call path this spec targets; the daemon's failure boundary already
  logs-and-continues (spec 038 draft, Part 1 non-goals).
