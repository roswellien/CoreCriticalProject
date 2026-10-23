"""Install learned pipeline warmup and remove unused monitor pixel buffers."""
from pathlib import Path
import argparse
import shutil


def apply(host):
    renderer = host / 'vk_scene.hpp'
    source = renderer.read_text()
    if 'using PerfOverlay = mw34::performance::Overlay;' not in source:
        raise RuntimeError('Install the current performance monitor adapter before resource warmup')
    patches = [
        ('#include <windows.h>\n', '#include <windows.h>\n#include "pipeline_warmup.hpp"\n'),
        ('    VkRenderPass renderPass{};', '    mw34::pipeline_warmup::Recipe pipelineWarmup;\n    VkRenderPass renderPass{};'),
        ('        flatNormal.valid = true;\n    }', '''        flatNormal.valid = true;
        pipelineWarmup.load(forPresent ? "present" : "scene");
        unsigned warmed = 0;
        for (auto key : pipelineWarmup.states()) {
            const bool model = (key >> 57) & 1, world = (key >> 58) & 1,
                       lit = (key >> 59) & 1;
            if ((model && !gpu_models()) || (lit && !mw34::sun::settings().enabled)) continue;
            PipelineKey state{std::uint8_t(key), std::uint8_t(key >> 8),
                std::uint8_t(key >> 16), std::uint8_t(key >> 24), std::uint8_t(key >> 32),
                std::uint8_t(key >> 40), std::uint8_t(key >> 48), std::uint8_t((key >> 56) & 1)};
            pipeline(state, model, world, lit);
            ++warmed;
        }
        if (warmed) std::fprintf(stderr, "Pipeline warmup: %u known states prepared before rendering\\n", warmed);
    }'''),
        ('        return pipelines[key] = p;', '        pipelineWarmup.record(key);\n        return pipelines[key] = p;'),
        ('        f.vkDeviceWaitIdle(device);\n        if (qualityPipeline)',
         '        f.vkDeviceWaitIdle(device);\n        pipelineWarmup.save();\n        if (qualityPipeline)'),
    ]
    for before, after in patches:
        if after in source:
            continue
        if source.count(before) != 1:
            raise RuntimeError('Unexpected native pipeline warmup anchor: ' + before[:65])
        source = source.replace(before, after, 1)
    hud = host / 'gpu_hud.inc'
    text = hud.read_text()
    before = ' hud_sc.color.resize(size_t(w)*h);hud_sc.depth.resize(hud_sc.color.size());try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);'
    after = ' /* GPU-resident overlay: no CPU color/depth upload or readback. */try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);'
    if after not in text:
        if text.count(before) != 1:
            raise RuntimeError('Unexpected monitor resident-buffer anchor')
        text = text.replace(before, after, 1)
    normals = host / 'surface_normals_stage.inc'
    normal_text = normals.read_text()
    normal_before = '    normal_state.loaded = true;\n}'
    normal_after = '''    normal_state.loaded = true;
    // At the first world material binding, mission texture loading has finished.
    // Use only live, unlocked texture surfaces and the existing version/content
    // checks. Never scan original game files or load every campaign normal page.
    static const bool prewarm = [] {
        const char *value = std::getenv("MW34_NORMAL_PREWARM");
        if (value && std::strcmp(value, "0") && std::strcmp(value, "1"))
            throw std::runtime_error("MW34_NORMAL_PREWARM must be 0 or 1");
        return value && !std::strcmp(value, "1");
    }();
    if (prewarm && mw34::materials::normal_maps_enabled()) {
        unsigned prepared = 0;
        for (auto &surface : host.vsurfaces) {
            if (!surface.guest || !surface.mem || surface.locks ||
                !host.com_object(surface.guest) ||
                !(surface.caps & DDSCAPS_TEXTURE) || surface.bpp != 16) continue;
            surface_normal_binding(surface);
            ++prepared;
        }
        std::fprintf(stderr, "Normal warmup: %u resident texture surfaces checked before rendering\\n", prepared);
    }
}'''
    if normal_after not in normal_text:
        # Upgrade the initial private candidate's weaker liveness predicate.
        normal_text = normal_text.replace(
            'if (!surface.guest || !surface.mem || surface.locks ||\n                !(surface.caps',
            'if (!surface.guest || !surface.mem || surface.locks ||\n                !host.com_object(surface.guest) ||\n                !(surface.caps')
    if normal_after not in normal_text:
        if normal_text.count(normal_before) != 1:
            raise RuntimeError('Unexpected normal catalog initialization anchor')
        normal_text = normal_text.replace(normal_before, normal_after, 1)
    flip = host / 'vdd.inc'
    flip_text = flip.read_text()
    flip_before = ' world_present();geometry_profile.present(host.frames);'
    flip_after = ''' // Keep loading/menu intervals out of the new gameplay measurement window.
 if(host.presenter&&host.presenter->overlay.on){static bool measured_gameplay=false;
  const bool gameplay=host.sren&&host.sren->scenes&&!frontend_on();
  if(gameplay!=measured_gameplay)host.presenter->overlay.reset();measured_gameplay=gameplay;}
 world_present();geometry_profile.present(host.frames);'''
    if flip_after not in flip_text:
        if flip_text.count(flip_before) != 1:
            raise RuntimeError('Unexpected presentation epoch anchor')
        flip_text = flip_text.replace(flip_before, flip_after, 1)
    renderer.write_text(source)
    hud.write_text(text)
    normals.write_text(normal_text)
    flip.write_text(flip_text)
    header = Path(__file__).parent / 'native-overrides' / 'pipeline_warmup.hpp'
    if header.resolve() != (host / header.name).resolve():
        shutil.copyfile(header, host / header.name)
    monitor = header.with_name('performance_monitor.hpp')
    if monitor.resolve() != (host / monitor.name).resolve():
        shutil.copyfile(monitor, host / monitor.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
