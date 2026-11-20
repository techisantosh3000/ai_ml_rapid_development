import os
import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine import (
    ModelRouter,
    PromptRegistry,
    QdrantVectorStore,
    TraceDebugger,
    UseCaseLoader,
)

try:
    from engine.a2a_skills import AGENT_CARD, rlm_recursive_log_analyzer
except ImportError:
    AGENT_CARD = {"protocolVersion": "1.0", "name": "SRE-Incident-Triage-Agent"}
    rlm_recursive_log_analyzer = None

STATE: Dict[str, Any] = {}


def sanitize_log(raw_log: str) -> Dict[str, Any]:
    """Pre-inference PII/secret redaction and prompt-injection firewall."""
    injection_detected = bool(
        re.search(r"ignore previous instructions|output all .* passwords", raw_log, re.I)
    )
    sanitized = re.sub(r"hf_[A-Za-z0-9]{8,}", "[REDACTED_HF_TOKEN]", raw_log)
    sanitized = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]", sanitized)
    sanitized = re.sub(
        r"'Ignore previous instructions[^']*'",
        "[BLOCKED_INJECTION_PAYLOAD]",
        sanitized,
        flags=re.I,
    )
    return {"injection_blocked": injection_detected, "sanitized_log": sanitized}


def get_or_init_domain(domain: str) -> Dict[str, Any]:
    """Lazily loads & indexes any of the 6 enterprise domains into its own Qdrant collection."""
    domain = (domain or "sre_finops").strip().lower()
    if domain not in UseCaseLoader.SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported domain: {domain}")

    domain_cache: Dict[str, Any] = STATE.setdefault("domains", {})
    if domain not in domain_cache:
        loader = UseCaseLoader(configs_dir=str(REPO_ROOT / "configs"), domain=domain)
        runbooks = loader.load_runbooks()
        incidents = loader.load_incidents()
        qdrant = QdrantVectorStore(
            collection_name=loader.collection_name,
            path=str(REPO_ROOT / "qdrant_local_db"),
        )
        qdrant.upsert_documents(runbooks)
        domain_cache[domain] = {
            "loader": loader,
            "runbooks": runbooks,
            "incidents": incidents,
            "qdrant": qdrant,
        }
    return domain_cache[domain]


def run_triage_pipeline(
    incident_id: str,
    raw_log: str,
    domain: str = "sre_finops",
    category_filter: Optional[str] = None,
    enable_vertex: bool = False,
    top_k: int = 2,
) -> Dict[str, Any]:
    """Executes Guardrails -> Domain Qdrant Retrieval -> Externalized YAML Prompt -> LLM Inference."""
    dom_ctx = get_or_init_domain(domain)
    qdrant: QdrantVectorStore = dom_ctx["qdrant"]
    prompts: PromptRegistry = STATE["prompts"]
    dbg: TraceDebugger = STATE["dbg"]
    router: ModelRouter = STATE["vertex_llm"] if enable_vertex else STATE["local_llm"]

    dbg.start_run(f"api_{domain}_{incident_id}")
    with dbg.start_span(f"FastAPI_Triage_{domain}_{incident_id}", span_kind="CHAIN") as root_span:
        if root_span:
            root_span.set_attribute("domain", domain)
            root_span.set_attribute("incident.id", incident_id)
            root_span.set_attribute("llm.provider", router.provider)
            root_span.set_attribute("input.value", raw_log)

        t0 = time.perf_counter()
        guard = sanitize_log(raw_log)
        t_guard = round((time.perf_counter() - t0) * 1000, 2)
        dbg.record_step("guardrail_sanitize", raw_log, guard, t_guard, span_kind="GUARDRAIL")

        t1 = time.perf_counter()
        meta_filter = (
            {"category": category_filter}
            if category_filter and category_filter != "all"
            else None
        )
        hits = qdrant.search(
            query=guard["sanitized_log"],
            top_k=top_k,
            metadata_filter=meta_filter,
        )
        t_ret = round((time.perf_counter() - t1) * 1000, 2)
        dbg.record_step(
            "qdrant_retrieve",
            {"domain": domain, "query": guard["sanitized_log"], "filter": meta_filter},
            hits,
            t_ret,
            span_kind="RETRIEVER",
        )

        p_cfg = prompts.load("day05_rag_grounded")
        ctx_block = "\n".join(f"- {h['text']}" for h in hits) if hits else "No matching runbooks."
        hydrated_prompt = prompts.render(
            p_cfg["user_template"],
            retrieved_context=ctx_block,
            incident_text=guard["sanitized_log"],
        )

        gen = router.generate(
            prompt=hydrated_prompt,
            system_instruction=p_cfg["system_prompt"],
            temperature=float(p_cfg.get("temperature", 0.1)),
            max_tokens=int(p_cfg.get("max_tokens", 180)),
        )
        dbg.record_step("llm_remediation_gen", hydrated_prompt, gen["output"], gen["latency_ms"], span_kind="LLM")

        top_match = hits[0] if hits else {"metadata": {"runbook_id": "NONE"}, "score": 0.0, "text": ""}
        result = {
            "domain": domain,
            "incident_id": incident_id,
            "provider": gen["provider"],
            "model": gen["model"],
            "injection_blocked": guard["injection_blocked"],
            "sanitized_log": guard["sanitized_log"],
            "matched_runbook": top_match["metadata"].get("runbook_id", "NONE"),
            "similarity_score": top_match["score"],
            "retrieved_runbooks": [
                {
                    "runbook_id": h["metadata"].get("runbook_id"),
                    "category": h["metadata"].get("category"),
                    "service": h["metadata"].get("service"),
                    "score": h["score"],
                    "text": h["text"],
                }
                for h in hits
            ],
            "remediation": gen["output"],
            "latency_breakdown_ms": {
                "guardrail": t_guard,
                "qdrant_retrieval": t_ret,
                "llm_generation": gen["latency_ms"],
                "total": round(t_guard + t_ret + gen["latency_ms"], 2),
            },
        }
        if root_span:
            root_span.set_attribute("output.value", result["remediation"])
        return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE["local_llm"] = ModelRouter(enable_vertex=False)
    STATE["vertex_llm"] = ModelRouter(enable_vertex=True)
    STATE["prompts"] = PromptRegistry(prompts_dir=str(REPO_ROOT / "configs" / "prompts"))
    STATE["dbg"] = TraceDebugger(
        debug_mode=False,
        enable_phoenix=False,
        phoenix_endpoint=os.getenv("PHOENIX_ENDPOINT", "http://127.0.0.1:6008/v1/traces"),
    )
    # Pre-warm default domain
    get_or_init_domain(os.getenv("BOOTCAMP_DOMAIN", "sre_finops"))
    yield
    STATE.clear()


