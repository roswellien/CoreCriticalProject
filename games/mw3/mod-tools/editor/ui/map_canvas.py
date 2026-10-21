"""Interactive Top-Down Map Canvas.

Provides panning, zooming, layer toggles, and selection/drag manipulation
for terrain bounds, world object placements, spawn points, and trigger regions.
"""

import math
import tkinter as tk
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Callable

from PIL import Image, ImageTk

from ..core.mission_loader import MissionData, PlacedObject, SpawnPoint, TriggerRegion


class MapCanvas(tk.Canvas):
    """Draw/select live mission objects using an X/Z-to-pixel viewport transform.

    Tk owns the UI thread and PhotoImage lifetime. The canvas references, rather
    than copies, mission placements. A drag mutates an object as a visual preview;
    on_object_moved receives that object and its old XYZ position on release.
    The parent window owns command creation and persisted deltas.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#1a1c23", highlightthickness=0, **kwargs)
        self.mission: Optional[MissionData] = None
        self.on_object_selected: Optional[Callable[[Optional[PlacedObject]], None]] = None
        self.on_object_moved: Optional[Callable[[PlacedObject, float, float, float], None]] = None
        self.on_cursor_coords: Optional[Callable[[float, float], None]] = None

        # Viewport transform: screen_x = (world_x - cam_x) * scale + w/2
        self.cam_x: float = 0.0
        self.cam_z: float = 0.0
        self.scale: float = 0.25  # screen pixels per world meter

        # Layers visibility
        self.show_bitmap: bool = True
        self.show_terrain_bounds: bool = True
        self.show_objects: bool = True
        self.show_spawns: bool = True
        self.show_triggers: bool = True
        self.show_grid: bool = True

        # Selection state
        self.selected_object: Optional[PlacedObject] = None
        self.drag_start_world: Optional[Tuple[float, float]] = None
        self.drag_start_pos: Optional[Tuple[float, float, float]] = None

        # Pan state
        self._pan_start_screen: Optional[Tuple[int, int]] = None

        # Cached background bitmap
        self._bg_image_pil: Optional[Image.Image] = None
        self._bg_image_tk: Optional[ImageTk.PhotoImage] = None

        # Mouse event bindings
        self.bind("<ButtonPress-1>", self._on_left_down)
        self.bind("<B1-Motion>", self._on_left_drag)
        self.bind("<ButtonRelease-1>", self._on_left_up)

        self.bind("<ButtonPress-2>", self._on_pan_down)
        self.bind("<B2-Motion>", self._on_pan_drag)
        self.bind("<ButtonRelease-2>", self._on_pan_up)

        self.bind("<ButtonPress-3>", self._on_pan_down)
        self.bind("<B3-Motion>", self._on_pan_drag)
        self.bind("<ButtonRelease-3>", self._on_pan_up)

        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Configure>", lambda e: self.redraw())

    def set_mission(self, mission: MissionData) -> None:
        """Set the active mission data and center viewport."""
        self.mission = mission
        self.selected_object = None
        self.cam_x = mission.calibration.offset_x
        self.cam_z = mission.calibration.offset_z
        # Compute nice initial scale
        bounds = mission.terrain_bounds
        w = max(100.0, bounds.width)
        d = max(100.0, bounds.depth)
        canvas_w = max(400, self.winfo_width())
        canvas_h = max(300, self.winfo_height())
        self.scale = min(canvas_w / w, canvas_h / d) * 0.85
        if self.scale <= 0.01:
            self.scale = 0.2

        # Load background map image if available
        self._bg_image_pil = None
        if mission.calibration.image_path and mission.calibration.image_path.is_file():
            try:
                self._bg_image_pil = Image.open(mission.calibration.image_path).convert("RGBA")
            except Exception as e:
                print(f"Warning: could not load map image: {e}")

        self.redraw()

    def world_to_screen(self, wx: float, wz: float) -> Tuple[float, float]:
        """Map world X/Z to canvas X/Y pixels using camera center and pixels/unit scale."""
        cx = self.winfo_width() / 2.0
        cy = self.winfo_height() / 2.0
        sx = cx + (wx - self.cam_x) * self.scale
        sy = cy + (wz - self.cam_z) * self.scale
        return (sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Invert the viewport transform; screen Y corresponds to world Z, not height."""
        cx = self.winfo_width() / 2.0
        cy = self.winfo_height() / 2.0
        wx = self.cam_x + (sx - cx) / self.scale
        wz = self.cam_z + (sy - cy) / self.scale
        return (wx, wz)

    def redraw(self) -> None:
        """Full redraw of the top-down tactical canvas."""
        self.delete("all")
        if not self.mission:
            self.create_text(
                self.winfo_width() / 2,
                self.winfo_height() / 2,
                text="No Mission Loaded\nUse File -> Open Mission",
                fill="#6e7681",
                font=("Segoe UI", 14),
                justify="center",
            )
            return

        w = self.winfo_width()
        h = self.winfo_height()

        # 1. Grid layer
        if self.show_grid:
            self._draw_grid(w, h)

        # 2. Map Bitmap layer
        if self.show_bitmap and self._bg_image_pil:
            self._draw_map_bitmap()

        # 3. Terrain bounds layer
        if self.show_terrain_bounds:
            self._draw_terrain_bounds()

        # 4. Trigger Regions layer
        if self.show_triggers:
            self._draw_trigger_regions()

        # 5. Spawn points layer
        if self.show_spawns:
            self._draw_spawns()

        # 6. Object placements layer
        if self.show_objects:
            self._draw_objects()

    def _draw_grid(self, w: int, h: int) -> None:
        # Determine grid step in world meters
        step = 500.0
        if self.scale > 0.8:
            step = 100.0
        elif self.scale > 0.4:
            step = 250.0
        elif self.scale < 0.1:
            step = 1000.0

        min_w, min_h = self.screen_to_world(0, 0)
        max_w, max_h = self.screen_to_world(w, h)

        start_x = math.floor(min(min_w, max_w) / step) * step
        end_x = math.ceil(max(min_w, max_w) / step) * step
        start_z = math.floor(min(min_h, max_h) / step) * step
        end_z = math.ceil(max(min_h, max_h) / step) * step

        x = start_x
        while x <= end_x:
            sx, _ = self.world_to_screen(x, 0)
            color = "#2d333b" if int(x) % 1000 != 0 else "#373e47"
            self.create_line(sx, 0, sx, h, fill=color, width=1)
            self.create_text(
                sx + 3, h - 12, text=f"{int(x)}m", fill="#484f58", font=("Consolas", 8), anchor="w"
            )
            x += step

        z = start_z
        while z <= end_z:
            _, sy = self.world_to_screen(0, z)
            color = "#2d333b" if int(z) % 1000 != 0 else "#373e47"
            self.create_line(0, sy, w, sy, fill=color, width=1)
            self.create_text(
                5, sy - 8, text=f"{int(z)}m", fill="#484f58", font=("Consolas", 8), anchor="w"
            )
            z += step

        # Origin crosshair (0,0)
        ox, oy = self.world_to_screen(0, 0)
        self.create_line(ox - 10, oy, ox + 10, oy, fill="#58a6ff", width=1)
        self.create_line(ox, oy - 10, ox, oy + 10, fill="#58a6ff", width=1)

    def _draw_map_bitmap(self) -> None:
        cal = self.mission.calibration
        # Bitmap image width and height in world meters:
        world_w = cal.image_width * abs(cal.mpp)
        world_h = cal.image_height * abs(cal.mpp)

        # Map top-left in world coords:
        top_left_wx = cal.offset_x - (world_w / 2.0)
        top_left_wz = cal.offset_z - (world_h / 2.0)

        # Screen coordinates of top-left and bottom-right
        sx1, sy1 = self.world_to_screen(top_left_wx, top_left_wz)
        target_pw = max(10, int(world_w * self.scale))
        target_ph = max(10, int(world_h * self.scale))

        try:
            resized = self._bg_image_pil.resize((target_pw, target_ph), Image.Resampling.BILINEAR)
            self._bg_image_tk = ImageTk.PhotoImage(resized)
            self.create_image(sx1, sy1, image=self._bg_image_tk, anchor="nw")
            # Border around map texture
            self.create_rectangle(
                sx1, sy1, sx1 + target_pw, sy1 + target_ph, outline="#444c56", width=1
            )
        except Exception as e:
            pass

    def _draw_terrain_bounds(self) -> None:
        tb = self.mission.terrain_bounds
        x1, y1 = self.world_to_screen(tb.min_x, tb.min_z)
        x2, y2 = self.world_to_screen(tb.max_x, tb.max_z)
        self.create_rectangle(x1, y1, x2, y2, outline="#388bfd", width=1, dash=(4, 4))
        self.create_text(
            min(x1, x2) + 5,
            min(y1, y2) + 12,
            text="Terrain Bounds",
            fill="#388bfd",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )

    def _draw_trigger_regions(self) -> None:
        for reg in self.mission.trigger_regions:
            if len(reg.points) < 2:
                continue
            screen_pts = []
            for pt in reg.points:
                sx, sy = self.world_to_screen(pt[0], pt[2])
                screen_pts.extend([sx, sy])
            # Draw polygon perimeter
            self.create_polygon(screen_pts, fill="", outline="#3fb950", width=1, dash=(3, 3))
            # Label
            first_x, first_y = self.world_to_screen(reg.points[0][0], reg.points[0][2])
            self.create_text(
                first_x,
                first_y - 8,
                text=reg.name,
                fill="#3fb950",
                font=("Segoe UI", 8),
                anchor="s",
            )

    def _draw_spawns(self) -> None:
        for sp in self.mission.spawn_points:
            sx, sy = self.world_to_screen(sp.x, sp.z)
            # Draw directional circle/arrow
            r = 8
            self.create_oval(
                sx - r, sy - r, sx + r, sy + r, fill="#d29922", outline="#f0883e", width=2
            )
            # Direction vector
            rad = math.radians(sp.yaw_degrees)
            dx = math.sin(rad) * 16
            dy = -math.cos(rad) * 16
            self.create_line(sx, sy, sx + dx, sy + dy, fill="#f0883e", width=2, arrow="last")
            self.create_text(
                sx,
                sy + r + 6,
                text=sp.name,
                fill="#e3b341",
                font=("Segoe UI", 8, "bold"),
                anchor="n",
            )

    def _draw_objects(self) -> None:
        """Draw visible placement markers; marker shapes are name-based UI hints only."""
        # Filter notable world entities
        for obj in self.mission.placed_objects:
            # Highlight root / named objects
            is_selected = self.selected_object == obj
            sx, sy = self.world_to_screen(obj.x, obj.z)

            # Cull offscreen markers
            if (
                sx < -30
                or sx > self.winfo_width() + 30
                or sy < -30
                or sy > self.winfo_height() + 30
            ):
                continue

            r = 6 if not is_selected else 9
            fill_color = "#f85149" if not is_selected else "#58a6ff"
            outline_color = "#ffffff" if is_selected else "#da3633"

            # Distinguish turrets, bunkers, and buildings
            low = obj.name.lower()
            if "tur" in low:
                # Square marker for turrets
                self.create_rectangle(
                    sx - r,
                    sy - r,
                    sx + r,
                    sy + r,
                    fill=fill_color,
                    outline=outline_color,
                    width=2 if is_selected else 1,
                )
            else:
                self.create_oval(
                    sx - r,
                    sy - r,
                    sx + r,
                    sy + r,
                    fill=fill_color,
                    outline=outline_color,
                    width=2 if is_selected else 1,
                )

            # Selection halo
            if is_selected:
                self.create_oval(
                    sx - r - 4,
                    sy - r - 4,
                    sx + r + 4,
                    sy + r + 4,
                    outline="#58a6ff",
                    width=1,
                    dash=(2, 2),
                )

            # Label on zoom
            if self.scale > 0.15 or is_selected or obj.parent_indices == [0]:
                self.create_text(
                    sx,
                    sy - r - 4,
                    text=obj.name or f"Node {obj.node_index}",
                    fill="#e6edf3" if is_selected else "#8b949e",
                    font=("Segoe UI", 8),
                    anchor="s",
                )

    def _on_left_down(self, event) -> None:
        """Select the nearest placement within a pixel-sized hit radius and snapshot a drag."""
        if not self.mission:
            return
        click_wx, click_wz = self.screen_to_world(event.x, event.y)

        # Hit test placed objects (closest within threshold)
        best_obj = None
        best_dist = 20.0 / self.scale  # 20 pixel hit radius in world units

        for obj in reversed(self.mission.placed_objects):
            dist = math.hypot(obj.x - click_wx, obj.z - click_wz)
            if dist < best_dist:
                best_dist = dist
                best_obj = obj

        self.selected_object = best_obj
        if best_obj:
            self.drag_start_world = (click_wx, click_wz)
            self.drag_start_pos = (best_obj.x, best_obj.y, best_obj.z)

        if self.on_object_selected:
            self.on_object_selected(best_obj)

        self.redraw()

    def _on_left_drag(self, event) -> None:
        """Preview an X/Z translation while retaining the source object's Y height."""
        if not self.selected_object or not self.drag_start_world or not self.drag_start_pos:
            return
        cur_wx, cur_wz = self.screen_to_world(event.x, event.y)
        dx = cur_wx - self.drag_start_world[0]
        dz = cur_wz - self.drag_start_world[1]

        # Apply continuous translation preview
        self.selected_object.x = round(self.drag_start_pos[0] + dx, 1)
        self.selected_object.z = round(self.drag_start_pos[2] + dz, 1)
        self.redraw()

    def _on_left_up(self, event) -> None:
        """Notify one committed X/Z move, passing its original coordinates for undo."""
        if self.selected_object and self.drag_start_pos and self.on_object_moved:
            orig_x, orig_y, orig_z = self.drag_start_pos
            cur_x, cur_y, cur_z = (
                self.selected_object.x,
                self.selected_object.y,
                self.selected_object.z,
            )
            if math.hypot(cur_x - orig_x, cur_z - orig_z) > 0.05:
                # Fire committed move callback
                self.on_object_moved(self.selected_object, orig_x, orig_y, orig_z)
        self.drag_start_world = None
        self.drag_start_pos = None

    def _on_pan_down(self, event) -> None:
        self._pan_start_screen = (event.x, event.y)

    def _on_pan_drag(self, event) -> None:
        """Move only the viewport camera; convert mouse-pixel deltas back to world units."""
        if not self._pan_start_screen:
            return
        dx = event.x - self._pan_start_screen[0]
        dy = event.y - self._pan_start_screen[1]
        self.cam_x -= dx / self.scale
        self.cam_z -= dy / self.scale
        self._pan_start_screen = (event.x, event.y)
        self.redraw()

    def _on_pan_up(self, event) -> None:
        self._pan_start_screen = None

    def _on_mousewheel(self, event) -> None:
        """Zoom around the cursor's world position, within the canvas scale limits."""
        # Zoom toward mouse position
        mouse_wx, mouse_wz = self.screen_to_world(event.x, event.y)
        factor = 1.15 if event.delta > 0 else (1.0 / 1.15)
        new_scale = max(0.02, min(5.0, self.scale * factor))
        if abs(new_scale - self.scale) > 1e-5:
            self.scale = new_scale
            # Adjust camera so world coord under mouse stays under mouse
            cx = self.winfo_width() / 2.0
            cy = self.winfo_height() / 2.0
            self.cam_x = mouse_wx - (event.x - cx) / self.scale
            self.cam_z = mouse_wz - (event.y - cy) / self.scale
            self.redraw()

    def _on_mouse_move(self, event) -> None:
        wx, wz = self.screen_to_world(event.x, event.y)
        if self.on_cursor_coords:
            self.on_cursor_coords(wx, wz)
