"""Arena runner: set up, run and rewatch AI bot matches without typing commands.

A developer tool for #287 and #289 (docs/arena.md, "Arena runner").

    python tools/arena-runner/arena_runner.py

The first start asks for the game folder and mw3.exe and keeps them in
%LOCALAPPDATA%/CoreCritical/arena-runner/settings.json. Batches are written
under runs/ beside it.
"""

from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog as catalog_module
from results_screen import ResultsScreen
from running_screen import RunningScreen
from setup_screen import SetupScreen

HOME = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "CoreCritical" / "arena-runner"
SETTINGS = HOME / "settings.json"
PILOTS = Path(__file__).resolve().parent / "pilots.json"


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(settings: dict) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=1), encoding="utf-8")


def ask_paths(root: tk.Tk, settings: dict) -> bool:
    """The game folder and mw3.exe, asked once and kept."""
    game = settings.get("game")
    if not game or not Path(game).is_dir():
        game = filedialog.askdirectory(parent=root, title="Pick the MechWarrior 3 game folder")
    exe = settings.get("exe")
    if game and (not exe or not Path(exe).is_file()):
        exe = filedialog.askopenfilename(
            parent=root, title="Pick the built mw3.exe", filetypes=[("mw3.exe", "mw3.exe")]
        )
    if not game or not exe:
        return False
    settings.update(game=game, exe=exe)
    save_settings(settings)
    return True


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.screen: ttk.Frame | None = None
        root.title("Arena runner")
        root.geometry("1180x820")
        self.settings = load_settings()
        if not ask_paths(root, self.settings):
            root.destroy()
            return
        self.exe = Path(self.settings["exe"])
        self.game = Path(self.settings["game"])
        self.settings_home = HOME
        status = ttk.Label(root, text="Reading the game's maps, mechs and pilots...")
        status.pack(pady=40)
        root.update()
        try:
            self.catalog = catalog_module.ensure_catalog(self.exe, self.game, HOME)
        except (OSError, RuntimeError, ValueError) as error:
            messagebox.showerror("Arena runner", f"The game's lists could not be read.\n\n{error}")
            root.destroy()
            return
        status.destroy()
        self.short_pilots = json.loads(PILOTS.read_text(encoding="utf-8"))["pilots"]
        self.show_setup()

    def screen_ready(self) -> bool:
        """False when start-up stopped (no paths, or no catalog) and the window is gone."""
        return self.screen is not None

    def _show(self, screen: ttk.Frame) -> None:
        if self.screen is not None:
            self.screen.destroy()
        self.screen = screen
        screen.pack(fill="both", expand=True)

    def show_setup(self) -> None:
        self._show(SetupScreen(self.root, self, HOME / "setups"))

    def show_running(self, batch) -> None:
        self._show(RunningScreen(self.root, self, batch))

    def show_results(self, batch, logs) -> None:
        self._show(ResultsScreen(self.root, self, batch, logs))


def main() -> None:
    root = tk.Tk()
    app = App(root)
    if app.screen_ready():
        root.mainloop()


if __name__ == "__main__":
    main()
