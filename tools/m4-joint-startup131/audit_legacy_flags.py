"""Archive-free physical proof for the two inherited DEC/JNE loops."""
from pathlib import Path
import hashlib, importlib.util, json, re, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def main(name):
    out = ROOT/'reports/m4-joint-startup131-source'/name
    assert not out.exists(); out.mkdir(parents=True)
    files = {}; passed = False; rows = []
    def pin(p, h=None):
        p = Path(p).resolve(); value = sha(p)
        assert h is None or value == h
        assert str(p) not in files or files[str(p)] == value
        files[str(p)] = value; return p
    try:
        scope = json.loads(pin(ROOT/'reports/m4-joint-startup131-source/preflight-r3/source-program-scope.json').read_bytes())
        source = json.loads(pin(ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2/extraction.json', '62983322b91c6b446ddee5562248614ad3a22512dc1c256f1c0bfea56fcf6b97').read_bytes())
        image = pin(source['image']['path'], source['image']['sha256']).read_bytes()
        parser = pin(source['PE_parser']['path'], source['PE_parser']['sha256'])
        spec = importlib.util.spec_from_file_location('legacy_flag_physical_PE', parser)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        pe = module.PE(image)
        bindings = {r[0]: r for r in source['code_bindings']}
        lookup = {r['pc']: r for r in source['instructions']}
        legacy = scope['legacy_source_catalog']
        conditional = [(r['root'], ins) for r in legacy for ins in r['architectural_consumer_rows'] if ins['mnemonic'] != 'jmp']
        assert [(root, r['pc'], r['mnemonic']) for root, r in conditional] == [(0x410910,0x410931,'jne'),(0x410940,0x410971,'jne')]
        for root, branch, decrement, body, count, base, stride in ((0x410910,0x410931,0x410930,0x41092a,167,0x604130,20),(0x410940,0x410971,0x410970,0x410962,4,0x6040d8,16)):
            graph = next(g for g in source['graphs'] if g['entry'] == root)
            instructions = [lookup[pc] for pc in graph['instruction_pcs']]
            assert graph['static_local_branch_decode_closed'] and not graph['unresolved_controls']
            incoming = []; physical = []
            for ins in instructions:
                pc, size = ins['pc'], ins['size']; raw = bytes.fromhex(ins['bytes'])
                file_offset, _ = pe.rva_range(pc-0x400000, size)
                assert bindings[pc][:3] == [pc,size,file_offset] and image[file_offset:file_offset+size] == raw
                physical.append(dict(instruction=ins,file_offset=file_offset))
                targets = []
                if ins['mnemonic'].startswith('j'):
                    target = int(re.match(r'0x[0-9a-f]+',ins['operands']).group(0),16); targets.append(target)
                    if ins['mnemonic'] != 'jmp': targets.append(pc+size)
                elif ins['mnemonic'] != 'ret': targets.append(pc+size)
                if branch in targets: incoming.append(pc)
            dec = lookup[decrement]; jump = lookup[branch]
            assert incoming == [decrement]
            assert dec == dict(pc=decrement,size=1,bytes='49',mnemonic='dec',operands='ecx')
            assert jump['mnemonic']=='jne' and int(jump['operands'].split()[0],16)==body and dec['pc']+dec['size']==branch
            body_rows = [r for r in instructions if body <= r['pc'] <= decrement]
            assert body_rows[-1] == dec
            assert all(r['mnemonic'] in ('mov','add') and not r['operands'].startswith('ecx,') for r in body_rows[:-1])
            initializer = [r for r in instructions if r['mnemonic']=='mov' and r['operands'].startswith('ecx,')]
            assert len(initializer)==1 and int(initializer[0]['operands'].split(',')[1],16)==count
            # DEC defines ZF at every source loop visit; the physical JNE has
            # exactly that immediate predecessor. Incoming undefined flags and
            # intervening ADD flags cannot reach the architectural ZF read.
            tests = [dict(iteration=i,ECX_before=count-i,ECX_after=count-i-1,defined_ZF=int(count-i-1==0),taken=count-i-1!=0) for i in range(count)]
            assert sum(r['taken'] for r in tests)==count-1 and tests[-1]['defined_ZF']==1
            rows.append(dict(root=root,branch_PC=branch,defining_PC=decrement,required_flags=['ZF'],unique_immediate_predecessors=incoming,loop_body=body,initial_count=count,architectural_source_consumers=count,loop_address_base=base,loop_stride=stride,physical_instructions=physical,source_defined_flag_visits=tests,no_intervening_instruction=True,actual_instruction_trace_claim=False))
        pin(ROOT/'tools/m4-joint-startup27-review/observe.py')
        pin(ROOT/'reports/m4-mixed-startup/independent-review-r1/review.py','53832a5587972840620254c792bcd732d805f411553386822ca0afb2530795c3')
        q=out/'legacy-defined-flag-proof.json'; q.write_text(json.dumps(rows,indent=2)+'\n'); pin(q)
        pin(__file__); pin(sys.executable)
        for p,h in files.items(): assert sha(p)==h
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        report=dict(passed=passed,scope='Physical archive-free source proof for every inherited legacy conditional consumer: immediate DEC ECX defines ZF before JNE; no dynamic instruction trace or initializer credit claimed',legacy_roots=26,conditional_PCs=2,source_consumers_per_sequence=171,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__': main(sys.argv[1])
