"""The setup screen: the map picker, how many matches, and the two sides."""

from __future__ import annotations

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import batch as batch_module
import catalog as catalog_module
import summary
import theme

THUMB_PIXELS = 150  # a map thumbnail's long side
PICTURE_ZOOM = 3  # the mech lab's icons are about 40 pixels wide
MAP_COLUMNS = 5
SIDE_NAMES = ("Side A (blue)", "Side B (red)")
HOW_TO = (
    "AI bots fight each other here so changes to the AI can be measured. "
    "1. Click a map.  2. Build each side: Add mech, then pick its chassis, loadout and pilot "
    "under Selected mech.  3. Set Matches to run and press Run. Every match gets its own "
    "random seed, so a batch shows how a setup does on average. To test an AI change, save "
    "the setup, run it on the build before and after the change, and compare the results."
)


def loadout_lines(loadout: dict) -> str:
    """What the loadout carries, one weapon per line, then the mech's numbers."""
    lines = []
    for w in loadout["weapons"]:
        count = f"{w['count']} x " if w["count"] > 1 else ""
        lines.append(f"{count}{w['weapon']}  ({w['where']})")
    for a in loadout["ammo"]:
        lines.append(f"ammo: {a['rounds']} rounds for {a['weapon']}")
    sinks = f"{loadout['heat_sinks']} {'double ' if loadout['double_sinks'] else ''}heat sinks"
    jets = f", {loadout['jump_jets']} jump jets" if loadout["jump_jets"] else ", no jump jets"
    lines.append(
        f"armor {loadout['armor']}, {loadout['walk_kph']:.0f} / {loadout['run_kph']:.0f} km/h, {sinks}{jets}"
    )
    return "\n".join(lines)


class SetupScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app, setups: Path) -> None:
        super().__init__(parent, padding=10)
        self.app = app
        self.catalog = app.catalog
        self.setups = setups
        self.images: dict[str, tk.PhotoImage] = {}  # kept, or tkinter drops them
        self.mech_names = {m["id"]: m["name"] for m in self.catalog.mechs}
        self.pilots = self._pilot_choices()
        self.map_id = tk.StringVar(value=self.catalog.maps[0]["id"])
        self.matches = tk.IntVar(value=1)
        default = self._new_bot()
        self.sides: list[list[dict]] = [[dict(default)], [dict(default)]]
        self.selected = (0, 0)
        ttk.Label(self, text=HOW_TO, style="Muted.TLabel", wraplength=1100, justify="left").pack(
            anchor="w", pady=(0, 8)
        )
        self._build_maps()
        self._build_controls()
        self._build_sides()
        self._build_editor()
        self._refresh_lists()
        self._load_editor()

    # --- choices ---------------------------------------------------------

    def _pilot_choices(self) -> list[tuple[str, dict]]:
        """The short list first (by its names), then every other enemy preset."""
        short, rest = [], []
        for preset in self.catalog.presets:
            label = summary.pilot_label(preset, self.app.short_pilots, self.mech_names)
            named = summary.preset_key(preset) in self.app.short_pilots
            (short if named else rest).append((label, preset))
        return sorted(short) + sorted(rest, key=lambda p: p[0])

    def _new_bot(self) -> dict:
        preset = self.pilots[0][1]
        return {
            "mech": self.catalog.mechs[0]["id"],
            "loadout": 0,
            "preset": {k: preset[k] for k in ("world", "mission", "record")},
        }

    def _pilot_of(self, bot: dict) -> tuple[str, dict]:
        key = summary.preset_key(bot["preset"])
        return next(
            ((label, p) for label, p in self.pilots if summary.preset_key(p) == key), ("?", {})
        )

    # --- the map picker --------------------------------------------------

    def _build_maps(self) -> None:
        box = ttk.LabelFrame(self, text="Map (click one)", padding=6)
        box.pack(fill="x")
        for i, m in enumerate(self.catalog.maps):
            image = tk.PhotoImage(file=str(self.catalog.terrain_picture(m["id"])))
            step = max(1, math.ceil(max(image.width(), image.height()) / THUMB_PIXELS))
            thumb = image.subsample(step)
            self.images[f"map-{m['id']}"] = thumb
            button = tk.Radiobutton(
                box, image=thumb, text=m["name"].title(), compound="top", variable=self.map_id,
                value=m["id"], indicatoron=False, selectcolor=theme.ACCENT_DARK, borderwidth=3,
            )  # fmt: skip
            button.grid(row=i // MAP_COLUMNS, column=i % MAP_COLUMNS, padx=4, pady=4)

    # --- matches, run, saved setups -------------------------------------

    def _build_controls(self) -> None:
        row = ttk.Frame(self, padding=(0, 8))
        row.pack(fill="x")
        ttk.Label(row, text="Matches to run (all at once):").pack(side="left")
        ttk.Spinbox(
            row, from_=batch_module.MIN_MATCHES, to=batch_module.MAX_MATCHES, width=4,
            textvariable=self.matches, state="readonly",
        ).pack(side="left", padx=6)  # fmt: skip
        ttk.Button(row, text="Run", style="Accent.TButton", command=self._run).pack(
            side="left", padx=12
        )
        ttk.Button(row, text="Load setup", command=self._load_setup).pack(side="right")
        ttk.Button(row, text="Reload game lists", command=self.app.reload_catalog).pack(
            side="right", padx=(0, 18)
        )
        ttk.Button(row, text="Save setup", command=self._save_setup).pack(side="right", padx=6)

    # --- the two sides ---------------------------------------------------

    def _build_sides(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.lists: list[tk.Listbox] = []
        for side in (0, 1):
            frame = ttk.LabelFrame(row, text=SIDE_NAMES[side], padding=6)
            frame.pack(side="left", fill="both", expand=True, padx=(0 if side == 0 else 6, 0))
            listbox = tk.Listbox(frame, height=8, exportselection=False)
            listbox.pack(fill="both", expand=True)
            listbox.bind("<<ListboxSelect>>", lambda _e, s=side: self._pick_row(s))
            self.lists.append(listbox)
            buttons = ttk.Frame(frame)
            buttons.pack(fill="x", pady=(4, 0))
            ttk.Button(buttons, text="Add mech", command=lambda s=side: self._add(s)).pack(
                side="left"
            )
            ttk.Button(buttons, text="Remove", command=lambda s=side: self._remove(s)).pack(
                side="left", padx=4
            )
            other = 1 - side
            ttk.Button(
                buttons,
                text=f"Copy side {'AB'[other]}",
                command=lambda s=side, o=other: self._copy(o, s),
            ).pack(side="right")

    def _row_text(self, bot: dict) -> str:
        mech = self.catalog.mech(bot["mech"])
        loadout = mech["loadouts"][bot["loadout"]]["name"]
        return f"{mech['name']}  ·  {loadout}  ·  {self._pilot_of(bot)[0]}"

    def _refresh_lists(self) -> None:
        for side, listbox in enumerate(self.lists):
            listbox.delete(0, "end")
            for bot in self.sides[side]:
                listbox.insert("end", self._row_text(bot))
        side, index = self.selected
        self.lists[side].selection_clear(0, "end")
        self.lists[side].selection_set(index)

    def _pick_row(self, side: int) -> None:
        chosen = self.lists[side].curselection()
        if chosen:
            self.selected = (side, chosen[0])
            self.lists[1 - side].selection_clear(0, "end")
            self._load_editor()

    def _add(self, side: int) -> None:
        if len(self.sides[side]) >= 8:
            messagebox.showinfo("Arena runner", "A side has at most 8 mechs.")
            return
        self.sides[side].append(dict(self.sides[side][-1]) if self.sides[side] else self._new_bot())
        self.selected = (side, len(self.sides[side]) - 1)
        self._refresh_lists()
        self._load_editor()

    def _remove(self, side: int) -> None:
        if len(self.sides[side]) <= 1:
            messagebox.showinfo("Arena runner", "A side needs at least one mech.")
            return
        index = self.selected[1] if self.selected[0] == side else len(self.sides[side]) - 1
        del self.sides[side][index]
        self.selected = (side, min(index, len(self.sides[side]) - 1))
        self._refresh_lists()
        self._load_editor()

    def _copy(self, source: int, target: int) -> None:
        self.sides[target] = [json.loads(json.dumps(b)) for b in self.sides[source]]
        self.selected = (target, 0)
        self._refresh_lists()
        self._load_editor()

    # --- the selected mech's editor -------------------------------------

    def _build_editor(self) -> None:
        box = ttk.LabelFrame(self, text="Selected mech", padding=8)
        box.pack(fill="both", expand=True, pady=(8, 0))
        self.picture = ttk.Label(box)
        self.picture.grid(row=0, column=0, rowspan=4, padx=(0, 12), sticky="n")
        self.chassis = ttk.Combobox(
            box, state="readonly", width=24, values=[m["name"] for m in self.catalog.mechs]
        )
        self.loadout = ttk.Combobox(box, state="readonly", width=24)
        self.pilot = ttk.Combobox(
            box, state="readonly", width=48, values=[p[0] for p in self.pilots]
        )
        for column, (label, widget) in enumerate(
            (("Chassis", self.chassis), ("Loadout", self.loadout), ("Pilot", self.pilot))
        ):
            ttk.Label(box, text=label).grid(row=0, column=1 + column, sticky="w")
            widget.grid(row=1, column=1 + column, sticky="w", padx=(0, 10))
        self.chassis.bind("<<ComboboxSelected>>", lambda _e: self._edit("chassis"))
        self.loadout.bind("<<ComboboxSelected>>", lambda _e: self._edit("loadout"))
        self.pilot.bind("<<ComboboxSelected>>", lambda _e: self._edit("pilot"))
        self.details = tk.Text(box, height=7, width=70, relief="flat", background=theme.BG)
        self.details.grid(row=2, column=1, columnspan=2, sticky="nw", pady=6)
        self.pilot_words = ttk.Label(box, wraplength=360, justify="left")
        self.pilot_words.grid(row=2, column=3, sticky="nw", pady=6)

    def _bot(self) -> dict:
        side, index = self.selected
        return self.sides[side][index]

    def _load_editor(self) -> None:
        bot = self._bot()
        mech = self.catalog.mech(bot["mech"])
        self.chassis.set(mech["name"])
        self.loadout.configure(values=[lo["name"] for lo in mech["loadouts"]])
        self.loadout.set(mech["loadouts"][bot["loadout"]]["name"])
        label, preset = self._pilot_of(bot)
        self.pilot.set(label)
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert(
            "1.0",
            f"{mech['name']}, {mech['tons']:.0f} t\n"
            + loadout_lines(mech["loadouts"][bot["loadout"]]),
        )
        self.details.configure(state="disabled")
        words = summary.pilot_summary(preset.get("numbers", {})) if preset else ""
        self.pilot_words.configure(text=f"{label}: {words}")
        picture = self.catalog.mech_picture(mech["id"])
        if picture:
            key = f"mech-{mech['id']}"
            if key not in self.images:
                self.images[key] = tk.PhotoImage(file=str(picture)).zoom(PICTURE_ZOOM)
            self.picture.configure(image=self.images[key], text="")
        else:
            self.picture.configure(image="", text=mech["name"])

    def _edit(self, what: str) -> None:
        bot = self._bot()
        if what == "chassis":
            bot["mech"] = self.catalog.mechs[self.chassis.current()]["id"]
            bot["loadout"] = 0
        elif what == "loadout":
            bot["loadout"] = self.loadout.current()
        else:
            preset = self.pilots[self.pilot.current()][1]
            bot["preset"] = {k: preset[k] for k in ("world", "mission", "record")}
        self._refresh_lists()
        self._load_editor()

    # --- saved setups and the run ---------------------------------------

    def _state(self) -> dict:
        return {"map": self.map_id.get(), "matches": self.matches.get(), "sides": self.sides}

    def _save_setup(self) -> None:
        self.setups.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            parent=self,
            initialdir=self.setups,
            defaultextension=".json",
            filetypes=[("Setups", "*.json")],
        )
        if path:
            Path(path).write_text(json.dumps(self._state(), indent=1), encoding="utf-8")

    def _load_setup(self) -> None:
        self.setups.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(
            parent=self, initialdir=self.setups, filetypes=[("Setups", "*.json")]
        )
        if not path:
            return
        try:
            state = json.loads(Path(path).read_text(encoding="utf-8"))
            problem = catalog_module.setup_problem(state, self.catalog)
        except (OSError, ValueError, KeyError, TypeError) as error:
            problem = f"it can't be read ({error})"
        if problem:
            messagebox.showerror("Arena runner", f"That setup can't be used: {problem}.")
            return
        self.map_id.set(state["map"])
        self.matches.set(state["matches"])
        self.sides = state["sides"]
        self.selected = (0, 0)
        self._refresh_lists()
        self._load_editor()

    def _run(self) -> None:
        seeds = batch_module.new_seeds(self.matches.get())
        batch = batch_module.prepare_batch(
            self.app.settings_home / "runs", self.app.exe, self.app.game, self.map_id.get(),
            self.sides, seeds, batch_module.user_write_dir() / "settings.reg",
        )  # fmt: skip
        batch_module.start_batch(batch)
        self.app.show_running(batch)
