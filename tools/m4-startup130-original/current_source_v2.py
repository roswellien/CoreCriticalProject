"""One current genuine original130 session: formatter4 and six tree cases."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Actual current dependency '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical dependency');PINS[str(p)]=v;return p
def load(p,n):
 s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-startup130-original'/name;need(not out.exists(),'Fresh current source proof');out.mkdir(parents=True);passed=False;reader=None;counts=collections.Counter();cases=[];started=time.perf_counter();format_rows=[];trees=[]
 try:
  current=R/'reports/m4-startup130-original/validation-r2/report.json';validation=read(current,'91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca');need(validation['passed'],'Current genuine original130 run')
  for p in [R/'reports/m4-startup130-original/current-source-preparation-r1/report.json',R/'reports/m4-startup130-original/format-source-preparation-r2/report.json']:
   prep=read(p);need(prep['passed']and not prep['capture_reader_opened'],'Unexecuted additive source preparation')
   for q,h in prep['files'].items():pin(q,h)
  D=load('tools/m4-crt-allocation-root/run_v2.py','one_current_original130_reader');reader=D.DirectSet(validation['original_capture'],pin)
  formatter=load('tools/m4-startup130-original/format_source_v2.py','fresh_original130_formatter4');formatter.PINS=PINS;formatter.main(name+'-formatter4',reader)
  path=R/'reports/m4-startup130-original'/(name+'-formatter4')/'report.json';receipt=read(path);need(receipt['passed'],'Fresh24literalformatterprefixes');counts.update(receipt['counts']);source=path.parent/'source-derivations.json';format_rows=read(source,receipt['files'][str(source.resolve())]);need(len(format_rows)==24,'Allfourroots×sixsequences')
  cases.append(dict(kind='formatter4',receipt=str(path.resolve()),sha256=sha(path)))
  tree=load('tools/m4-startup130-original/tree_source.py','fresh_original130_tree');tree.PINS=PINS;tree.SHARED_READER=reader
  for sequence in range(6):
   case=name+'-tree-'+str(sequence);tree.main(case,R/'tools/m4-tree-source/game_model_v4.py',sequence);path=R/'reports/m4-startup130-original'/case/'report.json';receipt=read(path);need(receipt['passed'],'Current literal treecase');counts.update(receipt['counts']);p=path.parent/'source-derivations.json';derived=read(p,receipt['files'][str(p.resolve())]);trees.append(dict(sequence=sequence,phase=78,source=derived,receipt=str(path.resolve()),sha256=sha(path)));cases.append(dict(kind='tree',sequence=sequence,receipt=str(path.resolve()),sha256=sha(path)));print(json.dumps(dict(tree_sequence=sequence,passed=True)),flush=True)
  need(len(trees)==6 and counts['literal_constructor_prefixes']==24,'Complete current original domains');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear();reader=None
  if 'tree'in locals():tree.SHARED_READER=None
  for label,value in [('original-Formatting-source-derivations.json',format_rows),('original-Tree-source-derivations.json',trees)]:p=out/label;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  pin(__file__)
  report=dict(passed=passed,scope='One current genuine original130 archive session:24literalformatter4 prefixes/six literal tree cases from their own untouched carried BEFORE, actualinitial allocator backing and bounded Win32 API volatile inputs; no native credit',original_validation_path=str(current.resolve())if'current'in locals()else None,original_validation_sha256=sha(current)if'current'in locals()else None,counts=dict(counts),cases=cases,files=PINS,reader_closed=True,archive_sessions_opened=1,elapsed_seconds=time.perf_counter()-started,candidate_AFTER_machine_seed=False,original_postRET_observed=False,original_postRET_source_derived=True,formatter_full_registration_provider_CPU_executed_by_model=False,original_current_CRT_registration_relation='Separate physical callback/pointer/cursor-store relation from complete genuine preceding carried BEFORE and finite true HeapReAlloc scalar if growth occurs; no AFTER input or new unused growth-tail model claim',initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=True,elapsed_seconds=report['elapsed_seconds'],report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
