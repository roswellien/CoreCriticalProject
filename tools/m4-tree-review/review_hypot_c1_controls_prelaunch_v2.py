"""Independent bounded numeric C1/control first-writer admission; no guest launch."""
from pathlib import Path
import ast, hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
A = R / 'reports/m4-hypot-native'
PH = '7219937e27edf2960129466f6416bfe109bee5b03f4e702c103fa296d80db03a'
BH = '9d36ad08985ecac2e28711cd2d9e3295b959eadd90524258ad166540c4f3f7dd'
FH = '1da61e5ba0103b88698c2e7acba8fd62095ef91022c168f86ed7ade1b1db5c93'
PINS = {}

def need(v, why):
    if not v: raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(p, h=None):
    p = Path(p).resolve()
    need(p.suffix.lower() not in ('.mwb', '.zip'), 'No archive/capture reader')
    v = sha(p); need(h is None or h == v, 'Exact physical input ' + str(p))
    need(str(p) not in PINS or PINS[str(p)] == v, 'Stable physical identity')
    PINS[str(p)] = v; return p

def load(p, h=None): return json.loads(pin(p, h).read_text(encoding='utf-8-sig'))

def module(p, name):
    spec = importlib.util.spec_from_file_location(name, pin(p))
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj

def ast_value(path, key):
    tree = ast.parse(pin(path).read_text())
    rows = [x.value for x in tree.body if isinstance(x, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == key for t in x.targets)]
    need(len(rows) == 1, 'One exact source-authored additive literal ' + key)
    return ast.literal_eval(rows[0])

def candidates(image, raw, relocs):
    need(raw and all(r['type'] == 4 or (r['type'] == 11 and r['symbol']['name'] == 'active'
         and r['symbol']['section'] > 0 and r['symbol']['value'] == 0) for r in relocs),
         'Only exact AMD64 REL32 and declared active TLS SECREL executable relocations')
    masked = {i for r in relocs for i in range(r['offset'], r['offset']+4)}
    need(all(0 <= i < len(raw) for i in masked), 'Entire relocation DWORD inside function')
    runs, first = [], None
    for i in range(len(raw)+1):
        if i < len(raw) and i not in masked:
            if first is None: first = i
        elif first is not None:
            runs.append((first, raw[first:i])); first = None
    off, needle = max(runs, key=lambda x: len(x[1])); result = []
    for sec in image.sections:
        if not sec['executable']: continue
        data = image.data[sec['raw_offset']:sec['raw_offset']+sec['raw_size']]; at = 0
        while True:
            at = data.find(needle, at)
            if at < 0: break
            begin = at-off; actual = data[begin:begin+len(raw)] if begin >= 0 else b''
            if len(actual) == len(raw) and all(a == b for i,(a,b) in enumerate(zip(raw,actual)) if i not in masked):
                result.append((image.image_base+sec['virtual_address']+begin, actual))
            at += 1
    return result

def image_bytes(image, va, size):
    for sec in image.sections:
        off = va-image.image_base-sec['virtual_address']
        if 0 <= off and off+size <= sec['raw_size']:
            return image.data[sec['raw_offset']+off:sec['raw_offset']+off+size]
    raise ValueError('Whole requested linked bytes in physical image')

def directories(image):
    pe = struct.unpack_from('<I', image.data, 60)[0]; optional = pe+24
    return [struct.unpack_from('<2I', image.data, optional+112+8*i) for i in range(16)]

def linked_function(C, image, symbols, sections, name, unique=True):
    raw, relocs = C.function(symbols, sections, name)
    found = candidates(image, raw, relocs)
    need(len(found) == 1 if unique else bool(found), 'Whole actual linked function ' + name)
    address, actual = found[0]; targets = []
    for row in relocs:
        i = row['offset']; source = struct.unpack_from('<i', raw, i)[0]
        final = struct.unpack_from('<i', actual, i)[0]
        if row['type'] == 4:
            targets.append(dict(offset=i, type=4, symbol=row['symbol']['name'], actual_target=address+i+4+final-source))
        else:
            tls_rva, tls_size = directories(image)[9]
            need(tls_size >= 40, 'Complete actual PE32+ TLS directory')
            start, end, _, _, zero, _ = struct.unpack('<4Q2I', image_bytes(image, image.image_base+tls_rva, 40))
            value = final-source
            need(value >= 0 and value+8 <= end-start+zero, 'Declared active section-relative TLS cell within actual template')
            need(image_bytes(image, start+value, 8) == bytes(8), 'Actual initialized active TLS pointer cell is zero')
            need(sections[row['symbol']['section']]['bytes'] == bytes(8), 'Whole compiler active TLS cell')
            targets.append(dict(offset=i,type=11,symbol='active',section_relative_offset=value,
                                actual_template_start=start,actual_template_end=end,
                                virtual_address_claim=False))
    return dict(symbol=name,address=address,bytes=len(raw),raw_hex=raw.hex(),linked_hex=actual.hex(),relocations=targets)

