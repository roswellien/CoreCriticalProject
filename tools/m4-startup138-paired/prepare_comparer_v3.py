"""Immutable concrete current138 comparer scaffold, inverse parent rules retained.

The complete typed-domain policy remains fail-closed before any raw reader.
"""
from pathlib import Path
import ast,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};hunks=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 parent=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43');original=parent.read_text();text=original
 def replace(old,new,label):
  global_dummy=None
  nonlocal text
  positions=[];start=0
  while (i:=text.find(old,start))>=0:positions.append(i);start=i+len(old)
  assert positions,(label,old)
  for position in reversed(positions):text=text[:position]+new+text[position+len(old):]
  hunks.append(dict(old=old,new=new,positions=positions,label=label))
 replace("ROOT=Path(__file__).resolve().parents[2];PINS={}","ROOT=Path(__file__).resolve().parents[3];PINS={}",'Generated report namespace root path only')
 # Physical identity/chronology changes are exact, never a broad path replacement.
 for old,new in [
 ('current131-paired-frozen-gates','current138-paired-frozen-gates'),
 ('e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57','2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6'),
 ('9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f'),
 ('203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801'),
 ('6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'),
 ('1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'),
 ('f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d','da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'),
 ('189e6c9e1cd3bfe910698984b8b97cdf68c2e61b3704f444ba69a187f888aac4','5ca81f7a324e0cd2d712dbc9d80698bb4012d54ee4a26292bfb04fcb8899cf81'),
 ('2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'),
 ('reports/m4-startup131-original/validation-r2','reports/m4-startup138-original/original-validation-r3'),
 ('reports/m4-startup131-original/preparation-r4','reports/m4-startup138-original/preparation-r8'),
 ('reports/m4-startup131-original/build-r3','reports/m4-startup138-original/build-r5'),
 ('reports/m4-startup131-original/execution-r1','reports/m4-startup138-original/original-execution-r2'),
 ('reports/m4-joint-startup131/preparation-r1','reports/m4-joint-startup138/preparation-r4'),
 ("ROOT/'reports/m4-startup131-paired'/name","ROOT/'reports/m4-startup138-paired'/name"),
 ("policy['paired_phases']==1572 and policy['total_source_pages']==46","policy['paired_phases']==1656 and policy['total_source_pages']==69"),
 ("struct.pack('<101I',*expected_callbacks)","struct.pack('<108I',*expected_callbacks)"),
 ("counts['paired_phases']==1572","counts['paired_phases']==1656"),
 ("counts['whole_nonstack_page_relations']==138336","counts['whole_nonstack_page_relations']==221904"),
 ("counts['separate_whole_loader_page_input_relations']==3144","counts['separate_whole_loader_page_input_relations']==3312"),
 ("counts['whole45_nonstack_page_endpoint_relations']==141480","counts['whole45_nonstack_page_endpoint_relations']==225216"),
 ("len(provider_page_rows)==9432","len(provider_page_rows)==9936"),
 ("counts['whole_exact_loaded_input_endpoint_relations']==3144","counts['whole_exact_loaded_input_endpoint_relations']==3312"),
 ("(nr.parent/level/'transport.json').resolve()","Path(next(v for v in execution['levels']if v['level']==level)['capture']).resolve()")]:replace(old,new,'Exact physical current input or finite extent '+old)
 replace('def main(configuration,name):','def main(configuration,name):\n global PAGES','Current physical extra page list scope')
 marker=" policy=json.loads(pin(policy_gate['policy'],policy_gate['policy_sha256']).read_bytes());"
 replace(marker,marker,"Explicit retained policy object")
 marker=" for row in policy['exact_format_IAT_domains']:"
 extra=""" need(policy['current138_complete_typed_domain_admission']is True and policy['allphase_CPU_FX_ENV_lastwriter_admission']is True and policy['widget_whole_raw_endpoint_domain_admission']is True and policy['current_observer_span_domain_admission']is True and policy['current_registry_realloc_fullbacking_domain_admission']is True,'Every current widget and retained scalar/FP/observer/backing relation independently admitted before any export reader')
 PAGES=FIXED_PAGES+tuple(policy['additional_whole_page_addresses']);need(len(PAGES)==len(set(PAGES))==69 and PAGES[:43]==FIXED_PAGES,'Exact physical current69page order')
 WG=load('paired138_literal_widget_relations',ROOT/'tools/m4-startup138-paired/widget_relations_v7.py')
 widget_path,widget_gate,widget_sha=gate('original_widget_source');widget_review_path,widget_review,widget_review_sha=gate('original_widget_source_review')
 need(widget_sha=='4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684'and widget_gate['finite_current42_widget_source_relations_passed'],'Exact complete current own original widget source')
"""+marker
 replace(marker,extra,'Fail-closed complete current relation admission and explicit finite helper')
 marker="roots.update({0x4df610:0x4df680,0x4e0710:0x4e07b0,0x4e0810:0x4e0850,0x4e1ca0:0x4e1ce0});"
 replace(marker,marker+"roots.update(dict(zip(WG.WIDGETS,WG.CALLBACKS)));",'Seven exact extra literal callback registrations retain all parent roots')
 marker="  original_MFC=source_artifact("
 extra="""  original_widgets=source_artifact(widget_path.parent,widget_gate,'source-derivations.json');original_fonts=source_artifact(widget_path.parent,widget_gate,'source-font-generations.json');native_widgets=source_artifact(Path(native_source_report).parent,source_gate,'Widget-source-derivations.json');native_font_cleanup=source_artifact(Path(native_source_report).parent,source_gate,'Widget-manual-native-cleanup.json');need(len(original_widgets)==42 and len(native_widgets)==84 and len(native_font_cleanup)==12,'All current original/native complete widget/cleanup source cases');widget_pairs=[];font_pairs=[]
"""
 replace(marker,extra+marker,'Complete source artifact extents; no failed source receipt admitted')
 marker="    expected_callbacks=[];values={};"
 extra="""    current_widgets=[WG.compare_root(next(r for r in original_widgets if r['sequence']==seq and r['root']==root),next(r for r in native_widgets if r['level']==level and r['sequence']==seq and r['root']==root))for root in WG.WIDGETS];widget_pairs.extend(current_widgets);font_pairs.extend(WG.compare_font_cleanup(original_fonts,current_widgets,next(r for r in native_font_cleanup if r['level']==level and r['sequence']==seq)));widget_field_policy=WG.HandleFieldPolicy()
"""
 replace(marker,extra+marker,'Typed all7 GDI/FS/registrar/birth/font joins per carried sequence')
 marker="      for i,page in enumerate(PAGES):"
 replace(marker,"      if side=='after'and entry in WG.WIDGETS:widget_field_policy.activate(next(r for r in current_widgets if r['root']==entry),phase)\n"+marker,'Literal GDI field lastwriter activation after exact current root source')
 marker="       differences=delta(original,actual);declared=set()"
 replace(marker,marker+";declared.update(widget_field_policy.page(phase,side,page,original,actual))",'Exact source-derived handle four-byte carry, no wildcard')
 # Current source producers share the exact same sealed original logical bytes.
 replace(" need(combined_gate['raw_export_report_sha256']==native_source_sha,'Fresh inherited source uses exact current raw export producer')", " original_export_gate=json.loads(pin(combined_gate['raw_export_report_path'],combined_gate['raw_export_report_sha256']).read_bytes());need(combined_gate['raw_export_report_sha256']=='02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f'and original_export_gate['passed']and original_export_gate['reader_closed'],'Current inherited source uses independently sealed original3 producer');oe=next(r for r in original_export_gate['paired_exports']if r['branch']=='original');se=next(r for r in source_gate['paired_exports']if r['branch']=='original');need(all(oe[k]==se[k]for k in('transport_sha256','index_sha256','payload_sha256','logical_files','payload_bytes'))and Path(oe['transport_path']).resolve()==Path(se['transport_path']).resolve(),'Complete identical original transport/index/payload/geometry shared by independent producers')",'Exact current same-original producer relation replaces obsolete same-report identity')
 replace(" need(pair_review['comparer_preparation_sha256']==pair_prep_sha,'Independent exact current comparer preflight')", " need(pair_review['comparer_preparation_sha256']==pair_prep_sha and pair_review['current138_complete_typed_domain_policy_reviewed']is True,'Independent exact current comparer and complete finite typed-domain policy preflight')",'Independent full current domain review required before raw readers')
 replace(" for row in policy['exact_new_MFC_IAT_domains']:"," for row in policy['exact_widget_FPS_IAT_domains']:IATS[row['cell']]=(row['actual_original_compiled_observer_target'],row['native_physical_raw_pointer32'])\n for row in policy['exact_new_MFC_IAT_domains']:",'Exact current three GDI and one FPS compiled/named import cells')
 replace("ROOT/'reports/m4-vtable-review/observer-compiled-r1/report.json'","ROOT/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json'",'Current physically complete compiled FS/full observer review')
 replace("widget_review_sha=gate('original_widget_source_review')","widget_review_sha=gate('original_widget_source_review');need(widget_review_sha=='6e980830a01cf6a4b04ff4e7abcf6faff78c9c4b478da694a64c671da6f79c46','Exact independent current widget raw/CPU/PC/resource policy review')",'Exact independent current widget policy gate identity')
 replace("  original_widgets=source_artifact(","  CG=load('paired138_current_CRT_page_policy',ROOT/'tools/m4-startup138-paired/crt_page_policy_v2.py');crt_domains=json.loads(pin(policy['CRT_page_source_domains_path'],policy['CRT_page_source_domains_sha256']).read_bytes());need(len(crt_domains)==12,'Complete current two-level six-case source CRT domains')\n  original_widgets=source_artifact(",'Current finite wholeCRT input/carry/registry source policy')
 replace("    current_widgets=[WG.compare_root(","    crt_domain=next(r for r in crt_domains if r['level']==level and r['sequence']==seq);crt_policy=CG.Policy({int(a):bytes.fromhex(b)for a,b in crt_domain['original_inputs'].items()},{int(a):bytes.fromhex(b)for a,b in crt_domain['native_inputs'].items()},crt_domain['patches'],crt_domain['unused_input_offsets']);need(len(crt_domain['registry_fields'])==138,'Every original/native literal pointer publication and carry phase retained')\n    current_widgets=[WG.compare_root(",'Per-case source-derived CRT pointer schedule, no actual AFTER input')
 replace("declared.update(widget_field_policy.page(phase,side,page,original,actual))", "declared.update(widget_field_policy.page(phase,side,page,original,actual));cr=crt_domain['registry_fields'][phase];need(cr['phase']==phase and not cr['AFTER_page_bytes_used_as_input'],'Exact literal source registry phase');declared.update(crt_policy.page(phase,side,page,original,actual,cr[side+'_original'],cr[side+'_native']))",'Exact whole own CRT pages and only literal next/begin or physical observer import identities')
 replace("('MFC-paired-source-relations.json',mfc_pairs)","('Widget-paired-source-relations.json',widget_pairs),('Font-paired-cleanup-relations.json',font_pairs),('MFC-paired-source-relations.json',mfc_pairs)",'Retain all84 source widget and180 same-instance cleanup joins in final evidence')
 inverse=text
 for h in reversed(hunks):
  for position in h['positions']:
   assert inverse[position:position+len(h['new'])]==h['new'];inverse=inverse[:position]+h['old']+inverse[position+len(h['new']):]
 assert inverse==original;ast.parse(text)
 target=out/'paired138.py';target.write_text(text);pin(target)
 for leaf in('mfc_relations_v2.py','tree_relations.py','format_relations.py'):pin(R/'tools/m4-startup131-paired'/leaf)
 for path in('tools/m4-startup138-paired/widget_relations_v7.py','reports/m4-startup138-paired/widget-pair-helper-preflight-r3/report.json','reports/m4-startup138-paired/adaptation-recipe-r3/report.json','reports/m4-startup138-original/original-validation-r3/report.json','reports/m4-startup138-original/widget-complete-source-r1/report.json','reports/m4-138-validation-review/current-widget-policy-review-r1/report.json','reports/m4-tree-review/loaded-input138-original-widget-r1/report.json'):pin(R/path)
 hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=json.loads(pin(R/'reports/m4-startup131-paired/preparation-r1/policy.json').read_bytes());cur=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes())
 policy.update(schema='mw34-paired138-preparation-incomplete-v1',selected_roots=138,paired_phases=1656,original_phases=828,callback_roots=108,total_source_pages=69,native_external_record_pages=52,additional_whole_page_addresses=cur['extra_whole_source_pages'],ordinary_nonstack_pages=67,whole_nonstack_page_relations=221904,separate_whole_loader_page_input_relations=3312,whole45_nonstack_page_endpoint_relations=225216,reconstructed_whole_provider_page_endpoints=9936,current138_complete_typed_domain_admission=False,allphase_CPU_FX_ENV_lastwriter_admission=False,widget_whole_raw_endpoint_domain_admission=False,current_observer_span_domain_admission=False,current_registry_realloc_fullbacking_domain_admission=False)
 # Old finite MFC/formatting domains are retained as parent rules, not current input admission.
 iat_gate=json.loads(pin(R/'reports/m4-startup138-paired/current-IAT-domain-r3/report.json','d84320f8586d025e36f1e4bec9feeac105bec5902fe6daef8f033283b33da204').read_bytes());iat=json.loads(pin(iat_gate['domains_path'],iat_gate['domains_sha256']).read_bytes());policy.update(iat)
 crt_gate=json.loads(pin(R/'reports/m4-startup138-paired/CRT-page-policy-r4/report.json','35fab86e1f2fe5199b69759cff6d995edd4a041ad40d9e99b8aece382c179f5e').read_bytes());pin(crt_gate['domains_path'],crt_gate['domains_sha256']);policy.update(CRT_page_source_domains_path=crt_gate['domains_path'],CRT_page_source_domains_sha256=crt_gate['domains_sha256'])
 admission_gates={}
 for path,h in [('reports/m4-startup138-paired/endpoint-domain-r1/report.json','316e7b3fc2f50a8fede92542e23390b05fe79ba8026711fb1e1a3a79e695fdac'),('reports/m4-startup138-paired/widget-pair-helper-preflight-r4/report.json','06d85e3becc811cc2b8bf0c1439417842d81e4ae770913164767c28df5009d3e'),('reports/m4-startup138-paired/current-MFC-pair-domain-r1/report.json','4409cba2b0bfde4c9f1edc7850d44ab183cd94a4fae161ab1cdc43d643bf8179'),('reports/m4-startup138-paired/original-registry-backings-r4/report.json','e90c569fa71b0a8dbdbb857eb079eb39295181241cc443d47723fbdef70727f5'),('reports/m4-tree-review/loaded-input138-r1/report.json','379e86517363d5abf25830b3805bb41ff5fe8b104a9e2349131e045c4a5cacec')]:
  gatepath=pin(R/path,h);g=json.loads(gatepath.read_bytes());assert g['passed'];admission_gates[str(gatepath)]=h
 policy.update(schema='mw34-paired138-complete-finite-policy-pending-independent-review-v2',current138_complete_typed_domain_admission=True,allphase_CPU_FX_ENV_lastwriter_admission=True,widget_whole_raw_endpoint_domain_admission=True,current_observer_span_domain_admission=True,current_registry_realloc_fullbacking_domain_admission=True,parent_domain_arrays_are_unadmitted_current_placeholders=False,current138_remaining_policy_frontiers=['Independent physical comparer/domain inverse preflight before any whole-pair invocation'],current_domain_receipts=admission_gates)
 policy['tree_activation_phase']=next(i for i,r in enumerate(cur['selected_order'])if r['entry']==0x4b7f70);cosine=json.loads(pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/Cosine-source-derivations.json').read_bytes());policy['cosine_phase']=next(i for i,r in enumerate(cur['selected_order'])if r['entry']==cosine[0]['root'])

 pp=out/'policy-preparation.json';pp.write_text(json.dumps(policy,indent=2)+'\n');pin(pp);pin(__file__);pin(sys.executable)
 r=dict(passed=True,scope='Concrete immutable comparer/policy preparation only; exact inverse retains accepted131 logic with current identities/69page extents/seven typed widget helper additions',comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(pp),policy_preparation_sha256=sha(pp),exact_inverse_restores_parent=True,all_parent_semantic_rules_retained=True,hunks=len(hunks),full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),comparer_sha256=sha(target),hunks=len(hunks),ready=False)))
if __name__=='__main__':main(sys.argv[1])
