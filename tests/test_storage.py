"""Tests for geo_analyzer.storage — SQLite history tracking."""
import pytest
from datetime import datetime
from geo_analyzer.storage import (
    _get_connection,
    save_scan,
    get_history,
    get_trend,
    _score_to_grade,
    ScanRecord,
    TrendResult,
)
from geo_analyzer.scorer import EngineResult, EngineScore, ScanReport


def _make_engine_score(engine="chatgpt", keyword="test keyword", score=75,
                       mentioned=True, cited=True, position="early"):
    """Helper to create an EngineScore for testing."""
    return EngineScore(
        engine=engine,
        keyword=keyword,
        score=score,
        mentioned=mentioned,
        cited=cited,
        position=position,
        details="test details",
        raw=EngineResult(
            engine=engine,
            query=keyword,
            response_text="test response",
            mentioned=mentioned,
            cited=cited,
            position=position,
        ),
    )


def _make_report(url="https://example.com", keywords=None, scores=None):
    """Helper to create a ScanReport for testing."""
    if keywords is None:
        keywords = ["test keyword"]
    if scores is None:
        scores = [_make_engine_score()]
    return ScanReport(url=url, keywords=keywords, engine_scores=scores)


class TestScoreToGrade:
    def test_grade_a(self):
        assert _score_to_grade(80) == "A"
        assert _score_to_grade(100) == "A"

    def test_grade_b(self):
        assert _score_to_grade(60) == "B"
        assert _score_to_grade(79) == "B"

    def test_grade_c(self):
        assert _score_to_grade(40) == "C"
        assert _score_to_grade(59) == "C"

    def test_grade_d(self):
        assert _score_to_grade(20) == "D"
        assert _score_to_grade(39) == "D"

    def test_grade_f(self):
        assert _score_to_grade(0) == "F"
        assert _score_to_grade(19) == "F"


class TestSaveScan:
    def test_save_single_score(self):
        report = _make_report()
        count = save_scan(report, db_path=":memory:")
        assert count == 1

    def test_save_multiple_scores(self):
        scores = [
            _make_engine_score(engine="chatgpt", keyword="kw1", score=80),
            _make_engine_score(engine="perplexity", keyword="kw1", score=60),
            _make_engine_score(engine="chatgpt", keyword="kw2", score=40),
        ]
        report = _make_report(keywords=["kw1", "kw2"], scores=scores)
        count = save_scan(report, db_path=":memory:")
        assert count == 3

    def test_save_empty_report(self):
        report = _make_report(scores=[])
        count = save_scan(report, db_path=":memory:")
        assert count == 0


class TestGetHistory:
    def _setup_db(self):
        """Create a shared in-memory db with test data."""
        import sqlite3
        from geo_analyzer.storage import CREATE_TABLE_SQL, CREATE_INDEX_SQL
        
        conn = sqlite3.connect(":memory:")
        conn.execute(CREATE_TABLE_SQL)
        for idx in CREATE_INDEX_SQL:
            conn.execute(idx)
        
        # Insert test data
        test_data = [
            ("https://example.com", "keyword1", "chatgpt", 80, "A", 1, 1, "early", "2026-01-01T10:00:00"),
            ("https://example.com", "keyword1", "perplexity", 60, "B", 1, 0, "middle", "2026-01-01T10:00:00"),
            ("https://example.com", "keyword2", "chatgpt", 40, "C", 1, 0, "late", "2026-01-01T10:00:00"),
            ("https://example.com", "keyword1", "chatgpt", 90, "A", 1, 1, "early", "2026-01-02T10:00:00"),
            ("https://other.com", "keyword1", "chatgpt", 50, "C", 1, 0, "middle", "2026-01-01T10:00:00"),
        ]
        conn.executemany(
            "INSERT INTO scans (url, keyword, engine, score, grade, mentioned, cited, position, scanned_at) VALUES (?,?,?,?,?,?,?,?,?)",
            test_data,
        )
        conn.commit()
        return conn

    def test_get_history_all(self):
        """Test retrieving all history for a URL using save_scan + get_history with a temp file."""
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        report = _make_report(
            url="https://example.com",
            keywords=["kw1"],
            scores=[
                _make_engine_score(engine="chatgpt", keyword="kw1", score=80),
                _make_engine_score(engine="perplexity", keyword="kw1", score=60),
            ],
        )
        save_scan(report, db_path=db_path)
        
        records = get_history("https://example.com", db_path=db_path)
        assert len(records) == 2
        assert all(isinstance(r, ScanRecord) for r in records)
        
        os.unlink(db_path)

    def test_get_history_with_keyword_filter(self):
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        report = _make_report(
            url="https://example.com",
            keywords=["kw1", "kw2"],
            scores=[
                _make_engine_score(engine="chatgpt", keyword="kw1", score=80),
                _make_engine_score(engine="chatgpt", keyword="kw2", score=40),
            ],
        )
        save_scan(report, db_path=db_path)
        
        records = get_history("https://example.com", keyword="kw1", db_path=db_path)
        assert len(records) == 1
        assert records[0].keyword == "kw1"
        
        os.unlink(db_path)

    def test_get_history_limit(self):
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        for i in range(5):
            report = _make_report(
                url="https://example.com",
                keywords=["kw"],
                scores=[_make_engine_score(keyword="kw", score=50 + i)],
            )
            save_scan(report, db_path=db_path)
        
        records = get_history("https://example.com", limit=3, db_path=db_path)
        assert len(records) == 3
        
        os.unlink(db_path)

    def test_get_history_empty(self):
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        records = get_history("https://nonexistent.com", db_path=db_path)
        assert records == []
        
        os.unlink(db_path)


