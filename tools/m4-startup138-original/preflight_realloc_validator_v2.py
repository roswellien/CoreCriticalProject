from pathlib import Path
import ast,collections,hashlib,json,struct,textwrap
R=Path(__file__).resolve().parents[2];path=R/'reports/m4-startup138-original/realloc-validator-preparation-r2/report.json';d=json.loads(path.read_bytes());assert hashlib.sha256(path.read_bytes()).hexdigest()=='18556f4314597eb48124d125404bc482979df6d7a2ffe77a18d05d893e30bec3'
change=d['changes'][1];body=textwrap.dedent(change['new'][:-len(change['old'])]);compile(body,'common-phase-gate','exec');results=[]
for phase,entry in((47,0x479590),(134,0x5a3c30)):
 for corrupt in(False,True):
  before=bytes(range(128));w=[0]*26;w[4]=0x20001000;w[14]=w[4]+20;w[10]=0x310000;w[22]=0x300000;w[23]=144;w[24]=3;w[25]=0x78011c2d;stem=f'phase/0/{phase}/';values={stem+'api-ledger.bin':struct.pack('<26I',*w),stem+'api-count.bin':struct.pack('<I',1),stem+'registry-before-meta.bin':struct.pack('<4I',0x300000,0x300080,128,1),stem+'registry-before-backing.bin':before,stem+'api-initial/0/size.bin':struct.pack('<I',144),stem+'api-initial/0/bytes.bin':(b'\xee'+before[1:]if corrupt else before)+b'\xcc'*16}
  class Records:
   def data(self,k):return values[k]
  def need(v,m):
   if not v:raise ValueError(m)
  env=dict(struct=struct,records=Records(),seq=0,phase=phase,entry=entry,roots={0x4b7f70:None},counts=collections.Counter(),need=need);passed=True
  try:exec(body,env)
  except ValueError:passed=False
  assert passed!=corrupt;assert entry not in env['roots'];assert env['counts']['actual_HeapReAlloc_initial_full_backing_witnesses']==int(passed);results.append(dict(phase=phase,entry=entry,outside_Lockit_roots=True,prefix_corrupt=corrupt,accepted=passed))
out=R/'reports/m4-startup138-original/realloc-validator-preflight-r2';assert not out.exists();out.mkdir();files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(path,Path(d['validator_path']),Path(__file__))};q=out/'report.json';q.write_text(json.dumps(dict(passed=True,controls=results,gate_executes_for_both_widget_growth_phases=True,archive_reader_opened=False,source_or_target_machine_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
