"""Performance: the GPU performance overlay no longer allocates full-frame host buffers.

overlay_gpu (performance monitor, on by default in the Big Lake launcher) sized
its HUD scene's colour and depth vectors to the full target every frame
(3440x1440: ~20 MB allocated, zero-filled and freed per frame). The scene is
rendered resident (no upload, no readback), and Renderer::render only requires
host pixels for an upload or a readback, so the vectors are left empty, as the
resident 3D scenes already do. A 3000-frame stress profile attributed ~7% of
main-thread samples to this resize and its frees. Rendering is unchanged.
Apply after apply_perf_env_cache.py.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one overlay anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    edit(host/'gpu_hud.inc',
         ' hud_sc.color.resize(size_t(w)*h);hud_sc.depth.resize(hud_sc.color.size());try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}',
         ' /* resident: no host colour/depth buffers */try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
