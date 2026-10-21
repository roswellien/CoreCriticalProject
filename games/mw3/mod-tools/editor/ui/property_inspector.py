"""Property Inspector Pane.

Displays and allows editing of confirmed object properties (transforms,
names, active flags) with undo/redo integration, while explicitly
documenting and labeling all preserved unresolved engine fields.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from ..core.mission_loader import PlacedObject
from ..core.project import CommandHistory, MoveObjectCommand, RotateObjectCommand, ToggleObjectActiveCommand


class PropertyInspector(ttk.Frame):
    """Side panel displaying confirmed properties and unresolved metadata for the selected entity."""

    def __init__(self, master, history: CommandHistory, on_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, padding=8, **kwargs)
        self.history = history
        self.on_change = on_change
        self.current_object: Optional[PlacedObject] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)

        # Header
        self.header_label = ttk.Label(self, text="Property Inspector", font=("Segoe UI", 11, "bold"))
        self.header_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Identity
        ttk.Label(self, text="Name:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, state="readonly")
        self.name_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(self, text="Node Index:").grid(row=2, column=0, sticky="w", pady=2)
        self.index_var = tk.StringVar(value="-")
        ttk.Label(self, textvariable=self.index_var, font=("Consolas", 9)).grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(self, text="Model Index:").grid(row=3, column=0, sticky="w", pady=2)
        self.model_var = tk.StringVar(value="-")
        ttk.Label(self, textvariable=self.model_var, font=("Consolas", 9)).grid(row=3, column=1, sticky="w", pady=2)

        # Separator: Transform
        sep1 = ttk.Separator(self, orient="horizontal")
        sep1.grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(self, text="Transform (Confirmed Properties)", font=("Segoe UI", 9, "bold")).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Pos X
        ttk.Label(self, text="World X (m):").grid(row=6, column=0, sticky="w", pady=2)
        self.x_var = tk.StringVar()
        self.x_entry = ttk.Entry(self, textvariable=self.x_var)
        self.x_entry.grid(row=6, column=1, sticky="ew", pady=2)
        self.x_entry.bind("<Return>", lambda e: self._apply_transform())

        # Pos Y (Height)
        ttk.Label(self, text="World Y (m):").grid(row=7, column=0, sticky="w", pady=2)
        self.y_var = tk.StringVar()
        self.y_entry = ttk.Entry(self, textvariable=self.y_var)
        self.y_entry.grid(row=7, column=1, sticky="ew", pady=2)
        self.y_entry.bind("<Return>", lambda e: self._apply_transform())

        # Pos Z
        ttk.Label(self, text="World Z (m):").grid(row=8, column=0, sticky="w", pady=2)
        self.z_var = tk.StringVar()
        self.z_entry = ttk.Entry(self, textvariable=self.z_var)
        self.z_entry.grid(row=8, column=1, sticky="ew", pady=2)
        self.z_entry.bind("<Return>", lambda e: self._apply_transform())

        # Yaw
        ttk.Label(self, text="Yaw (deg):").grid(row=9, column=0, sticky="w", pady=2)
        self.yaw_var = tk.StringVar()
        self.yaw_entry = ttk.Entry(self, textvariable=self.yaw_var)
        self.yaw_entry.grid(row=9, column=1, sticky="ew", pady=2)
        self.yaw_entry.bind("<Return>", lambda e: self._apply_yaw())

        # Active Status
        self.active_var = tk.BooleanVar(value=True)
        self.active_chk = ttk.Checkbutton(self, text="Active / Enabled at Spawn", variable=self.active_var, command=self._apply_active)
        self.active_chk.grid(row=10, column=0, columnspan=2, sticky="w", pady=6)

        # Apply Button
        self.apply_btn = ttk.Button(self, text="Apply Changes", command=self._apply_all)
        self.apply_btn.grid(row=11, column=0, columnspan=2, sticky="ew", pady=4)

        # Separator: Unresolved Fields
        sep2 = ttk.Separator(self, orient="horizontal")
        sep2.grid(row=12, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(self, text="Unresolved Engine Fields (Preserved Losslessly)", font=("Segoe UI", 9, "bold")).grid(row=13, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Text display for unresolved metadata
        self.unresolved_text = tk.Text(self, height=8, width=28, bg="#21262d", fg="#8b949e", font=("Consolas", 8), relief="flat", wrap="word")
        self.unresolved_text.grid(row=14, column=0, columnspan=2, sticky="nsew", pady=2)
        self.rowconfigure(14, weight=1)

        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.x_entry.config(state=state)
        self.y_entry.config(state=state)
        self.z_entry.config(state=state)
        self.yaw_entry.config(state=state)
        self.active_chk.config(state=state)
        self.apply_btn.config(state=state)

    def inspect_object(self, obj: Optional[PlacedObject]) -> None:
        """Populate inspector with object attributes."""
        self.current_object = obj
        if not obj:
            self._set_enabled(False)
            self.header_label.config(text="Property Inspector (No Selection)")
            self.name_var.set("")
            self.index_var.set("-")
            self.model_var.set("-")
            self.x_var.set("")
            self.y_var.set("")
            self.z_var.set("")
            self.yaw_var.set("")
            self.active_var.set(False)
            self.unresolved_text.delete("1.0", "end")
            self.unresolved_text.insert("end", "Select an object to inspect its confirmed properties and preserved engine state.")
            return

        self._set_enabled(True)
        self.header_label.config(text=f"Selected: {obj.name or 'Unnamed Node'}")
        self.name_var.set(obj.name or f"Node_{obj.node_index}")
        self.index_var.set(str(obj.node_index))
        self.model_var.set(str(obj.model_index) if obj.model_index != -1 else "None (Hierarchical)")
        self.x_var.set(f"{obj.x:.2f}")
        self.y_var.set(f"{obj.y:.2f}")
        self.z_var.set(f"{obj.z:.2f}")
        self.yaw_var.set(f"{obj.yaw_degrees:.1f}")
        self.active_var.set(obj.active)

        # Unresolved fields formatting
        self.unresolved_text.delete("1.0", "end")
        unresolved_info = (
            f"Parent Nodes: {obj.parent_indices}\n"
            f"Child Nodes: {len(obj.child_indices)} children\n"
            f"Update Flags: {obj.unresolved_fields.get('update_flags', 0)}\n"
            f"Raw Words: 192={obj.unresolved_fields.get('field192')}, 196={obj.unresolved_fields.get('field196')}\n"
            f"Bounding Box: {obj.unresolved_fields.get('active_bbox')}\n"
            f"Node Flags: {obj.flags}\n"
            f"Note: These fields are preserved byte-exact upon export."
        )
        self.unresolved_text.insert("end", unresolved_info)

    def _apply_transform(self) -> None:
        if not self.current_object:
            return
        try:
            nx = float(self.x_var.get())
            ny = float(self.y_var.get())
            nz = float(self.z_var.get())
            if (nx, ny, nz) != (self.current_object.x, self.current_object.y, self.current_object.z):
                cmd = MoveObjectCommand(self.current_object, nx, ny, nz, on_update=self.on_change)
                self.history.execute(cmd)
        except ValueError:
            pass

    def _apply_yaw(self) -> None:
        if not self.current_object:
            return
        try:
            nyaw = float(self.yaw_var.get())
            if abs(nyaw - self.current_object.yaw_degrees) > 0.05:
                cmd = RotateObjectCommand(self.current_object, nyaw, on_update=self.on_change)
                self.history.execute(cmd)
        except ValueError:
            pass

    def _apply_active(self) -> None:
        if not self.current_object:
            return
        nactive = self.active_var.get()
        if nactive != self.current_object.active:
            cmd = ToggleObjectActiveCommand(self.current_object, nactive, on_update=self.on_change)
            self.history.execute(cmd)

    def _apply_all(self) -> None:
        self._apply_transform()
        self._apply_yaw()
        self._apply_active()
