# Fresh Windows Machine Setup & Verification Guide

Follow these steps after cloning the `aiml_rpd` repository onto a brand-new Windows machine (`git clone <your-repo-url>`).

---

## Prerequisites

* **OS:** Windows 10 / 11 (x64)
* **Python:** Python 3.11+ (3.11–3.13 recommended for prebuilt PyTorch and Qdrant wheels)
* **Tools:** Git and PowerShell 5.1+

---

## Step 1: Clone & Bootstrap `.venv` + Dependencies

Open PowerShell, clone the repository, and run the automated PowerShell bootstrapper with `-InstallDeps` and `-SkipTests` (we will run tests right after placing the offline model weights):

```powershell
git clone <your-repo-url> aiml_rpd
cd aiml_rpd

# Allow local script execution for this PowerShell session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Creates .env from .env.example, initializes .venv, and installs requirements.txt
.\run_local.ps1 -InstallDeps -SkipTests
```

*(Press `Ctrl+C` once dependency installation finishes and the server starts, so you can provision the offline model weights in Step 2.)*

---

## Step 2: Provision Offline Model Weights (`models/`)

Large model weight files (`models/`) are excluded via `.gitignore` so the Git repository stays fast and lightweight. Provision the local weights using **either** option below:

### Option A: Fast USB / External SSD Transfer (100% Air-Gapped / Workshop Mode)

Copy your pre-downloaded `models\` directory from your primary workstation onto a USB 3.1 drive and paste it into the repository root so the structure matches:

```text
aiml_rpd\
└── models\
    ├── qwen2.5-coder-1.5b\
    └── bge-small-en-v1.5\
```

### Option B: One-Time Download from Hugging Face (Requires Internet)

```powershell
.\.venv\Scripts\Activate.ps1
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct --local-dir .\models\qwen2.5-coder-1.5b
huggingface-cli download BAAI/bge-small-en-v1.5 --local-dir .\models\bge-small-en-v1.5
```

---

## Step 3: Verify `.env` Configuration

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

## Step 4: Register the Jupyter Kernel (For VS Code / Jupyter Notebooks)

Register your `.venv` as a named Jupyter kernel so all 10 notebooks (`notebooks/day01` – `day10`) execute inside the isolated environment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m ipykernel install --user --name=aiml-rpd --display-name "Python (aiml-rpd .venv)"
```

---

## Step 5: Run Automated Regression Tests & Launch All Services

Run `.\run_local.ps1` with no flags. It will:
1. Validate `SETTINGS` and confirm `models\qwen2.5-coder-1.5b` is present on disk.
2. Execute `pytest -q` across **all 6 enterprise domains (60 runbooks & 60 production incidents)**.
3. Spawn **Arize Phoenix** (`http://127.0.0.1:6008`) in a dedicated PowerShell window.
4. Launch the **FastAPI + Gradio Console** (`http://127.0.0.1:8000/ui`).

```powershell
.\run_local.ps1
```

### Useful Launcher Flags

```powershell
# Launch directly into a specific enterprise domain profile
.\run_local.ps1 -Domain cicd_devops

# Fast startup (skip pytest regression gate)
.\run_local.ps1 -SkipTests
```

---

## Live Endpoints & Dashboards

| Service | URL | Purpose |
| :--- | :--- | :--- |
| **Gradio Interactive Console** | `http://127.0.0.1:8000/ui` | Switch across all 6 enterprise domains, pick incident presets, and inspect live triage outputs. |
| **Arize Phoenix Tracing UI** | `http://127.0.0.1:6008` | Inspect OpenTelemetry span waterfalls (`GUARDRAIL` → `RETRIEVER` → `LLM` → `TOOL`). |
| **FastAPI Swagger Docs** | `http://127.0.0.1:8000/docs` | Test `POST /v1/triage`, `POST /v1/rlm-scan`, and `GET /health` interactively. |
| **A2A v1.0 Agent Card** | `http://127.0.0.1:8000/.well-known/agent-card.json` | Machine-readable Agent-to-Agent discovery manifest advertising declared skills. |

---

## Windows Troubleshooting Checklist

* **PowerShell Execution Policy Blocked (`cannot be loaded because running scripts is disabled`):**
  Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your current PowerShell terminal before calling `.\run_local.ps1`.
* **Arize Phoenix Port Conflict (`Failed to bind to address 127.0.0.1:14317` or `6008`):**
  Ensure only one Phoenix window is running and keep `enable_phoenix=False` inside Jupyter notebooks (`Cell 1`) so notebooks stream traces to the standalone Phoenix process rather than spawning a duplicate server.
* **Qdrant Local Folder Lock (`Storage folder ./qdrant_local_db is already accessed by another instance`):**
  Embedded Qdrant uses a single-process file lock on `./qdrant_local_db`. Stop the FastAPI server (`Ctrl+C`) before running notebooks that point to the same `./qdrant_local_db` directory, or point notebooks to `../qdrant_local_db`.