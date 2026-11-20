import shutil
from pathlib import Path

DIRS = [
    "engine",
    "notebooks",
    "solutions",
    "data/default_finops_incidents",
    "data/custom_user_data",
    ".cache/huggingface",
]

NOTEBOOK_NAMES = [
    "day01_classical_baseline.ipynb",
    "day02_embeddings_mechanics.ipynb",
    "day03_llm_inference_engineering.ipynb",
    "day04_structured_outputs_tools.ipynb",
    "day05_rag_core.ipynb",
    "day06_advanced_rag_reranking.ipynb",
    "day07_peft_qlora_finetuning.ipynb",
    "day08_agentic_workflows.ipynb",
    "day09_evals_guardrails.ipynb",
    "day10_production_deployment.ipynb",
]

def scaffold_repository(template_path: str = "template_module.ipynb"):
    for d in DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)

    if Path(template_path).exists():
        for nb in NOTEBOOK_NAMES:
            target = Path("notebooks") / nb
            if not target.exists():
                shutil.copy(template_path, target)

    env_example = Path(".env.example")
    if not env_example.exists():
        env_example.write_text(
            "GOOGLE_CLOUD_PROJECT=your-gcp-project-id\n"
            "GOOGLE_CLOUD_LOCATION=us-central1\n"
            "HOST_HF_CACHE=./.cache/huggingface\n",
            encoding="utf-8",
        )
    print("[Success] Bootcamp folder structure and 10 notebooks scaffolded.")

if __name__ == "__main__":
    scaffold_repository()
