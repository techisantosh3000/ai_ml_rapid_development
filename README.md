# 🚀 10-Day Rapid Hands-On AI/ML Engineering Bootcamp (Visual Story Edition)

A **zero-configuration, visual, story-driven 10-working-day AI/ML Engineering Bootcamp & Multi-Domain Incident Triage Platform** designed to take engineers from classical ML baselines to production-grade RAG, QLoRA fine-tuning, Agentic workflows, Guardrails, and FastAPI/Gradio microservices.

Built around a **Modular `engine/` Architecture**, **Externalized YAML Prompts & `.env` Configuration**, **6 Plug-and-Play Enterprise Domains (60 Runbooks & 60 Production Incidents)**, **Persistent Qdrant Vector Storage**, and **Inline HTML X-Ray Storyboards + Arize Phoenix Observability**—running **100% offline** on your local machine using local Hugging Face **Qwen2.5-Coder-1.5B** weights, with a single-flag toggle (`ENABLE_VERTEX_AI=false` by default) for Google Cloud Vertex AI / Gemini parity.

## 🏗️ High-Level System & Component Architecture

### 1. End-to-End Visual Story & Hybrid Execution Architecture

```
flowchart LR
    subgraph Configs["1. Externalized Configs (Hot-Reload)"]
        ENV[".env & app_config.yaml<br/>(SETTINGS Singleton)"]
        PR["configs/prompts/*.yaml<br/>(System & User Prompts)"]
        KB["configs/domains/<domain>/<br/>(60 Runbooks + 60 Prod Incidents)"]
    end

    subgraph Engine["2. Modular Python Engine (engine/)"]
        UCL["UseCaseLoader<br/>(6 Enterprise Domain Profiles)"]
        MR["ModelRouter<br/>(Offline Qwen-1.5B + Cloud Toggle)"]
        QD["QdrantStore<br/>(Persistent Disk Vector DB + Filters)"]
        DBG["TraceDebugger & Quiz<br/>(Breakpoints, OTel & Assessments)"]
        VIZ["StoryVisualizer<br/>(Inline HTML X-Ray Storyboards)"]
    end

    subgraph LocalAI["3. Local Offline Runtime (Default)"]
        QW["Qwen2.5-Coder-1.5B-Instruct<br/>(models/qwen2.5-coder-1.5b)"]
        API["FastAPI + Gradio Console<br/>(http://127.0.0.1:8000/ui)"]
        PH["Arize Phoenix UI<br/>(http://127.0.0.1:6008)"]
    end

    subgraph CloudAI["4. Cloud Parity (ENABLE_VERTEX_AI=false)"]
        GEM["google-genai / OpenAI SDK<br/>(Opt-In Guarded Parity)"]
    end

    ENV --> UCL
    PR --> MR
    KB --> UCL --> QD
    QD --> MR
    MR --> QW
    MR -.->|Toggle True| GEM
    MR --> DBG
    DBG --> VIZ
    DBG -.->|OTel Trace| PH
    MR --> API

```

### 2. Live Step-Through Debugging & Storyboard Flow

```
sequenceDiagram
    autonumber
    actor Engineer
    participant NB as Day 01-10 Notebook / UI
    participant CFG as SETTINGS, PromptRegistry & Domain
    participant QD as QdrantStore (Local Disk)
    participant DBG as TraceDebugger & Visualizer
    participant QW as Local Qwen2.5-Coder-1.5B

    Engineer->>NB: Select ACTIVE_DOMAIN & INCIDENT_INDEX (0..9)
    NB->>CFG: Load Domain Incident & Hot-Reload YAML Prompt
    NB->>QD: Semantic Vector Search + Metadata Filter
    QD-->>DBG: Top-K Runbooks + Cosine Scores
    opt debug_mode = True (Live Breakpoint)
        DBG-->>Engineer: Pause & Inspect/Edit Hydrated Prompt
    end
    DBG->>QW: Offline Inference (HF_HUB_OFFLINE=1)
    QW-->>DBG: Structured JSON / Triage Output
    DBG-->>NB: Render Inline HTML X-Ray Storyboard & Quiz

```

## 📂 Repository Structure

