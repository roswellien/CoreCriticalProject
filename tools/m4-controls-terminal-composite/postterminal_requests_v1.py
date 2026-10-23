"""Post-review request builders for prepare_postterminal_templates_v1 (UNEXECUTED
until an actual composite reviewer PASS and ROOT field review exist).

Subcommands (each writes one fresh JSON under reports/m4-controls-terminal-composite/<name>/):
  final45-request REVIEWER_REPORT REVIEWER_SHA FIELD_REVIEW FIELD_REVIEW_SHA NAME
  all39-review    REVIEWER_REPORT REVIEWER_SHA FINALIZED841 FINALIZED841_SHA NAME
  bindings-request FINALIZED841 FINALIZED841_SHA ALL39_REVIEW ALL39_REVIEW_SHA NAME

Gate identities (39): 29 retained gates from root-criterion-delta-proposal-r6
candidate-33-gate-bindings, the four composite controls gates (terminal-composite-r1
preparation/prelaunch/controls plus the independent reviewer receipt), two retained
source gates identified by exact measured content in
root-inherited-source-field-measurements-r1, and six additional gates whose exact
acceptance constraints were checked (counts, closed readers, required edges).
Every path is freshly hashed at run time; nothing here creates allowances,
configuration or acceptance.
"""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE='reports/m4-controls-terminal-composite'
TERMINAL=BASE+'/terminal-composite-r1'
CANDIDATE33=('reports/m4-138-controls-review/root-criterion-delta-proposal-r6/candidate-33-gate-bindings.json',None)
RETAINED_SOURCE={'source_legacy_flags':'reports/m4-joint-startup131-source/legacy-flags-r4/report.json','source_preflight':'reports/m4-tree-review/joint131-source-preflight-r4/report.json'}
ADDITIONAL={'controls_full_raw':'reports/m4-138-controls-review/full-raw-inventory-review-r1/report.json','controls_gdi_owners':'reports/m4-138-controls-review/gdi-owners-r1/report.json','controls_current_link':'reports/m4-138-controls-review/current-link-join-r1/report.json',
 'source_widget_journal_review':'reports/m4-138-controls-review/source6-widget-journal-physical-r2/report.json','source_widget_memory_review':'reports/m4-138-controls-review/source6-widget-memory-physical-r2/report.json','source_widget_semantic_review':'reports/m4-138-controls-review/source138-widget-independent-r1/report.json'}
PROPOSAL6=('reports/m4-138-controls-review/root-criterion-delta-proposal-r6/report.json','626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505')
PROPOSAL841=('reports/m4-138-controls-review/root-criterion-delta-proposal-r6/criterion-841-proposal.json','c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4')
MAPPING45=('reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1/pending45-terminal-field-mapping.json','79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def row(rel,h=None):
 p=(R/rel).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);return dict(path=str(p),sha256=v)
def value_at(d,key):
 for k in key.split('.'):d=d[int(k)]if isinstance(d,list)else d[k]
 return d
def reviewer_pass(path,h):
 rv=json.loads((R/path).read_bytes())if not Path(path).is_absolute()else json.loads(Path(path).read_bytes());assert sha(path)==h
 assert rv['passed']is True and rv['all_named_composite_domains_independently_reviewed']is True and rv['whole_composite_union_expanded']is True and rv['final_input_conservation']['metadata_only_cache_used']is False,'Actual independent composite reviewer PASS only'
 return rv
def composite_gates(reviewer,reviewer_sha):
 rv=reviewer_pass(reviewer,reviewer_sha)
 gates={k:row(TERMINAL+'/'+leaf)for k,leaf in(('controls_preparation','controls-preparation.json'),('controls_prelaunch','controls-prelaunch.json'),('controls','controls.json'))}
 assert gates['controls']['sha256']==rv['controls_sha256'],'Reviewer bound the actual controls gate'
 gates['controls_review']=dict(path=str(Path(reviewer).resolve()),sha256=reviewer_sha);return gates
def all39(reviewer,reviewer_sha):
 cand=json.loads((R/CANDIDATE33[0]).read_bytes());gates={}
 for label,b in cand.items():
  if b.get('path'):gates[label]=row(b['path'],b['sha256'])
 gates.update(composite_gates(reviewer,reviewer_sha))
 for label,rel in{**RETAINED_SOURCE,**ADDITIONAL}.items():gates[label]=row(rel)
 assert len(gates)==39,sorted(gates);return gates
def out(name,value):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);d=R/BASE/name;assert not d.exists();d.mkdir();q=d/'request.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
def main(cmd,*a):
 if cmd=='final45-request':
  reviewer,reviewer_sha,field,field_sha,name=a;F=json.loads(Path(field).read_bytes());assert sha(field)==field_sha and F['passed']is True and F['fields_reviewed']==45
  out(name,dict(schema='mw34-root-postterminal-final45-request-v1',proposal6=row(*PROPOSAL6),proposal841=row(*PROPOSAL841),mapping45=row(*MAPPING45),ROOT_field_review=dict(path=str(Path(field).resolve()),sha256=field_sha),actual_composite_gates=composite_gates(reviewer,reviewer_sha)))
 elif cmd=='all39-review':
  reviewer,reviewer_sha,final841,final_sha,name=a;assert sha(final841)==final_sha;rows=json.loads(Path(final841).read_bytes());assert len(rows)==841
  gates=all39(reviewer,reviewer_sha);measured={}
  for label,g in gates.items():
   report=json.loads(Path(g['path']).read_bytes()) if label!='controls'else json.loads(Path(g['path']).read_bytes())
   assert report.get('passed')is True,'Passed actual gate '+label;fields={}
   for r in rows:
    if r['gate']==label:fields[r['current_field']]=value_at(report,r['current_field'])
   measured[label]=dict(path=g['path'],sha256=g['sha256'],fields=fields)
  assert set(r['gate']for r in rows)<=set(gates)
  out(name,dict(passed=True,independent_review=True,gates_reviewed=39,baseline_predicates_reviewed=841,gates={k:dict(path=v['path'],sha256=v['sha256'])for k,v in gates.items()},measured_gate_fields=measured,method='Every finalized row current_field read from the actual freshly hashed gate report; gates must report passed=true',allowance_created=False,configuration_created=False,accepted_function_credit=0))
 elif cmd=='bindings-request':
  final841,final_sha,review,review_sha,name=a;assert sha(final841)==final_sha and sha(review)==review_sha;G=json.loads(Path(review).read_bytes())
  for g in G['gates'].values():assert sha(g['path'])==g['sha256'],g['path']
  out(name,dict(schema='mw34-root-postterminal-bindings-request-v1',proposal841=row(*PROPOSAL841),finalized841=dict(path=str(Path(final841).resolve()),sha256=final_sha),ROOT_all39_review=dict(path=str(Path(review).resolve()),sha256=review_sha),gates={k:dict(path=v['path'],sha256=v['sha256'])for k,v in G['gates'].items()}))
 else:raise SystemExit('final45-request | all39-review | bindings-request')
if __name__=='__main__':main(*sys.argv[1:])
