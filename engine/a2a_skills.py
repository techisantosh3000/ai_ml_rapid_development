from typing import Any, Dict
from .settings import SETTINGS

AGENT_CARD = {
    "protocolVersion": "1.0",
    "name": "SRE-Incident-Triage-Agent",
    "description": "Local-First SLM + Qdrant Incident Triage Agent exposing A2A v1.0 & MCP-ready Skills",
    "url": SETTINGS.a2a_agent_url,
    "capabilities": {"streaming": False, "pushNotifications": False},
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["application/json"],
    "skills": [
        {
            "id": "triage-production-incident",
            "name": "Production Incident Triage & Runbook Grounding",
            "description": "Redacts secrets/PII, searches Qdrant runbooks, and returns grounded remediation.",
            "tags": ["sre", "finops", "qdrant", "slm"],
        },
        {
            "id": "rlm-recursive-log-scan",
            "name": "Recursive Language Model (RLM) Long-Log Analyzer",
            "description": "Splits massive multi-megabyte log dumps into programmatic chunks to prevent Context Rot.",
            "tags": ["rlm", "long-context", "log-analysis"],
        },
    ],
}


def rlm_recursive_log_analyzer(huge_log_blob: str, llm_router: Any, chunk_size: int = 400) -> Dict[str, Any]:
    chunks = [huge_log_blob[i:i + chunk_size] for i in range(0, len(huge_log_blob), chunk_size)]
    sub_findings = []
    for idx, chunk in enumerate(chunks):
        if any(kw in chunk.lower() for kw in ("error", "oomkilled", "out_of_ports", "expired", "critical")):
            res = llm_router.generate(
                prompt=f"Extract the exact error code or failure reason from this log slice in 10 words:\n{chunk}",
                system_instruction="Be strictly factual. Return 10 words or less.",
                temperature=0.0,
                max_tokens=40,
            )
            sub_findings.append({"chunk_index": idx, "finding": res["output"], "latency_ms": res["latency_ms"]})
    return {
        "total_chars": len(huge_log_blob),
        "chunks_created": len(chunks),
        "anomalous_chunks_analyzed": len(sub_findings),
        "sub_llm_findings": sub_findings,
    }
