"""The user's private profile: from the PROFILE env var (CI secret) or profile.toml."""

import os
import tomllib
from pathlib import Path

PROFILE_PATH = Path("profile.toml")


def load_profile() -> dict:
    text = os.getenv("PROFILE")
    if text:
        return tomllib.loads(text)
    if PROFILE_PATH.exists():
        return tomllib.loads(PROFILE_PATH.read_text())
    raise RuntimeError("No profile: set PROFILE or copy profile.example.toml to profile.toml")


def profile_text(profile: dict) -> str:
    """Profile as plain lines for the model prompt."""
    lines = []
    for key, value in profile.items():
        if isinstance(value, list):
            value = ", ".join(value)
        if value:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)
