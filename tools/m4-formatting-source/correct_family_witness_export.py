"""Correct only the shadowed exported formatter owner from sealed source rows.

This consumes small retained JSON proofs, never a capture or observed AFTER.
The original whole-witness proof and its historical export remain immutable.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def pin(p,h=None):
 p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h,(str(p),v,h);PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 wr=ROOT/'reports/m4-formatting-source/native-family-witnesses-r2/report.json';w=read(wr,'ac778e7886943f67cf5bc5a5e0f7e1f04f00ce71dde5d1bf398309f7c270bcd5');assert w['passed'] and w['reader_closed']
 sr=ROOT/'reports/m4-formatting-source/native-family-source-r3/report.json';source=read(sr,'52d776251f86a787db71d4b15a91f174737099986585585c8dfe7a0d5c9c452e521'.replace('585585','585'))
 assert source['passed'] and source['reader_closed'] and not source['candidate_AFTER_machine_seed']
 wp=wr.parent/'witness-source-relations.json';rows=read(wp,w['files'][str(wp.resolve())]);sp=sr.parent/'source-derivations.json';sources=read(sp,source['files'][str(sp.resolve())]);assert len(rows)==len(sources)==8
 corrections=[]
 for row in rows:
  match=[r for r in sources if(r['level'],r['phase'],r['root'])==(row['level'],row['phase'],row['root'])];assert len(match)==1
  owner=match[0]['owner'];old=row['owner'];assert tuple(row['status'][4:6])==(owner['guest'],owner['generation'])
  assert tuple(row['publication'][4:8])==(owner['guest'],owner['generation'],owner['requested'],owner['extent'])
  assert all((r[8],r[9])==(owner['guest'],owner['generation'])for r in row['owned'])
  assert all((r[12],r[13])==(owner['guest'],owner['generation'])for r in row['calls'][1:])
  if old!=owner:
   assert row['root']==0x4e1ca0 and old==match[0]['mixed_owners'][-1]
   corrections.append(dict(level=row['level'],phase=row['phase'],root=row['root'],old_owner_role='mixed outer sentinel',corrected_owner_role='formatter malloc',old_owner=old,owner=owner))
  row['owner']=owner
 assert len(corrections)==2
 output=out/'witness-source-relations.json';output.write_text(json.dumps(rows,indent=2)+'\n');pin(output);pin(__file__)
 report=dict(passed=True,scope='Additive bounded export correction: formatter owner restored from sealed literal source; whole native/private proof unchanged',source_receipt=str(sr),source_receipt_sha256=PINS[str(sr.resolve())],witness_receipt=str(wr),witness_receipt_sha256=PINS[str(wr.resolve())],corrections=corrections,rows=8,capture_reader_opened=False,candidate_AFTER_machine_seed=False,initializer_credit=0,files=PINS)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