```
aiml_rpd/
├── app/
│   └── main.py                         # FastAPI microservice + Gradio UI (/ui) + A2A v1.0 & RLM endpoints
├── configs/
│   ├── app_config.yaml                 # Non-secret default endpoints, paths, and feature flags
│   ├── prompts/                        # Externalized YAML system prompts (hot-reloaded on cell run)
│   │   ├── day03_summarizer.yaml
│   │   ├── day04_json_extractor.yaml
│   │   ├── day05_rag_grounded.yaml
│   │   ├── day08_react_agent.yaml
│   │   └── day09_judge_eval.yaml
│   └── domains/                        # 6 plug-and-play enterprise domains (60 runbooks + 60 incidents)
│       ├── sre_finops/                 # Kubernetes OOM, BigQuery FinOps, PgBouncer, Kafka, Cloud NAT
│       ├── cicd_devops/                # Gradle/NexusRM, Aqua Scan CVEs, SonarQube, Harness rollbacks
│       ├── payment_ops/                # ISO 8583 reversals, idempotency, Spanner hotspots, PCI leaks
│       ├── iam_servicedesk/            # SAML clock skew, OAuth2 refresh loops, AD lockouts, STS
│       ├── cloud_finops/               # JVM cgroup limits, CFS throttling, orphaned SSDs, idle GPUs
│       └── api_gateway/                # HTTP 429 bursts, circuit breakers, gRPC deadlines, mTLS certs
├── engine/
│   ├── __init__.py
│   ├── settings.py                     # Centralized .env + app_config.yaml loader (SETTINGS)
│   ├── use_case_loader.py              # Dynamic multi-domain profile loader
│   ├── router.py                       # Offline ModelRouter + LocalEmbedder + guarded cloud toggles
│   ├── qdrant_store.py                 # Local persistent Qdrant client + payload filtering
│   ├── prompts.py                      # Disk hot-reloading PromptRegistry
│   ├── visualizer.py                   # Inline HTML/SVG X-Ray Pipeline Storyboard renderer
│   ├── debugger.py                     # Step-through TraceDebugger + Arize Phoenix OTel exporter
│   ├── quiz_helper.py                  # Interactive inline self-assessment questionnaire renderer
│   └── a2a_skills.py                   # A2A v1.0 Agent Card & Recursive Language Model (RLM) scanner
├── notebooks/                          # 10 progressive notebooks with X-Ray visuals & self-assessments
│   ├── day01_classical_baseline.ipynb
│   ├── day02_embeddings_mechanics.ipynb
│   ├── day03_llm_inference_engineering.ipynb
│   ├── day04_structured_outputs_tools.ipynb
│   ├── day05_rag_core.ipynb
│   ├── day06_advanced_rag_reranking.ipynb
│   ├── day07_peft_qlora_finetuning.ipynb
│   ├── day08_agentic_workflows.ipynb
│   ├── day09_evals_guardrails.ipynb
│   └── day10_production_deployment.ipynb
├── scripts/
│   └── scaffold_domain.py              # CLI scaffolder to generate custom domain runbooks & incidents
├── tests/
│   └── test_all_domains.py             # Full-repository pytest suite validating all 60 incidents
├── models/                             # Git-ignored local flat model weights (Qwen + BGE)
├── qdrant_local_db/                    # Git-ignored persistent local Qdrant storage
├── .env.example                        # Template for local environment & URL overrides
├── run_local.ps1                       # Windows one-click bootstrap, pytest gate, and server launcher
├── run_local.sh                        # Linux/macOS launcher script
├── WINDOWS_SETUP.md                    # Step-by-step fresh Windows workstation setup guide
├── CUSTOM_USE_CASE_GUIDE.md            # Bring Your Own Use Case (BYOUC) scaffolding guide
├── WORKSHOP_SLIDES.md                  # Workshop slide deck & architecture walkthrough
├── WORKSHOP_GUIDELINE.md               # Facilitator runbook & pacing guide
├── requirements.txt
├── LICENSE
└── README.md

```

## 🌐 Dynamic Multi-Domain Profiles & BYOUC

Every notebook (`day01`–`day10`), `pytest` suite, and the Gradio/FastAPI console dynamically adapts to **6 enterprise domains** via `BOOTCAMP_DOMAIN` in `.env` or `ACTIVE_DOMAIN` in Cell 1:

* **`sre_finops` (Default):** GKE `OOMKilled`, BigQuery scan spikes, PgBouncer pool exhaustion, Kafka rebalance storms, Cloud NAT port exhaustion.

