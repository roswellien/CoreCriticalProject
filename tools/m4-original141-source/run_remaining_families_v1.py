"""ROOT-admitted narrow remaining MFC6/widgets42; ordinary only, no workers."""
from pathlib import Path
import hashlib,json,importlib.util,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,configuration_path,configuration_sha,name):
 ap=Path(admission_path).resolve();need(sha(ap)==admission_sha,'Exact ROOT remaining-family admission');A=json.loads(ap.read_bytes());need(A['passed']is True and A['independent_review']is True and A['scope_identity']=='original141_remaining_families_source'and A['configuration_sha256']==configuration_sha,'No self admission or field fallback')
 admitted={}
 for p,h in A['files'].items():
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Ordinary physical closure only');need(str(p)not in admitted and sha(p)==h,'Whole unique inputs before imports');admitted[str(p)]=h
 admitted[str(ap)]=admission_sha
 out=R/'reports/m4-original141-source'/name;dirs=[out,out.with_name(name+'-MFC'),out.with_name(name+'-widgets')];need(all(not p.exists()for p in dirs),'Exact fresh three output namespaces');out.mkdir();pins={str(ap):admission_sha};reader=None;passed=False;cases=[];stage='input admission'
 def own(p):return any(p.is_relative_to(q.resolve())for q in dirs)
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical byte access');v=sha(p);need(own(p)or admitted.get(str(p))==v,'Whole independently admitted external file, no global fallback');need(h is None or h==v,'Exact field identity');need(str(p)not in pins or pins[str(p)]==v,'Stable input/output dependency');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0;reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:
   need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No archives even through indirect imports')
   if p.is_relative_to(R)or str(p)in admitted:need(own(p)or str(p)in admitted,'Every project read belongs to pre-import ROOT closure')
 try:
  pin(__file__);C=read(configuration_path,configuration_sha);need(C['schema']=='mw34-original141-source-input-contract-v1'and configuration_sha=='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0','Exact unchanged current input configuration')
  sys.addaudithook(audit);V=read(C['validation']['path'],C['validation']['sha256']);need(V['passed']and V['reader_closed']and C['validation']['sha256']=='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c','Same genuine current strict3')
  stage='MFC6';M=load(R/'tools/m4-original141-source/mfc_source141_v1.py','remaining_current_MFC');M.main(name+'-MFC',C,pin);p=dirs[1]/'report.json';g=read(p);need(g['passed']and g['source_case_extent']==6 and g['original_validation_sha256']==C['validation']['sha256']and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False,'All current6 literal MFC cases, no reader/source waiver')
  for dep,h in g['files'].items():pin(dep,h)
  cases.append(dict(domain='new_MFC',path=str(p),receipt=str(p),sha256=sha(p),source_case_extent=6))
  stage='widget42';E=load(R/'tools/m4-startup138-original/export_reader_r2.py','remaining_current_export');reader=E.ExportReader(C['validation']['path'],C['validation']['sha256'],'original',pin);W=load(R/'tools/m4-original141-source/widget_source141_v3.py','remaining_current_widget');W.main(name+'-widgets',reader,C,pin);p=dirs[2]/'report.json';g=read(p);need(g['passed']and g['source_case_extent']==42 and g['original_validation_sha256']==C['validation']['sha256']and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False,'All current42 literal widget cases, no old source result substitution')
  for dep,h in g['files'].items():pin(dep,h)
  cases.append(dict(domain='widget',path=str(p),receipt=str(p),sha256=sha(p),source_case_extent=42));passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader:reader.close();reader.entries.clear();reader.bundles.clear()
  for dep,h in pins.items():need(sha(dep)==h,'Final whole source/code input conservation')
  p=out/'report.json';p.write_text(json.dumps(dict(passed=passed,frontier=stage,configuration_sha256=configuration_sha,original_validation_sha256=C['validation']['sha256']if'C'in locals()else None,cases=cases,reader_closed=reader is None or reader.closed,canonical_reader_opened=False,native_worker_launched=False,source_AFTER_seed=False,initializer_credit=0,complete_original141_combined_gate=False,scope='Only remaining current genuine MFC6/widget42 source families, closed own ordinary export. Reuse of three previous positive families and complete combined source gate require separate ROOT admission.',files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),passed=passed)))
if __name__=='__main__':main(*sys.argv[1:])
