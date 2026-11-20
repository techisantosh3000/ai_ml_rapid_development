import contextlib
import copy
import json
import time
from typing import Any, Callable, Dict, List, Optional
from .settings import SETTINGS


class TraceDebugger:
    """
    Live Step-Through Debugger & OpenTelemetry Exporter for Arize Phoenix.
    Reads Phoenix URL & endpoint dynamically from AppSettings (.env / configs/app_config.yaml).
    """
    def __init__(
        self,
        debug_mode: bool = False,
        enable_phoenix: bool = False,
        phoenix_endpoint: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        self.debug_mode = debug_mode
        self.enable_phoenix = enable_phoenix
        self.runs: Dict[str, List[Dict[str, Any]]] = {}
        self.current_run_id: Optional[str] = None
        self.phoenix_url: str = SETTINGS.phoenix_ui_url
        self._tracer = None

        endpoint = phoenix_endpoint or SETTINGS.phoenix_traces_endpoint
        proj = project_name or SETTINGS.phoenix_project_name

        try:
            from phoenix.otel import register
            tracer_provider = register(
                project_name=proj,
                endpoint=endpoint,
                set_global_tracer_provider=False,
            )
            self._tracer = tracer_provider.get_tracer("bootcamp.debugger")
        except Exception as exc:
            print(f"[TraceDebugger] OTel Phoenix exporter inactive ({exc}); local snapshots still active.")

    @contextlib.contextmanager
    def start_span(self, name: str, span_kind: str = "CHAIN"):
        if self._tracer is not None:
            with self._tracer.start_as_current_span(name) as span:
                span.set_attribute("openinference.span.kind", span_kind)
                yield span
        else:
            yield None

    def start_run(self, run_id: str):
        self.current_run_id = run_id
        self.runs[run_id] = []

    def record_step(
        self,
        step_name: str,
        input_data: Any,
        output_data: Any,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        span_kind: str = "CHAIN",
        breakpoint_fn: Optional[Callable[[Any], Any]] = None,
    ) -> Any:
        final_output = output_data
        if self.debug_mode and breakpoint_fn is not None:
            print(f"\n[BREAKPOINT @ {step_name}] Inspecting intermediate state...")
            final_output = breakpoint_fn(copy.deepcopy(output_data))

        snapshot = {
            "timestamp": round(time.time(), 3),
            "step": step_name,
            "latency_ms": round(latency_ms, 2),
            "input": copy.deepcopy(input_data),
            "output": copy.deepcopy(final_output),
            "metadata": metadata or {},
        }
        if self.current_run_id:
            self.runs[self.current_run_id].append(snapshot)

        if self._tracer is not None:
            with self._tracer.start_as_current_span(step_name) as span:
                span.set_attribute("openinference.span.kind", span_kind)
                span.set_attribute("bootcamp.run_id", str(self.current_run_id))
                span.set_attribute("bootcamp.latency_ms", float(latency_ms))
                span.set_attribute("input.value", json.dumps(input_data, default=str)[:4000])
                span.set_attribute("output.value", json.dumps(final_output, default=str)[:4000])
                if metadata:
                    for k, v in metadata.items():
                        span.set_attribute(f"metadata.{k}", str(v))

        return final_output
