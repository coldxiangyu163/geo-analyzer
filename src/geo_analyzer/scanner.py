"""Scan coordinator — runs queries across engines and aggregates results."""
import asyncio
from geo_analyzer.config import Config
from geo_analyzer.engines import ENGINES
from geo_analyzer.scorer import EngineResult, EngineScore, ScanReport, score_result


async def scan(
    url: str,
    keywords: list[str],
    config: Config,
    engine_names: list[str] | None = None,
) -> ScanReport:
    """Run a full GEO scan across all configured engines.
    
    Args:
        url: Target website URL to check visibility for
        keywords: List of keywords to query AI engines with
        config: Configuration with API keys
        engine_names: Optional list of specific engines to use
    
    Returns:
        ScanReport with aggregated scores
    """
    # Initialize engines
    engine_keys = {
        "chatgpt": config.openai_api_key,
        "perplexity": config.perplexity_api_key,
        "gemini": config.gemini_api_key,
    }

    if engine_names:
        selected = [e for e in engine_names if e in ENGINES]
    else:
        selected = list(ENGINES.keys())

    engines = []
    for name in selected:
        engine_cls = ENGINES[name]
        engine = engine_cls(api_key=engine_keys.get(name), timeout=config.timeout)
        engines.append(engine)

    # Run all queries concurrently
    all_scores: list[EngineScore] = []
    
    async def query_engine(engine, keyword):
        try:
            result = await engine.query(keyword, url)
            return score_result(result, url, keyword)
        except Exception as e:
            return EngineScore(
                engine=engine.name,
                keyword=keyword,
                score=0,
                mentioned=False,
                cited=False,
                position="error",
                details=f"❌ Error: {str(e)[:80]}",
                raw=EngineResult(
                    engine=engine.name,
                    query=keyword,
                    response_text="",
                    mentioned=False,
                ),
            )

    tasks = []
    for engine in engines:
        for keyword in keywords:
            tasks.append(query_engine(engine, keyword))

    results = await asyncio.gather(*tasks)
    all_scores.extend(results)

    return ScanReport(url=url, keywords=keywords, engine_scores=all_scores)
