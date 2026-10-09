"""Add exact handler-boundary recovery and an actionable static ABI plan.

Consumes the frozen first recovery files without editing them. The two earlier
exploratory extra addresses are explicitly excluded; reached handler addresses
are derived from actual initializer PUSH operands. No original/provider/native
instruction is executed. This source contains no original instruction bytes.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
from recover import ROOT, DECODER, ROW, Module, bind, closure, require, save, subgraph

OUT = ROOT / "reports/m4-service-initializers/static-r1"


def parse(module, data):
    for line in data.decode("utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        pc, code = int(match[1], 16), bytes.fromhex(match[2])
        off, _ = module.image.rva_range(pc - module.base, len(code))
        require(module.image.read(off, len(code)) == code, "Supplemental decoder bytes differ")
        asm = re.sub(r"\s+", " ", match[3].strip())
        mnemonic, _, operands = asm.partition(" ")
        row = {"pc": pc, "size": len(code), "bytes": code.hex(), "mnemonic": mnemonic, "operands": operands}
        require(pc not in module.rows or module.rows[pc] == row, "Supplemental conflicting boundary")
        module.rows[pc] = row


def main():
    require((OUT / "recovery-pins.json").is_file() and not (OUT / "report.json").exists(), "Fresh completion of existing recovery only")
    frozen = json.loads((OUT / "recovery-pins.json").read_text(encoding="utf-8"))["bindings"]
    for item in frozen:
        require(bind(item["path"]) == item, "Initial recovery pin changed")
    modules = {"game": Module(ROOT / "MW3/Mech3.exe"),
               "MSVCRT.DLL": Module(ROOT / "local/mw3-staged/Shared_DLLs/MSVCRT.DLL"),
               "MSVCP50.DLL": Module(ROOT / "local/mw3-staged/Shared_DLLs/MSVCP50.DLL"),
               "MFC42.DLL": Module(ROOT / "local/mw3-staged/Shared_DLLs/MFC42.DLL")}
    for module in modules.values():
        parse(module, (OUT / (module.path.name + ".linear-lookup.txt")).read_bytes())
    commands = []
    # Both handler addresses below come from exact reached PUSH operands; the
    # provider boundary is the one missing target from the first provider CFG.
    for name, start, stop in [("game", 0x5AED59, 0x5AED63), ("game", 0x5B986B, 0x5B9875),
                              ("game", 0x5AC100, 0x5AC106), ("MSVCRT.DLL", 0x78001222, 0x78001227)]:
        module = modules[name]
        command = [str(DECODER), "--disassemble", "--x86-asm-syntax=intel",
                   f"--start-address={start}", f"--stop-address={stop}", str(module.path)]
        result = subprocess.run(command, check=True, capture_output=True, timeout=30)
        path = OUT / (module.path.name + f".aligned-{start:x}.txt")
        require(not path.exists(), "Existing supplemental decode")
        path.write_bytes(result.stdout)
        parse(module, result.stdout)
        commands.append({"command": command, "output": bind(path)})
    game = modules["game"]
    handlers, deferred = closure(game, [0x5AED59, 0x5B986B, 0x5AC3A0])
    require(not deferred, "Entry/handler direct local deferred")
    require(len(handlers[0x5AED59]["instructions"]) == 3 and len(handlers[0x5B986B]["instructions"]) == 3,
            "Handler thunk extent changed")
    provider = json.loads((OUT / "MSVCRT.DLL.provider.json").read_text())
    amended, provider_deferred = closure(modules["MSVCRT.DLL"], [r["preferred_va"] for r in provider["requested_exports"]])
    require(not provider_deferred, "Provider supplement deferred")
    save(OUT / "aligned-entry-handler-provider-supplement.json", {
        "commands": commands, "game_graphs": handlers, "MSVCRT_graphs": amended,
        "excluded_exploratory_extra_entries": [0x5B1359, 0x5B386B],
        "exclusion_reason": "Earlier exploratory extra constants were not the reached SEH PUSH targets. They remain failed/open exploration only; exact reached 0x5AED59 and 0x5B986B supersede them without modifying the original dossier.",
        "provider_missing_boundary_now_decoded": 0x78001222,
        "remaining_provider_indirect_sites": sorted({r["pc"] for n in amended.values() for r in n["unresolved_controls"]})})
    game_nodes = json.loads((OUT / "game-all-initializer-graphs.json").read_text())
    classes = json.loads((OUT / "root-classification.json").read_text())
    extra = json.loads((OUT / "game-extra-callback-SEH-graphs.json").read_text())["graphs"]
    # Actual initial stores belong to CRT entry, not any table initializer.
    sentinel = [r for r in handlers[0x5AC3A0]["instructions"] if r["pc"] in (0x5AC3D8, 0x5AC3E2)]
    require(len(sentinel) == 2 and all(r["operands"].endswith("0xffffffff") for r in sentinel), "CRT entry sentinel stores changed")
    own_imports = game.imports
    require(own_imports[0x5BB660]["name"] == "__CxxFrameHandler", "Handler owning import differs")
    resolved_indirects = []
    # This is a narrow def/use fact within the complete decoded entry bodies.
    # It adds import requirements, never suppresses the original unresolved site.
    for name, entry, load_pc, call_pc, register, slot in [
            ("MFC42.DLL", 0x5F401EA0, 0x5F401EA1, 0x5F401EB5, "ebx", 0x5F49814C),
            ("MSVCP50.DLL", 0x7810A290, 0x7810A2ED, 0x7810A2F5, "esi", 0x78146194)]:
        original = json.loads((OUT / (name + ".provider.json")).read_text())
        rows = {r["pc"]: r for r in original["graphs"][str(entry)]["instructions"]}
        require(rows[load_pc]["mnemonic"] == "mov" and rows[load_pc]["operands"] == register + f", dword ptr [0x{slot:x}]" and
                rows[call_pc]["mnemonic"] == "call" and rows[call_pc]["operands"] == register, "Register IAT def/use changed")
        resolved_indirects.append({"module": name, "entry": entry, "load_pc": load_pc, "call_pc": call_pc,
                                   "register": register, "owning_IAT": slot, "symbol": modules[name].imports[slot],
                                   "claim": "Static exact load/CALL provenance; service implementation, loaded module and return are unobserved"})
    save(OUT / "register-import-and-SEH-requirements.json", {
        "resolved_register_IAT_sites": resolved_indirects,
        "unique_game_FS_sites": len({r["pc"] for q in classes["roots"] for r in q["FS_sites"]}),
        "all_reached_game_FS_offsets": [0],
        "game_SEH_roots": [{"slot": r["slot"], "entry": r["entry"], "FS_sites": r["FS_sites"],
                            "executable_literals": r["executable_literals"], "imports": r["imports"],
                            "unresolved_controls": r["unresolved_controls"]} for r in classes["roots"] if r["FS_sites"]],
        "representative_handlers": [
            {"entry": 0x5AED59, "EAX_metadata": 0x5D19A0, "tail": 0x5AC100, "owning_IAT": 0x5BB660,
             "metadata_initial": game.data(0x5D19A0, 32)},
            {"entry": 0x5B986B, "EAX_metadata": 0x5DC4B8, "tail": 0x5AC100, "owning_IAT": 0x5BB660,
             "metadata_initial": game.data(0x5DC4B8, 32)}],
        "required_contract": ["Guest-thread FS base and checked FS:[0] SEH head distinct from host FS/TEB.",
                              "Preserve entry head, guest registration frame, state changes, and exact restore order on normal returns.",
                              "Decode callback/unwind metadata and invoked handler/cleanup routes; normal local CFG closure is not exception closure.",
                              "Handle allocator null returns/throws and structured exception dispatch with original failure branches.",
                              "MSVCP _Lockit adds initialized shared critical-section lifetime, atomic state and actual Sleep loop; it is not a no-op."]})
    abi = {
        "notation": "S is the particular callee entry ESP, including its return address. ABI facts derive from exact instructions; symbolic expressions omit the staged provider's implementation rounding and are explanatory only.",
        "roots": [
            {"slot": 0x5E0154, "entry": 0x4B5910, "tail": 0x4B5920,
             "calls": [{"site": 0x4B5939, "target": 0x4B5860, "return_pc": 0x4B593E,
                        "ECX_this": 0x60B2C8, "callee_arguments_S_offsets": {"+4": "float word 0x41200000 (a0 = 10)", "+8": "float word 0x41F00000 (a1 = 30)", "+12": "float word 0x41200000 (a2 = 10)", "+16": "float word 0x43480000 (a3 = 200)"},
                        "return": {"pc": 0x4B590C, "pop_bytes": 16, "EAX": "ECX this", "nonvolatile": "ESI saved/restored; EBX/EDI/EBP untouched"}},
                       {"site": 0x4B58B8, "owning_IAT": 0x5BB5B0, "name": "_hypot", "return_pc": 0x4B58BE,
                        "abi": "cdecl; two double arguments, x87 ST0 return, no callee argument pop", "caller_ESP_before_CALL": "S-28", "provider_arguments": ["double conversion of a0", "double conversion of a1"]},
                       {"site": 0x4B58E3, "owning_IAT": 0x5BB5B0, "name": "_hypot", "return_pc": 0x4B58E9,
                        "abi": "cdecl; two double arguments, x87 ST0 return", "caller_ESP_before_CALL": "S-28", "provider_arguments": ["double conversion of a2", "double conversion of a3"]}],
             "ordered_object_stores": [{"pc": p, "offset": o, "width": 4, "symbolic_value": v} for p, o, v in [
                 (0x4B5892, 0, "a0"), (0x4B5896, 4, "a2"), (0x4B589F, 8, "a1"), (0x4B58AA, 12, "a3"),
                 (0x4B58AF, 16, "a3-a1"), (0x4B58B2, 20, "1/(a3-a1)"), (0x4B58DD, 24, "a1/hypot(a0,a1)"),
                 (0x4B5902, 28, "a3/hypot(a2,a3)"), (0x4B5905, 32, "second ratio minus stored first ratio")]],
             "FP_domain": "Depth reaches seven before transport; initially empty masked x87 would be a first gate domain. Generic nonempty/unmasked behavior remains required but unmeasured.",
             "flags": "Last integer flag writer ADD ESP,8 at 0x4B5909; arithmetic flags must use actual entry stack/address, not a fixed synthetic value. DF and other untouched flags persist.",
             "failure_routes": "No caller status branch: provider FP exceptions, overflow/underflow, errno/TLS/matherr/SEH and callback routes are real dependencies, not successful host hypot substitution."},
            {"slot": 0x5E016C, "entry": 0x4C19F0,
             "calls": [{"site": 0x4C19F3, "target": 0x4C1A00, "return_pc": 0x4C19F8},
                       {"site": 0x4C1A03, "owning_IAT": 0x5BB4FC, "return_pc": 0x4C1A09,
                        "abi": "No arguments; cdecl leaf FLD float returns x87 ST0, RET no argument pop"}],
             "provider": {"module": "MSVCP50.DLL", "ordinal": 1545, "import_hint_not_ordinal": 1544,
                          "entry": 0x780C10F0, "FLD_pc": 0x780C10F0, "RET_pc": 0x780C10F6,
                          "readonly_data": modules["MSVCP50.DLL"].data(0x78115004, 4), "provider_instructions": 2},
             "stores": [{"pc": 0x4C1A09, "address": 0x60B368, "width": 4, "source": "Actual returned x87 ST0; exact finite max-float if provider input storage is admitted"}] +
                       [{"pc": 0x4C1A0F + i*10, "address": 0x60B36C + i*4, "width": 4, "value": 0} for i in range(10)],
             "returns": [{"pc": 0x4C1A74, "pop_bytes": 0}, {"pc": 0x4C19F9, "pop_bytes": 0}],
             "flags": "All local/provider operations preserve integer flags; no invented fixed EAX result. Both EBP frames restore EBP. FSTP/status and dead raw storage require actual gate observations.",
             "finite_requirements": ["Exact owning game IAT, name/export/RX identity and real continuation 0x4C1A09.",
                                     "Pinned provider read-only constant or measured guest provider data mapping; never host-pointer cast.",
                                     "Actual State x87 push/pop/raw80/legacy metadata and permission/event checks at both FLD and FSTP.",
                                     "Existing runtime service_provider.hpp is MSVCRT-only; extend provider/library admission in a separately preserved/rebuilt gate or use a separately measured local provider leaf adapter.",
                                     "Original/native fullState/CPU/stack/global events, masked CW/TOP/dirty input and denied import/provider/data identities before shared integration."],
             "next_native_target": True},
            {"slot": 0x5E0178, "entry": 0x4C58C0, "normal_this": 0x60B3D0,
             "calls": [{"site": 0x4C58C0, "target": 0x4C58D0, "return_pc": 0x4C58C5},
                       {"site": 0x4C58E7, "target": 0x4C5960, "return_pc": 0x4C58EC, "ECX_this": 0x60B3D0,
                        "arguments": ["pointer 0", "pointer 0"], "null_pointer_substitute": 0x63D870,
                        "returns": [{"pc": 0x4C5A09, "pop_bytes": 8}, {"pc": 0x4C5A28, "pop_bytes": 8}]},
                       {"site": 0x4C59D4, "target": 0x4020D0, "return_pc": 0x4C59D9,
                        "abi": "ECX points to local three-float difference; no stack args; normalizes in place if magnitude nonzero and returns magnitude x87 ST0; RET 0x402131"},
                       {"site": 0x4C5935, "target": 0x5AC140, "return_pc": 0x4C593A,
                        "arguments": ["callback 0x4C5940"], "abi": "cdecl; caller ADD ESP,4; tail RET 0x4C593D"}],
             "branch": {"comparison": "FCOMP [0x5CAD6C] followed by FNSTSW AX and TEST AH,0x40", "site": 0x4C59E4,
                        "C3_zero_route": 0x4C5A0C, "C3_set_route": 0x4C59E6,
                        "caution": "C3 alone treats equality and unordered comparison together; do not replace with host ordered equality.",
                        "C3_set_stores": "Copy 12 initial bytes from 0x5EDA70 into this+16..+24",
                        "C3_zero_stores": "Store normalized difference Z to this+16, zero this+20, negative normalized X to this+24"},
             "object_vtable_writes": [{"pc": 0x4C596F, "value": 0x5CAD70}, {"pc": 0x4C58EC, "value": 0x5CACE0}],
             "cleanup_callback": {"entry": 0x4C5940, "guard_byte": 0x60B3CC, "guard_bit": 1,
                                  "already_set_RET": 0x4C595E, "first_time_set_pc": 0x4C594E,
                                  "ECX_this": 0x60B3D0, "tail": [0x4C5920, 0x4D0910],
                                  "last_vtable": 0x5BC868, "normal_imports": [],
                                  "not_reached_by_startup": "Registration stores callback; eventual dispatch remains a separate process-exit contract."},
             "registration_status": "5AC140 maps nonnull provider callback return to EAX=0 and null failure to EAX=-1; arithmetic flags remain observable. Constructor writes survive registration failure; no rollback branch exists.",
             "failure_routes": "Constructor null arguments use actual global vector storage; other invalid pointers fault. FP unmasked/NaN/stack conditions and registration growth/locking/allocation failure are not admitted."}
        ]}
    save(OUT / "three-root-ABI-plan.json", abi)
    plan = {
        "priority": [
            {"rank": 1, "root": 0x4C19F0, "reason": "21 game instructions plus exact two-instruction no-argument provider leaf; no allocator, FS, callback or nested provider import.", "requirements": abi["roots"][1]["finite_requirements"]},
            {"rank": 2, "root": 0x482CF0, "slot": 0x5E0110, "instructions": 22,
             "service": "USER32 SystemParametersInfoA", "owning_IAT": 0x5BB6DC, "CALL_pc": 0x482CDD, "return_pc": 0x482CE3,
             "this": 0x608F88, "copy": {"source": 0x5E6000, "bytes": 24, "REP_MOVSD_pc": 0x482CDB, "count": 6},
             "stdcall_arguments": ["uiAction numeric 0x30", "uiParam 0", "pvParam this+0x18 (16-byte output region)", "fWinIni 0"],
             "return": "Service callee pops16; BOOL is ignored; constructor returns EAX=this at RET0x482CE8",
             "requirements": ["Actual environment-dependent service output or clearly authored fixture, each labelled independently.", "Success/failure memory-write and preserve contract; failure has no caller guard or invented output defaults.", "DF-sensitive REP MOVSD, complete 40-byte object footprint, checked guest output pointer and real callback continuation.", "No ordinary game/UI launch is authorized by this static dossier."]},
            {"rank": 3, "group": "26 roots with _onexit/__dllonexit only and no FS/unresolved normal controls",
             "first_small_root": 0x4D9F60, "slot": 0x5E01C0, "startup_instructions": 32,
             "initial_store": {"pc": 0x4D9F70, "address": 0x60B5A0, "width": 4, "value": 0},
             "registration": {"CALL_pc": 0x4D9F85, "target": 0x5AC140, "return_pc": 0x4D9F8A, "callback": 0x4D9F90},
             "cleanup": {"guard": 0x60B59C, "pointer": 0x60B5A0, "free_CALL": 0x4D9FB0, "free_IAT": 0x5BB65C, "return_pc": 0x4D9FB6, "RET": 0x4D9FB9},
             "requirements": ["Restore actual CRT entry sentinel before initializers: 0x5AC3D8 writes 0x9A17EC=-1 and 0x5AC3E2 writes 0x9A17F0=-1.", "Exact _onexit callback registry ownership, provider globals/table capacity, lock and allocation lifetimes; current PE initial zero values are insufficient.", "Append order, repeated callback guards, reverse eventual cleanup order, checked nonnull guest free and no-rollback registration failure.", "Own successful capacity and growth/realloc-null branches separately, no fake nonnull registration.", "26-group closure is normal initializer CFG only; some other group's callbacks contain virtual destructors and additional services."]},
            {"rank": 4, "groups": "32 no-FS roots add MFC ordinal823; 17 no-FS roots add _strdup",
             "requirements": ["MFC ordinal823 actual staged entry0x5F401EA0 is allocation with malloc loaded through own IAT0x5F49814C and indirect CALL0x5F401EB5; it is not a guessed ordinal name or string constructor.", "Handle null/retry new-handler path0x5F41B01E, global/thread-local handler ownership, real callback stack and CxxThrow/SEH failure.", "MFC ordinal825 actual0x5F401782 forwards free; allocator/deallocator ownership must agree.", "_strdup actual0x78010A6D needs source termination/bounds, malloc result/copy, null allocation behavior and later guest-free ownership."]},
            {"rank": 5, "group": "31 FS roots (111 unique sites), overlapping import groups",
             "requirements": ["Guest FS:[0] normal chain, compiler metadata and unwind/handler closures before allocation exception tests.", "Four simpler lock/container roots add MSVCP _Lockit ctor/dtor; actual shared critical section/Sleep loop/atexit init must be implemented or remain unresolved.", "Six FS allocation/container roots and four FS allocation/free roots remain object-lifetime gates, not per-import stubs.", "Application object root0x47F760 still carries28 unresolved controls and24 imported names in its current direct closure; do not conflate it with the smaller groups."]},
            {"rank": 6, "root": 0x4B5910, "requirements": ["Full staged hypot numerical/control-word/errno/matherr/error contract and exception/TLS paths or explicitly measured narrow fixed-input gate.", "Do not use host std::hypot with assumed status/CW/return metadata equivalence.", "Branch tables and indirect service/callback targets recorded by the provider CFG remain open."]}],
        "CRT_registration_exact_ABI": {"wrapper": 0x5AC110, "sentinel_global": 0x9A17F0,
            "sentinel_minus_one_CALL": {"site": 0x5AC11E, "IAT": 0x5BB52C, "return_pc": 0x5AC124, "args": ["callback cdecl"]},
            "other_table_CALL": {"site": 0x5AC137, "tail": 0x5AC580, "IAT": 0x5BB530, "return_pc": 0x5AC13C,
                                 "args": ["callback", "address0x9A17F0 of table-begin", "address0x9A17EC of table-next"]},
            "_onexit_provider": {"entry": 0x78004A36, "append_pc": 0x78004A67, "next_increment_pc": 0x78004A69,
                                  "capacity_branch": 0x78004A5D, "growth_target": 0x7801E27B, "realloc_null_branch": 0x7801E295,
                                  "begin_global": 0x7803788C, "next_global": 0x78037888, "callback_return_EAX": "callback or0"},
            "__dllonexit_provider": {"entry": 0x78002FE5, "append_pc": 0x7800300C, "next_increment_pc": 0x7800300E,
                                     "capacity_branch": 0x78003004, "growth_target": 0x7800301D, "realloc_null_branch": 0x7800302B,
                                     "callback_return_EAX": "callback or0"}},
        "remaining_inventory": {"slots": 145, "nonzero_roots": 144, "import_free_normal_direct_roots": 26,
                                "import_dependent_roots": 117, "roots_with_unresolved_normal_controls": 17,
                                "FS_roots_overlap_not_additive": 31,
                                "one_zero_instruction_lookup_root": 0x4B64F0,
                                "note": "117 service roots +26 import-free roots +one undecoded root =144. Import/FS groups are workload buckets, not acceptance counts."}}
    save(OUT / "next-native-closure-plan.json", plan)
    report = {"schema_version": 1, "passed_static_recovery": True,
              "scope": "Exact static ABI/CFG and next service implementation plan; no execution, implementation, original equivalence, M4 startup or menu acceptance",
              "three_roots": [{"slot": r["slot"], "entry": r["entry"]} for r in abi["roots"]],
              "next_bounded_provider_candidate": 0x4C19F0,
              "fresh_decoder_inventory_matches": "363 local graph PC/byte sets; all145slots/144nonzero roots",
              "original_inputs_unchanged": True, "authored_CFG_controls": 11,
              "provider_closure_limits": "Complete directly decoded local instruction bodies/branches are preserved, with every known import and unresolved indirect site. Exact entry supplement repairs a missing linear boundary; indirect branch tables, handlers and loaded module initialization remain open.",
              "excluded_exploration": [0x5B1359, 0x5B386B],
              "checker_failures": ["An exploratory print used import record key pc instead of site and raised KeyError; no recovery artifact/source mutation resulted. Corrected formatting showed exact site fields."],
              "sources": [bind(Path(__file__)), bind(Path(__file__).with_name("recover.py"))],
              "artifacts": ["recovery.json", "three-FP-root-graphs.json", "three-root-ABI-plan.json", "next-native-closure-plan.json", "root-classification.json", "register-import-and-SEH-requirements.json", "aligned-entry-handler-provider-supplement.json"],
              "limits": ["No provider/DLL DllMain, original game, native worker or OS service was executed.",
                         "Only exact staged providers are resolved; the actual DLLs loaded by the working game remain unobserved.",
                         "No generic SEH exception, callback, indirect branch, allocator, libc numeric or Win32 success is inferred.",
                         "Scalar symbolic values are explanatory static def/use; full State/FP flags/events need new hardware/native gates.",
                         "Provider/global values are file-initial/zero-fill evidence only, except separately evidenced CRT entry sentinel writes."]}
    save(OUT / "report.json", report)
    for item in frozen:
        require(bind(item["path"]) == item, "Initial recovery evidence was changed")
    all_paths = {item["path"] for item in frozen}
    all_paths.update(str(p.resolve()) for p in OUT.iterdir() if p.is_file() and p.name != "pins.json")
    all_paths.update(str(p.resolve()) for p in (Path(__file__), Path(__file__).with_name("recover.py")))
    save(OUT / "pins.json", {"schema_version": 1, "bindings": [bind(p) for p in sorted(all_paths)],
         "association": "Every first recovery identity/artifact remains physical and unchanged; additive exact-handler and missing-boundary supplement supersedes explicitly excluded exploration only."})
    print(json.dumps({"passed_static_recovery": True, "report": bind(OUT / "report.json"), "pins": bind(OUT / "pins.json"), "bindings": len(all_paths)}))


if __name__ == "__main__":
    main()
