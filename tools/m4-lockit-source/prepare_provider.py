"""Additive complete124 provider observer derived from accepted120 observer.

This prepares only code/contracts. Execution is serialized after source124 and
uses one genuine bootstrap BEFORE per case, finite typed API leaf witnesses.
"""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;PINS[str(p)]=v;return p
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);base=ROOT/'tools/m4-vtable-review'
 accepted=pin(ROOT/'reports/m4-joint-startup120-root/acceptance-r1/report.json','e640ff4eaa068a039a5e810ad99b4c0ca0336821b8b1a6f33f81012ad43ed0ee');assert json.loads(accepted.read_bytes())['passed']
 source=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25').read_bytes());byroot={r['entry']:r for r in source['roots']};specs=[]
 for row in source['allocations']:
  root=byroot[row['root']];specs.append(dict(root=row['root'],CALL_pc=row['CALL_pc'],requested_size=row['requested'],object=root['objects'][0]['address'],publication=row['header_global']if row['conditional']else root['objects'][0]['address']+4,original_source_request_bytes=row['requested'],role=row['kind']))
 spec=out/'allocation-inputs.json';spec.write_text(json.dumps(specs,indent=2)+'\n');pin(spec)
 s=pin(base/'string_observer116.py').read_text();s=one(s,'import provider_capture as C','import capture as C');target=HERE/'string_observer124.py';assert not target.exists();ast.parse(s);target.write_text(s);pin(target)
 s=pin(base/'final_observer120_v2.py').read_text();s=one(s,"ROOT/'tools/m4-vtable-review/string_observer116.py'","ROOT/'tools/m4-lockit-source/string_observer124.py'")
 # Keep shared unchanged event observers importable; all new source/API code
 # remains in this lane's additive files and its physical closure is pinned.
 s=one(s,'from exact_equal import equal',"sys.path.insert(0,str(ROOT/'tools/m4-vtable-review'))\nfrom exact_equal import equal")
 anchor='  self.specs+=self.fs_specs';s=one(s,anchor,anchor+"\n  self.specs+=json.loads(self.pin(ROOT/'reports/m4-lockit-source/provider-preparation-r1/allocation-inputs.json').read_bytes())")
 s=s.replace('len(self.mfc)==50','len(self.mfc)==58').replace('Exact50 genuine','Exact58 genuine').replace('across43 MFC initializer roots','across47 MFC initializer roots')
 s=s.replace('len(responses.allocations)==70','len(responses.allocations)==78').replace('and50 actual MFC private owners','and58 actual MFC private owners').replace("==50 and sum(a.get('kind',1)==3", "==58 and sum(a.get('kind',1)==3")
 s=s.replace("len(responses.sections)==4,'Four actual source-initialized critical sections'","len(responses.sections)==5,'Four source CS plus fifth explicit native resource association'")
 s=s.replace('registry-replay-{92+n}', 'registry-replay-{96+n}').replace("COUNTS['complete120_provider_sequences']", "COUNTS['complete124_provider_sequences']").replace("COUNTS['selected_registration_closures']+=92", "COUNTS['selected_registration_closures']+=96").replace("COUNTS['actual_MFC_allocations']+=50", "COUNTS['actual_MFC_allocations']+=58").replace("COUNTS['actual_source_frees']+=70", "COUNTS['actual_source_frees']+=78").replace("COUNTS['actual_MFC_source_frees']+=50", "COUNTS['actual_MFC_source_frees']+=58").replace("COUNTS['actual_CS_deletes']+=4", "COUNTS['actual_CS_deletes']+=5").replace('actual_MFC_allocations=50','actual_MFC_allocations=58')
 s=one(s,"  self.prefix(m);self.owners", "  need(len(roots)==96,'Complete selected96 registration callbacks');responses.lockit_complete();COUNTS['complete_Lockit_semantic_API_relations']+=8\n  self.prefix(m);self.owners")
 target=HERE/'final_observer124.py';assert not target.exists();ast.parse(s);target.write_text(s);pin(target)
 for p in('exact_equal.py','event_model.py','vtable_model.py'):pin(base/p)
 prior=pin(ROOT/'reports/m4-lockit-source/connected-preparation-r3/report.json','cdf8d9a2fd70816e9d9a9de02f253b75bf9e42e8a64c5308256a45ca55c18535');d=json.loads(prior.read_bytes())
 for p,h in d['files'].items():pin(p,h)
 s=Path(d['comparer']).read_text();s=one(s,'import continuity as A','import continuity as A\nimport final_observer124 as F')
 s=one(s,"stem=f'sequence-{seq}/selected/'", "stem=f'sequence-{seq}/cleaned/'")
 s=one(s,'     class ObservedMachine(G.Machine):', '     F.configure(G,m,a,seq,level,pin)\n     class ObservedMachine(G.Machine):')
 s=one(s,"responses.associate_lockit(machine,resource,images,loaded_RW[0x640:0x658])", "machine.snapshot('lockit-resource-association-before');responses.associate_lockit(machine,resource,images,loaded_RW[0x640:0x658]);machine.snapshot('lockit-resource-association-after')")
 s=one(s,"       machine.call_stack.append((entry,FRAME,BROKER", "       F.begin(machine);machine.call_stack.append((entry,FRAME,BROKER")
 s=one(s,'G.complete_root(machine,api=responses)', 'G.complete_root(machine,api=responses);F.end(machine)')
 s=one(s,"counts['persistent124_sequences']+=1", "counts['persistent124_sequences']+=1;F.finish(machine,responses,expected_callbacks,G)")
 s=one(s,'finally:a.close();a.entries.clear();a.bundles.clear();del a', 'finally:\n    a.close();a.entries.clear()\n    for closed_bundle in a.bundles:closed_bundle._entries.clear()\n    a.bundles.clear();del a')
 s=one(s,"  passed=True\n except", "  need(F.COUNTS['complete124_provider_sequences']==12,'All12 complete persistent124 provider lifecycles')\n  for file in ('string_observer124.py','final_observer124.py','capture.py','responses.py'):pin(ROOT/'tools/m4-lockit-source'/file)\n  passed=True\n except")
 s=one(s,'native_continuity=continuity_rows,files=PINS','native_continuity=continuity_rows,provider_counts=dict(F.COUNTS),provider_sequences=F.ROWS,complete_provider_lifecycle=passed,worker_post_HeapDestroy_identity_observed=passed,files=PINS')
 target=HERE/'compare_provider124.py';assert not target.exists();ast.parse(s);target.write_text(s);pin(target);pin(__file__)
 report=dict(passed=True,scope='Additive prepared full provider124 source/owner/growth/cleanup observer from accepted120; no execution or root credit',comparer=str(target),MFC_owners=58,string_owners=19,registry_owners=1,CS_resources=5,selected_callbacks=96,selected_used_bytes=384,native_compared=False,initializer_credit=False,files=PINS)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),comparer=str(target))))
if __name__=='__main__':main(sys.argv[1])
