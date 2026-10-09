"""Closed locale fixture inventory and unchanged rich hardware semantics."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[3]
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
REQUESTS = [0] * 6 + list(range(97, 109)) + list(range(1, 49))
PAGES = (0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000)
PHASE_FILES = set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin'.split()) | {f'page-{p}.bin' for p in PAGES}
CASE_FILES = set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin locale-accesses.bin locale-events.bin locale-status.bin'.split())
BASE_PHASES = set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after locale-before locale-projected locale-after'.split())
SET_PHASE = {0,3,4,19,20,21,22,23,24,25,27,28,29,101,102,103,104,105,106,107,108}
LOCK_PHASE = SET_PHASE - {27,101}
MALLOC_PHASE = {0,3,4,19,20,21,22,23,24,25,106,107,108}
MALLOC_REACHED = {0,4,22,23,24,25,108}
COUNTS = {0:15,1:0,2:1,3:15,4:15,5:0,6:0,7:0,8:0,9:0,10:0,11:1,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:15,20:15,21:15,22:15,23:15,24:15,25:15,26:2,27:8,28:15,29:12,30:0,31:0,32:0,97:0,98:0,99:0,100:1,101:8,102:9,103:11,104:11,105:13,106:15,107:15,108:15}
COUNTS.update({m:0 for m in range(33,49)})


def need(value, why):
    if not value:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def semantic_inventory(reader, records):
    need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Closed independently authored native completion marker')
    result = json.loads(reader.read_bytes('controls.json'), object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios'] == 66 and
         result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,
         'Exact independent fixture result domain')
    need(type(result['checks']) is int and result['checks'] > 0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials'] == 25,
         'Exact actual assertion and malformed-token domain')
    expected = {'COMPLETE','controls.json'}
    for number, mode in enumerate(REQUESTS, 1):
        case = f'case-{number}'
        need(struct.unpack('<I', reader.read_bytes(case+'/mainargs-mode.bin'))[0] == mode, 'Fixed independent case request order')
        status = struct.unpack('<24I', reader.read_bytes(case+'/locale-status.bin'))
        event_count = 4 if mode in MALLOC_REACHED else 3 if mode in LOCK_PHASE else 2 if mode in SET_PHASE or mode == 12 else 1
        need(status[:8] == (mode, mode if mode>=97 else int(mode==7), 0x2000185c+int(mode==5), 0x20001860+int(mode==6), COUNTS[mode], event_count,4,0),
             'Independent actual locale progress and cleanup identity')
        need(status[10:14] == (1,0,int(mode!=32),int(mode in MALLOC_REACHED)) and status[14] == status[15], 'Typed firstfault ownership, lifecycle and actual LastError')
        need(status[16:] == (0x78003dd2,0x78003ddb,0x78001055,0x7800107b,0x780012b3,0x78001080,0x7803708c,269), 'Exact source and target constants')
        if mode in MALLOC_REACHED:
            need(status[8:10] == (0x7800107b,0x780012b3), 'First real malloc dependency retained through terminal faults')
        phases = set(BASE_PHASES)
        if mode in SET_PHASE:
            phases.add('locale-setmbcp-before')
        if mode in LOCK_PHASE:
            phases.add('locale-lock-before')
        if mode in MALLOC_PHASE:
            phases.add('locale-malloc-before')
        expected |= {case+'/'+name for name in CASE_FILES}
        for phase in phases:
            expected |= {case+'/'+phase+'/'+name for name in PHASE_FILES}
    need(reader.names() == tuple(sorted(expected)), 'Exact independently specified complete case/phase/file inventory')
    T.validate_inventory(reader, records)
    return result, len(expected)


def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-locale-default-contract/review'
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
                rejection('missing_case_record',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/locale-events.bin')))
                rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-67/locale-status.bin',)))))
                rejection('missing_required_malloc_phase',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/locale-malloc-before/state.bin')))
                rejection('invented_malloc_phase_on_early_fault',Overlay(names=tuple(sorted(bundle.names()+('case-19/locale-malloc-before/state.bin',)))))
                rejection('wrong_independent_request',Overlay({'case-1/mainargs-mode.bin':(97).to_bytes(4,'little')}))
                for label, offset in (('active_boundary_depth',28),('active_locale_after_cleanup',44)):
                    status=bytearray(bundle.read_bytes('case-1/locale-status.bin'));status[offset:offset+4]=(1).to_bytes(4,'little')
                    rejection(label,Overlay({'case-1/locale-status.bin':bytes(status)}))
                for field,value in (('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',24)):
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
    need(actual==264 and len(tests)==548 and len(inventory_tests)==14,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':132,'native_checks':native['native_checks'],
            'actual_hardware_pairs':264,'hardware_semantic_denials':548,'inventory_request_denials':14,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'native_executed':False,'original_executed':False,'malloc_body_executed':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':264,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
