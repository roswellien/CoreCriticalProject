"""Private candidate: route unhandled function targets straight to their body.

The complete adapter functions are pinned, not just their target literals. A
source change needs a fresh side-effect review before this fast route applies.
CALL/RET/SEH validation and HUD interception in enter() remain ahead of it.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

CONTRACTS = {
    "mfc_stage.hpp": (" void*lighting_body(", " void*enter(",
        "6f5c5c700362bb99ecf51457dd0e6658c0df233af9184f273e69f2deefccf020"),
    "photo_replay_stage.inc": ("void* photo_replay_body(", None,
        "89c07c9bcaed662714b8a39efd4ad2765d68ada5fe2079e16668917ee4a40f1d"),
    "controller_stage.inc": ("template<class Next>void*controller_body(", None,
        "610ba1795a695a73ba9143c02123c2d240f515784548db26fabf01c466e10488"),
    "turret_aim_stage.inc": ("template<class Next>void*turret_aim_body(", None,
        "d939d9c4cffcabc51b0c67017b381aa29b311ede06f5e2d07fbc83f86ad54a6c"),
}


def checked_targets(host):
    targets = set()
    for name, (start, end, expected) in CONTRACTS.items():
        text = (host / name).read_text(encoding="utf-8")
        begin = text.index(start)
        section = text[begin:text.index(end, begin) if end else None]
        if hashlib.sha256(section.encode()).hexdigest() != expected:
            raise ValueError(f"{name}: adapter side-effect contract changed; review required")
        targets.update(int(value, 16) for value in
                       re.findall(r"\btarget\s*==\s*(0x[0-9a-fA-F]+)", section))
    if len(targets) != 73 or any(value & 15 or not 0x400000 <= value < 0x600000 for value in targets):
        raise ValueError("Adapter target domain changed")
    return sorted(targets)


def header(targets):
    entries = ",".join(hex(value)+"U" for value in targets)
    return '''#pragma once
#include <array>
#include <cstdint>
namespace mw34::body_dispatch {
// All side effects in the four reviewed adapter bodies are target guarded.
// This table only classifies calls; it never replaces original game execution.
inline constexpr unsigned targets[]{ENTRIES};
inline constexpr auto table = [] {
    std::array<std::uint64_t, 2048> bits{};
    for (unsigned target : targets) {
        const unsigned slot = (target - 0x400000U) >> 4;
        bits[slot >> 6] |= std::uint64_t{1} << (slot & 63);
    }
    return bits;
}();
inline bool handled(unsigned target) {
    if (target < 0x400000U || target >= 0x600000U || (target & 15)) return false;
    const unsigned slot = (target - 0x400000U) >> 4;
    return (table[slot >> 6] >> (slot & 63)) & 1;
}
}
'''.replace("ENTRIES", entries)


def apply(host):
    targets = checked_targets(host)
    path = host / "mfc_stage.hpp"
    text = path.read_text(encoding="utf-8")
    include = '#include "service_history.hpp"'
    anchor = ' void*remaster_body(State*s,unsigned target,void*p,Body body){'
    member = ' mw34::GeometryProfile geometry_profile;'
    if text.count(include) != 1 or text.count(anchor) != 1 or text.count(member) != 1:
        raise ValueError("Body routing anchors changed")
    text = text.replace(include, include+'\n#include "body_dispatch.hpp"')
    text = text.replace(member, member+'\n bool body_dispatch_warmed{};')
    text = text.replace(anchor, anchor+'''
  static const bool fast=[]{const char*p=std::getenv("MW34_BODY_DISPATCH");
   if(!p||!*p||!std::strcmp(p,"0"))return false;
   if(!std::strcmp(p,"1"))return true;
   throw std::runtime_error("MW34_BODY_DISPATCH must be 0 or 1");}();
  // The first ordinary call still traverses every adapter, retaining lazy
  // launch-setting initialization and its original validation failures.
  if(fast&&!mw34::body_dispatch::handled(target)){
   if(body_dispatch_warmed)return body(s,target,p);
   body_dispatch_warmed=true;
  }
''')
    path.write_text(text, encoding="utf-8")
    (host / "body_dispatch.hpp").write_text(header(targets), encoding="utf-8")
    return {"targets": targets, "adapter_contracts": {name: row[2] for name, row in CONTRACTS.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    args = parser.parse_args()
    result = apply(args.host_source.resolve(strict=True))
    print(json.dumps(result, indent=2))
