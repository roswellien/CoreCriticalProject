"""Ordinary physical order/callback/code geometry checks, no execution."""
from pathlib import Path
import copy,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141/geometry-controls-r1';assert not out.exists();out.mkdir()
 p=R/'reports/m4-original141/geometry-preparation-r3';report=json.loads((p/'report.json').read_bytes());files={}
 for path,digest in report['files'].items():assert sha(Path(path))==digest;files[path]=digest
 game=PEImage((R/'MW3/Mech3.exe').read_bytes());order=json.loads((p/'selected-order.json').read_bytes());vector=json.loads((p/'callback-vector111.json').read_bytes());contracts=json.loads((p/'callback-source-contracts.json').read_bytes());proof=[];checks=[]
 def physical(pc,width):offset,_=game.rva_range(pc-game.image_base,width);return game.data[offset:offset+width]
 def callbacks(rows):
  assert len(rows)==111 and len({v['root']for v in rows})==111
  assert [v['root']for v in rows]==[v['entry']for v in order if str(v['entry'])in contracts]
  for v in rows:
   c=contracts[str(v['root'])];call=c.get('CALL_pc',c.get('registration_CALL_pc'));push=c.get('push_pc',c.get('push_PC',call-5));raw=physical(push,5);assert raw==b'\x68'+struct.pack('<I',v['callback']);callraw=physical(call,5);assert callraw[0]==0xe8;target=call+5+struct.unpack('<i',callraw[1:])[0]
   assert target==0x5ac140
  return True
 callbacks(vector);checks.append('Every111 callback PUSH/directCALL physically verified; exact sorted carried root order')
 for v in vector:
  c=contracts[str(v['root'])];call=c.get('CALL_pc',c.get('registration_CALL_pc'));push=c.get('push_pc',c.get('push_PC',call-5));proof.append(dict(**v,push_PC=push,push_hex=physical(push,5).hex(),CALL_PC=call,CALL_hex=physical(call,5).hex(),target=0x5ac140))
 def reject(label,change):
  v=copy.deepcopy(vector);change(v)
  try:callbacks(v)
  except AssertionError:checks.append(label);return
  raise AssertionError('Missing rejection '+label)
 reject('Missing callback rejected',lambda v:v.pop())
 reject('Altered callback rejected by physical PUSH',lambda v:v[0].__setitem__('callback',v[0]['callback']^1))
 reject('Reordered callback root rejected',lambda v:v.reverse())
 reject('Duplicate registration root rejected',lambda v:v.__setitem__(1,v[0]))
 old=json.loads((R/'reports/m4-startup138-original/preparation-r8/selected-order.json').read_bytes());assert [v for v in order if v['entry']not in(0x4103f0,0x410440,0x459b40)]==old;checks.append('All138 physical relative root/slot pairs retained exactly')
 raw=(p/'pages.bin').read_bytes();count=struct.unpack_from('<I',raw,8)[0];assert count==176 and len(raw)==12+count*4104;pages={struct.unpack_from('<I',raw,12+i*4104)[0]:raw[20+i*4104:4116+i*4104]for i in range(count)}
 oldreport=json.loads((R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes());oldpack=(R/'reports/m4-startup138-original/preparation-r8/pages.bin').read_bytes();n=struct.unpack_from('<I',oldpack,8)[0];oldpages={struct.unpack_from('<I',oldpack,12+i*4104)[0]:oldpack[20+i*4104:4116+i*4104]for i in range(n)}
 for row in oldreport['source_spans']:
  # The legacy game bytes and all provider rows retain their exact pack cells.
  for i in range(row['size']):
   address=row['pc']+i
   if address&~4095 in oldpages:assert pages[address&~4095][address&4095]==oldpages[address&~4095][address&4095]
 checks.append('All5040 inherited complete source bytes retained in union pack')
 f=out/'physical-callback-vector111.json';f.write_text(json.dumps(proof,indent=2)+'\n');files[str(f)]=sha(f);files[str(p/'report.json')]=sha(p/'report.json');files[str(Path(__file__).resolve())]=sha(Path(__file__))
 result=dict(passed=True,checks=checks,controls=len(checks),physical_callbacks=111,scope='Static actual physical geometry and callback source only; complete observer CPP/ASM composition/build/linked attribution/strict current capture/source/pair acceptance pending',canonical_reader_opened=False,worker_executed=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'report.json'),sha256=sha(out/'report.json'),controls=len(checks))))
if __name__=='__main__':main()
