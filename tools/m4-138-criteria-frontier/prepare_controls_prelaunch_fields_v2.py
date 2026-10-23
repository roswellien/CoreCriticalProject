"""Prepare exact current-eight controls physical blocks; no reviewer execution."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;pins[str(p)]=v;return p
 base=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r7';pr=json.loads(pin(base/'report.json','21204a6c0511100caae296f557710124de7f2d35d2223cf365d715ef54af4d11').read_bytes())
 for leaf in ('native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py'):
  p=pin(base/leaf,pr['files'][str(base/leaf)]);s=p.read_text();old=s;edits=[]
  def change(a,b):
   nonlocal s
   assert s.count(a)==1,(leaf,a,s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b))
  if leaf=='native-TLS.py':change("TLS_names={","TLS_names={'?injection@context_control@@3PEAUInjection@1@EA',")
  if leaf=='native-linked.py':
   s=s.replace('CMakeFiles/mw34_joint_startup138.dir','CMakeFiles/mw34_widget_context_controls.dir');edits.append(dict(old='CMakeFiles/mw34_joint_startup138.dir',new='CMakeFiles/mw34_widget_context_controls.dir',all_occurrences=old.count('CMakeFiles/mw34_joint_startup138.dir')))
   s=s.replace('native_main.cpp.obj','controls_main.cpp.obj');edits.append(dict(old='native_main.cpp.obj',new='controls_main.cpp.obj',all_occurrences=old.count('native_main.cpp.obj')))
   change("('main','?growth_and_cleanup@@')","('main','?before_phase@context_control@@')")
   change("counts['whole_current_main_growth_functions']+=1","counts['whole_current_main_fault_functions']+=1")
   # Independently prove actual negative guard and sink at both optimization levels.
   s+="""
for prefix in ('context_controls_guarded','?sink@Writer@context_control@@'):
 candidates=[s['name']for s in sy.values()if s['name'].startswith(prefix)and s['section']>0 and s['type']==32];assert len(candidates)==1,prefix
 raw,relocs=C.function(sy,se,candidates[0]);matches=linked_candidates(image,raw,relocs);assert len(matches)==1,(prefix,len(matches));TLS_relations(image,raw,matches[0][1],relocs,se)
 links.append(dict(level=level,symbol=candidates[0],address=matches[0][0],whole_bytes=len(raw),relocation_DWORDs=len(relocs),domain='actual eight-mode entry/cause/writer/guard'));counts['whole_current_negative_guard_sink_functions']+=1
 if prefix=='context_controls_guarded':guard_address=matches[0][0]
cm=linked_candidates(image,control_br,control_rels)
cm=[(a,b)for a,b in cm if a+29+struct.unpack_from('<i',b,25)[0]==guard_address];assert len(cm)==1
address,actual=cm[0];uw=[v for v in entries if image.image_base+v[0]==address]
assert len(uw)==1 and image.image_base+uw[0][1]==address+85 and N.image_bytes(image,image.image_base+uw[0][2],8)==bytes.fromhex('0105020005320130')
links.append(dict(level=level,symbol='context_controls_hardware_call',address=address,whole_bytes=85,actual_guarded_target=guard_address,unwind_hex='0105020005320130'));counts['whole_current_negative_hardware_boundaries']+=1
"""
   edits.append(dict(appended=s[len(old):]if False else s[s.index('\nfor prefix in (\'context_controls_guarded\''):]))
  if leaf=='native-boundary.py':
   marker="assert br.hex()=="
   at=s.index(marker);prefix=s[:at];tail=s[at:]
   prefix=prefix.replace("br,brels=bsec[1]['bytes'],bsec[1]['relocations']","br_all,brels_all=bsec[1]['bytes'],bsec[1]['relocations']")
   added="""assert len(br_all)==170 and len(brels_all)==2
