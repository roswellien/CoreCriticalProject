"""Closed locale fixture inventory and unchanged rich hardware semantics."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from stages import verify_stage
from paths import publish_bytes

FROZEN_TRANSPORT_SHA = '0feb19971049f6547dc40cdad1f338142d48de4bc8de4f675f2d71b2bc3f619f'
frozen_path = ROOT / 'tools/m4-review-bundles/transport.py'
if sha_file(frozen_path) != FROZEN_TRANSPORT_SHA:
    raise ValueError('Frozen unchanged rich hardware validator transport')
spec = importlib.util.spec_from_file_location('locale_independent_frozen_transport', frozen_path)
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
def need(value,why):
    if not value:raise ValueError(why)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
REQUESTS=[0]*6+list(range(145,157))+list(range(1,81))
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000,0x78035000,0x78005000,0x20000000,0x7800c000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin heap-fragment.bin heap-provider.bin heap-create-witness.bin heap-create-registry.bin heap-mode-selector.bin heap-stack-probe.bin heap-version-branch.bin heap-version-environment.bin heap-version-mode1.bin heap-version-epilogue.bin heap-version-query-witness.bin query-input.bin query-output.bin heap-version-output-accesses.bin'.split())|{f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin heap-accesses.bin heap-events.bin heap-undefined-sites.bin heap-scheduler.bin heap-status.bin heap-api-accesses.bin heap-witness.bin heap-registry.bin heap-create-api-before.bin heap-create-api-after.bin heap-destroy-api-before.bin heap-destroy-api-after.bin independent-ownership.bin declared-lower-input.bin lower-input-status.bin query-witness.bin query-input.bin query-output.bin query-output-accesses.bin query-api-before.bin query-api-after.bin query-status.bin'.split())
BASE_PHASES=set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after heap-create-before heap-create-projected heap-create-after'.split())
NEW=set(range(49,81))|set(range(145,157))
PROVIDER={0,*range(3,11),24,*range(33,49),*NEW}
API=set(PROVIDER);ACTUAL=API-{3};REGISTERED=ACTUAL-{4}
RETURN_BEFORE={0,*range(6,11),24,*range(33,41),*range(42,49),*NEW}
RETURNED=RETURN_BEFORE-{6};PUBLISHED=RETURNED-{7};MODE=set(PUBLISHED)
PROBE={0,9,10,33,34,35,36,37,39,40,42,43,45,47,48,*NEW}
PROBE_AFTER={0,9,10,33,39,43,45,*NEW}
QUERY={0,9,10,*NEW}
QPRE=QUERY-{49,59,71,72,73,74,79,145}
QCALLED=QUERY-{49,50,59,60,71,72,73,74,79,80,145}
QCOMPLETE={0,9,10,55,56,57,58,70,75,76,77,78,151,152,153,154,155,156}
QRETURN_BEFORE=QCOMPLETE-{55,70,151}
QRETURNED=QRETURN_BEFORE-{56,152}
SELECTOR={0,9,10,58,156}
COUNTS={m:0 for m in REQUESTS};COUNTS.update({0:31,2:1,17:1,8:10,9:31,10:31,24:10,33:23,34:14,35:15,36:18,37:19,38:12,39:24,40:12,41:8,42:12,43:24,44:10,45:19,46:10,47:12,48:18})
COUNTS.update({m:8 for m in range(3,8)});COUNTS.update({m:24 for m in NEW});COUNTS.update({58:31,78:30,155:30,156:31})
COPY_COUNTS={m:0 for m in REQUESTS};COPY_COUNTS.update({m:37 for m in QCOMPLETE|{54,150}});COPY_COUNTS.update({52:1,62:1,69:1,149:1,53:19,63:19})
def api_identity(data):
    need(len(data)==2184,'Packed measured API identity extent')
    if not any(data):return None
    address,named,owner,owner_named,base,size,allocation,state,kind,protect,allocation_protect=struct.unpack('<7Q4I',data[:72]);need(address==named==owner_named and owner==allocation and base<=named<base+size and state==0x1000 and kind==0x1000000 and not(protect&0x101) and protect&0xf0,'Actual named executable committed image export identity')
    digest=data[72:136].decode('ascii');need(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Physical module digest syntax');path=data[136:].decode('utf-16-le').split('\0',1)[0];need(Path(path).is_absolute() and sha_file(path)==digest,'Loaded physical API owner module identity');return(named,owner,path,digest)
def semantic_inventory(reader,records):
    need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed independent native completion');result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==98 and result['malformed_token_denials']==20 and result['direct_host_failure_queries']==2 and result['actual_GetVersionExA_executed'] is True and result['synthetic_API_results'] is False and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,'Exact integrated/host-only native corpus and scope')
    need(set(result)=={'passed','checks','scenarios','malformed_token_denials','direct_host_failure_queries','ordinary_game_launched','original_executed','actual_GetVersionExA_executed','synthetic_API_results','whole_M4_complete'},'Exact scope/result schema; no unsupported invented execution fields')
    need(type(result['checks']) is int and result['checks']>0,'Actual compiled assertion count');expected={'COMPLETE','controls.json'};created=destroyed=queried=output_commits=selector_returns=0
    for number,mode in enumerate(REQUESTS,1):
        case=f'case-{number}';need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Fixed independently authored request order');s=struct.unpack('<36I',reader.read_bytes(case+'/heap-status.bin'));q=struct.unpack('<10I',reader.read_bytes(case+'/query-status.bin'))
        ev=11 if mode in SELECTOR else 10 if mode in QRETURNED else 9 if mode in QUERY else 8 if mode in PROBE_AFTER else 7 if mode in PROBE else 6 if mode in MODE else 4 if mode in RETURNED else 3 if mode in API else 2 if mode==18 else 1
        undef=5 if mode in SELECTOR|{78,155} else 4 if mode in QUERY|{33,36,37,39,43,45,48} else 3 if mode==35 else 2 if mode in PUBLISHED else 1 if mode in PROVIDER or mode==19 else 0
        need(s[:10]==(mode,mode if mode>=145 else int(mode==13),0x20001858+int(mode==11),0x20001860+int(mode==12),COUNTS[mode],2 if mode in QRETURN_BEFORE else int(mode in RETURN_BEFORE),ev,undef,10,0),'Exact directed committed source/API progression and terminal depth')
        need(s[12:23]==(1,0,1,int(mode in API),int(mode in ACTUAL),int(mode in REGISTERED),int(mode in RETURNED),int(mode in PUBLISHED),int(mode in MODE),0,1),'Typed heap lifecycle and successful cleanup');need(s[23]==s[24]==0,'Actual integrated checkpoint caller saved/restored error zero scoped to these rows');need(s[25:32]==(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6),'Exact original source/API identities');need(s[32:]==(int(mode in PROBE),int(mode in PROBE_AFTER),int(mode in QUERY),0x2000184c if mode in PROBE or mode==38 else 0),'Genuine probe and query stage metadata')
        sites=struct.unpack('<8I',reader.read_bytes(case+'/heap-undefined-sites.bin'));count=0 if mode==19 else undef;need(sites==(0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31)[:count]+(0,)*(8-count),'Exact qualified source AF ledger');scheduler=struct.unpack('<8I',reader.read_bytes(case+'/heap-scheduler.bin'));need(scheduler[0]==1 and scheduler[2:6]==(0x20001860,0x7800183c,0x20001860,0) and scheduler[6:]==(0x5bb514,0x20001860),'State-PC-only scheduling carries CPU and frame')
        own=struct.unpack('<8Q',reader.read_bytes(case+'/independent-ownership.bin'));called=int(mode in ACTUAL);need(own[1:]==(called,called,called,called,called,int(mode!=156),0) and bool(own[0])==bool(called),'Independent live membership and released exact private full HANDLE');registry=struct.unpack('<18Q',reader.read_bytes(case+'/heap-registry.bin'));need(registry[0]==1 and registry[1] and registry[2]==1 and registry[3:11]==(0x48450001 if mode in REGISTERED else 0,own[0],called,int(mode in REGISTERED),0,called,called,called),'Private original HANDLE registry closure');need(registry[12]==called and registry[13:17]==(0,0,1,own[0]) and registry[17]==int(mode==40),'Actual sole release input and lookup denial')
        heap_w=struct.unpack('<16Q',reader.read_bytes(case+'/heap-witness.bin'))
        if called:need(heap_w[:6]==(1,0,1,0,4096,0) and heap_w[6]==own[0] and heap_w[7]==(0x48450001 if mode in REGISTERED else 0) and heap_w[8]==heap_w[10]==s[23] and heap_w[11]==(own[0] if mode in REGISTERED else 0) and heap_w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual creator arguments/HANDLE/token/error reads and genuine return frame')
        else:need(not any(heap_w),'No creator witness before actual call')
        identities={name:api_identity(reader.read_bytes(case+'/'+name+'.bin')) for name in ('heap-create-api-before','heap-create-api-after','heap-destroy-api-before','heap-destroy-api-after')};need(all(bool(v)==bool(called) for v in identities.values()) and identities['heap-create-api-before']==identities['heap-create-api-after'] and identities['heap-destroy-api-before']==identities['heap-destroy-api-after'],'Actual unchanged named heap APIs through cleanup')
        access=struct.unpack('<320I',reader.read_bytes(case+'/heap-accesses.bin'));ledger=[access[n:n+5] for n in range(0,len(access),5)];api=struct.unpack('<40I',reader.read_bytes(case+'/heap-api-accesses.bin'));events=struct.unpack('<64I',reader.read_bytes(case+'/heap-events.bin'));need(all(not any(v) for v in ledger[COUNTS[mode]:]) and not any(events[4*ev:]),'Exact zero unused source/event ledger slots')
        api_expected=[(0x780039d0,0x20001848,0x780039d6,4,0)] if mode in RETURN_BEFORE else []
        if mode in QRETURN_BEFORE:api_expected.append((0x78003a2b,0x20000618,0x78003a31,4,0))
        need(tuple(api)==tuple(v for row in api_expected for v in row)+(0,)*(40-5*len(api_expected)),'Two distinct genuine API return reads with exact timing')
        pattern,first,last=struct.unpack('<3I',reader.read_bytes(case+'/lower-input-status.bin'));need(pattern==(number-1 if number<=6 else 0),'Six explicitly declared initial lower-page patterns');pair=[(0,0),(4,8),(12,0x48),(1,0x80000000),(0x200,0x20000000),(0xffffffff,0xffffffff)][pattern];need((first,last)==pair,'Directed initial stack word pair');initial=bytearray(4096);struct.pack_into('<I',initial,0x850,first);struct.pack_into('<I',initial,0x624,last);need(reader.read_bytes(case+'/declared-lower-input.bin')==initial,'Complete initial lower research page, no original guard-growth claim')
        qw=struct.unpack('<20Q',reader.read_bytes(case+'/query-witness.bin'));input_bytes=reader.read_bytes(case+'/query-input.bin');output_bytes=reader.read_bytes(case+'/query-output.bin');need(len(input_bytes)==len(output_bytes)==148,'Private typed OSVERSIONINFOA byte extents');copies=struct.unpack('<320I',reader.read_bytes(case+'/query-output-accesses.bin'));copy_ledger=[copies[n:n+5] for n in range(0,len(copies),5)]
        need(q[0:2]==((0x20000618+int(mode==72),0x200017b8+int(mode==71)) if mode in QUERY else (0,0)) and q[3:]==(COPY_COUNTS[mode],int(mode in QCALLED),int(mode in QPRE),int(mode in QCOMPLETE),int(mode in QRETURNED),int(mode in SELECTOR),0),'Actual query preflight/native/copy/return/source terminal metadata')
        if mode in QUERY:
            need(qw[:3]==(1,1,int(mode in QCALLED)) and qw[4:9]==(148,0x200017b8,0x20000618,0x78003a31,0) and qw[10:18]==(0,COPY_COUNTS[mode],int(mode in QPRE),int(mode in QCOMPLETE),int(mode in QRETURN_BEFORE),int(mode in QRETURNED),int(mode in SELECTOR),0),'Canonical private query facts and exact partial output/return commitments')
            need(qw[3]==q[2]^(1 if mode in {64,147} else 0),'Only explicit hostile BOOL-witness mutation differs from private actual result');need(struct.unpack('<I',input_bytes[:4])[0]==148,'Actual source supplies original structure size148')
            canonical_input=reader.read_bytes(case+'/heap-mode-query-before/query-input.bin');changed=bytearray(canonical_input)
            if mode==66:changed[4]^=1
            need(input_bytes==changed,'Private input witness immutable except explicitly refused hostile fixture')
        else:need(not any(qw) and not any(q) and not any(input_bytes) and not any(output_bytes),'No query witness or scratch outcome before genuine source query CALL')
        if mode in QCALLED:
            canonical_output=reader.read_bytes(case+'/heap-version-query-native-after/query-output.bin');need(len(canonical_output)==148,'Actual native complete output witness');changed=bytearray(canonical_output)
            if mode==65:changed[0]^=1
            need(output_bytes==changed and qw[18:]==struct.unpack('<I',canonical_output[4:8])+struct.unpack('<I',canonical_output[16:20]),'Actual native major/platform derive full witnessed scratch, never fabricated')
            expected_copy=[(0x78003a2b,0x200017b8+4*i,struct.unpack_from('<I',canonical_output,4*i)[0],4,1) for i in range(COPY_COUNTS[mode])]
            if mode==69:expected_copy[0]=(expected_copy[0][0],expected_copy[0][1],expected_copy[0][2]^1,4,1)
            need(copy_ledger[:COPY_COUNTS[mode]]==expected_copy,'Every API-output commit is exact actual host scratch DWORD or explicit refused ledger mutation');native_before=api_identity(reader.read_bytes(case+'/heap-version-query-native-before/../query-api-before.bin')) if False else api_identity(reader.read_bytes(case+'/query-api-before.bin')) if mode!=67 else None
            after_identity=api_identity(reader.read_bytes(case+'/query-api-after.bin')) if mode!=68 else None
            if mode not in {67,68}:need(native_before==after_identity and native_before,'Actual native loaded named query export unchanged')
        else:need(not any(output_bytes) and not any(v for row in copy_ledger for v in row),'No invented native output/copy before actual API call')
        before_id=reader.read_bytes(case+'/query-api-before.bin');after_id=reader.read_bytes(case+'/query-api-after.bin')
        if mode==67:
            need(api_identity(after_id),'Actual measured post-query identity remains valid in refused pre-query identity mutation fixture');changed=bytearray(after_id);struct.pack_into('<Q',changed,0,struct.unpack_from('<Q',after_id)[0]+1);need(before_id==changed,'Exactly declared hostile pre-query export-address mutation retained')
        elif mode==68:
            need(api_identity(before_id),'Actual measured pre-query identity remains valid in refused post-query identity mutation fixture');changed=bytearray(before_id);struct.pack_into('<Q',changed,0,struct.unpack_from('<Q',before_id)[0]+1);need(after_id==changed,'Exactly declared hostile post-query export-address mutation retained')
        else:need(bool(api_identity(before_id))==bool(mode in QPRE) and bool(api_identity(after_id))==bool(mode in QCALLED),'Measured query identities occur exactly at declared preflight/native stages')
        need(not any(v for row in copy_ledger[COPY_COUNTS[mode]:] for v in row),'Unused fixed64 output records remain zero')
        if mode==0:
            need(qw[3]!=0 and qw[18]>=5 and qw[19]==2,'This ordinary integrated artifact covers actual qualifying manifest-dependent NT response; alternate paths retain static formula credit only');before=struct.unpack('<10I',reader.read_bytes(case+'/heap-create-projected/state-cpu.bin'));after=struct.unpack('<10I',reader.read_bytes(case+'/independent-after/state-cpu.bin'));major=qw[18];v=(major-5)&0xffffffff;flags=int(major<5)+(0x40 if not v else 0)+(4 if (v&255).bit_count()%2==0 else 0)+(0x80 if v&0x80000000 else 0)+(0x10 if (major^5^v)&0x10 else 0)+(0x800 if ((major^5)&(major^v))&0x80000000 else 0);need(after[:4]==(1,before[1],before[2],before[3]) and after[4:8]==(0x20001858,before[5],before[6],before[7]) and after[8]&0x8d5==flags and after[9]==0x780039e8,'Source POP/LEAVE/RET and final majorCMP flags restore original carried frame')
            new=[(0x78003a35,0x200017c8,qw[19],4,0),(0x78003a3e,0x200017bc,qw[18],4,0),(0x7800ccc5,0x2000061c,1,4,1),(0x7800ccc7,0x2000061c,1,4,0),(0x78003a7d,0x20000620,before[3],4,0),(0x78003a7e,0x20001850,before[5],4,0),(0x78003a7f,0x20001854,0x780039e8,4,0)];need(ledger[24:31]==new,'Seven exact genuine postquery source DWORD accesses');lower=bytearray(initial);struct.pack_into('<III',lower,0x618,0x78003a31,1,before[3]);need(reader.read_bytes(case+'/independent-after/page-536870912.bin')==lower,'Whole lower-page changes only by literal source stores, including genuine cold PUSH1');upper=reader.read_bytes(case+'/independent-after/page-536875008.bin');need(upper[0x7b8:0x84c]==canonical_output,'Whole148-byte resident output equals actual native bytes')
        phases=set(BASE_PHASES)
        for domain,phase in [(PROVIDER,'heap-create-provider-before'),(API,'heap-create-api-before'),(RETURN_BEFORE,'heap-create-api-return-before'),(RETURNED,'heap-create-api-returned'),(PUBLISHED,'heap-create-published'),(MODE,'heap-create-mode-before'),(PROBE,'heap-mode-probe-before'),(PROBE_AFTER,'heap-mode-probe-after'),(QUERY,'heap-mode-query-before'),(QPRE,'heap-version-query-native-before'),(QCALLED,'heap-version-query-native-after'),(QCOMPLETE,'heap-version-query-output-after'),(QRETURN_BEFORE,'heap-version-query-return-before'),(QRETURNED,'heap-version-query-returned'),(SELECTOR,'heap-version-selector-return-after')]:
            if mode in domain:phases.add(phase)
        expected|={case+'/'+name for name in CASE_FILES}
        for phase in phases:expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
        created+=called;destroyed+=own[5];queried+=int(mode in QCALLED);output_commits+=q[3];selector_returns+=q[8]
    for diagnostic,size in enumerate((147,0),1):
        case=f'direct-query-failure-{diagnostic}';status=struct.unpack('<8I',reader.read_bytes(case+'/status.bin'));need(status[0:3]==(1,size,148) and status[3]==status[6]==0xcada0000+diagnostic and status[4]==0 and status[7]==98+diagnostic,'Actual separate malformed-size host-only query and nonzero saved/restored error');before=reader.read_bytes(case+'/scratch-before.bin');need(len(before)==148 and struct.unpack('<I',before[:4])[0]==size and before[4:]==b'\xa5'*144 and len(reader.read_bytes(case+'/scratch-after.bin'))==148,'Exact independent host-only initial scratch and all actual failure output bytes');need(api_identity(reader.read_bytes(case+'/api-before.bin'))==api_identity(reader.read_bytes(case+'/api-after.bin')),'Actual host-only named query export before/after identity');expected|={case+'/'+name for name in ('status.bin','scratch-before.bin','scratch-after.bin','api-before.bin','api-after.bin','query-host-before.bin','query-host-after.bin')}
    need(reader.names()==tuple(sorted(expected)),'Exact closed case/phase/logical inventory, no declared or actual files omitted');need(created==destroyed,'Every independently observed acquired heap has actual successful release');T.validate_inventory(reader,records);return result,len(expected),created,queried,output_commits,selector_returns


def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-version-review'
    need(out.parent == base and out.name.startswith('check-') and not out.exists(), 'Fresh independent hardware/inventory report')
    out.mkdir()
    native = read(path)
    need(native['passed'] is True and native['native_scenarios'] == 196, 'Successful independent actual native corpus')
    files = dict(native['files'])
    def pin(p, expected=None):
        p = Path(p).absolute()
        actual = sha_file(p)
        need(expected is None or actual == expected, 'Current hardware/inventory physical association')
        key = normalized(str(p))
        need(key not in files or files[key] == actual, 'Conflict-free current observer association')
        files[key] = actual
    for p in (path,Path(__file__),frozen_path,Path(sys.executable)):
        pin(p)
    validator, association = T.load_validator()
    actual, counts, inventory_tests, before, after = 0, {}, [], None, None
    actual_heaps=actual_queries=actual_output_commits=actual_selector_returns=0
    for level in ('O0','O2'):
        info = native['levels'][level]
        verify_stage(info['native_stage'], info['native_stage_sha256'])
        verify_stage(info['pack_stage'], info['pack_stage_sha256'])
        pin(info['inventory_path'], info['inventory_sha256'])
        published_records = read(info['inventory_path'])['files']
        need(all(set(row) == {'bytes','sha256'} and type(row['bytes']) is int and row['bytes'] >= 0 for row in published_records.values()), 'Exact published logical inventory schema')
        records = {name:{'size_bytes':row['bytes'],'sha256':row['sha256']} for name,row in published_records.items()}
        with CaptureBundle(info['bundle'], info['bundle_sha256']) as bundle:
            result, count, heaps, queries, output_commits, selector_returns = semantic_inventory(bundle, records)
            need(count == info['logical_files'] and result == info['result'], 'Exact native-to-archive receipt association')
            reader = T.LogicalReader(records, bundle=bundle)
            for number in range(1,99):
                for actor in ('writer','entry'):
                    validator(reader.path(f'case-{number}/{actor}-host-before.bin'), reader.path(f'case-{number}/{actor}-host-after.bin'), number)
                    actual += 1
            for diagnostic in (1,2):
                validator(reader.path(f"direct-query-failure-{diagnostic}/query-host-before.bin"),reader.path(f"direct-query-failure-{diagnostic}/query-host-after.bin"),98+diagnostic)
                actual+=1
            actual_heaps+=heaps;actual_queries+=queries;actual_output_commits+=output_commits;actual_selector_returns+=selector_returns
            counts[level] = count
            if level == 'O0':
                before = bundle.read_bytes('case-1/entry-host-before.bin')
                after = bundle.read_bytes('case-1/entry-host-after.bin')
                class Overlay:
                    def __init__(self,changes=None,names=None):self.changes=changes or {};self.inventory=names
                    def read_bytes(self,name):return self.changes[name] if name in self.changes else bundle.read_bytes(name)
                    def names(self):return self.inventory if self.inventory is not None else bundle.names()
                def rejection(label, overlay):
                    denied, reason = False, ''
                    try:semantic_inventory(overlay, records)
                    except (ValueError,KeyError) as error:denied, reason = True, str(error)
                    need(denied, 'Independent inventory corruption refuses')
                    inventory_tests.append(dict(label=label,denied=True,reason=reason))
                rejection('missing_COMPLETE',Overlay({'COMPLETE':b'PARTIAL!'}))
                rejection('missing_case_record',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/heap-events.bin')))
                rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-99/heap-status.bin',)))))
                rejection('missing_required_HeapCreate_phase',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/heap-create-api-before/state.bin')))
                rejection('invented_HeapCreate_phase_on_early_fault',Overlay(names=tuple(sorted(bundle.names()+('case-19/heap-create-api-before/state.bin',)))))
                rejection('wrong_independent_request',Overlay({'case-1/mainargs-mode.bin':(121).to_bytes(4,'little')}))
                for label, offset in (('active_boundary_depth',36),('active_heap_after_cleanup',52)):
                    status=bytearray(bundle.read_bytes('case-1/heap-status.bin'));status[offset:offset+4]=(1).to_bytes(4,'little')
                    rejection(label,Overlay({'case-1/heap-status.bin':bytes(status)}))
                for filename,offset,label in (('independent-ownership.bin',24,'actual_create_count'),('independent-ownership.bin',40,'actual_release_success_count'),('independent-ownership.bin',56,'live_handle_after_cleanup'),('heap-registry.bin',32,'full_native_HANDLE_association'),('heap-registry.bin',56,'registry_live_after_cleanup'),('heap-registry.bin',80,'actual_destroy_result'),('heap-witness.bin',48,'actual_full_HANDLE_witness'),('heap-witness.bin',56,'guest_token_witness'),('heap-witness.bin',64,'actual_incoming_error_read'),('heap-witness.bin',80,'actual_restored_error_read'),('heap-api-accesses.bin',4,'real_source_return_frame'),('heap-create-api-before.bin',0,'named_creator_API_identity'),('heap-destroy-api-after.bin',0,'named_release_API_identity')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('lower-input-status.bin',0,'declared_initial_pattern'),('declared-lower-input.bin',0x624,'declared_initial_tail_word'),('heap-accesses.bin',13*20+8,'first_probe_read_value'),('heap-accesses.bin',23*20+8,'query_return_store_value'),('heap-undefined-sites.bin',12,'qualified_final_TEST_AF'),('heap-status.bin',128,'probe_reached'),('heap-status.bin',132,'genuine_probe_returned'),('heap-status.bin',136,'query_frontier_reached'),('heap-status.bin',140,'genuine_probe_frame'),('independent-after/page-536870912.bin',0x10,'complete_lower_page_untouched_byte'),('independent-after/page-536870912.bin',0x618,'literal_query_return_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('query-witness.bin',24,'private_actual_BOOL'),('query-witness.bin',88,'actual_output_commit_count'),('query-witness.bin',144,'actual_native_major'),('query-status.bin',28,'query_returned_flag'),('query-status.bin',32,'genuine_selector_RET_flag'),('query-output-accesses.bin',8,'native_output_commit_value'),('query-output.bin',4,'full_native_major_bytes'),('query-input.bin',0,'original_source_query_size'),('query-api-before.bin',0,'actual_named_query_API'),('heap-api-accesses.bin',24,'second_genuine_API_return_frame'),('heap-undefined-sites.bin',16,'qualified_query_TEST_AF'),('heap-accesses.bin',30*20+8,'genuine_selector_RET_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('status.bin',16,'actual_host_only_failed_BOOL'),('status.bin',12,'nonzero_host_only_incoming_error'),('scratch-before.bin',0,'host_only_invalid_size'),('api-after.bin',0,'actual_host_only_API_identity')):
                    data=bytearray(bundle.read_bytes('direct-query-failure-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'direct-query-failure-1/'+filename:bytes(data)}))
                for field,value in (('actual_GetVersionExA_executed',False),('synthetic_API_results',True),('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',17)):
                    changed=dict(result);changed[field]=value;rejection('result_'+field,Overlay({'controls.json':json.dumps(changed).encode()}))
    preservation=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+list(range(512,540))
    fixtures=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+[512,513,516,517,520,521]+list(range(524,538))
    tests=[]
    for direction,offsets in (('after',preservation),('coherent_wrong_before_fixture',fixtures)):
        for offset in offsets:
            b=bytearray(before);a=bytearray(after);a[offset]^=1
            if direction!='after':b[offset]^=1
            pb,pa=T.overlay_paths(b,a);denied=False
            try:validator(pb,pa,1)
            except ValueError:denied=True
            need(denied,'Unchanged meaningful hardware semantic corruption refuses')
            tests.append(dict(direction=direction,offset=offset,denied=True))
    for extent in (543,545):
        pb,pa=T.overlay_paths(before[:extent] if extent<544 else before+b'\0',after);denied=False
        try:validator(pb,pa,1)
        except ValueError:denied=True
        need(denied,'Wrong hardware extent rejected');tests.append(dict(direction='wrong_extent',bytes=extent,denied=True))
    need(actual==396 and len(tests)==548 and len(inventory_tests)==56,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':196,'native_checks':native['native_checks'],
            'actual_hardware_pairs':396,'hardware_semantic_denials':548,'inventory_request_denials':56,'actual_HeapCreate_calls':actual_heaps,'actual_successful_HeapDestroy_calls':actual_heaps,'actual_integrated_GetVersionExA_calls':actual_queries,'counterfactual_direct_host_failure_queries':4,'actual_output_DWORD_commits':actual_output_commits,'actual_selector_RETs':actual_selector_returns,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'full_causal_source_model_oracle':False,'native_executed':False,'original_executed':False,'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'declared_initial_lower_stack_patterns':6,'GetVersionExA_executed':False,'validates_actual_query_native_witness':True,'synthetic_API_results':False,'alternate_query_branch_live_coverage':False,'selector_result_produced_by_genuine_source':True,'guest_heap_mode_global_published':False,'probe_return_proved':True,'original_stack_guard_growth_proved':False,'heap_initialized':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':396,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
