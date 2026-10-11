"""Bounded independent source/input/build review before the native cached-root smoke."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R/'tools/analysis'))
from pe import PEImage
PINS = {}
PSHA = '55aa6aadb104ebdcda3a1e1a1fb6c53b1a8951da177e5ba4b3e9b25f31a97212'
BSHA = '7558739f895205601dcbc1574754e1907ab3639d57ab871b743b92d8b7bb3938'
def need(x, why):
    if not x: raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def pin(p, h=None):
    p = Path(p).resolve(); need(p.suffix.lower() not in ('.mwb','.zip'),'No archive reader')
    v = sha(p); need(h is None or h == v, 'Physical identity '+str(p)); need(str(p) not in PINS or PINS[str(p)] == v,'Stable identity'); PINS[str(p)] = v; return p
def load(p,h=None): return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,pin(path)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def main(name):
    out=R/'reports/m4-tree-review'/name; need(not out.exists(),'Additive owned output')
    prep=R/'reports/m4-mfc1168-native/fixture-preparation-r2'; p=load(prep/'report.json',PSHA)
    bp=R/'reports/m4-mfc1168-native/fixture-build-r3/build.json'; b=load(bp,BSHA)
    need(p['passed'] and b['passed'] and b['preparation_sha256']==PSHA and Path(b['preparation']).resolve()==(prep/'report.json').resolve(),'Exact current actual preparation/build')
    for report in (p,b):
        for map_name in ('files','artifacts'):
            for path,h in report.get(map_name,{}).items(): pin(path,h)
    need(p['counts']==dict(literal_entries=13,literal_instructions=142,causal_operands=113,borrowed_backings=5,borrowed_CS24=1,named_APIs=4,current_native_CS40=1,current_host_TLS_associations=1),'Finite current source/resource scope')
    need(not p['native_executed'] and not b['native_executed'] and p['initializer_credit']==b['initializer_credit']==0,'No execution or acceptance credit')
    orig=load(p['original_validation'],p['original_validation_sha256']); need(orig['passed'],'Genuine current finite source input')
    source=load(Path(p['original_validation']).parent/'source-derivations.json')
    contracts=load(Path(p['native_contracts']).parent/'contracts.json')
    lift=load(p['lifts'],p['lifts_sha256']); need(lift['passed'] and len(lift['source_bodies'])==13,'Frozen genuine-source literal lifts')
    text=pin(prep/'fixture.cpp').read_text(); need(text==pin(R/'tools/m4-mfc1168-native/fixture_v2.cpp').read_text(),'Exact current compiled fixture source')
    for fragment in ('sizeof(State)==3504&&sizeof(Cpu32)==40&&sizeof(CRITICAL_SECTION)==40',
        'r.domain()==Domain::admitted_game','context','s.gpr.rip.dword==e.pc&&address==e.address&&width==e.width&&writing==bool(e.writing)',
        'f.site==spec.call_site&&f.frame==s.gpr.rsp.dword','iat.pc==spec.site&&iat.writing==0&&iat.width==4&&iat.value==target',
        'f.site==0x5f4010b0&&target==0x5f4010b5&&s.gpr.rsp.dword==f.frame-12',
        'GetCurrentThreadId()==host_thread&&TLS_live&&CS_live','TlsAlloc()','TlsSetValue(host_TLS,host_thread_backing.data())',
        'p==host_thread_backing.data()','x==host_thread_backing','InitializeCriticalSection(&CS)',
        'EnterCriticalSection(&CS)','LeaveCriticalSection(&CS)','CS.RecursionCount==CS_depth',
        'raw==1252','mf::body(target)','frames.empty()&&!CS_depth',
        'r.register_translation({{0x5ae3e4},{Abi::Cdecl,0,true},&native_root',
        'r.freeze_registry();Context c(r,blocks);r.invoke({0x5ae3e4})',
        'r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned()',
        'TlsFree(host_TLS)','DeleteCriticalSection(&CS)'):
        need(fragment in text,'Explicit registered source/resource prerequisite '+fragment)
    need(text.index('EnterCriticalSection(&CS)') < text.index('CS_depth=1;CS_transport()')
        and text.index('LeaveCriticalSection(&CS);CS_depth=0;CS_transport()')>0,
        'Typed guest CS semantics follow actual native resource operations')
    need('EAX0, ECX/EDX/flags retained' in text,'Explicit volatile guest ABI representative scope')
    pack=pin(p['input_pack']).read_bytes(); need(pack[:8]==b'M4MFCNAT','Exact BEFORE-only pack magic')
    count=struct.unpack_from('<I',pack,8)[0]; need(count==len(p['layout'])==284,'Whole finite borrowed/provider input extent')
    at=12; blocks=[]
    for row in p['layout']:
        address,size,rights=struct.unpack_from('<3I',pack,at); at+=12; raw=pack[at:at+size]; at+=size
        need((address,size,rights)==(row['address'],row['size'],row['permissions']) and len(raw)==size
             and hashlib.sha256(raw).hexdigest()==row['initial_sha256'],'Whole own input backing and rights')
        need(all(address>=a+n or address+size<=a for a,n in blocks),'No overlapping borrowed input identity'); blocks.append((address,size))
        role=row['role']; base=R/'reports/m4-mfc1168-probe/execution-r6/trace'
        if role in ('MFC-loaded-before','CRT-loaded-before'):
            module=role.split('-')[0]; need(raw==pin(base/f'BEFORE/{module}/{address}.bin').read_bytes(),'Whole genuine provider BEFORE page')
        elif role.startswith('Borrowed ') and role!='Borrowed initialized opaque guest CS24':
            need(raw==pin(base/f'BEFORE/domain/{role[9:]}/bytes.bin').read_bytes(),'Whole genuine borrowed BEFORE backing')
        elif role=='Borrowed initialized opaque guest CS24':
            need(size==24 and raw==pin(base/'BEFORE/CRT-codepage-lock/bytes.bin').read_bytes(),'Opaque borrowed guest24 input stays distinct from native40')
        elif role=='Coherent genuine root TEB8192':
            need(size==8192 and raw==pin(base/'root-TEB-before-pages.bin').read_bytes(),'Coherent whole genuine TEB input')
        elif role=='Whole genuine source stack65536':
            need(size==65536 and raw==pin(base/'stack-before.bin').read_bytes(),'Whole genuine BEFORE source stack')
        elif role=='Game-loaded-before':
            need(raw==pin(base/f'BEFORE/game-physical/{address}.bin').read_bytes(),'Whole genuine game BEFORE page')
        else: raise ValueError('Unclassified finite backing '+role)
    need(at==len(pack),'Complete exact input pack')
    C=mod(R/'tools/m4-tree-review/amd64_coff.py','mfc_native_coff')
    links=[]; bodies=[]
    for level in ('O0','O2'):
        header=pin(prep/f'fixture_spec_{level}.hpp').read_text(); w=b['workers'][level]
        image=PEImage(pin(w['path'],w['sha256']).read_bytes()); folder=Path(w['path']).parent
        need(pin(folder/'fixture_spec.hpp').read_text()==header,'Actual consumed level header exact copy')
        m=re.search(r'array<AccessSpec,113>access_order\{\{(.*?)\}\};',header); need(m,'Current exact causal array')
        rows=[tuple(map(int,q)) for q in re.findall(r'\{(\d+)U,(\d+)U,(\d+)U,(\d+)U\}',m.group(1))]
        need(rows==[(pc,address,width,int(write)) for pc,address,_,width,write in source['accesses']],'All113 source-authored operand identities; values are not compiled inputs')
        need(p['objects'][level]==[q['objects'][level]['path'] for q in lift['source_bodies'].values()],'Exact thirteen current literal objects')
        graph=pin(folder/'build.ninja').read_text(); line=next(x for x in graph.splitlines() if x.startswith('build '+Path(w['path']).name+': CXX_EXECUTABLE_LINKER'))
        decode=lambda s:s.replace('$:',':').replace('$ ',' ')
        linked={str((folder/Path(decode(x))).resolve()).casefold() for x in line.split(' ',3)[3].split(' |')[0].split(' ') if x.endswith(('.obj','.lib'))}
        for body in lift['source_bodies'].values():
            q=body['objects'][level]; obj=pin(q['path'],q['sha256']); need(str(obj).casefold() in linked,'Actual linker consumes literal object')
            symbols,sections=C.parse(obj.read_bytes()); raw,relocs=C.function(symbols,sections,body['symbol']+'_body'); candidates=C.linked_candidates(image,raw,relocs)
            need(len(candidates)==1,'Unique whole literal linked body excluding exact relocation DWORDs')
            address,actual=candidates[0]; bodies.append(dict(level=level,entry=body['entry'],object=str(obj),linked_address=address,
                whole_function_bytes=len(raw),relocation_DWORDs=len(relocs),raw_sha256=hashlib.sha256(raw).hexdigest(),linked_sha256=hashlib.sha256(actual).hexdigest()))
        need('/showIncludes' in graph and str(prep/'fixture.cpp').replace('\\','/') in graph.replace('$:',':').replace('\\','/'),'Actual fixture source/include compiler graph')
        need(len(linked)==17,'Thirteen literal and four actually compiled source objects')
        need(all(command['exit_code']==0 for command in b['commands']),'Actual successful two-level compiler/linker stages')
        links.append(dict(level=level,literal_objects=13,compiled_sources=4,linked_inputs=17,worker_sha256=w['sha256']))
    pin(__file__); pin(R/'tools/analysis/pe.py'); pin(sys.executable)
    out.mkdir(); q=out/'whole-literal-link-observations.json'; q.write_text(json.dumps(bodies,indent=2)+'\n'); pin(q)
    report=dict(passed=True,preparation_sha256=PSHA,build_sha256=BSHA,levels=links,
        causal_operand_identity_joins=226,whole_BEFORE_input_backings=284,whole_literal_linked_bodies=26,
        initialized_owned_CS40_prerequisite=True,current_host_TLS_association_prerequisite=True,
        original_borrowed_guest_resources_are_native_resources=False,original_AFTER_seed=False,
        initializer_credit=0,native_root_executed=False,archive_reader_opened=False,
        scope='Independent bounded smoke prelaunch review only. Actual immutable inputs and build graph, unique whole literal linked bytes with relocation DWORDs declared, '
              'registered Runtime route and finite source/resource guards are authenticated. Final relocation-target/body semantics, actual resource lifetimes, source State/backing equality, '
              'caller hardware restoration, refusals and full broad-family applicability require their separate fresh execution/proofs. No general TLS/WinAPI/provider initialization credit.',files=PINS)
    q=out/'report.json'; q.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),files=len(PINS))))
if __name__=='__main__': main(sys.argv[1])
