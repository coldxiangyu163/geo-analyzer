"""Configuration management — reads API keys from env vars."""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    perplexity_api_key: Optional[str] = field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY"))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    timeout: int = 30
    max_retries: int = 2

    def get_available_engines(self) -> list[str]:
        """Return list of engines with configured API keys."""
        available = []
        if self.openai_api_key:
            available.append("chatgpt")
        if self.perplexity_api_key:
            available.append("perplexity")
        if self.gemini_api_key:
            available.append("gemini")
        return available


def load_config() -> Config:
    return Config()
