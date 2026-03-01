"""Tests for the scoring algorithm."""
from geo_analyzer.scorer import EngineResult, score_result, ScanReport


def test_not_mentioned_scores_zero():
    result = EngineResult(engine="test", query="kw", response_text="nothing here", mentioned=False)
    score = score_result(result, "https://example.com", "kw")
    assert score.score == 0
    assert score.mentioned is False


def test_mentioned_only():
    result = EngineResult(engine="test", query="kw", response_text="check example.com", mentioned=True)
    score = score_result(result, "https://example.com", "kw")
    assert score.score == 30
    assert score.mentioned is True


def test_mentioned_and_cited():
    result = EngineResult(
        engine="test", query="kw", response_text="check example.com",
        mentioned=True, cited=True,
    )
    score = score_result(result, "https://example.com", "kw")
    assert score.score == 55  # 30 + 25


def test_full_score():
    result = EngineResult(
        engine="test", query="kw", response_text="check example.com",
        mentioned=True, cited=True, position="early", accuracy=1.0,
    )
    score = score_result(result, "https://example.com", "kw")
    assert score.score == 100  # 30 + 25 + 25 + 20


def test_middle_position():
    result = EngineResult(
        engine="test", query="kw", response_text="check example.com",
        mentioned=True, position="middle",
    )
    score = score_result(result, "https://example.com", "kw")
    assert score.score == 45  # 30 + 15


def test_grade_calculation():
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[])
    assert report.grade == "F"
    assert report.overall_score == 0


def test_grade_a():
    result = EngineResult(engine="test", query="kw", response_text="x", mentioned=True, cited=True, position="early", accuracy=1.0)
    es = score_result(result, "https://example.com", "kw")
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    assert report.grade == "A"
    assert report.overall_score == 100
