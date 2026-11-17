"""Runs a batch of arena matches from the command line, for scripts and agents.

The same batch the window runs (docs/arena.md, "Arena runner"): every match at
once, hidden, each with its own random seed and write folder, then the
results. Nothing to click, so it suits comparing the AI before and after a
change.

    python tools/arena-runner/run_batch.py SETUP.json [--matches N]
        [--exe PATH --game DIR] [--timeout MINUTES] [--json]

SETUP.json is the runner's setup (the window's Save setup writes one; see
tools/arena-runner/examples/), not the game's own --arena setup file.
--exe and --game default to the paths the window keeps in settings.json;
give both the first time, and they are kept once the game's lists read.

It prints one line per match and the totals (or results.json with --json),
writes results.json into the batch folder, and exits 0 when every match
reached a result (a stuck match is a result), 1 when one crashed, was
stopped or timed out, 2 when the setup or paths can't be used. Errors go to
stderr.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import batch as batch_module
import catalog as catalog_module
import summary
from live_log import LiveLog
from runner_home import HOME, load_settings, save_settings

POLL_SECONDS = 0.5
# A match ends by itself at the setup's 15-minute limit (stuck); this is a
# guard against a hung game process, not a match limit.
DEFAULT_TIMEOUT_MINUTES = 20


def fail(message: str) -> int:
    print(f"run_batch: {message}", file=sys.stderr)
    return 2


def match_result(match: batch_module.Match, end: dict | None) -> dict:
    """One match's row, as the results screen shows it."""
    return {
        "seed": match.seed,
        "result": summary.outcome(end),
        "seconds": round(summary.result_seconds(end), 1) if end else None,
        "lost": (end or {}).get("lost"),
        "exit_code": match.exit_code,
        "stopped": match.stopped,
        "log": str(match.log),
        "command": batch_module.command_text(match.command),
    }


def batch_results(
    batch: batch_module.Batch, ends: list[dict | None], exe: Path, game: Path, setup: Path
) -> dict:
    totals = summary.totals(ends)
    return {
        "folder": str(batch.folder),
        "exe": str(exe),
        "game": str(game),
        "setup": str(setup),
        "map": batch.map_id,
        "wins_a": totals.wins_a,
        "wins_b": totals.wins_b,
        "draws": totals.draws,
        "stuck": totals.stuck,
        "average_seconds_to_a_win": totals.average_seconds,
        "matches": [match_result(m, e) for m, e in zip(batch.matches, ends, strict=True)],
    }


def report_lines(results: dict) -> list[str]:
    lines = [f"batch {results['folder']} on {results['map']}"]
    for m in results["matches"]:
        time_text = summary.clock(m["seconds"]) if m["seconds"] is not None else "-"
        lost = m["lost"] or ["-", "-"]
        words = summary.RESULT_WORDS[m["result"]]
        lines.append(f"  seed {m['seed']}: {words}, time {time_text}, lost A {lost[0]} B {lost[1]}")
    average = results["average_seconds_to_a_win"]
    average_text = summary.clock(average) if average is not None else "-"
    lines.append(
        f"side A wins {results['wins_a']}, side B wins {results['wins_b']}, "
        f"draws {results['draws']}, stuck {results['stuck']}, "
        f"average time to a win {average_text}"
    )
    return lines


def find_paths(
    exe_arg: str | None, game_arg: str | None, settings: dict
) -> tuple[Path, Path] | str:
    """The exe and game folder from the arguments, else the window's settings,
    as absolute paths; or what is wrong with them. An empty value is missing,
    never the current folder."""
    exe_text = exe_arg or settings.get("exe", "")
    game_text = game_arg or settings.get("game", "")
    if not exe_text:
        return "give --exe, the built mw3.exe (runtime/mw3-re/docs/building.md)"
    if not game_text:
        return "give --game, the MechWarrior 3 game folder"
    exe, game = Path(exe_text).resolve(), Path(game_text).resolve()
    if not exe.is_file():
        return f"no mw3.exe at {exe}"
    if not game.is_dir():
        return f"no game folder at {game}"
    return exe, game


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a batch of arena matches, hidden.")
    parser.add_argument("setup", type=Path, help="the runner's setup file (see examples/)")
    parser.add_argument("--matches", type=int, help="1 to 10; overrides the setup's count")
    parser.add_argument("--exe", help="the built mw3.exe")
    parser.add_argument("--game", help="the MechWarrior 3 game folder")
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_MINUTES,
        help=f"minutes before every match still going is stopped ({DEFAULT_TIMEOUT_MINUTES})",
    )  # fmt: skip
    parser.add_argument("--json", action="store_true", help="print results.json, not lines")
    args = parser.parse_args()

    settings = load_settings()
    found = find_paths(args.exe, args.game, settings)
    if isinstance(found, str):
        return fail(found)
    exe, game = found
    setup = args.setup.resolve()
    try:  # before the catalog, which can take a while on a first run
        state = json.loads(setup.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return fail(f"that setup can't be read: {error}")
    if args.matches is not None:
        state["matches"] = args.matches

    try:
        catalog = catalog_module.ensure_catalog(exe, game, HOME)
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        return fail(f"the game's lists could not be read with {exe} and {game}:\n{error}")
    if args.exe or args.game:  # kept only once they proved to work
        settings.update(exe=str(exe), game=str(game))
        save_settings(settings)

    try:
        problem = catalog_module.setup_problem(state, catalog)
    except KeyError as error:
        problem = f"it has no field {error}"
    except (TypeError, AttributeError) as error:
        problem = f"a field has the wrong kind of value ({error})"
    if problem:
        return fail(f"that setup can't be used: {problem}")

    batch = batch_module.prepare_batch(
        HOME / "runs", exe, game, state["map"], state["sides"],
        batch_module.new_seeds(state["matches"]), batch_module.user_write_dir() / "settings.reg",
    )  # fmt: skip
    deadline = time.monotonic() + args.timeout * 60
    try:
        batch_module.start_batch(batch)
        while batch.running() and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
            batch.poll()
    except KeyboardInterrupt:
        pass
    finally:
        batch.stop_all()  # nothing left running, however this ends

    ends = []
    for match in batch.matches:
        log = LiveLog(match.log)
        log.read_new()
        ends.append(log.end)
    results = batch_results(batch, ends, exe, game, setup)
    (batch.folder / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1) if args.json else "\n".join(report_lines(results)))
    every_match_has_a_result = all(m["result"] != "running" for m in results["matches"])
    return 0 if every_match_has_a_result else 1


if __name__ == "__main__":
    sys.exit(main())
