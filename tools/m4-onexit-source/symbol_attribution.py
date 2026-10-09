"""Additive physical COFF symbol attribution; never rewrites sealed lifts."""
from pathlib import Path
import hashlib, json, re, struct, subprocess, sys, time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
LIFTS = ROOT / 'reports/m4-onexit-source/lifts-r4'
LIFTS_SHA = '03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v, s):
    if not v: raise ValueError(s)

def coff_definition(p, symbol):
    data = Path(p).read_bytes()
    machine, sections, _, symoff, count, opts, _ = struct.unpack_from('<HHIIIHH', data)
    need(machine == 0x8664 and opts == 0, 'Physical AMD64 COFF required')
    stringoff = symoff + count * 18
    stringlen = struct.unpack_from('<I', data, stringoff)[0]
    need(stringoff + stringlen <= len(data), 'Bounded COFF strings')
    results = []; i = 0
    while i < count:
        off = symoff + i * 18
        namebytes, value, section, typ, storage, aux = struct.unpack_from('<8sIhHBB', data, off)
        if namebytes[:4] == b'\0' * 4:
            pos = stringoff + struct.unpack_from('<I', namebytes, 4)[0]
            need(stringoff + 4 <= pos < stringoff + stringlen, 'COFF symbol string offset')
            name = data[pos:data.index(b'\0', pos, stringoff + stringlen)].decode('ascii')
        else: name = namebytes.rstrip(b'\0').decode('ascii')
        if name == symbol:
            need(0 < section <= sections and storage == 2 and typ == 0x20, 'External function definition')
            sectionoff = 20 + (section - 1) * 40
            sectionname = data[sectionoff:sectionoff + 8].rstrip(b'\0').decode('ascii')
            chars = struct.unpack_from('<I', data, sectionoff + 36)[0]
            need(chars & 0x20000000, 'COFF defining section executable')
            results.append(dict(symbol=name, section=section, section_name=sectionname,
                                value=value, type=typ, storage_class=storage, section_characteristics=chars))
        i += 1 + aux
    need(len(results) == 1, 'Exactly one physical body definition')
    return dict(machine=machine, **results[0])

def main():
    out = ROOT / 'reports/m4-onexit-source' / sys.argv[1]
    need(re.fullmatch(r'symbol-attribution-r[1-9][0-9]*', out.name) and not out.exists(), 'Fresh additive output')
    need(sha(LIFTS / 'report.json') == LIFTS_SHA, 'Sealed lift report identity')
    d = json.loads((LIFTS / 'report.json').read_bytes()); need(d['passed'], 'Sealed passing lifts')
    out.mkdir(parents=True); pins = {}; mapping = []; objects = []
    def pin(p, expected=None):
        p = Path(p).resolve(); h = sha(p); need(expected is None or h == expected, 'Frozen artifact identity ' + str(p)); pins[str(p)] = h; return p
    pin(LIFTS / 'report.json', LIFTS_SHA)
    for item in d['dispatch_manifest']:
        component = 'f_' + format(item['entry'], 'x'); source = d['source_bodies'][component]
        host = pin(LIFTS / (component + '-host.ll'), source['host_sha256'])
        definitions = re.findall(r'^define\b[^\n]*@([A-Za-z0-9_.$]+)\(', host.read_text(), re.M)
        expected = 'mw34_onexit_game_' + component + '_body'
        need(definitions.count(expected) == 1, 'Literal LLVM body definition for entry')
        row = dict(entry=item['entry'], sealed_manifest_symbol=item['symbol'], source_function_symbol=expected,
                   metadata_correction_only=True, host_LL=str(host), host_sha256=sha(host), objects={})
        for level in ('O0', 'O2'):
            obj = pin(item['objects'][level]['path'], item['objects'][level]['sha256'])
            physical = coff_definition(obj, expected)
            row['objects'][level] = dict(path=str(obj), sha256=sha(obj), **physical)
            objects.append((obj, expected))
        mapping.append(row)
    need(len(mapping) == 64 and len(objects) == 128, 'All sealed game/sentinel bodies and COFFs')
    nm = pin(ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-nm.exe')
    argv = [str(nm), '--format=posix', '--print-file-name', '--defined-only', *[str(p) for p, _ in objects]]
    started = time.perf_counter(); result = subprocess.run(argv, capture_output=True, timeout=30, creationflags=0x08000000)
    (out / 'physical-defined-symbols.txt').write_bytes(result.stdout)
    (out / 'nm.stderr').write_bytes(result.stderr)
    need(result.returncode == 0, 'One batched physical llvm-nm enumeration')
    lines = result.stdout.decode('utf-8').splitlines()
    for p, symbol in objects:
        prefix = str(p) + ': ' + symbol + ' T '
        need(sum(line.startswith(prefix) for line in lines) == 1, 'llvm-nm agrees with independent physical COFF parser')
    header = '#pragma once\n// Additive physical-symbol mapping; original lifts-r4 manifest remains sealed.\n'
    header += '\n'.join('extern "C" void* ' + row['source_function_symbol'] + '(void*, unsigned long long, void*);' for row in mapping) + '\n'
    (out / 'physical-dispatch-declarations.hpp').write_text(header)
    (out / 'physical-dispatch.json').write_text(json.dumps(mapping, indent=2) + '\n')
    pin(Path(__file__).resolve()); pin(Path(sys.executable))
    for p in out.iterdir():
        if p.is_file(): pin(p)
    report = dict(passed=True, scope='Additive source-LLVM and physical AMD64 COFF symbol attribution only',
                  sealed_lifts_report_sha256=LIFTS_SHA, body_count=len(mapping), physical_COFF_count=len(objects),
                  metadata_suffix='_body', corrected_manifest_entries=len(mapping),
                  independent_COFF_parser=True, batched_llvm_nm=True,
                  command=dict(argv=argv, exit_code=result.returncode, seconds=time.perf_counter() - started),
                  mapping_file='physical-dispatch.json', declaration_header='physical-dispatch-declarations.hpp',
                  source_COFF_recompiled=False, sealed_sources_modified=False, native_execution=False,
                  initializer_credit=False, files=pins)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n'); pin(out / 'report.json')
    (out / 'pins.json').write_text(json.dumps(dict(files=pins), indent=2) + '\n')
    print(json.dumps(dict(passed=True, bodies=64, objects=128, report_sha256=sha(out / 'report.json'))))

if __name__ == '__main__': main()
