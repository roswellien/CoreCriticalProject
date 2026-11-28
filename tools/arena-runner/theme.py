"""The runner's dark green look, the mock-ups' palette, for ttk and plain tk widgets."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG = "#161a18"  # the window
PANEL = "#1f2522"  # boxes and lists
RAISED = "#2a312d"  # buttons and fields
LINE = "#3a443f"
FG = "#e3e8e4"
MUTED = "#9aa7a0"
ACCENT = "#6cc2a3"  # the picked map, the Run button, selections
ACCENT_DARK = "#2f6f5a"


def apply(root: tk.Tk) -> None:
    root.configure(background=BG)
    # Plain tk widgets (lists, text, menus, the map buttons) read these.
    for pattern, value in (
        ("*Background", PANEL), ("*Foreground", FG), ("*selectBackground", ACCENT_DARK),
        ("*selectForeground", FG), ("*highlightBackground", LINE), ("*highlightColor", ACCENT),
        ("*activeBackground", RAISED), ("*activeForeground", FG), ("*insertBackground", FG),
        ("*TCombobox*Listbox.background", PANEL), ("*TCombobox*Listbox.foreground", FG),
    ):  # fmt: skip
        root.option_add(pattern, value)
    style = ttk.Style(root)
    style.theme_use("clam")  # the one built-in theme that takes these colors everywhere
    style.configure(".", background=BG, foreground=FG, fieldbackground=RAISED, bordercolor=LINE,
                    lightcolor=RAISED, darkcolor=BG, troughcolor=PANEL, arrowcolor=FG,
                    selectbackground=ACCENT_DARK, selectforeground=FG)  # fmt: skip
    style.configure("TLabelframe", background=BG, bordercolor=LINE)
    style.configure("TLabelframe.Label", background=BG, foreground=ACCENT)
    style.configure("TButton", background=RAISED, padding=(10, 4))
    style.map(
        "TButton", background=[("active", LINE), ("disabled", BG)], foreground=[("disabled", MUTED)]
    )
    style.configure(
        "Accent.TButton", background=ACCENT_DARK, foreground=FG, font=("Segoe UI", 10, "bold")
    )
    style.map("Accent.TButton", background=[("active", ACCENT)])
    style.map("TCombobox", fieldbackground=[("readonly", RAISED)], foreground=[("readonly", FG)])
    style.configure("TSpinbox", fieldbackground=RAISED, foreground=FG)
    style.configure(
        "Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG, rowheight=24
    )
    style.configure("Treeview.Heading", background=RAISED, foreground=ACCENT)
    style.map("Treeview", background=[("selected", ACCENT_DARK)])
    style.configure("Muted.TLabel", foreground=MUTED)
