"""OTel span emission for MCP tool calls (spec 039).

`opentelemetry-sdk` is an **optional extra** (`chrono-ctx[otel]`, draft:
docs/agents/draft/enterprise-central-server-plan.md §7.6) - the
single-machine product must not pay for a server feature it doesn't use.
So this module is importable, and every function in it usable, with the
extra absent: the default is a true no-op tracer, and every `opentelemetry`
import is deferred inside `get_tracer()`, gated on
`OTEL_EXPORTER_OTLP_ENDPOINT` actually being set.

`_logged_tool` (app/mcp/server.py) is the only caller. It already computes
everything a span needs - operation name, path, status, elapsed time - for
the existing `data/mcp.log` line; this module is a second sink for the same
facts, not new instrumentation.
"""

import contextlib
import logging
import os

_tracer_cache = None
_cache_key = None


class _NoOpSpan:
    """Same call surface as `_RealSpan` below, every method a no-op - so
    `_logged_tool` never has to branch on whether OTel is configured."""

    def set_attribute(self, key, value):
        pass

    def record_exception(self, exc):
        pass


class _NoOpTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, name):
        yield _NoOpSpan()


_NOOP_TRACER = _NoOpTracer()


class _RealSpan:
    """Thin adapter over a real OTel span, so `_logged_tool` never needs
    to import `opentelemetry` types directly. `record_exception` also
    marks the span errored - the raw OTel API splits that into two calls
    (`record_exception` + `set_status`), collapsed here into the one
    method `_logged_tool` actually needs."""

    def __init__(self, otel_span):
        self._span = otel_span

    def set_attribute(self, key, value):
        self._span.set_attribute(key, value)

    def record_exception(self, exc):
        from opentelemetry.trace import Status, StatusCode

        self._span.record_exception(exc)
        self._span.set_status(Status(StatusCode.ERROR, str(exc)))


class _RealTracer:
    def __init__(self, otel_tracer):
        self._tracer = otel_tracer

    @contextlib.contextmanager
    def start_as_current_span(self, name):
        with self._tracer.start_as_current_span(name) as otel_span:
            yield _RealSpan(otel_span)


def get_tracer():
    """Returns a tracer usable via `with tracer.start_as_current_span(name)
    as span: span.set_attribute(...)`. A true no-op (no OTel import, no
    background thread) unless `OTEL_EXPORTER_OTLP_ENDPOINT` is set. Never
    raises - a telemetry misconfiguration must not fail the MCP server
    (same fail-open posture as spec 038's `_set_actor_hint`)."""
    global _tracer_cache, _cache_key

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return _NOOP_TRACER

    if _tracer_cache is not None and _cache_key == endpoint:
        return _tracer_cache

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logging.warning(
            "[MCP] OTEL_EXPORTER_OTLP_ENDPOINT is set but the 'otel' extra "
            "is not installed (pip install chrono-ctx[otel]) - spans will "
            "not be exported"
        )
        _tracer_cache, _cache_key = _NOOP_TRACER, endpoint
        return _tracer_cache

    provider = TracerProvider(
        resource=Resource.create(
            {"service.name": os.getenv("OTEL_SERVICE_NAME", "chrono-ctx")}
        )
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    _tracer_cache = _RealTracer(trace.get_tracer("chrono-ctx"))
    _cache_key = endpoint
    return _tracer_cache
