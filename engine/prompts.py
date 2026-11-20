import json
import re
from pathlib import Path
from typing import Any, Dict, List

class PromptRegistry:
    """Hot-reloading external prompt manager reading YAML/JSON prompt files from configs/prompts/."""
    def __init__(self, prompts_dir: str = "../configs/prompts"):
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            self.prompts_dir = Path("configs/prompts")

    def load(self, prompt_name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reads prompt config fresh from disk on every call so live edits take effect immediately."""
        yaml_path = self.prompts_dir / f"{prompt_name}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Prompt config not found: {yaml_path}")

        raw_text = yaml_path.read_text(encoding="utf-8")
        try:
            import yaml
            cfg = yaml.safe_load(raw_text)
        except ImportError:
            # Zero-dependency fallback parser for simple key: value YAML
            cfg = {}
            current_key = None
            buf = []
            for line in raw_text.splitlines():
                if re.match(r"^[a-zA-Z0-9_]+:\s*\|?$", line):
                    if current_key:
                        cfg[current_key] = "\n".join(buf).strip()
                    current_key = line.split(":")[0].strip()
                    buf = []
                elif re.match(r"^[a-zA-Z0-9_]+:\s+.+$", line) and not line.startswith(" "):
                    if current_key:
                        cfg[current_key] = "\n".join(buf).strip()
                        current_key = None
                    k, v = line.split(":", 1)
                    v = v.strip().strip('"').strip("'")
                    try:
                        v = float(v) if "." in v else int(v)
                    except ValueError:
                        pass
                    cfg[k.strip()] = v
                elif current_key:
                    buf.append(line[2:] if line.startswith("  ") else line)
            if current_key:
                cfg[current_key] = "\n".join(buf).strip()

        if overrides:
            cfg.update(overrides)
        return cfg

    def render(self, template_str: str, **variables) -> str:
        rendered = template_str
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

class UseCaseLoader:
    """Loads externalized domain use cases, runbooks, and 10 real-world production incidents."""
    def __init__(self, configs_dir: str = "../configs"):
        self.base = Path(configs_dir)
        if not self.base.exists():
            self.base = Path("configs")

    def load_incidents(self) -> List[Dict[str, Any]]:
        path = self.base / "knowledge_base" / "incidents_prod_10.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def load_runbooks(self) -> List[Dict[str, Any]]:
        path = self.base / "knowledge_base" / "runbooks.json"
        return json.loads(path.read_text(encoding="utf-8"))
