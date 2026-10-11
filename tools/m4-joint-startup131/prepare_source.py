"""Freeze the additive complete131 combined reader, without opening captures."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True)
 parent=ROOT/'tools/m4-formatting-source/compare_provider130_v6.py';target=ROOT/'tools/m4-joint-startup131/compare_provider.py';assert not target.exists();text=parent.read_text()
 def one(a,b):
  nonlocal text
  assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b)
 one("ROOT/'reports/m4-formatting-source'/name", "ROOT/'reports/m4-joint-startup131-source'/name")
 one("sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'))", "sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'))")
 one('import continuity130 as A','import continuity131 as A\nimport mfc_source as MF')
 one('def main(native_report,name):','def main(native_report,original_report,original_digest,name):')
 one("provider_scope_rows=[];executed_lineage={}","provider_scope_rows=[];executed_lineage={};loader_rows=[];ori=None;readers_closed=False")
 one('executed_lineage=Q.lineage(native_report,nr,pin)', """build_path=pin(nr['build_path'],nr['build_sha256']);build_data=json.loads(build_path.read_bytes());preparation_path=pin(build_data['preparation'],build_data['preparation_sha256']);joint131=json.loads(preparation_path.read_bytes());need(joint131['passed']and len(joint131['selected_order'])==131,'Exact current131 prepared schedule');extension=MF.Extension(joint131,pin)
  parent_native=pin(Path(joint131['native_library']).parent/'report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3');executed_lineage=dict(execution=str(native_report),execution_sha256=sha(native_report),build=str(build_path),build_sha256=nr['build_sha256'],joint_preparation=str(preparation_path),joint_preparation_sha256=build_data['preparation_sha256'],inherited_native_preparation=str(parent_native),inherited_native_preparation_sha256=sha(parent_native))
  for p,h in build_data['files'].items():pin(p,h)""")
 one("op=pin(ROOT/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca')", "op=pin(original_report,original_digest);need(json.loads(op.read_bytes())['passed'],'Current complete genuine original131 validation')")
 old="joint_preparation=json.loads(pin(ROOT/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c').read_bytes());order=joint_preparation['selected_order'];need(len(order)==130,'Exact selected130 rooted table order')"
 new="joint_preparation=joint131;order=joint_preparation['selected_order'];need(len(order)==131 and order[13]=={'entry':0x5ae3e4,'slot':0x5e0040},'Exact selected131 rooted table order')"
 one(old,new)
 one("before['memory']=dict(before['memory'])", "before['memory']=dict(before['memory']);loader_rows.append(dict(level=level,sequence=seq,**extension.loader(before)))")
 one("if entry in roots or entry==0x4c19f0:m.statecpu(machine.state,cpu)", "if entry in roots or entry in(0x4c19f0,0x5ae3e4):m.statecpu(machine.state,cpu)")
 one("if entry==S.ENTRY:goal=S.spi_goal", "if entry==0x5ae3e4:\n        extension.phase(machine,a,level,seq,phase);after_state=bytes(machine.state);goal=dict(pages=b''.join(machine.bytes(p,4096)for p in LEGACY_PAGES));counts['literal_MFC1168_roots']+=1\n       elif entry==S.ENTRY:goal=S.spi_goal")
 one("len(rows)==1560 and len(format_rows)==48", "len(rows)==1572 and len(extension.rows)==12 and len(format_rows)==48")
 one("1560*46", "1572*46")
 one("passed=True\n except Exception:", "pin(ROOT/'tools/m4-joint-startup131/mfc_source.py');pin(ROOT/'tools/m4-joint-startup131/continuity131.py');pin(ROOT/'tools/m4-joint-startup131/prepare_source.py');need(extension.counts['MFC_source_operands']==1356 and extension.counts['MFC_owned_resource_lifecycles']==12,'Complete literal/resource new131 closure');counts.update(extension.counts)\n  passed=True\n except Exception:")
 one("finally:\n  (out/'API-identity-proofs.json')", "finally:\n  if ori is not None:ori.close();ori.entries.clear();ori.bundles.clear()\n  readers_closed=True\n  (out/'API-identity-proofs.json')")
 one("('Loaded-provider-source-scope.json',provider_scope_rows)", "('MFC-source-derivations.json',extension.rows if 'extension'in locals()else []),('MFC-loader-projections.json',loader_rows),('MFC-native-lifecycle-caller.json',extension.resources if 'extension'in locals()else []),('MFC-native-identity-joins.json',extension.identities if 'extension'in locals()else []),('MFC-unique-native-API-proofs.json',list(extension.proofs.values())if 'extension'in locals()else []),('Loaded-provider-source-scope.json',provider_scope_rows)")
 one('reader_closed=passed','reader_closed=readers_closed')
 one("if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])", "if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3],sys.argv[4])")
 text=text.replace('persistent130_sequences','persistent131_sequences').replace('persistent native130','persistent native131').replace('Every130 phase','Every131 phase').replace('selected130','selected131')
 ast.parse(text);target.write_text(text)
 source=ROOT/'tools/m4-formatting-source/continuity130.py';destination=ROOT/'tools/m4-joint-startup131/continuity131.py';assert not destination.exists();s=source.read_text().replace("'selected-table.bin',130", "'selected-table.bin',131").replace("entry==0x4c19f0", "entry in(0x4c19f0,0x5ae3e4)");ast.parse(s);destination.write_text(s)
 files={str(p.resolve()):sha(p)for p in(Path(__file__),parent,target,source,destination,ROOT/'tools/m4-joint-startup131/mfc_source.py',ROOT/'tools/m4-mfc1168-native/persistent_source.py')}
 report=dict(passed=True,scope='Unexecuted combined full131 persistent source/provider/lifecycle reader; no capture opened or initializer credit',tool=str(target),files=files,new_root=0x5ae3e4,source_AFTER_seed=False,per_phase_BEFORE_reseed=False,duplicate_selected_source_reader=False,canonical_reader_changed=False,expected_phases=1572,expected_MFC_literal_phases=12,expected_MFC_instructions=1704,expected_MFC_operands=1356,expected_MFC_typed_API_relations=48,expected_MFC_native_resource_services=156,expected_whole_page_endpoints_per_side=72312,original131_validation_required=True,writer_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
