# Production AI/ML Engineering Bootcamp & Multi-Domain Incident Triage (`aiml_rpd`)

A modular, offline-first AI/ML Engineering Bootcamp and production incident triage platform powered by local **Qwen2.5-Coder-1.5B** (SLM), **Qdrant** vector storage, **Arize Phoenix** OpenTelemetry tracing, **FastAPI**, and **Gradio**.

Designed to run 100% locally on Windows workstations with zero cloud dependencies by default, while preserving clean opt-in parity for **GCP Vertex AI**, **OpenAI**, and **A2A v1.0** multi-agent workflows.

---

## Fresh Windows Machine Setup Guide

Follow these steps after cloning the repository onto a brand-new Windows machine (`git clone <your-repo-url>`).

### Prerequisites
* **OS:** Windows 10 / 11 (x64)
* **Python:** Python 3.11+ (3.11–3.13 recommended for prebuilt PyTorch/Qdrant wheels)
* **Git** and **PowerShell 5.1+**

---

### Step 1: Clone & Bootstrap `.venv` + Dependencies
Open PowerShell, clone the repository, and run the automated PowerShell bootstrapper with `-InstallDeps` and `-SkipTests` (we will run tests right after placing the local model weights):

```powershell
git clone <your-repo-url> aiml_rpd
cd aiml_rpd

# Allow local script execution for this PowerShell session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Creates .env from .env.example, initializes .venv, and installs requirements.txt
.\run_local.ps1 -InstallDeps -SkipTests
```
*(Press `Ctrl+C` once dependency installation finishes and the server starts, so you can place the offline model weights in Step 2.)*

---

### Step 2: Provision Offline Model Weights (`models/`)
Large model weight files (`models/`) are excluded via `.gitignore` so the Git repository stays fast and lightweight. Provision the local weights using **either** option below:

#### Option A: Fast USB / External SSD Transfer (100% Air-Gapped / Workshop Mode)
Copy your pre-downloaded `models\` directory from your primary workstation onto a USB 3.1 drive and paste it into the repository root so the structure matches:
```text
aiml_rpd\
└── models\
    ├── qwen2.5-coder-1.5b\
    └── bge-small-en-v1.5\
```

#### Option B: One-Time Download from Hugging Face (Requires Internet)
```powershell
.\.venv\Scripts\Activate.ps1
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct --local-dir .\models\qwen2.5-coder-1.5b
huggingface-cli download BAAI/bge-small-en-v1.5 --local-dir .\models\bge-small-en-v1.5
```

---

### Step 3: Verify `.env` Configuration
`run_local.ps1` automatically copies `.env.example` to `.env` on first run. Open `.env` in your repository root and confirm the relative paths and local ports match your setup:

```env
# Active Enterprise Domain Profile:
# Options: sre_finops | cicd_devops | payment_ops | iam_servicedesk | cloud_finops | api_gateway
BOOTCAMP_DOMAIN=sre_finops

# Local Observability & Microservice Endpoints
PHOENIX_UI_URL=http://127.0.0.1:6008
PHOENIX_ENDPOINT=http://127.0.0.1:6008/v1/traces
API_BASE_URL=http://127.0.0.1:8000
OPS_WEBHOOK_BASE_URL=https://ops.internal/trigger

# Local Storage & Offline Model Paths
QDRANT_DB_PATH=.\qdrant_local_db
LOCAL_MODEL_PATH=.\models\qwen2.5-coder-1.5b
LOCAL_EMBED_PATH=.\models\bge-small-en-v1.5

# Cloud Parity Toggles (Keep false for offline local execution)
ENABLE_VERTEX_AI=false
ENABLE_OPENAI=false
```

---

### Step 4: Register the Jupyter Kernel (For VS Code / Jupyter Notebooks)
Register your `.venv` as a named Jupyter kernel so all 10 notebooks (`notebooks/day01` – `day10`) use the isolated dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m ipykernel install --user --name=aiml-rpd --display-name "Python (aiml-rpd .venv)"
```

---

### Step 5: Run Automated Regression Tests & Launch All Services
Run `.\run_local.ps1` with no flags. It will:
1. Validate `SETTINGS` and confirm `models\qwen2.5-coder-1.5b` is present on disk.
2. Execute `pytest -q` across **all 6 enterprise domains (60 runbooks & 60 production incidents)**.
3. Spawn **Arize Phoenix** (`http://127.0.0.1:6008`) in a dedicated PowerShell window.
4. Launch the **FastAPI + Gradio Console** (`http://127.0.0.1:8000/ui`).

