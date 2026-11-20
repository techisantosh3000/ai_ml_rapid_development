# Workshop Facilitator Guideline & Execution Plan

## 1. What Can Be Achieved (Realistic 1-Day Scope)
Do **not** rewrite your working 10-notebook foundation overnight. Instead, add thin, high-impact wrappers around what you already verified today:
1. **Drop-In Engine Extensions (`engine/router.py` & `engine/a2a_skills.py`):**
   * Add `OpenAI` provider support with static-prefix **Prompt Caching** notes alongside `local_hf` and `vertex_gemini`.
   * Expose an **A2A v1.0 Agent Card** endpoint (`GET /.well-known/agent-card.json`) and a **Recursive Language Model (RLM)** log-chunking demo function.
2. **Slide Deck Ready to Present (`WORKSHOP_SLIDES.md`):**
   * Covers every feedback topic: Skills, MCP vs. A2A v1.0, Tool Calling Cost/Benefit/Drawbacks, SLM vs. LLM, Deterministic vs. Non-Deterministic scripts, Dependency Management, Prompt Caching, RLM, Agent Patterns, GCP/AWS deployment, and Slingshot workflow integration.
3. **Live Demo Flow (Zero Risk):**
   * Run **Day 5 / Day 8 / Day 9** notebooks + **FastAPI/Gradio UI (`http://127.0.0.1:8000/ui`)** + **Arize Phoenix (`http://127.0.0.1:6008`)** side-by-side.

---

## 2. Pre-Workshop Checklist (30 Minutes Before Session)
- [ ] **Terminal 1 (Arize Phoenix Observability):**
  ```powershell
  cd C:\python\ai_solutions\aiml_rpd
  .\.venv\Scripts\Activate.ps1
  $env:PHOENIX_PORT = "6008"
  $env:PHOENIX_GRPC_PORT = "14317"
  phoenix serve
  ```
- [ ] **Terminal 2 (FastAPI + Gradio Console):**
  ```powershell
  cd C:\python\ai_solutions\aiml_rpd
  .\.venv\Scripts\Activate.ps1
  uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```
- [ ] **Browser Tabs Open:**
  1. `http://127.0.0.1:8000/ui` (Gradio Incident Triage Console)
  2. `http://127.0.0.1:8000/docs` (FastAPI Swagger + A2A Agent Card)
  3. `http://127.0.0.1:6008` (Arize Phoenix Trace Waterfall)
  4. Jupyter / VS Code with `day05_rag_core.ipynb` and `day09_evals_guardrails.ipynb` pre-run once so model weights are warm in RAM.

---

## 3. Live Q&A Cheat Sheet for Reviewer Feedback
* **"How are you handling dependency management?"**
  * Isolated `.venv` locked with `requirements.txt`, offline Hugging Face cache locks (`HF_HUB_OFFLINE=1`), and identical container `Dockerfile` builds for local Docker/Rancher Desktop, GCP Cloud Run, and AWS ECS.
* **"Deterministic vs. Non-Deterministic scripts?"**
  * Guardrails (regex PII/token redaction), Qdrant metadata filters, and Pydantic schema validation are **100% deterministic**. Only root-cause summarization and remediation synthesis use the probabilistic SLM/LLM.
* **"Why SLM locally, and how do OpenAI / GCP / AWS fit?"**
  * `ModelRouter` abstracts the inference backend: default is local `Qwen2.5-Coder-1.5B` (zero token cost, air-gapped privacy), while flipping `ENABLE_VERTEX_AI=True` or `ENABLE_OPENAI=True` switches seamlessly to GCP Vertex AI or OpenAI (with static-prefix Prompt Caching) or AWS Bedrock/ECS for cloud scale.
* **"How does Slingshot / Workflow integration help?"**
  * Our FastAPI service exposes clean REST + A2A v1.0 Agent Card contracts so workflow orchestrators like Slingshot can trigger `/v1/triage` from incoming PagerDuty/Slack events, enforce Human-in-the-Loop approvals for `P1` actions, and close tickets automatically.
