"""Additive scope clarification and final physical pin check, without rewrites."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from recover import ROOT, bind, require, save

out = ROOT / "reports/m4-service-initializers/static-r1"
require(not (out / "final-report.json").exists(), "Fresh additive final seal required")
pins = json.loads((out / "pins.json").read_text())["bindings"]
for item in pins:
    require(bind(item["path"]) == item, "Frozen recovery/completion identity changed")
clarifications = {
    "registration_flag_scope": "0x5AC140's NEG/SBB/NEG/DEC flags are observable at that helper's return. At the complete 0x4C58C0 initializer return, ADD ESP,4 at 0x4C593A is the final integer arithmetic-flag writer; it overrides those six arithmetic flags. EAX remains registration status0/-1. Both phases must retain actual stack-dependent flag behavior.",
    "first_leaf_instruction_count": "Actual numeric_limits<float>::max provider is two instructions, FLD then RET; one earlier conversational progress note said three and is superseded by exact pinned decode.",
    "group_arithmetic": "Groups overlap FS/import categories. 117 import-dependent +26 import-free normal direct roots +one undecoded root =144; the31 FS roots are not an additional31 roots.",
    "original_scope": "Static instruction decoding and abstract ABI/def-use only. No original/provider/native worker execution, service success, full startup or M4 acceptance. Entire known branch-reachable bodies and outgoing unresolved dependencies are preserved, not falsely labelled full provider closure.",
    "frozen_initial_extra_addresses": "0x5B1359 and0x5B386B remain excluded exploratory constants with no execution/closure credit. Actual reached PUSH targets0x5AED59 and0x5B986B have independently byte-checked complete3-instruction metadata+__CxxFrameHandler thunks in the additive supplement."
}
save(out / "final-clarifications.json", clarifications)
report = {"schema_version": 1, "passed_static_recovery": True,
          "scope": "Static-only exact service-initializer ABI/CFG/workload plan",
          "base_report": bind(out / "report.json"), "prior_pin_map": bind(out / "pins.json"),
          "clarifications": bind(out / "final-clarifications.json"), "source": bind(Path(__file__)),
          "next_candidate": {"slot": 0x5E016C, "root": 0x4C19F0, "provider": "Exact staged MSVCP50.DLL leaf0x780C10F0", "normal_game_instructions": 21, "provider_instructions": 2},
          "all_prior_bindings_rehashed_unchanged": len(pins),
          "no_execution_or_admission_claim": True}
save(out / "final-report.json", report)
paths = {p["path"] for p in pins}
paths.update(str(p.resolve()) for p in out.iterdir() if p.is_file() and p.name != "final-pins.json")
paths.add(str(Path(__file__).resolve()))
save(out / "final-pins.json", {"schema_version": 1, "bindings": [bind(p) for p in sorted(paths)]})
print(json.dumps({"report": bind(out / "final-report.json"), "pins": bind(out / "final-pins.json"), "bindings": len(paths)}))
