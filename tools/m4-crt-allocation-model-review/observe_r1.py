"""Read-only current native allocation/source/model observation.

Current strict archives are inputs, not executable commands. Expected machines
come from the pinned full original BEFORE model, literal source prediction, and
typed finite measured API outputs. No captured AFTER machine is a model seed.
"""
import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import time
sys.dont_write_bytecode=True
import predict_v3 as P
import metadata
from transport import StrictUnion
from exports import PhysicalExports
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from paths import publish_bytes,workspace_path
from manifests import normalized,unique_object,verify_manifest
from stages import verify_stage
REC_SHA='5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6'
ACCEPT_SHA='7a71e5de996f841010817182875a7e068eba0dee9f7e0645efaca9bfde60aeaf'
CORE_PINS={'consumer.py':'2d6f357baabea5e2fa750fb7d111bb81ab313e4fe39d05c8c613f23aef2606e8',
 'before.py':'819ec625f266e99c1ce6c7bd2209e030a00a29dd283b060c3c61b5d8aea97ea6',
 'prefix.py':'9f1eafac2333c97cc5192b0681e57d3968269617a13a1b25c7e649eb5dee716e',
 'ownership.py':'bb812c5474934f520d421ac8fcc30ec2239b1a2c367feaaa66763ec229ef930d',
 'positive.py':'1e5ae8d9fc0a5f56eb86890a03e9b57e7d3ecd3a65e7ec74ea7b491674fc845a'}
ALLOCATION_SPANS=(('allocation-caller-source.bin',0x78001843,9),('allocation-malloc-source.bin',0x780012b3,18),
 ('allocation-size-source.bin',0x780012c5,30),('allocation-worker-source.bin',0x780012e3,173),
 ('allocation-round-source.bin',0x7800cc97,21),('allocation-null-source.bin',0x7800cc3f,35),
 ('allocation-free-source.bin',0x78001390,177),('allocation-freecold-source.bin',0x7800cc39,6))
SIZES=(0,1,24,31,32,4096)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(path.read_bytes() if hasattr(path,'read_bytes') else Path(path).read_bytes(),object_pairs_hook=unique_object)


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def words(path,count,width='I'):
    raw=path.read_bytes();P.need(len(raw)==count*(4 if width=='I' else 8),'Complete typed capture '+str(path))
    return struct.unpack('<'+str(count)+width,raw)


class NamedAPI:
    def __init__(self,add,eq):self.add=add;self.eq=eq;self.evidence=[];self.physical=PhysicalExports(add)
    def check(self,row,stem,name):
        raw=(row/(stem+'-api-before.bin')).read_bytes();self.eq((row/(stem+'-api-after.bin')).read_bytes(),raw,'Same actual API identity before/after '+name)
        P.need(len(raw)==2184,'Full2184B actual API identity')
        target,named,owner,ownernamed=struct.unpack_from('<4Q',raw)
        base,size,allocation,state,typ,protection,reserved=struct.unpack_from('<3Q4I',raw,32)
        P.need(target!=0 and owner!=0 and target==named==ownernamed and owner==allocation and
            allocation<=base<=target<base+size<=2**64 and state==0x1000 and typ==0x1000000 and protection&0xf0 and not protection&0x101,
            'Actual committed executable API owner/full-width target')
        digest=raw[72:136].decode('ascii');filename,separator,tail=raw[136:].decode('utf-16-le').partition('\0')
        P.need(separator and filename and all(char=='\0' for char in tail),'Complete API module path')
        if name in ('HeapAlloc','HeapFree'):
            proof=(row/(stem+'-export-before.bin')).read_bytes()
            self.eq((row/(stem+'-export-after.bin')).read_bytes(),proof,'Same physical requested/owner proof before and after '+name)
            item=self.physical.proof(proof,name,raw)
        else:
            path=self.add(Path(filename),digest);rva,forwarder,image_size=self.physical.get(path,digest,name)
            P.need(not forwarder,'Measured owner direct named export')
            self.eq(target,owner+rva,'Independent actual API export/RVA '+name);P.need(owner<=target<owner+image_size<=2**64,'Actual target within owner image')
            item=dict(name=name,target=target,owner=owner,path=str(path),sha256=digest,export_RVA=rva)
        if item not in self.evidence:self.evidence.append(item)


