"""Bind strict validator to current build5 exact observed hook transitions."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];base=Path(__file__).with_name('validate_realloc_v2.py');text=base.read_text();changes=[]
tp=R/'reports/m4-138-validation-review/mfc-transition-r4/report.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(tp)=='e14fbc230d19b05f3e5b711beb10bfd42e876d48b879ee13d98113a3ba3ac386';receipt=json.loads(tp.read_bytes());assert receipt['passed']and receipt['reader_closed']and receipt['patches']==13 and receipt['whole_page_relations']==1524
patch=tp.with_name('patch-identities.json');ph=sha(patch);assert receipt['files'][str(patch.resolve())]==ph
def one(old,new,count=1):
 global text
 assert text.count(old)==count,(old,text.count(old));start=0
 for _ in range(count):
  pos=text.index(old,start);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):];start=pos+len(new)
one('mfc-transition-r3','mfc-transition-r4',2);one('56cc2983c3448cf872e9247cb315cede98a83fa9a63c831264d9008b7ad9e834',sha(tp));one('1f8768938aa8f2ebb938e6a782a93734bb569cea8634d634fe23d335d7b9b2ed',ph)
old=next(line for line in text.splitlines()if 'for path in ('in line and 'transition_receipt' in line)
paths=[R/'reports/m4-startup138-original/preparation-r8/reference.cpp',R/'reports/m4-startup138-original/preparation-r8/fs-hook-bindings.json',R/'reports/m4-startup138-original/build-r5/original-worker.exe',R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/compiled-observers.json',R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json',R/'reports/m4-startup138-original/build-r5/build-x86/mw34_joint_startup124_original.dir/Release/fs_observer_x86.obj',R/'reports/m4-startup138-original/build-r5/build-x86/mw34_joint_startup124_original.dir/Release/nullfree_observer_x86.obj',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py']
assert all(receipt['files'][str(p.resolve())]==sha(p)for p in paths);new='   for path in '+repr(tuple(str(p.resolve())for p in paths))+":pin(path,transition_receipt['files'][path])";one(old,new)
reverse=text
for d in reversed(changes):
 pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
assert reverse==base.read_text();ast.parse(text);target=base.with_name('validate_realloc_v3.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-startup138-original/realloc-validator-preparation-r3';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,changes=changes,exact_inverse_restores_parent=True,current_transition_report=str(tp),current_transition_sha256=sha(tp),current_patch_sha256=ph,thirteen_physical_spans_current=True,current_1524_whole_page_transition_proof=True,archive_reader_opened=False,validation_executed=False,initializer_credit=0,validator_path=str(target),validator_sha256=sha(target),files={str(p.resolve()):sha(p)for p in[base,target,Path(__file__),tp,patch]+paths}),indent=2)+'\n');print(q,sha(q),ph)
