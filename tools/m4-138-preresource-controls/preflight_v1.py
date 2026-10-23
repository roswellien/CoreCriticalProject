"""Bounded admission inverses and synthetic refusal-domain controls only."""
from pathlib import Path
import json,hashlib,ast,sys,runpy
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'reports/m4-138-preresource-controls/synthetic-preflight-r1';assert not out.exists();pins={}
def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
ready=pin(R/'reports/m4-138-preresource-controls/readiness-r2/report.json');assert sha(ready)=='c8a358beda8a2fdd02aeda33e21aea07cf32f8d9f55b45ae2cbeb6698772df04';r=json.loads(ready.read_bytes());assert r['passed']
for p,h in r['files'].items():assert sha(Path(p))==h;pins[p]=h
p=pin(R/'tools/m4-138-preresource-controls/run_v1.py');s=p.read_text();start=s.index(" assert review['scope_identity']");end=s.index(' for p,h in b[\'files\'].items():',start);code='\n'.join(x[1:]if x.startswith(' ')else x for x in s[start:end].splitlines())
required=('complete_source_inverse','whole_linked_current_context_and_provider_inputs','typed_COFf_CALL_TLS_ownership','whole85byte_boundary_target_and_unwind','exact_real64byte_MFC_entry_frame','current_MFC_and_widget_fault_cleanup','bounded14prefix_no_reseed','complete_private_and_public_retry_inventory');tests=[]
def trial(label,change=None,bad=False):
 review=dict(scope_identity='current138_preresource_legacy12',ordinary_outputs_only=True,modes=list(range(1,13)),levels=['O0','O2'],prelaunch_checks={x:True for x in required},files={str(p):'h'for p in [Path('build'),Path('preparation'),Path('run').resolve()]})
 a=type('Args',(),dict(level='O0',mode=11))()
 if change:change(review,a)
 env=dict(review=review,a=a,bp=Path('build'),pp=Path('preparation'),Path=Path,__file__=str(Path('run').resolve()),sha=lambda p:'h',pin=lambda p:p)
 try:exec(compile(code,'synthetic pre-resource admission','exec'),env)
 except (AssertionError,KeyError):assert bad
 else:assert not bad,'Adverse admitted '+label
 tests.append(dict(label=label,passed=True,adverse=bad))
trial('exact finite12/2 admission including mode11')
trial('existing widget control scope refuses',lambda r,a:r.update(scope_identity='widget8'),True)
trial('missing current cleanup review refuses',lambda r,a:r['prelaunch_checks'].pop('current_MFC_and_widget_fault_cleanup'),True)
trial('false actual-frame review refuses',lambda r,a:r['prelaunch_checks'].update(exact_real64byte_MFC_entry_frame=False),True)
trial('integer success coercion refuses',lambda r,a:r['prelaunch_checks'].update(exact_real64byte_MFC_entry_frame=1),True)
trial('missing mode12 refuses',lambda r,a:r.update(modes=list(range(1,12))),True)
trial('unbounded next-mode refuses',lambda r,a:setattr(a,'mode',13),True)
trial('wrong optimization refuses',lambda r,a:setattr(a,'level','O3'),True)
trial('missing current controller pin refuses',lambda r,a:r['files'].pop(str(Path('run').resolve())),True)
for p in ['run_v2.py','build_v2.py']:
 q=pin(R/'tools/m4-138-preresource-controls'/p);ns=runpy.run_path(str(q),run_name='definition_only');assert callable(ns['main']);ast.parse(q.read_text())
pin(__file__);out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Synthetic admission and immutable definition parsing only, no checker/worker/controller main, no source machine or canonical reader',tests=tests,files=pins),indent=2)+'\n');print(sha(q))
