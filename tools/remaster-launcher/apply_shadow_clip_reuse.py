"""Reuse identical shadow-face corner transforms in an admitted private host.

This changes host-side shadow culling only. The original game bodies, caster
order, clipping comparisons, shadow shaders and emitted draws are retained.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = "f44627d44d1792b8a76eb2540103668570e84f725b756631cd238400d80aa087"


def apply(host):
    stage = host / "fixture_shadow_stage.inc"
    renderer = host / "vk_scene.hpp"
    source = stage.read_text(encoding="utf-8")
    if hashlib.sha256(stage.read_bytes()).hexdigest() != CONTRACT:
        raise ValueError("Shadow recording source changed; review required")
    begin = "                    bool outside=false;for(unsigned plane=0;plane<6;++plane)"
    end = "\n                    if(outside)continue;"
    if source.count(begin) != 1 or source.count(end) != 1:
        raise ValueError("Shadow face test anchors changed")
    start = source.index(begin)
    stop = source.index(end, start)
    original = source[start:stop]
    method = "    void record_fixture_shadows(const mw34::effects::Uniform& lights) {"
    if source.count(method) != 1:
        raise ValueError("Shadow recording entry changed")
    replacement = ("                    bool outside=false;\n"
                   "                    if(reuse_clip)outside=mw34::shadow_clip_reuse::outside(clip,caster->bounds);\n"
                   "                    else {" + original.strip().replace("bool outside=false;", "", 1) + "}")
    source = source[:start] + replacement + source[stop:]
    source = source.replace(method, method + '''
        static const bool reuse_clip=[] {
            const char* value=std::getenv("MW34_SHADOW_CLIP_REUSE");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_SHADOW_CLIP_REUSE must be 0 or 1");
        }();''')
    text = renderer.read_text(encoding="utf-8")
    anchor = '#include "fixture_shadow.hpp"'
    if text.count(anchor) != 1 or "shadow_clip_reuse.hpp" in text:
        raise ValueError("Shadow helper include changed")
    helper = host / "shadow_clip_reuse.hpp"
    if helper.exists():
        raise ValueError("Shadow helper already exists")
    payload = (Path(__file__).parent / "native-overrides/shadow_clip_reuse.hpp").read_bytes()
    text = text.replace(anchor, anchor + '\n#include "shadow_clip_reuse.hpp"')
    # All contracts are checked before modifying the private snapshot.
    stage.write_text(source, encoding="utf-8")
    renderer.write_text(text, encoding="utf-8")
    helper.write_bytes(payload)
    return {"parent_shadow_source_sha256": CONTRACT,
            "helper_sha256": hashlib.sha256(payload).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.host_source.resolve(strict=True)), indent=2))
