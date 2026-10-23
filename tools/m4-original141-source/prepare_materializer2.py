"""Immutable exact producer chronology correction, no reader or import."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/input-materialization-preparation-r2';assert not out.exists();out.mkdir();p=R/'tools/m4-original141-source/materialize_current_inputs_v1.py';q=p.with_name('materialize_current_inputs_v2.py');assert not q.exists();a=p.read_text();b=a
 changes=[("[(15,'before',z),(15,'after',a),(16,'before',a),(16,'after',z)]","[(14,'after',z),(15,'before',a),(15,'after',a),(16,'before',z)]"),("'Current exact owning remove/reinstall span'","f'Current exact owning producer-cut span PC={pc:#x} sequence={seq} phase={phase} side={side} expected={want.hex()} actual={page(seq,phase,side,pc&~4095)[pc&4095:(pc&4095)+len(want)].hex()}'")]
 for old,new in changes:assert b.count(old)==1;b=b.replace(old,new)
 q.write_text(b);back=b
 for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
 assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n')
 recipe=R/'reports/m4-original141-source/input-materialization-preparation-r1/required-ordinary-files.json';files=json.loads(recipe.read_bytes());files.pop(str(p));files[str(q)]=sha(q)
 reference=R/'reports/m4-original141/source-preparation-r6/reference.cpp';files[str(reference)]=sha(reference);files[str(Path(__file__).resolve())]=sha(Path(__file__));files[str(out/'inverse.json')]=sha(out/'inverse.json');(out/'required-ordinary-files.json').write_text(json.dumps(files,indent=2)+'\n')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,canonical_reader_opened=False,ordinary_export_opened=False,imports_executed=False,source_execution=False,initializer_credit=0,exact_whole_inverse=True,inverse_hunks=len(d),semantic_delta='Only exact actual producer input cut: phase14 AFTER patched; phase15 BEFORE and AFTER restored; phase16 BEFORE patched. Expanded error label reports PC/sequence/phase/side/expected/actual. Source originals and owning named input guards retained.',required_ordinary_files=str(out/'required-ordinary-files.json'),files={str(p):sha(p),str(p.with_name('materialize_current_inputs_v2.py')):sha(p.with_name('materialize_current_inputs_v2.py')),str(recipe):sha(recipe),str(reference):sha(reference),str(out/'inverse.json'):sha(out/'inverse.json'),str(out/'required-ordinary-files.json'):sha(out/'required-ordinary-files.json'),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
