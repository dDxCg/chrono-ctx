import logging
import sys

import pytest

import app.mcp.server as server
import app.mcp.telemetry as telemetry


@pytest.fixture(autouse=True)
def reset_tracer_cache():
    telemetry._tracer_cache = None
    telemetry._cache_key = None
    yield
    telemetry._tracer_cache = None
    telemetry._cache_key = None


def _in_memory_tracer():
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return telemetry._RealTracer(provider.get_tracer("test")), exporter


def test_ac1_get_tracer_is_noop_when_endpoint_unset(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    tracer = telemetry.get_tracer()

    assert isinstance(tracer, telemetry._NoOpTracer)
    # The no-op API surface must be usable without raising - this is what
    # _logged_tool calls on every tool invocation regardless of config.
    with tracer.start_as_current_span("x") as span:
        span.set_attribute("a", "b")
        span.record_exception(ValueError("boom"))


@pytest.mark.anyio
async def test_ac3_logged_tool_marks_span_errored_on_exception(monkeypatch):
    tracer, exporter = _in_memory_tracer()
    monkeypatch.setattr(server, "get_tracer", lambda: tracer)

    @server._logged_tool
    async def boom(path: str):
        raise RuntimeError("kaboom")

    with pytest.raises(RuntimeError):
        await boom(path="some/path")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "boom"
    assert spans[0].status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in spans[0].events)


def test_ac5_logs_warning_and_falls_back_to_noop_when_extra_missing(
    monkeypatch, caplog
):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    # sys.modules[name] = None is the standard trick to force the next
    # `import name` to raise ImportError, simulating chrono-ctx[otel] not
    # being installed even though it's a real dev dependency here.
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace", None)

    with caplog.at_level(logging.WARNING):
        tracer = telemetry.get_tracer()

    assert isinstance(tracer, telemetry._NoOpTracer)
    assert any(
        "otel" in record.message.lower() for record in caplog.records
    )
