"""Bounded independent-review inputs, synthetic storage and source inverse only."""
from pathlib import Path
import ast,hashlib,json,re,sys
sys.dont_write_bytecode=True
import acceptance138 as A
R=A.ROOT
def main():
 out=R/'reports/m4-138-controls-review/acceptance138-machinery-preflight-r1';assert not out.exists();out.mkdir();controls=[];files={};U=A.storage.Union
 def pin(p):p=Path(p).resolve();files[str(p)]=A.sha(p)
 def okay(label,callback):callback();controls.append(dict(name=label,passed=True))
 def refused(label,callback):
  try:callback()
  except (ValueError,AssertionError,KeyError):controls.append(dict(name=label,refused=True));return
  raise AssertionError('Adverse control unexpectedly allowed '+label)
 p=out/'payload.bin';p.write_bytes(b'whole physical source');h=A.sha(p);u=U(out/'positive.sqlite');u[str(p)]=h;u[str(p).lower()]=h
 okay('canonical-conflict-free-one-row',lambda: A.need(len(u)==1,'One normalized physical dependency'))
 refused('conflicting-whole-identity',lambda:u.__setitem__(str(p),'0'*64))
 okay('fresh-bytehash-whole-union',lambda:A.need(u.verify()['whole_dependency_rows_measured']==1,'Whole byte measure'))
 proof=u.seal();okay('closed-durable-union-identity',lambda:A.need(proof['sqlite_closed_before_hash']and proof['sha256']==A.sha(proof['path']),'Closed immutable proof'))
 v=U(out/'mutation.sqlite');v[str(p)]=h;p.write_bytes(b'x'*len(b'whole physical source'));refused('same-size-mutation-refused',v.verify);v.close();p.write_bytes(b'whole physical source')
 stream=out/'stream.json';stream.write_text(json.dumps(dict(passed=True,files={str(p):h},counts=dict(actual=1)))+'\n');items=[];row=A.storage.read_report(stream,lambda *v:items.append(v));okay('bounded-top-level-and-streamed-files',lambda:A.need(row['passed']is True and row['counts']['actual']==1 and row['files']=={}and items==[(str(p),h)],'Exact streamed receipt'))
 duplicate=out/'duplicate.json';duplicate.write_text('{"passed":true,"files":{'+json.dumps(str(p))+':'+json.dumps(h)+','+json.dumps(str(p))+':'+json.dumps(h)+'}}');refused('duplicate-physical-map-key',lambda:A.storage.read_report(duplicate,lambda *args:None))
 duplicate_top=out/'duplicate-top.json';duplicate_top.write_text('{"passed":true,"passed":true,"files":{}}');refused('duplicate-top-level-key',lambda:A.storage.read_report(duplicate_top,lambda *args:None))
 parent=R/'tools/m4-joint-startup131/acceptance.py';text=parent.read_text();old=text[text.index('def semantic_checks('):text.index('\ndef main(')];new=R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py';derived=new.read_text().split('\n',1)[1].rstrip()+'\n';delta=R/'reports/m4-138-controls-review/acceptance138-machinery-preparation-r3/source-delta.json';changes=json.loads(delta.read_bytes())['changes']
 for c in reversed(changes):assert derived.count(c['after'])==1;derived=derived.replace(c['after'],c['before'])
 okay('exact-inverse-retains-all-parent-semantics',lambda:A.need(derived.rstrip()==old.rstrip(),'Whole accepted source restored'))
 def roots(path):return [int(x,16)for x in re.findall(r'0x[0-9a-fA-F]+',re.search(r'registration_roots *[{]([^}]+)[}]',path.read_text()).group(1))]
 oldheader=R/'reports/m4-joint-startup131/preparation-r1/registration_contract.hpp';newheader=R/'reports/m4-joint-startup138/preparation-r4/registration_contract.hpp';before=roots(oldheader);after=roots(newheader);expected=[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0]
 def valid(values):A.need(len(before)==101 and len(values)==108 and values[:101]==before and values[101:]==expected,'Whole finite registration root extension')
 okay('physical108-root-exact-parent-prefix',lambda:valid(after));wrong=after.copy();wrong[-1]=0x5a6720;refused('callback-address-substitution-refused',lambda:valid(wrong));wrong=after.copy();wrong[0],wrong[1]=wrong[1],wrong[0];refused('old-root-reorder-refused',lambda:valid(wrong))
 okay('required39-gates-no-omitted-baseline',lambda:A.need(len(A.REQUIRED)==39 and len(A.BASE_REQUIRED)==33 and len(A.ADDITIONAL)==6,'All mandatory scopes'))
 for p in [parent,new,delta,oldheader,newheader,Path(__file__),Path(A.__file__),Path(A.storage.__file__),Path(sys.executable),R/'tools/m4-138-controls-review/configure_acceptance138.py',R/'tools/m4-138-controls-review/prepare_acceptance138_machinery.py',R/'tools/m4-138-controls-review/prepare_acceptance138_machinery_v3.py']:
  ast.parse(p.read_text())if p.suffix=='.py'else None;pin(p)
 for p in out.iterdir():
  if p.is_file():pin(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Bounded synthetic storage/duplicate/refusal controls and exact physical finite source/header review; no complete current gates configuration/acceptance/real inventory executed',controls=controls,baseline_gate_count=33,current_gate_count=39,semantic_inverse_changes=len(changes),acceptance_executed=False,real_inventory_expanded=False,capture_reader_opened=False,worker_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=A.sha(q),controls=len(controls))))
if __name__=='__main__':main()