```powershell
.\run_local.ps1
```

#### Useful Launcher Flags
```powershell
# Launch directly into a specific enterprise domain profile
.\run_local.ps1 -Domain cicd_devops

# Fast startup (skip pytest regression gate)
.\run_local.ps1 -SkipTests
```

---

## Live Endpoints & Dashboards

Once `.\run_local.ps1` is running, open the following local URLs:

| Service | URL | Purpose |
| :--- | :--- | :--- |
| **Gradio Interactive Console** | `http://127.0.0.1:8000/ui` | Switch across all 6 enterprise domains, pick incident presets, and inspect live triage outputs. |
| **Arize Phoenix Tracing UI** | `http://127.0.0.1:6008` | Inspect OpenTelemetry span waterfalls (`GUARDRAIL` → `RETRIEVER` → `LLM` → `TOOL`). |
| **FastAPI Swagger Docs** | `http://127.0.0.1:8000/docs` | Test `POST /v1/triage`, `POST /v1/rlm-scan`, and `GET /health` interactively. |
| **A2A v1.0 Agent Card** | `http://127.0.0.1:8000/.well-known/agent-card.json` | Machine-readable Agent-to-Agent discovery manifest advertising declared skills. |

---

## Repository Architecture

```text
aiml_rpd/
├── app/
│   └── main.py                  # FastAPI microservice + Gradio UI (/ui) + A2A v1.0 & RLM endpoints
├── configs/
│   ├── app_config.yaml          # Non-secret default endpoints, paths, and feature flags
│   ├── prompts/                 # Hot-reloaded YAML prompt templates (Days 3, 4, 5, 8, 9)
│   └── domains/                 # 6 plug-and-play enterprise domains (60 runbooks + 60 incidents)
│       ├── sre_finops/          # Kubernetes OOM, BigQuery FinOps, PgBouncer, Kafka, Cloud NAT
│       ├── cicd_devops/         # Gradle/NexusRM, Aqua Scan CVEs, SonarQube, Harness rollbacks
│       ├── payment_ops/         # ISO 8583 reversals, idempotency, Spanner hotspots, PCI leaks
│       ├── iam_servicedesk/     # SAML clock skew, OAuth2 refresh loops, AD lockouts, STS
│       ├── cloud_finops/        # JVM cgroup limits, CFS throttling, orphaned SSDs, idle GPUs
│       └── api_gateway/         # HTTP 429 bursts, circuit breakers, gRPC deadlines, mTLS certs
├── engine/
│   ├── settings.py              # Centralized .env + app_config.yaml loader
│   ├── router.py                # Local Qwen2.5-Coder-1.5B + guarded Vertex AI / OpenAI router
│   ├── qdrant_store.py          # Embedded Qdrant vector store with metadata payload filtering
│   ├── use_case_loader.py       # Dynamic multi-domain loader
│   ├── debugger.py              # Step-through debugger + Arize Phoenix OTel span exporter
│   ├── visualizer.py            # Inline HTML/SVG X-Ray Pipeline Storyboard renderer
│   └── a2a_skills.py            # A2A v1.0 Agent Card & Recursive Language Model (RLM) scanner
├── notebooks/                   # 10 progressive hands-on notebooks (day01 through day10)
├── tests/
│   └── test_all_domains.py      # Full-repository pytest suite validating all 60 incidents
├── .env.example                 # Template for local environment overrides
├── .gitignore                   # Excludes .venv/, models/, qdrant_local_db/, and .env
├── requirements.txt             # Complete pinned dependency manifest
├── run_local.ps1                # Windows one-click bootstrap, test, and server launcher
└── WORKSHOP_SLIDES.md           # Workshop slide deck & facilitator runbook
```

---

## Windows Troubleshooting Checklist

* **PowerShell Execution Policy Blocked (`cannot be loaded because running scripts is disabled`):**
  Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your current PowerShell terminal before calling `.\run_local.ps1`.
* **Arize Phoenix Port Conflict (`Failed to bind to address 127.0.0.1:14317` or `6008`):**
  Ensure only one Phoenix window is running and keep `enable_phoenix=False` inside Jupyter notebooks (`Cell 1`) so notebooks stream traces to the standalone Phoenix process rather than spawning a duplicate server.
* **Qdrant Local Folder Lock (`Storage folder ./qdrant_local_db is already accessed by another instance`):**
  Embedded Qdrant uses a single-process file lock on `./qdrant_local_db`. Stop the FastAPI server (`Ctrl+C`) before running notebooks that point to the same `./qdrant_local_db` directory, or point notebooks to `../qdrant_local_db`.