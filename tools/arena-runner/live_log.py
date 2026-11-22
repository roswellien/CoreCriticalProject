"""Reads a match log while the game is still writing it.

The game flushes each line as it writes it (arena_log.cpp, write_line), so
another process can follow the file. A last line without its newline is
still being written and waits for the next read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MechNow:
    side: int
    x: float = 0.0
    z: float = 0.0
    standing: bool = True


@dataclass
class LiveLog:
    path: Path
    offset: int = 0
    pending: bytes = b""
    t: float = 0.0
    mechs: dict[int, MechNow] = field(default_factory=dict)
    end: dict | None = None
    bad_lines: int = 0

    def read_new(self) -> bool:
        """Reads what was added since the last call; True when anything was."""
        if not self.path.exists():
            return False
        with self.path.open("rb") as f:
            f.seek(self.offset)
            data = f.read()
        if not data:
            return False
        self.offset += len(data)
        lines = (self.pending + data).split(b"\n")
        self.pending = lines.pop()  # "" after a complete line
        for line in lines:
            if line.strip():
                self._take(line)
        return True

    def _take(self, line: bytes) -> None:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            self.bad_lines += 1
            return
        kind = record.get("type")
        if kind == "start":
            for m in record.get("mechs", []):
                self.mechs[m["id"]] = MechNow(side=m["side"])
        elif kind == "state":
            self.t = record.get("t", self.t)
            for m in record.get("mechs", []):
                now = self.mechs.setdefault(m["id"], MechNow(side=m.get("side", 0)))
                pos = m.get("pos", [now.x, 0.0, now.z])
                now.x, now.z = pos[0], pos[2]
                now.standing = m.get("standing", now.standing)
        elif kind == "destroyed":
            if record.get("id") in self.mechs:
                self.mechs[record["id"]].standing = False
        elif kind == "end":
            self.end = record
            self.t = record.get("t", self.t)

    def standing(self, side: int) -> int:
        return sum(1 for m in self.mechs.values() if m.side == side and m.standing)
