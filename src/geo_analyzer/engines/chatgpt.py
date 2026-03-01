"""ChatGPT Search engine adapter."""
import httpx
from geo_analyzer.engines.base import BaseEngine
from geo_analyzer.scorer import EngineResult


class ChatGPTEngine(BaseEngine):
    name = "ChatGPT"

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
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]

        return EngineResult(
            engine=self.name,
            query=keyword,
            response_text=text,
            mentioned=self._check_mentioned(text, target_url),
            cited=self._check_cited(text, target_url),
            position=self._detect_position(text, target_url),
        )
