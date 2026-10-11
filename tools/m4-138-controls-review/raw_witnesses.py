"""Independent bounded ordinary controls witness review; never a full verifier."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();pins={};counts=collections.Counter();results=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');key=str(p)
  if key not in pins:pins[key]=sha(p)
  assert h is None or pins[key]==h,key;return p
 def raw(p):return pin(p).read_bytes()
 def read(p):return json.loads(raw(p))
 def words(p,n):b=raw(p);assert len(b)==n*8;return struct.unpack('<'+'Q'*n,b)
 execution=R/'reports/m4-joint-startup138/context-controls-execution-r1/report.json';pin(execution,'43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863')
 # Bounded header reader reuses no producer assertions or native/source execution.
 sp=importlib.util.spec_from_file_location('controls_receipt_header',pin(R/'tools/m4-138-controls-review/readiness.py'));module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)
 e=module.header(execution);assert e['passed']and e['all_workers_terminal']and not e['archive_reader_opened']and e['actual_workers_launched']==16
 report=R/'reports/m4-joint-startup138/context-controls-verification-r1/report.json';pin(report,'88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb')
 proofs=read(report.parent/'actual-Context-causes.json');assert len(proofs)==16;bycase={(p['level'],p['mode']):p for p in proofs};assert len(bycase)==16
 prep=read(e['preparation_path']);assert pin(e['preparation_path'],e['preparation_sha256'])
 contract=read(R/'reports/m4-fps-native/connected-component-preparation-r4/contracts.json');pcs={p['pc']for p in contract['instructions']}
 literals=raw(R/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp').decode()
 table=re.search(r'inline constexpr Operand \w+\[\]\{(.*?)\n\};',literals,re.S).group(1)
 operands=[(int(pc),int(role),int(off),int(width),write=='true')for pc,role,off,width,write in re.findall(r'\{(\d+),(\d+),(-?\d+),(\d+),(true|false)\}',table)]
 roots=re.search(r'inline constexpr Root \w+\[\]\{(.*?)\n\};',literals,re.S).group(1);roots=[tuple(map(int,x.split(',')))for x in re.findall(r'\{([^{}]+)\}',roots)]
 first=next(v for v in roots if v[0]==0x5a3c30);second=next(v for v in roots if v[0]==0x5a3ff0)
 def snapshot(folder):
  m={}
  for p in folder.iterdir():
   if p.is_file()and(p.name.startswith('game-region-')or p.name.startswith('provider-source-page-')):m[int(p.stem.split('-')[-1])]=bytearray(raw(p))
  m[0x20001000]=bytearray(raw(folder/'stack.bin'));t=struct.unpack('<5I',raw(folder/'TIB.bin'));assert t[0]==t[4]and t[2:4]==(0x20002000,0x20001000)
  for off,value in((0,t[1]),(4,t[2]),(8,t[3]),(24,t[4])):m[t[0]+off]=bytearray(struct.pack('<I',value))
  return m,t
 def locate(m,a,n):
  entries=[(p,v)for p,v in m.items()if p<=a and a+n<=p+len(v)];assert len(entries)==1;return entries[0]
 seen=set()
 for run in e['runs']:
  key=(run['level'],run['mode']);assert key not in seen;seen.add(key);proof=bycase[key];f=Path(run['capture']);mode=run['mode']
  status=struct.unpack('<16I',raw(f/'status.bin'));assert status[:5]==(1,mode,*proof['case'])and status[5:10]==(1,1,1,1,135)and status[15]==1
  assert raw(f/'refusal.txt').decode()==proof['actual_reason'];assert struct.unpack('<9I',raw(f/'cause.bin'))==tuple(proof['actual_cause_words'])
  assert raw(f/'admission.txt').decode()==e['admission_review_sha256'];assert raw(f/'COMPLETE.txt')==b'Complete current Context refusal/retry and owned cleanup'
  context=f/'Widget/same-context-before';after=f/'Widget/same-context-after';assert words(context/'Context.bin',13)==tuple(proof['actual_fault_context_words'])
  # This current Context folder contains only these complete direct files.
  before_files={p.name:p for p in context.iterdir()if p.is_file()};after_files={p.name:p for p in after.iterdir()if p.is_file()}
  assert set(before_files)==set(after_files)and len(before_files)==17
  assert all(p.is_file()for p in context.iterdir())and all(p.is_file()for p in after.iterdir())
  for n,p in before_files.items():assert raw(p)==raw(after_files[n]);counts['whole_current_Context_retry_files']+=1
  def component(stem):
   p=[p/stem for p in(f/'Widget').glob('root-*')if(p/stem).is_dir()];assert len(p)==1;return p[0]
  ca=component('input-after');fault=component('same-context-before');clean=component('cleaned')
  start=list(struct.iter_unpack('<IIQII',raw(ca/'accesses.bin')));finish=list(struct.iter_unpack('<IIQII',raw(fault/'accesses.bin')))
  assert finish[:len(start)]==start;source=finish[len(start):];assert [list(row)for row in source]==proof['actual_suffix_operands']
  m,t=snapshot(f/'Widget/input-after')
  if mode!=6:p,v=locate(m,0x20001800,4);v[0x20001800-p:0x20001804-p]=struct.pack('<I',0x410a80)
  for index,(pc,address,value,width,write)in enumerate(source):
   ep,role,off,ew,writing=operands[second[11]+index];ea=0x20001800+off if role==1 else t[0]if role==2 else off
   assert pc in pcs and(pc,address,width,bool(write))==(ep,ea,ew,writing)and value<1<<(8*width)
   p,v=locate(m,address,width)
   if not write:assert int.from_bytes(v[address-p:address-p+width],'little')==value
   elif mode in(5,7)and index==len(source)-1:assert [pc,address,value,width]==proof['last_denied_uncommitted_write']
   else:v[address-p:address-p+width]=value.to_bytes(width,'little')
  endpoint,_=snapshot(context);assert set(m)==set(endpoint)
  for a,value in m.items():assert value==endpoint[a];counts['whole_own_partial_memory_extents']+=1
  fonts=list(struct.iter_unpack('<IIIIQBB6x',raw(ca/'fonts.bin')));cleanfonts=list(struct.iter_unpack('<IIIIQBB6x',raw(clean/'fonts.bin')));owned=[x for x in fonts if x[5]and x[6]]
  assert len(owned)==15 and len(fonts)==len(cleanfonts)and all(x[3]==first[0]and x[0]==0x72001000+16*x[1]for x in owned)
  for a,b in zip(fonts,cleanfonts):assert b==(a[:6]+(0,)+a[7:]if a[5]and a[6]else a)
  thread=words(fault/'status.bin',12)[0];manual=f/'Widget/manual-font-cleanup'
  assert {p.name for p in manual.iterdir()}=={str(x[1])+suffix for x in owned for suffix in('-row.bin','-hardware.bin')}
  for font in owned:
   row=words(manual/(str(font[1])+'-row.bin'),8);assert row[:5]==font[:5]and row[5]==thread and row[6]and row[7]==1
   hardware=raw(manual/(str(font[1])+'-hardware.bin'));assert len(hardware)==1152;counts['actual_owned_DeleteObject_rows']+=1
  for label in('invoke','retry','cleanup'):
   h=raw(f/(label+'-hardware.bin'));assert len(h)==1632 and h[:512]==h[1088:1600]and h[512:540]==h[1600:1628];counts['whole_ASM_FX512_ENV28_restore_pairs']+=1
  summary=words(f/'cleaned/Registry/registry-summary.bin',32);prior=words(f/'retry-before/Registry/registry-summary.bin',32)
  assert summary[:5]==(1,1,0,1,1)and summary[5]==prior[5]and summary[10]==summary[11]==summary[15]==0
  counts['exact_current_case_witnesses']+=1;counts['exact_causal_source_operand_rows']+=len(source);results.append(dict(level=key[0],mode=mode,source_rows=len(source),resource_rows=len(owned),full_current_Context_direct_retry=True))
 # Authenticate every selected physical byte against the sealed verifier files
 # map with a bounded one-line JSON stream, never materializing its huge map.
 targets=dict(pins);embedded={};inside=False;rows_seen=0
 with report.open(encoding='utf-8')as stream:
  for line in stream:
   if line=='  "files": {\n':inside=True;continue
   if not inside:continue
   if line=='  }\n':break
   pair=json.loads('{'+line.strip().removesuffix(',')+'}');key,value=next(iter(pair.items()));rows_seen+=1
   if key in targets:assert key not in embedded;embedded[key]=value
 # The standalone audit header tool is new, the controls report cannot pin itself.
 excluded={str(report.resolve()),str((R/'tools/m4-138-controls-review/readiness.py').resolve())}
 assert set(embedded)==set(targets)-excluded
 for p,h in embedded.items():assert h==pins[p]and sha(p)==h
 pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Independent bounded16case exact refusal/source-prefix/whole current Context17file retry/typed cleanup/48hardware review; no full raw control acceptance',
  counts=dict(counts),cases=results,sealed_controls_report_sha256=pins[str(report.resolve())],files_map_rows_streamed=rows_seen,selected_raw_and_provenance_targets_authenticated=len(embedded),
  archive_reader_opened=False,worker_executed=False,verifier_rerun=False,initializer_credit=0,full_raw_inventory_authenticated=False,whole_component_private_retry_authenticated=False,whole_provider_resource_retry_authenticated=False,
  original138_or_current_native3_link_equivalence_proved=False,named_GDI_physical_export_ownership_independently_reverified=False,
  limitations=['No authentication of all10.7million output files or3,547,696reported private/resource retry relations','Typed cleanup row and generation/thread/handle joins checked; named physical GDI export-owner and all identity observations still need independent review','Source operands join exact immutable source roles and same input byteflow; new source callbacks not executed','Partial scalar registers, hidden frames, rights bytes and whole prior131 source equivalence remain unobserved'],files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