def finite_witness(row,index,eq,APIs):
    job=words(row/'allocation-job.bin',32);w=words(row/'allocation-witness.bin',16,'Q');r=words(row/'allocation-registry.bin',24,'Q')
    hw=words(row/'allocation-heap-witness.bin',16,'Q');hr=words(row/'allocation-heap-registry.bin',18,'Q');q=words(row/'allocation-query-witness.bin',20,'Q')
    request=SIZES[index];extent=(max(request,1)+15)&0xfffffff0
    eq(job,(0,request,5,118+(2 if request==0 else 0),4,22,10,6,10,0,0x78001424,P.FREE_MARKER,
            1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,P.ALLOC,extent,extent,job[30],job[30]),'Exact ordinary actual functional lifecycle job')
    P.need(job[30]<=0xffffffff,'Finite caller DWORD error')
    eq(hw[:6],(1,0,1,0,4096,0),'Actual noninjected HeapCreate request')
    P.need(hw[6]!=0 and hw[6]!=0x48450001 and hw[7]==0x48450001 and hw[11]==hw[6],'Private full heap and opaque guest token')
    eq((hw[8],hw[10]),(job[30],job[30]),'Actual HeapCreate restored caller error')
    eq(hw[12:],(0x20001848,0x780039d6,0x20001858,0x780039d6),'Real HeapCreate ABI frame')
    eq(hr[2:11],(1,0x48450001,hw[6],1,1,0,1,1,1),'Actual private heap exactly acquired/released once')
    eq(hr[12:],(1,0,0,1,hw[6],0),'Same full HANDLE cleanup without rollback/skip/duplicate')
    P.need(hr[0]==1 and hr[1]!=0 and hw[9]<=0xffffffff and hr[11]<=0xffffffff,'Typed private heap owner and measured errors')
    eq(w[:3],(1,0,extent),'Actual HeapAlloc flags0 and source-rounded extent')
    P.need(w[3]!=0 and w[3] not in (P.ALLOC,0x48450001,hw[6]) and w[8]!=0 and w[8]<=0xffffffff,'Distinct actual full pointer and successful raw HeapFree BOOL')
    eq((w[4],w[6],w[11],w[13]),(job[30],)*4,'Actual allocate/free caller LastError restored')
    eq((w[7],w[9],w[10],w[14],w[15]),(1,hw[6],w[3],0,0),'One same-full-pointer same-heap source HeapFree')
    P.need(w[5]<=0xffffffff and w[12]<=0xffffffff,'Actual unconstrained DWORD allocation/free errors')
    eq(r,(1,hr[1],1,P.ALLOC,w[3],request,extent,0,1,0,1,1,0,1,1,1,1,0,0,0,hw[6],w[3],P.MALLOC_MARKER,P.FREE_MARKER),
        'Complete24Q allocation registry; successful source release and zero diagnostic cleanup')
    qi,qo=(row/'allocation-query-input.bin').read_bytes(),(row/'allocation-query-output.bin').read_bytes()
    P.need(len(qi)==len(qo)==148 and struct.unpack_from('<I',qi)[0]==148,'Actual historical query full148B scratch')
    eq(q[:3],(1,1,1),'One actual named version query');P.need(q[3]<=0xffffffff and q[9]<=0xffffffff,'Actual raw query BOOL/errors')
    eq(q[4:8],(148,0x200017b8,0x20000618,0x78003a31),'Actual query authentic frame/buffer')
    eq((q[8],q[10]),(job[30],job[30]),'Actual query caller error restoration');eq(q[11:16],(37,1,1,1,1),'Complete query transport/return')
    _,major,minor,build,platform=struct.unpack_from('<5I',qo);P.need(q[3]!=0 and platform==2 and major>=5,'Measured actual output qualifies mode1; no hardcoded version')
    eq(q[16:],(1,0,major,platform),'Actual query source branch predicate')
    initial=(row/'allocation-initial.bin').read_bytes();P.need(len(initial)==extent,'Actual native HeapAlloc complete owned extent bytes')
    for stem,name in (('create','HeapCreate'),('destroy','HeapDestroy'),('query','GetVersionExA'),('alloc','HeapAlloc'),('free','HeapFree')):
        APIs.check(row,'allocation-'+stem,name)
    export_proofs={stem:(row/('allocation-'+stem+'-export-before.bin')).read_bytes() for stem in ('alloc','free')}
    return dict(owner=hr[1],handle=hw[6],pointer=w[3],request=request,extent=extent,BOOL=w[8],initial=initial,
        allocation_witness=w,heap_witness=hw,heap_registry=hr,query=q,query_input=qi,query_output=qo,
        response=dict(input=qi,output=qo,result=q[3]),major=major,minor=minor,build=build,platform=platform,export_proofs=export_proofs)


