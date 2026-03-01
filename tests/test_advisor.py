"""Tests for the GEO optimization advisor."""
from geo_analyzer.scorer import EngineResult, EngineScore, ScanReport, score_result
from geo_analyzer.advisor import generate_advice, Advice


def _make_score(mentioned=False, cited=False, position="not_found", response_text="some response", accuracy=None):
    result = EngineResult(
        engine="TestEngine", query="test kw", response_text=response_text,
        mentioned=mentioned, cited=cited, position=position, accuracy=accuracy,
    )
    return score_result(result, "https://example.com", "test kw")


def test_no_engines_configured():
    """When no engines have response text, suggest setup."""
    result = EngineResult(engine="Test", query="kw", response_text="", mentioned=False)
    es = score_result(result, "https://example.com", "kw")
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    assert any(a.category == "Setup" for a in advice)


def test_not_mentioned_gives_high_priority():
    """When site is not mentioned, should get high priority visibility advice."""
    es = _make_score(mentioned=False)
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    high = [a for a in advice if a.priority == "high"]
    assert len(high) >= 1
    assert any("Discoverability" in a.title or "Visibility" in a.title for a in high)


def test_mentioned_not_cited():
    """When mentioned but not cited, should suggest citation improvements."""
    es = _make_score(mentioned=True, cited=False, position="middle")
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    assert any("Citation" in a.title for a in advice)


def test_late_position():
    """When position is late, should suggest positioning improvements."""
    es = _make_score(mentioned=True, cited=True, position="late")
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    assert any("Position" in a.title for a in advice)


def test_high_score_maintenance():
    """When score is high, should suggest maintenance."""
    es = _make_score(mentioned=True, cited=True, position="early", accuracy=1.0)
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    assert any(a.category == "Maintenance" for a in advice)


def test_always_includes_best_practices():
    """Should always include general best practices."""
    es = _make_score(mentioned=True, cited=True, position="early")
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    assert any(a.category == "Best Practices" for a in advice)


def test_empty_report():
    """Empty report should return no advice."""
    report = ScanReport(url="https://example.com", keywords=[], engine_scores=[])
    advice = generate_advice(report)
    assert advice == []


def test_advice_has_action_items():
    """All advice should have at least one action item."""
    es = _make_score(mentioned=False)
    report = ScanReport(url="https://example.com", keywords=["kw"], engine_scores=[es])
    advice = generate_advice(report)
    for a in advice:
        assert len(a.action_items) >= 1, f"Advice '{a.title}' has no action items"
