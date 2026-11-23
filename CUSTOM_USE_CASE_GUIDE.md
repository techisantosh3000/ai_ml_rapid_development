# Bring Your Own Use Case (BYOUC) Guide

Because all 10 notebooks, `QdrantVectorStore`, `PromptRegistry`, `pytest`, and the FastAPI/Gradio console load data dynamically from `configs/`, you can plug in your own enterprise domain (e.g., **Supply Chain**, **Telecom NOC**, **Healthcare Claims**, **HR Operations**, or **Data Engineering**) in under 5 minutes without modifying any notebook code.

---

## Step 1: Scaffold Your Domain Files (30 Seconds)
Run the scaffolding CLI from `C:\python\ai_solutions\aiml_rpd`:

```powershell
cd C:\python\ai_solutions\aiml_rpd
.\.venv\Scripts\Activate.ps1
python scripts\scaffold_domain.py --domain supply_chain --prefix SCM-
```

This creates two starter JSON files with 10 runbooks and 10 incidents (including a Day 9 security/prompt-injection test case at index `5`):
* `configs/domains/supply_chain/runbooks.json`
* `configs/domains/supply_chain/incidents.json`

---

## Step 2: Register the Domain Key in `engine/use_case_loader.py`
Open `engine/use_case_loader.py` and add one entry to `UseCaseLoader.SUPPORTED_DOMAINS`:

```python
"supply_chain": {
    "label": "Supply Chain & Logistics Exception Triage",
    "collection_name": "supply_chain_runbooks",
    "id_prefix": "SCM-",
},
```

---

## Step 3: Customize Your Runbooks & Production Incidents
Edit `configs/domains/supply_chain/runbooks.json` and `incidents.json` with your real SOPs and log patterns:
1. **`runbooks.json` schema:**
   ```json
   {
     "id": 901,
     "text": "RB SCM-101 [Warehouse / WMS]: Carrier EDI 214 webhook timeout...",
     "metadata": {
       "runbook_id": "SCM-101",
       "category": "logistics",
       "service": "wms-edi-gateway",
       "severity": "P1"
     }
   }
   ```
2. **`incidents.json` schema:**
   ```json
   {
     "incident_id": "SCM-2026-001",
     "title": "Carrier EDI 214 Webhook Timeout",
     "severity": "P1",
     "category": "logistics",
     "service": "wms-edi-gateway",
     "expected_runbook": "SCM-101",
     "metrics": {"timeout_count": 42, "queue_lag": 1850},
     "raw_log": "2026-11-23T10:15:00Z ERROR wms-edi-gateway Carrier EDI 214 endpoint timed out..."
   }
   ```
   * **Pro Tip for Day 6 (Hybrid Reranking):** Make incident #3 (`index = 2`) a subtle edge case with a misleading nominal metric (e.g., `"CPU at 22%"`) so you can validate two-stage dense + lexical reranking.
   * **Pro Tip for Day 9 (Security Guardrails):** Keep incident #6 (`index = 5`) as a security test containing a mock `hf_...` token, IP address, and `"Ignore previous instructions..."` payload.

---

## Step 4: Activate & Validate Across All 10 Notebooks, `pytest` & Gradio UI
1. **In `.env` (Global Default):**
   ```env
   BOOTCAMP_DOMAIN=supply_chain
   ```
2. **Or in Cell 1 of Any Notebook (`day01` – `day10`):**
   ```python
   ACTIVE_DOMAIN = "supply_chain"
   ```
3. **Run Automated Validation (`pytest`):**
   Add `"supply_chain"` to `ALL_DOMAINS` in `tests/test_all_domains.py` and run `pytest -v`.
4. **Launch Interactive Console:**
   Run `.\run_local.ps1` and select `supply_chain` from the domain dropdown at `http://127.0.0.1:8000/ui`.