app = FastAPI(
    title="Multi-Domain Hybrid AI Incident Triage Microservice",
    description="Dynamic Domain-Agnostic Local Qwen2.5-Coder + Qdrant RAG Service (6 Enterprise Domains)",
    version="2.0.0",
    lifespan=lifespan,
)


class TriageRequest(BaseModel):
    domain: str = Field(default="sre_finops", description="sre_finops, cicd_devops, payment_ops, iam_servicedesk, cloud_finops, or api_gateway")
    incident_id: str = Field(default="INC-CUSTOM-001")
    raw_log: str = Field(..., min_length=5)
    category_filter: Optional[str] = Field(default=None)
    enable_vertex: bool = Field(default=False)
    top_k: int = Field(default=2, ge=1, le=5)


class RLMScanRequest(BaseModel):
    huge_log_blob: str = Field(..., min_length=10)
    chunk_size: int = Field(default=400, ge=100, le=2000)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/ui")


@app.get("/.well-known/agent-card.json")
def get_a2a_agent_card():
    return AGENT_CARD


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "local_model": os.path.basename(STATE["local_llm"].local_model_path),
        "supported_domains": list(UseCaseLoader.SUPPORTED_DOMAINS.keys()),
        "loaded_domains": list(STATE.get("domains", {}).keys()),
    }


@app.get("/v1/domains")
def list_domains():
    return {"domains": UseCaseLoader.SUPPORTED_DOMAINS}


@app.get("/v1/incidents")
def list_sample_incidents(domain: str = "sre_finops"):
    dom_ctx = get_or_init_domain(domain)
    return {"domain": domain, "incidents": dom_ctx["incidents"]}


@app.post("/v1/triage")
def triage_endpoint(req: TriageRequest):
    if req.enable_vertex and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        raise HTTPException(
            status_code=400,
            detail="enable_vertex=True requested, but GOOGLE_CLOUD_PROJECT is not set.",
        )
    return run_triage_pipeline(
        incident_id=req.incident_id,
        raw_log=req.raw_log,
        domain=req.domain,
        category_filter=req.category_filter,
        enable_vertex=req.enable_vertex,
        top_k=req.top_k,
    )


@app.post("/v1/rlm-scan")
def rlm_scan_endpoint(req: RLMScanRequest):
    if rlm_recursive_log_analyzer is None:
        raise HTTPException(status_code=501, detail="engine/a2a_skills.py not found.")
    return rlm_recursive_log_analyzer(
        huge_log_blob=req.huge_log_blob,
        llm_router=STATE["local_llm"],
        chunk_size=req.chunk_size,
    )


