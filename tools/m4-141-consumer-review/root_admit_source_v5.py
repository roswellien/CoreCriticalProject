"""Admit exact source-derived74-record chronology, retaining source6/FS proof."""
from pathlib import Path
import ast,json,hashlib,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-141-consumer-review/root-source-admission-r5';assert not out.exists();out.mkdir();pins={};checks=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,h in d.get('files',{}).items():pin(p,h)
 return d
try:
 receipt('reports/m4-141-consumer-review/root-source-admission-r4/report.json','0786193d656f797fbdf2af4bd35232cc3a62780791333222bfb88de2d71058ab')
 prep=receipt('reports/m4-startup141-source/preparation-r7/report.json','241ee09591bb014be6f1654de47ec26ffb414ddf6750c356645d9e68a6028f7f')
 review=receipt('reports/m4-141-consumer-review/MFC-chronology-preparation-r1/report.json','9cd9fcadd51379a16f984f236bc94722ba5f69fa0f1afab8f208823341da6804')
 receipt('reports/m4-141-consumer-review/root-FS-domain-controls-r4/report.json','a2455541b9d1afadce0e9ef18db935895e45d0dd914b45a564437d557b22a33b')
 driver=pin(prep['entrypoint']).read_text();delta=json.loads(pin(Path(prep['entrypoint']).parent/'driver-deltas.json').read_bytes());assert len(delta)==28
 for row in reversed(delta):assert driver.count(row['new'])==row['count'];driver=driver.replace(row['new'],row['old'])
 assert driver==pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py','093dbb3ddac7cab868058c45f6b7a14280a8a2a49ee33b06d5d931345b79e0d2').read_text()
 observer=pin(prep['observer'],'b1cd795699c2b81098eab35b1f6c9f3f30d8b29853efe02b0b542ab80ac741a0').read_text();ast.parse(observer)
 rows=json.loads(pin(R/'reports/m4-141-consumer-review/MFC-chronology-preparation-r1/observer-deltas.json').read_bytes());assert len(rows)==6
 for row in reversed(rows):assert observer.count(row['new'])==row.get('count',1);observer=observer.replace(row['new'],row['old'])
 assert observer==pin(R/'tools/m4-native141-source/final_observer141_v9.py').read_text()
 helper=pin(R/'tools/m4-native141-source/mfc_chronology141_v1.py','ac153f9d73532c52496ab50a7ff590f34a9e6e3b35950b24e84873f8ba1527de');ast.parse(helper.read_text())
 checks.append('Exact source6 driver inverse and six observer9 inverses; only source-event positive823 chronology/whole74 ledgers added')
 # Same named current native producer defines index as record count at entry,
 # and imports take its preceding count. Constructor root0 remains distinct
 # from the separately proved component root/site/mirror ownership journal.
 producer=pin(R/'reports/m4-startup141-runway/service-preparation-r2/mfc_operations.inc').read_text()
 assert 'record.words={1,mfc_records_.size(),registry_root_,target,site,frame,'in producer
 assert 'mfc_imports_.push_back({1,mfc_records_.size(),registry_root_'in producer
 checks.append('Native producer chronology and separate68+6 source domains, raw inputs/frames/owner birth/RET/free all preserved; no ordinal offset or captured-source seed')
 source=pin(R/'tools/m4-141-consumer-review/MFC_chronology_controls_v2.py','7b78e937f72016093291cc1fae05b8dd120746b0c0357897b241b0067ab508b7')
 code=source.read_text();a="MFC-chronology-controls-r2";b="root-MFC-chronology-controls-r1";assert code.count(a)==1;code=code.replace(a,b)
 q=out/'controls.py';q.write_text(code);pin(q)
 ns={'__name__':'root_chronology_controls','__file__':str(source)};exec(compile(code,str(q),'exec'),ns);ns['run']()
 c=receipt('reports/m4-141-consumer-review/root-MFC-chronology-controls-r1/report.json',None);assert c['controls']==74 and c['helper_sha256']==sha(helper)
 checks.append('Fresh74 dynamic interleaving/whole32-word/production union/import/store/ordinal controls passed')
 for p,h in tuple(pins.items()):assert sha(p)==h
 pin(__file__);passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,source_consumer_admitted=passed,source_consumer_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
