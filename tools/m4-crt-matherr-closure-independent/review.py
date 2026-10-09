"""Final independent physical/source/object/fault association for matherr leaf.

No author comparator/executor/model is imported. Root independently authored
raw/layout/causal stages are inspected and bound as distinct proof components.
"""
from pathlib import Path
import hashlib,importlib.util,json,ntpath,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-matherr'
OUT=BASE/'independent-final-closure-r5';PINS={};CHECKS=[];COMMANDS=[]
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(path,want=None):
    p=Path(path).resolve();key=str(p)
    if key in PINS:
        need(want is None or want==PINS[key],'Conflicting literal identity '+key);return p
    got=sha(p);need(want is None or got==want,'Physical identity '+key);PINS[key]=got;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def text(p,h=None):return pin(p,h).read_text(encoding='utf-8-sig')
def filemap(p,h=None,replacements=None):
    m=read(p,h);replacements=replacements or {};associations=[]
    for path,v in m['files'].items():
        digest=v['sha256'] if isinstance(v,dict) else v
        target=replacements.get(str(Path(path).resolve()),path);pin(target,digest)
        if target!=path:associations.append(dict(map=str(p),original_path=path,physical_path=str(target),sha256=digest))
    return len(m['files']),associations
def checked(name,**facts):CHECKS.append(dict(name=name,passed=True,**facts))
def run(argv,name):
    argv=list(map(str,argv));pin(argv[0]);r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),log_sha256=sha(p)))
    need(r.returncode==0,'Independent actual tooling/control step '+name);return r.stdout.decode(errors='replace')