class TestGetTrend:
    def test_trend_with_improvement(self):
        import tempfile, os, time
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        # First scan: low score
        report1 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=30)],
        )
        save_scan(report1, db_path=db_path)
        
        time.sleep(0.01)  # Ensure different timestamp
        
        # Second scan: higher score
        report2 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=80)],
        )
        save_scan(report2, db_path=db_path)
        
        trend = get_trend("https://example.com", db_path=db_path)
        assert trend is not None
        assert isinstance(trend, TrendResult)
        assert trend.latest_score == 80
        assert trend.previous_score == 30
        assert trend.score_change == 50
        assert trend.trend_direction == "up"
        assert trend.trend_icon == "↑"
        
        os.unlink(db_path)

    def test_trend_with_decline(self):
        import tempfile, os, time
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        report1 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=80)],
        )
        save_scan(report1, db_path=db_path)
        
        time.sleep(0.01)
        
        report2 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=30)],
        )
        save_scan(report2, db_path=db_path)
        
        trend = get_trend("https://example.com", db_path=db_path)
        assert trend is not None
        assert trend.score_change == -50
        assert trend.trend_direction == "down"
        assert trend.trend_icon == "↓"
        
        os.unlink(db_path)

    def test_trend_stable(self):
        import tempfile, os, time
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        # Two scans with same score but must have different timestamps
        report1 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=50)],
        )
        save_scan(report1, db_path=db_path)
        
        time.sleep(0.01)
        
        report2 = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=50)],
        )
        save_scan(report2, db_path=db_path)
        
        trend = get_trend("https://example.com", db_path=db_path)
        assert trend is not None
        assert trend.score_change == 0
        assert trend.trend_direction == "stable"
        assert trend.trend_icon == "→"
        
        os.unlink(db_path)

    def test_trend_no_data(self):
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        trend = get_trend("https://nonexistent.com", db_path=db_path)
        assert trend is None
        
        os.unlink(db_path)

    def test_trend_single_scan(self):
        import tempfile, os
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        report = _make_report(
            url="https://example.com",
            keywords=["kw"],
            scores=[_make_engine_score(keyword="kw", score=60)],
        )
        save_scan(report, db_path=db_path)
        
        trend = get_trend("https://example.com", db_path=db_path)
        assert trend is not None
        assert trend.latest_score == 60
        assert trend.score_change == 0
        assert trend.trend_direction == "stable"
        assert len(trend.history) == 1
        
        os.unlink(db_path)

    def test_trend_with_keyword_filter(self):
        import tempfile, os, time
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        
        report1 = _make_report(
            url="https://example.com",
            keywords=["kw1", "kw2"],
            scores=[
                _make_engine_score(keyword="kw1", score=30),
                _make_engine_score(keyword="kw2", score=90),
            ],
        )
        save_scan(report1, db_path=db_path)
        
        time.sleep(0.01)
        
        report2 = _make_report(
            url="https://example.com",
            keywords=["kw1", "kw2"],
            scores=[
                _make_engine_score(keyword="kw1", score=70),
                _make_engine_score(keyword="kw2", score=90),
            ],
        )
        save_scan(report2, db_path=db_path)
        
        trend = get_trend("https://example.com", keyword="kw1", db_path=db_path)
        assert trend is not None
        assert trend.keyword == "kw1"
        assert trend.latest_score == 70
        assert trend.previous_score == 30
        assert trend.trend_direction == "up"
        
        os.unlink(db_path)


class TestDatabaseInit:
    def test_memory_db_creation(self):
        conn = _get_connection(":memory:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scans'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_table_schema(self):
        conn = _get_connection(":memory:")
        cursor = conn.execute("PRAGMA table_info(scans)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {"id", "url", "keyword", "engine", "score", "grade", "mentioned", "cited", "position", "scanned_at"}
        assert expected == columns
        conn.close()
