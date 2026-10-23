"""Prepare exact source6 driver extension; observer adapter is a dependency.

Does not run a worker, open any capture, or authorize the resulting consumer.
"""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parent=R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py'
 observer=R/'tools/m4-native141-source/final_observer141_v3.py'
 assert observer.is_file(),'Independent final-observer adapter must exist before preparation'
 out=R/'reports/m4-startup141-source/preparation-r1';assert not out.exists();out.mkdir(parents=True)
 t=parent.read_text();changes=[]
 def one(a,b,n=1):
  nonlocal t
  assert t.count(a)==n,(a,t.count(a));t=t.replace(a,b);changes.append(dict(old=a,new=b,count=n))
 one("One persistent original-BEFORE source machine across selected131 native roots.", "One persistent bootstrap-BEFORE source machine across all selected141 native roots.")
 one("import continuity138 as A","_a_spec=importlib.util.spec_from_file_location('current141_continuity',ROOT/'tools/m4-native141-source/continuity141_v1.py');A=importlib.util.module_from_spec(_a_spec);_a_spec.loader.exec_module(A)")
 one("import final_observer138_v2 as F","_f_spec=importlib.util.spec_from_file_location('current141_final_observer',ROOT/'tools/m4-native141-source/final_observer141_v3.py');F=importlib.util.module_from_spec(_f_spec);_f_spec.loader.exec_module(F)")
 one("out=ROOT/'reports/m4-joint-startup138-source'/name","out=ROOT/'reports/m4-startup141-source'/name")
 one("nr=json.loads(pin(native_report).read_bytes());", "NI=load('current141_writer_input',ROOT/'tools/m4-native141-source/execution_input_v1.py');nr=NI.load(native_report,ROOT/'reports/m4-startup141-root/validation-r1/report.json','00406b1d901fe996e0d15f9281048ff6222d6bae5ceaf1d3e721b5d0f271d610',pin);")
 one("2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6","536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6")
 one("len(joint131['selected_order'])==138","len(joint131['selected_order'])==141")
 one("cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9","4483a6256bdbdc99482636fac97c6913be9a809d39e42686cb14757a00df8ad0")
 one("ROOT/'reports/m4-fps-original/source-preparation-r4/game_model.py'","ROOT/'tools/m4-native141-source/persistent_constructors_v4.py'")
 one("program,callbacks=G.source_program();static", "program,callbacks=G.source_program();roots.update({root:program[root+0x20]['decoded_operands'][0]['value']for root in G.ROOTS});constructor_rows=[];static")
 one("need(len(order)==138 and order[13]=={'entry':0x5ae3e4,'slot':0x5e0040},'Exact selected131 rooted table order');", "old_order=json.loads(pin(ROOT/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a').read_bytes())['selected_order'];need(len(order)==141 and [x for x in order if x['entry']not in G.ROOTS]==old_order,'Exact141 table insertion and complete unchanged138 order');original_phase={x['entry']:i for i,x in enumerate(old_order)};")
 one("checkpoint_index=PW.checkpoint_index(a,stem)","checkpoint_index=F.checkpoint_index(a,stem)")
 one("F.F.Observer=PW.observer_class(F.Observer);F.configure", "F.install_widget_observer(PW);F.configure")
 one("fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')))", "fsframes,rawrecords=F.partition_normal_FS(a,stem)")
 one("scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native138 game State/FX/CPU/ENV and entire69pages in actual table order. Component and provider source journals share exactly two literal borrowed CALL operands; actual native GDI scalar facts admit source-derived typed handle tokens only'", "scope='One true bootstrap BEFORE plus literal source and finite actual API responses in one carried native141 machine; whole State/CPU/FX/ENV, all69 inherited pages and constructor global5F2000 at every phase. Separate exhaustive component/provider source journals meet at exactly measured literal borrowed operands. Accepted old numerical oracle remains within immutable original138 domain.'")
 one("complete_selected_source=True", "complete_selected_source=passed,complete_persistent141_constructors=passed,original_constructor_equivalence=False")
 one("o=ori.data(f'phase/{seq}/{phase}.bin');", "o=ori.data(f'phase/{seq}/{original_phase[entry]}.bin')if entry not in G.ROOTS else None;")
 one("      if entry in PW.WIDGETS:","      if entry in G.ROOTS:\n       constructor_rows.append(F.constructor_phase(machine,responses,entry,a,seq,level,phase));counts['literal_constructor_roots']+=1\n      elif entry in PW.WIDGETS:")
 one("      fx,env=projection(m,machine.state);equal(machine.cpu,b[36:76]", "      equal(machine.bytes(0x5f2000,4096),a.data(f'sequence-{seq}/phase-{phase}-before-constructor-global5F2000.bin'),'Whole independently carried constructor global BEFORE');counts['whole_constructor_global_BEFORE']+=1\n      fx,env=projection(m,machine.state);equal(machine.cpu,b[36:76]")
 one("      need(machine.reg('esp')==FRAME+4 and machine.cursor==BROKER and not machine.call_stack,'Exact persistent source RETURN');", "      equal(machine.bytes(0x5f2000,4096),a.data(f'sequence-{seq}/phase-{phase}-after-constructor-global5F2000.bin'),'Whole independently computed constructor global AFTER');counts['whole_constructor_global_AFTER']+=1\n      need(machine.reg('esp')==FRAME+4 and machine.cursor==BROKER and not machine.call_stack,'Exact persistent source RETURN');")
 one("association.prove_projection_rows(a.data(stem+'locale-research-projections.bin'))", "association.prove_projection_rows(F.prove_constructor_projections(machine,a.data(stem+'locale-research-projections.bin')))")
 one("len(expected_callbacks)==108", "len(expected_callbacks)==111")
 one("if len([r for r in rows if r['level']==level])==828:", "if len([r for r in rows if r['level']==level])==846:")
 one("len(rows)==1656", "len(rows)==1692")
 one("1656*69", "1692*69")
 one("  need(F.COUNTS['complete130_provider_sequences']==12", "  need(len(constructor_rows)==36 and counts['whole_constructor_global_BEFORE']==counts['whole_constructor_global_AFTER']==1692,'All36 constructors and all1692 BEFORE plus1692 AFTER whole global page endpoints');\n  need(F.COUNTS['complete130_provider_sequences']==12")
 one("(('Widget-source-derivations.json',widget_rows)", "(('Constructor-carried-source-derivations.json',constructor_rows if 'constructor_rows'in locals()else []),('Widget-source-derivations.json',widget_rows)")
 ast.parse(t);reverse=t
 for c in reversed(changes):assert reverse.count(c['new'])==c['count'];reverse=reverse.replace(c['new'],c['old'])
 assert reverse==parent.read_text()
 for name in ('compare_provider141.py',):(out/name).write_text(t)
 (out/'paired_exports.py').write_bytes((R/'tools/m4-native141-source/paired_exports_v1.py').read_bytes())
 (out/'driver-deltas.json').write_text(json.dumps(changes,indent=2)+'\n')
 files={str(parent):sha(parent),str(observer):sha(observer),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for p in out.iterdir():files[str(p)]=sha(p)
 report=dict(passed=True,prepared_only=True,source_execution=False,canonical_reader_opened=False,exact_parent_inverse=True,entrypoint=str(out/'compare_provider141.py'),observer_policy_review_required=True,source_domain_current141=True,expected_native_phases=1692,expected_constructor_executions=36,expected_constructor_global_BEFORE=1692,expected_constructor_global_AFTER=1692,expected_constructor_global_endpoints_total=3384,original_numerical_oracle_domain_unchanged138=True,persistent_source_execution_pending=True,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
