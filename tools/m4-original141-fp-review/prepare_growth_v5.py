"""Code-only own-BEFORE realloc-domain derivative; no evaluator invocation."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-original141-fp-review/source-preparation-r2'
assert not O.exists();O.mkdir(parents=True);pins={}
def pin(p):
 p=Path(p).resolve()
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 pins[str(p)]=h;return h
parent=R/'reports/m4-original141-fp-review/source-preparation-r1/widget_source141_v4.py';text=parent.read_text();pin(parent);pin(parent.parent/'report.json')
helper='''"""Predict one DWORD registrar append from entire own BEFORE metadata."""
EXPECTED={(s,138,0x5a3ff0) for s in range(6)}
def predict(meta,backing_bytes):
 if len(meta)!=4:raise ValueError('Complete four-DWORD own metadata')
 begin,next_,capacity,mode=meta
 if any(type(v)is not int or not 0<=v<=0xffffffff for v in meta):raise ValueError('Exact DWORD types/domain')
 if mode!=1 or not begin or begin%4 or next_%4 or not 0<capacity<=1024 or capacity%4 or begin+capacity>0xffffffff or not begin<=next_<=begin+capacity or backing_bytes!=capacity:raise ValueError('Whole owned mode1 registry BEFORE geometry')
 return next_-begin+4>capacity
def domain(rows):
 expected_all={(s,p,r)for s in range(6)for p,r in ((17,0x40e250),(18,0x40ef50),(19,0x40f000),(50,0x479590),(137,0x5a3c30),(138,0x5a3ff0),(139,0x5a66f0))}
 if len(rows)!=42 or {tuple(r['identity'])for r in rows}!=expected_all:raise ValueError('Exact42 own source BEFORE cases once')
 selected={tuple(r['identity'])for r in rows if predict(r['meta'],r['backing_bytes'])}
 if selected!=EXPECTED:raise ValueError('Exact six chronological source overflow cases')
 return selected
'''
hp=O/'registry_growth_v1.py';hp.write_text(helper);pin(hp);changes=[]
def sub(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
sub("        for seq,phase,root in [(s,p,roots[r])for s in range(6)for p,r in schedule]:", "        GROWTH=load(R/'reports/m4-original141-fp-review/source-preparation-r2/registry_growth_v1.py','original141_registry_growth');growth_predictions=[]\n        for gs,gp,gr in [(s,p,r)for s in range(6)for p,r in schedule]:\n            own_meta=u(capture(f'phase/{gs}/{gp}/registry-before-meta.bin'),0,4);own_backing=capture(f'phase/{gs}/{gp}/registry-before-backing.bin');growth_predictions.append(dict(identity=[gs,gp,gr],meta=list(own_meta),backing_bytes=len(own_backing),predicted_growth=GROWTH.predict(own_meta,len(own_backing))))\n        predicted_growth_set=GROWTH.domain(growth_predictions);observed_growth_set=set()\n        for seq,phase,root in [(s,p,roots[r])for s in range(6)for p,r in schedule]:")
sub("registry_capacity=[registry[2]];reallocation_inputs=[]", "registry_capacity=[registry[2]];reallocation_inputs=[];own_growth=GROWTH.predict(registry,len(backing));need(own_growth==((seq,phase,root['entry'])in predicted_growth_set),'Same exact physical BEFORE prediction before source evaluation')")
sub("                        old_begin=u(model.bytes(0x7803788c,4))[0];", "                        need(own_growth and not reallocation_inputs,'One source overflow birth only in predicted case');old_begin=u(model.bytes(0x7803788c,4))[0];")
sub("            actual_registry=u(record,356464,4);", "            need(len(reallocation_inputs)==int(own_growth),'Per-case observed source birth equals own BEFORE overflow prediction')\n            if reallocation_inputs:observed_growth_set.add((seq,phase,root['entry']))\n            actual_registry=u(record,356464,4);")
sub("need(counts['literal_registry_reallocation_births']==12 and counts['literal_complete_registrar_root_endpoints']==42", "need(observed_growth_set==predicted_growth_set==GROWTH.EXPECTED and counts['literal_registry_reallocation_births']==len(predicted_growth_set) and counts['literal_complete_registrar_root_endpoints']==42")
sub("source_registry_reallocation_inputs=reallocation_inputs,FPS_joins", "source_registry_reallocation_inputs=reallocation_inputs,own_registry_BEFORE_growth_prediction=dict(meta=list(registry),backing_bytes=len(backing),predicted_growth=own_growth),FPS_joins")
sub("source_case_extent=42,source_AFTER_seed=False", "source_case_extent=42,registry_growth_prediction_scope='All42 complete own BEFORE registry meta/backing, six exact seq0..5 phase138 overflows; each actual birth matches prediction, physical HeapSize and literal realloc guards unchanged',source_AFTER_seed=False")
cp=O/'widget_source141_v5.py';cp.write_text(text);pin(cp);inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==parent.read_text();compile(text,str(cp),'exec');compile(helper,str(hp),'exec');pin(__file__)
q=O/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Unexecuted code preparation with whole exact inverse and syntax check; no capture/source evaluator',changes=changes,parent=str(parent),parent_sha256=pins[str(parent)],whole_inverse_equal=True,derived_checker=str(cp),helper=str(hp),expected_growth_cases=[[s,138,0x5a3ff0]for s in range(6)],legacy_12_count_not_transferred=True,retained_HeapSize_capacity_literal_realloc_birth_prefix_and_whole_endpoint_guards=True,source_evaluated=False,archive_reader_opened=False,acceptance_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=pin(q))))
