---
marp: true
theme: default
paginate: true
---

# Production AI Engineering Workshop
## From Local SLM & Qdrant RAG to Multi-Agent A2A & Cloud Deployment
**Instructor:** Santosh Kumar Sundar Ray | **Stack:** Local Qwen2.5-Coder SLM, Qdrant, FastAPI, Arize Phoenix, GCP & AWS

---

## Slide 1: Workshop Agenda & Live Lab Flow (3 Hours)
1. **Architecture & SLM vs. LLM Economics** — Why `Qwen2.5-Coder-1.5B` runs 100% locally offline before touching cloud APIs.
2. **Deterministic Scripts vs. Non-Deterministic Agents** — Where to use Python/Regex/Pydantic vs. Probabilistic Reasoning.
3. **Vector Retrieval & Prompt Caching** — Qdrant metadata filtering + static prefix caching (`OpenAI` / `Gemini` / `Local KV`).
4. **Skills, MCP & Agent2Agent (A2A v1.0) Protocol** — Tool calling trade-offs & cross-agent interoperability.
5. **Agentic Patterns & Recursive Language Models (RLM)** — Solving "Context Rot" programmatically.
6. **Live Demo & Cloud Parity** — FastAPI + Gradio Console, Arize Phoenix X-Ray Traces, GCP Cloud Run / AWS ECS & Slingshot.

---

## Slide 2: SLM vs. Frontier LLM (Why Local First?)
| Dimension | Small Language Model (SLM — Qwen 1.5B) | Frontier Cloud LLM (Gemini 2.5 / GPT-4o) |
| :--- | :--- | :--- |
| **Deployment** | Runs on 16GB Windows workstation / edge pod | Managed cloud API (`Vertex AI` / `OpenAI`) |
| **Data Privacy** | Zero egress; air-gapped compliant | Requires PII/secret redaction guardrails |
| **Unit Cost** | $0 marginal token cost | Per-1M token billing (mitigated via Prompt Caching) |
| **Best Fit** | Classification, JSON extraction, bounded RAG | Complex multi-hop synthesis, ambiguous planning |

---

## Slide 3: Deterministic Scripts vs. Non-Deterministic Agents
* **Deterministic Layer (100% Predictable, 0 Tokens, <2 ms):**
  * Regex PII/token redaction (`hf_...` -> `[REDACTED]`)
  * Qdrant metadata filtering (`category == "database"`)
  * Pydantic schema validation & `max_steps` loop caps
* **Non-Deterministic Layer (Semantic Reasoning, 150–800 ms):**
  * Interpreting unstructured stack traces (`INC-2026-001`..`010`)
  * Synthesizing multi-runbook remediation steps
* **Golden Rule:** *Never ask an LLM to do what a 5-line deterministic Python function can guarantee.*

---

## Slide 4: Dependency Management & Reproducibility
* **Layered Lock Strategy on Windows & Containers:**
  1. **Isolated Virtual Environment:** `.venv` pinned via `requirements.txt` (`qdrant-client`, `transformers`, `fastapi`, `arize-phoenix`).
  2. **Hard Offline Weight Lock:** `HF_HUB_OFFLINE=1` & `local_files_only=True` prevent unexpected Hugging Face Hub network downloads during live workshops.
  3. **Container Parity:** Identical `requirements.txt` baked into a multi-stage `Dockerfile` for local Rancher/Docker Desktop, GCP Cloud Run, and AWS ECS.

---

## Slide 5: Prompt Caching & Cost Optimization
* **How Prompt Caching Works (OpenAI, Vertex AI Gemini, Local vLLM/llama.cpp):**
  * LLMs cache the **Key-Value (KV) attention tensors** of static prompt prefixes (`System Instruction` + `Standard Runbooks`).
  * Place **static instructions first** and **dynamic incident logs last**.
* **Impact:** Up to **50%–90% input token cost reduction** and lower Time-To-First-Token (TTFT) on repeated triage calls.

---

## Slide 6: Agents Calling Tools & APIs — Cost, Benefit & Drawbacks
* **Benefits:** Grounds answers in live telemetry (`metrics`, `Qdrant`), eliminates stale training cutoffs, triggers real webhooks.
* **Costs & Drawbacks:**
  * **Latency Multiplication:** 3 sequential tool calls = 3x LLM round-trips.
  * **Token Bloat:** Raw JSON API responses flood the context window.
  * **Failure Cascades:** Flaky external APIs or infinite retry loops without circuit breakers.
* **Mitigation:** Enforce `max_steps`, strict Pydantic tool schemas, and Arize Phoenix span tracing.

---

## Slide 7: Skills, MCP & Agent2Agent (A2A v1.0) Protocol
* **Skills (Reusable Domain Capabilities):** Modular instruction + tool bundles (e.g., `triage-production-incident`, `rlm-recursive-log-scan`).
* **MCP (Model Context Protocol):** Vertical integration — connects **one agent to tools, databases, and APIs**.
* **A2A v1.0 (Linux Foundation Standard):** Horizontal integration — connects **independent agents across teams/vendors** via `/.well-known/agent-card.json` (JSON-RPC / HTTP+REST / gRPC) without exposing internal memory.

---

## Slide 8: Core AI Agent Patterns & Recursive Language Models (RLM)
* **4 Production Agent Patterns:**
  1. **Routing Pattern:** Classify intent (`P1`/`P2`/`P3`) -> dispatch to specialist handler.
  2. **RAG + Hybrid Rerank:** Bi-encoder Qdrant search + lexical overlap scoring.
  3. **ReAct Tool Loop:** `Observe Metrics -> Retrieve Runbook -> Synthesize Plan`.
  4. **Evaluator-Optimizer (Guardrail Loop):** Input firewall + output faithfulness check.
* **Recursive Language Models (RLM — MIT CSAIL 2026 Paradigm):**
  * Solves **"Context Rot"** on massive logs: instead of stuffing 1M tokens into one prompt, treat context as an **external Python variable**, slice programmatically, invoke sub-SLMs in parallel, and aggregate findings.

---

## Slide 9: Cloud Deployment Architecture (GCP & AWS Parity)
* **Local Dev:** Windows 11 + `.venv` + Local `Qwen2.5-Coder` + Embedded `Qdrant` + `Arize Phoenix` (`:6008`).
* **GCP Production Target:**
  * Containerized FastAPI (`app/main.py`) on **Cloud Run**
  * **Vertex AI** (`gemini-2.5-flash` + `Vertex AI Vector Search`) via `ENABLE_VERTEX_AI=True`
  * **Cloud Trace** (OpenTelemetry exporter)
* **AWS Production Target:**
  * Containerized FastAPI on **AWS ECS Fargate / App Runner**
  * **Amazon Bedrock** / **OpenAI API** + **Qdrant Cloud / OpenSearch**

---

## Slide 10: Workflow Orchestration & Slingshot Integration
* **Where Workflow Engines Fit:**
  * Our FastAPI microservice (`POST /v1/triage`) acts as a stateless, OpenTelemetry-traced execution worker.
* **How Slingshot / Enterprise Workflow Platforms Help:**
  * **Trigger & Ingestion:** Captures alerts from PagerDuty, Jira, Slack, or webhooks and routes payloads to `/v1/triage`.
  * **Human-in-the-Loop (HITL) Approvals:** Pauses high-risk `P1` remediations (e.g., pod rollback or token revocation) for Slack/Teams one-click approval before executing downstream playbooks.
  * **Closed-Loop Audit:** Logs ticket resolution outcomes back into Qdrant to continuously enrich runbooks.
