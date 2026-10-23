"""Exact additive schema-first/fixedbuilder/bulk predicate derivative."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-controls-terminal-composite/composite-expander-preparation-r2';assert not O.exists();O.mkdir();p=R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v1.py';a=p.read_text();b=a;changes=[]
def sub(x,y):
 global b
 assert b.count(x)==1;b=b.replace(x,y);changes.append(dict(before=x,after=y))
sub("ROLES={", "BUILDER_SHA='1d02e694331cdab180492149c051fe75f5bd2e3baca08015c6849d8d654be063'\nROLES={")
start=b.index(' tables=dict(connection.execute(');end=b.index(" need(connection.execute('SELECT COUNT(*) FROM physical')",start);schema=b[start:end]
sub(schema,' check_schema(connection)\n')
sub('def validate(connection,', 'def check_schema(connection):\n'+schema+'\ndef validate(connection,')
sub("need(str(builder)in d['files'],'Actual builder7 declaration')", "need(d['files'].get(str(builder))==BUILDER_SHA,'Exact physically reviewed immutable builder7 source')")
sub("connection.execute('PRAGMA query_only=ON')\n  def role", "connection.execute('PRAGMA query_only=ON');check_schema(connection)\n  def role")
start=b.index(' raw_counts=collections.Counter()');end=b.index(' return dict(whole_dependency_rows_measured=',start);old=b[start:end]
new=''' # Same exact raw scoped predicates via bulk indexed anti-joins, not10m SQL calls.
 need(connection.execute("SELECT COUNT(*)FROM raw r WHERE NOT EXISTS(SELECT 1 FROM edges e WHERE e.path=r.path AND e.scope=CASE WHEN r.scope='current16'THEN'current16-whole-inventory'ELSE'legacy24-union-declared'END)").fetchone()[0]==0,'Raw belongs to exact own inventory scoped edge')
 need(connection.execute("SELECT COUNT(*)FROM raw r WHERE r.scope='legacy24'AND NOT EXISTS(SELECT 1 FROM edges e WHERE e.path=r.path AND e.scope='legacy-execution-'||r.caseid||'-declared')").fetchone()[0]==0,'Legacy raw belongs to exact producing case inventory')
 raw_counts={}
 for scope,caseid,n in connection.execute('SELECT scope,caseid,COUNT(*)FROM raw GROUP BY scope,caseid ORDER BY scope,caseid'):
  need(type(scope)is str and scope in('current16','legacy24')and type(caseid)is str and type(n)is int and n>0,'Exact raw named scope/type/count')
  expected=current_counts if scope=='current16'else legacy_counts;need(caseid in expected,'Exact rawcase member');raw_counts[(scope,caseid)]=n
 need({k[1]:v for k,v in raw_counts.items()if k[0]=='current16'}==current_counts and{k[1]:v for k,v in raw_counts.items()if k[0]=='legacy24'}==legacy_counts,'All and only exact percase physical raw outputs')
 need(sum(raw_counts.values())==raw_rows,'Whole unique raw membership')
'''
sub(old,new)
sub('scoped_provenance_preserved=True,initializer_credit=0)', 'scoped_provenance_preserved=True,initializer_credit=0,accepted_function_credit=0)')
q=p.with_name('expand_composite_inventory_v2.py');assert not q.exists();ast.parse(b);q.write_text(b);inverse=b
for d in reversed(changes):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
assert inverse==a
controls=R/'tools/m4-controls-terminal-composite/composite_inventory_controls_v1.py';c=controls.read_text();assert c.count('expand_composite_inventory_v1.py')==1;c=c.replace('expand_composite_inventory_v1.py','expand_composite_inventory_v2.py');cp=controls.with_name('composite_inventory_controls_v2.py');assert not cp.exists();ast.parse(c);cp.write_text(c)
files={str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,controls,cp,Path(__file__).resolve(),p.with_name('build_v7.py'))};r=O/'report.json';r.write_text(json.dumps(dict(prepared_only=True,whole_parent_inverse_equal=True,changes=changes,controls_parent_inverse_equal=c.replace('expand_composite_inventory_v2.py','expand_composite_inventory_v1.py')==controls.read_text(),exact_builder7_SHA=files[str(p.with_name('build_v7.py'))],interface='expand(report_path, expected_sha, register, *, register_edge, progress=None)',mandatory_scoped_edge_callback=True,all_rows_actual_bytehash_required=True,production_inventory_opened=False,composer_executed=False,acceptance_checker_changed=False,raw16_expander_changed=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=hashlib.sha256(r.read_bytes()).hexdigest(),helper_sha256=files[str(q)])))
