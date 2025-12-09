CREATE TABLE IF NOT EXISTS uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  filetype TEXT,
  uploaded_at TEXT NOT NULL,
  source TEXT DEFAULT 'local'
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
  follow_up_needed INTEGER DEFAULT 0,
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