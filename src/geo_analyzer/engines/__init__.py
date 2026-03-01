"""AI search engine adapters."""
from geo_analyzer.engines.base import BaseEngine
from geo_analyzer.engines.chatgpt import ChatGPTEngine
from geo_analyzer.engines.perplexity import PerplexityEngine
from geo_analyzer.engines.gemini import GeminiEngine

ENGINES = {
    "chatgpt": ChatGPTEngine,
    "perplexity": PerplexityEngine,
    "gemini": GeminiEngine,
}

__all__ = ["BaseEngine", "ChatGPTEngine", "PerplexityEngine", "GeminiEngine", "ENGINES"]
