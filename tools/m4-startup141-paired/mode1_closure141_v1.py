"""Finite current141 mode1/229-PC CRT closure probe; ordinary inputs only.

Re-derives the inherited static 229-PC malloc/free/onexit closure (same pinned
MSVCRT and instruction contracts, same mode1/positive-API prunes) and applies the
inherited per-record rules to every current original141 26-DWORD ledger over
all 846 phases: heap mode 1, lock13 pointer, and only kinds 0/2/3/5/6 returning
to their exact closed CRT sites. Current counts are DERIVED (not 828/2718/1422).
A new kind or return site would expose a CRT path outside the closure and fails.
Measurement only; no footprint completeness, whole-page policy or credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
MSVCRT_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
CONTRACT=('reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
RETURNS={0:0x78001385,2:0x780015bb,3:0x78011c2d,5:0x78001075,6:0x780012b1}
PRUNES={0x7800130e:False,0x78001317:True,0x780013c2:False,0x780013cb:True,0x78001548:False,0x78001551:True,0x78001a34:False,0x78001a3d:True,0x7800106b:False,0x780012dc:False,0x78001a1b:False,0x78001a26:False,0x78011c0f:False,0x78011c2f:True}
ROOTS=(0x780012b3,0x78001390,0x78004a36)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def closure(program,image):
 seen=set();todo=list(ROOTS);missing=set()
 while todo:
  pc=todo.pop()
  if pc in seen:continue
  if pc not in program:missing.add(pc);continue
  seen.add(pc);row=program[pc];mn=row['mnemonic'];ops=row['decoded_operands'];following=pc+row['width'];raw=bytes.fromhex(row['bytes_hex']);off,_=image.rva_range(pc-image.image_base,len(raw));assert image.data[off:off+len(raw)]==raw
  if pc in PRUNES:
   assert mn.startswith('j')and ops[0]['kind']=='immediate';todo.append(ops[0]['value']if PRUNES[pc]else following);continue
  if mn not in('ret','jmp'):todo.append(following)
  if(mn.startswith('j')or mn=='call')and ops and ops[0]['kind']=='immediate':todo.append(ops[0]['value'])
 return seen,missing
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);D=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');PE=load('physicalPE',R/'tools/analysis/pe.py')
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());assert V['passed']and V['reader_closed']
 msvcrt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',MSVCRT_SHA);assert V['files'][str(msvcrt)]==MSVCRT_SHA;image=PE.PEImage(msvcrt.read_bytes())
 program={r['pc']:r for r in json.loads(pin(R/CONTRACT[0],CONTRACT[1]).read_bytes())['instructions']};assert len(program)==1404
 seen,missing=closure(program,image);assert len(seen)==229 and not missing,'Static closure unchanged at 229 PCs'
 assert all(v-6 in seen or v-5 in seen or any(v-w in seen for w in range(2,8))for v in RETURNS.values()),'Every allowed API return word follows a closed CALL site'
 row=next(e for e in V['paired_exports']if e['branch']=='original');i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256'])
 es=D.entries(i,re.compile(r'phase/[0-5]/\d+/(?:api-ledger|CRT-before/(?:2013483008|2013491200))\.bin'));assert len(es)==846*3,len(es)
 counts=collections.Counter();per_seq=[];violations=[]
 with p.open('rb')as f:
  def data(k):
   z=es[k];f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
  for s in range(6):
   c=collections.Counter()
   for ph in range(141):
    stem=f'phase/{s}/{ph}/';mode=data(stem+'CRT-before/2013483008.bin');page=data(stem+'CRT-before/2013491200.bin')
    if not(struct.unpack_from('<I',mode,4)[0]==1 and struct.unpack_from('<I',page,0x5c)[0]==0x78037130):violations.append(dict(sequence=s,phase=ph,rule='mode1/lock13 input'))
    for idx,v in enumerate(struct.iter_unpack('<26I',data(stem+'api-ledger.bin'))):
     kind=v[24];c[kind]+=1
     ok=v[9]==v[19]==0 and kind in RETURNS and v[25]==RETURNS[kind]
     if ok and kind==0:ok=v[10]>0 and 16<=v[22]<=768
     elif ok and kind==2:ok=v[10]>0 and v[22]>0
     elif ok and kind==3:ok=v[10]>0 and v[22]>0 and 0<v[23]<=1024
     elif ok and kind in(5,6):ok=v[20]==0x78037130
     if not ok:violations.append(dict(sequence=s,phase=ph,index=idx,kind=kind,return_word=v[25],args=list(v[20:24]),EAX=v[10]))
   counts.update(c);per_seq.append(dict(sequence=s,counts={str(k):n for k,n in sorted(c.items())}))
 assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)]
 rp=out/'mode1-closure.json';rp.write_text(json.dumps(dict(closure_PCs=sorted(seen),per_sequence=per_seq,violations=violations[:2000]),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=not violations,scope='Current141 original mode1/lock13 inputs at 846 phases and every 26-DWORD API record against the unchanged static 229-PC closure; derived counts; measurement only, not footprint completeness, whole-page policy or credit',
  static_closure_PCs=len(seen),mode_lock_inputs=846,api_records=sum(counts.values()),counts_by_kind={str(k):n for k,n in sorted(counts.items())},positive_heap_results=counts[0]+counts[2]+counts[3],inherited_counts_reused=False,violations=len(violations),
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','static_closure_PCs','mode_lock_inputs','api_records','counts_by_kind','positive_heap_results','violations')}))
 if violations:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
