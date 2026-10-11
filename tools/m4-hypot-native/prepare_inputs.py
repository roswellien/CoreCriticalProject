"""Seed six finite native cases from genuine BEFORE-only input storage."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / 'reports/m4-hypot-original'


def main(name):
    out = ROOT / 'reports/m4-hypot-native' / name
    assert re.fullmatch('inputs-r[1-9][0-9]*',name) and not out.exists()
    out.mkdir(parents=True)
    pins, rows, capture = {}, [], None

    def pin(path, expected=None):
        path = Path(path).resolve()
        with path.open('rb') as stream:
            identity = hashlib.file_digest(stream,'sha256').hexdigest()
        assert expected is None or identity == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == identity
        pins[str(path)] = identity
        return path

    def read(path, expected=None):
        return json.loads(pin(path,expected).read_text(encoding='utf-8-sig'))

    def module(path,label):
        spec = importlib.util.spec_from_file_location(label,pin(path))
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value

    try:
        original = read(ORIGINAL/'prefix-validation-r2/report.json',
            '80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313')
        assert original['passed'] and original['reader_closed']
        execution = read(original['execution_path'],original['execution_sha256'])
        assert execution['passed']
        build = read(execution['build_path'],execution['build_sha256'])
        preparation = Path(build['preparation'])
        prep = read(preparation/'report.json',build['preparation_sha256'])
        assert prep['record_bytes'] == 356992 and len(prep['observed_pages']) == 43
        pack = pin(preparation/'pages.bin',prep['pack_sha256']).read_bytes()
        assert pack[:8] == b'MW4J124P'
        count = struct.unpack_from('<I',pack,8)[0]
        assert len(pack) == 12+count*4104
        packed = {}
        for i in range(count):
            offset = 12+i*4104
            page,permission = struct.unpack_from('<2I',pack,offset)
            assert page not in packed and permission in (0,1,2)
            packed[page] = (permission,pack[offset+8:offset+4104])
        preflight = read(ORIGINAL/'root-preflight-r2/report.json',
            'cc9f62f16ce9b945d9d8b0a0038d07c93aa944d1f5f4841831c2a804cb414680')
        assert preflight['passed'] and preflight['worker_sha256'] == build['worker_sha256']
        observers = read(ORIGINAL/'root-preflight-r2/linked-observers.json')['functions']
        entry_observer = next(r['address'] for r in observers if r['kind']==0)
        PE = module(ROOT/'tools/analysis/pe.py','hypot_input_PE')
        CRT = PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
            '2ef1668832203026a9796fda9415a5955b9d917e6d42ea0b9a76e33cd9c28f41').read_bytes())
        direct = module(ROOT/'tools/m4-crt-allocation-root/run_v2.py','hypot_input_capture')
        capture = direct.DirectSet(Path(execution['original_capture']),pin)
        identity = struct.unpack('<4I',capture.data('hypot/identity.bin'))
        assert identity[:2] == (0x5bb5b0,0x7802a122) and identity[3] == 0x78000000
        seeds = bytearray()
        mapping = None
        for sequence in range(6):
            data = capture.data(f'phase/{sequence}/0.bin')
            assert len(data)==356992
            header = struct.unpack_from('<9I',data)
            assert header[0]==sequence and header[3:5]==(0x5e0154,0x4b5910) and header[7:]==(0,1)
            # These are precisely the ordinary root BEFORE fields, never the
            # original output state, cdecl results or later page images.
            seed = data[36:76]+data[116:628]+data[2164:2192]
            assert len(seed)==580
            seeds += seed
            pages = dict(packed)
            for i,page in enumerate(prep['observed_pages']):
                assert page in pages
                pages[page] = (pages[page][0],data[2276+i*4096:2276+(i+1)*4096])
            for i in range(64):
                page = 0x78000000+i*4096
                raw = capture.data(f'phase/{sequence}/0/hypot-CRT-before/{page}.bin')
                assert len(raw)==4096
                rva = page-CRT.image_base
                sections = [s for s in CRT.sections if s['virtual_address'] <= rva <
                            s['virtual_address']+max(s['raw_size'],s['virtual_size'])]
                assert len(sections)<=1
                permission = (2 if sections and sections[0]['writable'] else
                              1 if sections and sections[0]['executable'] else 0)
                pages[page] = (permission,raw)
            # The ordinary capture names the observer at this one game IAT
            # cell. Reconstruct its actual named provider identity from the
            # independently authenticated worker/export, never an AFTER page.
            permission,raw = pages[0x5bb000]
            assert struct.unpack_from('<I',raw,0x5b0)[0] == entry_observer
            repaired = bytearray(raw)
            struct.pack_into('<I',repaired,0x5b0,identity[1])
            assert all(raw[i]==repaired[i] for i in range(4096) if i not in range(0x5b0,0x5b4))
            pages[0x5bb000] = (permission,bytes(repaired))
            source = read(ORIGINAL/'recovery-r1/game-graphs.json')
            for graph in source.values():
                for row in graph['instructions']:
                    page = row['pc'] & ~4095
                    at = row['pc'] & 4095
                    assert pages[page][1][at:at+row['size']] == bytes.fromhex(row['bytes'])
            current = [(p,k) for p,(k,_) in sorted(pages.items())]
            assert mapping is None or current==mapping
            mapping = current
            blob = b'MW4J124P'+struct.pack('<I',len(pages))+b''.join(
                struct.pack('<2I',p,k)+raw for p,(k,raw) in sorted(pages.items()))
            path = out/f'input-{sequence}.bin'
            path.write_bytes(blob)
            pin(path)
            rows.append(dict(sequence=sequence,pack=str(path),pack_sha256=pins[str(path.resolve())],
                CPU_FX_ENV_BEFORE_sha256=hashlib.sha256(seed).hexdigest(),
                reconstructed_IAT=dict(slot=identity[0],observed_value=entry_observer,
                    actual_named_provider=identity[1],bytes=4),
                memory_pages=len(pages),input_source='Actual root BEFORE and CRT root BEFORE, plus physical game source pack'))
        path = out/'input-state.bin'
        path.write_bytes(seeds)
        pin(path)
        (out/'input-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
        pin(out/'input-mapping.json')
        capture.close()
        capture.entries.clear()
        capture.bundles.clear()
        capture = None
        for path in (Path(__file__),Path(sys.executable)):
            pin(path)
        report = dict(passed=True,scope='Genuine six-case root BEFORE-only native fixture input preparation',
            original_validation_sha256='80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313',
            cases=rows,state_input_bytes=len(seeds),memory_pages_per_case=len(mapping),
            original_AFTER_bytes_seeded=0,numerical_results_seeded=False,
            literal_argument_cells_from_source_only=True,
            explicit_named_IAT_instrumentation_reconstruction=True,
            reader_closed=True,native_executed=False,initializer_credit=0,files=pins)
        path = out/'report.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        pin(path)
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=True,sha256=pins[str(path.resolve())],cases=len(rows),pages=len(mapping))))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        if capture is not None:
            capture.close()


if __name__ == '__main__':
    main(sys.argv[1])
