"""Bounded native resource smoke admission: source, typed BEFORE relocation, link."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, subprocess, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
PSHA='bc56a951d2655876866fc8a75564e002fd754adb7a429a6a27df9e71b8ed97b1'
BSHA='4eeaa57715d2e4253a3ef02a6e422d838112ef80791418dd013b3a353bc93e69'
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive read');a=sha(p)
    need(h is None or h==a,'Physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable physical input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def module(p,name):
    s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def pack(p):
    raw=pin(p).read_bytes();need(raw[:8]==b'M4MFCNAT','BEFORE-only input magic');count=struct.unpack_from('<I',raw,8)[0];at=12;rows=[]
    for _ in range(count):
        a,n,r=struct.unpack_from('<3I',raw,at);at+=12;b=raw[at:at+n];at+=n
        need(n and len(b)==n and a+n<=2**32,'Whole bounded guest extent');rows.append(dict(address=a,size=n,permissions=r,bytes=b))
    need(at==len(raw),'No omitted input bytes');return rows
def main(name):
    out=R/'reports/m4-tree-review'/name;need(re.fullmatch('mfc1168-resource-prelaunch-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned review')
    folder=R/'reports/m4-mfc1168-native/resource-preparation-r3';p=read(folder/'report.json',PSHA)
    build=R/'reports/m4-mfc1168-native/resource-build-r3';b=read(build/'build.json',BSHA)
    need(p['passed']and b['passed']and b['preparation_sha256']==PSHA and Path(b['preparation']).resolve()==(folder/'report.json').resolve(),'Exact final resource build')
    for report in(p,b):
        need(not report['native_executed']and report['initializer_credit']==0,'No prior execution or initializer credit')
        for key in('files','artifacts'):
            for f,h in report.get(key,{}).items():pin(f,h)
    parent=read(R/'reports/m4-mfc1168-native/fixture-preparation-r2/report.json','55aa6aadb104ebdcda3a1e1a1fb6c53b1a8951da177e5ba4b3e9b25f31a97212')
    alias=read(p['alias_review'],'3347e59191d21bd78046ec2722c3e62706d9580cae382a3edfc00d99325d143d')
    need(alias['passed']and not alias['connected_same_address_admitted'],'Explicit independently reviewed connected alias exclusion')
    a=read(Path(p['alias_review']).parent/'alias-domain.json');proof=read(p['relocation_proof']);contracts=read(p['relocated_contracts'])
    original_contracts=read(Path(p['native_contracts']).parent/'contracts.json')
    need(len(proof['owners'])==5 and len(proof['pointer_cells'])==6 and proof['complete_genuine_BEFORE_only']
         and not proof['arbitrary_equal_integer_replacement'],'Finite typed relocation inventory')
    def relocated(address):
        for owner in proof['owners']:
            if owner['old']<=address<owner['old']+owner['extent']:return owner['new']+address-owner['old']
        return address
    need(proof['owners']==[dict(role=x['role'],old=x['guest'],new=0x33001000+i*0x1000,extent=x['extent'])
                               for i,x in enumerate(original_contracts['borrowed_backings'])],'Exact five genuine borrowed roles and capacities')
    expected_cells=[dict(cell=x['cell'],new_cell=relocated(x['cell']),role=x['role'],old_target=x['target'],new_target=relocated(x['target']),scope=x['scope'])for x in a['typed_pointer_cells']]
    need(proof['pointer_cells']==expected_cells,'All and only six independently typed pointer cells')
    old=pack(parent['input_pack']);new=pack(p['input_pack']);need(len(old)==len(new)==len(p['layout'])==284,'Complete declared input blocks')
    rewritten=set();observations=[]
    for before,after,layout in zip(old,new,p['layout']):
        need((after['address'],after['size'],after['permissions'])==(layout['address'],layout['size'],layout['permissions']),'Whole current layout identity')
        need(after['size']==before['size']and after['permissions']==before['permissions']and after['address']==relocated(before['address']),'Only declared whole-role address relocation')
        expected=bytearray(before['bytes']);changed=[]
        for cell in expected_cells:
            if before['address']<=cell['cell']and cell['cell']+4<=before['address']+before['size']:
                at=cell['cell']-before['address'];need(struct.unpack_from('<I',expected,at)[0]==cell['old_target'],'Genuine BEFORE pointer value')
                struct.pack_into('<I',expected,at,cell['new_target']);rewritten.add(cell['cell']);changed.append(cell['cell'])
        need(bytes(expected)==after['bytes']and hashlib.sha256(after['bytes']).hexdigest()==layout['initial_sha256'],'Every complete BEFORE input byte equals own original except exact typed cells')
        need(all(after['address']>=x['address']+x['size']or after['address']+after['size']<=x['address']for x in new if x is not after),'No relocated block aliases')
        observations.append(dict(address=after['address'],role=layout['role'],size=after['size'],typed_original_cells=changed,before_sha256=hashlib.sha256(before['bytes']).hexdigest(),current_sha256=layout['initial_sha256']))
    need(rewritten==set(x['cell']for x in expected_cells),'All six exact rewrites cover whole current inputs')
    need([(x['role'],x['guest'],x['extent'])for x in contracts['borrowed_backings']]==[(x['role'],x['new'],x['extent'])for x in proof['owners']],'Current borrowed capacities use distinct addresses')
    text=pin(folder/'fixture.cpp').read_text();witness=pin(folder/'resource_witness.hpp').read_text();asm=pin(folder/'hardware_boundary.s').read_text()
    need(text==pin(R/'tools/m4-mfc1168-native/fixture_resource_v3.cpp').read_text()and witness==pin(R/'tools/m4-mfc1168-native/resource_witness.hpp').read_text()and asm==pin(R/'tools/m4-mfc1168-native/hardware_boundary.s').read_text(),'Exact compiler-consumed fixture resource and assembly source')
    source=read(Path(p['original_validation']).parent/'source-derivations.json')
    required=('r.domain()==Domain::admitted_game','GetCurrentThreadId()==host_thread&&TLS_live&&CS_live',
      's.gpr.rip.dword==e.pc&&address==e.address&&width==e.width&&writing==bool(e.writing)',
      'p==host_thread_backing.data()','x==host_thread_backing','raw==1252',
      'f.site==0x5f4010b0&&target==0x5f4010b5&&s.gpr.rsp.dword==f.frame-12',
      'CS.RecursionCount<=1','if(CS.RecursionCount)mf_LeaveCriticalSection(&CS)',
      'mf_TlsSetValue(host_TLS,nullptr)&&mf_TlsGetValue(host_TLS)==nullptr','mf_TlsFree(host_TLS)',
      'CS.RecursionCount==CS_depth','CS.OwningThread',
      'r.register_translation({{0x5ae3e4},{Abi::Cdecl,0,true},&native_root','r.freeze_registry();Context c(r,blocks)',
      'std::equal(bytes.begin(),bytes.begin()+span.size,span.bytes.begin())','Unobserved source branch/callback is denied',
      'f.reason()==FaultReason::poisoned','c.checkpoint("retry/before")','c.checkpoint("retry/after")')
    for x in required:need(x in text,'Finite source/resource/refusal prerequisite '+x)
    for x in('c.accesses.size()*sizeof(Access)','c.APIs.size()*sizeof(ApiRecord)','c.frames.size()*sizeof(Frame)',
             '"/nativeCS40.bin"','"/native-thread-mirror.bin"','"/routes.bin"','"/resource-context.bin"',
             'private_dump("retry/before")','private_dump("retry/after")'):
        need(x in text,'Complete actual private retry witness source '+x)
    need(text.index('r->invoke({0x5ae3e4})')<text.index('c.finish()')<text.index('catch(const std::exception&e)'), 'Guarded invocation and cleanup caught inside hardware boundary')
    need(text.index('Context c(r,blocks)')<text.index('mfc_hardware_call(&r,hardware.data())'),'Constructor/resource bootstrap explicitly outside measured invocation boundary')
    for mode in range(1,13):need('control_mode=='+str(mode)in text,'Actual finite mutation case '+str(mode))
    need('0x5f4053fe'in text and 'r.memory().protect({mf::CS_pointer},Permissions::read)'in text,'Meaningful cold target and actual guest CS permission mutations')
    need(asm.index('fxsave64 0(%rbx)')<asm.index('callq mfc_invoke_guarded')<asm.index('fxsave64 544(%rbx)')<asm.index('fxrstor64 0(%rbx)')<asm.index('fxsave64 1088(%rbx)'),'Exact immediate hardware before/unrestored/restored observation timing')
    need(asm.count('fnstenv')==asm.count('fldenv')==3 and 'fldenv 512(%rbx)'in asm,'Complete own-caller ENV restoration and nondestructive observations')
    for name_ in('TlsAlloc','TlsSetValue','TlsGetValue','TlsFree','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection','GetACP'):
        need('reinterpret_cast<void*>(&'+name_+')'in witness,'Actual named native API function pointer '+name_)
    for x in('GetModuleHandleExA','VirtualQuery','MEM_IMAGE','GetModuleFileNameA','m4::sha256(bytes)','-entry64.bin','CS-before40.bin','CS-after40.bin','SetLastError(error)','SetLastError(actual_error)'):
        need(x in witness,'Physical resource identity and API observation '+x)
    C=module(R/'tools/m4-tree-review/amd64_coff.py','mfc_resource_coff')
    M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','mfc_resource_image')
    lifts=read(p['lifts'],p['lifts_sha256']);linked=[];deps=[]
    ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
    pin(ninja)
    for level,w in b['workers'].items():
        bf=Path(w['path']).parent;image=M.AMD64Image(pin(w['path'],w['sha256']).read_bytes());header=pin(bf/'fixture_spec.hpp').read_text()
        need(header==pin(folder/f'fixture_spec_{level}.hpp').read_text(),'Exact actual consumed level header')
        array=re.search(r'array<AccessSpec,113>access_order\{\{(.*?)\}\};',header);need(array,'Literal causal access inventory')
        rows=[tuple(map(int,v))for v in re.findall(r'\{(\d+)U,(\d+)U,(\d+)U,(\d+)U\}',array[1])]
        need(rows==[(pc,relocated(address),width,int(writing))for pc,address,_,width,writing in source['accesses']],'All113 exact current source operand identities')
        graph=pin(bf/'build.ninja').read_text();line=next(x for x in graph.splitlines()if x.startswith('build '+Path(w['path']).name+': CXX_EXECUTABLE_LINKER'))
        inputs=[str((bf/Path(x.replace('$:',':').replace('$ ',' '))).resolve())for x in line.split(' ',3)[3].split(' |')[0].split(' ')if x.endswith(('.obj','.lib'))]
        need(len(inputs)==18 and set(p['objects'][level])<set(inputs),'Thirteen literal, four compiled and one hardware object linked')
        for body in lifts['source_bodies'].values():
            q=body['objects'][level];obj=pin(q['path'],q['sha256']);symbols,sections=C.parse(obj.read_bytes());raw,relocs=C.function(symbols,sections,body['symbol']+'_body');candidates=C.linked_candidates(image,raw,relocs)
            need(len(candidates)==1,'Unique whole literal linked body with only declared relocation DWORDs');linked.append(dict(level=level,entry=body['entry'],bytes=len(raw),relocations=len(relocs),address=candidates[0][0]))
        symbols,sections=C.parse(pin(build/'hardware_boundary.obj').read_bytes());raw,relocs=C.function(symbols,sections,'mfc_hardware_call');matches=C.linked_candidates(image,raw,relocs)
        need(len(matches)==1 and len(relocs)==1 and relocs[0]['symbol']['name']=='mfc_invoke_guarded','Whole actual hardware function and exact call symbol')
        hardware_address,hardware_bytes=matches[0];call=relocs[0]['offset'];target=hardware_address+call+4+struct.unpack_from('<i',hardware_bytes,call)[0]
        fixture=pin(bf/'CMakeFiles/mfc1168-native.dir/fixture.cpp.obj');symbols,sections=C.parse(fixture.read_bytes());guarded,guarded_relocs=C.function(symbols,sections,'mfc_invoke_guarded');guarded_matches=C.linked_candidates(image,guarded,guarded_relocs)
        need(len(guarded_matches)==1 and guarded_matches[0][0]==target,'Actual final assembly CALL target is whole compiled guarded invocation')
        imports={x['name']for x in symbols.values()if x['section']==0}
        need(all('__imp_'+name_ in imports for name_ in('TlsAlloc','TlsSetValue','TlsGetValue','TlsFree','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection','GetACP')),'All nine named API targets are actual dllimport dependencies')
        db=pin(bf/'.ninja_deps');db_sha=sha(db);result=subprocess.run([str(ninja),'-C',str(bf),'-t','deps'],capture_output=True,creationflags=0x08000000)
        need(result.returncode==0 and sha(db)==db_sha,'Read-only actual compiler dependency database')
        actual_paths=[Path(x.strip())for x in result.stdout.decode().splitlines()if x.startswith('    ')and Path(x.strip()).is_file()]
        need(actual_paths and any(x.resolve()==(folder/'fixture.cpp').resolve()for x in actual_paths)and any(x.resolve()==(bf/'fixture_spec.hpp').resolve()for x in actual_paths),'Actual compiled fixture and header dependency records')
        for x in actual_paths:pin(x)
        for x in inputs:pin(x)
        deps.append(dict(level=level,dependency_database_sha256=db_sha,current_consumed_physical_paths=len(actual_paths),linked_inputs=len(inputs),hardware_function_bytes=len(raw),guarded_invocation_bytes=len(guarded)))
    need(all(c['exit_code']==0 for c in b['commands']),'Actual successful compiler/link commands')
    pin(__file__);pin(sys.executable);out.mkdir()
    for filename,value in [('whole-input-relations.json',observations),('whole-literal-link-observations.json',linked)]:
        q=out/filename;q.write_text(json.dumps(value,indent=2)+'\n');pin(q)
    report=dict(passed=True,preparation_sha256=PSHA,build_sha256=BSHA,alias_review_sha256=p['alias_review_sha256'],
        counts=dict(whole_BEFORE_blocks=284,relocated_borrowed_roles=5,typed_pointer_cells=6,causal_source_operands=226,
                    whole_literal_linked_bodies=26,whole_hardware_and_guarded_invocation_joins=2,planned_refusal_cases_per_level=12),
        levels=deps,archive_reader_opened=False,worker_launched=False,initializer_credit=0,original_AFTER_seed=False,
        historical_compiler_header_contents_proven=False,full_private_vector_retry_conservation_observed=False,
        scope='Independent finite resource prelaunch review only. Whole BEFORE inputs differ only by six independently typed pointer cells and five '
              'disjoint role addresses; literal linker membership, actual consumed dependency database and assembly CALL attribution are bound. '
              'Caller observation surrounds guarded Runtime invocation and cleanup, excluding prior resource construction. Actual exports, executable '
              'page identities, resource API lifetimes, source equivalence, full caller hardware restoration and precise refusal/retry outputs still '
              'require the fresh execution checker. Complete private vectors/resources are authored retry outputs, with actual conservation still pending. No connected '
              'initializer ownership or arbitrary cached/lazy branch admission is credited.',files=PINS)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),files=len(PINS),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
