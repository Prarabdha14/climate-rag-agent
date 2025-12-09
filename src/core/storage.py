# src/core/storage.py
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import json

DB_PATH = Path("data/db.sqlite")

# We create the schema inline to avoid "file not found" errors if schema.sql is missing
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT,
    filetype TEXT,
    uploaded_at TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS processing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    summary_json_path TEXT,
    one_line TEXT,
    three_bullets TEXT,
    five_sentence TEXT,
    sentiment_label TEXT,
    sentiment_score REAL,
    follow_up_needed INTEGER,
    processed_at TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id)
);

CREATE TABLE IF NOT EXISTS retrieval_chunks (
    id TEXT PRIMARY KEY,
    source_file TEXT,
    start_token INTEGER,
    end_token INTEGER,
    metadata TEXT
);
"""

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

def record_upload(filename, filepath, filetype="unknown", source="local"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # FIXED: Use timezone-aware datetime
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO uploads (filename, filepath, filetype, uploaded_at, source) VALUES (?,?,?,?,?)",
        (filename, str(filepath), filetype, now, source)
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    return uid

def record_result(upload_id, summary_json_path, summaries, sentiment, follow_up):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # FIXED: Use timezone-aware datetime
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        """INSERT INTO processing_results
           (upload_id, summary_json_path, one_line, three_bullets, five_sentence, sentiment_label, sentiment_score, follow_up_needed, processed_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (upload_id, str(summary_json_path),
         summaries.get("one_line",""),
         summaries.get("three_bullets",""),
         summaries.get("five_sentence",""),
         sentiment.get("label","unknown"),
         float(sentiment.get("score",0.0)),
         1 if follow_up else 0,
         now)
    )
    conn.commit()
    conn.close()

def register_chunks(chunks):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for c in chunks:
        cur.execute(
            "INSERT OR REPLACE INTO retrieval_chunks (id, source_file, start_token, end_token, metadata) VALUES (?,?,?,?,?)",
            (c.get("id"), c.get("source"), c.get("start",0), c.get("end",0), json.dumps(c.get("metadata",{})))
        )
    conn.commit()
    conn.close()