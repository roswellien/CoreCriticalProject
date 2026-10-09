"""Root current-disk closure for prepared entry and independently checked raw prerequisites.

No author oracle imports and no original or native code execution. Compiled
independent API/failure review and original FDIV comparison remain separate.
"""
import hashlib,importlib.util,json,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
OUT=ROOT/'reports/m4-startup/status-after-entry-prerequisites-r2'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();value=sha(p)
    assert want is None or value==want,str(p)
    assert str(p) not in PINS or PINS[str(p)]==value,str(p)
    PINS[str(p)]=value;return p
def stage(path,rh,ph):
    path=ROOT/path;r=json.loads(pin(path/'report.json',rh).read_text());assert r['passed']
    manifest=json.loads(pin(path/'pins.json',ph).read_text())
    if 'files' in manifest:
        for p,h in manifest['files'].items():pin(p,h)
    else:
        for row in manifest['bindings']:pin(row['path'],row['sha256'])
    return r
def proofs(text):
    rows=[line.split('|')[1:4] for line in text.splitlines() if line.startswith('| M4-')]
    assert len(rows)==12
    return [(a.strip(),b.strip()) for a,b,_ in rows]
def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    (OUT/'checkpoint-source.py').write_bytes(Path(__file__).read_bytes());pin(OUT/'checkpoint-source.py')
    try:
        entry=stage('reports/m4-crt-entry/root-preparation-checkpoint-r1','f764d2020f1875e4b54461f9c28c165480bf9c3a4b61761673ee2723044b46af','14689e5a541afcc17d43850f93fec91a523ff2f962ab4e6125332adb20612fc7')
        assert entry['CRT_entry']['ordinary_PCs']==118 and not entry['full_CRT']
        author=stage('reports/m4-fp-numeric-max-host-boundary/author-review-r1','efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a','4abbd1d60ef7bba49ac434279f79090924700da169450f77119b8bba3897011e')
        for history in author['historical_source_resolutions']:
            pin(history['resolved_path'],history['expected_sha256']);pin(history['manifest'])
        for row in author['literal_sources']:
            pin(row['original_path'],row['sha256']);pin(row['preserved_path'],row['sha256'])
        for row in author['unchanged_guest_object_identity']:
            pin(row['new'],row['sha256']);pin(row['frozen_r5'],row['sha256'])
        persistent=stage('reports/m4-fp-numeric-max-host-boundary/independent-persistent-r1','b60340f1f948c22eddc2ef6ea6f35dec5954093ef7fe8546365a118d39696d4d','df4037c3ed4a4fa515715b84179f48b7452d73e422010dff78686e3577b09830')
        replay=stage('reports/m4-fp-numeric-max-host-boundary/independent-replay-r1','5998adc521615d520c4639ed0a5dd02ae701b209babbe3181e10df78c948d113','fd3b09e5b8f1aff533d0b0d3271a1d1dc12bf9e8d1d567a6d1aa2b0c27af5460')
        assert persistent['native_records']==864 and replay['native_records']==14688
        derivation=pin(ROOT/'reports/m4-fp-numeric-max-host-boundary/root-observer-derivation-r1/report.json','98670b49d1096880ea2a5aa9c06fd96f8ff762ff58c7bdcc9a081ade4b9fbfc0')
        for p,h in json.loads(derivation.read_text())['files'].items():pin(p,h)
        header=pin(ROOT/'reports/m4-fp-numeric-max-host-boundary/derivation-r4/session.hpp','e352aa2298289fff02d041e10159d726bbbf5740c28a0f4d286ea2d6db90b8e3')
        ancestor=pin(header.with_suffix('.hpp.ancestor'),'a3084c8d62164275c606630fdb152d80d595e9585e72eb728f9b3727c976469b')
        text=header.read_text();a=text.index('// This scope owns numerical host FP state;');b=text.index('class Session;',a)
        stripped=text[:a]+text[b:];a=stripped.index(' // The explicit outer numerical boundary');b=stripped.index(' [[noreturn]]void deny',a)
        stripped=stripped[:a]+stripped[b:]
        assert stripped==ancestor.read_text(),'Only host guard and explicit invoke are production source additions'
        guard=text[text.index('struct NumericHostBoundary'):text.index('class Session;')]
        assert all(token in guard for token in ('fxsave64','fnstenv','fninit','fldcw','ldmxcsr','fxrstor64','fldenv'))
        invoke=text[text.index(' bool invoke('):text.index(' [[noreturn]]void deny')]
        assert 'noexcept' in invoke and 'catch(...){ok=false;}' in invoke and 'return ok;' in invoke
        # A second root-owned observer checks both the declared host input and
        # after-return preservation, including the bytes formerly hidden by cleanup.
        path=pin(ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/persistent_model.py')
        spec=importlib.util.spec_from_file_location('root_owned_direct_host_raw',path);model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        controls=[];positive=[]
        spans=list(range(5))+list(range(24,28))+[32+16*i+j for i in range(8) for j in range(10)]
        build=ROOT/'reports/m4-fp-numeric-max-host-boundary/native-build-r3'
        for level in ('O0','O2'):
            raw=pin(build/f'unit-{level}/persistent.bin')
            with raw.open('rb') as f:f.seek(24);row=f.read(46680)
            cw=struct.unpack_from('<I',row,12)[0];model.host_boundary(row,cw)
            for offset in [45068+i for i in spans]+[45580+i for i in spans]+list(range(46092,46148)):
                bad=bytearray(row);bad[offset]^=1
                try:model.host_boundary(bad,cw)
                except ValueError:controls.append(dict(level=level,offset=offset,rejected=True))
                else:raise AssertionError('Numerical host corruption accepted')
            for offset in (45580+160,45580+166,45580+42,45580+480):
                observed=bytearray(row);observed[offset]^=1;model.host_boundary(observed,cw)
                positive.append(dict(level=level,offset=offset,numerical_scope_only=True,volatile_SIMD_or_padding_observation=True))
        objdump=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        objects=[]
        for item in author['fresh_COFF_objects']:
            path=Path(item['path'])
            if path.name.startswith('native-') or path.name=='native.cpp.obj':
                pin(path,item['sha256']);out=OUT/f'object-{len(objects):02}.txt'
                command=[str(objdump),'--disassemble','--demangle','--unwind-info',str(path)]
                result=subprocess.run(command,capture_output=True);out.write_bytes(result.stdout);(OUT/(out.name+'.stderr')).write_bytes(result.stderr)
                assert result.returncode==0
                decoded=result.stdout.decode('utf-8');assert 'file format coff-x86-64' in decoded
                if path.name=='native.cpp.obj':assert 'fxsave64' in decoded and 'fxrstor64' in decoded and 'fldenv' in decoded
                objects.append(dict(path=str(path),sha256=item['sha256'],command=command,output=str(pin(out)),review='Fresh x64 object source association, not fresh execution'))
        assert len(objects)==4
        fdiv=stage('reports/m4-crt-fdiv/independent-native-model-r2','3a88302fcea65b0f68f981bc508c3146740185641cfd6a9ed293c4be0bb41792','cb10c6fa7320dbfa16ee774a7526d8b8169a9827c0bcd860ba4833dad4346463')
        fdivauthor=stage('reports/m4-crt-fdiv/author-review-r1','c3398673510bc8ff28079173d486d8dfe73b1c481541927e37fccfbb94cc99e1','2d3272ed71e22449c4564cbfd728712a3cf9b00c69a2629c73f1369807123d42')
        assert fdiv['native_records']==48 and fdiv['pages']==9 and not fdiv['original_executed']
        for name in ('review-source.py','failure.txt'):pin(ROOT/'reports/m4-crt-fdiv/independent-native-model-r1'/name)
        before=ROOT/'reports/m4-startup/status-before-entry-preparation-r1'
        saved=json.loads(pin(before/'manifest.json').read_text())['files'];documents=[]
        for name,h in saved.items():
            old=pin(before/name,h);now=pin(ROOT/'docs'/name);copy=OUT/name;copy.write_bytes(now.read_bytes());pin(copy)
            documents.append(dict(name=name,before_sha256=h,current_sha256=sha(now),preserved_before=str(old),preserved_after=str(copy)))
        assert proofs((before/'m4-startup-plan.md').read_text())==proofs((ROOT/'docs/m4-startup-plan.md').read_text()),'All twelve required proof definitions unchanged'
        for name in ('m4-crt-entry-preparation.md','m4-crt-fdiv-native.md','m4-fp-numeric-max-integration-limits.md'):pin(ROOT/'docs'/name)
        for path in (ROOT/'reports/m4-startup/status-after-entry-prerequisites-r1').iterdir():
            if path.is_file():pin(path)
        pin(Path(__file__));pin(sys.executable)
        report=dict(passed=True,scope='Independent raw/model/source/current-disk prerequisite closure and unchanged M4 criteria; compiled API review and original FDIV comparison pending',numeric=dict(native_phases=15552,carry_boundaries=432,events=342144,routes=46656,root_raw_corruption_rejects=328,additional_host_field_controls=controls,numerical_scope_positive_controls=positive,exact_production_additions_only=True,guest_objects_byte_identical_to_r5=True,compiled_API_closure=False,original_oracle_preserved=True,raw_Runtime_call_direct_outside_host_preservation_scope=True),FDIV=dict(native_records=48,whole_State_bytes=3504,pages=9,events=4656,routes=144,original_reference_accepted=False,independent_compiled_API_review_pending=True),CRT=dict(ordinary_PCs=118,union_PCs=148,roots=11,compiled_objects=True,entry_executed=False),fresh_COFF_source_associations=objects,status_documents=documents,all_twelve_required_proofs_unchanged=True,physical_bindings=len(PINS),identity_scope='Current files and post-build source/header associations; no complete execution-time dependency attestation',selected_joint_initializer_roots=26,remaining_outside_joint_gate=118,full_CRT=False,full_startup=False,frontend=False,whole_M4_complete=False)
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,physical_bindings=len(PINS),host_corruption_rejects=len(controls),host_scope_positive_controls=len(positive),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'),whole_M4_complete=False)))
    except Exception:
        (OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
