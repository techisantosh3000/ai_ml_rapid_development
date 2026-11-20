import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(dotenv_path: Path) -> None:
    """Lightweight .env loader (no external dependency required)."""
    if not dotenv_path.exists():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


class AppSettings:
    """
    Single Source of Truth for URLs, Endpoints, Paths, and Feature Flags.
    Precedence: Environment Variables (.env / OS env) > configs/app_config.yaml > Safe Defaults.
    """

    def __init__(self, config_path: Optional[str] = None):
        _load_dotenv(REPO_ROOT / ".env")
        cfg_file = Path(config_path) if config_path else (REPO_ROOT / "configs" / "app_config.yaml")
        raw_cfg: Dict[str, Any] = {}
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                raw_cfg = yaml.safe_load(f) or {}

        obs = raw_cfg.get("observability", {})
        models = raw_cfg.get("models", {})
        storage = raw_cfg.get("storage", {})
        service = raw_cfg.get("service", {})
        cloud = raw_cfg.get("cloud", {})

        # Observability (Arize Phoenix)
        self.phoenix_ui_url: str = os.getenv(
            "PHOENIX_UI_URL", obs.get("phoenix_ui_url", "http://127.0.0.1:6008")
        )
        self.phoenix_traces_endpoint: str = os.getenv(
            "PHOENIX_ENDPOINT",
            obs.get("phoenix_traces_endpoint", f"{self.phoenix_ui_url.rstrip('/')}/v1/traces"),
        )
        self.phoenix_project_name: str = os.getenv(
            "PHOENIX_PROJECT_NAME", obs.get("project_name", "sre-incident-bootcamp")
        )

        # Service & Webhook Endpoints
        self.api_base_url: str = os.getenv(
            "API_BASE_URL", service.get("api_base_url", "http://127.0.0.1:8000")
        )
        self.a2a_agent_url: str = os.getenv(
            "A2A_AGENT_URL", service.get("a2a_agent_url", f"{self.api_base_url.rstrip('/')}/a2a")
        )
        self.ops_webhook_base_url: str = os.getenv(
            "OPS_WEBHOOK_BASE_URL", service.get("ops_webhook_base_url", "https://ops.internal/trigger")
        )

        # Local Paths & Domain Selection
        self.active_domain: str = os.getenv(
            "BOOTCAMP_DOMAIN", storage.get("default_domain", "sre_finops")
        ).strip().lower()
        self.qdrant_db_path: str = os.getenv(
            "QDRANT_DB_PATH", str(REPO_ROOT / storage.get("qdrant_dir", "qdrant_local_db"))
        )
        self.local_model_path: str = os.getenv(
            "LOCAL_MODEL_PATH",
            models.get("local_slm_path", str(REPO_ROOT / "models" / "qwen2.5-coder-1.5b")),
        )
        self.local_embed_path: str = os.getenv(
            "LOCAL_EMBED_PATH",
            models.get("local_embed_path", str(REPO_ROOT / "models" / "bge-small-en-v1.5")),
        )

        # Guarded Cloud Flags (Strictly False by default)
        self.enable_vertex_ai: bool = (
            os.getenv("ENABLE_VERTEX_AI", str(cloud.get("enable_vertex_ai", False))).lower() == "true"
        )
        self.enable_openai: bool = (
            os.getenv("ENABLE_OPENAI", str(cloud.get("enable_openai", False))).lower() == "true"
        )
        self.gcp_project: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT") or cloud.get("gcp_project")
        self.gcp_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", cloud.get("gcp_location", "us-central1"))
        self.gcp_model: str = os.getenv("GCP_MODEL_ID", cloud.get("gcp_model", "gemini-2.5-flash"))
        self.openai_model: str = os.getenv("OPENAI_MODEL_ID", cloud.get("openai_model", "gpt-4o-mini"))


# Global singleton loaded cleanly on import
SETTINGS = AppSettings()
