"""Install authored missile presentation and PPC light gain in a fresh R6 host.

No original game media or generated bodies are embedded in this applicator.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def apply(host):
    pending = {}

    def edit(name, old, new):
        path = host / name
        text = pending.get(path, path.read_text(encoding="utf-8"))
        if new in text:
            return
        if text.count(old) != 1:
            raise ValueError(f"{name}: expected one weapon-presentation anchor {old[:70]!r}")
        pending[path] = text.replace(old, new, 1)

    edit("mfc_stage.hpp", '#include "vk_scene.hpp"',
         '#include "vk_scene.hpp"\n#include "missile_exhaust.hpp"')
    edit("mfc_stage.hpp", '#include "effect_lighting_stage.inc"',
         '#include "effect_lighting_stage.inc"\n#include "missile_exhaust_stage.inc"')
    edit("mfc_stage.hpp", 'bool condition_schematic{};unsigned hud_role{};',
         'bool missile_exhaust{};bool condition_schematic{};unsigned hud_role{};')
    edit("mfc_stage.hpp", 'void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};',
         'void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};\n'
         '  if(missile_enabled()){\n'
         '   if(target==0x585010)return missile_create_body(s,target,p,body);\n'
         '   if(target==0x584f40||target==0x586600)missile_retire(state.gpr.rdx.dword);\n'
         '   if(target==0x4eaea0)missile_retire_root(state.gpr.rcx.dword);\n'
         '  }')
    edit("mfc_stage.hpp", '(override_enabled()||photo_replay_detached_cam())){const auto previous=override_begin(state.gpr.rcx.dword);',
         '(override_enabled()||photo_replay_detached_cam()||missile_enabled())){const auto previous=override_begin(state.gpr.rcx.dword);missile_begin(state.gpr.rcx.dword);')
    edit("mfc_stage.hpp", 'catch(...){override_restore(previous);throw;}override_restore(previous);',
         'catch(...){missile_end();override_restore(previous);throw;}missile_end();override_restore(previous);')
    edit("mfc_stage.hpp", 'if(target==0x51fb30)override_emit();',
         'if(target==0x51fb30){override_emit();missile_emit();}')
    edit("body_dispatch.hpp", '0x57e110U,0x5a6790U',
         '0x57e110U,0x584f40U,0x585010U,0x586600U,0x4eaea0U,0x5a6790U')
    edit("d3d_provider.inc", 'if(c.override_texture>=0){const auto&o=override_state();',
         'if(c.missile_exhaust){missile_texture(sc,dr);}else if(c.override_texture>=0){const auto&o=override_state();')
    edit("d3d_provider.inc", '((tex||c.override_texture>=0)?4U:0U)',
         '((tex||c.override_texture>=0||c.missile_exhaust)?4U:0U)')
    for name, source in (
        ("missile_exhaust.hpp", ROOT / "runtime/graphics/missile_exhaust.hpp"),
        ("missile_exhaust_stage.inc", Path(__file__).parent / "native-overrides/missile_exhaust_stage.inc"),
    ):
        pending[host / name] = source.read_text(encoding="utf-8")
    # The selected host has the existing fixture-shadow uniform extension.
    # Retain that shader ABI while updating the authored cache implementation.
    effects = (ROOT / "runtime/graphics/effect_lighting.hpp").read_text(encoding="utf-8")
    if "shadow{}" in (host / "effect_lighting.hpp").read_text(encoding="utf-8"):
        effects = effects.replace("std::array<Light, capacity> lights{};",
                                  "std::array<Light, capacity> lights{};\n    std::array<std::array<float, 4>, capacity> shadow{};")
        effects = effects.replace("sizeof(Uniform) == 16 + 48 * capacity", "sizeof(Uniform) == 16 + 64 * capacity")
    pending[host / "effect_lighting.hpp"] = effects
    for path, text in pending.items():
        path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
