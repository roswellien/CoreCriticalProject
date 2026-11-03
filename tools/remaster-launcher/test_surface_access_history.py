"""Regression checks for read-only surface readback and HUD CPU fallback."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "tools/m4-crt-heap-carry/host"


def section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    return source[start_index:source.index(end, start_index)]


class SurfaceAccessHistoryTests(unittest.TestCase):
    def test_read_only_z_buffer_lock_does_not_change_surface_version(self):
        source = (HOST / "vdd.inc").read_text(encoding="utf-8")
        lock = section(source, 'if(n=="Lock")', 'if(n=="Unlock")')
        unlock = section(source, 'if(n=="Unlock")', 'if(n=="Flip")')

        self.assertIn(
            "const bool gpu_hud_lock=hud_gpu_active&&v->guest==host.res_rt;", lock
        )
        self.assertIn(
            "if(!(flags&DDLOCK_READONLY)&&!gpu_hud_lock)camera_surface_written(v->guest);",
            lock,
        )
        self.assertIn(
            "v->lock_access.acquire((flags&DDLOCK_READONLY)!=0,gpu_hud_lock);", lock
        )
        self.assertIn("v->lock_access.release(!v->locks)", unlock)
        self.assertIn("if(v->lock_access.release(!v->locks))v->version=++host.surface_versions;", unlock)

    def test_hud_fallback_invalidates_before_cpu_access_but_gpu_unlock_does_not(self):
        vdd = (HOST / "vdd.inc").read_text(encoding="utf-8")
        hud = (HOST / "gpu_hud.inc").read_text(encoding="utf-8")
        mfc = (HOST / "mfc_stage.hpp").read_text(encoding="utf-8")
        unlock = section(vdd, 'if(n=="Unlock")', 'if(n=="Flip")')
        self.assertIn('#include "surface_access.hpp"', mfc)
        self.assertIn("mw34::surface::LockAccess lock_access;", mfc)
        fallback = section(hud, "void hud_fallback()", "// Entry interception")
        intercept = section(hud, "bool hud_intercept", "// FPS/frame-time")
        touch_sync = section(mfc, "void touch_sync()", "bool touch_range")

        self.assertIn("run_cpu_fallback", fallback)
        self.assertLess(
            fallback.index("camera_surface_written(host.res_rt)"),
            fallback.index("hud_flush()"),
        )
        self.assertLess(
            fallback.index("hud_flush()"),
            fallback.index("lock_access.expose_cpu_access()"),
        )
        self.assertIn(
            "rt&&rt->locks&&rt->lock_access.writable())camera_surface_written(host.res_rt);",
            fallback,
        )
        self.assertLess(
            fallback.index("lock_access.expose_cpu_access()"),
            fallback.index("gpu_sync(host.res_rt)"),
        )
        self.assertNotIn("lock_writable", fallback)
        self.assertIn("hud_fallback();", intercept)
        self.assertIn("return false;", intercept)
        self.assertIn("if(hud_gpu_active)", touch_sync)
        self.assertIn("hud_fallback();", touch_sync)
        self.assertIn("if(hud_intercept(target,p,r))return r;", mfc)
        self.assertIn(
            "if(hud_gpu_active&&v->guest==host.res_rt){"
            "hud_flush();hud_gpu_active=false;--v->locks;"
            "if(v->lock_access.release(!v->locks))v->version=++host.surface_versions;"
            "return done(DD_OK,2);}",
            unlock,
        )


if __name__ == "__main__":
    unittest.main()
