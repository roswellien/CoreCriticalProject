"""Finite current141 native registry schedule vs original source schedule probe.

Decodes native141 source6 per-phase onexit Session::summary() (32 QWORDs:
bootstrapped, running, failed, finished, roots, begin@7803788C, next@78037888,
capacity, entries, ...) for O0/O2 and joins it to the original141 source-derived
schedule (registry-output141-r1): entry count, growth phases and capacity, plus
native CRT-page metadata cells 0x888/0x88C against the summary. Heap addresses
legitimately differ by branch and are not compared. Measurement only: no native
backing/vector or unused-tail claim, no paired141 or accepted credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ORIGINAL_ROWS=('reports/m4-startup141-paired/registry-output141-r1/report.json','01001e325524d61f7d1f6f10cc7509d12c53a174c0f8f7bbb919dc090776b005')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);helper=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');spec=importlib.util.spec_from_file_location('ordinary_entries',helper);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 O=json.loads(pin(R/ORIGINAL_ROWS[0],ORIGINAL_ROWS[1]).read_bytes());assert O['passed']is True and O['corroboration']['rows_corroborated']==846
 rows=json.loads(pin(O['output']['path'],O['output']['sha256']).read_bytes());assert len(rows)==846
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True and N['paired_export_readers_closed']is True
 orig={(r['sequence'],r['phase']):r for r in rows}
 def entries(meta):return(meta[1]-meta[0])//4
 results={};mismatch=[]
 for lv in('O0','O2'):
  row=next(e for e in N['paired_exports']if e['branch']==lv);i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256'])
  es=D.entries(i,re.compile(r'sequence-[0-5]/phase-\d+-(?:after-registry|after-page-2013491200)\.bin'));assert len(es)==1692,len(es)
  counts=dict(phases=0,entries_equal=0,capacity_equal=0,capacity_zero=0,growth_phase_equal=0,crt_cells_equal=0)
  with p.open('rb')as f:
   def data(k,n):
    z=es[k];assert z['bytes']==n;f.seek(z['offset']);b=f.read(n);assert len(b)==n and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
   for s in range(6):
    prev_begin=None
    for ph in range(141):
     q=struct.unpack('<32Q',data(f'sequence-{s}/phase-{ph}-after-registry.bin',256));page=data(f'sequence-{s}/phase-{ph}-after-page-2013491200.bin',4096)
     assert q[0]==1 and q[1]==1 and q[3]==0,'Bootstrapped, not failed native registry';o=orig[(s,ph)];om=o['source_computed_after_metadata']
     counts['phases']+=1;ne=q[9];native_growth=prev_begin is not None and q[6]!=prev_begin;prev_begin=q[6]
     cells=struct.unpack_from('<2I',page,0x888)
     ok=dict(entries=ne==entries(om)and q[7]-q[6]==om[1]-om[0],capacity=q[8]==om[2],growth=native_growth==o['growth'],crt=cells==(q[7],q[6]))
     counts['entries_equal']+=ok['entries'];counts['capacity_equal']+=ok['capacity'];counts['capacity_zero']+=q[8]==0;counts['growth_phase_equal']+=ok['growth'];counts['crt_cells_equal']+=ok['crt']
     if not all(ok.values()):mismatch.append(dict(level=lv,sequence=s,phase=ph,native_summary=list(q[:16]),original_after_metadata=om,original_growth=o['growth'],native_growth=native_growth,crt_next_begin=list(cells),failed_relations=[k for k,v in ok.items()if not v]))
  assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)],'Whole index/payload unchanged after reads';results[lv]=counts
 rp=out/'native-schedule-relations.json';rp.write_text(json.dumps(dict(counts=results,mismatches=mismatch),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='Measured native141 source6 registry summary schedule against original141 source-derived schedule (entries, growth phases, capacity) and native CRT metadata cells; no backing/vector/unused-tail, alias or paired141 claim',
  counts=results,mismatch_rows=len(mismatch),mismatch_relation_kinds=sorted({k for m in mismatch for k in m['failed_relations']}),output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),
  native_backing_vector_compared=False,capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('counts','mismatch_rows','mismatch_relation_kinds')}))
if __name__=='__main__':main(sys.argv[1])
