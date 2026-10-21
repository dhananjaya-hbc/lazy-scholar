"""One generate() call over three providers.

Gemma is open-weight, so the same model runs on Google AI Studio, OpenRouter,
or a self-hosted Ollama. Switching is one MODEL_PROVIDER setting.
"""

import httpx

from lazy_scholar.config import Config


def generate(config: Config, prompt: str) -> str:
    if config.model_provider == "google":
        from google import genai

        client = genai.Client(api_key=config.gemini_api_key)
        response = client.models.generate_content(model=config.model_name, contents=prompt)
        return response.text or ""

    if config.model_provider == "openrouter":
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.openrouter_api_key}"},
            json={
                "model": f"google/{config.model_name}",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    if config.model_provider == "ollama":
        response = httpx.post(
            f"{config.ollama_host}/api/generate",
            json={"model": config.model_name, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["response"]

    raise ValueError(f"Unknown MODEL_PROVIDER: {config.model_provider}")
