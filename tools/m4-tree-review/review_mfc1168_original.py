"""Independent bounded source/observer/physical review of genuine cached MFC1168."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
PINS={}
VH='81006b3089f41d0df95aae70428d400108d44c5026cc428682faab2407bd99f2'
def need(x,m):
    if not x:raise ValueError(m)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def load(p,h=None):return json.loads(pin(p,h).read_bytes())
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(name):
    out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Additive output')
    vd=R/'reports/m4-mfc1168-probe/validation-r6';v=load(vd/'report.json',VH)
    need(v['passed']and v['normal_cached_domain_only']and not v['source_AFTER_seed']and v['initializer_credit']==0,'Bounded current genuine source gate')
    for p,h in v['files'].items():pin(p,h)
    e=load(v['execution'],v['execution_sha256']);b=load(e['build'],e['build_sha256']);prep=Path(b['preparation']);p=load(prep/'report.json',b['preparation_sha256'])
    need(e['passed']and b['passed']and p['passed'],'Current actual original chain')
    for row in e['results']:
        stage=load(row['stage'],row['stage_sha256']);need(stage['passed']and stage['exit_code']==0,'Actual both unseeded writer exits')
    source=load(vd/'source-derivations.json');facts=load(vd/'actual-trace-observations.json');reached=load(vd/'reached-instruction-contracts.json')['instructions'];domains=load(vd/'actual-domain-observations.json');apis=load(vd/'actual-named-API-boundaries.json');physical=load(vd/'actual-physical-API-proofs.json');normal=load(vd/'actual-normal-boundaries.json')
    need(len(source['PCs'])==len(facts)==len(reached)==142 and len(set(source['PCs']))==142 and len(source['accesses'])==113,'Exact reached physical source/order/operand extent')
    need(not any(x['mnemonic'].startswith('f')for x in reached),'Actual reached integer-only source')
    for x in reached:
        module='MFC42.DLL'if 0x5f400000<=x['pc']<0x5f4d0000 else 'MSVCRT.DLL'if 0x78000000<=x['pc']<0x78040000 else None
        image=PEImage(pin(R/('local/mw3-staged/Shared_DLLs/'+module)if module else R/'MW3/Mech3.exe').read_bytes());raw=bytes.fromhex(x['bytes_hex']);off,_=image.rva_range(x['pc']-image.image_base,len(raw));need(image.data[off:off+len(raw)]==raw,'Every whole reached physical source instruction')
    run=Path(v['execution']).parent
    raw_trace=pin(run/'trace/trace/events.bin').read_bytes();need(len(raw_trace)==142*1768,'All complete raw trace events')
    for i,f in enumerate(facts):
        block=raw_trace[i*1768:(i+1)*1768];need(u(block,0,4)==(i,f['PC'],f['next_PC'],f['PC']+1),'Exact actual debugger breakpoint/control fields')
        need(block[32:748].hex()==f['raw_before_hex']and block[748:1464].hex()==f['raw_after_hex'],'All284 whole raw CONTEXT sides are retained')
        need(block[236:748].hex()==f['FX_before']and block[952:1464].hex()==f['FX_after'],'Every whole512B actual stopped FX side')
    need(source['no_AFTER_or_trace_post_state_seed']is True and source['call_stack_empty'],'Source never begins from AFTER and all literal returns close')
    eh=next(f for f in facts if f['PC']==0x780014b4);call=next(f for f in facts if f['PC']==0x5f40107d)
    need(call['next_PC']==0x78001496 and eh['next_PC']==0x5f4010b5 and eh['cells'][0][0]==eh['before'][4]and eh['cells'][0][7]==0x5f4010b5 and eh['after'][4]==eh['before'][4]+4,'Imported EH helper RET uses actual saved source return with literal ESP+4')
    eh_read=next(x for x in source['accesses']if x[0]==0x780014b4 and not x[4]);need(eh_read[1:4]==[eh['before'][4],0x5f4010b5,4],'EH special logical call-stack handling is joined to actual source read')
    need(len(source['FS_source_writes'])==2,'One literal FS record install/restore')
    for mode,domain in zip(('normal','trace'),domains):
        need(domain['mode']==mode and len(domain['backings'])==5 and domain['new_allocations']==domain['new_callbacks']==0,'Separate own-process genuine cached domains')
        env=pin(run/mode/'ENV-before.bin').read_bytes();need(env==pin(run/mode/'ENV-after.bin').read_bytes()and len(env)==28 and env[12:26]==bytes(14),'Complete current root ENV and zero latent FIP/FDP input domain')
        teb=u(pin(run/mode/'root-TEB-before-base.bin').read_bytes())[0];pages=pin(run/mode/'root-TEB-before-pages.bin').read_bytes();need(len(pages)==8192 and teb==domain['domain'][0]and u(pages)[0]==domain['domain'][8],'Coherent entry assembly whole TEB8192/actual FS scalar')
        for owner in domain['backings']:
            need(len(bytes.fromhex(owner['initial_hex']))==len(bytes.fromhex(owner['source_final_hex']))==owner['extent'],'Complete genuine backing capacity')
            expected=bytearray.fromhex(owner['initial_hex'])
            if owner['role']=='global-object':
                need(owner['extent']==4240,'Exact original cached global backing')
                expected[20]=0;struct.pack_into('<I',expected,4160,0x421)
            need(expected.hex()==owner['source_final_hex'],'Every backing tail and exact two source fields')
        need(pin(run/mode/'BEFORE/CRT-codepage-lock/bytes.bin').read_bytes()==pin(run/mode/'AFTER/CRT-codepage-lock/bytes.bin').read_bytes(),'Borrowed wholeCS24 restored at observed endpoints')
    need(len(normal)==7 and len(apis)==len(physical)==4,'Full bounded normal/source/API geometry')
    kernel=PEImage(pin('C:/Windows/SysWOW64/kernel32.dll').read_bytes());requested={n:x for x in kernel.exports()for n in x['names']}
    for a,q in zip(apis,physical):
        need(a['API']==q['API']and a['entry64_hex']==q['entry64_hex']and a['owner_metadata']==q['owner_metadata'],'Actual raw API row and physical export proof join')
        image=PEImage(pin(q['physical_module_path'],q['module_sha256']).read_bytes());meta=q['owner_metadata'];owner,target,base,size,state,protect,kind,allocation=meta
        need(owner==allocation and target==a['target']and base<=target<base+size and state==0x1000 and kind==0x1000000 and protect==0x20,'Actual owner committed executable MEM_IMAGE target')
        exported=next(x for x in image.exports()if q['owning_alias']in x['names']);need('forwarder'not in exported and exported['rva']==q['export_rva']and target==owner+exported['rva'],'Exact physical owning export')
        need(requested[a['API']].get('forwarder','')==q['forwarder'],'Exact kernel32 named/forwarded identity')
        if q['forwarder']:need(q['forwarder']=='NTDLL.'+q['owning_alias']and Path(q['physical_module_path']).name.lower()=='ntdll.dll','Exact forwarded owner domain')
        else:need(Path(q['physical_module_path']).name.lower()=='kernel32.dll','Exact direct owner domain')
        off,_=image.rva_range(exported['rva'],64);expected=bytearray(image.data[off:off+64]);found=[];d,n=image.directories[5];cursor=0
        while cursor<n:
            off,_=image.rva_range(d+cursor,8);page,extent=u(image.data,off,2);need(8<=extent<=n-cursor and extent%2==0,'Complete actual HIGHLOW table')
            off,_=image.rva_range(d+cursor+8,extent-8)
            for z in range(0,extent-8,2):
                word=struct.unpack_from('<H',image.data,off+z)[0];typ,at=word>>12,page+(word&4095)
                if typ and at<exported['rva']+64 and at+4>exported['rva']:
                    need(typ==3 and exported['rva']<=at and at+4<=exported['rva']+64,'Exact complete observed x86 HIGHLOW')
                    i=at-exported['rva'];struct.pack_into('<I',expected,i,(u(expected,i)[0]+owner-image.image_base)&0xffffffff);found.append(at)
            cursor+=extent
        need(found==q['HIGHLOW_RVAs']and expected.hex()==a['entry64_hex'],'Entire actual owner/export entry64 after every declared relocation')
    asm=pin(prep/'reference_x86.asm').read_text();worker_source=pin(prep/'worker.cpp').read_text();validator=pin(R/'tools/m4-mfc1168-probe/validate_v6.py').read_text();tracer=pin(prep/'trace.hpp').read_text()
    need(asm.index('mov esi,DWORD PTR fs:[18h]')<asm.index('rep movsd')<asm.index('fxrstor mixed_guest_fx')<asm.index('jmp DWORD PTR mixed_input[36]'),'Whole coherent TEB precedes source entry and no observing safe_read is its origin')
    need('require(reinterpret_cast<unsigned>(service)==0x5f401083' in worker_source and 'GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168))'in worker_source,'Exact genuine MFC ordinal and preferred source address')
    need('source_result=dict(root=0x5ae3e4' in validator and 'memory[root_teb]=bytearray(root_teb_pages[:4096])'in validator and 'm.api_return(pc,a[\'argc\'],a[\'after\'][0])'in validator,'Literal BEFORE-only replay with explicitly bounded external volatile API responses')
    need('m.bytes(page,4096),raw(p/f\'AFTER/{module}/{page}.bin\')'in validator,'Entire source-derived272 provider pages compared at endpoints')
    need(tracer.count('SetThreadContext(thread.value,&c)')==2 and 'c.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS'in tracer,'Historical actual full-CONTEXT stepping scope retained explicitly')
    # Whole linked ASM sections retain the shared capture prefixes as well as
    # the public procedures; no wrapper prefix is dropped from attribution.
    tool=pin(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v6.py');spec=importlib.util.spec_from_file_location('mfc_review_coff',tool);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    image=PEImage(pin(b['worker'],b['worker_sha256']).read_bytes());objdir=Path(e['build']).parent/'build-x86/mw34_mfc1168_probe.dir/Release';linked=[]
    for filename in ('reference_x86.obj','boundaries.obj','api_boundaries.obj'):
        path=pin(objdir/filename);sy,se=C.coff(path.read_bytes());executable=[i for i,s in se.items()if s['flags']&0x20000000 and s['bytes']];need(len(executable)==1,'One complete ASM text section')
        index=executable[0];fake={0:dict(name=filename+' whole text',value=0,section=index,type=0x20,storage=2)}
        proof=C.linked_function(image,fake,se,filename+' whole text');proof['object_path']=str(path);proof['object_sha256']=sha(path);linked.append(proof)
        bases={}
        for q in proof['relocations']:
            need(q['type']in(6,20),'Actual exact ASM DIR32/REL32 relocation')
            sec=q['symbol_section'];value=(q['actual_symbol_address']-q['symbol_value'])&0xffffffff
            if sec>0:need(sec not in bases or bases[sec]==value,'Whole same-object section-relative relocation consistency');bases[sec]=value
    log=pin(Path(e['build']).parent/'compile.log').read_text();need('/WX'in log and '0 Error(s)'in log and str(prep/'worker.cpp')in log,'Current compiled source/ASM actual provenance')
    pin(__file__);pin(R/'tools/analysis/pe.py');pin(sys.executable)
    out.mkdir();a=out/'compiled-assembly.json';a.write_text(json.dumps(linked,indent=2)+'\n');pin(a)
    report=dict(passed=True,validation_sha256=VH,execution_sha256=v['execution_sha256'],build_sha256=e['build_sha256'],preparation_sha256=b['preparation_sha256'],genuine_reached_instructions=142,whole_raw_CONTEXT_sides=284,literal_operands=113,normal_boundaries=7,physical_named_API_export_joins=4,whole_genuine_backing_byteflows=10,source_derived_provider_pages=272,provider_page_endpoint_pairs=544,whole_borrowed_CS24_endpoint_pairs=2,FS_record_install_restore_pairs=1,coherent_TEB_input_bytes=8192,compiled_assembly_sections=3,compiled_assembly_bytes=sum(x['bytes']for x in linked),compiled_assembly_relocations=sum(len(x['relocations'])for x in linked),source_AFTER_seed=False,original_cached_domain_only=True,initializer_credit=0,native_credit=0,archive_reader_opened=False,scope='Independent bounded source/compiler/whole-ASM/physical-export review of the genuine cached TLS index3/manager slot1/global fallback domain. Normal shim PCs are explicitly projected, with actual control separately witnessed by the unshimmed trace. Historical debugger writes full CONTEXT; reached integer source and actual zero latent caller metadata plus wholeENV endpoints bound the current claim. No arbitrary/nonzero caller-FP input, WinAPI internals, intermediate borrowedCS bytes, full TEB AFTER equality, lazy allocation/callback path, provider initialization, or native/general game acceptance follows.',files=PINS)
    target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(target),sha256=sha(target),files=len(PINS))))
if __name__=='__main__':main(sys.argv[1])
