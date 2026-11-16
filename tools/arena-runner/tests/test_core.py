"""Tests for the arena runner's modules that need no window and no game.

Run: python -m unittest discover tools/arena-runner/tests
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

# The folder's name has a hyphen, so it can't be a package: import from it directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import batch
import live_log
import summary

BOT = {
    "mech": "thor",
    "loadout": 1,
    "preset": {"world": "c1", "mission": "ia1", "record": "Enemy_01"},
}


class SeedsTest(unittest.TestCase):
    def test_seeds_are_all_different_and_in_range(self):
        for count in (1, 5, 10):
            seeds = batch.new_seeds(count, random.Random(count))
            self.assertEqual(len(set(seeds)), count)
            self.assertTrue(all(0 <= s <= batch.MAX_SEED for s in seeds))

    def test_match_count_is_one_to_ten(self):
        for bad in (0, 11):
            with self.assertRaises(ValueError):
                batch.new_seeds(bad)


class BatchTest(unittest.TestCase):
    def test_setup_and_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = root / "settings.reg"
            settings.write_text("players settings", encoding="utf-8")
            b = batch.prepare_batch(
                root / "runs", Path("C:/game/mw3.exe"), Path("C:/MW3"), "c3mp1", [[BOT], [BOT]], [7, 9],
                settings, datetime(2026, 11, 16, 12, 0, 0, tzinfo=UTC),
            )  # fmt: skip
            setup = json.loads((b.folder / "setup.json").read_text(encoding="utf-8"))
            self.assertEqual(b.folder.name, "20261116-120000")
            self.assertEqual(setup["map"], "c3mp1")
            self.assertEqual(setup["minutes"], batch.STUCK_MINUTES)
            self.assertEqual(setup["sides"][0][0]["loadout"], 1)
            self.assertEqual([m.seed for m in b.matches], [7, 9])
            for m in b.matches:
                # Each match its own write folder, starting from the player's settings.
                self.assertEqual(
                    (m.write_dir / "settings.reg").read_text(encoding="utf-8"), "players settings"
                )
                self.assertIn("--write-dir", m.command)
                self.assertEqual(m.command[m.command.index("--seed") + 1], str(m.seed))
                self.assertEqual(m.log.name, f"match-{m.seed}.jsonl")
            self.assertIn(
                "--replay3d", batch.replay_command(Path("x.exe"), Path("g"), Path("l"), True)
            )

    def test_a_side_needs_one_to_eight(self):
        with self.assertRaises(ValueError):
            batch.setup_record("c3mp1", [[], [BOT]], Path("out"))
        with self.assertRaises(ValueError):
            batch.setup_record("c3mp1", [[BOT] * 9, [BOT]], Path("out"))


def write_lines(path: Path, records: list[dict], last_without_newline: str = "") -> None:
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.write(last_without_newline)


START = {"type": "start", "mechs": [{"id": 0, "side": 0}, {"id": 1, "side": 1}]}


def state(t: float, x: float) -> dict:
    return {"type": "state", "t": t, "mechs": [
        {"id": 0, "side": 0, "pos": [x, 0, 5], "standing": True},
        {"id": 1, "side": 1, "pos": [9, 0, 9], "standing": True},
    ]}  # fmt: skip


class LiveLogTest(unittest.TestCase):
    def test_follows_a_log_as_it_grows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "match-1.jsonl"
            log = live_log.LiveLog(path)
            self.assertFalse(log.read_new())  # not there yet
            write_lines(path, [START, state(0.1, 1.0)], '{"type": "state", "t": 0.2')
            self.assertTrue(log.read_new())
            self.assertEqual((log.mechs[0].x, log.mechs[0].z), (1.0, 5))
            self.assertEqual(log.t, 0.1)  # the half-written line waits
            write_lines(path, [], ', "mechs": []}\n')
            write_lines(
                path,
                [
                    {"type": "destroyed", "id": 1, "t": 3.0},
                    {"type": "end", "winner": "A", "t": 8.0},
                ],
            )
            log.read_new()
            self.assertEqual(log.bad_lines, 0)
            self.assertFalse(log.mechs[1].standing)
            self.assertEqual((log.standing(0), log.standing(1)), (1, 0))
            self.assertEqual(log.end["winner"], "A")


class SummaryTest(unittest.TestCase):
    def test_outcomes(self):
        self.assertEqual(summary.outcome(None), "running")
        self.assertEqual(summary.outcome({"winner": "B", "t": 90}), "B")
        self.assertEqual(summary.outcome({"winner": "draw", "t": 90}), "draw")
        self.assertEqual(
            summary.outcome({"winner": "draw", "t": summary.STUCK_SECONDS + 5}), "stuck"
        )

    def test_totals_average_only_decided_matches(self):
        ends = [
            {"winner": "A", "t": 60},
            {"winner": "B", "t": 120},
            {"winner": "draw", "t": 905},
            None,
        ]
        t = summary.totals(ends)
        self.assertEqual((t.wins_a, t.wins_b, t.draws, t.stuck), (1, 1, 0, 1))
        self.assertEqual(t.average_seconds, 90)
        self.assertEqual(summary.clock(150.4), "2:30")

    def test_pilot_words(self):
        numbers = {"attack_m": 800.0, "burst_s": 5.0, "rest_s": 1.0, "attack_for_s": 25.0,
                   "breaks_off_after_damage": 0.5, "aim_error": 1.2}  # fmt: skip
        self.assertEqual(
            summary.pilot_summary(numbers),
            "attacks from 800 m, fires 5 s bursts, 1 s apart, presses the attack 25 s, "
            "breaks off after losing 50% of its health, aim error 1.2",
        )
        preset = {"world": "c1", "mission": "ia1", "record": "Enemy_01", "mech": "firefly"}
        self.assertEqual(
            summary.pilot_label(preset, {}, {"firefly": "Firefly"}), "c1 ia1, Enemy_01 (Firefly)"
        )
        self.assertEqual(
            summary.pilot_label(preset, {"c1/ia1/Enemy_01": "Early grunt"}, {}), "Early grunt"
        )


if __name__ == "__main__":
    unittest.main()
