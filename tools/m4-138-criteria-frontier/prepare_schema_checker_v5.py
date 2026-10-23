"""Materialize exact current positive-file inverses, no blanket unchanged claim."""
from pathlib import Path
import hashlib,json,runpy,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r4';assert sha(old/'report.json')=='292b94cf8caeed8f7871e4ee952d10e1caaf7af3deb2bb0b52d99a3cbf3844ca'
out=old.parent/'schema-checker-preparation-r5';assert not out.exists();out.mkdir()
pr=json.loads((old/'report.json').read_bytes());pins={str(old/'report.json'):sha(old/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for n in ['accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json']:
 p=old/n;assert sha(p)==pr['files'][str(p)];pins[str(p)]=sha(p);q=out/n;q.write_bytes(p.read_bytes());pins[str(q)]=sha(q)
base=R/'tools/m4-138-criteria-frontier/check_schema138_v3.py';assert sha(base)=='517c18c1ff14151fabb98326ffed73f8da0acbac4b85fb50961c7dfdec4b05ef';pins[str(base)]=sha(base)
ns=runpy.run_path(str(base),run_name='definition_only');s=ns['s']
anchor="  pf=R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5'"
addition='''
  # Two exact current positive-file extensions are proved independently of
  # the otherwise byte-identical source domain. No changed file is skipped.
  original_widget=read(R/'reports/m4-fps-original/preparation-r1/report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1')
  wc=read(prep['widget_component_preparation'],prep['widget_component_preparation_sha256']);assert wc['passed'] is True
  wp=Path(prep['widget_component_preparation']).parent
  contracts=read(wp/'contracts.json',wc['files'][str(wp/'contracts.json')]);newroots=[x['root']for x in contracts['roots']]
  assert newroots==wc['roots'] and len(newroots)==7 and len(set(newroots))==7
  fixed=[int(v,16)for v in re.search(r' pages\\{([^}]+)',blob(pf/'joint_protocol.hpp').decode())[1].split(',')];assert len(fixed)==17
  service=read(prep['borrowed_service_preparation'],prep['borrowed_service_preparation_sha256']);assert service['passed'] is True
  service_header=Path(prep['borrowed_service_preparation']).parent/'session.hpp'
  assert blob(folder/'onexit_session.hpp')==blob(service_header,service['files'][str(service_header)])
  positive_relations=[]
  def prove_positive_file(rel,before,after):
   if rel.as_posix()=='onexit_session.hpp':
    added=b' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);\\r\\n'
    at=b' void finish();void dump(Sink,void*)const;'
    assert before.count(at)==1 and before.count(added)==0 and after.count(added)==1
    assert after==before.replace(at,added+at) and after.replace(added,b'')==before
    return 'exact_one_method_declaration_no_fields_or_class_layout_change'
   assert rel.as_posix()=='registration_contract.hpp'
   old_pages=[int(v,16)for v in re.search(rb'registration_pages\\{([^}]+)',before)[1].split(b',')]
   old_roots=[int(v,16)for v in re.search(rb'registration_roots\\{([^}]+)',before)[1].split(b',')]
   assert len(old_pages)==29 and len(set(old_pages))==29 and len(old_roots)==101 and len(set(old_roots))==101 and not set(old_roots)&set(newroots)
   expected_pages=sorted((set(original_widget['observed_pages'])|set(original_widget['external_pages'])|set(old_pages)|set(fixed)|{0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000})-set(fixed))
   assert len(expected_pages)==52
   expected=before
   for name,count,values in [('registration_pages',29,expected_pages),('registration_roots',101,old_roots+newroots)]:
    pattern=rb'constexpr std::array<unsigned,'+str(count).encode()+rb'> '+name.encode()+rb'\\{[^}]+\\};'
    replacement=('constexpr std::array<unsigned,'+str(len(values))+'> '+name+'{'+','.join(hex(x)for x in values)+'};').encode()
    expected,n=re.subn(pattern,replacement,expected);assert n==1
   # The generator's whole registration header also normalizes CR bytes.
   assert before.replace(b'\\r',b'').count(b'\\n')==3+1
   assert expected.replace(b'\\r',b'')==after
   page_union=read(folder/'source-page-union.json',prep['files'][str(folder/'source-page-union.json')]);assert page_union['fixed']==fixed and page_union['extra']==expected_pages
   phase_map=read(folder/'widget-phase-map.json',prep['files'][str(folder/'widget-phase-map.json')]);assert [x['root']for x in phase_map]==newroots
   assert [x for x in prep['selected_order']if x['entry']in newroots]==[dict(entry=x['root'],slot=x['slot'])for x in sorted(contracts['roots'],key=lambda z:z['slot'])]
   return 'exact101_callback_prefix_plus7_and29_page_source_inventory_union52'
'''
oldcheck="   assert blob(folder/rel)==blob(p).replace(pf.as_posix().encode(),folder.as_posix().encode()),rel\n   counts['whole_unchanged_positive_component_files']+=1"
newcheck="""   before=blob(p).replace(pf.as_posix().encode(),folder.as_posix().encode());after=blob(folder/rel)
   if before==after:counts['whole_unchanged_positive_component_files']+=1;relation='whole_bytes_equal'
   else:relation=prove_positive_file(rel,before,after);counts['whole_exact_inverse_positive_component_files']+=1
   counts['whole_inherited_positive_file_domain']+=1
   positive_relations.append(dict(file=rel.as_posix(),relation=relation,parent_sha256=pins[str(p.resolve())],current_sha256=pins[str((folder/rel).resolve())]))
  assert counts['whole_exact_inverse_positive_component_files']==2
  measurements['positive_file_relations']=positive_relations"""
assert s.count(anchor)==1 and s.count(oldcheck)==1;s=s.replace(anchor,anchor+addition).replace(oldcheck,newcheck)
assert s.replace(anchor+addition,anchor).replace(newcheck,oldcheck)==ns['s']
checker=R/'tools/m4-138-criteria-frontier/check_schema138_v4.py';assert not checker.exists();checker.write_text(s);pins[str(checker)]=sha(checker)
result=dict(passed=True,scope='Code-only complete positive-file domain exact byte/inverse proof; two transformed files separately classified, not unchanged and not excluded',whole_extracted_baseline_predicates_preserved=True,checker_sha256=sha(checker),checker_source_delta=dict(anchor=anchor,addition=addition,before=oldcheck,after=newcheck,parent_checker_sha256=sha(base)),files=pins)
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(out/'report.json'));print(sha(checker))
