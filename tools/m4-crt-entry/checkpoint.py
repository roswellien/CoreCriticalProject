"""Bind full-entry preparation and the independently observed FP limitation."""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
PINS={}


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file,'sha256').hexdigest()


def pin(path, expected=None):
    path=Path(path).resolve(); value=sha(path)
    assert expected is None or value==expected, str(path)
    assert str(path) not in PINS or PINS[str(path)]==value, str(path)
    PINS[str(path)]=value
    return path


def stage(path, report_sha, pins_sha):
    path=ROOT/path
    report=json.loads(pin(path/'report.json',report_sha).read_text())
    assert report['passed']
    for name,value in json.loads(pin(path/'pins.json',pins_sha).read_text())['files'].items():
        pin(name,value)
    return report


def host_records(raw):
    assert len(raw)==6*1648
    result=[]
    for i,cw in enumerate((0x7f,0x37f,0xb7f)):
        for mode in (0,1):
            record=raw[(2*i+mode)*1648:(2*i+mode+1)*1648]
            assert struct.unpack_from('<4I',record)==(cw,mode,mode,0)
            before=record[16:16+544]; after=record[560:560+544]
            word=lambda data,offset:struct.unpack_from('<H',data,offset)[0]
            bsw,asw=word(before,2),word(after,2)
            assert word(before,0)==cw and word(after,0)==cw
            assert bsw&0x20 and not asw&0x20, 'Actual direct caller PE lost'
            assert bsw&0x3800==asw&0x3800 and before[4]==after[4], 'TOP/tag retained'
            assert before[24:28]==after[24:28], 'MXCSR retained'
            assert before[32:42]==after[32:42] and before[48:58]==after[48:58], 'Two live raw80 values retained'
            assert word(before,512)==cw and word(after,512)==cw
            assert word(before,516)==bsw and word(after,516)==asw, 'Separate actual ENV status'
            assert before[524:538]!=after[524:538], 'Actual legacy FP metadata changed'
            result.append(dict(cw=cw,fault=bool(mode),before_SW=bsw,after_SW=asw,lost_caller_PE=True,legacy_metadata_changed=True))
    return result


def main():
    out=ROOT/'reports/m4-crt-entry/root-preparation-checkpoint-r1'
    assert not out.exists()
    prepared=stage('reports/m4-crt-entry/preparation-r2','0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724','51777aa9efd244d30c4303bc916eb88200931d41de36904fd601c9f2107d30d0')
    native=stage('reports/m4-crt-entry/native-preparation-r1','4c1174a4a68e6d6ea00c75bb053a4f16f68767d841132be9d6defeaecd5c7ed3','8b6fac785fbcddbdefff6672709b7dfca7a34ad287a7843eef8c6cc90b018839')
    assert len(prepared['entries'])==11 and prepared['ordinary_entry_instructions']==118 and prepared['unique_instructions']==148
    assert native['State_bytes']==3504 and native['original_direct_calls_replaced']==8 and native['root_entry_checks']==11 and native['instruction_arithmetic_rewrites']==0
    assert not native['native_executed'] and not native['full_startup']
    static=stage('reports/m4-crt-fdiv/independent-static-scope-r1','c2be15964692046e118a8be890ac0bee140988aa356e401024d5141718aa138c','465e5a40bee7a1aae08c5d04477e00501f984a01387dc43c16e0d3ca9fa431dd')
    continuation=stage('reports/m4-crt-fdiv/independent-static-continuation-r2','bcea15a582799dda4eea11fa04c01db9415c4e0e6db3b9cb87a39f46495fdc2b','cd012ccd9b1132a5c0fd63ef00d99895bd560e40a21360775b8b1149b8112fc9')
    assert static['unique_writer_dependency_instructions']==204 and not static['native_execution_credit']
    assert continuation['residual_unportable_halfword_intervals']==[[-34,-32],[-42,-40]] and not continuation['original_or_native_execution']
    direct=stage('reports/m4-fp-numeric-max-integration/independent-direct-host-r1','49a5d97801d3f6827a9d46e87b1f25e107961f9208ac905a3cf42417d649abaa','5aee2a2496ff83978dc2b023d92bbef7786a40ae4eabab7cdff898e46a6ac896')
    assert all(r['result']['after_capture_before_restore'] and r['result']['records']==6 for r in direct['results'])
    records=[]
    for level in ('O0','O2'):
        path=pin(ROOT/f'reports/m4-fp-numeric-max-integration/independent-direct-host-r1/{level}.bin')
        observed=host_records(path.read_bytes())
        assert len(observed)==6
        mutated=bytearray(path.read_bytes()); struct.pack_into('<H',mutated,560+2,struct.unpack_from('<H',mutated,16+2)[0])
        rejected=False
        try:
            host_records(mutated)
        except AssertionError:
            rejected=True
        assert rejected, 'Fabricated host-status restoration rejected by limitation observer'
        records.extend(dict(level=level,**row) for row in observed)
    document=pin(ROOT/'docs/m4-crt-entry-preparation.md','44e4855da37d9e7f49e80aae684eea5ce8c02a19f6d31c56e20111e00f4082b2')
    pin(ROOT/'tools/m4-crt-entry/README.md'); pin(Path(__file__))
    out.mkdir(); (out/'checkpoint-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'checkpoint-source.py')
    result=dict(passed=True,scope='Root exact preparation/source association and independent raw host-clobber confirmation; no startup admission',physical_bindings=len(PINS),CRT_entry=dict(roots=11,ordinary_PCs=118,union_PCs=148,native_objects=['O0','O2'],State_bytes=3504,native_executed=False),FDIV=dict(independent_static_PCs=204,portable_residual_halfword_intervals=[[-34,-32],[-42,-40]],initialized_original_result_accepted=False),numeric_max=dict(direct_actual_host_observations=records,raw_corruption_controls=2,numerical_host_boundary_passed=False,requires_production_boundary_repair=True,previous_harness_cleanup_not_boundary_proof=True),document=str(document),selected_joint_initializer_roots=26,remaining_outside_joint_gate=118,full_CRT=False,full_startup=False,frontend=False,whole_M4_complete=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,bindings=len(PINS),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),host_repair_required=True,whole_M4_complete=False)))


if __name__=='__main__':
    main()
