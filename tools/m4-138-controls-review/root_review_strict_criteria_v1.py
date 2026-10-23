"""Independent root machinery review; actual39-gate configuration unadmitted."""
from pathlib import Path
import ast,hashlib,json,importlib.util,copy,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/acceptance138-strict-root-review-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-138-controls-review/acceptance138-strict-criteria-preparation-r1/report.json','7b4a8097397bc3ba5e3734eb5b2ef36e0b53c436904a1aa35cbd2c229d7cd7cd');prep=json.loads(pp.read_bytes());assert prep['passed']and prep['checker_source_inverse']and prep['configuration_source_inverse']
 for p,h in prep['files'].items():pin(p,h)
 baseline=json.loads(pin(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7').read_bytes());required=set(baseline['gates']);assert len(required)==33
 p=pin(T/'acceptance138_criteria_v1.py','4fa464674bd2f0b5d1558fc6e1fbe8e847d3d12267689280f6e1e73f60326b86');s=importlib.util.spec_from_file_location('root_criteria',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 config=dict(gates=copy.deepcopy(baseline['gates']),baseline_criteria={l:{f:m.relation(f,v,v)for f,v in g['equal'].items()}for l,g in baseline['gates'].items()});assert m.validate(config,baseline,required)=={};count=sum(len(g['equal'])for g in baseline['gates'].values());assert count==841
 controls=[]
 def reject(label,fn):
  try:fn()
  except (ValueError,KeyError,TypeError):controls.append(label);return
  raise AssertionError(label)
 for label,gate in baseline['gates'].items():
  for field,expected in gate['equal'].items():
   if field=='passed':continue
   q=copy.deepcopy(config);q['baseline_criteria'][label][field]['current_field']='passed';q['baseline_criteria'][label][field]['current_expected']=True;reject(label+'.'+field+':success-collapse',lambda q=q:m.validate(q,baseline,required))
 assert len(controls)==808
 checker=pin(T/'acceptance138_v3.py').read_text();tree=ast.parse(checker);assigns={t.id:ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)for t in n.targets if isinstance(t,ast.Name)and t.id=='ADDITIONAL'}
 assert len(assigns['ADDITIONAL'])==6 and not required&assigns['ADDITIONAL'];assert "criteria.review_allowances(review,deltas)"in checker and "Path(criteria.__file__),configuration"in checker
 assert checker.index('criteria.review_allowances(review,deltas)')<checker.index("for label,gate in config['gates'].items()")
 assert "for key in ('ROOT','PARENT_SHA','PINS','need','typed_equal','read','register','sha','has','Path','re','normalized')"in checker
 for p,h in pins.items():assert sha(p)==h
 pin(__file__);pin(sys.executable);out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_machinery_review=True,scope='Root-reviewed strict criterion retention, scoped evidence and mandatory fullbyte union machinery only; actual bindings and finite delta allowances still unreviewed',baseline_gates=33,baseline_predicates=841,mandatory_current_gates=39,independent_success_collapse_refusals=len(controls),actual_configuration_reviewed=False,actual_finite_deltas_allowed=False,acceptance_executed=False,physical_union_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
