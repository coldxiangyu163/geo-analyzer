"""Abstract base class for AI search engines."""
from abc import ABC, abstractmethod
from geo_analyzer.scorer import EngineResult


class BaseEngine(ABC):
    """Base class for AI search engine adapters."""

    name: str = "base"

    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    @abstractmethod
    async def query(self, keyword: str, target_url: str) -> EngineResult:
        """Query the AI engine and return raw result."""
        ...

    def _build_query(self, keyword: str) -> str:
        """Build the search query for the AI engine."""
        return f"What are the best tools or websites for {keyword}? Please provide specific recommendations with URLs."

    def _check_mentioned(self, response: str, url: str) -> bool:
        """Check if the target URL/domain is mentioned."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        return domain.lower() in response.lower()

    def _check_cited(self, response: str, url: str) -> bool:
        """Check if the target URL is directly cited."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        # Check for full URL or domain link
        return url.lower() in response.lower() or f"[{domain}" in response.lower()

    def _detect_position(self, response: str, url: str) -> str:
        """Detect where in the response the URL is mentioned."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        lower = response.lower()
        domain_lower = domain.lower()
        
        if domain_lower not in lower:
            return "not_found"
        
        pos = lower.index(domain_lower)
        ratio = pos / max(len(lower), 1)
        
        if ratio < 0.33:
            return "early"
        elif ratio < 0.66:
            return "middle"
        else:
            return "late"
