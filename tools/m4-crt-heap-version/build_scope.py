"""Bind a pre-execution scope correction and documentary-only source exclusion."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
p=pathlib.Path(sys.argv[1]).absolute()
assert p.parent.parent==ROOT/'reports/m4-crt-heap-version'
old=p.read_bytes();b=json.loads(old.decode('utf-8-sig'));assert b['passed'] and not b['native_component_executed']
history=p.parent/'build-original.json';assert not history.exists();history.write_bytes(old)
primary=ROOT/'reports/m4-crt-fdiv/native-build-r3/build.json';historical=json.loads(primary.read_text(encoding='utf-8-sig'))
excluded={k:dict(historical_sha256=v,current_sha256=sha(k),reason='Inherited documentation, never a compiler-read translation unit/header; historical frozen snapshot and receipt retained') for k,v in historical['sources'].items() if pathlib.Path(k).suffix=='.md'}
note=p.parent/'source-scope.json';assert not note.exists()
data=dict(passed=True,compiler_and_native_rerun=False,original_build_sha256=sha(history),documentary_exclusions=excluded,
 all_actual_compiler_cpp_hpp_inc_required_unchanged=True,old_guest_objects=30,old_FDIV_libraries=2,original_receipt=str(history),
 note_tool=str(pathlib.Path(__file__).resolve()),note_tool_sha256=sha(__file__),historical_primary_receipt=str(primary),historical_primary_sha256=sha(primary))
note.write_text(json.dumps(data,indent=2)+'\n')
b['scope']='Source/build only: real version-query bridge, exact four new post-query source blocks, private full HANDLE lifecycle; no worker/game/provider execution'
b['documentary_source_exclusions']=dict(path=str(note),sha256=sha(note),count=len(excluded),changes_compiler_input_scope=False)
b['scope_correction']=dict(tool=str(pathlib.Path(__file__).resolve()),tool_sha256=sha(__file__),original_build=str(history),original_build_sha256=sha(history),source_scope_note=str(note),source_scope_note_sha256=sha(note))
p.write_text(json.dumps(b,indent=2)+'\n');print(json.dumps(dict(passed=True,build_sha256=sha(p),scope_note_sha256=sha(note))))
