import os
import json
import time
from typing import Any, Dict, List, Optional, Type
import numpy as np
from pydantic import BaseModel

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

DEFAULT_LOCAL_MODEL = r"C:\python\ai_solutions\aiml_rpd\models\qwen2.5-coder-1.5b"
DEFAULT_LOCAL_EMBED = r"C:\python\ai_solutions\aiml_rpd\models\bge-small-en-v1.5"

class LocalEmbedder:
    def __init__(self, model_path: str = DEFAULT_LOCAL_EMBED, dim: int = 128):
        self.dim = dim
        self._st_model = None
        self._vectorizer = None
        if os.path.isdir(model_path):
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(model_path, local_files_only=True)
            self.dim = self._st_model.get_sentence_embedding_dimension()
            self.backend = f"local_st ({os.path.basename(model_path)})"
        else:
            from sklearn.feature_extraction.text import HashingVectorizer
            self._vectorizer = HashingVectorizer(n_features=dim, alternate_sign=False, norm="l2")
            self.backend = "offline_hashing_dense (zero-download)"

    def encode(self, texts: List[str]) -> np.ndarray:
        if self._st_model is not None:
            return self._st_model.encode(texts, normalize_embeddings=True)
        mat = self._vectorizer.transform(texts).toarray().astype(np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
        return mat / norms

class ModelRouter:
    """
    Unified Multi-Provider Router:
      - Default: 'local_hf' (100% offline Qwen2.5-Coder-1.5B SLM)
      - Optional: 'vertex_gemini' (Guarded, False by default)
      - Optional: 'openai' (Guarded, supports automatic prefix Prompt Caching)
    """
    def __init__(
        self,
        local_model_path: str = DEFAULT_LOCAL_MODEL,
        enable_vertex: bool = False,
        enable_openai: bool = False,
        gcp_model: str = "gemini-2.5-flash",
        openai_model: str = "gpt-4o-mini"
    ):
        self.enable_vertex = enable_vertex
        self.enable_openai = enable_openai
        if enable_vertex:
            self.provider = "vertex_gemini"
        elif enable_openai:
            self.provider = "openai"
        else:
            self.provider = "local_hf"

        self.local_model_path = local_model_path
        self.gcp_model_id = gcp_model
        self.openai_model_id = openai_model
        self.gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.gcp_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self._hf_pipeline = None
        self._genai_client = None
        self._openai_client = None

    def _init_local_hf(self):
        if self._hf_pipeline is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        tokenizer = AutoTokenizer.from_pretrained(self.local_model_path, local_files_only=True)
        load_kwargs = {"device_map": "auto" if device != "cpu" else None}
        model = AutoModelForCausalLM.from_pretrained(self.local_model_path, local_files_only=True, **load_kwargs)
        self._hf_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

    def _init_vertex_gemini(self):
        if self._genai_client is not None:
            return
        from google import genai
        self._genai_client = genai.Client(vertexai=True, project=self.gcp_project, location=self.gcp_location)

    def _init_openai(self):
        if self._openai_client is not None:
            return
        from openai import OpenAI
        self._openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI engineer.",
        temperature: float = 0.1,
        max_tokens: int = 384,
        response_schema: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        sys_prompt = system_instruction
        cache_metrics = {"cached_tokens": 0, "prompt_caching_note": "Static prefix placed first for KV/Prompt Caching"}

        if self.provider == "local_hf":
            self._init_local_hf()
            if response_schema is not None:
                example_obj = {k: f"<{v.description or k}>" for k, v in response_schema.model_fields.items()}
                sys_prompt += (
                    "\nRespond ONLY with a valid JSON object using these exact keys:\n"
                    f"{json.dumps(example_obj, indent=2)}"
                )
            messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
            out = self._hf_pipeline(
                messages,
                max_new_tokens=max_tokens,
                temperature=max(temperature, 1e-4),
                do_sample=temperature > 0
            )
            text = out[0]["generated_text"][-1]["content"].strip()
            if response_schema is not None:
                s, e = text.find("{"), text.rfind("}")
                if s != -1 and e != -1:
                    text = text[s:e + 1]
            model_used = os.path.basename(self.local_model_path)

        elif self.provider == "openai":
            self._init_openai()
            # OpenAI automatically caches static system_instruction + static runbook prefixes > 1024 tokens
            resp = self._openai_client.chat.completions.create(
                model=self.openai_model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}],
            )
            text = resp.choices[0].message.content.strip()
            model_used = self.openai_model_id
            if getattr(resp, "usage", None) and getattr(resp.usage, "prompt_tokens_details", None):
                cache_metrics["cached_tokens"] = getattr(resp.usage.prompt_tokens_details, "cached_tokens", 0)

        else:
            self._init_vertex_gemini()
            from google.genai import types
            cfg = {"system_instruction": sys_prompt, "temperature": temperature, "max_output_tokens": max_tokens}
            if response_schema is not None:
                cfg["response_mime_type"] = "application/json"
                cfg["response_schema"] = response_schema
            resp = self._genai_client.models.generate_content(
                model=self.gcp_model_id,
                contents=prompt,
                config=types.GenerateContentConfig(**cfg)
            )
            text = resp.text.strip()
            model_used = self.gcp_model_id

        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "provider": self.provider,
            "model": model_used,
            "latency_ms": latency_ms,
            "system_prompt_used": sys_prompt,
            "user_prompt_used": prompt,
            "cache_metrics": cache_metrics,
            "output": text
        }
