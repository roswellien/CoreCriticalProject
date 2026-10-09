"""Author source model and lossless differences for original-BEFORE replay.

Imports only the author's frozen original-byte scalar interpreter. Windows
results come from this replay's real native lookup records, never original
AFTER. Original AFTER is used separately to enumerate observed differences.
"""
import argparse, hashlib, importlib.util, json, pathlib, struct
ROOT=pathlib.Path(__file__).resolve().parents[2]; BASE=ROOT/'reports/m4-crt-fdiv-replay'
PRIOR=ROOT/'tools/m4-crt-fdiv/validate_native.py'
def need(v,m):
    if not v: raise ValueError(m)
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:f.write(json.dumps(v,indent=2)+'\n')
def put(b,o,v,n=4):b[o:o+n]=int(v).to_bytes(n,'little')
def u(b,o=0):return struct.unpack_from('<I',b,o)[0]
def h(b,o=0):return struct.unpack_from('<H',b,o)[0]
need(sha(PRIOR)=='8c51a4e7ad38eca5e128fec209b4855c51190554a803c38c2192e5941222ae0c','Frozen author interpreter identity')
spec=importlib.util.spec_from_file_location('author_fdiv_scalar',PRIOR);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
CW=M.CW;STRIDE=M.STRIDE
def ranges(indices):
    result=[]
    for i in indices:
        if result and result[-1][1]==i:result[-1][1]+=1
        else:result.append([i,i+1])
    return result
def projection(original):
    t=struct.unpack_from('<27I',original);ident,repeat,debug,cw=t[:4];W=t[9];lo=t[7];hi=lo+t[8]
    need(not debug and ident<24,'Only actual direct BEFORE input admission')
    cpu=list(struct.unpack_from('<10I',original,108));need(cpu[4]==W and cpu[9]==0x78004254,'Actual original BEFORE CPU')
    cpu[4]=0x20001800;fx=original[188:700];env=original[2236:2264]
    variable=91348+40*(t[18]+t[19]);stack=original[variable:variable+t[8]]
    need(len(stack)==t[8] and h(fx)==cw and h(fx,2)==0 and fx[4]==0 and u(fx,24)==0x1f80,'Actual original BEFORE empty FP domain')
    need(h(env)==cw and h(env,4)==0 and h(env,8)==0xffff,'Separate actual original BEFORE ENV domain')
    guest=bytearray([0xa5]*4096);mask=bytearray(4096)
    for i in range(4096):
        address=W-0x800+i
        if lo<=address<hi:guest[i]=stack[address-lo];mask[i]=1
    need(u(guest,0x800)==0x10000100,'Measured authored outer return word')
    put(guest,0x800,0x78004232)
    return struct.pack('<6I10I',ident,repeat,cw,W,lo,hi,*cpu)+fx+env+guest+mask
def seeded(inp):
    ident=u(inp);s=bytearray((i*31+ident*17+3)&255 for i in range(3504));s[2112:2208]=bytes(96);put(s,2168,0x7ffde000)
    cpu=struct.unpack_from('<10I',inp,24);fx=inp[64:576];env=inp[576:604]
    for name,v in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi','eflags','eip'),cpu):
        if name=='eflags':put(s,2080,v,8)
        else:put(s,M.GPR[name],v)
    for off,bit in M.AF:s[off]=(cpu[8]>>bit)&1
    s[2768:3280]=fx
    for dest,source,width in ((2776,12,4),(2780,16,2),(2774,18,2),(2784,20,4),(2788,24,2)):s[dest:dest+width]=env[source:source+width]
    for off in (2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743):s[off]=0
    for i in range(8):s[16+64*i:32+64*i]=fx[160+16*i:176+16*i];s[2616+16*i:2624+16*i]=fx[32+16*i:40+16*i]
    return bytes(s)
