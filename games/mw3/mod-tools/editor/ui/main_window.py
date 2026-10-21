"""Main Window of the MW3 Map & Mission Editor.

Integrates the top-down interactive canvas, object hierarchy list,
property inspector, undo/redo command history, and mod exporter.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Tuple

from ..core.mission_loader import MissionLoader, MissionData, PlacedObject, SpawnPoint, TriggerRegion
from ..core.project import ModProject, CommandHistory, MoveObjectCommand
from ..core.exporter import ModExporter
from .map_canvas import MapCanvas
from .property_inspector import PropertyInspector

ROOT = Path(__file__).resolve().parents[5]


class MainWindow(tk.Tk):
    """MW3 Map & Mission Editor Main Application Window."""

    def __init__(self, game_root: Optional[Path] = None, initial_op: str = "c1", initial_mission: str = "c1m1"):
        super().__init__()
        self.title("MechWarrior 3 Map & Mission Editor (Native Modding Suite)")
        self.geometry("1400x900")
        self.minsize(1000, 650)

        # Style configuration
        self._configure_styles()

        self.game_root = Path(game_root) if game_root else ROOT / "MW3"
        self.loader = MissionLoader(self.game_root)
        self.exporter = ModExporter(ROOT / "local/mods")
        self.history = CommandHistory()
        self.history.add_change_callback(self._on_history_changed)

        self.current_mission: Optional[MissionData] = None
        self.current_project: Optional[ModProject] = None

        self._build_menu()
        self._build_toolbar()
        self._build_main_layout()
        self._build_statusbar()

        # Keyboard shortcuts
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Control-s>", lambda e: self._save_project())
        self.bind("<F5>", lambda e: self._run_native_game())

        # Load initial mission if available
        try:
            self._open_mission(initial_op, initial_mission)
        except Exception as e:
            print(f"Warning: could not open initial mission {initial_op}/{initial_mission}: {e}")

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background="#21262d", foreground="#e6edf3", font=("Segoe UI", 9))
        style.configure("TFrame", background="#21262d")
        style.configure("TLabel", background="#21262d", foreground="#e6edf3")
        style.configure("TButton", background="#30363d", foreground="#e6edf3", borderwidth=1)
        style.map("TButton", background=[("active", "#388bfd"), ("disabled", "#21262d")])
        style.configure("TCheckbutton", background="#21262d", foreground="#e6edf3")
        style.configure("Treeview", background="#161b22", foreground="#e6edf3", fieldbackground="#161b22", font=("Segoe UI", 8))
        style.configure("Treeview.Heading", background="#30363d", foreground="#e6edf3", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#1f6feb")])

    def _build_menu(self) -> None:
        menubar = tk.Menu(self, bg="#21262d", fg="#e6edf3", activebackground="#388bfd", activeforeground="#ffffff")
        self.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#21262d", fg="#e6edf3", activebackground="#388bfd")
        file_menu.add_command(label="Open Mission...", command=self._show_open_mission_dialog, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="New Mod Project...", command=self._new_project)
        file_menu.add_command(label="Open Mod Project...", command=self._open_project)
        file_menu.add_command(label="Save Mod Project", command=self._save_project, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Mod Package...", command=self._export_mod)
        file_menu.add_command(label="Play Mod in Native Game", command=self._run_native_game, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        self.edit_menu = tk.Menu(menubar, tearoff=0, bg="#21262d", fg="#e6edf3", activebackground="#388bfd")
        self.edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        menubar.add_cascade(label="Edit", menu=self.edit_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0, bg="#21262d", fg="#e6edf3", activebackground="#388bfd")
        self.view_bitmap_var = tk.BooleanVar(value=True)
        self.view_bounds_var = tk.BooleanVar(value=True)
        self.view_objects_var = tk.BooleanVar(value=True)
        self.view_spawns_var = tk.BooleanVar(value=True)
        self.view_triggers_var = tk.BooleanVar(value=True)
        self.view_grid_var = tk.BooleanVar(value=True)

        view_menu.add_checkbutton(label="Map Texture", variable=self.view_bitmap_var, command=self._update_layers)
        view_menu.add_checkbutton(label="Terrain Bounds", variable=self.view_bounds_var, command=self._update_layers)
        view_menu.add_checkbutton(label="World Objects", variable=self.view_objects_var, command=self._update_layers)
        view_menu.add_checkbutton(label="Spawn Points", variable=self.view_spawns_var, command=self._update_layers)
        view_menu.add_checkbutton(label="Trigger Regions", variable=self.view_triggers_var, command=self._update_layers)
        view_menu.add_checkbutton(label="Coordinate Grid", variable=self.view_grid_var, command=self._update_layers)
        view_menu.add_separator()
        view_menu.add_command(label="Reset Camera / Center", command=lambda: self.canvas.set_mission(self.current_mission) if self.current_mission else None)
        menubar.add_cascade(label="View", menu=view_menu)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self, padding=(6, 4))
        toolbar.pack(side="top", fill="x")

        ttk.Button(toolbar, text="📂 Open Mission", command=self._show_open_mission_dialog).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)

        self.undo_btn = ttk.Button(toolbar, text="↶ Undo", command=self._undo, state="disabled")
        self.undo_btn.pack(side="left", padx=2)
        self.redo_btn = ttk.Button(toolbar, text="↷ Redo", command=self._redo, state="disabled")
        self.redo_btn.pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)

        ttk.Button(toolbar, text="💾 Save Project", command=self._save_project).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📦 Export Mod", command=self._export_mod).pack(side="left", padx=2)
        ttk.Button(toolbar, text="▶ Play in Native Game", command=self._run_native_game).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)
        ttk.Label(toolbar, text="Active Mission:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 2))
        self.mission_label = ttk.Label(toolbar, text="None", foreground="#58a6ff")
        self.mission_label.pack(side="left", padx=2)

    def _build_main_layout(self) -> None:
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left Pane: Hierarchy / Entities Treeview
        left_frame = ttk.Frame(paned, width=280)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Mission Entities", font=("Segoe UI", 9, "bold")).pack(side="top", anchor="w", padx=6, pady=4)
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side="right", fill="y")
        self.tree = ttk.Treeview(left_frame, selectmode="browse", yscrollcommand=tree_scroll.set)
        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Center Pane: Interactive Map Canvas
        center_frame = ttk.Frame(paned)
        paned.add(center_frame, weight=5)
        self.canvas = MapCanvas(center_frame)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.on_object_selected = self._on_canvas_object_selected
        self.canvas.on_object_moved = self._on_canvas_object_moved
        self.canvas.on_cursor_coords = self._on_cursor_coords

        # Right Pane: Property Inspector
        self.inspector = PropertyInspector(paned, history=self.history, on_change=self._on_property_edited, width=320)
        paned.add(self.inspector, weight=2)

    def _build_statusbar(self) -> None:
        statusbar = ttk.Frame(self, padding=(6, 2))
        statusbar.pack(side="bottom", fill="x")

        self.coords_label = ttk.Label(statusbar, text="X: 0.0m, Z: 0.0m", width=25)
        self.coords_label.pack(side="left", padx=4)

        self.zoom_label = ttk.Label(statusbar, text="Scale: 100%", width=16)
        self.zoom_label.pack(side="left", padx=4)

        self.status_msg = ttk.Label(statusbar, text="Ready", foreground="#8b949e")
        self.status_msg.pack(side="left", fill="x", expand=True, padx=4)

    def _update_layers(self) -> None:
        self.canvas.show_bitmap = self.view_bitmap_var.get()
        self.canvas.show_terrain_bounds = self.view_bounds_var.get()
        self.canvas.show_objects = self.view_objects_var.get()
        self.canvas.show_spawns = self.view_spawns_var.get()
        self.canvas.show_triggers = self.view_triggers_var.get()
        self.canvas.show_grid = self.view_grid_var.get()
        self.canvas.redraw()

    def _show_open_mission_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Select Operation & Mission")
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Mission to Open:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=8)

        tree = ttk.Treeview(dialog, columns=("op", "mid", "label"), show="headings", selectmode="browse")
        tree.heading("op", text="Op")
        tree.heading("mid", text="ID")
        tree.heading("label", text="Mission Name")
        tree.column("op", width=50)
        tree.column("mid", width=70)
        tree.column("label", width=280)
        tree.pack(fill="both", expand=True, padx=10, pady=4)

        for op, mid, label in self.loader.list_available_missions():
            tree.insert("", "end", values=(op.upper(), mid, label))

        def on_select():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])["values"]
            dialog.destroy()
            self._open_mission(str(vals[0]).lower(), str(vals[1]).lower())

        btn_box = ttk.Frame(dialog)
        btn_box.pack(fill="x", padx=10, pady=8)
        ttk.Button(btn_box, text="Open", command=on_select).pack(side="right", padx=4)
        ttk.Button(btn_box, text="Cancel", command=dialog.destroy).pack(side="right")

    def _open_mission(self, operation: str, mission_id: str) -> None:
        self.status_msg.config(text=f"Loading {operation.upper()} / {mission_id}...")
        self.update_idletasks()
        try:
            mission = self.loader.load_mission(operation, mission_id)
            self.current_mission = mission
            self.current_project = ModProject(
                project_name=f"{mission_id.upper()} Custom Mod",
                target_operation=operation,
                target_mission=mission_id,
            )
            self.history.clear()
            self.mission_label.config(text=f"{operation.upper()} / {mission_id}")

            # Populate Treeview
            self._populate_tree()

            # Set Canvas
            self.canvas.set_mission(mission)
            self.inspector.inspect_object(None)
            self.status_msg.config(text=f"Loaded {len(mission.placed_objects)} world objects, {len(mission.spawn_points)} spawns, {len(mission.trigger_regions)} trigger regions.")
        except Exception as e:
            messagebox.showerror("Error Opening Mission", str(e))
            self.status_msg.config(text="Error loading mission")

    def _populate_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        if not self.current_mission:
            return

        # Spawns folder
        sp_root = self.tree.insert("", "end", text="Spawn Points", open=True)
        for sp in self.current_mission.spawn_points:
            self.tree.insert(sp_root, "end", text=f"🎯 {sp.name}", values=("spawn", sp.name))

        # Triggers folder
        tr_root = self.tree.insert("", "end", text="Trigger Regions", open=False)
        for tr in self.current_mission.trigger_regions:
            self.tree.insert(tr_root, "end", text=f"📐 {tr.name}", values=("trigger", tr.name))

        # Placed World Objects folder
        obj_root = self.tree.insert("", "end", text="World Objects", open=True)
        for obj in self.current_mission.placed_objects:
            low = obj.name.lower()
            icon = "⚡" if "tur" in low else "🏢" if "build" in low or "bunk" in low else "📦"
            self.tree.insert(obj_root, "end", text=f"{icon} {obj.name or f'Node_{obj.node_index}'}", values=("object", obj.node_index))

    def _on_tree_select(self, event) -> None:
        sel = self.tree.selection()
        if not sel or not self.current_mission:
            return
        item = self.tree.item(sel[0])
        vals = item.get("values")
        if not vals or len(vals) < 2:
            return
        kind, key = vals[0], vals[1]
        if kind == "object":
            node_idx = int(key)
            obj = next((o for o in self.current_mission.placed_objects if o.node_index == node_idx), None)
            if obj:
                self.canvas.selected_object = obj
                self.canvas.cam_x = obj.x
                self.canvas.cam_z = obj.z
                self.canvas.redraw()
                self.inspector.inspect_object(obj)
        elif kind == "spawn":
            sp = next((s for s in self.current_mission.spawn_points if s.name == key), None)
            if sp:
                self.canvas.cam_x = sp.x
                self.canvas.cam_z = sp.z
                self.canvas.redraw()

    def _on_canvas_object_selected(self, obj: Optional[PlacedObject]) -> None:
        self.inspector.inspect_object(obj)
        if obj:
            # Highlight item in tree
            for item in self.tree.get_children():
                for sub in self.tree.get_children(item):
                    vals = self.tree.item(sub).get("values")
                    if vals and len(vals) >= 2 and vals[0] == "object" and int(vals[1]) == obj.node_index:
                        self.tree.selection_set(sub)
                        self.tree.see(sub)
                        break

    def _on_canvas_object_moved(self, obj: PlacedObject, old_x: float, old_y: float, old_z: float) -> None:
        new_x, new_y, new_z = obj.x, obj.y, obj.z
        # Revert temporary visual state so command execution applies it cleanly to history
        obj.x, obj.y, obj.z = old_x, old_y, old_z
        cmd = MoveObjectCommand(obj, new_x, new_y, new_z, on_update=self._on_property_edited)
        self.history.execute(cmd)

    def _on_property_edited(self) -> None:
        if self.canvas.selected_object and self.current_project:
            self.current_project.record_object_change(self.canvas.selected_object)
        self.canvas.redraw()
        self.inspector.inspect_object(self.canvas.selected_object)

    def _on_cursor_coords(self, wx: float, wz: float) -> None:
        self.coords_label.config(text=f"X: {wx:7.1f}m, Z: {wz:7.1f}m")
        self.zoom_label.config(text=f"Scale: {int(self.canvas.scale * 100)}%")

    def _on_history_changed(self) -> None:
        self.undo_btn.config(state="normal" if self.history.can_undo else "disabled", text=f"↶ Undo {self.history.undo_description[:16]}" if self.history.can_undo else "↶ Undo")
        self.redo_btn.config(state="normal" if self.history.can_redo else "disabled", text=f"↷ Redo {self.history.redo_description[:16]}" if self.history.can_redo else "↷ Redo")

    def _undo(self) -> None:
        cmd = self.history.undo()
        if cmd:
            self.status_msg.config(text=f"Undid: {cmd.description}")
            if self.canvas.selected_object and self.current_project:
                self.current_project.record_object_change(self.canvas.selected_object)
            self.canvas.redraw()
            self.inspector.inspect_object(self.canvas.selected_object)

    def _redo(self) -> None:
        cmd = self.history.redo()
        if cmd:
            self.status_msg.config(text=f"Redid: {cmd.description}")
            if self.canvas.selected_object and self.current_project:
                self.current_project.record_object_change(self.canvas.selected_object)
            self.canvas.redraw()
            self.inspector.inspect_object(self.canvas.selected_object)

    def _new_project(self) -> None:
        if not self.current_mission:
            messagebox.showinfo("New Project", "Please open a mission first.")
            return
        self.current_project = ModProject(
            project_name=f"{self.current_mission.mission_id.upper()} Custom Mod",
            target_operation=self.current_mission.operation,
            target_mission=self.current_mission.mission_id,
        )
        self.history.clear()
        messagebox.showinfo("New Project", f"Created new project for {self.current_mission.mission_id.upper()}.")

    def _open_project(self) -> None:
        f = filedialog.askopenfilename(filetypes=[("MW3 Mod Project", "*.mw3mod"), ("JSON Files", "*.json")])
        if not f:
            return
        try:
            proj = ModProject.load(Path(f))
            self._open_mission(proj.target_operation, proj.target_mission)
            self.current_project = proj
            # Reapply project modifications to current mission objects
            if self.current_mission:
                for obj in self.current_mission.placed_objects:
                    if obj.node_index in proj.modified_objects:
                        edits = proj.modified_objects[obj.node_index]
                        if "x" in edits: obj.x = float(edits["x"])
                        if "y" in edits: obj.y = float(edits["y"])
                        if "z" in edits: obj.z = float(edits["z"])
                        if "rot_y" in edits: obj.rot_y = float(edits["rot_y"])
                        if "active" in edits: obj.active = bool(edits["active"])
                self.canvas.redraw()
            messagebox.showinfo("Project Loaded", f"Loaded '{proj.project_name}' with {len(proj.modified_objects)} modified objects.")
        except Exception as e:
            messagebox.showerror("Error Loading Project", str(e))

    def _save_project(self) -> None:
        if not self.current_project:
            return
        if not self.current_project.project_file_path:
            f = filedialog.asksaveasfilename(defaultextension=".mw3mod", filetypes=[("MW3 Mod Project", "*.mw3mod")])
            if not f:
                return
            self.current_project.project_file_path = Path(f)
        self.current_project.save(self.current_project.project_file_path)
        self.status_msg.config(text=f"Saved project: {self.current_project.project_file_path.name}")
        messagebox.showinfo("Project Saved", f"Project saved to:\n{self.current_project.project_file_path}")

    def _export_mod(self) -> None:
        if not self.current_project or not self.current_mission:
            messagebox.showinfo("Export Mod", "No active mission or project to export.")
            return
        try:
            self.status_msg.config(text="Exporting mod package...")
            self.update_idletasks()
            receipt = self.exporter.export(self.current_project, self.current_mission)
            self.status_msg.config(text=f"Mod exported to: {receipt.mod_dir.name}")
            info = (
                f"Mod exported successfully!\n\n"
                f"Directory: {receipt.mod_dir}\n"
                f"Manifest: {receipt.manifest_path.name}\n"
                f"Modified Archives: {len(receipt.modified_files)}\n\n"
                f"To run this mod in the native game:\n"
                f"Double click 'Play-Mod.cmd' in the mod folder or press F5 in the editor."
            )
            messagebox.showinfo("Mod Exported", info)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
            self.status_msg.config(text="Mod export failed")

    def _run_native_game(self) -> None:
        if not self.current_project or not self.current_mission:
            messagebox.showinfo("Run Mod", "Please load a mission and create a project first.")
            return
        try:
            receipt = self.exporter.export(self.current_project, self.current_mission)
            cmd_file = receipt.mod_dir / "Play-Mod.cmd"
            if cmd_file.is_file():
                subprocess.Popen(["cmd.exe", "/c", str(cmd_file)], cwd=str(ROOT))
                self.status_msg.config(text=f"Launched {self.current_project.project_name} in native engine.")
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))