def main(args):
    started=time.perf_counter_ns();out=workspace_path(ROOT/'reports/m4-crt-allocation-model-review'/args.name,reports=True)
    P.need(re.fullmatch('observe-r[1-9][0-9]*',args.name) and not out.exists(),'Fresh independent current observer output')
    files={};checks=0
    def add(path,digest=None):
        path=Path(path).absolute();key=normalized(str(path));value=sha(path)
        P.need(digest is None or value==digest,'Exact current physical dependency '+str(path))
        P.need(key not in files or files[key]==value,'Unique exact dependency');files[key]=value;return path
    def eq(actual,expected,why):
        nonlocal checks;checks+=1
        if actual!=expected:
            if isinstance(actual,bytes) and isinstance(expected,bytes):
                mismatch=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
                why+=' first_difference='+str(mismatch)+' lengths='+str((len(actual),len(expected)))
            raise ValueError(why)
    recovery=read(add(ROOT/'reports/m4-crt-allocation-recovery/recovery-r1/report.json',REC_SHA))
    P.need(recovery['passed'],'Sealed exact allocation source recovery')
    add(ROOT/'reports/m4-crt-heap-return-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    execution_path=add(Path(args.execution)/'report.json',args.execution_sha);execution=read(execution_path)
    P.need(execution['passed'],'Actual current author native receipt passes before independent observation')
    eq((execution['native_stages_completed'],execution['positive_sequences'],execution['causal_sequences']),(2,12,24),'Two current native levels and exact ordinary/directed row inventory')
    P.need(execution['native_executed_by_coordinator'] is True and execution['original_executed'] is False and
           execution['game_launched'] is False and execution['original_attach_proved'] is False and
           execution['full_CRT_complete'] is False and execution['whole_M4_complete'] is False,'Explicit bounded current native execution scope')
    build=read(add(execution['build_path'],execution['build_sha256']))
    P.need(build['passed'],'Exact successful owning worker build')
    for category in ('files','sources','source_files','tools','libraries','entry_objects','compiler_read_headers','artifacts','input_files'):
        for path,digest in execution.get(category,{}).items():add(path,digest)
    if execution_path.with_name('pins.json').exists():
        pin_path=add(execution_path.with_name('pins.json'))
        for path,digest in read(pin_path)['files'].items():add(path,digest)
    core=ROOT/'tools/m4-crt-heap-return-root'
    for filename,digest in CORE_PINS.items():add(core/filename,digest)
    for path in (Path(__file__),Path(P.__file__),Path(metadata.__file__),Path(__file__).with_name('transport.py'),Path(__file__).with_name('exports.py'),P.MODEL_PATH,Path(__file__).with_name('README.md'),
                 Path(__file__).with_name('README-observer.md'),Path(sys.executable),
                 ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/stages.py'):
        add(path)
    previous={name:sys.modules.get(name) for name in ('consumer','before')}
    consumer=load('allocation_review_consumer',core/'consumer.py');sys.modules['consumer']=consumer
    try:
        before=load('allocation_review_before',core/'before.py');sys.modules['before']=before
        prefix=load('allocation_review_prefix',core/'prefix.py');ownership=load('allocation_review_ownership',core/'ownership.py')
    finally:
        for name,value in previous.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
    F,M,OLD=consumer.F,consumer.M,consumer.OLD
    original=add(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2')
    out.mkdir(parents=True)
    program,providers,maths,ctrl,init,mainargs,argv,pages,commands=M.source_material(out)
    heap_program,source_pages,heap_commands=prefix.source_material(out);pages.update(source_pages);wp,pp,gp=M.R.source_material()
    payloads=[M.R.project(value) for value in M.R.originals(original.read_bytes())[:6]]
    APIs=NamedAPI(add,eq);rows=[];machine_sets=metadata_sets=actual_allocation_pages=0;archives=[]
    # Immutable reused unused-job schema, independently reviewed at the prior
    # gate. Only source constants and the declared row index enter evaluation.
    old_ast=ast.parse((core/'positive.py').read_text());function=next(node for node in old_ast.body if isinstance(node,ast.FunctionDef) and node.name=='positive')
    unused_assignment=next(node for node in function.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='unused' for t in node.targets))
    unused_expression=compile(ast.Expression(unused_assignment.value),str(core/'positive.py'),'eval')
    try:
      with contextlib.ExitStack() as stack:
        readers={}
        for level in ('O0','O2'):
            identity=execution['levels'][level];manifest=add(identity['transport_manifest'],identity['transport_sha256'])
            worker=add(identity['worker']);eq(normalized(str(worker)),normalized(build['workers'][level]),'Native level uses the exact owning built worker')
            eq({normalized(p):h for p,h in build['artifacts'].items()}.get(normalized(str(worker))),sha(worker),'Owning build authenticates the actual worker artifact')
            reader=stack.enter_context(StrictUnion(manifest,identity['transport_sha256'],add))
            eq(reader.read_bytes('COMPLETE'),b'COMPLETE','Actual current direct archive completed publication')
            if 'logical_files' in identity:eq(len(reader.names()),identity['logical_files'],'Exact strict archive inventory count')
            eq((len(reader.parts),reader.value['payload_bytes']),(identity['archive_parts'],identity['payload_bytes']),'Exact direct part/payload association')
            for field in ('native_stage',):
                stage_path=add(Path(identity[field])/'stage.json',identity['stage_sha256']);stage=verify_stage(stage_path.parent,sha(stage_path))
                P.need(stage['recorded_stage_passed'],'Actual current native stage passed before observer')
                stage_record=read(stage_path)
                eq([normalized(v) for v in stage_record['argv']],[normalized(v) for v in identity['argv']],'Exact current native stage request association')
                eq(len(stage_record['argv']),7,'Complete native request arguments')
                eq(normalized(stage_record['argv'][0]),normalized(str(worker)),'Actual stage runs this owning worker')
                eq(normalized(stage_record['argv'][6]),normalized(str(manifest.parent)),'Actual stage emits this final transport directory')
                inputs={normalized(p):h for p,h in stage_record['input_sha256'].items()}
                for argument in stage_record['argv'][:6]:
                    argument_path=add(argument);eq(inputs.get(normalized(str(argument_path))),sha(argument_path),'Actual worker/source request is a stable stage input')
                eq({normalized(p):h for p,h in stage_record['artifact_sha256'].items()}.get(normalized(str(manifest))),identity['transport_sha256'],
                   'Actual worker stage output is this exact completed direct manifest')
            archives.append(dict(level=level,transport_manifest=str(manifest),transport_sha256=identity['transport_sha256'],
                parts=reader.parts,logical_records=len(reader.names()),payload_bytes=reader.value['payload_bytes']))
            readers[level]=reader
        for level,reader in readers.items():
          for index,payload in enumerate(payloads):
            row=F.LogicalPath(reader,'row-'+str(index));result=read(row/'result.json')
            P.need(result['passed'] and result['scenario']==index and result['control']==0 and result['writer_complete'] and result['entry_executed'] and
                   result['poisoned_retry'] and not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
                   'Exact current ordinary actual request and bounded original carry')
            eq((row/'input.bin').read_bytes(),payload,'Declared current ordinary original BEFORE input')
            actual=finite_witness(row,index,eq,APIs)
            entry,earlier=before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,level)
            P.need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used and not entry.args_accesses,'Healthy full original BEFORE mainargs seam')
            initial=prefix.predict(entry,heap_program,0x48450001,actual['response'])
            eq(initial['initializer_RET'],True,'Source-derived qualifying initializer genuinely returns')
            chain=P.predict(initial,actual['request'],actual['initial'],actual['BOOL'])
            expected_phases=copy.deepcopy(earlier);expected_phases.update(copy.deepcopy(initial['phases']))
            for tag,value in chain['phases'].items():expected_phases[tag]=before.stage(value['state'],value['fx'],value['cpu'],value['memory'])
            tags={name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/')==1}
            eq(tags,set(expected_phases),'Exact full current ordinary phase inventory');eq(len(tags),69,'All69 wholemachine checkpoints')
            for tag,expected in expected_phases.items():
                for filename,address,size in ALLOCATION_SPANS:
                    raw=initial['memory'][address&~4095][address&4095:(address&4095)+size];expected[filename]=bytes(raw)
                phase_metadata,known,mapped=metadata.phase(tag,expected,initial,chain,actual,ownership);expected.update(phase_metadata)
                phase=row/tag;actual_files=row.inventory[row.name+'/'+tag]
                if mapped:
                    expected['allocation-owned-page.bin']=bytes(chain['phases'][tag]['memory'][P.ALLOC]);actual_allocation_pages+=1
                else:P.need('allocation-owned-page.bin' not in actual_files,'Actual guest allocation absent after release/before publication')
                # Entire machine plus captured source and typed ownership state.
                eq(actual_files,set(expected),'Exact whole phase capture fields '+tag)
                for filename,value in expected.items():eq((phase/filename).read_bytes(),value,'Independent whole phase '+tag+'/'+filename)
                machine_sets+=1;metadata_sets+=1
            # Row-level genuine source/ABI/protocol ledgers are not expected
            # from native AFTER State, public flags or the author access plan.
            eq((row/'allocation-source-accesses.bin').read_bytes(),metadata.packed(chain['accesses'],5,2560),'Exact complete independent source access ledger')
            eq((row/'allocation-api-return-accesses.bin').read_bytes(),metadata.packed([initial['API_return_access'],initial['query_return_access'],*chain['API_reads']],5,160),'Exact four distinct real API return-word reads')
            eq((row/'allocation-external-accesses.bin').read_bytes(),metadata.packed(chain['external_accesses'],5,320),'Separate external argument/return store ledger')
            eq((row/'allocation-external-projections.bin').read_bytes(),metadata.packed(chain['external_projections'],8,256),'Separate external EIP/ESP projections/argument cleanups')
            eq((row/'allocation-pattern.bin').read_bytes(),chain['pattern'],'Declared client protocol full actual extent pattern')
            eq((row/'allocation-backing.bin').read_bytes(),chain['pattern']+bytes(4096-chain['extent']),'Declared padding/private final byte mirror')
            representatives=initial['undefined']+chain['caller']['undefined']+chain['malloc']['undefined']+chain['free']['undefined']+chain['null']['undefined']
            # The exact lifted AND AL,F0 writes AF representative 0 directly;
            # unlike the other sites it emits no undefined-intrinsic callback.
            # Its source machine effect remains in the frozen affine model.
            eq((len(representatives),representatives.count((0x7800cca4,0))),(11,1),'Eleven defined research representative effects including direct AND AF0')
            undefined=[pc for pc,representative in representatives if pc!=0x7800cca4]
            eq((row/'allocation-undefined.bin').read_bytes(),struct.pack('<32I',*undefined,*([0]*(32-len(undefined)))),
               'Exact ten actual undefined callback records; direct AND AF0 is a separate instruction effect')
            events=[(1,0x7800183c,0x20001860,0),(2,0x7800183e,0x780039bf,0x78001843),
                (3,0x780039d0,0x7802e0a8,0x3461e),(4,0x780039d0,0x20001848,0x780039d6),
                (5,0x780039d8,0x78035000,0x48450001),(6,0x780039e3,0x78003a0c,0x780039e8),
                (7,0x78003a14,0x780058b5,0x78003a19),(8,0x780058cf,0x78003a19,0x20000620),
                (9,0x78003a2b,0x7802e0a0,0x34600),(10,0x78003a2b,0x20000618,0x78003a31),
                (11,0x78003a7f,0x780039e8,0x20001854),(12,0x780039eb,0x78035004,1),
                (13,0x78003a0b,0x78001843,0x20001858),
                (20,0x780012bd,0x780012c5,0x780012c2),(21,0x780012d4,0x780012e3,0x780012d9),
                (22,0x7800137f,0x7802e094,0x345c6),(24,0x78001375,0x780012d9,0x20001844),
                (25,0x780012e2,0x780012c2,0x2000184c),(26,0x780012c4,P.MALLOC_MARKER,0x20001858),
                (23,0x78001430,0x7802e090,0x345ba),(27,0x78001424,P.FREE_MARKER,0x20001858),
                (27,0x78001424,P.FREE_MARKER,0x20001858)]
            eq((row/'allocation-events.bin').read_bytes(),metadata.packed(events,4,768),'Authentic CALL/RET and declared finite API event chronology')
            eq((row/'allocation-query-output-accesses.bin').read_bytes(),metadata.packed(initial['query_output_accesses'],5,1280),'Historical actual query transport ledger remains distinct')
            eq((result['fault_reason'],result['fault_site'],result['fault_target']),(0,0x78001424,P.FREE_MARKER),'Bounded research caller terminal source RET')
            eq((result['source_events'],result['writer_events'],result['data_routes']),(len(entry.events),97,1),'Preserved original source events/Runtime CALL records')
            evidence=OLD.evidence(entry)
            evidence['mainargs-job.bin']=struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,0x78001424,P.FREE_MARKER)
            evidence['mainargs-events.bin'],evidence['mainargs-accesses.bin']=bytes(256),bytes(1280)
            for filename,wanted in evidence.items():
                captured=(row/filename).read_bytes()
                eq(json.loads(captured,object_pairs_hook=unique_object) if filename.endswith('.json') else captured,wanted,
                   'Complete source-derived earlier job/CPU/CALL/event evidence '+filename)
            entry_job=words(row/'entry-job.bin',10)
            eq(entry_job[5:8],(0,0x78001424,P.FREE_MARKER),'Typed outer bounded caller-return fault')
            eq(entry_job[8:],(0,0),'No fixture entry callback')
            for actor in ('writer','entry'):M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
            unused=eval(unused_expression,dict(vars(prefix),struct=struct,index=index))
            for filename,value in unused.items():eq((row/filename).read_bytes(),value,'Exact unused ancestral/later service '+filename)
            unused_hr=(0,)*24+(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x78003a0c,0x780039e3,21,84,
                0,0x780058b5,0x78003a14,0x78003a19,0x78003a2b,0x7802e0a0,0x34600,0x78003a31,0,0,86,2086,
                0,0,0,0,0,0,0,0,0,0,26,23,8,3,0x78003a5c,0x7802e09c,0x345e6,0x7800ccc5,148,2086,
                0,0,0,0,0,0,8,4)
            eq(words(row/'heap-return-job.bin',72),unused_hr,'Frozen ancestor return producer has constructor-only exact job')
            for filename,capacity in (('heap-return-accesses.bin',1280),('heap-return-api-accesses.bin',160),('heap-return-events.bin',256),
                ('heap-return-undefined.bin',32),('heap-return-scheduler.bin',32),('heap-return-witness.bin',128),('heap-return-query-witness.bin',160),
                ('heap-return-output-accesses.bin',1280),('heap-return-query-input.bin',148),('heap-return-query-output.bin',148),('heap-return-lower-input.bin',4096)):
                eq((row/filename).read_bytes(),bytes(capacity),'Exact unused heap-return ledger/witness '+filename)
            owners=[actual['owner']]
            for filename in ('heap-create-registry.bin','heap-mode-registry.bin','heap-version-registry.bin','heap-return-registry.bin'):
                values=words(row/filename,18,'Q');P.need(values[0]==1 and values[1]!=0 and values[1] not in owners and values[2:]==(1,*(0,)*15),'Distinct constructor-only unused private owner');owners.append(values[1])
            reason='Functional source allocation/free research caller completed; original attach remains unadmitted'
            for stem in ('mainargs','allocation'):eq((row/(stem+'-reason.txt')).read_text().strip(),reason,'Exact first bounded functional diagnostic')
            for stem in ('filename','commandline','parser','locale','heap','heap-create','heap-mode','heap-version','heap-return'):
                eq((row/(stem+'-reason.txt')).read_text().strip(),'','No invented unused-service diagnostic')
            root_files=set(evidence)|set(unused)|{'heap-create-registry.bin','heap-mode-registry.bin','heap-version-registry.bin',
                'input.bin','writer-record.bin','writer-host-before.bin','writer-host-after.bin','entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json',
                'matherr-reason.txt','control-reason.txt','initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt',
                'parser-reason.txt','locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-mode-reason.txt','heap-version-reason.txt','heap-return-reason.txt',
                'heap-return-job.bin','heap-return-accesses.bin','heap-return-api-accesses.bin','heap-return-events.bin','heap-return-undefined.bin',
                'heap-return-scheduler.bin','heap-return-witness.bin','heap-return-registry.bin','heap-return-lower-input.bin','heap-return-query-witness.bin',
                'heap-return-query-input.bin','heap-return-query-output.bin','heap-return-output-accesses.bin',
                'allocation-job.bin','allocation-source-accesses.bin','allocation-api-return-accesses.bin','allocation-events.bin','allocation-undefined.bin',
                'allocation-external-accesses.bin','allocation-external-projections.bin','allocation-registry.bin','allocation-witness.bin','allocation-progress.bin',
                'allocation-initial.bin','allocation-pattern.bin','allocation-backing.bin','allocation-heap-registry.bin','allocation-heap-witness.bin',
                'allocation-query-witness.bin','allocation-query-input.bin','allocation-query-output.bin','allocation-query-output-accesses.bin','allocation-reason.txt'}
            root_files|={'allocation-'+stem+'-api-'+side+'.bin' for stem in ('create','destroy','query','alloc','free') for side in ('before','after')}
            root_files|={'allocation-'+stem+'-export-'+side+'.bin' for stem in ('alloc','free') for side in ('before','after')}
            eq(row.inventory[row.name],root_files,'Exact whole ordinary root record inventory')
            rows.append(dict(level=level,index=index,requested_bytes=actual['request'],rounded_extent=chain['extent'],source_PCs=len(chain['PCs']),
                source_accesses=len(chain['accesses']),source_CALLs=9,genuine_source_RETs=8,separate_API_return_reads=4,
                source_AF_representative_effects=11,actual_undefined_callback_records=10,direct_AND_AF_representative=0,
                current_phases=69,State_bytes=3504,FX_bytes=512,Runtime_CPU_bytes=40,carried_whole_pages=21,
                actual_HeapCreate_calls=1,actual_GetVersionExA_calls=1,actual_HeapAlloc_calls=1,actual_source_HeapFree_calls=1,
                successful_source_HeapFree_calls=1,NULL_free_HeapFree_calls=0,diagnostic_allocation_cleanup_calls=0,actual_HeapDestroy_calls=1,
                native_heap_handle=actual['handle'],native_allocation_pointer=actual['pointer'],source_NULL_free_EAX=chain['null']['previous_SEH'],
                native_initial_sha256=hashlib.sha256(actual['initial']).hexdigest(),private_owner_count=len(owners),
                actual_version=dict(raw_BOOL=actual['query'][3],major=actual['major'],minor=actual['minor'],build=actual['build'],platform=actual['platform'])))
        # Bind actual imported source-only modules, not ancestral capture trees.
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and Path(path).suffix=='.py' and Path(path).absolute().is_relative_to(ROOT/'tools'):add(path)
        for path in out.iterdir():
            if path.is_file():add(path)
        physical=verify_manifest(files)
        report=dict(schema='mw34-m4-allocation-native-model-observation-v1',passed=True,
            scope='All current ordinary wholemachine/source/finiteAPI/ownedallocation/normalSEH checkpoints from original BEFORE; explicit external research caller/client protocol',
            execution_sha256=args.execution_sha,source_recovery_sha256=REC_SHA,frozen_affine_predictor_sha256=P.MODEL_SHA,
            observer_predictor_sha256=sha(P.__file__),ordinary_rows=len(rows),current_native_checkpoints_per_row=69,rows=rows,checks=checks,
            complete_machine_sets=machine_sets,complete_phase_metadata_sets=metadata_sets,actual_owned_allocation_pages_compared=actual_allocation_pages,
            archives=archives,named_API_identities=APIs.evidence,actual_functional_allocations=len(rows),actual_successful_source_releases=len(rows),
            actual_NULL_free_returns=len(rows),NULL_free_additional_API_calls=0,private_HANDLE_and_pointer_truncation=False,
            captured_AFTER_machine_used_as_seed=False,author_expected_state_imported=False,original_BEFORE_model_used=True,
            observer_native_execution=False,observer_API_execution=False,original_provider_executed=False,root_full_causal_model_claim=False,
            original_API_internals_equivalence=False,universal_manifest_version_equivalence=False,normal_SEH_dispatch_or_exceptional_unwind_proved=False,
            directed_fault_wholemachine_model_credit=False,declared_lower_page_original_capture_credit=False,original_guard_stack_growth_proved=False,
            persistent_game_heap_or_full_CRT_claim=False,whole_M4_complete=False,files=files,physical_closure=physical,
            source_decode_commands=commands+heap_commands,seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out/'report.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode())
        publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-allocation-observer-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode())
        print(json.dumps(dict(passed=True,ordinary_rows=len(rows),phases=machine_sets,checks=checks,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        import traceback
        publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('name');parser.add_argument('--execution',required=True);parser.add_argument('--execution-sha',required=True)
    main(parser.parse_args())
