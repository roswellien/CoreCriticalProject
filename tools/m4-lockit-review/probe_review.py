"""Independent exact COFF/link and genuine scratch Lockit observations audit."""
from collections import Counter
import hashlib, importlib.util, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def expected_function(pc,kind,replay=b'',continuation=None,target=None):
    b=bytearray();rel=[]
    def emit(h):b.extend(bytes.fromhex(h))
    def addr(name,addend=0,typ=6):rel.append((len(b),name,typ));b.extend(struct.pack('<I',addend))
    stores=('a3','890d','8915','891d','8925','892d','8935','893d')
    loads=('a1','8b0d','8b15','8b1d','8b25','8b2d','8b35','8b3d')
    for i,op in enumerate(stores):emit(op);addr('_probe_cpu',i*4)
    emit('c705');addr('_probe_cpu',36);b.extend(struct.pack('<I',pc))
    emit('c705');addr('_probe_kind');b.extend(struct.pack('<I',kind))
    emit('9c8f05');addr('_probe_cpu',32)
    emit('0fae05');addr('_probe_fx');emit('d935');addr('_probe_env');emit('d925');addr('_probe_env')
    emit('e8');addr('_probe_observe',0,0x14)
    emit('0fae0d');addr('_probe_fx');emit('d925');addr('_probe_env')
    emit('ff35');addr('_probe_cpu',32);emit('9d')
    for i,op in enumerate(loads):
        if i==4:continue
        emit(op);addr('_probe_cpu',i*4)
    emit('8b25');addr('_probe_cpu',16);b.extend(replay)
    if continuation or target:emit('ff25');addr(continuation or target)
    return bytes(b),rel

