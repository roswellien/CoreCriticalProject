"""Root current-disk closure of connected prerequisites; full M4 remains open."""
import hashlib,json,struct,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def stage(path,rh,ph):
    base=ROOT/path;r=json.loads(pin(base/'report.json',rh).read_text());assert r['passed']
    m=json.loads(pin(base/'pins.json',ph).read_text())
    for p,h in m['files'].items():pin(p,h)
    return r
def proofs(text):
    rows=[line.split('|')[1:4] for line in text.splitlines() if line.startswith('| M4-')];assert len(rows)==12
    return [(a.strip(),b.strip()) for a,b,_ in rows]
def main(out):
    assert out.parent==ROOT/'reports/m4-startup' and not out.exists();out.mkdir();(out/'checkpoint-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        numeric=stage('reports/m4-fp-numeric-max-carry/root-component-acceptance-r2','fe713df4600d61acb3ac1eb6ea80963c1dc225d5e73fa3032795dc1905ca7706','1bc0128a56213ba02858c90ee8588371f41445ac32ec559bc48f13afcc5ec953')
        assert numeric['component_accepted'] and numeric['native_phases']==57024 and numeric['selected_joint_initializer_roots']==26
        prefix=stage('reports/m4-crt-entry/prefix-observation-r2','65c7aeb701d7d51f0b21f547bf12bf8482897812beda6b127fcee6959c5a3723','58c73c7f0cab87d98df4fda7deabcbe9c2f97c77adbae7ee7ad5886321911506')
        assert prefix['raw_game_IAT_508']==0x1ded32 and len(prefix['rows'])==2 and len(prefix['own_corruption_rejects'])==56
        fdiv=stage('reports/m4-crt-fdiv/independent-native-closure-r2','463403fd5751828c8b575a30e60743f28dbd79a34fafed221387e145615d65b1','b3347c5dee7c1b25ba6dbb7061429d6dff18de930e1f48c63f1b1b72df654972')
        assert fdiv['acceptance'] and fdiv['native_records']==48 and fdiv['actual_events']==4656
        original=stage('reports/m4-crt-fdiv-reference/run-normal-r1','4d5b66e3b48a808b722b0b38e921d11a8e716b1fe06f79516364283c5f0261e6','ace672f9f4689ea53980e4e9e8ecbb3b39fed3d17d534d7d36d9675e7e51fed5')
        observation=stage('reports/m4-crt-fdiv-reference/observations-r1','229ddb12152f31820c4ba2d42d141b58156a3217b1554c972c18038354fec8a0','bc6171e251855eebe3f483c98a93d0249637033a347554f000966bf69bb1294c')
        assert original['original_executed'] and original['records']==48 and observation['direct_rows']==observation['debug_rows']==24
        assert observation['direct_retained_legacy_metadata_rows']==24 and observation['debug_zeroed_legacy_metadata_rows']==24
        raw=pin(original['raw']['path'],original['raw']['sha256']).read_bytes();assert raw[:8]==b'MW4FDOR1' and struct.unpack_from('<6I',raw,8)==(1,48,91348,716,80,1048576)
        off=32;direct=bytearray();debug=bytearray();loaded=set();actual_threads=set()
        for i in range(48):
            n=struct.unpack_from('<I',raw,off)[0];r=raw[off+4:off+4+n];tags=struct.unpack_from('<27I',r)
            assert tags[0]==i and tags[2]==i//24 and tags[4]==0 and tags[24:]==(1,1,1)
            assert tags[10]==tags[12]==tags[7] and tags[11]==tags[13]==tags[7]+tags[8] and tags[8]==65536
            assert tags[18]==tags[19]==16 and n==91348+2*16*40+2*65536
            assert tags[16]==0x34000000 and tags[17]==716
            actual_threads.add(tags[14]);loaded.add(tags[16]);(direct if tags[2]==0 else debug).extend(raw[off:off+4+n]);off+=4+n
        assert raw[off:]==b'COMPLETE' and len(actual_threads)==48
        base=ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1'
        assert pin(base/'direct-original-rows.bin').read_bytes()==direct and pin(base/'debug-original-rows.bin').read_bytes()==debug,'Lossless separate original observations'
        before=ROOT/'reports/m4-startup/status-before-three-service-prefix-r1';m=json.loads(pin(before/'manifest.json').read_text());documents=[]
        for name,h in m['files'].items():
            prior=pin(before/name,h);now=pin(ROOT/'docs'/name);copy=out/name;copy.write_bytes(now.read_bytes());pin(copy)
            documents.append(dict(name=name,prior_sha256=h,current_sha256=sha(now),preserved_before=str(prior),preserved_after=str(copy)))
        assert proofs((before/'m4-startup-plan.md').read_text())==proofs((ROOT/'docs/m4-startup-plan.md').read_text()),'All twelve required proof definitions unchanged'
        for name in ('m4-crt-entry-three-service-prefix.md','m4-fp-numeric-max-canonical-acceptance.md','m4-crt-fdiv-replay-contract.md'):pin(ROOT/'docs'/name)
        pin(__file__);pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,scope='Root numeric component/native FDIV closure and observed three-service entry/original-reference prerequisite checkpoint; no full CRT/menu acceptance',numeric=dict(component_accepted=True,native_phases=57024,events=1254528,routes=171072,independent_compiled_checks=136208,actual_joint_carry_accepted=False),CRT_entry=dict(native_game_PCs=26,game_events=52,completed_imports_per_level=3,guest_FS_frame_installed=True,guest_SEH_dispatch=False,initialized_FDIV_data_unconnected=True,raw_IAT_508=0x1ded32,full_static_union_not_execution_credit=148,independent_prefix_compiled_composition_review=False),FDIV=dict(native_component_accepted=True,native_records=48,original_records=48,direct_original_records=24,instrumented_original_records_separate=24,original_loaded_worker_bases=sorted(loaded),original_thread_count=48,lossless_partitions_rechecked=True,actual_original_native_replay_compared=False,original_legacy_metadata_vs_debug_effect_retained=True),status_documents=documents,all_twelve_required_proofs_unchanged=True,selected_joint_initializer_roots=26,remaining_outside_joint_gate=118,physical_bindings=len(PINS),identity_scope='Current disk and literal historical associations; no complete execution-time process/dependency attestation',full_CRT=False,full_startup=False,frontend=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,physical_bindings=len(PINS),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),whole_M4_complete=False)))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
