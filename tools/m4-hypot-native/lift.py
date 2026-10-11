"""Physically pinned hypot game/normal-provider source, native preparation only."""
from pathlib import Path
import collections
import ctypes as c
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / 'reports/m4-hypot-original/recovery-r1'
REC_SHA = 'eac482b63a16938e9f931f34baa294e59aa8c216b861528426c24a988079eb77'
HELPER_SHA = '95a491304f80a654ca82d20b0e68a6fcfe476c1b8cda5f6e5bb97c307828fcb4'
CRT_ENTRIES = (0x7802a122, 0x7802a15c, 0x7802d278, 0x78029241,
               0x7802d19a, 0x7802d12c, 0x7802d103,
               0x7802c2fa, 0x7802c2ca, 0x7802c2e1)
# These are actual backward jump destinations in the sqrt graph. They are
# separate literal machine fragments, not independently callable ABI helpers.
TAIL_ENTRIES = (0x78028969, 0x78029110, 0x7802c353)


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = ROOT / 'reports/m4-hypot-native' / name
    need(re.fullmatch('lifts-r[1-9][0-9]*', name) and not out.exists(), 'Fresh lift output')
    out.mkdir(parents=True)
    pins, commands, bodies, physical = {}, [], {}, {}
    started = time.perf_counter()

    def pin(path, expected=None):
        path = Path(path).resolve()
        need(path.suffix.lower() not in ('.mwb', '.zip'), 'No capture reader in source preparation')
        identity = sha(path)
        need(expected is None or identity == expected, 'Physical input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == identity, 'Conflicting physical identity')
        pins[str(path)] = identity
        return path

    def module(path, label, expected=None):
        spec = importlib.util.spec_from_file_location(label, pin(path, expected))
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def run(program, args, label):
        argv = [str(program), *map(str, args)]
        begin = time.perf_counter()
        result = subprocess.run(argv, capture_output=True, timeout=120,
                                creationflags=0x08000000)
        (out / (label + '.stdout')).write_bytes(result.stdout)
        (out / (label + '.stderr')).write_bytes(result.stderr)
        commands.append(dict(argv=argv, exit_code=result.returncode,
                             seconds=time.perf_counter()-begin))
        need(result.returncode == 0, 'Source tool ' + label)
        return result.stdout

    try:
        recovery = read(REC / 'report.json', REC_SHA)
        need(recovery['passed'] is True, 'Passed physical source recovery')
        for path, digest in recovery['files'].items():
            pin(path, digest)
        game_graphs = read(REC / 'game-graphs.json')
        crt_graphs = read(REC / 'CRT-provider-graphs.json')
        PE = module(ROOT / 'tools/analysis/pe.py', 'hypot_native_PE')
        identities = module(ROOT / 'tools/m4-service-initializers/recover.py',
                            'hypot_native_identities').IDENTITIES
        images = dict(game=PE.PEImage(pin(ROOT / 'MW3/Mech3.exe',
                          identities['MW3/Mech3.exe']).read_bytes()),
                      crt=PE.PEImage(pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
                          identities['local/mw3-staged/Shared_DLLs/MSVCRT.DLL']).read_bytes()))
        selected = [(key, g, 'game', False) for key,g in game_graphs.items()]
        selected += [(str(e), crt_graphs[str(e)], 'crt', False) for e in CRT_ENTRIES]
        sqrt_rows = {r['pc']:r for r in crt_graphs[str(0x78029241)]['instructions']}
        for entry in TAIL_ENTRIES:
            rows, pc = [], entry
            while pc in sqrt_rows:
                row = sqrt_rows[pc]
                rows.append(row)
                pc += row['size']
                if row['mnemonic'] in ('ret','jmp'):
                    break
            need(rows and rows[-1]['mnemonic'] in ('ret','jmp'), 'Whole physical tail fragment')
            selected.append((str(entry), dict(entry=entry, instructions=rows,
                                              unresolved_controls=[]), 'crt', True))

        helper = module(ROOT / 'tools/m4-widget-source/lift.py',
                        'hypot_native_FP_helpers', HELPER_SHA)
        llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
        lifter = pin(ROOT / 'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')
        sem = pin(ROOT / 'local/tools/remill-x87-control-repair/semantics/x86.bc',
                  '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
        dll = pin(llvm / 'LLVM-C.dll',
                  '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
        lower_path = pin(ROOT / 'tools/m4-crt-mainargs-recovery/recover.py')
        text = lower_path.read_text()
        body = text[text.index('def lower('):text.index("if __name__ == '__main__':")]
        body = body.replace('mw34_mainargs_', 'mw34_hypot_')
        before = "and '__remill_missing_block' not in text"
        need(body.count(before) == 1, 'One explicit incomplete graph scope')
        body = body.replace(before, '')
        before = "need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32')"
        need(body.count(before) == 1, 'One intrinsic admission list')
        body = body.replace(before, "need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32','llvm.fabs.f80','llvm.fabs.f32','llvm.fabs.f64','llvm.memcpy.p0.p0.i32','llvm.memmove.p0.p0.i32','llvm.lifetime.start.p0','llvm.lifetime.end.p0') or n.startswith('llvm.experimental.constrained.')")
        before = "need(api.IsAFunction(api.GetCalledValue(inst)),'Only named LLVM calls')"
        need(body.count(before) == 1, 'One exact FP ordering barrier scope')
        body = body.replace(before, "\n                    if not api.IsAFunction(api.GetCalledValue(inst)):\n                        need('call void asm sideeffect \\\"\\\", \\\"~{memory},~{dirflag},~{fpsr},~{flags}\\\"()' in api.text(inst),'Only exact original empty FP ordering barrier');continue")
        bridges = set(helper.BRIDGES) | {'__remill_read_memory_f80',
                     '__remill_write_memory_f80', '__remill_sync_hyper_call',
                     '__remill_async_hyper_call'}
        bridges.discard('mw34_onexit_game_fsqrt_raw80')
        bridges.add('mw34_hypot_fsqrt_raw80')
        rename = {s:'mw34_hypot_' + s.removeprefix('__remill_') for s in bridges
                  if s.startswith('__remill_')}
        before = 'bridges.add(n)\n        api.SetFunctionCallConv'
        need(body.count(before) == 1, 'One namespace boundary')
        body = body.replace(before, "bridges.add(n)\n            renamed=(RENAME.get(n) or ('mw34_hypot_direct_'+direct[1] if direct else n)).encode()\n            if renamed.decode()!=n:\n                api.dll.LLVMSetValueName2(fn,renamed,len(renamed));bridges.remove(n);bridges.add(renamed.decode())\n        api.SetFunctionCallConv")
        namespace = dict(c=c,re=re,sha=sha,LLVM=helper.FPTypes,
                         HOST_LAYOUT=helper.HOST_LAYOUT,FUNCTION_INDEX=helper.FUNCTION_INDEX,
                         checked_state_offsets=helper.checked_state_offsets,
                         need=need,BRIDGES=bridges,RENAME=rename)
        exec(compile(body, str(lower_path), 'exec'), namespace)
        (out / 'host-lowering.py').write_text(body)
        upstream = pin(ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()

        for key,graph,owner,fragment in selected:
            entry = int(key)
            component = f'f_{entry:x}'
            rows = graph['instructions']
            included = [r for r in rows if r['pc'] >= entry]
            end = max(r['pc'] + r['size'] for r in included)
            code = bytearray(b'\xcc' * (end-entry))
            assigned = set()
            for row in included:
                raw = bytes.fromhex(row['bytes'])
                image = images[owner]
                offset,_ = image.rva_range(row['pc']-image.image_base,len(raw))
                need(image.data[offset:offset+len(raw)] == raw, 'Every literal instruction')
                for at,byte in enumerate(raw, row['pc']):
                    need(at not in assigned, 'No overlapping instruction decode')
                    assigned.add(at)
                    need(at not in physical or physical[at] == byte, 'Shared byte identity')
                    physical[at] = byte
                code[row['pc']-entry:row['pc']-entry+len(raw)] = raw
            (out / (component+'-source.bin')).write_bytes(code)
            flags = out / (component+'-lift.flags')
            flags.write_text('\n'.join(['--arch=x86','--os=windows',
                '--address='+str(entry),'--entry_address='+str(entry),'--bytes='+code.hex(),
                '--semantics_dir='+str(sem.parent),
                '--ir_out='+str(out/(component+'-guest.ll'))])+'\n')
            run(lifter, ['--flagfile='+str(flags)], component+'-lift')
            guest = out / (component+'-guest.ll')
            original = guest.read_text()
            (out / (component+'-baseline.ll')).write_text(original)
            calls = [dict(kind='direct',target=int(a,16)) for a in
                     re.findall(r'^declare ptr @sub_([0-9a-f]+)',original,re.M)]
            strict, counts = helper.strict_fp(original)
            strict = strict.replace('mw34_onexit_game_fsqrt_raw80','mw34_hypot_fsqrt_raw80')
            guest.write_text(strict)
            compiled = namespace['lower'](out,component,dict(entry=entry,outgoing_calls=calls),
                                          dll,upstream,run,llvm)
            compiled.update(entry=entry,owner=owner,machine_fragment=fragment,
                physical_instructions=included,
                lower_address_rows_deferred=[r for r in rows if r['pc']<entry],
                source_span_bytes=len(code),physical_bytes=len(assigned),
                direct_source_targets=calls,strict_FP=counts,
                unresolved_controls=graph.get('unresolved_controls',[]),
                missing_block_retained='__remill_missing_block' in original,
                initializer_credit=0)
            bodies[component] = compiled
            print(json.dumps(dict(entry=hex(entry),objects=2,physical_bytes=len(assigned))),flush=True)

        for path in (Path(__file__), Path(sys.executable), ROOT/'tools/lifting/host_adapter.py',
                     llvm/'clang.exe',llvm/'llvm-nm.exe'):
            pin(path)
        for path in out.iterdir():
            if path.is_file():
                pin(path)
        report = dict(passed=True,scope='Hypot literal game/provider x64 COFF preparation; execution and cold branch admission remain separate',
            root=0x4b5910,slot=0x5e0154,recovery_sha256=REC_SHA,
            bodies=bodies,counts=dict(source_bodies=len(bodies),objects=2*len(bodies),
                                     unique_physical_instruction_bytes=len(physical)),
            State_bytes=3504,CPU_bytes=40,FX_bytes=512,
            host_pointer_replaces_guest_address=False,source_after_seed=False,
            numerical_expected_seed=False,source_dynamic_path_proven=False,
            native_executed=False,original_executed=False,initializer_credit=0,
            complete_provider_closure=False,commands=commands,files=pins,
            seconds=time.perf_counter()-started)
        path = out/'report.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        pin(path)
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=True,sha256=sha(path),counts=report['counts'])))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main(sys.argv[1])
