"""SQLite memory: every URL seen, its verdict, and its deadline.

In CI the database file lives on a separate `data` branch between nightly runs.
"""

import json
import sqlite3
from dataclasses import asdict
from datetime import date

from lazy_scholar.judge import Verdict
from lazy_scholar.search import SearchResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    url        TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    snippet    TEXT NOT NULL,
    query      TEXT NOT NULL,
    first_seen TEXT NOT NULL,   -- YYYY-MM-DD
    judged_at  TEXT,            -- NULL until Gemma has judged it (retried next night)
    eligible   INTEGER,
    category   TEXT,
    score      INTEGER,
    deadline   TEXT,            -- YYYY-MM-DD or NULL
    amount     TEXT,
    summary    TEXT,
    reasons    TEXT             -- JSON list
)
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def remember(conn: sqlite3.Connection, results: list[SearchResult]) -> list[SearchResult]:
    """Store new URLs and return the results that still need judging."""
    today = date.today().isoformat()
    for r in results:
        conn.execute(
            "INSERT OR IGNORE INTO opportunities (url, title, snippet, query, first_seen)"
            " VALUES (?, ?, ?, ?, ?)",
            (r.url, r.title, r.snippet, r.query, today),
        )
    conn.commit()
    judged = {
        row["url"]
        for row in conn.execute("SELECT url FROM opportunities WHERE judged_at IS NOT NULL")
    }
    return [r for r in results if r.url not in judged]


def unjudged(conn: sqlite3.Connection) -> list[SearchResult]:
    """Results from earlier nights whose judging failed, to retry."""
    rows = conn.execute("SELECT url, title, snippet, query FROM opportunities WHERE judged_at IS NULL")
    return [SearchResult(row["title"], row["url"], row["snippet"], row["query"]) for row in rows]


def save_verdicts(conn: sqlite3.Connection, verdicts: list[Verdict]) -> None:
    today = date.today().isoformat()
    for v in verdicts:
        d = asdict(v)
        conn.execute(
            "UPDATE opportunities SET judged_at=?, eligible=?, category=?, score=?, deadline=?,"
            " amount=?, summary=?, reasons=? WHERE url=?",
            (today, int(d["eligible"]), d["category"], d["score"], d["deadline"],
             d["amount"], d["summary"], json.dumps(d["reasons"]), d["url"]),
        )
    conn.commit()


def open_matches(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Eligible opportunities that have not closed: soonest deadline first, then best score."""
    return conn.execute(
        "SELECT * FROM opportunities WHERE eligible = 1"
        " AND (deadline IS NULL OR deadline >= ?)"
        " ORDER BY deadline IS NULL, deadline, score DESC",
        (date.today().isoformat(),),
    ).fetchall()