assert [(r['offset'],r['type'],r['symbol']['name'])for r in brels_all]==[(25,4,'mfc_connected_invoke_guarded'),(110,4,'context_controls_guarded')]
assert bsec[4]['bytes']==bytes.fromhex('01050200053201300105020005320130') and bsec[5]['bytes']==struct.pack('<6I',0,85,0,85,170,8)
labels_control=[s for s in bs.values()if s['name']=='context_controls_hardware_call'];assert len(labels_control)==1 and labels_control[0]['section']==1 and labels_control[0]['value']==85
br=br_all[:85];brels=[brels_all[0]];control_br=br_all[85:];control_rels=[dict(brels_all[1],offset=25)]
assert control_br==br
# Retained single-boundary predicates below consume exact physically proved
# first entries; the entire aggregate170B/2reloc/16xdata/24pdata is checked above.
bsec={**bsec,4:{**bsec[4],'bytes':bsec[4]['bytes'][:8]},5:{**bsec[5],'bytes':bsec[5]['bytes'][:12]}}
"""
   s=prefix+added+tail;edits.append(dict(old=old,new=s,domain='Complete two-boundary170-byte aggregate, exact both relocations/unwind rows, retained85-byte MFC slice plus own85-byte current negative guard'))
  ast.parse(s);q=out/leaf;q.write_text(s);pin(q);changes.append(dict(file=leaf,parent=str(p),parent_sha256=pins[str(p)],current_sha256=pins[str(q)],inverse_recipe=edits,retained_source_whole=(s==old)))
 identities=json.loads(pin(base/'inputs.json',pr['files'][str(base/'inputs.json')]).read_bytes())
 identities.update(native_prelaunch=['reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json','55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a'],native_preparation=['reports/m4-joint-startup138/controls-preparation-r4/report.json','f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'],native_build=['reports/m4-joint-startup138/controls-build-r2/build.json','e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'])
 q=out/'inputs.json';q.write_text(json.dumps(identities,indent=2)+'\n');pin(q)
 # Exact schema6 checker prefix includes complete positive-file domain and
 # its two source inverses. Keep it, only use actual current negative sources.
 p=pin(R/'tools/m4-138-criteria-frontier/check_schema138_v6.py','737749fb40562ed9ce89a3d1b9944e41eb936e158810101b097415cca6dbda09');s=p.read_text();start=s.index('  # Source preparation predicates remain');end=s.index('  for leaf,value in(');s=s[:start]+s[end:]
 for a,b in [("('whole-native-linked.json',links),('compiler-dependency-occurrences.json',all_deps),('original-pack-delta.json',pack_delta)","('whole-native-linked.json',links),('compiler-dependency-occurrences.json',all_deps)"),("measurements['native_prelaunch']","measurements['current8_shared_MFC_prelaunch']")]:assert s.count(a)==1;s=s.replace(a,b)
 # All component/body object location substitutions reside in the retained blocks.
 s=s.replace("any(p.resolve()==(folder/'native_main.cpp').resolve()for p in consumed)","any(p.resolve()==(folder/'controls_main.cpp').resolve()for p in consumed)")
 s=s.replace("Path(__file__).with_name('check_schema138_v1.py')","R/'tools/m4-138-criteria-frontier/check_schema138_v1.py'").replace("Path(__file__).with_name('check_schema138_v2.py')","R/'tools/m4-138-criteria-frontier/check_schema138_v2.py'")
 q=out/'review.py';ast.parse(s);q.write_text(s);pin(q)
 q=out/'source-delta.json';q.write_text(json.dumps(changes,indent=2)+'\n');pin(q)
 pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Source-only immutable current8 physical reviewer preparation; ROOT review and actual ordinary physical invocation required',whole_extracted_baseline_predicates_preserved=True,old12_fault_and_literal_entry_observer_not_transferred=True,current8_whole_two_boundary_aggregate_checked=True,current8_linked_main_beforephase_guard_sink_declared=True,old_positive_file_domain_two_inverse_predicates_preserved=True,worker_launched=False,archive_reader_opened=False,reviewer_executed=False,allowance_created=False,accepted_function_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
