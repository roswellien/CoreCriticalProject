"""Fresh, original-byte provider contracts for independent onexit review.

This reads the recovered PE source, not the native candidate. No execution or
initializer credit is asserted by producing this interface.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from paths import publish_bytes, workspace_path
from manifests import normalized, verify_manifest

RECOVERY_SHA = '7195aa825cde0c1d47279f285f66604b2fcd0eb66e1d88419d9eb4e7360170ee'
PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASE_INTERFACE_SHA = '194e2ca814869c500fd2948d9cc801d3ad7a8aef2367166379a5d0ad87e5a624'

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def prepare(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == ROOT / 'reports/m4-onexit-review' and not out.exists(),
         'Fresh independent provider-interface directory')
    files = {}
    def pin(path, expected=None):
        path = Path(path).resolve(); actual = sha(path)
        need(expected is None or actual == expected, 'Exact original source binding ' + str(path))
        key = normalized(str(path)); need(key not in files or files[key] == actual, 'One binding per physical path')
        files[key] = actual; return path
    recovery = ROOT / 'reports/m4-onexit-batch-recovery/recovery-r3'
    report = json.loads(pin(recovery / 'report.json', RECOVERY_SHA).read_bytes())
    need(report['passed_static_recovery'] and report['roots_admitted'] == 0,
         'Source-only static recovery remains separate from acceptance')
    for p, digest in json.loads(pin(recovery / 'pins.json').read_bytes())['files'].items(): pin(p, digest)
    parser_path = pin(ROOT / 'tools/m4-crt-locale-batch-recovery/recover_v2.py')
    parser = load_module('independent_onexit_operand_parser', parser_path)
    pe_path = pin(ROOT / 'tools/m4-crt/recover_provider.py')
    pe_module = load_module('independent_onexit_PE', pe_path)
    pe = pe_module.PE(pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', PROVIDER_SHA), PROVIDER_SHA)
    base_path = pin(ROOT / 'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json', BASE_INTERFACE_SHA)
    rows = {r['pc']: r for r in json.loads(base_path.read_bytes())['instructions']}
    graphs = json.loads((recovery / 'provider-graphs.json').read_bytes())
    original = {r['pc']: r for body in graphs.values() for r in body['instructions']}
    spans = [dict(name=name, start=a, stop=b) for name,a,b in (
        ('registry-producer',0x78004482,0x780044A8),
        ('onexit',0x78004A36,0x78004A7B),
        ('onexit-growth',0x7801E27B,0x7801E2C0),
        ('lock13-stub',0x78001514,0x7800151D),
        ('unlock13-stub',0x78003041,0x7800304A),
        ('dllonexit',0x78002FE5,0x78003041),
        ('dllonexit-null',0x7801E2E4,0x7801E2EB),
    )]
    spans += [dict(name=s['name'], start=s['start'], stop=s['stop'])
              for s in json.loads((recovery / 'mode1-selected-spans.json').read_bytes())['spans']]
    added = set()
    for span in spans:
        picked = [original[p] for p in sorted(original) if span['start'] <= p < span['stop']]
        need(picked and picked[0]['pc'] == span['start'] and picked[-1]['pc']+picked[-1]['size'] == span['stop'],
             'Complete source-only provider span ' + span['name'])
        raw = b''.join(bytes.fromhex(r['bytes']) for r in picked)
        need(raw == pe.read(span['start']-pe.base, span['stop']-span['start']), 'Whole physical provider source identity')
        span['sha256'] = hashlib.sha256(raw).hexdigest()
        for r in picked:
            value = dict(pc=r['pc'], width=r['size'], bytes_hex=r['bytes'], mnemonic=r['mnemonic'],
                         operands=r['operands'].split(' <')[0].strip())
            contract = parser.instruction_contract(value)
            need(r['pc'] not in rows or rows[r['pc']] == contract, 'Consistent literal shared provider instruction')
            rows[r['pc']] = contract; added.add(r['pc'])
    for row in rows.values():
        need(pe.read(row['pc']-pe.base,row['width']) == bytes.fromhex(row['bytes_hex']), 'Every reused/current row matches original DLL')
    for p in (Path(__file__), ROOT/'tools/m4-onexit-review/provider_model.py',
              ROOT/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py',
              ROOT/'tools/m4-crt-locale-batch-model-review/batch.py', Path(sys.executable)):
        pin(p)
    out.mkdir(parents=True)
    interfaces = dict(schema='mw34-onexit-independent-provider-source-v1',
                      instructions=[rows[p] for p in sorted(rows)], new_spans=spans,
                      unique_new_instruction_count=len(added), AFTER_machine_seed=False,
                      expected_machine_values_included=False, native_executed=False)
    path=out/'instruction-contracts.json'; publish_bytes(path,(json.dumps(interfaces,indent=2)+'\n').encode()); pin(path)
    result=dict(passed=True, schema='mw34-onexit-independent-provider-interface-v1',
                recovery_sha256=RECOVERY_SHA, provider_sha256=PROVIDER_SHA,
                instruction_contracts=str(path), instruction_contracts_sha256=sha(path),
                unique_new_instructions=len(added), instruction_count=len(rows), files=files,
                native_executed=False, original_executed=False, roots_admitted=0,
                physical_closure=verify_manifest(files))
    path=out/'report.json'; publish_bytes(path,(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,report_sha256=sha(path),instruction_contracts_sha256=sha(out/'instruction-contracts.json'),
                         unique_new_instructions=len(added))))

if __name__=='__main__': prepare(sys.argv[1])
