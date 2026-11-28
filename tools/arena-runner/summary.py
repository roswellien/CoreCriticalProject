"""Plain-words results and pilot descriptions for the arena runner."""

from __future__ import annotations

from dataclasses import dataclass

STUCK_SECONDS = 15 * 60  # batch.STUCK_MINUTES: the setup's time limit
# The game logs 5 more seconds after the result is settled (arena.h,
# kAftermathSeconds), so a log's end line is that much later than the result.
AFTERMATH_SECONDS = 5


RESULT_WORDS = {  # outcome() in plain words, for the results screen and run_batch.py
    "A": "side A won",
    "B": "side B won",
    "draw": "draw",
    "stuck": "stuck",
    "running": "did not finish",
}


def result_seconds(end: dict) -> float:
    """The match's time as the game's own result line gives it: the end
    line's time less the aftermath."""
    return max(0.0, end.get("t", 0.0) - AFTERMATH_SECONDS)


def outcome(end: dict | None) -> str:
    """The match's result: A or B for a winner, draw when both sides fell
    together, stuck when it reached its time limit (the game then names the
    side with more mechs standing, but nobody won it), running with no end
    line."""
    if end is None:
        return "running"
    if result_seconds(end) >= STUCK_SECONDS:
        return "stuck"
    winner = end.get("winner", "draw")
    return winner if winner in ("A", "B") else "draw"


def clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


@dataclass
class BatchTotals:
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    stuck: int = 0
    average_seconds: float | None = None


def totals(ends: list[dict | None]) -> BatchTotals:
    """Wins per side, draws and stuck matches, and the average time of the
    matches a side won (a stuck match's time is the limit, not a result)."""
    t = BatchTotals()
    decided = []
    for end in ends:
        result = outcome(end)
        if result == "A":
            t.wins_a += 1
        elif result == "B":
            t.wins_b += 1
        elif result == "draw":
            t.draws += 1
        elif result == "stuck":
            t.stuck += 1
        if result in ("A", "B"):
            decided.append(result_seconds(end))
    if decided:
        t.average_seconds = sum(decided) / len(decided)
    return t


def pilot_summary(numbers: dict) -> str:
    """One line from a preset's numbers (arena_catalog.cpp, preset_numbers)."""
    parts = [f"attacks from {numbers.get('attack_m', 0):.0f} m"]
    burst, rest = numbers.get("burst_s", 0), numbers.get("rest_s", 0)
    parts.append(f"fires {burst:g} s bursts, {rest:g} s apart")
    if "attack_for_s" in numbers:
        parts.append(f"presses the attack {numbers['attack_for_s']:g} s")
    if "breaks_off_after_damage" in numbers:
        parts.append(
            f"breaks off after losing {numbers['breaks_off_after_damage'] * 100:.0f}% of its health"
        )
    if "breaks_off_below_health" in numbers:
        parts.append(f"breaks off below {numbers['breaks_off_below_health'] * 100:.0f}% health")
    parts.append(f"aim error {numbers.get('aim_error', 0):g}")
    return ", ".join(parts)


def preset_key(preset: dict) -> str:
    return f"{preset['world']}/{preset['mission']}/{preset['record']}"


def pilot_label(preset: dict, short_names: dict[str, str], mech_names: dict[str, str]) -> str:
    """The short list's name when it has one, else where the preset comes
    from: "c1 ia1, Enemy_01 (Firefly)". The game data has no mission titles."""
    named = short_names.get(preset_key(preset))
    if named:
        return named
    mech = mech_names.get(preset.get("mech", ""), preset.get("mech", ""))
    return f"{preset['world']} {preset['mission']}, {preset['record']} ({mech})"
