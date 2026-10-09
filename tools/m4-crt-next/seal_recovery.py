"""Seal static dossier and failed attempt as physical bytes; no execution credit."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 base=ROOT/'reports/m4-crt-next';out=base/'closure-r1'
 if out.exists():raise ValueError('Fresh static closure required')
 files={}
 for name,h in json.loads((base/'recovery-r2/pins.json').read_text())['files'].items():
  if sha(name)!=h:raise ValueError('Static recovery exact pin changed')
  files[name]=h
 for folder in (base/'recovery-r1',base/'recovery-r2',ROOT/'tools/m4-crt-next'):
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:files[str(p.resolve())]=sha(p)
 doc=ROOT/'docs/m4-crt-next-plan.md';files[str(doc)]=sha(doc)
 report=json.loads((base/'recovery-r2/report.json').read_text())
 if not report['passed'] or len(report['authored_failure_controls'])!=6 or any(not x['complete_import_free'] for x in report['complete_roots']):raise ValueError('Exact static closure/control contract')
 out.mkdir();result={'passed':True,'scope':'Static next CRT code/data provenance only; no execution, native service or data-import admission','recovery_report':{'path':str(base/'recovery-r2/report.json'),'sha256':sha(base/'recovery-r2/report.json')},'root_instruction_counts':{hex(x['entry']):x['instruction_count'] for x in report['complete_roots']},'authored_graph_failure_controls':6,'failed_first_range_attempt_preserved':True,'physical_bindings_before_report':len(files),'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('Static next CRT closure sealed:',len(files),'physical files')
if __name__=='__main__':main()
