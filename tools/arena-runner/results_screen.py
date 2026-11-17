"""The results screen: the batch's totals and one row per match to rewatch."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import batch as batch_module
import summary


class ResultsScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app, batch: batch_module.Batch, logs: list) -> None:
        super().__init__(parent, padding=10)
        self.app = app
        self.batch = batch
        ends = [log.end for log in logs]
        totals = summary.totals(ends)

        tiles = ttk.Frame(self)
        tiles.pack(fill="x")
        average = (
            summary.clock(totals.average_seconds) if totals.average_seconds is not None else "-"
        )
        for value, label in (
            (totals.wins_a, "side A wins"),
            (totals.wins_b, "side B wins"),
            (totals.draws, "draws"),
            (totals.stuck, "stuck (15 min)"),
            (average, "average time to a win"),
        ):
            box = ttk.Frame(tiles, padding=(0, 0, 28, 0))
            box.pack(side="left")
            ttk.Label(box, text=str(value), font=("Segoe UI", 18, "bold")).pack(anchor="w")
            ttk.Label(box, text=label).pack(anchor="w")

        columns = ("seed", "result", "time", "lost_a", "lost_b")
        self.table = ttk.Treeview(
            self, columns=columns, show="headings", height=12, selectmode="browse"
        )
        for column, heading, width in zip(
            columns,
            ("Seed", "Result", "Time", "Lost by A", "Lost by B"),
            (130, 140, 80, 90, 90),
            strict=True,
        ):
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, anchor="w")
        for match, end in zip(batch.matches, ends, strict=True):
            lost = (end or {}).get("lost", ["-", "-"])
            time = summary.clock(summary.result_seconds(end)) if end else "-"
            self.table.insert(
                "",
                "end",
                iid=str(match.seed),
                values=(match.seed, summary.RESULT_WORDS[summary.outcome(end)], time, *lost),
            )
        self.table.pack(fill="x", pady=12)
        if batch.matches:
            self.table.selection_set(str(batch.matches[0].seed))

        buttons = ttk.Frame(self)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Watch map", command=lambda: self._watch(False)).pack(side="left")
        ttk.Button(buttons, text="Watch 3D", command=lambda: self._watch(True)).pack(
            side="left", padx=6
        )
        ttk.Button(buttons, text="Copy command", command=self._copy).pack(side="left")
        ttk.Button(buttons, text="New batch", command=app.show_setup).pack(side="right")
        ttk.Label(
            self,
            text=(
                "Pick a row, then Watch map (from above, with each bot's route, targets and "
                "reasons) or Watch 3D (the game's own mechs and weapons). Copy command copies "
                "the line that plays that exact match again. Stuck means no side won within "
                "15 minutes."
            ),
            style="Muted.TLabel",
            wraplength=1100,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))
        self.note = ttk.Label(self, text=f"Logs and setup: {batch.folder}")
        self.note.pack(anchor="w", pady=(12, 0))

    def _match(self) -> batch_module.Match | None:
        chosen = self.table.selection()
        return (
            next((m for m in self.batch.matches if str(m.seed) == chosen[0]), None)
            if chosen
            else None
        )

    def _watch(self, three_d: bool) -> None:
        match = self._match()
        if match and match.log.exists():
            batch_module.start_replay(self.batch, match, three_d, self.app.exe, self.app.game)

    def _copy(self) -> None:
        """The match's exact command, its own write folder included, to rerun it."""
        match = self._match()
        if match:
            self.clipboard_clear()
            self.clipboard_append(batch_module.command_text(match.command))
            self.note.configure(text=f"Copied the command for seed {match.seed}.")
