"""Materialize a source-only derivative; never evaluate source or open captures."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-original141-fp-review/source-preparation-r1'
assert not O.exists();O.mkdir(parents=True)
pins={}
def pin(p):
 p=Path(p).resolve()
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 pins[str(p)]=h;return h
parent=R/'tools/m4-original141-source/widget_source141_v3.py';old=parent.read_text();pin(parent)
audit=R/'reports/m4-original141-fp-review/env-readiness-r1/report.json';pin(audit);a=json.loads(audit.read_text());fact=a['nonconserved_pairs'][0]
validation=R/'reports/m4-original141/root-capture-validation-r3/report.json';vh=pin(validation)
wrapper=R/'reports/m4-original141/source-preparation-r6/widget_observer_x86.asm';wh=pin(wrapper)
helper='''"""One original-only opaque API metadata effect; no AFTER state assignment."""
EXPECTED = %s
VALIDATION_SHA = %r
WRAPPER_SHA = %r
def predict(before,after,own_env,validation_sha,wrapper_sha,seen):
 if validation_sha!=VALIDATION_SHA or wrapper_sha!=WRAPPER_SHA:raise ValueError('Exact current physical validation/wrapper')
 if len(own_env)!=28:raise ValueError('Entire own source ENV28')
 if own_env.hex()!=before['ENV28_hex']:raise ValueError('Source-derived complete BEFORE ENV')
 if before['FX512_hex']!=after['FX512_hex'] or len(bytes.fromhex(before['FX512_hex']))!=512:raise ValueError('Entire FX512 conservation')
 key={k:before[k]for k in ('sequence','phase','root','API','index')}
 if key==EXPECTED['identity']:
  if seen!=0:raise ValueError('Exactly one predeclared event')
  if before['header']!=EXPECTED['before_header'] or after['header']!=EXPECTED['after_header'] or before['CPU']!=EXPECTED['before_CPU'] or after['CPU']!=EXPECTED['after_CPU'] or before['arguments']!=EXPECTED['arguments']:raise ValueError('Whole typed current event/frame/arguments')
  if before['FX512_hex']!=EXPECTED['FX512_hex'] or own_env.hex()!=EXPECTED['before_ENV28_hex']:raise ValueError('Exact finite input domain')
  if before['side']!='entry' or after['side']!='first-source-return' or after['index']!=37:raise ValueError('Exact source API boundary')
  predicted=own_env[:12]+bytes(14)+own_env[26:]
  if predicted.hex()!=after['ENV28_hex']:raise ValueError('All 28 independently computed output bytes')
  return predicted,seen+1,True
 if before['ENV28_hex']!=after['ENV28_hex']:raise ValueError('Whole ENV conservation outside exact event')
 return own_env,seen,False
'''%(repr({k:fact[k]for k in ('identity','before_header','after_header','before_CPU','after_CPU','arguments','FX512_hex','before_ENV28_hex')}),vh,wh)
hp=O/'finite_env_contract_v1.py';hp.write_text(helper);pin(hp)
changes=[]
def replace(before,after):
 global old
 assert old.count(before)==1;old=old.replace(before,after);changes.append(dict(before=before,after=after))
replace("boundaries=sealed('widget-GDI-observations.json');", "ENV_CONTRACT=load(R/'reports/m4-original141-fp-review/source-preparation-r1/finite_env_contract_v1.py','original141_finite_env_contract');env_effect_seen=[0];pin(prepdir/'widget_observer_x86.asm',ENV_CONTRACT.WRAPPER_SHA);need(C['validation']['sha256']==ENV_CONTRACT.VALIDATION_SHA,'Exact finite original-only ENV validation');boundaries=sealed('widget-GDI-observations.json');")
replace("eq(before['FX512_hex'],after['FX512_hex'],'Entire actual GDI FX512 conserved; no FP output transport');eq(before['ENV28_hex'],after['ENV28_hex'],'Entire actual GDI ENV28 conserved; no environment output transport');counts['actual_GDI_whole_FP_conservation_relations']+=1;undefined={}", "eq(before['FX512_hex'],after['FX512_hex'],'Entire actual GDI FX512 conserved; no FP output transport');env[0],env_effect_seen[0],cleared=ENV_CONTRACT.predict(before,after,env[0],C['validation']['sha256'],sha(prepdir/'widget_observer_x86.asm'),env_effect_seen[0]);counts['actual_GDI_whole_FX512_conservation_relations']+=1;counts['original_only_finite_GDI_ENV_metadata_clear_responses'if cleared else'actual_GDI_whole_ENV28_conservation_relations']+=1;undefined={}")
replace("passed=True\n    except BaseException:", "need(env_effect_seen[0]==1 and counts['actual_GDI_whole_FX512_conservation_relations']==894 and counts['actual_GDI_whole_ENV28_conservation_relations']==893 and counts['original_only_finite_GDI_ENV_metadata_clear_responses']==1,'Exact894 FX/893ENV/one finite original-only metadata response');passed=True\n    except BaseException:")
replace("GDI_FP_output_seed=False,unused_API_stack_bytes_seeded=False", "GDI_FP_output_seed=False,original_only_ENV_metadata_projection=True,original_only_ENV_metadata_bytes=14,GDI_ENV_metadata_clear_not_API_body_proof=True,native_ENV_projection_proven=False,paired_ENV_projection_proven=False,unused_API_stack_bytes_seeded=False")
replace("scope='Current141 six-sequence", "scope='Original-only one finite opaque GDI metadata-clear response with entire own-before-derived ENV28 output comparison; no native API body or paired projection proof. Current141 six-sequence")
cp=O/'widget_source141_v4.py';cp.write_text(old);pin(cp)
inverse=old
for d in reversed(changes):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
assert inverse==parent.read_text()
compile(old,str(cp),'exec');compile(helper,str(hp),'exec')
pin(__file__)
report=dict(passed=True,scope='Code-only immutable preparation with exact whole parent inverse and syntax checks; source evaluator not executed',parent=str(parent),parent_sha256=pins[str(parent)],changes=changes,whole_inverse_equal=True,source_contract=str(hp),derived_checker=str(cp),predeclared_event=fact['identity'],validation_sha256=vh,wrapper_sha256=wh,required_counts=dict(FX512=894,ENV28_conserved=893,original_only_metadata_clear=1),remaining_native_paired_policy_required=True,reader_opened=False,source_evaluated=False,accepted_credit=0,files=pins)
q=O/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=pin(q))))
