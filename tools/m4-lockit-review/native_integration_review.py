"""Independent source/resource admission review; this gives no execution credit."""
from __future__ import annotations
import hashlib, importlib.util, json, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=ROOT/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh revision required');out.mkdir(parents=True)
    pins={};counts={}
    def pin(p,h=None):
        p=Path(p).resolve();a=sha(p);need(h is None or h==a,'Exact input '+str(p));pins[str(p)]=a;return p
    def read(p):return json.loads(pin(p).read_bytes())
    def text(p):return pin(p).read_text(encoding='utf-8')
    def emit(n,v):
        p=out/n;p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');pin(p)
    np=ROOT/'reports/m4-lockit-native/preparation-r3';jp=ROOT/'reports/m4-joint-startup124/preparation-r3'
    n=read(np/'report.json');j=read(jp/'report.json');need(n['passed'] and j['passed'],'Passed preparation inputs')
    for p,h in n['files'].items():pin(p,h)
    for p,h in j['generated_sources'].items():pin(p,h)
    need(Path(j['native_include']).resolve()==np.resolve() and Path(j['native_library']).resolve()==np/'registry_library.cpp','Actual combined build source connects current native resources')
    original=ROOT/'reports/m4-lockit-original/original-validation-r2'
    pin(original/'report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3')
    own=read(ROOT/'reports/m4-lockit-review/full-original-r1/report.json');need(own['passed'],'Independent final original compiled/capture gate')
    physical=read(ROOT/'reports/m4-lockit-review/static-r1/four-root-physical.json')
    interfaces=read(ROOT/'reports/m4-lockit-review/source-interface-r2/root-interface-relations.json')
    c=text(np/'lockit_contract.inc');op=text(np/'lockit_operations.inc');lb=text(np/'locale_batch_operations.inc');bh=text(np/'locale_batch_binding.inc');session=text(np/'session_impl.inc')
    def array_bytes(name):
        m=re.search(r'const std::array<std::byte,4096>'+name+r'\{(.*?)\};',c,re.S);need(m,'Exact whole loaded array '+name)
        b=bytes(map(int,re.findall(r'std::byte\{(\d+)\}',m[1])));need(len(b)==4096,'Whole 4096B array');return b
    for address,name in ((0x78145000,'lockit_loaded_page'),(0x78146000,'lockit_loaded_iat_page')):
        p=pin(original/f'post-DllMain-{address:x}-page.bin');need(array_bytes(name)==p.read_bytes(),'Whole final authentic loaded input '+hex(address))
        need((f'p.address==0x{address:x}?lb::{name}') in session,'Actual mapped loaded input branch')
    counts['whole_loaded_input_pages']=2
    need(struct.unpack_from('<I',array_bytes('lockit_loaded_page'),0x658)[0]==2,'Actual final loaded state2')
    need(n['native_DllMain_executed'] is False and not n['guest_CS_native_opaque_copy'],'No native DllMain/raw opaque struct copy claim')
    imports=read(original/'loaded-imports.json');table={i['symbol']:i for i in imports}
    api={name:(int(site,16),int(slot,16),int(raw),int(argc),int(tail)) for site,slot,raw,argc,name,tail in re.findall(r'v.push_back\(\{0x([0-9a-f]+),0x([0-9a-f]+),(\d+),(\d+),"([^"]+)",(\d+)\}\)',c)}
    for name,site,slot in (('EnterCriticalSection',0x7810a30b,0x78146198),('LeaveCriticalSection',0x7810a35e,0x78146184)):
        need(api[name]==(site,slot,table[name]['target'],1,0),'Exact actual original named API interface')
        need(struct.unpack_from('<I',array_bytes('lockit_loaded_iat_page'),slot-0x78146000)[0]==table[name]['target'],'Actual whole input IAT cell')
    counts['actual_named_API_contracts']=2
    im=re.search(r'constexpr LockitInput lockit_inputs\[\]\{(.*?)\};',c,re.S)
    ins=[tuple(map(int,re.findall(r'\d+',row))) for row in re.findall(r'\{([^{}]+)\}',im[1])]
    need(len(ins)==4 and {i[0] for i in ins}=={i['root'] for i in physical},'Exactly four current small roots')
    for i in interfaces:
        row=next(x for x in ins if x[0]==i['root']);need(row[3:]==(i['scratch_frame_offsets']['constructor'],i['scratch_frame_offsets']['destructor']),'Physical CALL scratch frame')
    fm=re.search(r'constexpr MfcRootInput lockit_mfc_inputs\[\]\{(.*?)\};',c,re.S)
    mfc=[tuple(map(int,re.findall(r'\d+',row))) for row in re.findall(r'\{([^{}]+)\}',fm[1])]
    for root in physical:
        for allocation in root['allocations']:need(any(x[0:3]==(root['root'],allocation['CALL_pc'],allocation['requested_size']) for x in mfc),'Physical requested20/24 actual CALL')
    need(len(mfc)==8,'Eight exact new syntactic allocation sites');counts['literal_CALL_scratch_contracts']=8;counts['exact_allocation_size_contracts']=8
    pe_path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638');spec=importlib.util.spec_from_file_location('lockit_review_PE',pe_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    game=module.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    cp=module.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
    spanblock=re.search(r'constexpr SourceSpan lockit_spans\[\]\{(.*?)\};',c,re.S)[1];spans=[]
    for address,size,perm,h in re.findall(r'\{(\d+),(\d+),(\d+),"([0-9a-f]{64})"\}',spanblock):
        address,size,perm=map(int,(address,size,perm));pe=cp if address>=cp.image_base else game;off,_=pe.rva_range(address-pe.image_base,size);need(hashlib.sha256(pe.read(off,size)).hexdigest()==h and perm==5,'Whole literal RX source span');spans.append((address,size,h))
    need(len(spans)==22,'Exact current source RX spans');counts['whole_literal_RX_spans']=len(spans)
    clauses={
        'authentic_initialized_input':('lockit_admitted_||runtime.memory().load<unsigned>({0x78145658})!=2||section_for(0x78145640)','lockit_loaded_page.begin()+0x640,lockit_loaded_page.begin()+0x658'),
        'distinct_native_resource_association':('object->guest=0x78145640;object->generation=++generation_','lifecycle_api("InitializeCriticalSection",0x78146190,0x866ce','::InitializeCriticalSection(&section->native);section->initialized=true;++section->initializes;++sections_initialized_'),
        'actual_recursive_resource_guard':('section->generation!=lockit_generation_','section->initializes!=1||section->deletes','section->depth!=section->enters-section->leaves','section->native.RecursionCount!=LONG(section->depth)','thread!=GetCurrentThreadId()'),
        'source_import_call_admission':('if(!lockit_admitted_||!section_for(0x78145640))deny("Explicit live Lockit resource admission required"','if(!lockit_admitted_||!section_for(0x78145640))deny("Explicit live Lockit resource CALL admission required"','state.gpr.rcx.dword!=frame+(ctor?input->ctor_offset:input->dtor_offset)'),
        'literal_source_return_guard':('w[5]!=frame||w[11]','entry==0x7810a290&&result!=w[7]','w[8]+1:w[8]-1'),
        'semantic_guest24_from_real_native40':('put(4,static_cast<unsigned>(section->native.LockCount));put(8,section->depth);put(12,section->depth?GetCurrentThreadId():0)','preflight_write(0x78145640,24)','std::memcpy(actual.data(),&section->native,40)'),
    }
    for name,clauses_ in clauses.items():
        for clause in clauses_:need(clause in op,'Reviewed source resource clause '+name)
    need('static_assert(sizeof(CRITICAL_SECTION)==40&&alignof(CRITICAL_SECTION)==8)' in lb,'Compiled native layout prerequisite')
    need('api_return(frame,argc,preserve_eax)' in lb,'Explicit bounded VOID guest CPU projection')
    need('runtime.memory().load<unsigned>({frame+4})!=guest' in lb,'Actual source API frame checked immediately before real native call')
    need('::EnterCriticalSection(&section->native)' in lb and '::LeaveCriticalSection(&section->native)' in lb,'Real named Windows resource operations')
    need('while(p.depth)' in lb and '::DeleteCriticalSection(&p.native)' in lb and 'if(live_critical_sections())' in lb,'Recursive release/delete precedes allocation backing cleanup')
    for field in ('lockit_calls','lockit_imports','lockit_images','lockit_cs','lockit_generation','lockit_admitted'):
        need(field+'!='+field+('_' if field not in ('lockit_images','lockit_cs') else '') in bh or field+'!=lockit_native_images_' in bh or field+'!=lockit_source_cs_' in bh,'Private witness guarded '+field)
    need('std::memcmp(lockit_native.data(),&p->native,40)' in bh,'Complete actual native resource image guarded through observer')
    need('binding->live_critical_sections()==4' in session and 'binding->lockit_bootstrap()' in session,'Actual fifth association follows inherited four source CS resources')
    counts['reviewed_resource_admission_invariants']=len(clauses)
    emit('resource-domain.json',{'roots':ins,'allocation_sites':mfc,'source_RX_spans':spans,'named_original_API_contracts':api,'admitted_source_state':2,'guest_CS_bytes':24,'native_CS_bytes':40,'native_DllMain_executed':False,'original_volatile_API_EAX_equivalence_claimed':False,'resource_association':'Measured native InitializeCriticalSection after genuine inherited source bootstrap; genuine current loaded input, not native MSVCP DllMain','causal_controls_pending':True})
    pin(Path(__file__))
    report={'passed':True,'scope':'Independent exact loaded input/source/native resource integration review only; no native execution or initializer acceptance','initializer_credit':False,'counts':counts,'files':pins}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json'),'counts':counts}))
if __name__=='__main__':main(sys.argv[1])
