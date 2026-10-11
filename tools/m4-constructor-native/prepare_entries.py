"""Two physical tail entries already present in the frozen constructor union."""
from pathlib import Path
from collections import deque
import hashlib,json,re,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh additive tail-entry preparation');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Exact physical source input '+str(p));files[str(p)]=v;return p
 source=pin(R/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf');receipt=json.loads(source.read_bytes());p=source.parent/'source-instructions.json';rows=json.loads(pin(p,receipt['files'][str(p.resolve())]).read_bytes());by={x['pc']:x for x in rows};need(len(by)==1401,'Complete current physical instruction union')
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 pin(R/'tools/analysis/pe.py');image=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());graphs={};frontiers=[]
 for entry in(0x4c0310,0x4c0570):
  pending=deque([entry]);seen={};calls=[];unresolved=[];edges=[]
  while pending:
   pc=pending.popleft()
   if pc in seen:continue
   need(pc in by,'Reached physical source row exists '+hex(pc));row=by[pc];seen[pc]=row;raw=bytes.fromhex(row['bytes']);off,_=image.rva_range(pc-image.image_base,row['size']);need(image.data[off:off+len(raw)]==raw,'Whole exact tail instruction '+hex(pc));op=row['mnemonic'];target=re.match(r'0x([0-9a-f]+)\b',row['operands']);target=int(target[1],16)if target else None;fall=pc+row['size']
   if op.startswith('ret'):continue
   if op=='call':
    if target is None:unresolved.append(dict(pc=pc,mnemonic=op,operands=row['operands']))
    else:calls.append(dict(pc=pc,target=target))
    pending.append(fall);edges.append(dict(source=pc,target=fall,kind='source-call-return'));continue
   if op=='jmp':
    need(target is not None,'No unresolved tail JMP in new entries');pending.append(target);edges.append(dict(source=pc,target=target,kind='literal-jump'));continue
   if op.startswith('j'):
    need(target is not None,'Physical finite conditional target');pending.append(target);edges.append(dict(source=pc,target=target,kind='literal-branch'))
   pending.append(fall);edges.append(dict(source=pc,target=fall,kind='literal-fallthrough'))
  ordered=[seen[x]for x in sorted(seen)];need(min(seen)==entry,'No separately reached lower-tail omission');graphs[str(entry)]=dict(entry=entry,instructions=ordered,instruction_count=len(ordered),instruction_bytes_sha256=hashlib.sha256(b''.join(bytes.fromhex(x['bytes'])for x in ordered)).hexdigest(),direct_calls=calls,unresolved_controls=unresolved,FS_sites=[x for x in ordered if'fs:'in x['operands']],FP_sites=[],edges=edges,execution_or_admission=False);frontiers += [dict(entry=entry,**x)for x in unresolved]
 for n,data in [('game-new-graphs.json',graphs),('fs-roots.json',[])]:p=out/n;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
 for p in(__file__,R/'tools/m4-constructor-native/lift_entries.py'):pin(p)
 v=dict(passed=True,scope='Physical closure for two genuine constructor tail entries missing from old dispatch; exact subset of existing1401 rows, no capture/native execution or source equivalence',source_sha256=sha(source),entries=[0x4c0310,0x4c0570],instruction_counts={k:g['instruction_count']for k,g in graphs.items()},priority_new_unresolved_controls=frontiers,source_union_changed=False,initializer_credit=0,files=files);p=out/'report.json';p.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),instruction_counts=v['instruction_counts'])))
if __name__=='__main__':main(sys.argv[1])
