"""Prepare a local research copy of MW3 that runs on the CD's 1998 runtime (original/native comparisons).

MSVCRT is a KnownDLL on current Windows, so the installed Mech3.exe always binds System32 msvcrt.dll, while the
native host runs the CD's 1998 MSVCRT/MFC42/MSVCP50. This copy binds the same 1998 DLLs as the native host:
- MSVCRZ.dll is the CD's MSVCRT.DLL, byte for byte, under a name Windows does not redirect;
- Mech3.exe, Mech3Msg.dll and the CD's MFC42.DLL/MSVCP50.DLL import "MSVCRZ.dll" instead of "MSVCRT.dll".
  Each patch replaces exactly the import descriptor name string; every other byte is checked identical;
- the CD's MFC42.DLL/MSVCP50.DLL/IFORCE2.dll sit next to the executable (application directory precedes System32);
- dgVoodoo (DDraw.dll, D3DImm.dll, dgVoodoo.conf) is copied; pilots/ and configs/ are copied (the user's saves are
  never written); zbd/ (read-only game data) is a directory junction.
The installed game is not modified. Output is local research data (git-ignored).
Usage: python -I prepare_runtime.py OUT_DIR
"""
import hashlib, shutil, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'MW3'
STAGED = ROOT / 'local/mw3-staged/Shared_DLLs'
ADMITTED_GAME = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
OLD, NEW = b'MSVCRT.dll', b'MSVCRZ.dll'


def need(ok, what):
    if not ok:
        raise SystemExit('prepare_runtime: ' + what)


def rva_to_offset(data, rva):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    opt = struct.unpack_from('<H', data, pe + 20)[0]
    for i in range(count):
        vsize, va, rsize, rptr = struct.unpack_from('<IIII', data, pe + 24 + opt + 40 * i + 8)
        if va <= rva < va + max(vsize, rsize):
            return rptr + rva - va
    raise SystemExit('prepare_runtime: RVA outside sections')


def patch_import(data):
    """Rename the MSVCRT import descriptor's DLL name; returns (patched bytes, patched offset)."""
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    need(struct.unpack_from('<H', data, pe + 24)[0] == 0x10b, 'PE32 image required')
    imp_rva, imp_size = struct.unpack_from('<II', data, pe + 24 + 104)
    out = bytearray(data)
    hits = []
    at = rva_to_offset(data, imp_rva)
    while True:
        desc = struct.unpack_from('<IIIII', data, at)
        if not any(desc):
            break
        name = rva_to_offset(data, desc[3])
        end = data.index(b'\0', name)
        if data[name:end].lower() == OLD.lower():
            need(end - name == len(NEW), 'MSVCRT import name length')
            out[name:end] = NEW
            hits.append(name)
        at += 20
    need(len(hits) == 1, 'exactly one MSVCRT import descriptor')
    diff = [i for i in range(len(data)) if data[i] != out[i]]
    need(diff and min(diff) >= hits[0] and max(diff) < hits[0] + len(NEW), 'only the import name changed')
    return bytes(out), hits[0]


def main(out_dir):
    out = Path(out_dir).resolve()
    need(not out.exists(), 'fresh output directory required')
    game = (GAME / 'Mech3.exe').read_bytes()
    need(hashlib.sha256(game).hexdigest() == ADMITTED_GAME, 'admitted Mech3.exe required')
    out.mkdir(parents=True)
    record = {}
    for src in (GAME / 'Mech3.exe', GAME / 'Mech3Msg.dll', STAGED / 'MFC42.DLL', STAGED / 'MSVCP50.DLL'):
        data = src.read_bytes()
        patched, at = patch_import(data)
        (out / src.name).write_bytes(patched)
        record[src.name] = {'source_sha256': hashlib.sha256(data).hexdigest(),
                            'patched_sha256': hashlib.sha256(patched).hexdigest(), 'name_offset': at}
    shutil.copyfile(STAGED / 'MSVCRT.DLL', out / 'MSVCRZ.dll')
    shutil.copyfile(STAGED / 'IFORCE2.dll', out / 'IFORCE2.dll')
    for name in ('DDraw.dll', 'D3DImm.dll', 'dgVoodoo.conf', 'force_eff.ifr'):
        shutil.copyfile(GAME / name, out / name)
    for name in ('pilots', 'configs'):
        shutil.copytree(GAME / name, out / name)
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(out / 'zbd'), str(GAME / 'zbd')], check=True, capture_output=True)
    for name, info in record.items():
        print(name, info['source_sha256'][:16], '->', info['patched_sha256'][:16], 'name at', hex(info['name_offset']))
    print('runtime:', hashlib.sha256((out / 'MSVCRZ.dll').read_bytes()).hexdigest()[:16], '(CD MSVCRT.DLL)')


if __name__ == '__main__':
    main(*sys.argv[1:])
