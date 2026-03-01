"""SQLite-based scan history storage for GEO Analyzer."""
import sqlite3
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


DEFAULT_DB_PATH = Path.home() / ".geo-analyzer" / "history.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    keyword TEXT NOT NULL,
    engine TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    grade TEXT NOT NULL DEFAULT 'F',
    mentioned INTEGER NOT NULL DEFAULT 0,
    cited INTEGER NOT NULL DEFAULT 0,
    position TEXT DEFAULT 'not_found',
    scanned_at TEXT NOT NULL
)
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_scans_url ON scans(url)",
    "CREATE INDEX IF NOT EXISTS idx_scans_url_keyword ON scans(url, keyword)",
    "CREATE INDEX IF NOT EXISTS idx_scans_scanned_at ON scans(scanned_at)",
]


@dataclass
class ScanRecord:
    """A single scan record from the database."""
    id: int
    url: str
    keyword: str
    engine: str
    score: int
    grade: str
    mentioned: bool
    cited: bool
    position: str
    scanned_at: str


@dataclass
class TrendResult:
    """Trend analysis result."""
    url: str
    keyword: Optional[str]
    total_scans: int
    latest_score: int
    previous_score: int
    score_change: int
    latest_grade: str
    previous_grade: str
    trend_direction: str  # "up", "down", "stable"
    history: list[tuple[str, int, str]]  # [(scanned_at, avg_score, grade), ...]

    @property
    def trend_icon(self) -> str:
        return {"up": "↑", "down": "↓", "stable": "→"}.get(self.trend_direction, "?")


def _get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection, creating the database if needed."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    db_path = Path(db_path) if not isinstance(db_path, Path) and db_path != ":memory:" else db_path
    
    if db_path != ":memory:" and isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.execute(CREATE_TABLE_SQL)
    for idx_sql in CREATE_INDEX_SQL:
        conn.execute(idx_sql)
    conn.commit()
    return conn


def _score_to_grade(score: int) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    else:
        return "F"


def save_scan(scan_report, db_path: str | Path | None = None) -> int:
    """Save all engine scores from a ScanReport to the database.
    
    Args:
        scan_report: A ScanReport object from scorer.py
        db_path: Optional database path (default: ~/.geo-analyzer/history.db)
    
    Returns:
        Number of records inserted
    """
    conn = _get_connection(db_path)
    now = datetime.now().isoformat()
    count = 0
    
    try:
        for es in scan_report.engine_scores:
            grade = _score_to_grade(es.score)
            conn.execute(
                """INSERT INTO scans (url, keyword, engine, score, grade, mentioned, cited, position, scanned_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scan_report.url,
                    es.keyword,
                    es.engine,
                    es.score,
                    grade,
                    1 if es.mentioned else 0,
                    1 if es.cited else 0,
                    es.position or "not_found",
                    now,
                ),
            )
            count += 1
        conn.commit()
    finally:
        conn.close()
    
    return count


def get_history(
    url: str,
    keyword: str | None = None,
    limit: int = 10,
    db_path: str | Path | None = None,
) -> list[ScanRecord]:
    """Query scan history for a URL, optionally filtered by keyword.
    
    Args:
        url: Target URL to look up
        keyword: Optional keyword filter
        limit: Maximum number of records to return
        db_path: Optional database path
    
    Returns:
        List of ScanRecord objects, most recent first
    """
    conn = _get_connection(db_path)
    try:
        if keyword:
            cursor = conn.execute(
                """SELECT id, url, keyword, engine, score, grade, mentioned, cited, position, scanned_at
                   FROM scans WHERE url = ? AND keyword = ?
                   ORDER BY scanned_at DESC LIMIT ?""",
                (url, keyword, limit),
            )
        else:
            cursor = conn.execute(
                """SELECT id, url, keyword, engine, score, grade, mentioned, cited, position, scanned_at
                   FROM scans WHERE url = ?
                   ORDER BY scanned_at DESC LIMIT ?""",
                (url, limit),
            )
        
        records = []
        for row in cursor.fetchall():
            records.append(ScanRecord(
                id=row[0],
                url=row[1],
                keyword=row[2],
                engine=row[3],
                score=row[4],
                grade=row[5],
                mentioned=bool(row[6]),
                cited=bool(row[7]),
                position=row[8],
                scanned_at=row[9],
            ))
        return records
    finally:
        conn.close()


def get_trend(
    url: str,
    keyword: str | None = None,
    db_path: str | Path | None = None,
) -> TrendResult | None:
    """Calculate score trends for a URL.
    
    Compares the most recent scan session with the previous one to determine
    if visibility is improving, declining, or stable.
    
    Args:
        url: Target URL
        keyword: Optional keyword filter
        db_path: Optional database path
    
    Returns:
        TrendResult or None if insufficient data
    """
    conn = _get_connection(db_path)
    try:
        # Get all scan sessions grouped by scanned_at, with average score
        if keyword:
            cursor = conn.execute(
                """SELECT scanned_at, 
                          CAST(AVG(score) AS INTEGER) as avg_score,
                          COUNT(*) as cnt
                   FROM scans WHERE url = ? AND keyword = ?
                   GROUP BY scanned_at
                   ORDER BY scanned_at DESC""",
                (url, keyword),
            )
        else:
            cursor = conn.execute(
                """SELECT scanned_at,
                          CAST(AVG(score) AS INTEGER) as avg_score,
                          COUNT(*) as cnt
                   FROM scans WHERE url = ?
                   GROUP BY scanned_at
                   ORDER BY scanned_at DESC""",
                (url,),
            )
        
        sessions = cursor.fetchall()
        
        if not sessions:
            return None
        
        # Build history list: (scanned_at, avg_score, grade)
        history = [(s[0], s[1], _score_to_grade(s[1])) for s in sessions]
        
        latest_score = sessions[0][1]
        latest_grade = _score_to_grade(latest_score)
        
        if len(sessions) >= 2:
            previous_score = sessions[1][1]
            previous_grade = _score_to_grade(previous_score)
            score_change = latest_score - previous_score
        else:
            previous_score = latest_score
            previous_grade = latest_grade
            score_change = 0
        
        if score_change > 0:
            trend_direction = "up"
        elif score_change < 0:
            trend_direction = "down"
        else:
            trend_direction = "stable"
        
        total_scans = sum(s[2] for s in sessions)
        
        return TrendResult(
            url=url,
            keyword=keyword,
            total_scans=total_scans,
            latest_score=latest_score,
            previous_score=previous_score,
            score_change=score_change,
            latest_grade=latest_grade,
            previous_grade=previous_grade,
            trend_direction=trend_direction,
            history=history,
        )
    finally:
        conn.close()