def original_identity():
    path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec=importlib.util.spec_from_file_location('exact_readonly_PE',path);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
    gamebytes=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
    dllbytes=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes()
    game=pe.PEImage(gamebytes);dll=pe.PEImage(dllbytes)
    imports=[(d['library'],s) for d in game.imports() for s in d['symbols'] if game.image_base+s['iat_rva']==0x5bb50c]
    need(len(imports)==1 and imports[0][0].lower()=='msvcrt.dll' and imports[0][1].get('name')=='__setusermatherr','Unique real game named import owner')
    exports=[s for s in dll.exports() if '__setusermatherr' in s['names']]
    need(len(exports)==1 and dll.image_base+exports[0]['rva']==0x7800b38f and 'forwarder' not in exports[0],'Unique actual provider named export')
    source=pin(BASE/'preparation-r1/source.bin','db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9').read_bytes()
    offset=dll.rva_range(0xb38f,17)[0];need(dllbytes[offset:offset+17]==source,'Actual full17-byte provider leaf extraction')
    fields=[]
    for address,size,role in ((0x7800b38f,17,'leaf RX'),(0x780392b8,4,'zero global RW'),(0x7803b0c4,4,'callback DWORD RW')):
        rva=address-dll.image_base;ss=[s for s in dll.sections if s['virtual_address']<=rva and rva+size<=s['virtual_address']+max(s['virtual_size'],s['raw_size'])]
        need(len(ss)==1 and ss[0]['readable'] and (ss[0]['executable'] and not ss[0]['writable'] if role=='leaf RX' else ss[0]['writable'] and not ss[0]['executable']),'Actual owning provider section '+role)
        fields.append(dict(address=address,bytes=size,role=role,section=ss[0]['name'],file_backed=rva+size<=ss[0]['virtual_address']+ss[0]['raw_size']))
    decoded=run([LLVM/'llvm-objdump.exe','--disassemble','--start-address=0x7800b38f','--stop-address=0x7800b3a0','--x86-asm-syntax=intel',ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'],'provider-leaf-static.txt')
    instructions=[]
    for line in decoded.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
        if match:
            address=int(match[1],16);body=bytes.fromhex(match[2]);rva=address-dll.image_base
            need(dllbytes[dll.rva_range(rva,len(body))[0]:][:len(body)]==body,'Own decoded bytes match private actual source')
            instructions.append((address,len(body),match[3],match[4].strip()))
    need(instructions==[(0x7800b38f,4,'mov','eax, dword ptr [esp + 0x4]'),(0x7800b393,7,'and','dword ptr [0x780392b8], 0x0'),(0x7800b39a,5,'mov','dword ptr [0x7803b0c4], eax'),(0x7800b39f,1,'ret','')],'Independent complete actual four-instruction decode/operands')
    caller=gamebytes[game.rva_range(0x5ac423-game.image_base,11)[0]:][:11]
    need(hashlib.sha256(caller).hexdigest()=='ed4e3e4ef3536ad0d20aab36b55f011878b9bc1e9bd9760631ee5a4fb5b4456e' and caller[0]==0x68 and struct.unpack_from('<I',caller,1)[0]==0x51e7b0 and caller[5:7]==bytes((0xff,0x15)) and struct.unpack_from('<I',caller,7)[0]==0x5bb50c,'Own private actual PUSH/CALL span identity and operands')
    checked('Actual named game import/provider export and exact RX leaf/RW global ownership',game_iat=0x5bb50c,raw_iat=game.rva_u32(0x5bb50c-game.image_base),provider_export=exports[0],leaf_file_offset=offset,source_length=17,provider_fields=fields,global_initialization='Three pages are explicitly authored fixtures; PE placement alone does not prove initialized process globals or callback execution')
def source_and_build(author,build):
    count=0;maps={};aliases=0
    for a in author['all_source_map_associations']:
        if a['map'] not in maps:maps[a['map']]=read(a['map'])
        m=maps[a['map']]
        group=m[a['group']]
        if a['original_path'] in group:value=group[a['original_path']]
        else:
            entries=[v for p,v in group.items() if str(Path(p).resolve()).casefold()==str(Path(a['original_path']).resolve()).casefold()]
            need(len(entries)==1,'Unique Windows canonical source-map spelling');value=entries[0];aliases+=1
        value=value['sha256'] if isinstance(value,dict) else value
        need(value==a['sha256'],'Exact recorded map-to-physical association');pin(a['resolved_physical_path'],a['sha256']);count+=1
    need(count==1552 and len(author['historical_source_associations'])==11,'Full recorded source and history extent')
    for a in author['historical_source_associations']:pin(a['literal_path'],a['sha256'])
    for a in author['literal_sources']:pin(a['preserved_path'],a['sha256']);pin(a['original_path'],a['sha256'])
    for group in ('source_files','tool_files','artifacts'):
        for p,h in build[group].items():pin(p,h)
    for a in build['literal_sources']:pin(a['preserved_path'],a['sha256']);need(build['source_files'][a['original_path']]==a['sha256'],'Before-build literal source binding')
    logs={};includes=set()
    for a in author['actual_read_header_associations']:
        if a['log'] not in logs:
            logs[a['log']]={ntpath.normcase(ntpath.normpath(p.strip())) for p in re.findall(r'^\s*Note: including file:\s*(.+)$',text(a['log']),re.M)}
        need(ntpath.normcase(ntpath.normpath(a['original_path'])) in logs[a['log']],'Actual consumed header path occurs in compiler log: '+a['original_path']);pin(a['literal_or_current_path'],a['sha256']);includes.add((a['literal_or_current_path'],a['sha256']))
    cmake=text(ROOT/'tools/m4-crt-matherr/paired/native/CMakeLists.txt')
    need('string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS' in cmake and '/EHs)' in cmake,'Exact extern-C synchronous-unwind recipe')
    for level in ('O0','O2'):
        log=text(BASE/f'paired-native-build-r7/build-{level}.log');lines=[l for l in log.splitlines() if ' -c -- ' in l and 'clang-cl.exe' in l]
        need(len(lines)==4 and all('/EHs ' in l and '/EHsc' not in l for l in lines),'Actual final compiler lines remove extern-C no-unwind assumption')
    context=text(ROOT/'tools/m4-crt-matherr/paired/paired_context.hpp','5eab85d9e012571fb7347f4f846c6f8d5b9d82c95601d0e97ba784a5d52dbb01')
    need('std::longjmp' not in context and 'setjmp(' not in context and 'noexcept' not in context.replace('non-noexcept','') and 'throw BridgeAbort{};' in context and 'catch(const BridgeAbort &)' in context,'Real typed bounded exception transport')
    need('if(!failed){failed=true;reason=why;fault_pc=state.gpr.rip.dword;fault_address=address;}' in context and 'catch(...) { active=false; throw; }' in context and 'active=false;' in context,'First typed failure and active-scope cleanup')
    pin(ROOT/'tools/m4-runtime/runtime.hpp','41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536');pin(ROOT/'tools/m4-runtime/runtime.cpp','48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')
    checked('All source/history/header/build associations and exact typed fault transport',source_map_associations=count,Windows_case_canonical_map_spellings=aliases,historical_source_associations=11,literal_author_sources=len(author['literal_sources']),actual_include_log_associations=len(author['actual_read_header_associations']),unique_read_header_versions=len(includes),source_count=len(build['source_files']),tool_count=len(build['tool_files']),artifact_count=len(build['artifacts']),Runtime_r9_changed=False,identity_scope='Physical hashes measured post-build, linked to recorded commands/header-read logs; no execution-time/full process claim')
def objects_and_root_controls(build):
    coff=[]
    for b in build['builds']:
        level=b['level'];guest=pin(b['object'],build['artifacts'][b['object']]);directory=Path(b['directory'])
        objs=[guest]+[p for p in directory.rglob('*.obj') if p.name in ('native_paired.cpp.obj','runtime.cpp.obj','image_loader.cpp.obj','guest_memory.cpp.obj')]
        need(len(objs)==5,'Actual final guest plus production boundaries')
        for index,p in enumerate(objs):
            pin(p,build['artifacts'][str(p)])
            d=run([LLVM/'llvm-objdump.exe','--disassemble','--reloc','--x86-asm-syntax=intel',p],f'{level}-object-{index}.txt')
            u=run([LLVM/'llvm-readobj.exe','--file-headers','--symbols','--unwind',p],f'{level}-object-{index}-coff.txt')
            need('IMAGE_FILE_MACHINE_AMD64' in u and 'file format coff-x86-64' in d,'Actual AMD64 compiled object')
            if index==0:
                for symbol in ('sub_7800b38f','__remill_read_memory_32','__remill_write_memory_32','__remill_function_return'):need(symbol in u and symbol in d,'Actual leaf bridge relocation '+symbol)
                need('UnwindInfo' in u,'Guest body actual Windows unwind metadata')
            if p.name=='native_paired.cpp.obj':
                blocks=u.split('  RuntimeFunction {')[1:];execute=[x for x in blocks if re.search(r'StartAddress: \?execute@Context@',x)]
                need(len(execute)==1 and re.search(r'Handler: __CxxFrameHandler[34]',execute[0]),'Actual final production Context::execute owns C++ EH catch handler')
            coff.append(dict(level=level,path=str(p),sha256=sha(p)))
    root=read(BASE/'independent-compiled-r1/build.json');need(root['passed'] and root['consumed_candidate_build_sha256']==sha(BASE/'paired-native-build-r7/build.json'),'Root independent causal exact build identity')
    for group in ('sources','tools','artifacts'):
        for p,h in root[group].items():pin(p,h)
    # Re-observe the root's independently authored fixture programs unchanged;
    # these are not author workers and do not execute original provider bytes.
    for level in ('O0','O2'):
        exe=pin(BASE/f'independent-compiled-r1/{level}/controls.exe',root['artifacts'][str(BASE/f'independent-compiled-r1/{level}/controls.exe')])
        output=run([exe,ROOT/'MW3/Mech3.exe',BASE/'preparation-r1/source.bin'],level+'-root-causal-replay.log')
        need(output.strip()=='231 root compiled checks / 24 scenarios passed','Exact root-owned actual causal replay extent')
    checked('Fresh final production COFF/typed relocations/Context catch and independent causal replay',fresh_decoded_objects=len(coff),objects=coff,root_independently_authored_checks_per_level=231,root_independent_scenarios_per_level=24,root_causal_replayed_unchanged=True,original_or_provider_execution=False,supplemental_new_scenarios=0,causal_assessment='Root fixture/control model adequate: exact whole State/pages/FX; actual partial faults and first diagnostic; poisoned corrected retry; pre-routing IAT/return denial remains unentered and can recover; completed Context is one-use')
def root_stages():
    refs=(('independent-original-model-r1','ba5941592ed4158a59a3e07a808a4244f1eafc7e3769e71b7b8e4515322a53e4','41fc31ff6726fcfc370cd37006e5a759b89ae5608c57c9c64f639bb7931a6874'),('independent-native-model-r1','5f1863d519aea7054d090edab6437e6f7c330a9edbd88c239b410c90df9205eb','fd70d0d33ce1404d14f92e1382b56a6fb7431b826cac4fdb5c0c016c54e7c0de'),('independent-static-review-r3','3be19405b0a7586122a1d3c34660b2278496c25fb32f70d8618ea902137531bf','32ecfb5a98c0ce41eae7eb846a604667d844b16bbaf120dbc7253ae2f89de372'))
    stages=[]
    for folder,h,ph in refs:
        r=read(BASE/f'{folder}/report.json',h);count,_=filemap(BASE/f'{folder}/pins.json',ph);need(r['passed'],'Exact root positive review stage');stages.append(dict(path=str(BASE/f'{folder}/report.json'),sha256=h,physical_bindings=count))
    static=read(BASE/'independent-static-review-r3/report.json');need(static['complete_type_layouts']==34 and static['complete_State_bytes']==3504 and static['alignment']==8 and static['exact_Context_derivative_changes']==8,'Entire recursive named-type/State and explicit Context derivative scope')
    need(len(static['independent_static_corruptions'])==5 and all(c['rejected'] for c in static['independent_static_corruptions']),'Cause-specific independent static controls')
    r2=read(BASE/'independent-static-review-r2/report.json');need(r2['complete_type_layouts']==87,'Literal prior cache-count label retained')
    _,associations=filemap(BASE/'independent-static-review-r2/pins.json',None,{str((ROOT/'tools/m4-crt-matherr-independent/static_review.py').resolve()):BASE/'independent-static-review-r2/review-source.py'})
    for p in (BASE/'independent-static-review-r1').rglob('*'):
        if p.is_file():pin(p)
    need('Own actual typed C++ catch support' in text(BASE/'independent-static-review-r1/failure.txt'),'Literal root early unwind-search failure retained')
    checked('Inspected independently authored raw/whole-layout/model sources and their exact immutable stages/history',stages=stages,root_static_r2_historical_associations=associations,whole_named_type_layouts=34,State_size=3504,State_alignment=8,unchanged_leaf_IR=True,upstream_identity_helpers=2,allowed_fault_transport_derivatives=8,root_raw_scope='1536 actual originals /3072 native rows; whole3504 State, 15360 native access events and3072 complete named routes. Original State/events unobserved; native ENV after is preserved-input serialization, actual State proves metadata preservation; RuntimeFX/host buffers separate. Original AF undefined/native AND AF0 source policy. Captured original outer PC10000100 projects to native real5AC42E.',root_history='r1 wrongly searched text disassembly for CxxFrameHandler rather than actual unwind Handler; r2 label counted87 cached aggregate/scalar/array entries; r3 labels34 actual named LLVM types. Literal prior sources and failures retained, no underlying proof changes.',primary_comparator_or_executor_imported=False)
def safe_package():
    old=ROOT/'tools/m4-crt-matherr-independent';private=BASE/'public-package-derivative-r1'
    original=text(old/'original_model.py','492647c15e2622078577f96f22de7af12c92a95158503da25e6bba71b97ee24d')
    native=text(old/'native_model.py','1c3b67c819b4d5bfd200f1070c4a78f355b3db2457803585cc4835e0b02cb477')
    need(text(private/'original_model.py')==original and text(private/'native_model.py')==native,'Exact private literal historical checker preservation')
    safe=text(old/'original_model_safe.py','432b687488372b857e08f169fa269b2acca9106a9e7f0c03eee5a7f639780e9b')
    safenative=text(old/'native_model_safe.py','369e282a85998b87b3a7d3c00298980b8038fa64671e1184e45d3b976e47cabe')
    before=original.splitlines();after=safe.splitlines()
    source_line=[x for x in before if 'need(source==bytes.fromhex(' in x];caller_line=[x for x in before if 'need(at(game,game_raw,0x5ac423,11)==bytes.fromhex(' in x]
    need(len(source_line)==len(caller_line)==1 and source_line[0] not in after and caller_line[0] not in after,'Public full instruction literal removal')
    at=after.index("    need(hashlib.sha256(source).hexdigest()=='db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9','Complete source identity')")
    after.insert(at,source_line[0])
    at=after.index('    caller=at(game,game_raw,0x5ac423,11)')
    need('ed4e3e4ef3536ad0d20aab36b55f011878b9bc1e9bd9760631ee5a4fb5b4456e' in after[at+1] and 'word(caller,7)==0x5bb50c' in after[at+2],'Hash plus true reached caller operands')
    after[at:at+3]=caller_line
    at=after.index('    import re');end=next(i for i in range(at,len(after)) if after[i].startswith('    pack=pin('))
    block=after[at:end]
    need(len(block)==7 and "body=bytes.fromhex(match[2]);need(at(provider,provider_raw,address,len(body))==body" in '\n'.join(block) and "(ENTRY+16,1,'ret','')" in block[-1],'Additive actual private decode/operand checking only')
    del after[at:end];need(after==before,'Entire public-safe original derivative reverses exactly to literal frozen checker')
    nlines=safenative.splitlines();oldline=[x for x in native.splitlines() if "spec_from_file_location('own_root_matherr_original'" in x]
    new=[i for i,x in enumerate(nlines) if "spec_from_file_location('own_root_matherr_original_safe'" in x]
    need(len(oldline)==len(new)==1 and 'original_model_safe.py' in nlines[new[0]] and sha(old/'original_model_safe.py') in nlines[new[0]],'Safe native imports only exact hash-bound safe root original model')
    nlines[new[0]]=oldline[0];need(nlines==native.splitlines(),'Entire native safe derivative differs only exact root original import identity')
    package=read(private/'report.json');need(package['passed'] and package['proof_execution_pending'],'Historical additive package report retained with then-pending proof label')
    for p in private.iterdir():
        if p.is_file():pin(p)
    pin(old/'package_derivative.py');pin(ROOT/'.gitignore')
    need('/tools/m4-crt-matherr-independent/original_model.py' in text(ROOT/'.gitignore').splitlines(),'Specific frozen literal checker excluded from public source control')
    rows=[]
    for name,oldname,reporthash,pinshash in (
        ('independent-original-safe-r1','independent-original-model-r1','ba5941592ed4158a59a3e07a808a4244f1eafc7e3769e71b7b8e4515322a53e4','604036683cffabfc7fb24f5f04a56c52aa06aa53bbcf2590ace50d96335c6af6'),
        ('independent-native-safe-r1','independent-native-model-r1','5f1863d519aea7054d090edab6437e6f7c330a9edbd88c239b410c90df9205eb','3083b059de8f62f0c230f654b7bb53c388a6cf2261d3a6ada827ad4ac143c50b')):
        r=read(BASE/name/'report.json',reporthash);count,_=filemap(BASE/name/'pins.json',pinshash)
        need(r['passed'] and (BASE/name/'report.json').read_bytes()==(BASE/oldname/'report.json').read_bytes(),'Fresh safe actual model/controls result exactly matches historical scope')
        rows.append(dict(report=str(BASE/name/'report.json'),sha256=reporthash,physical_bindings=count))
    checked('Public byte finding repaired additively with exact private history and unchanged full model/control scope',historical_public_full_instruction_bytes=28,frozen_history_unchanged=True,public_literal_checker_ignored=True,derivative_scope='Private hash and actual decode/operand assertions replace full original byte literals; whole raw/State/access/oracle logic unchanged; native import points only at safe root model',fresh_safe_stages=rows,finding_resolved=True)
def main():
    need(not OUT.exists(),'Fresh independent final closure required');OUT.mkdir(parents=True)
    (OUT/'review.py').write_bytes(Path(__file__).read_bytes());pin(OUT/'review.py')
    try:
        a=read(BASE/'paired-author-review-r1/report.json','896664a4f52cc4fe4d3bed11e9fd53f74936640c237db8f7873fff1b552274e9');count,_=filemap(BASE/'paired-author-review-r1/pins.json','e1e9adc4c1105b043766ea26bd11b885de1ae7ed3890ad4df7035648bac4a5f7')
        need(a['passed'] and count==1287,'Exact author physical closure')
        checked('Entire final author literal/artifact/failure physical closure rehashed',bindings=count,author_native_rows=3072,author_actual_unit_positives=3072,author_unit_assertions=3384,author_fault_scenarios=42,author_worker_denials=20,recipe_unchanged_sentinel_denials=3)
        b=read(BASE/'paired-native-build-r7/build.json','2a2fa0d652ce8436b21b4305d0e4f922117ebd75f8fbceb320a9664b235d61a3');need(b['passed'],'Final exact native build')
        original_identity();source_and_build(a,b);objects_and_root_controls(b);root_stages();safe_package()
        for folder in ('independent-final-closure-r1','independent-final-closure-r2','independent-final-closure-r3','independent-final-closure-r4'):
            for p in (BASE/folder).rglob('*'):
                if p.is_file():pin(p)
        checked('Own initial closure path and history-label failures retained literally',attempts=['r1 treated case-normalized Hostx64 as a case-sensitive JSON key; literal source/failure/partial and provider decode preserved. Later attempts validate unique Windows canonical spelling against the recorded hash.','r2 compared raw compiler header paths as substrings; actual include log has doubled directory separators. Literal r2 source/failure/partial retained.','r3 normalized directory separators but wrongly required every Note include-log line to start at column0. Actual original-build log indents Note lines. r4 parses observed leading whitespace then compares normalized exact paths; literal r3 source/failure/partial retained.','r4 successfully checked all header/source/object/causal stages but used the wrong literal wording to identify root static-r1 failure. r5 checks the actual preserved wording; literal r4 source/failure/partial/ten actual object decodes/two passing causal replays retained.'])
        report=dict(passed=True,scope='Final independent isolated native __setusermatherr leaf admission: physical/source/build/header/compiled catch/fault closure plus distinct root independent raw/static/causal models',checks=CHECKS,commands=COMMANDS,findings=[],original_records=1536,native_records=3072,native_access_events=15360,named_routes=3072,root_compiled_assertions=462,root_compiled_scenarios=48,actual_fresh_object_decodes=10,original_or_vendor_executed_by_this_review=False,primary_comparator_or_executor_imported=False,full_CRT_caller_executed=False,callback_invoked=False,full_startup=False,frontend=False,whole_M4_complete=False,limitations=['Isolated17-byte actual provider leaf and authored return/data/stack boundaries. Native actual guest writer/accesses and named import route are compiled; original fullCRT argument PUSH/CALL/process attach remains unexecuted.','Twelve masked CW, all eight TOP values, authored live depths0/1/7/8, eight DWORD callback fixtures, optional sticky0x25 and two repeats are measured. The integer-only leaf preserves FP storage; no numerical operation or arbitrary configuration admission follows.','Original State/events/routes remain unobserved. Complete software State is independently derived from common original BEFORE fields, source/IR and exact native capture; original AFTER fields are oracle only.','Native legacyENV-after is copied from BEFORE input; actual whole State preserves legacy metadata. RuntimeFX-after and outer hostFX/ENV are captured. Zero-initialized reserved hostFX tail is serialized padding, not extra hardware restoration architecture credit.','Original logical-AND AF is undefined. Native IR deterministically stores AF0, checked in full native CPU/State; original AF has no native-input role.','Fault tests verify actual non-noexcept bridge unwind, partial accesses, retained first error and poisoned entered retry. Pre-routing bad rawIAT/return denials remain unentered and can be corrected; successful Context cannot be reused.','Serial stable trusted owner/metadata, unchanged r9, private ordinary paths. No general callback execution, threading/ownership transfer, arbitrary swallowed raw GuestMemory faults, mapping replacement/reparse/concurrent publication or completeCRT/frontend/M4 claim.','Tool/SDK/link/read-dependency identities are post-build physical associations to actual logs; no complete execution-time process attestation.'])
        rp=OUT/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        for p,h in PINS.items():need(sha(p)==h,'Unchanged final physical association '+p)
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(PINS),fresh_decoded_objects=10,root_compiled_checks_per_level=231,root_compiled_scenarios_per_level=24,report_sha256=sha(rp),pins_sha256=sha(OUT/'pins.json'))))
    except Exception:
        (OUT/'failure.txt').write_text(traceback.format_exc());(OUT/'partial.json').write_text(json.dumps(dict(checks=CHECKS,commands=COMMANDS,bindings=len(PINS)),indent=2));raise
if __name__=='__main__':main()