def cpu(state):
    flags=int.from_bytes(state[2080:2088],'little')
    for off,bit in M.AF:flags=(flags&~(1<<bit))|((state[off]&1)<<bit)
    return [u(state,M.GPR[n]) for n in ('eax','ecx','edx','ebx','esp','ebp','esi','edi')]+[flags,u(state,M.GPR['eip'])]
def native(row,inp,program,pack,game,bindings):
    ident,repeat,cw,status,events,routes,lookups=struct.unpack_from('<7I',row)
    need(ident==u(inp) and repeat==u(inp,4) and cw==u(inp,8) and status==1 and routes==lookups==3 and events<256,'Exact replay corpus/actual completion')
    s0=row[28:3532];s1=row[3532:7036];fx0=row[7036:7548];fx1=row[7548:8060];p0=row[9140:46004];p1=row[46004:82868]
    need(s0==seeded(inp),'Whole3504 State BEFORE exactly observed inputs plus declared authored seed')
    need(fx0==inp[64:576],'Separate literal512 observed original BEFORE FX')
    expected_pages=b''.join(pack[20+i*4104:20+i*4104+4096] for i in range(7))+inp[604:4700]+game.bytes(0x5bb000,4096)
    need(p0==expected_pages,'Whole9page BEFORE exact sparse provider/rawIAT/originalBEFOREstack/gameimage')
    need(row[8060:8572]==row[8572:9084] and row[9084:9112]==row[9112:9140],'Internal whole host FP restoration checkpoint')
    handles=[];feature=None
    for j,name in enumerate(('GetModuleHandleA','GetProcAddress','IsProcessorFeaturePresent')):
        lookup=row[88072+j*6556:88072+(j+1)*6556];kind,token,arg,result,error=struct.unpack_from('<5I',lookup);host=int.from_bytes(lookup[20:28],'little')
        need(kind==j+1 and arg==0,'Actual lookup kind/feature0')
        handle,pe=M.module(lookup[4396:],bindings);handles.append(handle)
        need(lookup[28:2212]==lookup[2212:4396],'Actual stable native API identity')
        target=M.api(lookup[28:2212],name,pe,bindings)
        if j==0:need(host==handle and token==0x11001000 and result==0,'Actual native module token association')
        elif j==1:
            need(host and token==0x11000300 and result==0,'Actual native FARPROC token association');exports,d,n=pe.exports();r=exports['IsProcessorFeaturePresent'];need(d<=r<d+n or host==handle+r,'Actual native returned feature export');feature_target=host
        else:need(host==result and token==0x11000300 and target==feature_target,'Actual invoked feature BOOL association');feature=result
    need(len(set(handles))==1,'One actual borrowed native module')
    model=M.Model(s0,p0,fx0,program,feature).run()
    need(s1==model[0] and p1==model[1] and fx1==model[2],'Whole native State9pagesFX from exact source instructions/native volatility policy')
    need([struct.unpack_from('<5I',row,82868+i*20) for i in range(events)]==model[3] and not any(row[82868+events*20:87988]),'Exact97 ordered source/native events and unused tail')
    need([struct.unpack_from('<7I',row,87988+i*28) for i in range(3)]==model[4],'Actual native stdcall frames/cleanup/continuations')
    return model
