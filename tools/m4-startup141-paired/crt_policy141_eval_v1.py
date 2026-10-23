"""Finite current141 whole two-page CRT policy evaluation probe; ordinary only.

Builds the 12 current (O0/O2 x six sequences) policy domains from current own
original141/native141 phase0 BEFORE pages, the eight current registry-IAT patch
spec rows, the measured import-cells141-r1 cells, lock13-counts141-r1 counts,
own lock25 cells and the source-derived original registry metadata
(registry-output141-r1) plus native summary metadata, then runs the unchanged
crt_page_policy141_v1 (v5 with measured restore phase 15 and lock13 [111,111])
over every phase/side for both whole pages. Not ROOT-admitted acceptance: the
lock25 targets are own-input bound here (not independently source/API bound),
and footprint inventory completeness remains pending. No credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
IAT,DATA=0x7802e000,0x78037000
TYPED=set(range(0x8c,0x90))|set(range(0x130,0x148))|set(range(0x888,0x890))
CONFIG=('reports/m4-original141-source/configuration-preparation-r3/configuration.json','451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0')
RECEIPTS={'registry':'reports/m4-startup141-paired/registry-output141-r1/report.json','imports':'reports/m4-startup141-paired/import-cells141-r1/report.json','lock13':'reports/m4-startup141-paired/lock13-counts141-r1/report.json','footprint':'reports/m4-startup141-paired/footprint141-r2/report.json','native_schedule':'reports/m4-startup141-paired/registry-native-schedule141-r2/report.json'}
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);D=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');P=load('policy141',R/'tools/m4-startup141-paired/crt_page_policy141_v1.py')
 rec={k:json.loads(pin(R/v).read_bytes())for k,v in RECEIPTS.items()};assert all(r['passed']is True for r in rec.values())
 rows=json.loads(pin(rec['registry']['output']['path'],rec['registry']['output']['sha256']).read_bytes());orig={(r['sequence'],r['phase']):r for r in rows}
 cells_doc=json.loads(pin(rec['imports']['output']['path'],rec['imports']['output']['sha256']).read_bytes());cells=cells_doc['cells'];assert len(cells)==144 and rec['imports']['violations']==0
 counts=rec['lock13']['original_per_sequence'];assert all(c==counts[0]for c in counts)and all(c==counts[0]for lv in('O0','O2')for c in rec['lock13']['native_selected_per_sequence'][lv]);lock13_counts=counts[0]
 restore=sorted({int(k.split('/')[1])for k in rec['imports']['first_not_fully_installed']});assert restore==[15]and rec['imports']['endpoints_with_shims_not_fully_installed']==12;restore_phase=restore[0]
 C=json.loads(pin(R/CONFIG[0],CONFIG[1]).read_bytes());V=json.loads(pin(C['validation']['path'],C['validation']['sha256']).read_bytes());assert V['passed']and V['reader_closed']
 patches=[p for p in json.loads(pin(C['current_transition_patches']['path'],C['current_transition_patches']['sha256']).read_bytes())if IAT<=p['pc']<IAT+4096];assert len(patches)==8 and all(p['kind']=='registry-IAT'for p in patches)
 import_rows=[dict(offset=c['offset'],library=c['library'],name=c['name'],native_raw_thunk=c['native_raw_thunk'],original_real_target=c['original_real_target'],original_installed_target=c['observer_shim_target']if c['observer_shim_target']is not None else c['original_real_target'],observer_shim=c['observer_shim_target']is not None,physical_export_chain=c['physical_export_chain'])for c in cells]
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True
 orow=next(e for e in V['paired_exports']if e['branch']=='original');oi=pin(orow['index_path'],orow['index_sha256']);op=pin(orow['payload_path'],orow['payload_sha256'])
 oes=D.entries(oi,re.compile(r'phase/[0-5]/\d+/CRT-(?:before|after)/(?:2013454336|2013491200)\.bin'));assert len(oes)==846*4
 def reader(path,es):
  f=Path(path).open('rb')
  def rd(k):
   z=es[k];f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
  return f,rd
 of,ord_=reader(op,oes);evaluated=0;failures=[];domains=[]
 try:
  for lv in('O0','O2'):
   row=next(e for e in N['paired_exports']if e['branch']==lv);ni=pin(row['index_path'],row['index_sha256']);np_=pin(row['payload_path'],row['payload_sha256'])
   nes=D.entries(ni,re.compile(r'sequence-[0-5]/(?:phase-\d+-(?:before|after)-page-(?:2013454336|2013491200)|phase-\d+-after-registry|caller-projection-before/registry|selected/locale-critical-sections)\.bin'))
   nf,nrd=reader(np_,nes)
   try:
    for s in range(6):
     ao={IAT:ord_(f'phase/{s}/0/CRT-before/{IAT}.bin'),DATA:ord_(f'phase/{s}/0/CRT-before/{DATA}.bin')};bo={IAT:nrd(f'sequence-{s}/phase-0-before-page-{IAT}.bin'),DATA:nrd(f'sequence-{s}/phase-0-before-page-{DATA}.bin')}
     unused=sorted({i for i in range(4096)if ao[DATA][i]!=bo[DATA][i]}-TYPED)
     section=next(v for v in struct.iter_unpack('<16Q',nrd(f'sequence-{s}/selected/locale-critical-sections.bin'))if v[1]==0x78037130)
     lock13=[dict(offset=0x130,size=24,role='initialized_lock13_opaque_API_resource',guest_address=0x78037130,original_initial_hex=ao[DATA][0x130:0x148].hex(),native_initial_hex=bo[DATA][0x130:0x148].hex(),native_resource_extent=section[11],native_resource_pointer=section[10],original_enter_leave=lock13_counts,native_enter_leave=list(section[3:5]),native_initializations=section[6],opaque_API_internals_equivalent=False)]
     loader=[dict(offset=0x8c,role='initialized_lock25',original_target=struct.unpack_from('<I',ao[DATA],0x8c)[0],native_target=struct.unpack_from('<I',bo[DATA],0x8c)[0],binding='own BEFORE input value; independent source/API binding pending')]
     policy=P.Policy(ao,bo,patches,unused,import_rows,loader,lock13,restore_phase,lock13_counts)
     native_before=struct.unpack('<32Q',nrd(f'sequence-{s}/caller-projection-before/registry.bin'));native_meta_prev=[native_before[6],native_before[7]]
     for ph in range(141):
      o=orig[(s,ph)];nq=struct.unpack('<32Q',nrd(f'sequence-{s}/phase-{ph}-after-registry.bin'));native_after=[nq[6],nq[7]]
      for side,om,nm in(('before',o['source_before_metadata'],native_meta_prev),('after',o['source_computed_after_metadata'],native_after)):
       for page in(IAT,DATA):
        a=ord_(f'phase/{s}/{ph}/CRT-{side}/{page}.bin');b=nrd(f'sequence-{s}/phase-{ph}-{side}-page-{page}.bin')
        try:policy.page(ph,side,page,a,b,om,nm);evaluated+=1
        except ValueError as e:failures.append(dict(level=lv,sequence=s,phase=ph,side=side,page=page,reason=str(e)))
      native_meta_prev=native_after
     domains.append(dict(level=lv,sequence=s,unused=len(unused),lock25=loader[0],native_lock13_pointer=section[10]))
   finally:nf.close()
   assert sha(ni)==pins[str(ni)]and sha(np_)==pins[str(np_)]
 finally:of.close()
 assert sha(oi)==pins[str(oi)]and sha(op)==pins[str(op)]
 rp=out/'policy-evaluation.json';rp.write_text(json.dumps(dict(domains=domains,failures=failures[:3000]),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=not failures,scope='Current141 whole two-page CRT policy (v5 with measured restore phase/lock13 counts) evaluated over every phase/side of 12 domains; probe, not ROOT-admitted acceptance',
  page_evaluations=evaluated,expected_evaluations=12*141*2*2,failures=len(failures),failure_reasons=sorted({f['reason']for f in failures})[:20],restore_phase=restore_phase,lock13_counts=lock13_counts,
  lock25_independent_source_binding=False,footprint_inventory_completeness_claim=False,output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','page_evaluations','expected_evaluations','failures','failure_reasons','restore_phase','lock13_counts')}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
