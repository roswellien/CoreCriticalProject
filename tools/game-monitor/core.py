"""Bounded local event storage and incremental log ingestion; no game dependency."""

from collections import deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
import uuid


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _replace_status_snapshot(temporary, destination):
    # Windows readers such as Get-Content may omit FILE_SHARE_DELETE. Keep the
    # complete old snapshot until atomic replacement succeeds after they close.
    deadline = time.monotonic() + 1.0
    while True:
        try:
            temporary.replace(destination)
            return
        except OSError as failure:
            # WinError5 is also returned for a destination sharing conflict.
            # Permanent access failures still propagate at the bounded deadline;
            # other errors and all event-file writes retain their fatal behavior.
            if os.name != "nt" or getattr(failure, "winerror", None) not in (5, 32, 33):
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(.01, remaining))


def severity(text):
    # Treat classifications as reported messages, not proof of their root cause.
    text = re.sub(r"\b0\s+errors?\b|\bno\s+errors?\b", "", text, flags=re.I)
    text = re.sub(r"\bhandled\s+exception\b", "", text, flags=re.I)
    if re.search(r"\b(fatal|assertion failed|access violation)\b", text, re.I):
        return "critical"
    if re.search(r"\b(error|failed|failure|exception)\b", text, re.I):
        return "error"
    if re.search(r"\b(warning|warn)\b", text, re.I):
        return "warning"
    return "info"


class EventStore:
    def __init__(self, directory, segment_bytes=8 * 1024 * 1024, segments=8):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=False)
        if segment_bytes < 512 or segments < 2:
            raise ValueError("Retention requires segments >= 2 and segment_bytes >= 512")
        self.session = str(uuid.uuid4())
        self.started = time.monotonic()
        self.sequence = 0
        self.segment_bytes = segment_bytes
        self.segments = segments
        self.files = deque()
        self.alerts = deque(maxlen=50)
        self.dropped_segments = 0
        self.file = None
        self._rotate()

    def _rotate(self):
        if self.file:
            self.file.close()
        path = self.directory / f"events-{self.sequence + 1:012d}.jsonl"
        self.file = path.open("xb")
        self.files.append((path, self.sequence + 1))
        while len(self.files) > self.segments:
            # Only files created by this instance in its exclusive run directory.
            self.files.popleft()[0].unlink()
            self.dropped_segments += 1

    def emit(self, source, event, level="info", **data):
        record = {"schema_version": 1, "session_id": self.session, "seq": self.sequence + 1,
                  "timestamp_utc": utc_now(), "elapsed_ms": round((time.monotonic() - self.started) * 1000),
                  "source": source, "event": event, "severity": level, "data": data}
        encoded = (json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
        if len(encoded) > 256 * 1024:
            raise ValueError("Event exceeds bounded record size")
        if self.file.tell() and self.file.tell() + len(encoded) > self.segment_bytes:
            self._rotate()
        self.file.write(encoded)
        self.file.flush()  # Observer-side buffering only; no fsync in the game.
        self.sequence += 1
        if level in ("warning", "error", "critical"):
            self.alerts.append(record)
        return record

    def status(self, **state):
        record = {"schema_version": 1, "session_id": self.session, "updated_utc": utc_now(),
                  "collector_pid": os.getpid(), "latest_seq": self.sequence,
                  "oldest_seq": self.files[0][1], "dropped_segments": self.dropped_segments,
                  "recent_alerts": list(self.alerts), **state}
        temporary = self.directory / "status.tmp"
        temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
        _replace_status_snapshot(temporary, self.directory / "status.json")

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


class Tail:
    """Read new bytes only, tolerate partial lines, truncation and replacement."""
    def __init__(self, path, from_start=False, chunk_bytes=64 * 1024, max_line=64 * 1024):
        self.path = Path(path)
        self.chunk_bytes = chunk_bytes
        self.max_line = max_line
        self.offset = 0
        self.identity = None
        self.mtime = None
        self.pending = b""
        self.discarding = False
        if self.path.exists():
            stat = self.path.stat()
            self.identity = (stat.st_dev, stat.st_ino)
            self.mtime = stat.st_mtime_ns
            self.offset = 0 if from_start else stat.st_size
            if self.offset:
                with self.path.open("rb") as stream:
                    stream.seek(self.offset - 1)
                    self.discarding = stream.read(1) != b"\n"

    def poll(self):
        notices, lines = [], []
        try:
            with self.path.open("rb") as stream:
                stat = os.fstat(stream.fileno())
                identity = (stat.st_dev, stat.st_ino)
                rewritten = self.mtime is not None and stat.st_mtime_ns != self.mtime and stat.st_size == self.offset
                if self.identity is not None and (identity != self.identity or stat.st_size < self.offset or rewritten):
                    notices.append("source_reset")
                    self.offset, self.pending, self.discarding = 0, b"", False
                self.identity = identity
                self.mtime = stat.st_mtime_ns
                stream.seek(self.offset)
                block = stream.read(min(self.chunk_bytes, max(0, stat.st_size - self.offset)))
                self.offset += len(block)
        except FileNotFoundError:
            return lines, notices
        for piece in block.splitlines(keepends=True):
            ending = piece.endswith(b"\n")
            if self.discarding:
                if ending:
                    self.discarding = False
                continue
            self.pending += piece
            if len(self.pending) > self.max_line:
                notices.append("oversized_line_dropped")
                self.pending = b""
                self.discarding = not ending
            elif ending:
                lines.append(self.pending.rstrip(b"\r\n").decode("utf-8", errors="replace"))
                self.pending = b""
        return lines, notices

    def finish(self):
        if self.pending:
            line = self.pending.decode("utf-8", errors="replace")
            self.pending = b""
            return line
        return None


def ingest(store, source, line, json_lines=False):
    if not line.strip():
        return
    if json_lines:
        if len(line) > 16 * 1024:
            store.emit(source, "structured_event_too_large", "warning", text=line[:512])
            return
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or not isinstance(record.get("event"), str):
                raise ValueError("Expected an event object")
        except (ValueError, RecursionError):
            store.emit(source, "invalid_json", "warning", text=line[:4096])
            return
        level = "info"
        if record["event"] == "fatal" or record.get("mismatches", 0) != 0:
            level = "critical"
        store.emit(source, record["event"], level, payload=record)
    else:
        store.emit(source, "message", severity(line), text=line[:4096])


def read_events(directory, after=0, limit=200):
    if after < 0 or not 1 <= limit <= 10000:
        raise ValueError("Invalid cursor or limit")
    result = []
    paths = sorted(path for path in Path(directory).glob("events-*.jsonl")
                   if re.fullmatch(r"events-[0-9]{12,20}\.jsonl", path.name))
    starts = [int(path.stem.split("-")[1]) for path in paths]
    oldest = starts[0] if starts else None
    for index, path in enumerate(paths):
        if index + 1 < len(paths) and starts[index + 1] <= after + 1:
            continue  # Cursor seeks past whole old segments without parsing them.
        try:
            with path.open("rb") as stream:
                for line in stream:
                    if not line.endswith(b"\n"):
                        break  # Concurrent write is not yet a complete event.
                    record = json.loads(line)
                    if record["seq"] > after:
                        result.append(record)
                        if len(result) >= limit:
                            break
        except FileNotFoundError:
            continue  # Retention rotation while a reader takes its snapshot.
        if len(result) >= limit:
            break
    return {"events": result, "next_cursor": result[-1]["seq"] if result else after,
            "retention_gap": oldest is not None and after < oldest - 1}
