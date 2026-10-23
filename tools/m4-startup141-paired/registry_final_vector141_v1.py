"""Finite current141 final registry vector/unused-tail relation probe.

At the end of the selected141 chronology, joins the native141 source6 owned
registry allocation (locale-allocations record at the final summary begin, its
selected owned page and own initial bytes) to the original141 source-computed
phase140 backing (registry-output141-r1). Requires the whole used callback
vector to be byte-identical, equal to the original cleanup vector, and each
branch's unused capacity tail to equal its OWN API-initial bytes (cross-branch
padding is not required equal). Measurement only; no per-phase native backing,
whole-page policy or paired141 credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ORIGINAL_ROWS=('reports/m4-startup141-paired/registry-output141-r1/report.json','01001e325524d61f7d1f6f10cc7509d12c53a174c0f8f7bbb919dc090776b005')
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);helper=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');spec=importlib.util.spec_from_file_location('ordinary_entries',helper);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 O=json.loads(pin(R/ORIGINAL_ROWS[0],ORIGINAL_ROWS[1]).read_bytes());assert O['passed']is True;rows=json.loads(pin(O['output']['path'],O['output']['sha256']).read_bytes());assert len(rows)==846
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());assert V['passed']and V['reader_closed']
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True and N['paired_export_readers_closed']is True
 orow=next(e for e in V['paired_exports']if e['branch']=='original');oi=pin(orow['index_path'],orow['index_sha256']);op=pin(orow['payload_path'],orow['payload_sha256']);oes=D.entries(oi,re.compile(r'cleanup/[0-5]/registry\.bin'));assert len(oes)==6
 def read(path,es,k):
  z=es[k]
  with Path(path).open('rb')as f:f.seek(z['offset']);b=f.read(z['bytes'])
  assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
 results=[]
 for s in range(6):
  final=next(r for r in rows if r['sequence']==s and r['phase']==140);om=final['source_computed_after_metadata'];ob=bytes.fromhex(final['source_computed_after_backing_hex']);used=om[1]-om[0];cap=om[2]
  last=[r for r in rows if r['sequence']==s and r['growth']][-1];oinit=bytes.fromhex(last['source_realloc_input']['initial_hex']);assert last['source_computed_after_metadata'][2]==cap and len(oinit)>=cap
  cleanup=read(op,oes,f'cleanup/{s}/registry.bin');assert len(cleanup)==444 and used==444 and ob[:used]==cleanup,'Original source vector equals actual cleanup vector'
  assert ob[used:cap]==oinit[used:cap],'Original unused tail is its own API-initial bytes'
  results.append(dict(sequence=s,used=used,capacity=cap,original_tail_hex=ob[used:cap].hex(),levels={}))
 for lv in('O0','O2'):
  row=next(e for e in N['paired_exports']if e['branch']==lv);i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256'])
  es=D.entries(i,re.compile(r'sequence-[0-5]/(?:phase-140-after-registry|selected/locale-allocations|selected/locale-allocation-\d+-(?:owned-page|initial))\.bin'))
  for s in range(6):
   res=results[s];used=res['used'];cap=res['capacity'];final=next(r for r in rows if r['sequence']==s and r['phase']==140);ob=bytes.fromhex(final['source_computed_after_backing_hex'])
   q=struct.unpack('<32Q',read(p,es,f'sequence-{s}/phase-140-after-registry.bin'));begin=q[6];assert q[7]-q[6]==used
   allocs=[a for a in struct.iter_unpack('<16Q',read(p,es,f'sequence-{s}/selected/locale-allocations.bin'))if a[1]==begin];assert len(allocs)==1,'One owned native allocation at the final registry begin'
   a=allocs[0];assert a[0]==1 and a[2]==cap and a[3]==cap and a[9]==1 and a[10]==0 and a[11]==0,'Live mapped native registry allocation with original capacity'
   page=read(p,es,f'sequence-{s}/selected/locale-allocation-{a[5]}-owned-page.bin');init=read(p,es,f'sequence-{s}/selected/locale-allocation-{a[5]}-initial.bin');assert len(page)==a[4]and len(init)>=cap
   assert page[:used]==ob[:used],'Whole native callback vector equals original source vector'
   assert page[used:cap]==init[used:cap],'Native unused tail is its own API-initial bytes'
   res['levels'][lv]=dict(native_generation=a[5],native_tail_hex=page[used:cap].hex(),vector_equal=True,own_tail=True,cross_branch_tail_equal=page[used:cap]==ob[used:cap])
  assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)]
 assert sha(oi)==pins[str(oi)]and sha(op)==pins[str(op)]
 rp=out/'final-vector-relations.json';rp.write_text(json.dumps(results,indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='Final selected141 registry: whole111 callback vector equal across original source, original cleanup and native O0/O2 owned allocation; each unused tail equals own API-initial bytes. No per-phase native backing, whole-page policy or paired141 claim',
  sequences=6,levels=2,vector_relations=12,own_tail_relations=18,cross_branch_tail_equal=sum(r['levels'][lv]['cross_branch_tail_equal']for r in results for lv in('O0','O2')),
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('vector_relations','own_tail_relations','cross_branch_tail_equal')}))
if __name__=='__main__':main(sys.argv[1])
