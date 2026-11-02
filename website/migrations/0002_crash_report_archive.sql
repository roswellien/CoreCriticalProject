CREATE TABLE IF NOT EXISTS crash_report_archive (
  report_id TEXT PRIMARY KEY NOT NULL,
  created_utc TEXT NOT NULL,
  stored_utc TEXT NOT NULL,
  mode TEXT NOT NULL,
  exit_code INTEGER NOT NULL,
  failure_summary TEXT NOT NULL,
  crash_fingerprint TEXT,
  report_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS crash_report_archive_stored_utc
  ON crash_report_archive (stored_utc DESC);

CREATE INDEX IF NOT EXISTS crash_report_archive_fingerprint
  ON crash_report_archive (crash_fingerprint);