* **`cicd_devops`:** Gradle/NexusRM timeouts, 403 registry auth, Aqua Scan critical CVEs, SonarQube gates, Harness canary rollbacks.

* **`payment_ops`:** Duplicate idempotency keys, ISO 8583 code 91 reversals, Cloud Spanner hotspots, Kafka settlement lag, PCI token leaks.

* **`iam_servicedesk`:** SAML NTP clock skew, OAuth2 refresh loops, AD account lockouts, STS `AssumeRole`, social-engineering prompt injections.

* **`cloud_finops`:** JVM cgroup limits, CFS CPU throttling, orphaned SSDs, idle GPU node pools, cross-AZ Kafka egress.

* **`api_gateway`:** HTTP 429 bursts, Resilience4j circuit breakers, Jackson schema drift, gRPC deadlines, Istio SPIFFE mTLS cert expiry.

* **Bring Your Own Use Case (BYOUC):** Scaffold your own custom domain in seconds (`python scripts/scaffold_domain.py --domain my_domain --prefix MY-`) using the [Custom Use Case Guide](CUSTOM_USE_CASE_GUIDE.md).

## 1. Quickstart & Local Setup

* **Windows Workstation Setup:** Follow the step-by-step [Windows Local Setup & Verification Guide](WINDOWS_SETUP.md) to bootstrap `.venv`, provision offline model weights, configure `.env`, run `pytest` across all 60 scenarios, and launch the FastAPI/Gradio console + Arize Phoenix UI (`.\run_local.ps1`).

* **One-Click Windows Launcher:**

  ```
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\run_local.ps1
  
  ```

* **Workshop Slide Deck & Facilitator Guide:** See [WORKSHOP_SLIDES.md](WORKSHOP_SLIDES.md) and [WORKSHOP_GUIDELINE.md](WORKSHOP_GUIDELINE.md).

## 2. Live Debugging, Visualization & Self-Assessment Guide

Every notebook includes built-in visual storytelling, interactive debugging, and active learning checkpoints:

1. **Switch Across Domains & 10 Production Incidents (`Cell 1` & `Cell 2`):**
   Set `ACTIVE_DOMAIN = "cicd_devops"` (or leave default from `.env`) in **Cell 1**, and change `INCIDENT_INDEX = 0` to any integer from `0` to `9` in **Cell 2** to test real-world failure modes—including red-herring telemetry (`index 2`) and prompt-injection + leaked token payloads (`index 5`).

2. **Hot-Reload Externalized System Prompts (`configs/prompts/*.yaml`):**

   * Open any YAML file under `configs/prompts/` (e.g., `configs/prompts/day05_rag_grounded.yaml`).

   * Edit `system_prompt`, `temperature`, or `max_tokens` and save the file.

   * Re-run **Cell 4** (`Shift + Enter`)—`PromptRegistry` reads directly from disk on every execution without needing a kernel restart.

3. **Inspect the Inline HTML X-Ray Storyboard (`Cell 4 Output`):**
   Below Cell 4, `StoryVisualizer` renders a visual flow diagram showing:

   * **Input Incident Metadata & Raw Logs**

   * **Qdrant Retrieval Matches & Cosine Similarity Progress Bars**

   * **Exact Hydrated System + User Prompt Sent to Qwen**

   * **Model Latency (ms) & Structured JSON Output**

4. **Step-Through Snapshot Inspection & Live Breakpoints (`TraceDebugger`):**

   * Inspect stage payloads anytime:

     ```
     dbg.inspect("qdrant_retrieval")   # Inspect exact retrieved documents & scores
     dbg.inspect("llm_generation")     # Inspect exact prompt & raw model response
     
     ```

   * Set `dbg = TraceDebugger(debug_mode=True)` in **Cell 1** to pause execution right before LLM inference and inspect/approve the hydrated prompt.

5. **Interactive Self-Assessments & Lab Challenges (`Cells 7–9`):**
   Each notebook concludes with a hands-on modification challenge and a 3-question interactive architecture quiz (`render_quiz(...)`) with instant inline feedback.

6. **Arize Phoenix Web UI (`http://127.0.0.1:6008`):**
   Launched automatically by `.\run_local.ps1` (or manually via `$env:PHOENIX_PORT="6008"; phoenix serve`) to inspect OpenTelemetry trace waterfalls, latency spans, and guardrail events.

