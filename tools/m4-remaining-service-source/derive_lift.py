from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
parent=R/'tools/m4-widget-source/lift.py';prep=R/'reports/m4-remaining-service-source/preparation-r1/report.json'
v=json.loads(prep.read_text());need=lambda x,m:(_ for _ in()).throw(ValueError(m))if not x else None
need(v['passed'],'Frozen preparation');s=parent.read_text();old="need(not g['unresolved_controls'] or (entry==0x5ac210 and {u['pc']for u in g['unresolved_controls']}=={0x5ac24b}), 'Only retained reverse-destructor callback frontier; no admission');"
replacement="""expected={row['pc'] for row in json.loads((REC/'report.json').read_bytes())['priority_new_unresolved_controls'] if row['entry']==entry};need({u['pc']for u in g['unresolved_controls']}==expected,'Only physically retained current unresolved controls; compilation grants no target or owner admission');"""
need(s.count(old)==1,'Exact parent frontier guard')
s=s.replace(old,replacement).replace("ROOT/'reports/m4-widget-source/lift-preparation-r1'","ROOT/'reports/m4-remaining-service-source/preparation-r1'").replace("ROOT/'reports/m4-widget-source'/name","ROOT/'reports/m4-remaining-service-source'/name").replace('b1778f7359075bae0c6c2afa0f5745b864b481f2e762dce64b385bb16c9a01dd',hashlib.sha256(prep.read_bytes()).hexdigest()).replace('Widget exact literal source compilation; no execution or admission.','Remaining priority3MFC+2font exact literal source compilation; no execution or admission.')
s=s.replace("pin(REC/'report.json',REC_SHA);graphs=", "pin(ROOT/'tools/m4-widget-source/lift.py');pin(ROOT/'tools/m4-remaining-service-source/derive_lift.py');pin(REC/'report.json',REC_SHA);graphs=")
out=T/'lift.py';need(not out.exists(),'Fresh compiler derivative');out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
