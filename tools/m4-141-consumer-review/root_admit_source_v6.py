"""Independently admit the exact real owner-schema correction; no archive read."""
from pathlib import Path
import ast,hashlib,json,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-141-consumer-review/root-source-admission-r6';assert not out.exists();out.mkdir();pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,v in d.get('files',{}).items():pin(p,v)
 return d
try:
 receipt('reports/m4-141-consumer-review/root-source-admission-r5/report.json','1adc2abd3c4d1c195a7c30ed444cdf1a7d2df11d8861939700c9ae5c228a0bc3')
 prep=receipt('reports/m4-startup141-source/preparation-r8/report.json','01a6415bf94b2860d4986bfb2eeff160c23586c81cf37451cd53605173e2e58d')
 receipt('reports/m4-141-consumer-review/MFC-chronology-preparation-r2/report.json','1c729740e4f848dae6da3764cfc38e72cd5e33de563e87e94c9a2ce5b1ed53e6')
 helper=pin(prep['helper']);s=helper.read_text();parent=pin(R/'tools/m4-native141-source/mfc_chronology141_v1.py').read_text()
 assert parent.count("owner['acquired']")==1 and s==parent.replace("owner['acquired']","owner['native']")
 actual=json.loads(pin(R/'reports/m4-startup141-source/combined-source-provider-r3/Formatting-source-derivations.json').read_bytes())[-1]['mixed_owners'][0]
 keys={n.slice.value for n in ast.walk(ast.parse(s))if isinstance(n,ast.Subscript)and isinstance(n.value,ast.Name)and n.value.id=='owner'and isinstance(n.slice,ast.Constant)}
 assert keys=={'guest','native','generation','extent','kind','requested','live'} and keys<=set(actual)and 'acquired'not in actual
 real=pin(R/'tools/m4-native141-source/persistent_constructors_v4.py').read_text();assert "native="in real and "generation="in real
 checks.append('Exact one-expression helper inverse; every owner key matches retained real ActualResponses owner schema')
 obs=pin(prep['observer']).read_text();rows=json.loads(pin(R/'reports/m4-141-consumer-review/MFC-chronology-preparation-r2/observer-deltas.json').read_bytes());assert len(rows)==2
 for row in reversed(rows):assert obs.count(row['new'])==row['count'];obs=obs.replace(row['new'],row['old'])
 assert obs==pin(R/'tools/m4-native141-source/final_observer141_v10.py').read_text()
 driver=pin(prep['entrypoint']).read_text();rows=json.loads(pin(Path(prep['entrypoint']).parent/'driver-deltas.json').read_bytes());assert len(rows)==28
 for row in reversed(rows):assert driver.count(row['new'])==row['count'];driver=driver.replace(row['new'],row['old'])
 assert driver==pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').read_text()
 checks.append('Entire observer11 inverse to admitted observer10 and all28 source6 driver inverse retained')
 source=pin(R/'tools/m4-141-consumer-review/MFC_chronology_controls_v3.py');code=source.read_text();assert code.count('MFC-chronology-controls-r3')==1;code=code.replace('MFC-chronology-controls-r3','root-MFC-chronology-controls-r2');q=out/'controls.py';q.write_text(code);pin(q)
 ns={'__name__':'root_chronology_controls','__file__':str(source)};exec(compile(code,str(q),'exec'),ns);ns['run']()
 c=receipt('reports/m4-141-consumer-review/root-MFC-chronology-controls-r2/report.json',None);assert c['controls']==74 and c['helper_sha256']==sha(helper)and set(c['actual_owner_keys'])==set(actual)
 checks.append('Fresh74 real-shaped synthetic chronology/whole32Q/interleaving/import/store adverses; runtime equivalence still untested')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,source_consumer_admitted=passed,source_consumer_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))));raise SystemExit(0 if passed else 1)
