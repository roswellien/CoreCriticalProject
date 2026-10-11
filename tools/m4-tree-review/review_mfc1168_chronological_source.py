"""Bounded independent current MFC source byteflow/observer-scope review."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No capture reader');v=sha(p);need(h is None or h==v,'Physical source binding '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Immutable input');PINS[str(p)]=v;return p
def raw(p,h=None):return pin(p,h).read_bytes()
def read(p,h=None):return json.loads(raw(p,h))
def eq(a,b,s):need(a==b,s+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:10]))
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def load(p,n):
    s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
    out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh owned review');out.mkdir();passed=False;counts=collections.Counter();proofs=[]
    try:
        base=R/'reports/m4-mfc1168-connected-original';p=base/'source-r3/report.json';r=read(p,'3afcb5f1669726f43fa4c86a23eb1af8349dae1710e63ca7e87271a4fa1907d0');need(r['passed']and not r['source_AFTER_seed']and r['all_bounded_readers_closed'],'Actual current source proof')
        for path,h in r['files'].items():pin(path,h)
        d=read(p.parent/'source-derivations.json',r['files'][str((p.parent/'source-derivations.json').resolve())]);validation=read(r['original_validation_path'],r['original_validation_sha256']);current=read(Path(r['original_validation_path']).parent/'retained-actual-inputs.json');execution=read(validation['execution_path'],validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prepdir=Path(build['preparation']);prep=read(prepdir/'report.json',build['preparation_sha256']);contract=read(prep['contracts'])
        def input_(key):
            row=current[key];b=raw(row['path'],row['sha256']);need(len(b)==row['bytes'],'Whole actual current extent');return b
        memory={};targets={};record=input_('phase/0/13.bin')
        for i,address in enumerate(contract['fixed_current_source_pages']):memory[address]=bytearray(record[2276+i*4096:2276+(i+1)*4096]);targets[address]=record[178404+i*4096:178404+(i+1)*4096]
        for address in contract['external_source_pages']:memory[address]=bytearray(input_(f'phase/0/13/extra-before/{address}.bin'));targets[address]=input_(f'phase/0/13/extra-after/{address}.bin')
        for module in('MFC','CRT'):
            for address,*tail in struct.iter_unpack('<4I',input_('MFC1168/BEFORE/'+module+'/metadata.bin')):
                b=input_(f'MFC1168/BEFORE/{module}/{address}.bin');need(address not in memory or memory[address]==b,'Exact overlapping complete own BEFORE pages');memory[address]=bytearray(b);targets[address]=input_(f'MFC1168/AFTER/{module}/{address}.bin')
        teb=u(input_('phase/0/13/TEB-before-base.bin'))[0];tb=input_('phase/0/13/TEB-before.bin');need(len(tb)==8192 and u(tb,24)[0]==teb,'Actual coherent root-entry TIB');memory[teb]=bytearray(tb[:4096]);memory[teb+4096]=bytearray(tb[4096:])
        for o in d['source_borrowed_backings']:memory[o['address']]=bytearray(bytes.fromhex(o['initial_hex']))
        def bytes_(address,size):
            result=bytearray()
            for at in range(address,address+size):
                candidates=[b[at-a]for a,b in memory.items()if a<=at<a+len(b)];need(candidates and len(set(candidates))==1,'Exact currently carried source alias '+hex(at));result.append(candidates[0])
            return bytes(result)
        for pc,address,value,width,writing in d['source_accesses']:
            if writing:
                payload=value.to_bytes(width,'little');bytes_(address,width)
                for a,b in memory.items():
                    lo,hi=max(a,address),min(a+len(b),address+width)
                    if lo<hi:b[lo-a:hi-a]=payload[lo-address:hi-address]
                counts['independent_causal_source_writes']+=1
            else:eq(bytes_(address,width),value.to_bytes(width,'little'),'Entire independent source read input '+hex(pc));counts['independent_causal_source_reads']+=1
        for address,goal in targets.items():
            if address==0x20001000:continue
            eq(bytes_(address,4096),goal,'Whole current nonstack own-BEFORE/source-write byteflow '+hex(address));counts['independent_whole_page_byteflows']+=1
        for o in d['source_borrowed_backings']:
            eq(bytes_(o['address'],o['extent']),bytes.fromhex(o['source_final_hex']),'Whole literal borrowed capacity and untouched tail');counts['independent_whole_borrowed_backings']+=1
        need(u(tb)[0]==d['source_FS_BEFORE']==d['source_FS_AFTER']==u(input_('phase/0/13/TEB-after.bin'))[0]==u(bytes_(teb,4))[0],'Actual coherent source TIB heads join independent source EH install/restore');counts['actual_coherent_TIB_source_head_joins']=2
        need(d['actual_per_instruction_chronological_trace']is False and d['intermediate_source_FS_observation']is False and d['whole_stack_endpoint_claim']is False and d['opaque_OS_CS_internal_writes_claim']is False,'Preserved normal-boundary/source/OS-stack distinctions')
        asm=raw(prepdir/'reference_x86.asm').decode();boundasm=raw(prepdir/'boundaries.asm').decode();api_asm=raw(prepdir/'api_boundaries.asm').decode();observer=raw(prepdir/'connected_observer.hpp').decode()
        need(asm.index('mov mixed_teb_before_base,esi')<asm.index('fxrstor mixed_guest_fx')<asm.index('jmp DWORD PTR mixed_input[36]'),'Source TIB input copied in root assembly before entry')
        need(boundasm.index('mov DWORD PTR b_cpu[16],esp')<boundasm.index('mov esp,mixed_host_esp')<boundasm.index('call observe_boundary'),'True source CPU captured before host stack and C++ observation');need('b.FShead=__readfsdword(0)'in observer and 'try{require(boundary_count<16'in observer and 'try{require(api_kind<4'in observer,'FS scalar explicitly inside host C++ exception frames')
        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','chronological_scope_coff');sy,sections=C.coff(raw(base/'build-r2/build-x86/mw34_joint_startup124_original.dir/Release/reference.obj'));PE=load(R/'tools/analysis/pe.py','chronological_scope_PE');worker=PE.PEImage(raw(build['worker'],build['worker_sha256']))
        for symbol in('_observe_boundary','_observe_named_API'):
            f=next(v for v in sy.values()if v['name']==symbol);section=sections[f['section']];b=section['bytes'];reads=[i for i in range(len(b))if b.startswith(bytes.fromhex('64a100000000'),i)];stores=[i for i in range(len(b))if b.startswith(bytes.fromhex('64a300000000'),i)]
            need(len(reads)==2 and stores and reads[0]<stores[0]<reads[1],'Actual compiler EH FS install dominates observer metadata FS read');proof=C.linked_function(worker,sy,sections,symbol);proof.update(FS_read_offsets=reads,FS_store_offsets=stores,first_read_scope='compiler EH prologue predecessor',second_read_scope='C++ observer metadata after compiler FS installation',source_input=False);proofs.append(proof);counts['whole_compiled_linked_host_FS_observers']+=1
        for relation in d['source_normal_boundary_relations']+d['source_API_relations']:
            need(relation['intermediate_source_FS_observation']is False and relation['derived_source_FS_head']==d['source_FS_BEFORE'],'Source head derived from root TIB, not observer scalar');counts['explicit_host_owned_boundary_FS_scalars']+=1
        flag_rows=d['flag_lifetimes'];api_sites={r['source_PC']for r in d['source_API_relations']};program=read(R/'reports/m4-mfc1168-probe/validation-r6/reached-instruction-contracts.json')['instructions'];program={v['pc']:v for v in program};before={}
        consume={'je':('ZF',),'jne':('ZF',),'jae':('CF',),'ja':('CF','ZF'),'jl':('SF','OF'),'jge':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'sbb':('CF',)}
        for row in flag_rows:
            pc=row['PC'];used=consume.get(program[pc]['mnemonic'],());need(not set(used)&set(before),'No source use of undefined prior condition/carry bits');counts['independent_defined_source_control_uses']+=bool(used);before={}if pc in api_sites else row['undefined_flags']
        eq(len(d['source_PCs']),142,'Finite physical cached domain');eq(len(d['source_accesses']),113,'Entire finite chronological source operand closure');passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        pin(__file__);pin(sys.executable);q=out/'compiled-FS-observer-scope.json';q.write_text(json.dumps(proofs,indent=2)+'\n');pin(q)
        report=dict(passed=passed,current_source_sha256='3afcb5f1669726f43fa4c86a23eb1af8349dae1710e63ca7e87271a4fa1907d0',scope='Independent bounded chronological MFC source byteflow and compiled host-observer FS timing. Coherent root TIB heads alone supply source FS. C++ metadata follows actual compiler SEH installation; no intermediate source FS or opaque OS stack/CS-write claim.',counts=dict(counts),source_AFTER_seed=False,archive_reader_opened=False,initializer_credit=0,files=PINS);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
