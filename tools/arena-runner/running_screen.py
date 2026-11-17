"""The running screen: one small live map per match, filled in as each ends."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

import batch as batch_module
import summary
from live_log import LiveLog

TILE_PIXELS = 220  # a tile's map, long side
COLUMNS = 5
POLL_MS = 200
SIDE_COLORS = ("#3d7be0", "#d9463b")  # the replays' side A blue and side B red
DOT = 4


class RunningScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app, batch: batch_module.Batch) -> None:
        super().__init__(parent, padding=10)
        self.app = app
        self.batch = batch
        catalog = app.catalog
        image = tk.PhotoImage(file=str(catalog.terrain_picture(batch.map_id)))
        self.step = max(1, math.ceil(max(image.width(), image.height()) / TILE_PIXELS))
        self.map_image = image.subsample(self.step)
        self.place = catalog.terrain_place(batch.map_id)
        self.logs = [LiveLog(m.log) for m in batch.matches]
        self.tiles: list[tuple[tk.Canvas, ttk.Label]] = []

        top = ttk.Frame(self)
        top.pack(fill="x")
        self.headline = ttk.Label(top, text="", font=("Segoe UI", 11, "bold"))
        self.headline.pack(side="left")
        self.results_button = ttk.Button(
            top, text="See results", state="disabled", command=self._results
        )
        self.results_button.pack(side="right")
        ttk.Button(top, text="Stop all", command=self._stop).pack(side="right", padx=8)
        ttk.Label(
            self,
            text=(
                "The matches run hidden, much faster than real time; each small map follows "
                "one match as the game writes its log (blue side A, red side B). Click a "
                "finished map to watch it. See results opens when every match is done."
            ),
            style="Muted.TLabel",
            wraplength=1100,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        grid = ttk.Frame(self, padding=(0, 10))
        grid.pack(fill="both", expand=True)
        for i, match in enumerate(batch.matches):
            cell = ttk.Frame(grid, padding=4)
            cell.grid(row=i // COLUMNS, column=i % COLUMNS, sticky="n")
            canvas = tk.Canvas(
                cell,
                width=self.map_image.width(),
                height=self.map_image.height(),
                highlightthickness=2,
            )
            canvas.create_image(0, 0, image=self.map_image, anchor="nw")
            canvas.pack()
            canvas.bind("<Button-1>", lambda e, k=i: self._tile_menu(e, k))
            label = ttk.Label(cell, text=f"seed {match.seed}: starting")
            label.pack(anchor="w")
            self.tiles.append((canvas, label))
        self.after(POLL_MS, self._poll)

    def _to_pixel(self, x: float, z: float) -> tuple[float, float]:
        """World meters to a tile's pixels (the catalog's placement, shrunk by step)."""
        cell = self.place["cell"] * self.step
        return (x - self.place["x0"]) / cell, (self.place["z_top"] - z) / cell

    def _draw(self, index: int) -> None:
        canvas, label = self.tiles[index]
        log, match = self.logs[index], self.batch.matches[index]
        canvas.delete("mech")
        for mech in log.mechs.values():
            px, py = self._to_pixel(mech.x, mech.z)
            color = SIDE_COLORS[mech.side]
            if mech.standing:
                canvas.create_oval(
                    px - DOT, py - DOT, px + DOT, py + DOT, fill=color, outline="white", tags="mech"
                )
            else:
                canvas.create_line(
                    px - DOT, py - DOT, px + DOT, py + DOT, fill=color, width=2, tags="mech"
                )
                canvas.create_line(
                    px - DOT, py + DOT, px + DOT, py - DOT, fill=color, width=2, tags="mech"
                )
        result = summary.outcome(log.end)
        if result == "running":
            if match.stopped:
                text = f"seed {match.seed}: stopped at {summary.clock(log.t)}"
            elif match.exit_code not in (None, 0):
                text = f"seed {match.seed}: did not start (exit {match.exit_code})"
            else:
                standing = f"standing A {log.standing(0)} B {log.standing(1)}"
                text = f"seed {match.seed}: {summary.clock(log.t)}, {standing}"
        else:
            names = {
                "A": "side A won",
                "B": "side B won",
                "draw": "draw",
                "stuck": "stuck (15 min)",
            }
            text = f"seed {match.seed}: {names[result]} at {summary.clock(summary.result_seconds(log.end))}"
            canvas.configure(
                highlightbackground=SIDE_COLORS[0 if result == "A" else 1]
                if result in "AB"
                else "gray"
            )
        label.configure(text=text)

    def _poll(self) -> None:
        self.batch.poll()
        for i, log in enumerate(self.logs):
            if log.read_new() or self.batch.matches[i].exit_code is not None:
                self._draw(i)
        done = sum(1 for m in self.batch.matches if m.exit_code is not None)
        self.headline.configure(
            text=f"{self.batch.map_id}: {done} of {len(self.batch.matches)} matches done"
        )
        if done == len(self.batch.matches):
            self.results_button.configure(state="normal")
            return
        self.after(POLL_MS, self._poll)

    def _stop(self) -> None:
        self.batch.stop_all()

    def _results(self) -> None:
        self.app.show_results(self.batch, self.logs)

    def _tile_menu(self, event: tk.Event, index: int) -> None:
        match = self.batch.matches[index]
        if match.exit_code is None or not match.log.exists():
            return  # a replay reads a finished log
        menu = tk.Menu(self, tearoff=False)
        for label, three_d in (("Watch map", False), ("Watch 3D", True)):
            menu.add_command(
                label=label,
                command=lambda d=three_d: batch_module.start_replay(
                    self.batch, match, d, self.app.exe, self.app.game
                ),
            )
        menu.tk_popup(event.x_root, event.y_root)
