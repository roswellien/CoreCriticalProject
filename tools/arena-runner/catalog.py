"""The game's own lists for the arena runner: maps, mechs, loadouts, pilots.

Written by ``mw3 GAME --arena-catalog DIR`` (runtime/mw3-re, arena_catalog.h)
into a cache folder, and written again whenever ``mw3.exe`` changes, so the
window only ever offers what that build of the game can run.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import batch
import summary

CATALOG_VERSION = 1
STAMP_FILE = "stamp.json"


@dataclass
class Catalog:
    folder: Path
    maps: list[dict]
    mechs: list[dict]
    presets: list[dict]

    def terrain_picture(self, map_id: str) -> Path:
        return self.folder / "terrain" / f"{map_id}.ppm"

    def terrain_place(self, map_id: str) -> dict:
        """x0, z_top, cell (meters per pixel), width and height of the picture."""
        return json.loads((self.folder / "terrain" / f"{map_id}.json").read_text(encoding="utf-8"))

    def mech_picture(self, mech_id: str) -> Path | None:
        path = self.folder / "mechs" / f"{mech_id}.ppm"
        return path if path.exists() else None

    def mech(self, mech_id: str) -> dict:
        return next(m for m in self.mechs if m["id"] == mech_id)


def exe_stamp(exe: Path) -> dict:
    """What identifies a build of the game: its size and modified time."""
    info = exe.stat()
    return {"exe": str(exe), "size": info.st_size, "mtime_ns": info.st_mtime_ns}


def load_catalog(folder: Path) -> Catalog:
    data = json.loads((folder / "catalog.json").read_text(encoding="utf-8"))
    if data.get("version") != CATALOG_VERSION:
        raise ValueError(f"catalog version {data.get('version')}, expected {CATALOG_VERSION}")
    return Catalog(folder, data["maps"], data["mechs"], data["presets"])


def setup_problem(state: dict, catalog: Catalog) -> str:
    """What a saved setup names that this game build lacks; "" when nothing.
    A setup saved with another build or mod set may name a map, mech,
    loadout or pilot this catalog doesn't have. Used by the window's Load
    setup and by run_batch.py."""
    if state["map"] not in {m["id"] for m in catalog.maps}:
        return f"this game has no arena map {state['map']}"
    if not batch.MIN_MATCHES <= state["matches"] <= batch.MAX_MATCHES:
        return f"{state['matches']} matches ({batch.MIN_MATCHES} to {batch.MAX_MATCHES})"
    pilots = {summary.preset_key(p) for p in catalog.presets}
    mechs = {m["id"]: m for m in catalog.mechs}
    try:
        batch.setup_record(state["map"], state["sides"], Path("."))
    except ValueError as error:
        return str(error)
    for side in state["sides"]:
        for bot in side:
            mech = mechs.get(bot["mech"])
            if not mech:
                return f"this game has no mech {bot['mech']}"
            loadout = bot.get("loadout", 0)  # the game's default too (docs/arena.md)
            if not 0 <= loadout < len(mech["loadouts"]):
                return f"{mech['name']} has no loadout {loadout}"
            key = summary.preset_key(bot["preset"])
            if key not in pilots:
                return f"this game has no pilot {key}"
    return ""


def catalog_is_current(folder: Path, exe: Path) -> bool:
    stamp = folder / STAMP_FILE
    if not stamp.exists() or not (folder / "catalog.json").exists():
        return False
    return json.loads(stamp.read_text(encoding="utf-8")) == exe_stamp(exe)


def catalog_command(exe: Path, game: Path, folder: Path, write_dir: Path) -> list[str]:
    """The catalog run; its own write folder keeps the player's mw3.log as it was."""
    return [str(exe), str(game), "--arena-catalog", str(folder), "--write-dir", str(write_dir)]


def ensure_catalog(exe: Path, game: Path, cache: Path, force: bool = False) -> Catalog:
    """The cached catalog, made again first when the game build changed, or
    when `force` asks (the window's Reload game lists: mods or game files
    changed, which the exe's stamp can't see)."""
    folder = cache / "catalog"
    if force or not catalog_is_current(folder, exe):
        write_dir = cache / "catalog-write"
        write_dir.mkdir(parents=True, exist_ok=True)
        done = subprocess.run(
            catalog_command(exe, game, folder, write_dir),
            capture_output=True, text=True, timeout=300, check=False,  # the exit code is read below
        )  # fmt: skip
        if done.returncode != 0:
            log = write_dir / "mw3.log"
            detail = (
                log.read_text(encoding="utf-8", errors="replace")[-2000:] if log.exists() else ""
            )
            raise RuntimeError(f"mw3 --arena-catalog failed (exit {done.returncode})\n{detail}")
        (folder / STAMP_FILE).write_text(json.dumps(exe_stamp(exe)), encoding="utf-8")
    return load_catalog(folder)
