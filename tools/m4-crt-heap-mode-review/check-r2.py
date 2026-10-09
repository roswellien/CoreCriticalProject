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
REQUESTS=[0]*6+list(range(133,145))+list(range(1,49))
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000,0x78035000,0x78005000,0x20000000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin heap-fragment.bin heap-provider.bin heap-create-witness.bin heap-create-registry.bin heap-mode-selector.bin heap-stack-probe.bin'.split())|{f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin heap-accesses.bin heap-events.bin heap-undefined-sites.bin heap-scheduler.bin heap-status.bin heap-api-accesses.bin heap-witness.bin heap-registry.bin heap-create-api-before.bin heap-create-api-after.bin heap-destroy-api-before.bin heap-destroy-api-after.bin independent-ownership.bin declared-lower-input.bin lower-input-status.bin'.split())
BASE_PHASES=set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after heap-create-before heap-create-projected heap-create-after'.split())
PROVIDER={0,*range(133,145),*range(3,11),24,*range(33,49)}
API=set(PROVIDER)
ACTUAL=API-{3}
REGISTERED=ACTUAL-{4}
RETURN_BEFORE={0,*range(133,145),*range(6,11),24,*range(33,41),*range(42,49)}
RETURNED=RETURN_BEFORE-{6}
PUBLISHED=RETURNED-{7}
MODE=set(PUBLISHED)
PROBE={0,*range(135,145),9,10,33,34,35,36,37,39,40,42,43,45,47,48}
PROBE_AFTER={0,*range(141,145),9,10,33,39,43,45}
QUERY={0,9,10,144}
COUNTS={m:0 for m in REQUESTS}
COUNTS.update({0:24,2:1,17:1,133:10,134:10,135:13,136:17,137:16,138:14,139:15,140:18,141:19,142:19,143:24,144:24})
COUNTS.update({m:8 for m in range(3,8)})
COUNTS.update({8:10,9:24,10:24,24:10,33:23,34:14,35:15,36:18,37:19,38:12,39:24,40:12,41:8,42:12,43:24,44:10,45:19,46:10,47:12,48:18})
def api_identity(data):
    need(len(data)==2184,'Packed actual API identity extent')
    if not any(data):return None
    address,named,owner,owner_named,base,size,allocation,state,kind,protect,allocation_protect=struct.unpack('<7Q4I',data[:72])
    need(address==named==owner_named and owner==allocation and base<=named<base+size and state==0x1000 and kind==0x1000000 and not(protect&0x101) and protect&0xf0,'Actual named executable committed image API identity')
    digest=data[72:136].decode('ascii');need(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Physical module digest syntax')
    path=data[136:].decode('utf-16-le').split('\0',1)[0];need(Path(path).is_absolute() and sha_file(path)==digest,'Actual loaded owner physical module binding');return(named,owner,path,digest)
def semantic_inventory(reader,records):
    need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed native completion')
    result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==66 and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False and result['GetVersionExA_executed'] is False,'Exact compiled fixture domain without query execution')
    need(type(result['checks']) is int and result['checks']>0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials']==19,'Native checks and typed denial count')
    expected={'COMPLETE','controls.json'};created=destroyed=0
    for number,mode in enumerate(REQUESTS,1):
        case=f'case-{number}';need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Fixed independent request order')
        s=struct.unpack('<36I',reader.read_bytes(case+'/heap-status.bin'))
        ev=9 if mode in QUERY else 8 if mode in PROBE_AFTER else 7 if mode in PROBE else 6 if mode in MODE else 4 if mode in RETURNED else 3 if mode in API else 2 if mode==18 else 1
        undef=4 if mode in {0,9,10,33,36,37,39,43,45,48,136,137,140,141,142,143,144} else 3 if mode in {35,139} else 2 if mode in PUBLISHED else 1 if mode in PROVIDER or mode==19 else 0
        need(s[:10]==(mode,mode if mode>=133 else int(mode==13),0x20001858+int(mode==11),0x20001860+int(mode==12),COUNTS[mode],int(mode in RETURN_BEFORE),ev,undef,10,0),'Declared partial source/API progression and terminal depth')
        need(s[12:23]==(1,0,1,int(mode in API),int(mode in ACTUAL),int(mode in REGISTERED),int(mode in RETURNED),int(mode in PUBLISHED),int(mode in MODE),0,1),'Exact lifecycle source flags and cleanup')
        need(s[23]==s[24]==0,'Actual ordinary checkpoint caller saved/restored error zero; no nonzero error claim')
        need(s[25:32]==(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6),'Exact source/API constants')
        need(s[32:]==(int(mode in PROBE),int(mode in PROBE_AFTER),int(mode in QUERY),0x2000184c if mode in PROBE or mode==38 else 0),'Authentic probe/query/RET stage flags and fixed frame')
        sites=struct.unpack('<8I',reader.read_bytes(case+'/heap-undefined-sites.bin'));site_count=0 if mode==19 else undef
        need(sites==(0x780039bf,0x780039d6,0x780058db,0x780058c5)[:site_count]+(0,)*(8-site_count),'Exact qualified artifact AF ledger')
        scheduler=struct.unpack('<8I',reader.read_bytes(case+'/heap-scheduler.bin'));need(scheduler[0]==1 and scheduler[2:6]==(0x20001860,0x7800183c,0x20001860,0) and scheduler[6:]==(0x5bb514,0x20001860),'Explicit State-only scheduler without guest store')
        own=struct.unpack('<8Q',reader.read_bytes(case+'/independent-ownership.bin'));called=int(mode in ACTUAL)
        need(own[1:]==(called,called,called,called,called,int(mode!=144),0) and bool(own[0])==bool(called),'Actual independently observed live/released heap and duplicate cleanup')
        registry=struct.unpack('<18Q',reader.read_bytes(case+'/heap-registry.bin'));need(registry[0]==1 and registry[1] and registry[2]==1 and registry[3:11]==(0x48450001 if mode in REGISTERED else 0,own[0],called,int(mode in REGISTERED),0,called,called,called),'Private full-HANDLE observational registry association')
        need(registry[12]==called and registry[13:17]==(0,0,1,own[0]) and registry[17]==int(mode==40),'Actual sole release path, original full-HANDLE input and lookup denial')
        w=struct.unpack('<16Q',reader.read_bytes(case+'/heap-witness.bin'))
        if called:
            need(w[:6]==(1,0,1,0,4096,0) and w[6]==own[0] and w[7]==(0x48450001 if mode in REGISTERED else 0) and w[8]==w[10]==s[23] and w[11]==(own[0] if mode in REGISTERED else 0) and w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual API arguments/full HANDLE/token/error reads and genuine separate return frame')
        else:need(not any(w),'No API witness invented before actual call')
        ids={name:api_identity(reader.read_bytes(case+'/'+name+'.bin')) for name in ('heap-create-api-before','heap-create-api-after','heap-destroy-api-before','heap-destroy-api-after')};need(all(bool(v)==bool(called) for v in ids.values()),'Actual API identities only when acquired/released');need(ids['heap-create-api-before']==ids['heap-create-api-after'] and ids['heap-destroy-api-before']==ids['heap-destroy-api-after'],'Actual named API owner preserved across real lifetime')
        accesses=struct.unpack('<320I',reader.read_bytes(case+'/heap-accesses.bin'));ledger=[accesses[n:n+5] for n in range(0,len(accesses),5)];api=struct.unpack('<40I',reader.read_bytes(case+'/heap-api-accesses.bin'));events=struct.unpack('<64I',reader.read_bytes(case+'/heap-events.bin'))
        need(all(not any(v) for v in ledger[COUNTS[mode]:]) and all(not v for v in events[4*ev:]),'Zero unused fixed-size source/event ledger slots')
        if mode in RETURN_BEFORE:need(api[:5]==(0x780039d0,0x20001848,0x780039d6,4,0) and not any(api[5:]),'Separate genuine checked API return-word read')
        else:need(not any(api),'No API return read before corresponding source adapter stage')
        initial=reader.read_bytes(case+'/declared-lower-input.bin');need(len(initial)==4096,'Declared lower-page input extent');pattern,first,last=struct.unpack('<3I',reader.read_bytes(case+'/lower-input-status.bin'));need(pattern==(number-1 if number<=6 else 0),'Six fixed independent initial pattern rows')
        pair=[(0,0),(4,8),(12,0x48),(1,0x80000000),(0x200,0x20000000),(0xffffffff,0xffffffff)][pattern];need((first,last)==pair,'Fixed independently chosen input word pair');wanted=bytearray(4096);struct.pack_into('<I',wanted,0x850,first);struct.pack_into('<I',wanted,0x624,last);need(initial==wanted,'No undeclared initial lower bytes')
        if mode==0:
            before=struct.unpack('<10I',reader.read_bytes(case+'/heap-create-projected/state-cpu.bin'));after=struct.unpack('<10I',reader.read_bytes(case+'/independent-after/state-cpu.bin'));word=last&0x20001848;flags=(0 if word else 0x40)|(0 if (word&255).bit_count()%2 else 4)
            need(after[:4]==(0x200017b8,before[1],before[2],before[3]) and after[4:8]==(0x20000618,0x20001850,before[6],before[7]) and after[8]&0x8d5==flags and after[9]==0x34600,'Literal final State CPU and defined TEST flags from separately declared input')
            expected_new=[(0x78003a0c,0x20001850,before[5],4,1),(0x78003a14,0x2000184c,0x78003a19,4,1),(0x780058b5,0x20001848,before[1],4,1),(0x780058db,0x20000850,first,4,0),(0x780058c5,0x20000624,last,4,0),(0x780058c9,0x20001848,before[1],4,0),(0x780058cb,0x2000184c,0x78003a19,4,0),(0x780058ce,0x20000620,0x78003a19,4,1),(0x780058cf,0x20000620,0x78003a19,4,0),(0x78003a1f,0x20000620,before[3],4,1),(0x78003a20,0x2000061c,0x200017b8,4,1),(0x78003a21,0x200017b8,0x94,4,1),(0x78003a2b,0x7802e0a0,0x34600,4,0),(0x78003a2b,0x20000618,0x78003a31,4,1)];need(ledger[10:24]==expected_new,'Exact new authentic source access trace independent affine facts')
            final=bytearray(initial);struct.pack_into('<III',final,0x618,0x78003a31,0x200017b8,before[3]);need(reader.read_bytes(case+'/independent-after/page-536870912.bin')==final,'Complete declared lower-page source writes exactly reproduced')
        phases=set(BASE_PHASES)
        for domain,phase in ((PROVIDER,'heap-create-provider-before'),(API,'heap-create-api-before'),(RETURN_BEFORE,'heap-create-api-return-before'),(RETURNED,'heap-create-api-returned'),(PUBLISHED,'heap-create-published'),(MODE,'heap-create-mode-before'),(PROBE,'heap-mode-probe-before'),(PROBE_AFTER,'heap-mode-probe-after'),(QUERY,'heap-mode-query-before')):
            if mode in domain:phases.add(phase)
        expected|={case+'/'+name for name in CASE_FILES}
        for phase in phases:expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
        created+=called;destroyed+=own[5]
    need(reader.names()==tuple(sorted(expected)),'Exact closed full case/phase/logical-file inventory');need(created==destroyed==42,'Expected real heap ownership count per optimization');T.validate_inventory(reader,records);return result,len(expected)


def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-mode-review'
    need(out.parent == base and out.name.startswith('check-') and not out.exists(), 'Fresh independent hardware/inventory report')
    out.mkdir()
    native = read(path)
    need(native['passed'] is True and native['native_scenarios'] == 132, 'Successful independent actual native corpus')
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
    for level in ('O0','O2'):
        info = native['levels'][level]
        verify_stage(info['native_stage'], info['native_stage_sha256'])
        verify_stage(info['pack_stage'], info['pack_stage_sha256'])
        pin(info['inventory_path'], info['inventory_sha256'])
        published_records = read(info['inventory_path'])['files']
        need(all(set(row) == {'bytes','sha256'} and type(row['bytes']) is int and row['bytes'] >= 0 for row in published_records.values()), 'Exact published logical inventory schema')
        records = {name:{'size_bytes':row['bytes'],'sha256':row['sha256']} for name,row in published_records.items()}
        with CaptureBundle(info['bundle'], info['bundle_sha256']) as bundle:
            result, count = semantic_inventory(bundle, records)
            need(count == info['logical_files'] and result == info['result'], 'Exact native-to-archive receipt association')
            reader = T.LogicalReader(records, bundle=bundle)
            for number in range(1,67):
                for actor in ('writer','entry'):
                    validator(reader.path(f'case-{number}/{actor}-host-before.bin'), reader.path(f'case-{number}/{actor}-host-after.bin'), number)
                    actual += 1
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
                rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-67/heap-status.bin',)))))
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
                for field,value in (('GetVersionExA_executed',True),('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',17)):
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
    need(actual==264 and len(tests)==548 and len(inventory_tests)==39,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':132,'native_checks':native['native_checks'],
            'actual_hardware_pairs':264,'hardware_semantic_denials':548,'inventory_request_denials':39,'actual_HeapCreate_calls':84,'actual_successful_HeapDestroy_calls':84,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'full_causal_source_model_oracle':False,'native_executed':False,'original_executed':False,'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'declared_initial_lower_stack_patterns':6,'GetVersionExA_executed':False,'probe_return_proved':True,'original_stack_guard_growth_proved':False,'heap_initialized':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':264,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
