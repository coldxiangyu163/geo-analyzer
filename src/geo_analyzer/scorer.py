"""Visibility scoring algorithm for GEO analysis."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EngineResult:
    """Raw result from a single AI search engine."""
    engine: str
    query: str
    response_text: str
    mentioned: bool = False
    cited: bool = False
    citation_url: Optional[str] = None
    position: Optional[str] = None  # "early", "middle", "late", "not_found"
    context_snippet: Optional[str] = None
    accuracy: Optional[float] = None  # 0.0 - 1.0


@dataclass
class EngineScore:
    """Scored result for one engine + one keyword."""
    engine: str
    keyword: str
    score: int  # 0-100
    mentioned: bool
    cited: bool
    position: str
    details: str
    raw: EngineResult


def score_result(result: EngineResult, url: str, keyword: str) -> EngineScore:
    """Score a single engine result for visibility.
    
    Scoring breakdown (0-100):
    - Mentioned (0/30): Is the site/brand mentioned in the response?
    - Cited (0/25): Is there a direct URL citation?
    - Position (0/25): Where in the response? (early=25, middle=15, late=5)
    - Accuracy (0/20): How accurately is the site described?
    """
    score = 0
    details_parts = []

    # Mentioned (30 pts)
    if result.mentioned:
        score += 30
        details_parts.append("✅ Mentioned")
    else:
        details_parts.append("❌ Not mentioned")
        return EngineScore(
            engine=result.engine,
            keyword=keyword,
            score=0,
            mentioned=False,
            cited=False,
            position="not_found",
            details="Not mentioned in AI response",
            raw=result,
        )

    # Cited (25 pts)
    if result.cited:
        score += 25
        details_parts.append("🔗 Cited with URL")
    else:
        details_parts.append("⚠️ No URL citation")

    # Position (25 pts)
    position = result.position or "not_found"
    position_scores = {"early": 25, "middle": 15, "late": 5, "not_found": 0}
    pos_score = position_scores.get(position, 0)
    score += pos_score
    if position != "not_found":
        details_parts.append(f"📍 Position: {position} (+{pos_score})")

    # Accuracy (20 pts)
    if result.accuracy is not None:
        acc_score = int(result.accuracy * 20)
        score += acc_score
        details_parts.append(f"🎯 Accuracy: {result.accuracy:.0%} (+{acc_score})")

    return EngineScore(
        engine=result.engine,
        keyword=keyword,
        score=min(score, 100),
        mentioned=result.mentioned,
        cited=result.cited,
        position=position,
        details=" | ".join(details_parts),
        raw=result,
    )


@dataclass
class ScanReport:
    """Aggregated scan report across all engines and keywords."""
    url: str
    keywords: list[str]
    engine_scores: list[EngineScore]
    overall_score: int = 0
    grade: str = ""

    def __post_init__(self):
        if self.engine_scores:
            self.overall_score = sum(s.score for s in self.engine_scores) // len(self.engine_scores)
        self.grade = self._calc_grade()

    def _calc_grade(self) -> str:
        if self.overall_score >= 80:
            return "A"
        elif self.overall_score >= 60:
            return "B"
        elif self.overall_score >= 40:
            return "C"
        elif self.overall_score >= 20:
            return "D"
        else:
            return "F"
