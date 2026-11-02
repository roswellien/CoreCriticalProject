#!/usr/bin/env python3
"""MW3 Visual Map Studio - Web Application Server.

Serve the Three.js preview and local prototype export/launch APIs on loopback.
The preview terrain and requested gameplay properties are not all implemented
by the archive builder. Exports stay local under mods/map-packs/<pack_id>/.
This process does not own the game installation or a running native game session.
"""

import http.server
import json
import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

# Setup paths
TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parents[2]
WEB_ROOT = TOOLS_ROOT / "editor/web"

# Add tools root to sys.path so editor modules can be imported
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.map_pack import MapPackProject, MapPackBuilder, pack_directory
from editor.core.campaign import CampaignProject, CampaignBuilder, campaign_directory
from editor.config import game_directory


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving Studio frontend and handling Mod Pack APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        if not self.check_local_request():
            return
        if self.path == "/api/list-packs":
            self.handle_list_packs()
        elif self.path == "/api/list-campaigns":
            self.handle_list_campaigns()
        else:
            super().do_GET()

    def do_POST(self):
        if not self.check_local_request():
            return
        if (
            self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            != "application/json"
        ):
            self.send_error(415, "Use application/json")
            return
        if self.path == "/api/export-pack":
            self.handle_export_pack()
        elif self.path == "/api/launch-map":
            self.handle_launch_map()
        elif self.path == "/api/export-campaign":
            self.handle_export_campaign()
        elif self.path == "/api/launch-campaign":
            self.handle_launch_campaign()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_export_pack(self):
        try:
            data = self.read_json_request()

            project = MapPackProject.from_dict(data)
            builder = MapPackBuilder(
                packs_root=PROJECT_ROOT / "mods/map-packs", game_root=game_directory()
            )
            out_folder = builder.build(project)

            launcher_name = f"Play Map - {project.pack_id}.cmd"

            resp = {
                "status": "ok",
                "pack_id": project.pack_id,
                "pack_folder": str(out_folder),
                "total_placed_assets": len(project.assets),
                "launcher_script": launcher_name,
            }
            self.send_json_response(200, resp)
        except (ValueError, TypeError, KeyError) as e:
            self.send_json_response(400, {"status": "error", "message": str(e)})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def handle_launch_map(self):
        try:
            data = self.read_json_request()
            pack_id = data.get("pack_id", "")

            pack_folder = pack_directory(PROJECT_ROOT / "mods/map-packs", pack_id)
            if not pack_folder.is_dir():
                self.send_json_response(
                    400, {"status": "error", "message": f"Pack folder not found: {pack_id}"}
                )
                return

            cmd_files = list(pack_folder.glob("Play Map - *.cmd"))
            if not cmd_files:
                self.send_json_response(
                    400, {"status": "error", "message": "No launcher command file found in pack"}
                )
                return

            cmd_file = cmd_files[0].resolve()
            if not cmd_file.is_relative_to(pack_folder):
                raise ValueError("Pack launcher resolves outside its pack directory.")
            # Launch in a new visible console window so the user sees launch status & controls
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                ["cmd.exe", "/c", str(cmd_file.resolve())],
                cwd=str(PROJECT_ROOT),
                creationflags=CREATE_NEW_CONSOLE,
            )

            self.send_json_response(200, {"status": "ok", "message": f"Launched {cmd_file.name}"})
        except (ValueError, TypeError, KeyError) as e:
            self.send_json_response(400, {"status": "error", "message": str(e)})
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

    def handle_export_campaign(self):
        try:
            data = self.read_json_request()
            campaign = CampaignProject.from_dict(data)
            builder = CampaignBuilder(
                campaigns_root=PROJECT_ROOT / "mods/campaign-packs",
                map_packs_root=PROJECT_ROOT / "mods/map-packs",
                game_root=game_directory(),
            )
            out_folder = builder.build(campaign)
            launcher_name = f"Play Campaign - {campaign.campaign_id}.cmd"

            resp = {
                "status": "ok",
                "campaign_id": campaign.campaign_id,
                "campaign_folder": str(out_folder),
                "total_missions": len(campaign.missions),
                "launcher_script": launcher_name,
            }
            self.send_json_response(200, resp)
        except (ValueError, TypeError, KeyError) as e:
            self.send_json_response(400, {"status": "error", "message": str(e)})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def handle_launch_campaign(self):
        try:
            data = self.read_json_request()
            campaign_id = data.get("campaign_id", "")
            campaign_folder = campaign_directory(PROJECT_ROOT / "mods/campaign-packs", campaign_id)
            if not campaign_folder.is_dir():
                self.send_json_response(
                    400, {"status": "error", "message": f"Campaign folder not found: {campaign_id}"}
                )
                return

            cmd_files = list(campaign_folder.glob("Play Campaign - *.cmd"))
            if not cmd_files:
                self.send_json_response(
                    400, {"status": "error", "message": "No launcher command file found in campaign"}
                )
                return

            cmd_file = cmd_files[0].resolve()
            if not cmd_file.is_relative_to(campaign_folder):
                raise ValueError("Campaign launcher resolves outside its campaign directory.")

            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                ["cmd.exe", "/c", str(cmd_file.resolve())],
                cwd=str(PROJECT_ROOT),
                creationflags=CREATE_NEW_CONSOLE,
            )
            self.send_json_response(200, {"status": "ok", "message": f"Launched {cmd_file.name}"})
        except (ValueError, TypeError, KeyError) as e:
            self.send_json_response(400, {"status": "error", "message": str(e)})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def handle_list_campaigns(self):
        try:
            campaigns_dir = PROJECT_ROOT / "mods/campaign-packs"
            campaigns = []
            if campaigns_dir.is_dir():
                for d in campaigns_dir.iterdir():
                    if d.is_dir() and (d / "manifest.json").is_file():
                        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                        campaigns.append(manifest)
            self.send_json_response(200, {"status": "ok", "campaigns": campaigns})
        except Exception as e:
            self.send_json_response(500, {"status": "error", "message": str(e)})

    def send_json_response(self, code: int, data: dict):
        """Send one UTF-8 JSON body with a byte length for browser response framing."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def check_local_request(self) -> bool:
        """Loopback binding does not protect against a page on another origin.

        Check Host to prevent DNS rebinding and Origin for browser mutations.
        Command-line clients can omit Origin; they must still use the local host.
        """
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "").lower() not in hosts:
            self.send_error(403, "Local Host required")
            return False
        origin = self.headers.get("Origin")
        if origin is not None:
            try:
                parsed = urlsplit(origin)
                valid = (
                    parsed.scheme == "http"
                    and parsed.netloc.lower() in hosts
                    and not parsed.path
                    and not parsed.query
                    and not parsed.fragment
                )
            except ValueError:
                valid = False
            if not valid:
                self.send_error(403, "Same-origin request required")
                return False
        return True

    def read_json_request(self) -> dict:
        """Bound memory use and reject malformed bodies before touching packs."""
        if self.headers.get("Transfer-Encoding"):
            raise ValueError("Transfer-Encoding is not supported.")
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 1024 * 1024:
            raise ValueError("JSON body must be between 1 byte and 1 MiB.")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Request must contain a JSON object.")
        return data

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
