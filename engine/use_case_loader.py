import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class UseCaseLoader:
    """
    Dynamic Domain-Agnostic Use Case Loader.
    Supports switching across all 6 enterprise domains (default SRE/FinOps + 5 new domains)
    without modifying any notebook or FastAPI code:
      - sre_finops    (default: configs/knowledge_base/runbooks.json & incidents_prod_10.json)
      - cicd_devops   (configs/domains/cicd_devops/...)
      - payment_ops   (configs/domains/payment_ops/...)
      - iam_servicedesk (configs/domains/iam_servicedesk/...)
      - cloud_finops  (configs/domains/cloud_finops/...)
      - api_gateway   (configs/domains/api_gateway/...)
    """

    SUPPORTED_DOMAINS = {
        "sre_finops": {
            "label": "Cloud SRE & FinOps Incident Triage (Default)",
            "collection_name": "sre_runbooks",
            "id_prefix": "RB-",
        },
        "cicd_devops": {
            "label": "CI/CD Build & Release Failure Triage (Harness/Gradle/Aqua)",
            "collection_name": "cicd_runbooks",
            "id_prefix": "CI-",
        },
        "payment_ops": {
            "label": "Banking & Payment Gateway Exception Triage (ISO8583/Kafka/Spanner)",
            "collection_name": "payment_runbooks",
            "id_prefix": "PAY-",
        },
        "iam_servicedesk": {
            "label": "Enterprise IT Service Desk & IAM Access Triage (Okta/SAML/RBAC)",
            "collection_name": "iam_runbooks",
            "id_prefix": "IAM-",
        },
        "cloud_finops": {
            "label": "Cloud FinOps & Kubernetes Capacity Optimization (GKE/EKS/GPU)",
            "collection_name": "finops_runbooks",
            "id_prefix": "FIN-",
        },
        "api_gateway": {
            "label": "API Gateway & Microservice Contract Drift Triage (Spring/Istio/gRPC)",
            "collection_name": "apigw_runbooks",
            "id_prefix": "API-",
        },
    }

    def __init__(self, configs_dir: Optional[str] = None, domain: Optional[str] = None):
        if configs_dir is None:
            repo_root = Path(__file__).resolve().parent.parent
            configs_dir = str(repo_root / "configs")
        self.configs_dir = Path(configs_dir)
        self.domain = (domain or os.getenv("BOOTCAMP_DOMAIN", "sre_finops")).strip().lower()
        if self.domain not in self.SUPPORTED_DOMAINS:
            raise ValueError(
                f"Unknown domain '{self.domain}'. Valid domains: {list(self.SUPPORTED_DOMAINS.keys())}"
            )

    @property
    def collection_name(self) -> str:
        return self.SUPPORTED_DOMAINS[self.domain]["collection_name"]

    @property
    def domain_label(self) -> str:
        return self.SUPPORTED_DOMAINS[self.domain]["label"]

    def list_domains(self) -> List[str]:
        return list(self.SUPPORTED_DOMAINS.keys())

    def _resolve_kb_dir(self) -> Path:
        if self.domain == "sre_finops":
            return self.configs_dir / "knowledge_base"
        return self.configs_dir / "domains" / self.domain

    def load_runbooks(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        if domain and domain != self.domain:
            self.domain = domain
        kb_dir = self._resolve_kb_dir()
        path = kb_dir / "runbooks.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_incidents(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        if domain and domain != self.domain:
            self.domain = domain
        kb_dir = self._resolve_kb_dir()
        # Preserve backwards compatibility with default incidents_prod_10.json
        default_path = kb_dir / "incidents_prod_10.json"
        alt_path = kb_dir / "incidents.json"
        target = default_path if default_path.exists() else alt_path
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
