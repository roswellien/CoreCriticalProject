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
REQUESTS=[0]*6+list(range(121,133))+list(range(1,49))
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000,0x78035000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin heap-fragment.bin heap-provider.bin heap-create-witness.bin heap-create-registry.bin'.split())|{f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin heap-accesses.bin heap-events.bin heap-undefined-sites.bin heap-scheduler.bin heap-status.bin heap-api-accesses.bin heap-witness.bin heap-registry.bin heap-create-api-before.bin heap-create-api-after.bin heap-destroy-api-before.bin heap-destroy-api-after.bin independent-ownership.bin'.split())
BASE_PHASES=set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after heap-create-before heap-create-projected heap-create-after'.split())
PROVIDER={0,*range(121,133),*range(3,11),24,34,35,*range(36,44),45,46,47}
API=PROVIDER-{34,35}
RETURN_BEFORE={0,121,*range(125,133),*range(6,11),39,42,43,45,46,47}
RETURNED=RETURN_BEFORE-{125,6,43}
PUBLISHED={0,121,127,*range(129,133),*range(8,11),39,42,45,46,47}
MODE={0,*range(130,133),*range(8,11),39,42,45}
ACTUAL={0,*range(122,133),*range(4,11),*range(36,44),45,46,47}
REGISTERED=ACTUAL-{122,123,4,36}
API_READ=RETURN_BEFORE-{43}
COUNTS={m:0 for m in REQUESTS}
COUNTS.update({0:10,2:1,17:1,33:2,34:7,35:8})
COUNTS.update({m:8 for m in {3,4,5,6,7,24,36,37,38,40,41,43,122,123,124,125,126,128}})
COUNTS.update({m:9 for m in {46,121,127,129}})
COUNTS.update({m:10 for m in {8,9,10,39,42,45,47,130,131,132}})