def main(name):
    out=R/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh additive probe audit');out.mkdir(parents=True)
    pins={};counts=Counter()
    def pin(p,h=None):
        p=Path(p).resolve();actual=sha(p);need(h is None or h==actual,'Pinned physical input '+str(p));need(str(p)not in pins or pins[str(p)]==actual,'Immutable input');pins[str(p)]=actual;return p
    def read(p):return json.loads(pin(p).read_bytes())
    def emit(n,v):
        p=out/n;p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');pin(p)
    p=R/'reports/m4-lockit-original/probe-preparation-r2';b=R/'reports/m4-lockit-original/probe-build-r2';e=R/'reports/m4-lockit-original/probe-execution-r1'
    prep=read(p/'report.json');build=read(b/'build.json');validation=read(R/'reports/m4-lockit-original/probe-validation-r1/report.json')
    need(prep['passed'] and build['passed'] and validation['passed'],'Authentic prepared, compiled and original validation gates')
    need(prep['snapshot_bytes']==12964 and validation['snapshot_bytes']==12964,'Actual compiled fixed snapshot ABI')
    need(build['preparation_sha256']==sha(p/'report.json') and validation['build_sha256']==sha(b/'build.json') and validation['preparation_sha256']==sha(p/'report.json'),'Direct exact producer bindings')
    for q,h in validation['files'].items():pin(q,h)
    worker_path=pin(build['worker'],build['worker_sha256'])
    spec=importlib.util.spec_from_file_location('independent_scratch_PE',pin(R/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
    worker=PE.PEImage(worker_path.read_bytes());cp=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
    need(worker.machine==0x14c and worker.image_base==0x400000,'Actual fixed i386 observer worker')
    def physical(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    def worker_exec(a):
        return any(s['executable'] and worker.image_base+s['virtual_address']<=a<worker.image_base+s['virtual_address']+s['raw_size'] for s in worker.sections)
    obj=pin(b/'observer.obj');spec=importlib.util.spec_from_file_location('independent_COFF_metadata_parser',pin(R/'tools/m4-fs-source/observer_attribution.py'));C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C);symbols,sections=C.parse_coff(obj.read_bytes())
    need(any(str(obj).lower()==str(x).lower() for command in build['commands'] for x in command['arguments']),'Actual observer object named in final compiler/link invocation')
    hooks=read(p/'hook-bindings.json');need(len(hooks)==4,'Exactly four provider observation spans')
    observations=read(e/'observations.json');run=read(e/'run.json');exit_=read(e/'exit.json')
    need(exit_['exit_code']==0 and (R/exit_['worker']).resolve()==worker_path,'Actual zero-exit worker binding')
    need(observations['process_bits']==32 and observations['post_DllMain_state']==2 and not observations['state_seeded'],'Genuine post-DllMain initialized domain')
    need(run['passed'] and run['original_executed'] and run['restored'] and not run['state_seeded'] and run['snapshot_bytes']==12964 and run['snapshots']==18,'Actual bounded balanced scratch execution')
    boot={};final={}
    for page in (0x7810A000,0x78145000,0x78146000):
        boot[page]=pin(e/f'post-DllMain-{page:08x}-page.bin').read_bytes();final[page]=pin(e/f'after-restored-{page:08x}-page.bin').read_bytes()
        need(len(boot[page])==4096 and final[page]==boot[page],'Whole provider page restored after balanced execution')
    need(physical(cp,0x7810A000,4096)==boot[0x7810A000],'Entire post-loader code page equals exact PE bytes at preferred base')
    stateCS=pin(e/'state-and-CS.bin').read_bytes();need(len(stateCS)==28 and stateCS==boot[0x78145000][0x640:0x65C],'Complete captured post-loader state/CS input')
    initial=struct.unpack('<7I',stateCS);need(initial[:6]==tuple(observations['critical_section']) and initial[6]==2 and initial[2:4]==(0,0),'Actual unheld CS and state2 identity')
    raw=pin(e/'snapshots.bin').read_bytes();need(len(raw)==18*12964,'Complete physical snapshot archive')
    records=[raw[i*12964:(i+1)*12964] for i in range(18)]
    def row(x):return dict(words=struct.unpack_from('<8I',x),cpu=struct.unpack_from('<10I',x,32),frame=struct.unpack_from('<8I',x,612),cs=struct.unpack_from('<6I',x,644),fx=x[72:584],env=x[584:612],scratch=x[12956:12964])
    rr=[row(x) for x in records];patched=records[0][668:4764]
    functions=[];resolved={}
    defs={v['name']:v for v in symbols.values() if v['storage']==2 and v['section']>0}
    for h in hooks:
        need(physical(cp,h['pc'],h['size'])==bytes.fromhex(h['raw']),'Exact entire original source broker span')
        i=h['pc']-0x7810A000;span=patched[i:i+h['size']]
        need(span[0]==0xE9 and span[5:]==b'\x90'*(h['size']-5),'Exactly declared E9/NOP observation span')
        target=(h['pc']+5+int.from_bytes(span[1:5],'little',signed=True))&0xFFFFFFFF
        need(worker_exec(target),'Actual provider broker targets linked owned worker code')
        continuation='_probe_continue_'+format(h['pc'],'x') if h['continuation'] else None
        functions.append((h['name'],h['pc'],h['kind'],bytes.fromhex(h['replay']),continuation,None,target))
    for name,kind,cell,symbol in (('probe_api_Enter',1,0x78146198,'_probe_actual_Enter'),('probe_api_Leave',4,0x78146184,'_probe_actual_Leave')):
        target=struct.unpack_from('<I',records[0],668+2*4096+cell-0x78146000)[0]
        need(worker_exec(target),'Actual modified provider IAT points to linked own API wrapper')
        functions.append((name,0,kind,b'',None,symbol,target))
    for name,pc,kind,replay,continuation,target,linked in functions:
        definition=defs['_'+name];section=sections[definition['section']];expected,rel=expected_function(pc,kind,replay,continuation,target)
        actual=section['bytes'][definition['value']:definition['value']+len(expected)]
        need(actual==expected,'Every compiled preservation/replay instruction and addend '+name)
        actualrel=[(o-definition['value'],n,t) for o,n,t in section['relocations'] if definition['value']<=o<definition['value']+len(expected)]
        need(actualrel==rel,'Exact complete COFF relocation table '+name)
        linkedbytes=physical(worker,linked,len(expected));normalized=bytearray(linkedbytes)
        for offset,symbol,typ in rel:
            addend=struct.unpack_from('<I',expected,offset)[0];value=struct.unpack_from('<I',linkedbytes,offset)[0]
            address=(value-addend)&0xFFFFFFFF if typ==6 else (linked+offset+4+value-addend)&0xFFFFFFFF
            need(symbol not in resolved or resolved[symbol]==address,'Consistent whole linked symbol relocation '+symbol);resolved[symbol]=address
            normalized[offset:offset+4]=expected[offset:offset+4]
        need(bytes(normalized)==expected,'Every final linked observer byte outside actual relocations '+name)
        if continuation:need(struct.unpack('<I',physical(worker,resolved[continuation],4))[0]==pc+len(replay),'Linked exact original continuation DWORD')
        counts['compiled_and_linked_functions']+=1;counts['compiled_function_bytes']+=len(expected);counts['compiled_relocations']+=len(rel)
    need(resolved['_probe_fx']%16==0 and worker_exec(resolved['_probe_observe']),'Actual aligned FX storage and executable observer callback')
    expected_kinds=[0,1,2,3,4,5,0,1,2,0,1,2,3,4,5,3,4,5]
    expected_depths=[0,0,1,1,1,0,0,0,1,1,1,2,2,2,1,1,1,0]
    patches=[(h['pc']-0x7810A000,h['size']) for h in hooks]
    masked=bytearray(patched)
    for offset,n in patches:masked[offset:offset+n]=boot[0x7810A000][offset:offset+n]
    need(bytes(masked)==boot[0x7810A000],'Only four exact patches change entire code page')
    imported={x['cell']:x for x in observations['imports']}
    for index,(x,r) in enumerate(zip(records,rr)):
        w,c,f,cs=r['words'],r['cpu'],r['frame'],r['cs'];depth=expected_depths[index]
        need(w[0:2]==(1,index) and w[2]==(0 if index<6 else 1) and w[3]==expected_kinds[index] and w[4]==observations['thread_id'] and w[5]==2,'Exact authentic ordered source/interface boundary')
        obj=run['scratch']+(4 if 9<=index<=14 else 0);need(w[6]==obj and r['scratch']==bytes(8),'Actual genuine scratch identity and unchanged complete8B object')
        need(cs[0]==initial[0] and cs[4:]==initial[4:6] and cs[1]==(0xFFFFFFFE if depth else 0xFFFFFFFF) and cs[2]==depth and cs[3]==(observations['thread_id'] if depth else 0),'Complete actual original serial recursive CS bytes')
        need(c[9]==(run['actual_Enter'] if w[3]==1 else run['actual_Leave'] if w[3]==4 else {0:0x7810A290,2:0x7810A311,3:0x7810A350,5:0x7810A364}[w[3]]),'Exact source/interface PC labels')
        if w[3] in (1,4):need(w[7]==c[9] and f[:2]==((0x7810A311 if w[3]==1 else 0x7810A364),0x78145640),'Actual source API caller return/argument frame')
        else:need(w[7]==0,'Only API interfaces have named target field')
        for page_no,page in enumerate((0x7810A000,0x78145000,0x78146000)):
            actual=x[668+page_no*4096:668+(page_no+1)*4096];expected=bytearray(boot[page])
            if page_no==0:expected[:]=patched
            elif page_no==1:expected[0x640:0x658]=x[644:668]
            else:
                for cell,name in ((0x78146198,'probe_api_Enter'),(0x78146184,'probe_api_Leave')):
                    target=next(item[-1] for item in functions if item[0]==name);struct.pack_into('<I',expected,cell-page,target)
            need(actual==bytes(expected),'Every whole provider page with only exact observed relation')
            counts['whole_provider_page_relations']+=1
        counts['actual_CPU_FX_ENV_boundaries']+=1
    for start in range(0,18,3):
        a,m,z=rr[start:start+3];ctor=a['words'][3]==0;F=a['cpu'][4]
        need(m['cpu'][4]==F-(16 if ctor else 8) and z['cpu'][4]==F-(8 if ctor else 0),'Actual full caller/API/epilogue stack geometry')
        need(a['fx']==m['fx']==z['fx'] and a['env']==m['env']==z['env'],'Every512B FX and28B ENV equal across genuine source/API/return boundary')
        for reg in (3,5,6):need(a['cpu'][reg]==m['cpu'][reg]==z['cpu'][reg],'Genuine preserved EBX/EBP/ESI across actual provider call')
        if ctor:
            need(a['cpu'][1]==a['words'][6] and m['cpu'][7]==z['cpu'][7]==a['cpu'][1],'Literal saved EDI retains original ECX')
            need(m['frame'][2:4]==(a['cpu'][7],a['cpu'][6]) and m['frame'][4]==a['frame'][0] and z['frame'][:3]==(a['cpu'][7],a['cpu'][6],a['frame'][0]),'Actual complete original saved-register/caller frame')
        else:
            need(a['cpu'][7]==m['cpu'][7]==z['cpu'][7] and m['frame'][2]==a['frame'][0] and z['frame']==a['frame'],'Actual genuine destructor caller frame/nonvolatile EDI unchanged')
        counts['full_FX_ENV_triple_relations']+=1;counts['actual_API_frame_relations']+=1
    for basename,base in (('kernel32',next(i['declared_base'] for i in imported.values() if i['library']=='KERNEL32.dll')),('ntdll',next(i['actual_owner_base'] for i in imported.values() if i['actual_owner_path'].lower().endswith('/ntdll.dll')))):
        pe=PE.PEImage(pin(e/(basename+'-image.bin')).read_bytes());need(pe.machine==0x14C,'Actual copied x86 Windows provider')
        exports={n:x for x in pe.exports() for n in x['names']}
        for i in imported.values():
            if basename=='kernel32' and i['library']=='KERNEL32.dll':
                named=exports[i['symbol']]
                if 'forwarder' not in named:need(base+named['rva']==i['target'],'Exact direct Windows named export')
                else:need(named['forwarder'].startswith('NTDLL.'),'Exact bounded Windows forwarder owner')
            elif basename=='ntdll' and i['actual_owner_base']==base:
                need(any(base+x['rva']==i['target'] for x in exports.values()),'Actual named owner export target')
        counts['physical_x86_Windows_provider_images']+=1
    pin(__file__)
    emit('compiled-linked-symbols.json',resolved)
    report=dict(passed=True,scope='Independent exact original observer COFF/final-linked bytes and18 genuine initialized scratch source/API interface boundaries; no game initializer credit',counts=dict(counts),preparation_sha256=sha(p/'report.json'),build_sha256=sha(b/'build.json'),validation_sha256=sha(R/'reports/m4-lockit-original/probe-validation-r1/report.json'),post_DllMain_state=2,snapshot_bytes=12964,balanced_pairs=3,recursive_max_depth=2,constructor_boundary='Actual entry, API-wrapper entry before literal same-frame tailJMP, actual returned pre-epilogue7810A311; outer returned EAXscratch only validated by worker; no actual postRETCPU capture',destructor_boundary='Actual entry, API-wrapper entry before literal same-frame tailJMP, actual preRET7810A364',PC_interface_labels_not_API_body_stepping=True,source_stack_whole_page_transparency_claimed=False,genuine_lazy_initialization_observed=False,initializer_credit=0,files=pins)
    emit('report.json',report);print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
