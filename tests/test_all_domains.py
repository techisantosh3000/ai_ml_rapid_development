import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine import PromptRegistry, QdrantVectorStore, UseCaseLoader
from app.main import sanitize_log

ALL_DOMAINS = [
    "sre_finops",
    "cicd_devops",
    "payment_ops",
    "iam_servicedesk",
    "cloud_finops",
    "api_gateway",
]


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_domain_dataset_integrity(domain):
    loader = UseCaseLoader(domain=domain)
    runbooks = loader.load_runbooks()
    incidents = loader.load_incidents()
    assert len(runbooks) == 10, f"{domain} should have 10 runbooks"
    assert len(incidents) == 10, f"{domain} should have 10 incidents"
    rb_ids = {r["metadata"]["runbook_id"] for r in runbooks}
    for inc in incidents:
        assert inc["expected_runbook"] in rb_ids, f"{inc['incident_id']} expected_runbook missing"


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_qdrant_retrieval_and_guardrails_across_all_60_incidents(domain, tmp_path):
    loader = UseCaseLoader(domain=domain)
    runbooks = loader.load_runbooks()
    incidents = loader.load_incidents()

    qdrant = QdrantVectorStore(
        collection_name=f"test_{domain}",
        path=str(tmp_path / f"qdrant_{domain}"),
    )
    qdrant.upsert_documents(runbooks)

    for inc in incidents:
        guard = sanitize_log(inc["raw_log"])
        if inc["incident_id"].endswith("-006"):
            assert guard["injection_blocked"] is True
            assert "[REDACTED_HF_TOKEN]" in guard["sanitized_log"]
            assert "[REDACTED_IP]" in guard["sanitized_log"]

        # Verify metadata-filtered retrieval isolates exact expected runbook
        hits = qdrant.search(
            query=guard["sanitized_log"],
            top_k=2,
            metadata_filter={"category": inc["category"]},
        )
        assert len(hits) >= 1
        retrieved_ids = [h["metadata"]["runbook_id"] for h in hits]
        assert inc["expected_runbook"] in retrieved_ids, (
            f"[{domain}] {inc['incident_id']} expected {inc['expected_runbook']}, got {retrieved_ids}"
        )


def test_externalized_yaml_prompts_load_cleanly():
    reg = PromptRegistry()
    for name in ["day03_summarizer", "day04_json_extractor", "day05_rag_grounded", "day08_react_agent"]:
        cfg = reg.load(name)
        assert "system_prompt" in cfg and "user_template" in cfg
