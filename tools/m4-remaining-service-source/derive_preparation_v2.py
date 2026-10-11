from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent;B=R/'reports/m4-remaining-service-source';old=B/'preparation-r1';out=B/'preparation-r2'
if out.exists():raise ValueError('Fresh deferred recursive frontier')
v=json.loads((old/'report.json').read_text());assert v['passed'];new=json.loads((old/'game-new-graphs.json').read_text());recursive=new.pop(str(0x56fea0));assert any(x['site']==0x56ff31 and x['target']==0x56fea0 for x in recursive['direct_calls'])
out.mkdir();pins=dict(v['files'])
def pin(p):pins[str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in old.glob('*.json'):
 if p.name=='report.json':continue
 data=json.loads(p.read_text())
 if p.name=='game-new-graphs.json':data=new
 (out/p.name).write_text(json.dumps(data,indent=2)+'\n');pin(out/p.name)
f=out/'deferred-recursive-source.json';f.write_text(json.dumps(dict(entry=0x56fea0,physical_graph=recursive,failed_compiler_evidence=str(B/'lifts-r1/failure.txt'),failed_source_lift_flags=str(B/'lifts-r1/f_56fea0-lift.flags'),reason='Current SimpleTraceManager always returns null for primary entry; recursive source CALL56FF31 revisits that entry and bounded120s Remill lift timed out. No source bytes altered or numerical/API result supplied.',Runtime_dispatch_admitted=False,cold_path_not_observed=True,required_genuine_current_inputs=[0x72c2cc,0x72c508],remaining_obligation='Prove normal branch exclusion from genuine current BEFORE and source; if reached, repair/review independent recursive lifter then execute source accurately.'),indent=2)+'\n');pin(f)
for p in [old/'report.json',T/'derive_preparation_v2.py',B/'lifts-r1/failure.txt',B/'lifts-r1/f_56fea0-lift.flags']:pin(p)
v['files']=pins;v['counts']['priority_new_literal_bodies']=29;v['counts']['explicit_uncompiled_recursive_frontiers']=1;v['new_entries']=sorted(map(int,new));v['parent_preparation_sha256']=hashlib.sha256((old/'report.json').read_bytes()).hexdigest();v['scope']+='; additive29-body usable corpus, full physical recursive56FEA0 retained explicitly uncompiled/unadmitted';(out/'report.json').write_text(json.dumps(v,indent=2)+'\n');digest=hashlib.sha256((out/'report.json').read_bytes()).hexdigest()
s=(T/'lift.py').read_text().replace("ROOT/'reports/m4-remaining-service-source/preparation-r1'","ROOT/'reports/m4-remaining-service-source/preparation-r2'").replace(hashlib.sha256((old/'report.json').read_bytes()).hexdigest(),digest);s=s.replace("pin(ROOT/'tools/m4-widget-source/lift.py');", "pin(ROOT/'tools/m4-remaining-service-source/lift.py');pin(ROOT/'tools/m4-remaining-service-source/derive_preparation_v2.py');pin(ROOT/'tools/m4-widget-source/lift.py');");p=T/'lift_v2.py';assert not p.exists();p.write_text(s);print(json.dumps(dict(passed=True,preparation_sha256=digest,compiler_sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
