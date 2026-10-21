#!/usr/bin/env python3
"""MW3 Visual Map Studio - Web Application Server.

Launches a modern, visual 3D map creation studio for MechWarrior 3.
Allows visual terrain generation, 3D asset placement, real-time lighting previews,
and 1-click standalone map pack compilation into mods/map-packs/<pack_id>/.
"""

import http.server
import json
import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

# Setup paths
TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parents[2]
WEB_ROOT = TOOLS_ROOT / "editor/web"

# Add tools root to sys.path so editor modules can be imported
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.map_pack import MapPackProject, MapPackBuilder


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving Studio frontend and handling Mod Pack APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/api/list-packs":
            self.handle_list_packs()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/export-pack":
            self.handle_export_pack()
        elif self.path == "/api/launch-map":
            self.handle_launch_map()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_export_pack(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            project = MapPackProject.from_dict(data)
            builder = MapPackBuilder(packs_root=PROJECT_ROOT / "mods/map-packs", game_root=PROJECT_ROOT / "MW3")
            out_folder = builder.build(project)

            launcher_name = f"Play Map - {project.pack_title}.cmd"

            resp = {
                "status": "ok",
                "pack_id": project.pack_id,
                "pack_folder": str(out_folder),
                "total_placed_assets": len(project.assets),
                "launcher_script": launcher_name,
            }
            self.send_json_response(200, resp)
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def handle_launch_map(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            pack_id = data.get("pack_id", "")

            pack_folder = PROJECT_ROOT / "mods/map-packs" / pack_id
            if not pack_folder.is_dir():
                self.send_json_response(400, {"status": "error", "message": f"Pack folder not found: {pack_id}"})
                return

            cmd_files = list(pack_folder.glob("Play Map - *.cmd"))
            if not cmd_files:
                self.send_json_response(400, {"status": "error", "message": "No launcher command file found in pack"})
                return

            cmd_file = cmd_files[0]
            # Launch in a new visible console window so the user sees launch status & controls
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                ["cmd.exe", "/c", str(cmd_file.resolve())],
                cwd=str(PROJECT_ROOT),
                creationflags=CREATE_NEW_CONSOLE
            )

            self.send_json_response(200, {"status": "ok", "message": f"Launched {cmd_file.name}"})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def handle_list_packs(self):
        try:
            packs_dir = PROJECT_ROOT / "mods/map-packs"
            packs = []
            if packs_dir.is_dir():
                for d in packs_dir.iterdir():
                    if d.is_dir() and (d / "manifest.json").is_file():
                        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                        packs.append(manifest)
            self.send_json_response(200, {"status": "ok", "packs": packs})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def send_json_response(self, code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Concise logging
        print(f"[Studio Web] {self.address_string()} - {format % args}")


def find_free_port(start_port: int = 8080) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port


def main():
    port = find_free_port(8080)
    server_address = ("127.0.0.1", port)
    httpd = http.server.HTTPServer(server_address, StudioRequestHandler)

    url = f"http://127.0.0.1:{port}/"
    print("=" * 70)
    print("  MECHWARRIOR 3 - VISUAL 3D MAP STUDIO")
    print("=" * 70)
    print(f"  Web Studio running at: {url}")
    print("  Open this URL in any browser to create and export custom map packs.")
    print("  Press Ctrl+C to stop.")
    print("=" * 70)

    # Open browser automatically if not in headless environment
    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Studio server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
