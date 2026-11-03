"""Verification test for MW3 Visual Map Studio web server & API endpoints."""

import json
import threading
import time
import urllib.request
from pathlib import Path
import sys

TOOLS_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(TOOLS_ROOT))

from run_studio import StudioRequestHandler
import http.server


def test_studio_api():
    port = 8899
    server = http.server.HTTPServer(("127.0.0.1", port), StudioRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # 1. Test GET / (HTML index)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "Visual 3D Map Studio" in html
            print("[OK] GET / returned 200 with Studio HTML")

        # 1b. Test GET /api/status
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as resp:
            assert resp.status == 200
            status_data = json.loads(resp.read().decode("utf-8"))
            assert status_data["status"] == "ok"
            assert "game_installed" in status_data
            assert "tools_available" in status_data
            print(f"[OK] GET /api/status returned ok (game_installed={status_data['game_installed']})")

        # 2. Test GET /api/list-packs
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/list-packs") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert any(p["pack_id"] == "iron_ridge_outpost" for p in data["packs"])
            print(
                f"[OK] GET /api/list-packs returned {len(data['packs'])} packs (including iron_ridge_outpost)"
            )

        # 3. Test POST /api/export-pack
        sample_pack = {
            "pack_id": "test_api_pack",
            "pack_title": "Test API Map",
            "author": "Test Author",
            "version": "1.0.0",
            "description": "Automated API test pack",
            "base_operation": "c1",
            "terrain": {
                "biome": "coastal",
                "width": 3000.0,
                "depth": 3000.0,
                "height_scale": 80.0,
                "water_level": 3.0,
                "roughness": 0.5,
            },
            "lighting": {
                "preset_name": "noon",
                "azimuth": 180.0,
                "elevation": 75.0,
                "strength": 1.0,
                "ambient": 0.3,
                "sun_color": [1, 1, 1],
                "sky_tint": [0.4, 0.6, 0.9],
                "fog_distance": 1100,
            },
            "assets": [
                {
                    "asset_id": "t1",
                    "asset_type": "turret_srm",
                    "name": "Test SRM",
                    "x": 100.0,
                    "y": 5.0,
                    "z": 200.0,
                    "yaw_deg": 45.0,
                    "faction": "enemy",
                    "health": 100,
                }
            ],
        }
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/export-pack",
            data=json.dumps(sample_pack).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            res_data = json.loads(resp.read().decode("utf-8"))
            assert res_data["status"] == "ok"
            assert res_data["pack_id"] == "test_api_pack"
            print("[OK] POST /api/export-pack compiled and returned ok")

        # 3b. Test POST /api/package-pack
        req_pkg = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/package-pack",
            data=json.dumps({"pack_id": "test_api_pack"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_pkg) as resp:
            assert resp.status == 200
            res_pkg = json.loads(resp.read().decode("utf-8"))
            assert res_pkg["status"] == "ok"
            assert "zip_name" in res_pkg
            assert (ROOT / "dist" / res_pkg["zip_name"]).is_file()
            print(f"[OK] POST /api/package-pack produced {res_pkg['zip_name']}")

        # Cleanup test pack
        import shutil

        test_folder = ROOT / "mods/map-packs/test_api_pack"
        if test_folder.is_dir():
            shutil.rmtree(test_folder)
        test_zip = ROOT / "dist/test_api_pack.zip"
        if test_zip.is_file():
            test_zip.unlink()

        # 4. Test POST /api/export-campaign
        sample_campaign = {
            "campaign_id": "test_api_campaign",
            "campaign_title": "Test Campaign",
            "author": "API Tester",
            "version": "1.0.0",
            "missions": [
                {
                    "mission_id": "m1_test",
                    "pack_id": "iron_ridge_outpost",
                    "title": "Stage 1: Beachhead",
                    "briefing_text": "Establish beachhead at Iron Ridge.",
                }
            ],
        }
        req_camp = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/export-campaign",
            data=json.dumps(sample_campaign).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_camp) as resp:
            assert resp.status == 200
            res_camp = json.loads(resp.read().decode("utf-8"))
            assert res_camp["status"] == "ok"
            assert res_camp["campaign_id"] == "test_api_campaign"
            print("[OK] POST /api/export-campaign compiled and returned ok")

        # 5. Test GET /api/list-campaigns
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/list-campaigns") as resp:
            assert resp.status == 200
            data_camp = json.loads(resp.read().decode("utf-8"))
            assert data_camp["status"] == "ok"
            assert any(c["campaign_id"] == "test_api_campaign" for c in data_camp["campaigns"])
            print(f"[OK] GET /api/list-campaigns returned {len(data_camp['campaigns'])} campaigns")

        # Cleanup test campaign
        test_camp_folder = ROOT / "mods/campaign-packs/test_api_campaign"
        if test_camp_folder.is_dir():
            shutil.rmtree(test_camp_folder)

        print("\nAll Studio API tests PASSED successfully!")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    test_studio_api()