def main(name):
    need(re.fullmatch('hypot-c1-controls-prelaunch-r[1-9][0-9]*', name), 'Finite additive review name')
    out = R/'reports/m4-tree-review'/name; need(not out.exists(), 'Fresh immutable review output'); out.mkdir()
    passed=False; compiled=[]; literal=[]; boundaries=[]; levels=[]; inline=[]; inputs=[]
    try:
        prior = load(R/'reports/m4-tree-review/hypot-coupled-prelaunch-r1/report.json',
                     'abcac29a4df6e80ee18453f717bfaa2cfd3f86f8efd06abdbc6fba5322661a96')
        prep = load(A/'fixture-preparation-r6/report.json', PH)
        build = load(A/'fixture-build-r6/build.json', BH)
        old = load(A/'fixture-preparation-r4/report.json', prior['preparation_sha256'])
        for receipt in (prior, prep, build, old):
            need(receipt['passed'], 'Passed current preparation/build and independent input review')
            for key in ('files','artifacts'):
                for p,h in receipt.get(key,{}).items(): pin(p,h)
        need(build['preparation_sha256'] == PH and Path(build['preparation']).resolve() == (A/'fixture-preparation-r6/report.json').resolve(), 'Exact current preparation consumed')
        need(prep['inputs'] == old['inputs'] and prep['inputs_sha256'] == old['inputs_sha256'] == prior['inputs_sha256'], 'Unchanged complete coupled BEFORE storage')
        need(prep['source_domain'] == old['source_domain'] and prep['source_domain_sha256'] == old['source_domain_sha256'], 'Unchanged physically reached source domain')
        need(prep['writer_launched'] is False and prep['native_executed'] is False and prep['initializer_credit'] == 0, 'No execution/acceptance inferred')
        need(prep['original_AFTER_seed'] is prep['source_API_response_seed'] is prep['numerical_oracle'] is False, 'No AFTER/response/value seed')
        need(prep['counts'] == dict(literal_bodies=21,literal_objects=42,genuine_cases=6,causal_operands_per_case=616,source_pages_per_case=190), 'Exact finite input/literal geometry')
        need(prep['refusal_modes'] == {'1':'source read address','2':'source access width','3':'source current PC','4':'literal source CALL target','5':'guest versus actual hardware CW','6':'control State identity','7':'FP exception mask','8':'source saved return identity'}, 'Explicit eight actual worker fault seams')
        source = pin(R/'tools/m4-hypot-native/fixture_v5.cpp', FH).read_text()
        need(source == pin(A/'fixture-preparation-r6/fixture.cpp').read_text(), 'Actual generated current fixture equals reviewed source')
        for f in ('CMakeLists.txt','control_runtime.cpp','fixture_spec_O0.hpp','fixture_spec_O2.hpp','generated_bridges.inc','literal_dispatch.hpp'):
            need(pin(A/'fixture-preparation-r4'/f).read_bytes() == pin(A/'fixture-preparation-r6'/f).read_bytes(), 'Complete unchanged literal/Runtime input ' + f)
        # Independently reconstruct both additive source transformations, without executing a generator.
        original = pin(R/'tools/m4-hypot-native/fixture_v2.cpp').read_text()
        repair = ast_value(R/'tools/m4-hypot-native/derive_fixture_v3.py','new')
        oldline = ast_value(R/'tools/m4-hypot-native/derive_fixture_v3.py','old')
        need(original.count(oldline) == 1, 'Unique source C1 seam')
        base = original.replace(oldline,repair)
        need(base == pin(R/'tools/m4-hypot-native/fixture_v3.cpp').read_text(), 'Only finite raw80/CW/C1 repair in parent fixture')
        changes = ast_value(R/'tools/m4-hypot-native/derive_fixture_v4.py','changes')
        need(len(changes) == 9, 'Exact nine authored control/wrapper changes')
        for before,after in changes:
            need(base.count(before) == 1, 'Unique additive control seam'); base=base.replace(before,after)
        guard = ast_value(R/'tools/m4-hypot-native/derive_fixture_v4.py','guard')
        need(base.count('int main(int argc,char **argv) {') == 1, 'Unique caller wrapper insertion')
        need(base.replace('int main(int argc,char **argv) {',guard+'int main(int argc,char **argv) {') == source, 'Entire current code explained by exact finite changes')
        for text in ('reinterpret_cast<const std::byte*>(&c.s)+2486,10','proof.actual_CW==c.s.x87.fxsave.cwd.flat','proof.lowered_F32==proof.hardware_F32','c.s.sw.c1=static_cast<unsigned char>((proof.actual_SW>>9)&1)',
                     'if(c.s.gpr.rip.dword==0x4b5905)','need(a==0x60b2e8','c.checkpoint(stem.c_str())','dump(stem+"/RuntimeFX.bin",r->fx().data(),512)',
                     'dump(stem+"/accesses.bin"','dump(stem+"/frames.bin"','dump(stem+"/APIs.bin"','dump(stem+"/routes.bin"','dump(stem+"/context.bin"',
                     'checkpoint("retry/before")','checkpoint("retry/after")','r->invoke({0x4b5910})','f.reason()==FaultReason::poisoned','r->poisoned()&&!c.complete'):
            need(text in source, 'Actual source repair/refusal/full retry prerequisite '+text)
        need(source.index('checkpoint("retry/before")') < source.index('f.reason()==FaultReason::poisoned') < source.index('checkpoint("retry/after")') < source.index('active=nullptr;'), 'Same live actual Context before/after poisoned retry, then revocation')
        asm = pin(R/'tools/m4-hypot-native/hardware_boundary.s').read_text()
        parent_asm = pin(R/'tools/m4-mfc1168-native/hardware_boundary.s').read_text()
        need(parent_asm.replace('mfc_hardware_call','hypot_hardware_call').replace('mfc_invoke_guarded','hypot_invoke_guarded') == asm, 'Exact previously measured caller boundary renamed only')
        need(asm.index('fnstenv 512(%rbx)') < asm.index('callq hypot_invoke_guarded') < asm.index('fxsave64 544(%rbx)') < asm.index('fxrstor64 0(%rbx)') < asm.index('fxsave64 1088(%rbx)'), 'Immediate caller BEFORE, unrestored exit, real restoration, restored exit capture')
        need('.seh_pushreg %rbx' in asm and '.seh_stackalloc 32' in asm and prep['hardware_boundary_bytes'] == 1632, 'Aligned Windows caller frame and declared unwind')
        current_inputs = load(prep['inputs'], prep['inputs_sha256'])
        need(len(current_inputs['cases']) == 6 and not current_inputs['source_AFTER_seed'] and not current_inputs['numerical_results_seeded'], 'Only six genuine BEFORE cases')
        P = module(R/'tools/m4-tree-review/review_hypot_coupled_prelaunch.py','c1_parent')
        C = module(R/'tools/m4-tree-review/amd64_coff.py','c1_coff')
        M = module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','c1_image')
        bodies = load(A/'reached-domain-r1/literal-bodies.json')
        state = pin(A/'inputs-r5/input-state.bin').read_bytes(); need(len(state)==3480, 'Whole six CPU40/FX512/ENV28 BEFORE inputs')
        for case in current_inputs['cases']:
            _, pages = P.pack(pin(case['pack'],case['pack_sha256']))
            need(len(pages)==190, 'Actual complete coupled input pages')
            inputs.append(dict(sequence=case['sequence'],pack_sha256=case['pack_sha256'],whole_pages=190,CPU_FX_ENV_bytes=580))
        need(all(v['exit_code']==0 for v in build['commands']), 'Actual successful current configure/compile/link')
        boundary_obj = pin(A/'fixture-preparation-r6/hardware_boundary.obj')
        bs,bsec=C.parse(boundary_obj.read_bytes()); boundary_raw=bsec[1]['bytes']; boundary_rel=bsec[1]['relocations']
        need(boundary_raw.hex()=='534883ec204889d3480fae03d9b300020000d9a300020000e800000000480fae8320020000d9b320040000d9a320040000480fae0bd9a300020000480fae8340040000d9b340060000d9a3400600004883c4205bc3', 'Independent full 85-byte caller boundary')
        need(len(boundary_rel)==1 and boundary_rel[0]['offset']==25 and boundary_rel[0]['type']==4 and boundary_rel[0]['symbol']['name']=='hypot_invoke_guarded', 'Only exact caller REL32 to guarded wrapper')
        need(bsec[4]['bytes']==bytes.fromhex('0105020005320130') and bsec[5]['bytes']==struct.pack('<3I',0,85,0), 'Exact assembler unwind and function-table templates')
        ninja = pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
        for level, worker in build['workers'].items():
            folder=Path(worker['path']).parent; image=M.AMD64Image(pin(worker['path'],worker['sha256']).read_bytes())
            graph=pin(folder/'build.ninja').read_text()
            line=next(x for x in graph.splitlines() if x.startswith('build hypot-native.exe: CXX_EXECUTABLE_LINKER'))
            actual_inputs={str((folder/Path(x.replace('$:',':'))).resolve()) for x in line.split(' ',3)[3].split(' |')[0].split(' ') if x.endswith('.obj')}
            need(len(actual_inputs)==27 and set(worker['literal_objects']) < actual_inputs and str(boundary_obj) in actual_inputs, 'Actual21 literal +five compiler +one ASM object link graph')
            need(worker['literal_objects']==old['objects'][level]+[str(boundary_obj)], 'Exact preserved source bodies plus boundary input')
            for body in bodies.values():
                q=body['objects'][level]; obj=pin(q['path'],q['sha256']); s,sec=C.parse(obj.read_bytes())
                raw,rel=C.function(s,sec,body['symbol']); found=C.linked_candidates(image,raw,rel)
                need(len(found)==1, 'Unique complete unchanged linked literal body')
                literal.append(dict(level=level,entry=body['entry'],address=found[0][0],bytes=len(raw),relocation_DWORDs=len(rel),object_sha256=q['sha256']))
            need(pin(folder/'fixture_spec.hpp').read_bytes()==pin(A/'fixture-preparation-r6'/f'fixture_spec_{level}.hpp').read_bytes(), 'Actual current compiled spec header')
            fixture_obj=pin(folder/'CMakeFiles/hypot-native.dir/fixture.cpp.obj'); symbols,sections=C.parse(fixture_obj.read_bytes())
            wanted=['mw34_hypot_write_memory_f32','mw34_hypot_control_admit','hypot_invoke_guarded','?native_root@@YAXAEAVRuntime@m4_runtime@mw34@@@Z',
                    '?authority@Context@@QEAAXXZ','?read@Context@@QEAAXIV?$span@W4byte@std@@$0?0@std@@@Z',
                    '?write@Context@@QEAAXIV?$span@$$CBW4byte@std@@$0?0@std@@@Z','?dispatch@Context@@QEAAPEAXI_N@Z',
                    '?returned@Context@@QEAAXI@Z','?access@Context@@QEAAXII_NV?$span@$$CBW4byte@std@@$0?0@std@@@Z',
                    'mw34_hypot_fpu_exception_test','main']
            current=[]
            for symbol in wanted:
                exists=any(s['name']==symbol and s['section']>0 for s in symbols.values())
                if not exists:
                    inline.append(dict(level=level,symbol=symbol,separate_function_absent=True,source_dependency_authenticated=True,separate_linked_function_credit=False)); continue
                row=linked_function(C,image,symbols,sections,symbol); row['level']=level;current.append(row);compiled.append(row)
            repair_row=next(x for x in current if x['symbol']=='mw34_hypot_write_memory_f32')
            raw=bytes.fromhex(repair_row['raw_hex'])
            need(any(raw[i:i+2] in (b'\xdb\x6c',b'\xdb\xad',b'\xdb\x6d',b'\xdb\xaf',b'\xdb\xae') for i in range(len(raw)-1)) and b'\xd9' in raw and b'\xdd' in raw, 'Actual compiled x87 conversion sequence exists; whole bytes retained')
            wrapper=next(x for x in current if x['symbol']=='hypot_invoke_guarded')
            found=candidates(image,boundary_raw,boundary_rel); need(len(found)==1, 'Unique entire linked hardware boundary')
            address,actual=found[0];target=address+29+struct.unpack_from('<i',actual,25)[0]
            need(target==wrapper['address'], 'Actual boundary call resolves to reviewed guarded wrapper')
            exception_rva,exception_size=directories(image)[3]
            table=image_bytes(image,image.image_base+exception_rva,exception_size)
            entries=[struct.unpack_from('<3I',table,i) for i in range(0,len(table),12)]
            unwind=[v for v in entries if image.image_base+v[0]==address]
            need(len(unwind)==1 and image.image_base+unwind[0][1]==address+85 and image_bytes(image,image.image_base+unwind[0][2],8)==bsec[4]['bytes'], 'Actual linked exception-table entry and all8 unwind bytes match assembler')
            boundaries.append(dict(level=level,address=address,bytes=85,call_target=target,whole_hex=actual.hex(),unwind_hex=bsec[4]['bytes'].hex()))
            control=pin(folder/'CMakeFiles/hypot-native.dir/control_runtime.cpp.obj'); cs,csec=C.parse(control.read_bytes())
            for helper in ('mw34_hypot_store_cw','mw34_hypot_load_cw','mw34_hypot_wait'):
                row=linked_function(C,image,cs,csec,helper); row['level']=level;compiled.append(row)
            # All other compiler units use identical source; authenticate exact code/data/relocations with only the timestamp allowed.
            before_folder=A/'fixture-build-r4'/('build-'+level)
            for obj in actual_inputs-set(worker['literal_objects'])-{str(fixture_obj)}:
                relation=P.object_relation(before_folder/Path(obj).relative_to(folder),Path(obj));relation['level']=level
                need(relation['all_code_data_relocations_and_other_header_bytes_identical'],'Exact unchanged Runtime/control/compiler input object');compiled.append(relation)
            db=pin(folder/'.ninja_deps'); dbsha=sha(db)
            process=subprocess.run([str(ninja),'-C',str(folder),'-t','deps'],capture_output=True,creationflags=0x08000000)
            need(process.returncode==0 and sha(db)==dbsha, 'Read-only actual compiler dependency database')
            consumed=[Path(x.strip()) for x in process.stdout.decode().splitlines() if x.startswith('    ') and Path(x.strip()).is_file()]
            need(any(q.resolve()==(A/'fixture-preparation-r6/fixture.cpp').resolve() for q in consumed), 'Actual compiler consumes reviewed new source')
            for q in consumed: pin(q)
            levels.append(dict(level=level,literal_objects=21,compiled_objects=5,ASM_objects=1,linked_inputs=27,actual_consumed_dependencies=len(consumed),dependency_database_sha256=dbsha))
        controller=pin(R/'tools/m4-hypot-native/run_fixture.py').read_text()
        need("review['files'][str(Path(build_path).resolve())]==build_sha" in controller and 'timeout=30' in controller, 'Positive writer requires exact current review/build and bounded closed subprocesses')
        need('control_mode' not in controller and 'for case in input_report[\'cases\']' in controller, 'Current controller is twelve positives only; fault execution remains separately required')
        pin(R/'tools/m4-hypot-native/prepare_fixture_v6.py');pin(R/'tools/m4-hypot-native/prepare_fixture_v5.py');pin(__file__);pin(sys.executable)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        for filename,value in [('whole-current-linked-functions.json',compiled),('whole-linked-literal-functions.json',literal),('whole-caller-boundary-relations.json',boundaries),('inlined-or-absent-functions.json',inline),('whole-BEFORE-input-relations.json',inputs)]:
            p=out/filename;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        report=dict(passed=passed,preparation_sha256=PH,build_sha256=BH,current_fixture_sha256=FH,
                    parent_independent_review_sha256='abcac29a4df6e80ee18453f717bfaa2cfd3f86f8efd06abdbc6fba5322661a96',
                    counts=dict(genuine_BEFORE_cases=len(inputs),whole_BEFORE_pages=190*len(inputs),literal_bodies=21,whole_linked_literal_functions=len(literal),whole_hardware_boundaries=len(boundaries),declared_fault_modes=8),levels=levels,
                    source_C1_measured_from_current_raw80_under_actual_CW=True,source_numeric_AFTER_seed=False,numerical_oracle=False,worker_launched=False,
                    archive_reader_opened=False,initializer_credit=0,current_fault_execution_measured=False,
                    scope='Independent first-writer admission only. Current compiled source, immutable complete coupled BEFORE inputs, literal bodies and whole changed linked functions/caller boundary are bound. Exact TLS relocations are section-relative offsets, not virtual-address evidence. Faults mutate eight real worker seams and same live Runtime/Context retries dump complete resources; current controller runs twelve positives only. Actual C1/source State, fault reasons, full caller FX/ENV restoration, fresh refusal execution and connected prefix applicability still require measured postexecution proof.',files=PINS)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),files=len(PINS),counts=report['counts'])))

if __name__=='__main__': main(sys.argv[1])