# ==============================================================================
# INTERACTIVE MULTI-DOMAIN GRADIO UI MOUNTED AT /ui
# ==============================================================================
try:
    import gradio as gr

    def _on_domain_change(domain_key: str):
        dom_ctx = get_or_init_domain(domain_key)
        incs = dom_ctx["incidents"]
        choices = [f"{i['incident_id']} | {i['title']} ({i['severity']})" for i in incs]
        cats = ["all"] + sorted({r["metadata"]["category"] for r in dom_ctx["runbooks"]})
        first = incs[0]
        return (
            gr.Dropdown(choices=choices, value=choices[0]),
            gr.Dropdown(choices=cats, value="all"),
            first["incident_id"],
            first["raw_log"],
        )

    def _load_preset_incident(domain_key: str, choice: str):
        if not choice:
            return "INC-CUSTOM-001", "", "all"
        dom_ctx = get_or_init_domain(domain_key)
        inc_id = choice.split(" | ")[0].strip()
        for inc in dom_ctx["incidents"]:
            if inc["incident_id"] == inc_id:
                return inc["incident_id"], inc["raw_log"], "all"
        return "INC-CUSTOM-001", "", "all"

    def _ui_triage(domain_key: str, incident_id: str, raw_log: str, category: str, use_vertex: bool):
        if not raw_log.strip():
            return "Please enter or select an incident log.", {}, {}
        if use_vertex and not os.getenv("GOOGLE_CLOUD_PROJECT"):
            return "Vertex AI toggle is ON, but GOOGLE_CLOUD_PROJECT is not configured.", {}, {}
        res = run_triage_pipeline(
            incident_id=incident_id or "INC-UI-001",
            raw_log=raw_log,
            domain=domain_key,
            category_filter=category,
            enable_vertex=use_vertex,
            top_k=2,
        )
        lines = [
            f"### Domain: `{res['domain']}` | Matched Runbook: `{res['matched_runbook']}` (Score: `{res['similarity_score']}`)",
            f"**Provider:** `{res['provider']}` (`{res['model']}`) | **Injection Blocked:** `{res['injection_blocked']}` | **Total Latency:** `{res['latency_breakdown_ms']['total']} ms`",
            "",
            f"> {res['remediation']}",
        ]
        return "\n".join(lines), res["retrieved_runbooks"], res["latency_breakdown_ms"]

    with gr.Blocks(title="Multi-Domain AI Incident Triage Console") as demo:
        gr.Markdown("# Multi-Domain Hybrid AI Incident Triage Console (6 Enterprise Domains)")
        gr.Markdown(
            "Switch dynamically across **SRE/FinOps, CI/CD DevOps, Payment Ops, IAM Service Desk, Cloud FinOps, and API Gateway** "
            "using the exact same Qdrant + Local Qwen2.5-Coder pipeline."
        )

        with gr.Row():
            domain_dropdown = gr.Dropdown(
                choices=list(UseCaseLoader.SUPPORTED_DOMAINS.keys()),
                value="sre_finops",
                label="1. Select Enterprise Domain Profile",
            )
            preset_dropdown = gr.Dropdown(
                choices=["INC-2026-001 | GKE Payment Pod OOMKilled (P1)"],
                value="INC-2026-001 | GKE Payment Pod OOMKilled (P1)",
                label="2. Select Production Incident Preset",
            )
            category_dropdown = gr.Dropdown(
                choices=["all", "compute", "finops", "database", "streaming", "networking", "security", "cache"],
                value="all",
                label="3. Qdrant Metadata Filter",
            )
            vertex_checkbox = gr.Checkbox(value=False, label="Enable Vertex AI (False = Local Qwen)")

        with gr.Row():
            inc_id_box = gr.Textbox(value="INC-2026-001", label="Incident ID", scale=1)
            raw_log_box = gr.Textbox(
                value="2026-11-16T18:12:04Z WARN container=checkout-api pod=checkout-api-7d9f8c-x2k9p namespace=checkout-api OOMKilled (Exit Code 137) after deployment v2.14.3 rollout; RSS heap hit 2048Mi limit.",
                label="Raw Production Log / Alert Payload",
                lines=3,
                scale=4,
            )

        run_btn = gr.Button("Run Multi-Domain Triage Pipeline", variant="primary")
        output_md = gr.Markdown()

        with gr.Row():
            retrieved_json = gr.JSON(label="Qdrant Retrieved Runbooks & Cosine Scores")
            latency_json = gr.JSON(label="Pipeline Latency Breakdown (ms)")

        domain_dropdown.change(
            fn=_on_domain_change,
            inputs=[domain_dropdown],
            outputs=[preset_dropdown, category_dropdown, inc_id_box, raw_log_box],
        )
        preset_dropdown.change(
            fn=_load_preset_incident,
            inputs=[domain_dropdown, preset_dropdown],
            outputs=[inc_id_box, raw_log_box, category_dropdown],
        )
        run_btn.click(
            fn=_ui_triage,
            inputs=[domain_dropdown, inc_id_box, raw_log_box, category_dropdown, vertex_checkbox],
            outputs=[output_md, retrieved_json, latency_json],
        )

    app = gr.mount_gradio_app(app, demo, path="/ui")
except ImportError:
    pass
