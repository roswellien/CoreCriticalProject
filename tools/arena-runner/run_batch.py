"""Runs a batch of arena matches from the command line, for scripts and agents.

The same batch the window runs (docs/arena.md, "Arena runner"): every match at
once, hidden, each with its own random seed and write folder, then the
results. Nothing to click, so it suits comparing the AI before and after a
change.

    python tools/arena-runner/run_batch.py SETUP.json [--matches N]
        [--exe PATH --game DIR] [--json]

SETUP.json is a setup saved by the window's Save setup button, or written by
hand in the same shape (see tools/arena-runner/examples/). --exe and --game
default to the paths the window keeps in settings.json; give both the first
time, and they are kept.

It prints one line per match and the totals, writes results.json into the
batch folder, and exits 0 when every match finished, 1 when one didn't
(crashed or stuck), 2 when the setup or paths can't be used.
"""

from __future__ import annotations

import argparse
import json
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


def match_result(match: batch_module.Match, end: dict | None) -> dict:
    """One match's row, as the results screen shows it."""
    return {
        "seed": match.seed,
        "result": summary.outcome(end),
        "seconds": round(summary.result_seconds(end), 1) if end else None,
        "lost": (end or {}).get("lost"),
        "exit_code": match.exit_code,
        "log": str(match.log),
        "command": batch_module.command_text(match.command),
    }


def batch_results(batch: batch_module.Batch, ends: list[dict | None]) -> dict:
    totals = summary.totals(ends)
    return {
        "folder": str(batch.folder),
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
        lines.append(
            f"  seed {m['seed']}: {summary.RESULT_WORDS[m['result']]}, time {time_text}, lost A {lost[0]} B {lost[1]}"
        )
    average = results["average_seconds_to_a_win"]
    lines.append(
        f"side A wins {results['wins_a']}, side B wins {results['wins_b']}, "
        f"draws {results['draws']}, stuck {results['stuck']}, average time to a win "
        f"{summary.clock(average) if average is not None else '-'}"
    )
    return lines


def paths(args: argparse.Namespace) -> tuple[Path, Path] | None:
    """The exe and game folder from the arguments, else the window's settings."""
    settings = load_settings()
    exe = Path(args.exe or settings.get("exe", ""))
    game = Path(args.game or settings.get("game", ""))
    if not exe.is_file() or not game.is_dir():
        return None
    if args.exe or args.game:
        settings.update(exe=str(exe), game=str(game))
        save_settings(settings)
    return exe, game


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a batch of arena matches, hidden.")
    parser.add_argument("setup", type=Path, help="a setup saved by the window, or the same shape")
    parser.add_argument("--matches", type=int, help="1 to 10; overrides the setup's count")
    parser.add_argument("--exe", help="the built mw3.exe")
    parser.add_argument("--game", help="the MechWarrior 3 game folder")
    parser.add_argument("--json", action="store_true", help="print results.json, not lines")
    args = parser.parse_args()

    found = paths(args)
    if not found:
        print("run_batch: give --exe (the built mw3.exe) and --game (the game folder)")
        return 2
    exe, game = found
    try:
        state = json.loads(args.setup.read_text(encoding="utf-8"))
        if args.matches is not None:
            state["matches"] = args.matches
        catalog = catalog_module.ensure_catalog(exe, game, HOME)
        problem = catalog_module.setup_problem(state, catalog)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        problem = f"it can't be read ({error})"
    if problem:
        print(f"run_batch: that setup can't be used: {problem}")
        return 2

    batch = batch_module.prepare_batch(
        HOME / "runs", exe, game, state["map"], state["sides"],
        batch_module.new_seeds(state["matches"]), batch_module.user_write_dir() / "settings.reg",
    )  # fmt: skip
    batch_module.start_batch(batch)
    try:
        while batch.running():
            time.sleep(POLL_SECONDS)
            batch.poll()
    except KeyboardInterrupt:
        batch.stop_all()

    ends = []
    for match in batch.matches:
        log = LiveLog(match.log)
        log.read_new()
        ends.append(log.end)
    results = batch_results(batch, ends)
    (batch.folder / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1) if args.json else "\n".join(report_lines(results)))
    all_finished = all(m["result"] in ("A", "B", "draw") for m in results["matches"])
    return 0 if all_finished else 1


if __name__ == "__main__":
    sys.exit(main())
