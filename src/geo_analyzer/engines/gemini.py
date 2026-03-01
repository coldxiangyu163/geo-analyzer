"""Google Gemini engine adapter."""
import httpx
from geo_analyzer.engines.base import BaseEngine
from geo_analyzer.scorer import EngineResult


class GeminiEngine(BaseEngine):
    name = "Gemini"

    async def query(self, keyword: str, target_url: str) -> EngineResult:
        if not self.is_configured:
            return EngineResult(
                engine=self.name,
                query=keyword,
                response_text="",
                mentioned=False,
            )

        prompt = self._build_query(keyword)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]

        return EngineResult(
            engine=self.name,
            query=keyword,
            response_text=text,
            mentioned=self._check_mentioned(text, target_url),
            cited=self._check_cited(text, target_url),
            position=self._detect_position(text, target_url),
        )
