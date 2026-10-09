"""Independent raw ownership, source frontier and strict rich-HW review."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes,workspace_path
from stages import verify_stage
from transport import DirectSet,read,need
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000,0x78035000,0x78005000,0x20000000,0x7800c000)
REQUESTS=(0,1,24,31,32,4096)
PREALLOC={1001,1002,1007,1010}

def hardware(bundle,prefix,boundary,metrics):
    a=bundle.data(prefix+boundary+'-host-before.bin');b=bundle.data(prefix+boundary+'-host-after.bin')
    need(len(a)==len(b)==544,'Full direct host FX+ENV extent')
    need(a[512:540]==b[512:540],'Unchanged strict complete legacy ENV28')
    need(any(a[524:540]) and struct.unpack_from('<H',a,520)[0]!=0xffff,'Actual nonzero legacy pointer/opcode and active x87 stack witness')
    need(a[:5]==b[:5] and a[24:28]==b[24:28],'Unchanged strict CW/SW/FTW/MXCSR')
    need(struct.unpack_from('<H',a,0)[0]==0xa7f and struct.unpack_from('<I',a,24)[0]==0x5fa5 and a[4]!=0,'Actively loaded rich host control fixture')
    for i in range(8):need(a[32+16*i:42+16*i]==b[32+16*i:42+16*i],'Unchanged strict each physical raw80')
    for i in range(6,16):need(a[160+16*i:176+16*i]==b[160+16*i:176+16*i],'Unchanged strict nonvolatile XMM6..15')
    errors0,errors1,flags0,flags1=bundle.words(prefix+boundary+'-host-abi.bin',4,'Q')
    need(errors0==errors1 and (flags0^flags1)&0x400==0,'Caller LastError and ABI direction flag preserved')
    metrics['hardware_pairs']+=1;metrics['strict_hardware_domain_gates']+=24

def api_identity(raw,pin):
    need(len(raw)==2184,'Frozen packed API identity extent')
    address,named,owner,owner_named,base,size,allocation,state,kind,protect,allocation_protect=struct.unpack_from('<7Q4I',raw)
    need(address==named==owner_named and owner==allocation and base<=address<base+size and state==0x1000 and kind==0x1000000 and not(protect&0x101) and protect&0xf0,'Actual named target executable image and full owner identity')
    digest=raw[72:136].decode('ascii');path=raw[136:].decode('utf-16-le').split('\0',1)[0];pin(path,digest)
    return address,owner,path,digest

def export(raw,name):
    def u16(p):return struct.unpack_from('<H',raw,p)[0]
    def u32(p):return struct.unpack_from('<I',raw,p)[0]
    need(u16(0)==0x5a4d,'Physical native module DOS identity');pe=u32(60);opt=pe+24
    need(u32(pe)==0x4550 and u16(pe+4)==0x8664 and u16(opt)==0x20b,'Physical native module AMD64 PE identity')
    directory,length=u32(opt+112),u32(opt+116);sections=[opt+u16(pe+20)+40*i for i in range(u16(pe+6))]
    def at(rva,n=1):
        hits=[u32(s+20)+rva-u32(s+12) for s in sections if u32(s+12)<=rva and rva+n<=u32(s+12)+u32(s+16)]
        need(len(hits)==1 and hits[0]+n<=len(raw),'Unique bounded physical export RVA');return hits[0]
    def text(rva):
        start=at(rva);end=raw.find(b'\0',start,min(len(raw),start+4096));need(end>=start,'Terminated physical export string');return raw[start:end].decode('ascii')
    e=at(directory,40);functions,names,ordinals=u32(e+28),u32(e+32),u32(e+36);matches=[]
    for i in range(u32(e+24)):
        if text(u32(at(names+4*i,4)))==name:
            ordinal=u16(at(ordinals+2*i,2));need(ordinal<u32(e+20),'Physical named export ordinal');rva=u32(at(functions+4*ordinal,4));matches.append((rva,text(rva) if directory<=rva<directory+length else ''))
    need(len(matches)==1,'Unique physical named export');return matches[0]

def export_proof(raw,identity,requested,pin):
    need(len(raw)==4624,'Separate finite full-width PE forwarding witness extent')
    version,named_module,target,named,owner,owner_named=struct.unpack_from('<6Q',raw)
    text=lambda offset,size:raw[offset:offset+size].split(b'\0',1)[0].decode('ascii')
    wanted=text(48,32);forward=text(80,256);alias=text(336,64);named_sha=raw[400:464].decode('ascii');owner_sha=raw[464:528].decode('ascii')
    named_path=raw[528:2576].decode('utf-16-le').split('\0',1)[0];owner_path=raw[2576:4624].decode('utf-16-le').split('\0',1)[0]
    need(version==1 and wanted==requested and target==named==owner_named==identity[0] and owner==identity[1] and owner_path==identity[2] and owner_sha==identity[3],'Immutable named/owner/API association')
    named_file=pin(named_path,named_sha);owner_file=pin(owner_path,owner_sha);rva,physical_forward=export(named_file.read_bytes(),requested)
    need(physical_forward==forward,'Actual physical forwarder text')
    if requested=='HeapAlloc':need(forward=='NTDLL.RtlAllocateHeap' and alias=='RtlAllocateHeap','Only admitted exact HeapAlloc native chain')
    else:need(requested=='HeapFree' and not forward and alias=='HeapFree' and named_module==owner and named_module+rva==target,'Exact direct HeapFree named RVA')
    owner_rva,owner_forward=export(owner_file.read_bytes(),alias)
    need(not owner_forward and owner+owner_rva==target,'Actual owner direct export RVA resolves full target')

def semantics(bundle,pin,metrics):
    need(bundle.data('COMPLETE')==b'COMPLETE' and 'INCOMPLETE' not in bundle.entries,'Complete independent semantic publication')
    controls=json.loads(bundle.data('review-controls.json'));need(controls['rows']==24 and controls['ordinary_rows']==12 and controls['independent_control_rows']==12 and controls['token_units']==24 and controls['wrong_thread_units']==1 and controls['checks']>0,'Actual bounded independent fixture/assertion units')
    metrics['compiled_assertions']+=controls['checks'];metrics['readonly_alias_units']+=controls['token_units'];metrics['wrong_thread_denials']+=controls['wrong_thread_units']
    need({n.split('/')[0] for n in bundle.names()}=={'COMPLETE','review-controls.json',*(f'row-{i}' for i in range(24))},'Exact finite row/root logical namespace')
    for i in range(24):
        prefix=f'row-{i}/';mode=0 if i<12 else i+989;request=REQUESTS[(i+3*(i//6))%6] if i<12 else 24
        summary=json.loads(bundle.data(prefix+'result.json'));need(summary['passed'] and summary['scenario']==i and summary['control']==mode and summary['poisoned_retry'] and not summary['State_reseed_after_writer'] and not summary['full_CRT'] and not summary['whole_M4_complete'],'Exact actual row identity and bounded source/retry scope')
        j=bundle.words(prefix+'allocation-job.bin',32);p=bundle.words(prefix+'allocation-progress.bin',16);r=bundle.words(prefix+'allocation-registry.bin',24,'Q');w=bundle.words(prefix+'allocation-witness.bin',16,'Q');h=bundle.words(prefix+'allocation-heap-registry.bin',18,'Q');o=bundle.words(prefix+'review-ownership.bin',12,'Q')
        allocated=int(not mode or mode not in PREALLOC)
        need(j[:2]==(mode,request) and p[0]==r[0]==1 and p[7]==r[5]==request,'Private declared allocator input')
        need(p[13:15]==(0,0) and r[9]==r[12]==h[7]==0 and h[15]==1,'Private allocation/heap ownership closed after terminal cleanup')
        need(j[22:27]==(1,1,allocated,int(mode==0),int(mode==0)) and h[8:11]==(1,1,1),'Actual source API and cleanup counters')
        need(h[4]==h[16]==r[20] and h[4]>0xffffffff and r[4]==r[21]==w[3] and bool(r[4])==bool(allocated),'Full actual HANDLE/pointer retained; guest token does not truncate either')
        need(r[8]==allocated and r[10]==r[11]==int(mode==0) and r[17]==r[18]==int(bool(mode) and allocated),'Each normal/fault actual pointer freed once before heap destruction')
        need(o==(1,i,mode,int(bool(mode)),h[4],r[4],1,1,allocated,int(mode==0),r[17],r[18]),'Independent hook reached and separate private resource witnesses agree')
        need(j[30]==j[31] and w[4]==w[6] and (not r[10] or w[11]==w[13]),'Actual source API caller LastError restored')
        q=bundle.words(prefix+'allocation-query-witness.bin',20,'Q');output=bundle.data(prefix+'allocation-query-output.bin');copy=bundle.words(prefix+'allocation-query-output-accesses.bin',320)
        need(q[:3]==(1,1,1) and q[3]!=0 and q[4]==148 and q[11:18]==(37,1,1,1,1,1,0) and q[18]>=5 and q[19]==2 and len(output)==148,'Actual measured qualifying original query and preserved query-return witness')
        need(tuple(copy[:185])==tuple(v for k in range(37) for v in (0x78003a2b,0x200017b8+4*k,struct.unpack_from('<I',output,4*k)[0],4,1)) and not any(copy[185:]),'37 exact actual output DWORD commits with unused slots zero')
        metrics['actual_heaps']+=1;metrics['actual_heap_releases']+=1;metrics['actual_queries']+=1;metrics['actual_output_DWORD_commits']+=37;metrics['actual_HeapAlloc_calls']+=allocated;metrics['actual_source_HeapFree_calls']+=r[10];metrics['actual_fallback_HeapFree_calls']+=r[17]
        for boundary in ('writer','entry'):hardware(bundle,prefix,boundary,metrics)
        phases=sorted({n[len(prefix):].split('/')[0] for n in bundle.names() if n.startswith(prefix) and '/' in n[len(prefix):]})
        for phase in phases:
            need(phase.startswith('allocation-') or phase in {'writer-before','writer-after','heap-create-after','retry-after'},'Only declared independent complete milestones')
            root=prefix+phase+'/';need(len(bundle.data(root+'state.bin'))==3504 and len(bundle.data(root+'fx.bin'))==512 and len(bundle.data(root+'runtime-cpu.bin'))==40,'Complete State/FX/CPU observations')
            need(bundle.data(root+'reserved-runtime-heap.bin')==bytes(4096),'Original reserved Runtime heap page unchanged by distinct guest allocation')
            for page in PAGES:need(len(bundle.data(root+f'page-{page}.bin'))==4096,'All21 carried full source/memory pages')
            if phase.startswith('allocation-'):
                need(bundle.data(root+'fx.bin')==bundle.data(prefix+'writer-after/fx.bin'),'Allocator carries complete distinct Runtime FX')
                need(bundle.data(root+'runtime-cpu.bin')==bundle.data(prefix+'allocation-caller-before/runtime-cpu.bin'),'Allocator source effects do not reseed/rewrite Runtime CPU')
            metrics['complete_milestones']+=1
        for name in ('state.bin','fx.bin','runtime-cpu.bin',*(f'page-{page}.bin' for page in PAGES)):
            need(bundle.data(prefix+'heap-create-after/'+name)==bundle.data(prefix+'retry-after/'+name),'Terminal poisoned retry retains full State/FX/CPU and all21 pages')
        for name in ('create','destroy','query'):
            a=api_identity(bundle.data(prefix+f'allocation-{name}-api-before.bin'),pin);b=api_identity(bundle.data(prefix+f'allocation-{name}-api-after.bin'),pin);need(a==b,'Actual fixed native prefix/cleanup API identity')
        if allocated:
            a=api_identity(bundle.data(prefix+'allocation-alloc-api-before.bin'),pin);b=api_identity(bundle.data(prefix+'allocation-alloc-api-after.bin'),pin);need(a==b,'Actual unchanged genuine HeapAlloc export identity')
            raw_a=bundle.data(prefix+'allocation-native-before/allocation-alloc-export-before.bin');raw_b=bundle.data(prefix+'allocation-native-after/allocation-alloc-export-after.bin');need(raw_a==raw_b,'Immutable measured forwarding witness across actual HeapAlloc');export_proof(raw_b,b,'HeapAlloc',pin)
        if not mode:
            extent=((request or 1)+15)&~15;pattern=bytes((k*37+request*11+0x5a)&255 for k in range(extent))
            need(p[1:7]==(1,1,1,1,1,1) and j[15:21]==(1,1,1,1,1,1) and p[8]==r[6]==w[2]==extent,'Authentic complete malloc/client/free/NULLfree batch and source rounding')
            need(j[3]==(118 if request else 120) and j[4]==4 and j[6]==10,'Exact literal source, genuine API-read and intrinsic AF callback counts')
            undefined=bundle.words(prefix+'allocation-undefined.bin',32)
            need(undefined==(0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31,0x78001843,0x7800cc9a,0x780012d9,0x780013b6,0x780013b6)+(0,)*22,'Ten genuine intrinsic callbacks; generated CCA4 AND publishes AF0 without callback')
            need(bundle.data(prefix+'allocation-pattern.bin')==pattern and len(bundle.data(prefix+'allocation-initial.bin'))==extent,'Actual complete allocation initial output and synchronized pattern')
            a=api_identity(bundle.data(prefix+'allocation-free-api-before.bin'),pin);b=api_identity(bundle.data(prefix+'allocation-free-api-after.bin'),pin);need(a==b,'Actual unchanged genuine HeapFree identity')
            raw_a=bundle.data(prefix+'allocation-free-native-before/allocation-free-export-before.bin');raw_b=bundle.data(prefix+'allocation-free-native-after/allocation-free-export-after.bin');need(raw_a==raw_b,'Immutable direct export witness across actual HeapFree');export_proof(raw_b,b,'HeapFree',pin)
            need(w[7]==1 and w[8]!=0 and w[10]==r[4] and r[4]>0xffffffff,'One actual full native pointer passed to source HeapFree; NULL free adds no call')
            client=bundle.data(prefix+'allocation-client-after/allocation-owned-page.bin');need(client==pattern+bytes(4096-extent),'All resident allocation bytes match declared synchronized client output')
            before=bundle.words(prefix+'allocation-malloc-before/state-cpu.bin',10);returned=bundle.words(prefix+'allocation-malloc-returned/state-cpu.bin',10);final=bundle.words(prefix+'allocation-batch-complete/state-cpu.bin',10)
            need(returned[0]==0x31000000 and returned[4]==before[4]+4 and returned[9]==0xffffffe0 and returned[3]==before[3] and returned[5:8]==before[5:8],'Genuine malloc RET ABI and opaque guest token publication')
            need(final[4]==0x2000185c and final[9]==0xffffffd0,'Genuine free(NULL) RET before declared external caller boundary')
            metrics['ordinary_sequences']+=1
        else:need(not p[6] and j[10]!=0 and bundle.data(prefix+'allocation-reason.txt').strip(),'Independent exact directed fault prevents clean batch completion');metrics['independent_control_sequences']+=1

def main(native_path,native_sha,directory):
    start=time.perf_counter();out=workspace_path(directory,reports=True);need(out.parent==ROOT/'reports/m4-crt-allocation-review' and not out.exists(),'Fresh raw independent review report');out.mkdir(parents=True)
    native=read(native_path);need(sha_file(native_path)==native_sha and native['passed'] and native['native_scenarios']==48 and not native['native_rerun'],'Exact frozen independent native receipt')
    files=dict(native['files']);passed=False;closure=None;metrics={key:0 for key in ('hardware_pairs','strict_hardware_domain_gates','compiled_assertions','readonly_alias_units','wrong_thread_denials','actual_heaps','actual_heap_releases','actual_queries','actual_output_DWORD_commits','actual_HeapAlloc_calls','actual_source_HeapFree_calls','actual_fallback_HeapFree_calls','complete_milestones','ordinary_sequences','independent_control_sequences')}
    def pin(p,expected=None):
        p=Path(p).absolute();actual=sha_file(p);need(expected is None or actual==expected,'Current literal raw review input');key=normalized(str(p));need(key not in files or files[key]==actual,'Conflict-free current raw review closure');files[key]=actual;return p
    try:
        for p in (Path(native_path),Path(__file__),Path(__file__).parent/'transport.py',Path(sys.executable)):pin(p)
        for level in ('O0','O2'):
            info=native['levels'][level];verify_stage(info['native_stage'],info['native_stage_sha256']);pin(info['inventory_path'],info['inventory_sha256']);b=DirectSet(info['transport_manifest'],pin)
            try:need(read(info['inventory_path'])['files']==dict(sorted(b.records.items())),'Exact externally pinned complete logical union');semantics(b,pin,metrics)
            finally:b.close()
        need(metrics['hardware_pairs']==96 and metrics['ordinary_sequences']==metrics['independent_control_sequences']==24,'Actual bounded complete corpus counts')
        closure=verify_manifest(files);passed=True
    except BaseException:publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
    finally:
        report={'passed':passed,'native_path':str(Path(native_path).absolute()),'native_sha256':native_sha,'metrics':metrics,'files':files,'current_physical_closure':closure,'native_rerun':False,'game_launched':False,'original_executed':False,'volatile_XMM0_5_equality_claimed':False,'full_CRT_complete':False,'whole_M4_complete':False,'elapsed_seconds':time.perf_counter()-start}
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in report.items() if k!='files'}))

if __name__=='__main__':main(*sys.argv[1:])
