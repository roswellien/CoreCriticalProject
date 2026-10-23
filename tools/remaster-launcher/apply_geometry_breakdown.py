"""Instrument a fresh private host to separate original geometry from adapters.

Does not modify the translated module or enable any geometry bypass. All anchors
are checked before writes. Never apply to a selected runtime source snapshot.
"""
from pathlib import Path
import argparse


def apply(host):
    files = {name: (host / name).read_text(encoding="utf-8") for name in
             ("vk_scene.hpp", "mfc_stage.hpp", "d3d_provider.inc", "vdd.inc", "main_v2.inc")}

    def replace(name, old, new):
        if files[name].count(old) != 1:
            raise ValueError(f"{name}: expected one geometry breakdown anchor: {old[:65]}")
        files[name] = files[name].replace(old, new)

    replace("vk_scene.hpp", '#include "geometry_profile.hpp"',
            '#include "geometry_profile.hpp"\n#include "geometry_breakdown.hpp"')
    replace("mfc_stage.hpp", 'inline std::atomic<unsigned>mw34_frames_presented{0};',
            'inline std::atomic<State*> mw34_profile_state{nullptr};\n'
            'inline DWORD mw34_profile_main_thread{};\n'
            'inline std::atomic<unsigned>mw34_frames_presented{0};')
    replace("mfc_stage.hpp", 'active=true;FastGateScope fast_gate(*this);',
            'active=true;FastGateScope fast_gate(*this);'
            'struct PublishProfileState{bool main;PublishProfileState(State*s):'
            'main(::GetCurrentThreadId()==mw34_profile_main_thread){'
            'if(main)mw34_profile_state.store(s);}~PublishProfileState(){'
            'if(main)mw34_profile_state.store(nullptr);}} publish_profile_state(&state);')
    replace("mfc_stage.hpp", " void*remaster_body(State*s,unsigned target,void*p,Body body){",
            " void*remaster_body(State*s,unsigned target,void*p,Body body){"
            "mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::Adapter,"
            "mw34::geometry_breakdown::selected(target));")
    # Body-only timing starts after the admission/override adapters. Nested API,
    # draw and material scopes remove their time from this body category.
    start = files["mfc_stage.hpp"].index(" void*remaster_body_inner(")
    end = files["mfc_stage.hpp"].index(" void*controller_next_body(", start)
    section = files["mfc_stage.hpp"][start:end]
    if section.count("body(s,target,p)") != 4:
        raise ValueError("Original geometry body invocation anchors changed")
    section = section.replace("body(s,target,p)", "geometry_profiled_body(s,target,p,body)")
    helper = (" void*geometry_profiled_body(State*s,unsigned target,void*p,Body body){"
              "mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::body(target,"
              "bool(world_scope)),mw34::geometry_breakdown::selected(target));return body(s,target,p);}\n")
    files["mfc_stage.hpp"] = files["mfc_stage.hpp"][:start] + helper + section + files["mfc_stage.hpp"][end:]
    replace("mfc_stage.hpp", "void*api(State*s,unsigned token,void*p){",
            "void*api(State*s,unsigned token,void*p){"
            "mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::Api);")
    replace("d3d_provider.inc", "if(vcount>65535||!readable(verts,32*vcount))",
            "mw34::geometry_breakdown::Scope draw_measure(mw34::geometry_breakdown::Draw);"
            "if(vcount>65535||!readable(verts,32*vcount))")
    for call, category in (("world_capture(c)", "WorldBinding"),
                           ("sun_capture_tl(c);sun_capture_sky(c)", "SunCapture"),
                           ("effect_observe(c)", "EffectCapture")):
        replace("d3d_provider.inc", call + ";", "{mw34::geometry_breakdown::Scope measure("
                f"mw34::geometry_breakdown::{category});{call};}}")
    replace("d3d_provider.inc", "void render_scene(D3DDev&d){",
            "void render_scene(D3DDev&d){mw34::geometry_breakdown::Scope measure("
            "mw34::geometry_breakdown::Scene);")
    # Keep render/shadow time out of scene assembly; these anchors cover both
    # renderer entry points and the existing bounded shadow preparation phase.
    replace("vk_scene.hpp", "void render(Scene &s, bool upload_in = true, bool readback_out = true) {",
            "void render(Scene &s, bool upload_in = true, bool readback_out = true) {"
            "mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::Renderer);")
    replace("vk_scene.hpp", "void finish_world() {", "void finish_world() {"
            "mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::Renderer);")
    replace("vk_scene.hpp", "const auto fixtureLights = prepare_fixture_shadows(s, bound);",
            "const auto fixtureLights = [&]{mw34::geometry_breakdown::Scope measure("
            "mw34::geometry_breakdown::ShadowPrepare);return prepare_fixture_shadows(s,bound);}();")
    replace("vk_scene.hpp", "record_fixture_shadows(fixtureLights);",
            "{mw34::geometry_breakdown::Scope measure(mw34::geometry_breakdown::ShadowRecord);"
            "record_fixture_shadows(fixtureLights);}")
    replace("vdd.inc", "world_present();geometry_profile.present(host.frames);",
            "world_present();geometry_profile.present(host.frames);"
            "mw34::geometry_breakdown::present(host.frames);")
    # Reuse the deeper sampler already used for the whole-frame investigation.
    # Read the main guest PC only while that thread is suspended. This is a
    # correlation to its last published PC, not instruction-exact guest timing.
    sampler = (Path(__file__).parent / 'native-overrides/geometry_breakdown_sampler.inc').read_text(encoding='utf-8')
    begin = files['main_v2.inc'].index('struct HostProfiler{')
    finish = files['main_v2.inc'].index('static HostProfiler host_profiler;', begin)
    files['main_v2.inc'] = files['main_v2.inc'][:begin] + sampler + files['main_v2.inc'][finish:]
    for name, content in files.items():
        (host / name).write_text(content, encoding="utf-8")
    (host / "geometry_breakdown.hpp").write_bytes(
        (Path(__file__).parent / "native-overrides/geometry_breakdown.hpp").read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
