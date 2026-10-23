"""Independent full141 physical source inversion; full-link gate separate."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-startup141-runway';O=R/'reports/m4-138-validation-review/full141-source-delta-review-r1'
files={};counts=collections.Counter()
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p);need(p.suffix.lower()not in('.mwb','.zip'),'No archives');v=sha(p);need(h is None or v==h,'Physical identity '+str(p));files[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
need(not O.exists(),'Fresh review namespace')
recipe=read(B/'review-recipe-r1/independent-review-recipe.json')
for x in recipe['inputs'].values():pin(x['path'],x['sha256'])
p=read(B/'preparation-r2/report.json');u=read(B/'service-preparation-r1/report.json')
delta=read(B/'preparation-r2/full141-source-deltas.json');rels=read(B/'preparation-r2/source-relations.json')
need(len(delta)==18,'Exactly eighteen finite source replacements')
group=collections.defaultdict(list)
for x in delta:group[x['file']].append(x)
for x in rels:
 a=pin(x['parent'],x['sha256_parent']);b=pin(x['child'],x['sha256_child']);s=b.read_text()
 for change in reversed(group.get(b.name,[])):
  need(change['occurrences']==1 and s.count(change['after'])==1,'Unique reviewed inverse '+b.name);s=s.replace(change['after'],change['before'],1);counts['exact_source_inverse_changes']+=1
 need(s==a.read_text(),'Whole inherited138 source restored '+b.name);counts['whole_source_parent_relations']+=1
need(counts['exact_source_inverse_changes']==18,'All declared replacements applied')
ud=read(B/'service-preparation-r1/service-union-delta.json');uc=read(B/'service-preparation-r1/service-union-contract.json')
for x in u['source_relations']:
 a=pin(x['parent'],x['parent_sha256']);b=pin(x['child'],x['child_sha256']);s=b.read_text()
 if b.name==ud['file']:
  need(s.count(ud['union_after'])==1,'Exact whole union adapter body');s=s.replace(ud['union_after'],ud['constructor_before'],1)
  need(s.count(ud['comment_after'])==1,'Exact comment delta');s=s.replace(ud['comment_after'],ud['comment_before'],1);counts['union_adapter_inverse']+=1
 need(s==a.read_text(),'Whole constructor8 service retained '+b.name);counts['whole_constructor_service_relations']+=1
growth=ud['union_after'];cases=ud['constructor_callback_case_addition'];need(growth.count(cases)==1 and growth.replace(cases,'',1)==ud['current138_growth_baseline'],'Whole current138 growth method exact except three callback cases')
need(len(uc['callbacks'])==10 and len({x['root']for x in uc['callbacks']})==10,'Ten distinct literal callback routes')
for x in uc['callbacks']:need(('case '+hex(x['root'])+':callback='+hex(x['callback'])+';break;')in growth,'Exact source callback '+hex(x['root']))
sp=importlib.util.spec_from_file_location('full141_physical_game',pin(R/'tools/analysis/pe.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
game=m.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
physical=[dict(slot=slot,entry=struct.unpack('<I',game.read_va(slot,4))[0])for slot in range(0x5e0000,0x5e0244,4)if struct.unpack('<I',game.read_va(slot,4))[0]]
need(len(physical)==144,'Exactly144 physical nonzero initializer entries')
selected=p['selected_order'];need(len(selected)==141 and len({x['slot']for x in selected})==141 and selected==sorted(selected,key=lambda x:x['slot'])and all(x in physical for x in selected),'Physical141 selected order')
parent=read(p['parent_preparation'],p['parent_preparation_sha256']);roots={0x4103f0,0x410440,0x459b40}
need([x for x in selected if x['entry']not in roots]==parent['selected_order'],'Complete138 relative source order retained')
for phase,slot,entry in[(13,0x5e0038,0x4103f0),(14,0x5e003c,0x410440),(39,0x5e00a0,0x459b40)]:need(selected[phase]==dict(slot=slot,entry=entry),'Physical constructor141 phase/slot')
main=pin(B/'preparation-r2/native_main.cpp').read_text();wrapper=pin(B/'preparation-r2/onexit_session.hpp').read_text();header=pin(B/'preparation-r2/constructor_component.hpp').read_text()
need(wrapper=='#pragma once\n#include "'+(B/'service-preparation-r1/session.hpp').as_posix()+'"\n','Canonical actual union Session wrapper')
need('#include "onexit_session.hpp"'in header,'Same constructor Session declaration')
for token in ('std::unique_ptr<cc::Component>constructor_component_','cc::HostBoundary hardware','constructor_component_->borrow_entry(r.cpu().eip,hardware)','sync_fx(r,c->s_)','Constructors/','0x5f2000'):
 need(token in main,'Current source observation '+token)
for level in('O0','O2'):
 need(p['objects'][level]==parent['objects'][level]and len(p['objects'][level])==410,'Exact410 inherited COFF path inventory')
 for q in p['objects'][level]:pin(q);counts['whole_inherited_COFF_objects']+=1
 for lib in (p['widget_libraries'][level],p['constructor_libraries'][level]):
  if isinstance(lib,str):pin(lib)
  else:pin(lib['path'],lib['sha256'])
counts['physical_selected_initializer_slots']=141
for q,h in list(files.items()):need(sha(q)==h,'Whole reviewer input conservation')
pin(Path(__file__));O.mkdir(parents=True)
d=dict(passed=True,scope='Independent physical order, eighteen full source inverses, exact union growth/service ancestry and inherited COFF inventory only',preparation_sha256=sha(B/'preparation-r2/report.json'),build_sha256=sha(B/'build-r2/build.json'),counts=dict(counts),whole_current_link_review_pending=True,execution_admitted=False,actual_worker_launches=0,archive_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,current141_acceptance=False,files=files)
q=O/'report.json';q.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
