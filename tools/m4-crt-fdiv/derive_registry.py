"""Fresh private native registry inputs with literal provider caller binding."""
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-crt-control-integration'))
from prepare import PE


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(preparation, out):
    preparation, out = Path(preparation).resolve(), Path(out).resolve()
    assert preparation.parent == out.parent == ROOT / 'reports/m4-crt-fdiv' and not out.exists()
    report = json.loads((preparation / 'report.json').read_text())
    adapted = json.loads((preparation / 'adaptation.json').read_text())
    assert sha(preparation / 'host.ll') == adapted['host_sha256']
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = PE(provider, report['provider_sha256'], 0x78000000)
    pack = bytearray((preparation / 'pack.bin').read_bytes())
    assert sha(preparation / 'pack.bin') == report['pack_sha256']
    parent = pe.bytes(0x78004227, 45, True)
    assert parent[9:11] == bytes.fromhex('ffd0')
    page_index = next(i for i, p in enumerate(report['pages']) if p['address'] == 0x78004000)
    offset = 12 + page_index * 4104 + 8 + 0x227
    pack[offset:offset + len(parent)] = parent
    out.mkdir()
    (out / 'pack.bin').write_bytes(pack)
    (out / 'host.ll').write_bytes((preparation / 'host.ll').read_bytes())
    rows = report['source_ranges'] + [dict(address=0x78004227, size_bytes=45,
        file_offset=pe.offset(0x78004227, len(parent), True), sha256=hashlib.sha256(parent).hexdigest())]
    spec = ('#pragma once\n#include <array>\nnamespace mw34::m4_crt_fdiv {\n'
        f'inline constexpr char pack_sha[]="{sha(out / "pack.bin")}";\n'
        f'inline constexpr unsigned pack_bytes={len(pack)};\n'
        'struct SourceRange{unsigned address,bytes;const char*sha;};\n'
        'inline constexpr std::array<SourceRange,5> source_ranges{{' +
        ','.join('{%d,%d,"%s"}' % (r['address'], r['size_bytes'], r['sha256']) for r in rows) + '}};\n}\n')
    (out / 'spec.hpp').write_text(spec)
    result = dict(passed=True, scope='Literal source derivative and native-only admitted dependency inputs',
        preparation=str(preparation), preparation_sha256=sha(preparation / 'report.json'),
        adaptation_sha256=sha(preparation / 'adaptation.json'), parent_call=0x78004230,
        parent_return=0x78004232, parent_execution=False, source_ranges=rows,
        pack_sha256=sha(out / 'pack.bin'), pack_bytes=len(pack), host_sha256=sha(out / 'host.ll'),
        source_sha256=sha(__file__), provider_sha256=report['provider_sha256'], whole_M4_complete=False)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main(*sys.argv[1:])
