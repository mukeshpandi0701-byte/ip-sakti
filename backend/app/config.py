import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("IP_SAKTI_APP_NAME", "IP-SAKTI API")
    environment: str = os.getenv("IP_SAKTI_ENVIRONMENT", "development")
    frontend_origin: str = os.getenv("IP_SAKTI_FRONTEND_ORIGIN", "http://localhost:5173")
    llm_provider: str = os.getenv("IP_SAKTI_LLM_PROVIDER", "ollama")
    ollama_base_url: str = os.getenv("IP_SAKTI_OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("IP_SAKTI_OLLAMA_MODEL", "qwen3:8b")
    retrieval_limit: int = int(os.getenv("IP_SAKTI_RETRIEVAL_LIMIT", "3"))
    ollama_timeout_seconds: float = float(os.getenv("IP_SAKTI_OLLAMA_TIMEOUT_SECONDS", "60"))


settings = Settings()
