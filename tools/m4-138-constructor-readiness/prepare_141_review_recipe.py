"""Author-provided immutable review inputs; independent reviewer must run checks."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-runway'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 paths={
 'union_service':('reports/m4-startup141-runway/service-preparation-r1/report.json','6edf61e7b56bb178a6b1dbbb5a0b647af4099272cb59a80f3e277267c435aade'),
 'union_service_build':('reports/m4-startup141-runway/service-build-r1/build.json','f822b1d1ec46933486f7abe1d008c45f6d87d7ee7fdd947511aa0b3462a880f5'),
 'full141_preparation':('reports/m4-startup141-runway/preparation-r2/report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c'),
 'full141_build':('reports/m4-startup141-runway/build-r2/build.json','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032'),
 'full141_build_lineage':('reports/m4-startup141-runway/build-lineage-r1/report.json','1c4040d8f285a38fdae979f75314a80f51474959001727c00003de16eb917118'),
 'independent_current138_prelaunch':('reports/m4-tree-review/joint138-prelaunch-r10/report.json','cede59b7c9b77ab98b78da72374938775b3c78ec3e9a737f618bd688873e3325'),
 'independent_constructor37_prelaunch':('reports/m4-138-validation-review/constructor-native37-prelaunch-r3/report.json','0812e8221ce134d74b4d872d379e7af24009679dabf533b0420bd72043c5e3a2')}
 inputs={};receipts={}
 for label,(path,h)in paths.items():
  p=pin(R/path,h);d=read(p,h);assert d['passed'];inputs[label]=dict(path=str(p),sha256=h);receipts[label]=d
 prep=receipts['full141_preparation'];build=receipts['full141_build'];assert build['preparation_sha256']==inputs['full141_preparation']['sha256']
 for p in ['reports/m4-startup141-runway/preparation-r2/full141-source-deltas.json','reports/m4-startup141-runway/preparation-r2/source-relations.json','reports/m4-startup141-runway/preparation-r2/selected-order.json',
 'reports/m4-startup141-runway/service-preparation-r1/service-union-delta.json','reports/m4-startup141-runway/service-preparation-r1/service-union-contract.json']:
  inputs[p.split('/')[-1]]=dict(path=str(pin(R/p)),sha256=sha(R/p))
 for label,worker in build['workers'].items():pin(worker['path'],worker['sha256'])
 for p in ['tools/m4-tree-review/review_joint138_prelaunch_v10.py','tools/m4-tree-review/review_joint138_prelaunch.py','tools/m4-138-validation-review/review_constructor_native37_prelaunch_v7.py','tools/m4-tree-review/amd64_coff.py','tools/m4-138-constructor-readiness/prepare_full141_v2.py','tools/m4-138-constructor-readiness/prepare_union_service.py','tools/m4-138-constructor-readiness/build_full141.py','tools/m4-138-constructor-readiness/build_full141_v2.py']:pin(R/p)
 criteria=[
 dict(id='physical141_order',check='Read only ordinary exact pinned GamePE table5e0000..5e0244; independently decode144nonzero slots. Select exact parent138+constructor3; verify141unique pairs, constructorphase13slot5e0038/4103f0,14slot5e003c/410440,39slot5e00a0/459b40; parent138 relative order identical.'),
 dict(id='18_full_source_inverse',check='Independently inspect all18declared replacements, reverse each onlyonce and recover complete parent138 filesbyte-for-byte. Check addedconstructor_entry exactly successful37fixture6 implementation; noState/FX/private/page/owner reseed. Preserve entirety oldnumeric/SPI/currentMFC/widget/GDI/FPS/formatter/growth/cleanup/caller bodies.'),
 dict(id='canonical_Session_declaration',check='onexit_session.hpp is sole wrapper to actual union/session.hpp; constructor_component.hpp imports samewrapper; current numericSession remains separate namespace. Union Session class semantics match constructor8 wholeclass bytes, allsevennew/oldmethods exactABI; actualcompiler includes resolve thisoneclass definition.'),
 dict(id='union10_callbacks_growth',check='Remove onlyexact3constructorcallbackcase strings from union borrowed-onexitmethod and recover complete current138FPS service3method. Verify7originalcallbacks including40f000→40f030 plus ctor4103f0→410420,410440→410470,459b40→459b70. Preserve wholeHeapSize/HeapReAlloc/full-vector/capacity/generation/cursor/move/allbyte guards. Reverse uniondelta restores constructor8 wholeoutsideadapter; check nooldsubstrate regression.'),
 dict(id='constructor_variants_and_mirrors',check='Retain allconstructor component7 33frozenIRs/readflag/store/getter contracts from admitted37fixture. Three actual29byte Game roots+exactCOFF tags; liveMFC823/825 allocation12/4bytes and genuineNULLfree, readonly getter slotvptr+18 target40a850, actual603fdc/603fe0 bidirectional ownergraph and exactmatchingreceiver. Keep scoped root/priorread storeguard, fullrequested/native/mappedtailmirror, exact12BFS mirror and literal allocator/free-family balancedjournal provenance unchanged.'),
 dict(id='new_observation_coverage',check='Each3constructor entry exports privateaccesses/frames/FS/getters/calls/status/currentcallerhardware via Constructorsprfx; each141phase observes complete5f2000page. SameSessiondump carries constructor-sourcemirror/scope/privateowner records; preserve all oldwidget/GDI/FPS/source/provider/hardware observations and normal fontcleanup beforeregistry finish. Noendpointseeds.'),
 dict(id='old138_finite_IR_equivalence',check='Physically hash same410inheritedCOFFs eachlevel plus actualold58widgetlibrary and allparentadmitted sourceheaders. Verify all138oldtranslation source/COFF/gate/type/linktarget pairs and olddispatch bodies unchanged apart fromadding3constructor bindings. Independently inspect new33constructorIRs/currentcomponent7 library against admitted37 identities.'),
 dict(id='whole_new_full_link',check='Adapt existing independent physical admission helpers to current141targetname. Derive freshcurrentadmissionmap from actualO0/O2main/core/component/libraryCOFFs, not onlyreported parentcounts. Reattribute everyselected current function complete bytes with actualrelocations, everytypedcallback/getter/calltarget/registryroute/thunk/global/TLS/staticlibrarymember, completeASM/unwind and actualcompiler dependencies. Include constructor_entry and allconstructor Component/lib methods; reject missing body or merelyprefix match.'),
 dict(id='builder_objects_and_counts',check='Pin exactbuildchain and410entry CMake cacheperlevel; JSONdecodecachelist equals parent410paths afterslashnormalization. Actual configurecmd links unchanged58widgetlibrary and correct33constructorlibrary, exactunionregistrycpp/include; measure141selectedcalls+3inheritedextra=144routes,142translations,111registrationcallbacks and six846phase domains fromsource/actualbindinginventories. FixedNative159716 and17oldfixedpages unchanged.'),
 dict(id='terminal_prelaunch_scope',check='Write fresh independent review receipt with ownchecker+allactualconsumedphysicalinputs; explicitly noarchive/workerrun/credit. Positive preparation/source/full-link review permits boundednewnative141 observation onlyafterrootconsumesexactreview SHA. Whole141source/original/provider/GDI/paired/refusal/cleanup acceptance remains separately pending.')]
 config=dict(schema='m4-startup141-independent-review-inputs-v1',reviewer='/root/original_validation_review or root',author='/root/controls_audit',inputs=inputs,criteria=criteria,
  proposed_prelaunch_equal=dict(passed=True,preparation_sha256=inputs['full141_preparation']['sha256'],build_sha256=inputs['full141_build']['sha256'],archive_reader_opened=False,actual_worker_launches=0,initializer_credit=0,current141_acceptance=False),
  admission_created=False,execution_admitted=False,worker_launch_arguments_created=False,canonical_reads_authorized=False,
  expected_workers={level:dict(path=v['path'],sha256=v['sha256'])for level,v in build['workers'].items()},
  future_execution_gate='Root must receive genuinely independent successful source+whole currentlink receipt and supply exact path/hash to a separately prepared141controller; thisrecipe is not admission')
 out.mkdir(parents=True);q=out/'independent-review-recipe.json';q.write_text(json.dumps(config,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Author-provided unexecuted exact141independent source/full-link review recipe and physical input configuration only',recipe_path=str(q),recipe_sha256=sha(q),independent_review_performed=False,prelaunch_admission_created=False,execution_admitted=False,worker_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),criteria=len(criteria))))
if __name__=='__main__':main(sys.argv[1])
