"""Independent current141 source/link completion and finite builder bindings."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-startup141-runway';O=R/'reports/m4-138-validation-review/full141-prelaunch-r1';files={}
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p);need(p.suffix.lower()not in('.mwb','.zip'),'No capture archive input');v=sha(p);need(h is None or v==h,'Exact combined prelaunch dependency '+str(p));files[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
need(not O.exists(),'Fresh combined prelaunch')
source=read(R/'reports/m4-138-validation-review/full141-source-delta-review-r5/report.json','ad41a14303e37bc6fc4ab1cdf5878ad1adf61d3ee8443409aef5705205f42200')
link=read(R/'reports/m4-138-validation-review/full141-current-link-review-r7/report.json','1c9d4a565e9b932318d4d158f7fd43a220517739caa08a345e3c052a02085874')
need(source['passed']and link['passed']and not source['selected_relation_metadata_correction_pending'],'Independent source and whole current link gates')
p=read(B/'preparation-r2/report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');build=read(B/'build-r2/build.json','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032')
for report in(source,link):
 for q,h in report['files'].items():pin(q,h)
main=pin(B/'preparation-r2/native_main.cpp').read_text();protocol=pin(B/'preparation-r2/joint_protocol.hpp').read_text();registration=pin(B/'preparation-r2/registration_contract.hpp').read_text()
need('sizeof(Native)==159716'in protocol and '1,6,141,846,17,sizeof(Native)'in main and 'phase==141&&r_.calls().size()==144&&r_.translation_count()==142'in main,'Exact actual finite phase/frame/route source geometry')
match=re.search(r'array<unsigned,(\d+)> registration_roots\{([^}]+)\}',registration);old_roots=[int(x,0)for x in match[2].split(',')];need(int(match[1])==len(old_roots)==108 and len(set(old_roots))==108,'All108 inherited registration observation roles retained')
extra={0x4103f0,0x410440,0x459b40};need(not(extra&set(old_roots)),'Three constructor observations distinct from inherited registry observation array')
levels=[]
for level,w in build['workers'].items():
 tree=Path(w['path']).parent;cache=pin(tree/'CMakeCache.txt').read_text();entries={}
 for line in cache.splitlines():
  if line.startswith('MW34_')and'='in line:k,v=line.split('=',1);entries[k.split(':')[0]]=v
 normalize=lambda v:Path(v).resolve().as_posix().casefold()
 objects=entries['MW34_OBJECTS'].split(';');need(len(objects)==410 and list(map(normalize,objects))==list(map(normalize,p['objects'][level])),'Actual410 cache object list exact finite inherited order')
 need(normalize(entries['MW34_CONSTRUCTOR_LIBRARY'])==normalize(p['constructor_libraries'][level])and normalize(entries['MW34_WIDGET_LIBRARY'])==normalize(p['widget_libraries'][level]),'Actual two native component library flags')
 need(normalize(entries['MW34_REGISTRY'])==normalize(B/'service-preparation-r1/registry_library.cpp')and normalize(entries['MW34_REGISTRY_INCLUDE'])==normalize(B/'service-preparation-r1'),'Actual canonical union service compiler source')
 bindings=pin(B/'preparation-r2'/level/'constructor_bindings.inc').read_text();rows=re.findall(r'r_\.register_translation\(\{\{(\d+)\}',bindings);need({int(x)for x in rows}==extra and len(rows)==3 and bindings.count('&constructor_entry')==3 and bindings.count('m4::admitted_image_hash,29,')==3,'Exactly three typed physical constructor29B bindings')
 for child in ('constructor_bindings.inc','constructor_gate.hpp','widget_build_bindings.hpp','registry_build_bindings.hpp'):
  q=str((B/'preparation-r2'/level/child).resolve());need(q in w['compiler_dependencies'],'Actual current compiler consumed typed header '+child)
 levels.append(dict(level=level,worker=str(pin(w['path'],w['sha256'])),worker_sha256=w['sha256'],cache_objects=410,whole_linked_functions=sum(x['level']==level and x.get('linked',True)for x in link['whole_linked_functions']),constructor_routes=3,inherited_registration_roles=108,total_registration_callbacks=111))
for q,h in list(files.items()):need(sha(q)==h,'Combined prelaunch input conservation')
pin(Path(__file__));O.mkdir(parents=True)
d=dict(passed=True,scope='Independent exact current141 preparation source, actual O0/O2 whole link and finite compiler/builder/typed route prelaunch; root must admit any bounded execution separately',preparation_sha256=sha(B/'preparation-r2/report.json'),build_sha256=sha(B/'build-r2/build.json'),source_review_sha256=sha(R/'reports/m4-138-validation-review/full141-source-delta-review-r5/report.json'),link_review_sha256=sha(R/'reports/m4-138-validation-review/full141-current-link-review-r7/report.json'),order_relation_correction_sha256=sha(B/'order-relation-correction-r1/report.json'),levels=levels,source_roots=141,source_sequences=6,phase_records=846,Runtime_translations=142,Runtime_calls_per_sequence=144,source_old_registration_observation_roles=108,typed_constructor_observation_roles=3,registration_callbacks_total=111,FixedNative_bytes=159716,whole_current_source_comparison_pending=True,current_original_pair_pending=True,current_refusal_cleanup_controls_pending=True,closed_O2_fixture_probe_COMDAT_scope=link['counts']['closed_unlinked_constructor_fixture_registry_methods'],archive_reader_opened=False,actual_worker_launches=0,execution_admitted=False,native_executed=False,initializer_credit=0,current141_acceptance=False,files=files)
q=O/'report.json';q.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
