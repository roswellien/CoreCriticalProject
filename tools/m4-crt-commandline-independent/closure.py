"""Independent literal LLVM/source/build and actual compiled causal closure."""
import ctypes as c, hashlib, json, pathlib, re, sys

ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-native'
def need(v,w):
    if not v:raise ValueError(w)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def static_proof():
    # Minimal independent LLVM-C bindings, no imports from lifting/author helpers.
    path=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll';api=c.CDLL(str(path));P=c.c_void_p;U=c.c_uint;ULL=c.c_ulonglong
    def fn(name,rest,*args):
        f=getattr(api,'LLVM'+name);f.restype=rest;f.argtypes=list(args);return f
    context=fn('ContextCreate',P)();parse=fn('ParseIRInContext',c.c_int,P,P,c.POINTER(P),c.POINTER(P));buffer=fn('CreateMemoryBufferWithContentsOfFile',c.c_int,c.c_char_p,c.POINTER(P),c.POINTER(P));disposemod=fn('DisposeModule',None,P)
    td=fn('CreateTargetData',P,c.c_char_p);dispose=fn('DisposeTargetData',None,P);dl=fn('GetDataLayoutStr',c.c_char_p,P);named=fn('GetTypeByName2',P,P,c.c_char_p);size=fn('ABISizeOfType',ULL,P,P);align=fn('ABIAlignmentOfType',U,P,P);count=fn('CountStructElementTypes',U,P);offset=fn('OffsetOfElement',ULL,P,P,U);elements=fn('GetStructElementTypes',None,P,c.POINTER(P));kind=fn('GetTypeKind',U,P);element=fn('GetElementType',P,P)
    getfunc=fn('GetNamedFunction',P,P,c.c_char_p);functype=fn('GlobalGetValueType',P,P);nparams=fn('CountParamTypes',U,P);params=fn('GetParamTypes',None,P,c.POINTER(P));ret=fn('GetReturnType',P,P);bits=fn('GetIntTypeWidth',U,P);conv=fn('GetFunctionCallConv',U,P)
    modules=[];data=[];texts={}
    for name in ('guest','host'):
        p=BASE/'static-r1'/f'{name}.ll';m,b,e=P(),P(),P();need(buffer(str(p).encode(),c.byref(b),c.byref(e))==0,'Own LLVM buffer');need(parse(context,b,c.byref(m),c.byref(e))==0,'Own LLVM parser');modules.append(m);data.append(td(dl(m)));texts[name]=p.read_text()
    try:
        types=re.findall(r'^%([^ =]+) = type',texts['guest'],re.M);need(types==re.findall(r'^%([^ =]+) = type',texts['host'],re.M),'Literal type names/order unchanged')
        layouts={}
        for name in types:
            ty=named(context,name.encode());n=count(ty);a=[[size(d,ty),align(d,ty),[offset(d,ty,i)for i in range(n)]] for d in data]
            need(a[0]==a[1],'Every concrete type guest/host size/alignment/offset equal');layouts[name]=a[0]
        need(layouts['struct.State'][:2]==[3504,8],'Complete State bytes/alignment')
        def struct_element(ty,index):
            array=(P*count(ty))();elements(ty,array);return array[index]
        def gep(ty,indices,d):
            total=indices[0]*size(d,ty)
            for index in indices[1:]:
                k=kind(ty)
                if k==10:total+=offset(d,ty,index);ty=struct_element(ty,index)
                elif k==11:ty=element(ty);total+=index*size(d,ty)
                else:raise ValueError('Unexpected State GEP type')
            return total,size(d,ty)
        state_offsets={}
        for line in texts['host'].splitlines():
            m=re.match(r'\s*(%\w+) = getelementptr (?:inbounds )?(?:nuw )?(%[^, ]+|i8), ptr %state, (.+)',line)
            if m:
                indices=[int(x)for x in re.findall(r'i(?:32|64) (-?\d+)',m[3])]
                if m[2]=='i8':state_offsets[m[1]]=[indices[0],1]
                else:
                    ty=named(context,m[2][1:].encode());a=gep(ty,indices,data[0]);b=gep(ty,indices,data[1]);need(a==b,'All State GEPs equal');state_offsets[m[1]]=list(a)
        need(state_offsets=={'%EAX':[2216,4],'%DSBASE':[2184,4],'%PC':[2472,4],'%8':[2312,1],'%12':[2120,1],'%16':[2472,1],'%36':[2472,1]},'All exact host State fields resolved independently')
        # Verify full guest definition equality after only the declared outer
        # capture and C ABI calling-convention changes. Attribute removal is
        # separate and needed for real fault unwinding.
        def body(text,name):
            m=re.search(r'^define [^\n]*@'+name+r'\([^\n]*\) [^\n]*\{\n(.*?)^\}',text,re.M|re.S);need(m is not None,'Literal complete function definition');return m[1]
        guest=body(texts['guest'],'sub_7800188c');host=body(texts['host'],'sub_7800188c')
        normalized=guest.replace('@__remill_missing_block','@mw34_cmd_outer_capture')
        normalized=re.sub(r'\b(?:x86_stdcallcc|x86_fastcallcc|fastcc)\s+','',normalized)
        need(normalized==host,'Complete actual instruction CFG equality after exact outer capture/ABI mapping')
        need(not re.search(r'\b(?:nounwind|willreturn|undef|poison|inttoptr|ptrtoint|float|double|x86_fp80)\b',texts['host']),'No hidden result/FP or incompatible unwind attributes')
        externs={name:arguments for name,arguments in re.findall(r'^declare [^\n]*?@([^ (]+)\(([^\n]*)\)',texts['host'],re.M)}
        need(set(externs)=={'__remill_read_memory_32','__remill_write_memory_32','__remill_function_call','mw34_cmd_outer_capture'},'Complete typed bridges only')
        functions={'sub_7800188c':('ptr','i32','ptr'),'mw34_cmd_writer':('ptr','i32','ptr'),
                   '__remill_read_memory_32':('ptr','i32'),'__remill_write_memory_32':('ptr','i32','i32'),
                   '__remill_function_call':('ptr','i32','ptr'),'mw34_cmd_outer_capture':('ptr','i32','ptr')}
        for name,expected in functions.items():
            f=getfunc(modules[1],name.encode());need(f and conv(f)==0,'Each compiled definition/bridge uses native C ABI');t=functype(f);n=nparams(t);array=(P*n)();params(t,array)
            actual=tuple('ptr'if kind(x)==12 else'i'+str(bits(x))for x in array);need(actual==expected,'Exact pointer/guest32 bridge signature')
            need(kind(ret(t))==(8 if name=='__remill_read_memory_32' else 12),'Exact bridge return type')
        stores=[]
        for typ,target in re.findall(r'^\s*store (i\d+) [^\n]*?, ptr (%\w+),',host,re.M):
            if target in state_offsets:stores.append({'offset':state_offsets[target][0],'bytes':int(typ[1:])//8})
        need(all(x['offset']in(2312,2472)and x['bytes']==4 for x in stores)and len(stores)==7,'Actual compiled State store extent, no invented EAX write in lifted MOV')
        return {'passed':True,'layouts':layouts,'State_GEPs':state_offsets,'State_stores':stores,'complete_guest_body_equal':True,'native_C_ABI':True,'no_nounwind_or_willreturn':True,'LLVM_C_path':str(path),'LLVM_C_sha256':sha(path)}
    finally:
        for d in data:dispose(d)
        for m in modules:disposemod(m)
        fn('ContextDispose',None,P)(context)

def main(out):
    need(not out.exists() and out.is_relative_to(BASE),'Fresh independent closure path')
    files={};checks=[]
    def bind(p,expected=None):
        p=pathlib.Path(p).resolve();actual=sha(p);need(expected is None or actual==expected,'Exact immutable file '+str(p));need(str(p)not in files or files[str(p)]==actual,'Conflicting binding');files[str(p)]=actual;return actual
    author=BASE/'author-review-r1/report.json';pins=BASE/'author-review-r1/pins.json'
    need(bind(author)=='b4826114a08989c14525a3c6d6972175181432db0461fb9ced8095f69b33eb9c' and bind(pins)=='096dde24b0bb26d42af2d500cc32abf455de8c2fdb02e6b977db86368e39f2a0','Exact frozen author submission')
    ap=read(pins);need(len(ap['bindings'])==2164 and len(ap['historical_replacements'])==63 and len(ap['literal_sources'])==26,'Exact supplied identity/version inventory')
    for row in ap['bindings']:bind(row['path'],row['sha256']);need(pathlib.Path(row['path']).stat().st_size==row['bytes'],'Literal file extent')
    for row in ap['historical_replacements']:bind(row['physical_literal'],row['sha256']);bind(row['build'])
    checks.append({'name':'All2164 author physical bindings,63 exact historical versions and26 final source associations rehashed','passed':True})
    proof=static_proof();bind(proof['LLVM_C_path'],proof['LLVM_C_sha256']);checks.append({'name':'Independent complete two-instruction plus authored JMP lowering/ABI/layout/state-store proof','proof':proof,'passed':True})
    raw=BASE/'independent-raw-foundation-r1/report.json';rawpins=BASE/'independent-raw-foundation-r1/pins.json';rv=read(raw);need(rv['passed'] and rv['actual_records']=={'original':384,'native':768} and len(rv['observer_controls'])==1256,'Own independent full raw model')
    bind(raw);bind(rawpins)
    for p,h in read(rawpins)['files'].items():bind(p,h)
    checks.append({'name':'Own full raw model and1256 observer controls unchanged','passed':True})
    cb=BASE/'independent-causal-r6/build.json';cv=read(cb);need(cv['passed'] and cv['failure'] is None and len(cv['commands'])==6,'Own exact compiled causal run')
    for key in('sources','tools','consumed_libraries','artifacts'):
        for p,h in cv[key].items():bind(p,h)
    bind(cb)
    dependency_headers={}
    for level in('O0','O2'):
        log=BASE/'independent-causal-r6'/f'run-{level}.log';text=log.read_text(encoding='utf-8-sig');line=json.loads(text.strip().splitlines()[-1]);need(line=={'independent':True,'checks':319,'scenarios':28,'original_execution':False},'Actual independent compiled causal assertions')
        source=BASE/'independent-causal-r6'/f'compile-{level}.log'
        for p in re.findall(r'^Note: including file:\s+(.+)$',source.read_text(encoding='utf-8-sig'),re.M):
            path=pathlib.Path(p.strip());dependency_headers[str(path.resolve())]=bind(path)
    for row in cv['commands']:need(row['exit_code']==0,'Actual compiled command success');bind(row['log_path'],row['log_sha256'])
    checks.append({'name':'Own compiled frozen O0/O2 library controls,whole dirty State,real own OS bytes,partial ownership cleanup and terminal faults','checks_per_level':319,'scenarios_per_level':28,'compiler_recorded_dependencies':len(dependency_headers),'passed':True})
    # Retain every own unsuccessful tool/model attempt literally. Old recipes
    # are resolved to the exact pre-build copy, never their changed live path.
    histories=[]
    for i in range(1,6):
        d=BASE/f'independent-causal-r{i}';value=read(d/'build.json');need(not value['passed'],'Preserved own setup/compiler bookkeeping failure')
        for p,h in value['sources'].items():bind(d/pathlib.Path(p).name,h)
        for p,h in value['artifacts'].items():bind(p,h)
        bind(d/'build.json');histories.append({'directory':str(d),'failure':value['failure'],'production_finding':False})
    for d in [BASE/'independent-model-attempt-r1',BASE/'independent-model-attempt-r2',BASE/'independent-closure-attempt-r1',BASE/'independent-closure-attempt-r2']:
        for p in d.iterdir():bind(p)
    # Author's original only uses measured system calls, not a fake native result;
    # the attached original provider is not a complete DLL process-attach run.
    contract=ROOT/'docs/m4-crt-commandline-native-contract.md';bind(contract)
    for p in (ROOT/'tools/m4-crt-commandline-independent').iterdir():
        if p.is_file():bind(p)
    report={'passed':True,'scope':'Independent exact source/raw/build/compiled causal acceptance of bounded OS-backed command-line writer/data route only',
            'checks':checks,'bindings_from_author':2164,'historical_author_versions':63,'own_failed_attempts':histories,'source_build_findings':[],
            'raw_model_path':str(raw),'raw_model_sha256':sha(raw),'compiled_causal_path':str(cb),'compiled_causal_sha256':sha(cb),
            'independent_code_execution':'Only authored independent harness and frozen statically translated native library; original game/vendor instructions not executed by reviewer',
            'prior_dependency_authorship':'Reviewer authored older reference-only data-admission gate; this new OS-backed command-line writer/Registry was authored by another agent. Old dependency credit remains separate.',
            'proof_limits':['Actual original service-after volatile CPU/FP observations are retained; native software State preservation is an explicit representative policy, not proof of full Windows API implementation equivalence',
                            'Eight ASCII commandline fixtures, twelve masked CWs and empty TOP0/7, serial fresh ordinary private paths and trusted stable Runtime borrowers',
                            'Current disk API module/export/RVA association,including x86 System32 redirection,is not complete loaded-code/hotpatch/process dependency attestation',
                            'Original State and access events are not observed; native buffer-copy event is explicit adapter transfer,validation reads are not original instruction tracing',
                            'Direct raw GuestMemory faults bypass registry poison; hostile external mapping/permission replacement,concurrent publication/reparse races and general thread ownership remain excluded',
                            'Complete original DLL/process attach,all CRT/SEH/provider imports,data-consumption paths,full initializer traversal and frontend/menu remain open'],
            'whole_M4_complete':False}
    out.mkdir();rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');bind(rp);pp=out/'pins.json';pp.write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n');print('Independent command-line closure passed',len(files),'bindings',sha(rp),sha(pp))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve())
