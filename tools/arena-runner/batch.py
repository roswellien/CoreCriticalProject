"""A batch of arena matches: seeds, folders, setup files and processes.

Every match in a batch runs at once, hidden, in its own process with its own
write folder (a copy of the player's settings.reg), so ten matches never race
on the player's settings or mw3.log, and each match can be rerun exactly from
its command line (docs/arena.md, "Arena runner").
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

MIN_MATCHES, MAX_MATCHES = 1, 10
MAX_SEED = 2147483647  # the arena's seed range (docs/arena.md)
STUCK_MINUTES = 15  # the setup's time limit: a match still going then is stuck
FRAME_MS = 33


def user_write_dir() -> Path:
    """The game's own write folder, where the player's settings.reg lives."""
    return Path(os.environ.get("APPDATA", "")) / "MicroProse" / "MechWarrior 3"


def new_seeds(count: int, rng: random.Random | None = None) -> list[int]:
    """`count` different seeds: a repeat would name two logs alike, and the
    game refuses to write over a log (arena_setup.cpp, create_arena_log)."""
    if not MIN_MATCHES <= count <= MAX_MATCHES:
        raise ValueError(f"matches: {count}, must be {MIN_MATCHES} to {MAX_MATCHES}")
    return (rng or random.SystemRandom()).sample(range(MAX_SEED + 1), count)


def setup_record(map_id: str, sides: list[list[dict]], out: Path) -> dict:
    """The setup file the game reads. Each bot is {mech, loadout, preset}."""
    if len(sides) != 2 or not all(1 <= len(side) <= 8 for side in sides):
        raise ValueError("each side needs 1 to 8 mechs")
    return {"map": map_id, "minutes": STUCK_MINUTES, "out": str(out), "sides": sides}


def match_command(exe: Path, game: Path, setup: Path, seed: int, write_dir: Path) -> list[str]:
    return [
        str(exe), str(game), "--arena", str(setup), "--seed", str(seed),
        "--frame-ms", str(FRAME_MS), "--hidden", "-nofmv", "--write-dir", str(write_dir),
    ]  # fmt: skip


def replay_command(exe: Path, game: Path, log: Path, three_d: bool) -> list[str]:
    return [str(exe), str(game), "--replay3d" if three_d else "--replay", str(log)]


def command_text(command: list[str]) -> str:
    """The command as one line to paste into a shell (paths quoted)."""
    return subprocess.list2cmdline(command)


@dataclass
class Match:
    seed: int
    log: Path
    write_dir: Path
    command: list[str]
    process: subprocess.Popen | None = None
    exit_code: int | None = None


@dataclass
class Batch:
    folder: Path
    map_id: str
    matches: list[Match] = field(default_factory=list)

    def running(self) -> list[Match]:
        return [m for m in self.matches if m.process and m.exit_code is None]

    def poll(self) -> None:
        for m in self.running():
            m.exit_code = m.process.poll()

    def stop_all(self) -> None:
        for m in self.running():
            m.process.kill()
            m.exit_code = m.process.wait()


def prepare_batch(
    runs: Path, exe: Path, game: Path, map_id: str, sides: list[list[dict]], seeds: list[int],
    settings: Path | None, now: datetime | None = None,
) -> Batch:  # fmt: skip
    """The batch's folder, setup file and per-match write folders; nothing started."""
    folder = runs / (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")  # local time
    folder.mkdir(parents=True, exist_ok=False)
    out = folder / "logs"
    setup = folder / "setup.json"
    setup.write_text(json.dumps(setup_record(map_id, sides, out), indent=1), encoding="utf-8")
    batch = Batch(folder, map_id)
    for seed in seeds:
        write_dir = folder / f"match-{seed}"
        write_dir.mkdir()
        if settings and settings.exists():
            shutil.copy2(settings, write_dir / "settings.reg")
        command = match_command(exe, game, setup, seed, write_dir)
        batch.matches.append(Match(seed, out / f"match-{seed}.jsonl", write_dir, command))
    return batch


def start_batch(batch: Batch) -> None:
    """Every match at once; an argument list, never a shell."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for m in batch.matches:
        m.process = subprocess.Popen(
            m.command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags
        )