## 3. Local Deployment Guide (FastAPI + Gradio + A2A v1.0)

Start the production microservice and interactive web console on `http://127.0.0.1:8000`:

1. **Launch via Uvicorn (or `.\run_local.ps1`):**

   ```
   cd C:\python\ai_solutions\aiml_rpd
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   
   ```

2. **Live Endpoints:**

   * **Interactive Gradio Console:** `http://127.0.0.1:8000/ui` (switch domains, select incident presets, and run live triage)

   * **Interactive Swagger API Docs:** `http://127.0.0.1:8000/docs`

   * **A2A v1.0 Agent Discovery Card:** `http://127.0.0.1:8000/.well-known/agent-card.json`

3. **Send a Live `POST /v1/triage` Request via PowerShell:**

   ```
   $body = @{
       domain = "sre_finops"
       incident_id = "INC-LIVE-99"
       raw_log = "ALERT [P1]: gke-prod-payments checkout-api OOMKilled exit code 137"
   } | ConvertTo-Json
   
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/triage" -Method Post -ContentType "application/json" -Body $body
   
   ```

## 4. Testing & Validation Guide (Point-to-Point)

Run these checks to verify offline readiness, multi-domain regression gates, and API health:

1. **Run Full-Repository Multi-Domain `pytest` Suite (All 60 Incidents):**

   ```
   cd C:\python\ai_solutions\aiml_rpd
   .\.venv\Scripts\Activate.ps1
   pytest -v
   
   ```

2. **Run Day-by-Day Automated Validation Gates (`Cell 6` in Every Notebook):**
   Execute **Cell 6** in each notebook (`day01` through `day10`). Every notebook includes deterministic `assert` gates validating schema keys, Qdrant retrieval relevance, guardrail redaction, and latency thresholds, printing `[PASS]` on success.

3. **Optional GCP Vertex AI / OpenAI Parity Check (`ENABLE_VERTEX_AI=false` by Default):**
   Cloud calls are disabled by default across `.env` and all notebooks. When you are ready to compare local Qwen output against GCP Gemini:

   ```
   gcloud auth application-default login
   $env:GOOGLE_CLOUD_PROJECT = "your-gcp-project-id"
   
   ```

   Then set `ENABLE_VERTEX_AI = True` in **Cell 1** (or `ENABLE_VERTEX_AI=true` in `.env`) and run **Cell 5**.

## 📅 10-Day Curriculum Overview

| Day | Notebook | Core Concept | Hands-On Deliverable | 
| ----- | ----- | ----- | ----- | 
| **01** | `day01_classical_baseline.ipynb` | Classical ML Baseline | `TF-IDF + LogisticRegression` severity classifier & latency floor | 
| **02** | `day02_embeddings_mechanics.ipynb` | Vector Embeddings & Qdrant | L2-normalized dense embeddings & Qdrant metadata-filtered search | 
| **03** | `day03_llm_inference_engineering.ipynb` | Local LLM Inference | Deterministic vs. sampled local `Qwen2.5-Coder-1.5B` benchmarking | 
| **04** | `day04_structured_outputs_tools.ipynb` | Structured JSON & Tools | Pydantic schema extraction + Python runbook lookup tool | 
| **05** | `day05_rag_core.ipynb` | Grounded RAG Pipeline | End-to-end Qdrant retrieval + YAML-prompted Qwen synthesis | 
| **06** | `day06_advanced_rag_reranking.ipynb` | Hybrid Reranking | Dense + lexical fusion reranking to defeat red-herring logs (`index 2`) | 
| **07** | `day07_peft_qlora_finetuning.ipynb` | PEFT / LoRA Mechanics | Instruction dataset builder & LoRA rank/parameter reduction simulation | 
| **08** | `day08_agentic_workflows.ipynb` | Multi-Step ReAct Agent | Autonomous tool-routing loop (`fetch_metrics` → `search_qdrant` → `Qwen`) | 
| **09** | `day09_evals_guardrails.ipynb` | Evals & Security Guardrails | Token/PII redaction, prompt-injection defense (`index 5`) & faithfulness eval | 
| **10** | `day10_production_deployment.ipynb` | Production Microservice | FastAPI `/v1/triage` service + automated `TestClient` validation | 

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.