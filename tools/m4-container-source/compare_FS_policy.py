"""Normal116 frame relation from authentic original and persistent native source."""
from pathlib import Path
import collections,hashlib,json,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-source'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh116 normal FS relation');out.mkdir(parents=True);pins={};counts=collections.Counter();pairs=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact sealed source evidence');pins[str(p)]=v;return p
 def report(path,h=None):
  r=json.loads(pin(path,h).read_bytes());need(r['passed'],'Only current passed source evidence');return r
 try:
  source=report(BASE/'original-game-source-r6/report.json','6f3f23261d711ce6a8a423b79d82410a2e75ab7e1ffcd6e27def7c27d0a408a5');native=report(BASE/'connected-native-source-r4/report.json');report(ROOT/'reports/m4-joint-startup116-root/execution-r1/report.json','0a852e3714e4b3dbc069f5a9b83e0107780c810796090b24537fd335e78c0e5a');original=json.loads(pin(BASE/'original-game-source-r6/FS-source-derivations.json',source['files'][str((BASE/'original-game-source-r6/FS-source-derivations.json').resolve())]).read_bytes());events=json.loads(pin(BASE/'connected-native-source-r4/FS-source-derivations.json',native['files'][str((BASE/'connected-native-source-r4/FS-source-derivations.json').resolve())]).read_bytes());need(len(original)==342 and len(events)==504,'57 actual original FS accesses and42 literal native game accesses per sequence/level')
  for level in('O0','O2'):
   for seq in range(6):
    old=[r for r in original if r['sequence']==seq and r['PC']<0x78000000];new=[r for r in events if r['sequence']==seq and r['level']==level];need(len(old)==len(new)==42,'All fourteen corresponding normal game record groups');active=[];opaque=None
    for a,b in zip(old,new):
     need(a['root']==b['root']and a['PC']==b['PC']and a['kind']==b['kind']and a['source_ESP']==b['ESP'],'Actual/source exact root/PC/direction/stack geometry');kind=a['kind']
     if kind==0:
      if opaque is None:opaque=a['before_head'];need(opaque not in(0,0xffffffff)and not 0x20001000<=opaque<0x20002000,'Retain genuine opaque Windows previous chain DWORD')
      if active:need(a['before_head']==b['before_head']==active[-1]['record'],'Exact nested game predecessor address');counts['exact_nested_game_head_reads']+=1
      else:need(a['before_head']==opaque and b['before_head']==0xffffffff,'Explicit actual Windows predecessor/native Runtime sentinel normal-context boundary')
      active.append(dict(root=a['root'],group=b['group_entry'],previous_original=a['before_head'],previous_native=b['before_head'],record=b['ESP']-4,handler=b['handler']))
     else:
      f=active[-1];need(a['record_address']==b['record_address']==f['record'],'Exact corresponding complete12B source record address');ar=struct.unpack('<3I',bytes.fromhex(a['record_hex']));br=struct.unpack('<3I',bytes.fromhex(b['record_hex']));need(ar[0]==f['previous_original']and br[0]==f['previous_native']and ar[1:]==br[1:]and ar[1]==f['handler'],'All actual original/native12B data with explicit previous-context relation')
      if kind==1:need(ar[2]==0xffffffff and a['after_head']==b['after_head']==f['record'],'Exact literal pushes and record install')
      else:need(a['after_head']==f['previous_original']and b['after_head']==f['previous_native'],'Exact saved predecessor load and normal restore');active.pop();counts['paired_normal_game_frames']+=1
      pairs.append(dict(level=level,sequence=seq,root=a['root'],PC=a['PC'],kind=kind,record_address=f['record'],original_previous=f['previous_original'],native_previous=f['previous_native'],original_complete12B_hex=a['record_hex'],native_complete12B_hex=b['record_hex']));counts['whole12B_paired_game_record_relations']+=1
    need(not active,'All normal nested game frames close')
    for a in[r for r in original if r['sequence']==seq and r['PC']>=0x78000000]:
     need(a['PC']in(0x7800139f,0x780013a6,0x78001419),'Only exact genuine sourcefree NULL normal CRT FS rows');counts['actual_nested_CRT_NULL_FS_source_accesses']+=1
  need(counts['paired_normal_game_frames']==168 and counts['whole12B_paired_game_record_relations']==336,'Complete fourteen frame/level/sequence paired scope');pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'frame-relations.json').write_text(json.dumps(pairs,indent=2)+'\n');pin(out/'frame-relations.json');r=dict(passed=passed,scope='All116 normal game frames: entire12B pushes/scope/previous-chain data, literal source PCs/ESP, authentic original Windows head vs explicit Runtime end-sentinel, exact nested game predecessor and normal restoration. Genuine nested NULL-free source frames separately joined to actual original CPU/FX/ENV/RET by original-source and compiled-observer gates.',counts=dict(counts),AFTER_machine_seed=False,original_context_copied=False,normal_context_relation=True,handler_exception_dispatch=False,unwind_or_cold_TLS=False,files=pins);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