def differences(original,row,inp,model,level):
    t=struct.unpack_from('<27I',original);W=t[9];lo=t[7];size=t[8];variable=91348+40*(t[18]+t[19]);stack1=original[variable+size:variable+2*size]
    s1=row[3532:7036];fx1=row[7548:8060];original_fx=original[700:1212];env=original[2264:2292]
    fx_diff=[i for i in range(512) if fx1[i]!=original_fx[i]]
    defined_fp={'CW':h(fx1)==h(original_fx)==h(env), 'SW':h(fx1,2)==h(original_fx,2)==h(env,4),
        'abridged_FTW':fx1[4]==original_fx[4]==0 and h(env,8)==0xffff,
        'MXCSR':u(fx1,24)==u(original_fx,24), 'raw80_all_physical_slots':all(fx1[32+i*16:42+i*16]==original_fx[32+i*16:42+i*16] for i in range(8)),
        'legacy_IP_CS_FOP_DP_DS':all(s1[2768+f:2768+f+n]==env[e:e+n] for f,e,n in ((8,12,4),(12,16,2),(6,18,2),(16,20,4),(20,24,2)))}
    need(all(defined_fp.values()),'Measured defined FP/legacy agreement without fullFX equality')
    ocpu=list(struct.unpack_from('<10I',original,148));projected=ocpu[:];projected[4]=ocpu[4]-W+0x20001800;projected[9]=0x78004232
    need(cpu(s1)==projected,'Observed final complete32CPU with explicit ESP/outerPC transport')
    pages1=row[46004:82868];stack=row[46004+7*4096:46004+8*4096]
    stack_diff=[];observed=[]
    for i in range(4096):
        if inp[4700+i]:
            a=W-0x800+i;original_byte=stack1[a-lo];observed.append(i)
            if stack[i]!=original_byte:stack_diff.append(i)
    source_bytes=set()
    for kind,pc,address,value,width in model[3]:
        if kind==1 and 0x20001000<=address and address+width<=0x20002000:source_bytes.update(range(address-0x20001000,address-0x20001000+width))
    detailed=[]
    for a,b in ranges(stack_diff):
        detailed.append({'guest_page_offsets':[a,b],'original_addresses':[W-0x800+a,W-0x800+b],
            'original_after_hex':stack1[W-0x800+a-lo:W-0x800+b-lo].hex(),'native_after_hex':stack[a:b].hex(),
            'source_emitted_write_offsets_in_range':[i for i in range(a,b) if i in source_bytes]})
    source_provider=original[31020:59692];provider_differences=[]
    for i in range(7*4096):
        if source_provider[i]!=pages1[i]:provider_differences.append(i)
    need(set(provider_differences)<=set(range(3*4096+0x98,3*4096+0x9c))|set(range(3*4096+0xd0,3*4096+0xd4)), 'All provider output differences confined to two explicit owning IAT transports')
    return {'level':level,'original_id':t[0],'defined_FP_fields_agree':defined_fp,
        'CPU_agrees_after_only_declared_ESP_outerPC_projection':True,
        'full512_FX_equal':not fx_diff,'all_differing_FX_byte_offsets':fx_diff,'differing_FX_ranges':ranges(fx_diff),
        'all_differing_FX_values':[{'offset':i,'original':original_fx[i],'native':fx1[i]} for i in fx_diff],
        'SIMD_volatile_observation':'x86 original service-modified SIMD is retained; native guest vector preservation is its declared representative, not fullFX equivalence',
        'original_FX_after_sha256':hashlib.sha256(original_fx).hexdigest(),'native_FX_after_sha256':hashlib.sha256(fx1).hexdigest(),
        'observed_stack_byte_count':len(observed),'all_differing_observed_stack_bytes':len(stack_diff),'differing_observed_stack_ranges':detailed,
        'source_emitted_stack_write_byte_coverage':ranges(sorted(source_bytes)),
        'ECX_ABI_residual_halfwords':[{'delta':d,'original_after_hex':stack1[W+d-lo:W+d-lo+2].hex(),'native_after_hex':stack[0x800+d:0x800+d+2].hex()} for d in (-34,-42)],
        'all_differing_provider_page_offsets':provider_differences,'provider_difference_scope':'Exactly two owning IAT pointer transports; no provider data/output projection',
        'whole_real_stack_or_fullFX_equivalence_claim':False}
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private author validation directory');files={};bindings={}
    for pins in (BASE/'run-normal-r1/pins.json',BASE/'preparation-r1/pins.json'):
        for p,v in read(pins)['files'].items():need(sha(p)==v,'Frozen physical replay association '+p);files[p]=v
        files[str(pins)]=sha(pins)
    original=(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin').read_bytes();orows=[];offset=32
    for i in range(48):n=u(original,offset);orows.append(original[offset+4:offset+4+n]);offset+=4+n
    need(original[offset:]==b'COMPLETE','Whole48 original rows retained')
    inputs=(BASE/'preparation-r1/before-inputs.bin').read_bytes();need(inputs[:8]==b'MW4FRIN1' and len(inputs)==211128,'Exact input schema')
    ins=read(ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json');provider=M.PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');game=M.PE(ROOT/'MW3/Mech3.exe');program={}
    for graph in ins['complete_graphs']:
        for i in graph['instructions']:
            need(provider.bytes(i['address'],i['size']).hex()==i['bytes_hex'],'Every actual provider instruction byte')
            need(i['address'] not in program or program[i['address']]==i,'Consistent recovered source CFG');program[i['address']]=i
    need(len(program)==204,'All complete writer dependency nodes retained');pack=(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin').read_bytes()
    differences_all=[];pcs=set();controls=0;count=0
    for level in ('O0','O2'):
        raw=(BASE/'run-normal-r1'/('native-'+level+'.bin')).read_bytes();need(len(raw)==24+24*STRIDE+8 and raw[:8]==b'MW4FDRN1' and raw[-8:]==b'COMPLETE','Exact complete actual replay raw')
        for i in range(24):
            inp=inputs[24+i*8796:24+(i+1)*8796];need(inp==projection(orows[i]),'Every input byte independently rederived from only original BEFORE plus explicit projection')
            row=raw[24+i*STRIDE:24+(i+1)*STRIDE];model=native(row,inp,program,pack,game,bindings);pcs.update(model[5]);count+=1
            differences_all.append(differences(orows[i],row,inp,model,level))
            for p in (28,28+2112,28+2168,28+2768,28+2776,28+16,28+2616,3532,3532+2768,3532+3280,7036,7548,8060,9084,9140,9140+7*4096+0x800,46004,46004+6*4096+0xc2c,46004+7*4096+0x7de,82868,87988,88072+20,88072+28,88072+4396):
                bad=bytearray(row);bad[p]^=1
                try:native(bad,inp,program,pack,game,{})
                except Exception:controls+=1
                else:raise ValueError('Required raw source/seed observer corruption accepted '+str(p))
    out.mkdir();save(out/'observed-differences.json',{'rows':differences_all,'normalization_of_original_or_native_raw':False})
    save(out/'report.json',{'passed':True,'scope':'Author whole native source/BEFORE model and explicit observed original differences; independent acceptance pending',
        'native_records':count,'before_only_inputs':24,'complete_State_bytes':3504,'whole_owned_pages':9,'ordered_events':count*97,'actual_routes':count*3,
        'source_dependency_PCs':len(program),'actual_reached_PCs':sorted(pcs),'observer_corruptions_rejected':controls,
        'defined_FP_and_final_CPU_projection_agreement_rows':count,'full512_FX_equal_rows':sum(r['full512_FX_equal'] for r in differences_all),
        'FX_difference_offsets_union':sorted({i for r in differences_all for i in r['all_differing_FX_byte_offsets']}),
        'host_FP_scope':'Internal restoration checkpoints only; final C++ volatile SIMD padding equality not claimed',
        'native_source_model_author_only':True,'independent_acceptance':False,'whole_original_stack_or_fullFX_equivalence':False,
        'whole_CRT_startup_or_M4_complete':False})
    files.update(bindings)
    for p in (PRIOR,pathlib.Path(__file__).resolve(),ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json',ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h'):files[str(p)]=sha(p)
    for p in out.rglob('*'):
        if p.is_file():files[str(p)]=sha(p)
    save(out/'pins.json',{'files':files});print(json.dumps({'passed':True,'records':count,'controls':controls,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
