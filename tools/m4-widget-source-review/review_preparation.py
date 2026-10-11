"""Independent bounded source/operand review of the immutable widget52 comparers.

Reads source and PE files only. It does not import or open a capture reader and
does not grant execution credit. The finite SETE proof supplements the explicit
flag consumer guard without changing either executed comparer.
"""
from pathlib import Path
import ast, hashlib, json, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}
CHECKS = []

def need(value, label):
    if not value:
        raise ValueError(label)
    CHECKS.append(label)

def pin(path, expected=None):
    p = Path(path).resolve()
    need(p.suffix.lower() not in ('.mwb', '.zip'), 'No archive input: ' + str(p))
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    need(expected is None or h == expected, 'Exact physical input: ' + str(p))
    need(str(p) not in PINS or PINS[str(p)] == h, 'Stable physical input: ' + str(p))
    PINS[str(p)] = h
    return b

def read(path, expected=None):
    return json.loads(pin(path, expected))

def main(name):
    out = R / 'reports/m4-widget-source-review' / name
    need(not out.exists(), 'Fresh independent bounded review output')
    out.mkdir(parents=True)
    prep = read(R/'reports/m4-widget-native/source-comparison-preparation-r5/report.json',
                '563eee87b514a65c33480243df0170a2391163d3e958e4a177d70d3408af0d93')
    need(prep['passed'] and prep['physical_widget_rows'] == 1093 and
         prep['static_program_rows'] == 5643 and prep['source_prefix_roots'] == 6,
         'Exact current52 prepared source extent')
    need(len(prep['files']) == 75 and prep['all_successful_static_dependencies_pinned'],
         'Current static source construction closure has 75 pinned inputs')
    for path, h in prep['files'].items():
        pin(path, h)
    policy = read(R/'reports/m4-widget-native/source-comparison-preparation-r5/comparison-policy.json')
    need(policy['comparison_sha256'] ==
         'fed26231f517526ab961cee11cff4eb49a0048ef8c2d615d94fe2027616a4e7a' and
         policy['source_provider_tail_comparison_sha256'] ==
         '6b64b0212595e7ca812a6b1bec600480afcb4656e819e237e0dc717664b24744',
         'Exact prepared prefix4/registry4 code identity')
    need(policy['source_roots'] == [0x40e250,0x40ef50,0x5a3c30,0x5a3ff0,0x5a66f0,0x479590]
         and policy['comparison_terminal'] == 0x78004a36,
         'Six explicit roots and physical borrowed provider terminal')
    need(not policy['original_result_or_memory_seed'] and
         not policy['cold_or_GDI_failure_admission'] and
         not policy['source_shutdown_execution'], 'Explicit bounded source admission')

    prefix_path = R/'tools/m4-widget-native/compare_prefix_v4.py'
    registry_path = R/'tools/m4-widget-native/compare_registry_v4.py'
    prefix = pin(prefix_path).decode()
    registry = pin(registry_path).decode()
    trees = {'prefix': ast.parse(prefix), 'registry': ast.parse(registry)}
    # These exact AST construction sites are the model's machine inputs. The
    # strings are audited dataflow assertions on pinned code, not a generic
    # taint analysis or a claim about all possible Python programs.
    constructors = {}
    for branch, tree in trees.items():
        constructors[branch] = [ast.unparse(n) for n in ast.walk(tree)
                                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                and n.func.id in ('Prefix', 'Provider')]
    need(len(constructors['prefix']) == len(constructors['registry']) == 1,
         'One explicit source machine construction per comparer')
    need(constructors['prefix'][0].startswith('Prefix(state, fx, cpu, memory,'),
         'Prefix machine receives own entry State/FX/CPU/BEFORE memory')
    need(constructors['registry'][0].startswith('Provider(state, fx, cpu, memory,'),
         'Provider machine receives own source-joined entry checkpoint')
    anchors = {
      'prefix': [
        "state=raw(before_dir/'State.bin');fx=raw(before_dir/'FX.bin');cpu=raw(before_dir/'CPU.bin')",
        "memory,tib=region_memory(phase_dir/'before')",
        "eq(bytes(m.state),observed_state,'Whole independently derived State3504 at provider entry')",
        "eq(m.bytes(0x20001000,4096),raw(prefix/f'registry-checkpoint-{n}-page-{0x20001000}.bin')",
        "eq(current_accesses[:len(expected)],expected",
        "eq([v[:5]for v in native_FS],FS",
        "eq(native_virtual,derived",
        "eq(native_arrays,derived",
        "eq(model.bytes(model.reg('esp'),64),a['frame']",
        "eq(args,a['args'][:w[7]]",
        "model.api_return(site,w[7],w[9])",
        "m.run(lambda x:x.cursor==0x78004a36,api=external)",
      ],
      'registry': [
        "hashlib.sha256(state).hexdigest()==prefix['computed_provider_entry_State_sha256']",
        "memory=checkpoint_memory(dump,b)",
        "response.index=start",
        "m.run(lambda x:x.cursor==0x5ac124,api=response)",
        "need(response.index==end",
        "eq(bytes(m.state),raw(dump/f'registry-checkpoint-{a}-state.bin')",
        "eq(m.bytes(address,len(payload)),bytes(payload)",
        "eq(source_ledger[cursor+2:cursor+2+len(provider_accesses)],[tuple(v)for v in provider_accesses]",
        "m.run(lambda x:x.cursor==0xfffffff0)",
        "eq(bytes(m.state),raw(after_component/'State.bin')",
        "eq(m.bytes(0x20001000,4096),raw(folder/f'phase-{phase}'/'after'/'stack.bin')",
        "need(not m.call_stack and m.reg('esp')==frame+4",
      ],
    }
    for branch, labels in anchors.items():
        text = prefix if branch == 'prefix' else registry
        for label in labels:
            need(label in text, 'Audited source/equality chain '+branch+': '+label)
    need("p['AFTER_State_or_memory_seed']is False" in registry and
         "No canonical/archive reader" in prefix and
         "AFTER_machine_or_memory_seed=False" in registry,
         'No AFTER machine seed and no canonical archive path')
    need("pin(C.__file__)" in registry and 'compare_prefix_v4.py' in registry,
         'Registry pins the exact input and I/O prefix adapter')

    # Match the entire 1093-row widget/font contract to the physical game PE,
    # independently of the compiler/lifter's hashes.
    contract = read(R/'reports/m4-font479590-original/source-preparation-r1/source-contracts.json')
    rows = contract['instructions']
    need(len(rows) == 1093 and len({r['pc'] for r in rows}) == 1093,
         'Unique complete current widget source contract')
    pe = pin(R/'MW3/Mech3.exe')
    off = struct.unpack_from('<I', pe, 0x3c)[0]
    need(pe[off:off+4] == b'PE\0\0', 'Physical source is PE')
    sections, optional_size = struct.unpack_from('<H',pe,off+6)[0],struct.unpack_from('<H',pe,off+20)[0]
    image_base = struct.unpack_from('<I',pe,off+24+28)[0]
    section_rows=[]
    for n in range(sections):
        s=off+24+optional_size+n*40
        virtual_size,rva,raw_size,raw_offset=struct.unpack_from('<4I',pe,s+8)
        section_rows.append((rva,max(virtual_size,raw_size),raw_size,raw_offset))
    for row in rows:
        rva=row['pc']-image_base
        matches=[s for s in section_rows if s[0]<=rva and rva+row['width']<=s[0]+s[2]]
        need(len(matches)==1, 'One physical PE section at '+hex(row['pc']))
        s=matches[0];offset=s[3]+rva-s[0]
        need(pe[offset:offset+row['width']].hex()==row['bytes_hex'],
             'Exact complete physical instruction at '+hex(row['pc']))

    bypc={r['pc']:r for r in rows}
    incoming={pc:[] for pc in bypc}
    for row in rows:
        op=row['mnemonic']; pc=row['pc']; target=None
        args=row['decoded_operands']
        if args and args[0]['kind']=='immediate' and (op.startswith('j') or op=='call'):
            target=args[0]['value']
            if target in incoming: incoming[target].append((pc,'target'))
        if op not in ('jmp','ret','retn') and pc+row['width'] in incoming:
            incoming[pc+row['width']].append((pc,'fallthrough'))
    expected={0x51741d:[(0x51741b,'fallthrough')],
              0x517472:[(0x51745e,'target'),(0x517469,'target'),(0x517470,'fallthrough')],
              0x51747f:[(0x51747d,'fallthrough')],
              0x51748f:[(0x51748d,'fallthrough')]}
    proof=[]
    need({r['pc'] for r in rows if r['mnemonic']=='sete'}==set(expected),
         'Exact four physical SETE ZF consumers')
    for pc, predecessors in expected.items():
        need(sorted(incoming[pc])==sorted(predecessors),
             'Complete direct/fallthrough SETE predecessors '+hex(pc))
        causes=[]
        for pred,edge in predecessors:
            cause=pred
            if bypc[pred]['mnemonic']=='jmp':
                need(len(incoming[pred])==1 and incoming[pred][0][1]=='fallthrough',
                     'Unique pre-JMP ZF lifetime '+hex(pred))
                cause=incoming[pred][0][0]
            need(bypc[cause]['mnemonic'] in ('cmp','test'),
                 'Physical immediate defined ZF producer '+hex(cause))
            causes.append(dict(predecessor=pred,edge=edge,producer=bypc[cause],
                               preserved_jump=bypc[pred] if pred!=cause else None))
        proof.append(dict(consumer=bypc[pc],incoming=causes,
                          scope='Current recovered normal direct/fallthrough graph; arbitrary cold indirect entry denied'))
    q=out/'SETE-ZF-lifetimes.json';q.write_text(json.dumps(proof,indent=2)+'\n');pin(q)
    pin(__file__);pin(sys.executable)
    report=dict(passed=True,scope='Independent current52 comparator preparation/source dataflow review and exact physical 1093-row/SETE finite graph proof; raw equality runs remain separate',
      preparation_sha256='563eee87b514a65c33480243df0170a2391163d3e958e4a177d70d3408af0d93',
      counts=dict(prepared_input_pins=75,physical_instruction_rows=1093,SETE_consumers=4,
                  SETE_defined_ZF_paths=6,source_constructor_input_sites=2,checks=len(CHECKS)),
      constructors=constructors,reviewed_chains=anchors,
      limitations=['Six own-BEFORE component prefixes and source-joined provider entries; entire bootstrap persistent source is separate',
                   'Typed actual GDI/WinAPI response inputs are admitted only at their literal CALL; this is not an API reimplementation',
                   'The four SETE flags are independently proved for the current normal graph; the comparer guard itself remains immutable',
                   'GDI failures, cold formatter/unwind paths and source cleanup execution remain unadmitted'],
      archive_reader_opened=False,worker_launched=False,native_equality_claimed=False,initializer_credit=0,
      checks=CHECKS,files=PINS)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),passed=True,counts=report['counts'])))

if __name__=='__main__':main(sys.argv[1])
