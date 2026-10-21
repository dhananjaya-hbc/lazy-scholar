"""Settings loaded from the environment (.env locally, GitHub Secrets in CI)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Open weights mean the same Gemma model can run on any of these.
PROVIDERS = ("google", "ollama", "openrouter")


@dataclass(frozen=True)
class Config:
    model_provider: str
    model_name: str
    gemini_api_key: str | None
    openrouter_api_key: str | None
    ollama_host: str
    serpapi_api_key: str | None
    db_path: str


def load_config() -> Config:
    provider = os.getenv("MODEL_PROVIDER", "google").lower()
    if provider not in PROVIDERS:
        raise ValueError(f"MODEL_PROVIDER must be one of {PROVIDERS}, got {provider!r}")
    return Config(
        model_provider=provider,
        model_name=os.getenv("MODEL_NAME", "gemma-3-27b-it"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        db_path=os.getenv("DB_PATH", "lazy_scholar.db"),
    )
