"""Compare actual compiled compound-FCOS outputs to genuine original endpoints."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, counts, observations = {}, collections.Counter(), []
    bundle = None
    passed = False

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or expected == value, path
        pins[str(path)] = value
        return path

    def eq(a, b, context):
        if a != b:
            if isinstance(a, bytes) and isinstance(b, bytes):
                difference = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
                raise ValueError((context, len(a), len(b), difference,
                                  a[max(0, (difference or 0) - 4):(difference or 0) + 8].hex(),
                                  b[max(0, (difference or 0) - 4):(difference or 0) + 8].hex()))
            raise ValueError((context, a, b))

    try:
        build = json.loads(pin(AREA / 'fixture-build-r1/report.json',
            '91c873f5e740c7ac87ae501f234b87b2815093e88e9a752262ae372dcdfeb6a1').read_bytes())
        assert build['passed'] and build['native_executed'] and not build['source_after_seed']
        for path, digest in build['files'].items():
            pin(path, digest)
        original = json.loads(pin(ROOT / 'reports/m4-cosine-original/prefix-validation-r2/report.json',
            'cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e').read_bytes())
        assert original['passed'] and not original['source_after_seed']
        execution = json.loads(pin(original['execution_path'], original['execution_sha256']).read_bytes())
        prep = json.loads(pin(build['preparation'], build['preparation_sha256']).read_bytes())
        pages = prep['observed_pages']
        assert len(pages) == 43
        spec = importlib.util.spec_from_file_location('compound_compare_direct',
            pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py'))
        direct = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(direct)
        bundle = direct.DirectSet(Path(execution['original_capture']), pin)
        for level in ('O0', 'O2'):
            output = build['outputs'][level]
            raw = pin(output['path'], output['sha256']).read_bytes()
            eq(raw[:8], b'MW4COS03', 'actual native output identity')
            eq(struct.unpack_from('<6I', raw, 8), (1, 6, 361836, 3504, 43, 4096), 'fixed native record ABI')
            eq(len(raw), 32 + 6 * 361836, 'complete physical native output')
            for sequence in range(6):
                n = raw[32 + sequence * 361836:32 + (sequence + 1) * 361836]
                o = bundle.data(f'phase/{sequence}/0.bin')
                assert len(o) == 356992
                tag = struct.unpack_from('<9I', o)
                eq(struct.unpack_from('<5I', n), (sequence, 0x4b64f0, tag[5], tag[6], 0), 'actual matching CW/TOP and positive completion')
                eq(n[20:60], o[36:76], 'whole genuine BEFORE CPU40')
                nc, oc = list(struct.unpack_from('<10I', n, 60)), list(struct.unpack_from('<10I', o, 76))
                # Only XOR AF is undefined. Every other complete CPU bit must agree.
                nc[8] &= ~0x10
                oc[8] &= ~0x10
                eq(nc, oc, 'whole original/native CPU40 relation with explicit XOR AF definedness')
                counts['complete_CPU_endpoint_relations'] += 2
                for nbase, obase, side in ((7108, 116, 'before'), (7620, 628, 'after')):
                    nf, of = n[nbase:nbase + 512], o[obase:obase + 512]
                    # The native format stores source x87 pointers, while actual
                    # x86 FXSAVE leaves 6:24 zero; legacy ENV carries those exact
                    # source pointers and selectors and is checked in full below.
                    eq(nf[:5], of[:5], side + ' actual CW/SW/empty abridged tag')
                    eq(nf[24:32], of[24:32], side + ' complete MXCSR/mask')
                    eq(nf[160:], of[160:], side + ' complete SSE and opaque tail')
                    for register in range(8):
                        begin = 32 + register * 16
                        eq(nf[begin:begin + 10], of[begin:begin + 10], side + ' actual latent raw80 register ' + str(register))
                        counts['raw80_register_relations'] += 1
                    counts['FX512_architectural_relations'] += 1
                eq(n[8132:8160], o[2164:2192], 'complete BEFORE ENV28')
                eq(n[8160:8188], o[2192:2220], 'complete AFTER ENV28 source attribution')
                counts['complete_ENV28_relations'] += 2
                for i, page in enumerate(pages):
                    eq(n[9268 + i * 4096:9268 + (i + 1) * 4096],
                       o[2276 + i * 4096:2276 + (i + 1) * 4096], 'complete BEFORE input page ' + hex(page))
                    eq(n[185396 + i * 4096:185396 + (i + 1) * 4096],
                       o[178404 + i * 4096:178404 + (i + 1) * 4096], 'complete original/native AFTER page ' + hex(page))
                    counts['whole_43page_endpoint_relations'] += 2
                counters = struct.unpack_from('<8I', n, 361524)
                eq(counters, (14, 4, 10, 6, 6, 1, 1, 3), 'literal access/primitive/host completion counts')
                events = [struct.unpack_from('<IQII', n, 361556 + i * 20) for i in range(14)]
                eq([row[0] for row in events], [0x5c93d0, 0x5e886c, 0x5e8870, 0x5e8874, 0x5e8878,
                    0x5e887c, 0x5e888c, 0x5e8890, 0x5e8880, 0x5c93d8, 0x5e8884, 0x5c93e0,
                    0x5e8888, 0x20001800], 'exact literal memory-access order')
                outputs = []
                for event in (events[8], events[10], events[12]):
                    assert event[2:] == (4, 1)
                    outputs.append(dict(address=event[0], F32_bits=event[1]))
                    counts['actual_original_native_F32_pairs'] += 1
                counts['native_root_phases'] += 1
                counts['literal_access_order_rows'] += 14
                host0, host1 = n[8188:8700], n[8700:9212]
                eq(host0[:5], host1[:5], 'actual restored host CW/SW/tag')
                eq(host0[24:32], host1[24:32], 'actual restored host MXCSR and mask')
                eq(host0[160:416], host1[160:416], 'actual restored host sixteen XMM registers')
                for register in range(8):
                    begin = 32 + register * 16
                    eq(host0[begin:begin + 10], host1[begin:begin + 10], 'actual restored host raw80 ' + str(register))
                eq(n[9212:9240], n[9240:9268], 'actual restored whole host ENV28')
                host_differences = [dict(offset=i, before=a, after=b)
                    for i, (a, b) in enumerate(zip(host0, host1)) if a != b]
                counts['actual_architectural_host_FX_and_whole_ENV_pairs'] += 1
                observations.append(dict(level=level, sequence=sequence, CW=tag[5], TOP=tag[6], outputs=outputs,
                                         host_FX_raw_differences=host_differences, whole_host_FX512_equality_claimed=False,
                                         XOR_AF_semantic_equality_claimed=False, full_State_source_comparison=False))
        assert counts['native_root_phases'] == 12 and counts['actual_original_native_F32_pairs'] == 36
        assert counts['whole_43page_endpoint_relations'] == 1032
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        if bundle is not None:
            bundle.close()
        pin(__file__)
        artifact = out / 'observations.json'
        artifact.write_text(json.dumps(observations, indent=2) + '\n')
        pin(artifact)
        report = dict(passed=passed, scope='Six genuine original cases against both actual native levels; CPU/FX architectural/whole ENV/pages',
                      root=0x4b64f0, counts=dict(counts), source_after_seed=False,
                      original_AFTER_used_only_for_comparison=True,
                      host_cos_expected_output_used=False, full_State_source_comparison=False,
                      provider_lifetime_controls=False, initializer_credit=0,
                      reader_closed=True, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