def api_identity(data,changed=False):
    need(len(data)==2184,'Exact packed actual API identity extent')
    q=struct.unpack('<7Q4I',data[:72]);address,named,owner,owner_named,base,size,allocation,state,kind,protect,allocation_protect=q
    if not any(data):return None
    need(address==(named^int(changed)) and named==owner_named and owner==allocation and base<=named<base+size and state==0x1000 and kind==0x1000000 and not(protect&0x101) and protect&0xf0,'Actual named executable committed image API identity')
    digest=data[72:136].decode('ascii');need(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Actual physical module hash syntax')
    path=data[136:].decode('utf-16-le').split('\0',1)[0];need(Path(path).is_absolute() and sha_file(path)==digest,'Actual API loaded owner module physical hash')
    return (named,owner,path,digest)

def semantic_inventory(reader,records):
    need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed independent native completion marker')
    result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==66 and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,'Exact independent fixture domain')
    need(type(result['checks']) is int and result['checks']>0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials']==18,'Actual assertion and token denial domain')
    expected={'COMPLETE','controls.json'};created=destroyed=0
    for number,mode in enumerate(REQUESTS,1):
        case=f'case-{number}';need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Fixed independent case order')
        s=struct.unpack('<32I',reader.read_bytes(case+'/heap-status.bin'))
        ev=6 if mode in MODE or mode==121 else 4 if mode in RETURNED else 3 if mode in API else 2 if mode in PROVIDER or mode==18 else 1
        undef=2 if mode in PUBLISHED or mode==128 else 1 if mode in PROVIDER or mode==19 else 0
        need(s[:10]==(mode,mode if mode>=121 else int(mode==13),0x20001858+int(mode==11),0x20001860+int(mode==12),COUNTS[mode],int(mode in API_READ),ev,undef,10,0),'Independent specified source/API progress and closed depth')
        need(s[12:23]==(1,0,1,int(mode in API),int(mode in ACTUAL),int(mode in REGISTERED),int(mode in RETURNED),int(mode in PUBLISHED),int(mode in MODE),int(mode==121),1),'Independent typed result and owned lifecycle')
        need(s[23]==s[24]==0,'Actual checkpoint-observed saved/restored caller LastError; explicit nonzero seam tested separately')
        need(s[25:]==(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6),'Exact original source/API constants')
        sites=struct.unpack('<8I',reader.read_bytes(case+'/heap-undefined-sites.bin'))
        expected_sites=(0x780039bf,0x780039d6)+(0,)*6 if undef==2 else (0x780039bf,)+(0,)*7 if mode in PROVIDER else (0,)*8
        need(sites==expected_sites,'Exact narrowly scoped source-artifact AF ledger')
        scheduler=struct.unpack('<8I',reader.read_bytes(case+'/heap-scheduler.bin'));need(scheduler[0]==1 and scheduler[2:6]==(0x20001860,0x7800183c,0x20001860,0) and scheduler[6:]==(0x5bb514,0x20001860),'StatePC-only bootstrap has no guest store or CPU projection')
        own=struct.unpack('<8Q',reader.read_bytes(case+'/independent-ownership.bin'));called=int(mode in ACTUAL)
        need(own[1:]==(called,called,called,called,called,int(mode!=131),0) and bool(own[0])==bool(called),'Independent actual live/released heap membership, matching release and duplicate no-op checks')
        r=struct.unpack('<18Q',reader.read_bytes(case+'/heap-registry.bin'))
        need(r[:3]==(1,r[1],1) and r[1] and r[3:11]==(0x48450001 if mode in REGISTERED else 0,own[0],called,int(mode in REGISTERED),0,called,called,called),'Private full-HANDLE registry agrees with independent actual ownership counters')
        need(r[12]==called+int(mode==132) and r[13]==int(mode==132) and r[14]==int(mode==123) and r[15]==1 and r[16]==own[0] and r[17]==int(mode==40),'Exact rollback/cleanup skip/success input/lookup refusal')
        w=struct.unpack('<16Q',reader.read_bytes(case+'/heap-witness.bin'))
        if mode in ACTUAL or mode==121:
            need(w[:6]==(1,int(mode==121),called,0,4096,0) and w[6]==(own[0]^(0x100000000 if mode==36 else 0)) and w[7]==((0x48450001^int(mode==124)) if mode in REGISTERED else 0),'Typed actual API argument/full-HANDLE/token witness with declared fixture mutation')
            need(w[8]==w[10]==s[23] and w[11]==(own[0] if mode in REGISTERED else 0) and w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual API error reads and source stdcall return frame witness')
        else:need(not any(w),'No invented API witness before actual admission')
        identities={name:api_identity(reader.read_bytes(case+'/'+name+'.bin'),(mode==38 and name=='heap-create-api-after') or (mode==39 and name=='heap-destroy-api-before')) for name in ('heap-create-api-before','heap-create-api-after','heap-destroy-api-before','heap-destroy-api-after')}
        measured=bool(called or mode==121)
        need(bool(identities['heap-create-api-before'])==measured and bool(identities['heap-create-api-after'])==measured and bool(identities['heap-destroy-api-before'])==measured and bool(identities['heap-destroy-api-after'])==bool(called),'Actual API identities exist only for measured creation/release phases')
        need(identities['heap-create-api-before']==identities['heap-create-api-after'],'Matching actual create API owner identity after normalization of explicit metadata fixture')
        if called:need(identities['heap-destroy-api-before']==identities['heap-destroy-api-after'],'Matching actual release API owner identity after explicit metadata fixture normalization')
        phases=set(BASE_PHASES)
        for mode_set,name in ((PROVIDER,'heap-create-provider-before'),(API,'heap-create-api-before'),(RETURN_BEFORE,'heap-create-api-return-before'),(RETURNED,'heap-create-api-returned'),(PUBLISHED,'heap-create-published'),(MODE,'heap-create-mode-before'),({121},'heap-create-zero-before')):
            if mode in mode_set:phases.add(name)
        expected|={case+'/'+name for name in CASE_FILES}
        for phase in phases:expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
        created+=called;destroyed+=own[5]
    need(reader.names()==tuple(sorted(expected)),'Exact whole native case/phase/logical-file inventory')
    need(created==destroyed==35,'Exact actual native heap create and successful release count per optimization')
    T.validate_inventory(reader,records)
    return result,len(expected)

def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-create-review'
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
                for field,value in (('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',17)):
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
    need(actual==264 and len(tests)==548 and len(inventory_tests)==27,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':132,'native_checks':native['native_checks'],
            'actual_hardware_pairs':264,'hardware_semantic_denials':548,'inventory_request_denials':27,'actual_HeapCreate_calls':70,'actual_successful_HeapDestroy_calls':70,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'full_causal_source_model_oracle':False,'native_executed':False,'original_executed':False,'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'heap_initialized':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':264,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
