CREATE TABLE IF NOT EXISTS crash_issue_daily_limits (
  utc_day TEXT PRIMARY KEY NOT NULL,
  issue_count INTEGER NOT NULL CHECK (issue_count >= 0)
);
