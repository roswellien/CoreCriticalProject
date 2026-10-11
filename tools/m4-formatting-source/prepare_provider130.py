"""Freeze one combined persistent130 source/provider reader, retaining canonical format."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 src=R/'tools/m4-tree-source/compare_provider125_v4.py';dst=HERE/'compare_provider130.py';assert not dst.exists();s=src.read_text()
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one("ROOT/'reports/m4-tree-source'/name","ROOT/'reports/m4-formatting-source'/name")
 one("sys.path.insert(0,str(ROOT/'tools/m4-lockit-source'))", "sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'));sys.path.insert(0,str(ROOT/'tools/m4-tree-source'));sys.path.insert(0,str(ROOT/'tools/m4-lockit-source'))")
 one('import continuity125 as A','import continuity130 as A')
 one('import final_observer125_v2 as F','import final_observer130 as F')
 one("PAGES=(", "LEGACY_PAGES=(")
 one('FRAME=0x20001800;', 'PAGES=LEGACY_PAGES+(0x5cd000,0x5e3000,0x5e9000)\nR.EXPECTED_LOCKIT_CALLS=36\nFRAME=0x20001800;')
 one('PINS={}', '''PINS={};READS=set()
def input_audit(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 if p.is_relative_to(ROOT)and p.is_file()and(isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)):READS.add(str(p))
sys.addaudithook(input_audit)''')
 one("tree_rows=[];executed_lineage={}","tree_rows=[];format_rows=[];cosine_rows=[];executed_lineage={}")
 one("G=load('persistent54_game',ROOT/'tools/m4-tree-source/game_model_v4.py')", "model_receipt=json.loads(pin(ROOT/'reports/m4-formatting-source/persistent-family-model-r1/report.json','53c2a9f6dc3ede4ed5b089ff7c92490bbcdd4113679fc35ba830a4e359f50887').read_bytes());G=load('persistent130_game',pin(model_receipt['model'],model_receipt['model_sha256']))")
 one('m.PAGES=list(PAGES);J.PAGES=PAGES;S.PAGES=PAGES','m.PAGES=list(LEGACY_PAGES);J.PAGES=LEGACY_PAGES;S.PAGES=LEGACY_PAGES;m.FP.add(0x4b64f0)')
 one("op=pin(ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534')", "op=pin(ROOT/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca')")
 one("roots[0x4b7f70]=0x4b7fa0;program,callbacks=G.source_program();", "roots[0x4b7f70]=0x4b7fa0;roots.update({0x4df610:0x4df680,0x4e0710:0x4e07b0,0x4e0810:0x4e0850,0x4e1ca0:0x4e1ce0});program,callbacks=G.source_program();")
 one("order=json.loads(pin(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==125,'Exact selected125 rooted table order')", "joint_preparation=json.loads(pin(ROOT/'reports/m4-joint-startup130/preparation-r1/report.json','21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f').read_bytes());order=joint_preparation['selected_order'];need(len(order)==130,'Exact selected130 rooted table order');COS=load('compound130_source',ROOT/'tools/m4-cosine-native/persistent_source.py');pin(COS.SOURCE_PATH,'8cc0115421f6c7e6c8ac100201fdc5c3faa4161621ed3187738e3cf3a2570302');cos_contracts=json.loads(pin(ROOT/'reports/m4-cosine-original/prefix-preparation-r2/instruction-contracts.json','bf37da154d91b744d3b6d19368171685e87960507db3fc240e55222374f0cf71').read_bytes());pin(ROOT/'reports/m4-cosine-native/runtime-fixture-verification-r1/report.json','cc037925bc3f47f8d31c5ef96f0865632939688e65455e3c2b68c97b1ff3e12d')")
 one('FS_READ_BIAS={0x4125a0:0,0x500cd0:0}', '''mixed_interface=json.loads(pin(ROOT/'reports/m4-formatting-native/preparation-r18/family-contracts.json').read_bytes())['mixed_interface']
  for f in mixed_interface['FS_frame_contracts']:
   for k,kind in(('read_pc',0),('install_pc',1),('restore_pc',2)):FS_SPECS[f[k]]=(kind,f['function'],f['handler'])
  FS_READ_BIAS={0x4125a0:0,0x500cd0:0}''')
 one("need(len(image_raw)==34*40,'Exactly34 genuine native CS40 images')", "need(len(image_raw)==36*40,'Exactly36 genuine native CS40 images')")
 one('v=super().read(address,size,domain,pc)\n       if domain', '''original_pc=self.word(2472)if pc is None else pc;v=super().read(address,size,domain,pc)
       binding={(0x4dea15,0x5bb5a8):(0x1deb6c,0x780264a9),(0x4deab1,0x5bb664):(0x1de9aa,0x780012b3),(0x4dead1,0x5bb658):(0x1de9d0,0x78022b9a)}.get((original_pc,address))if domain=='source'and size==4 else None
       if binding:need(v==binding[0],'Literal formatter raw owning IAT');self.import_projections.append((10,original_pc,address,v,binding[1],0,0,0));v=binding[1]
       if domain''')
 one("root_access_start=len(machine.accesses);b=", "root_access_start=len(machine.accesses);root_PC_start=len(machine.PCs);root_alloc_start=len(responses.allocations);b=")
 one('expected=before_pages[i*4096:(i+1)*4096];actual=', 'expected=machine.bytes(p,4096);actual=')
 one('if entry==S.ENTRY:goal=S.spi_goal(tuple(cpu),before_pages,', 'if entry==S.ENTRY:goal=S.spi_goal(tuple(cpu),before_pages[:43*4096],')
 one('J.numeric_goal(c,bytes(machine.state),before_pages);','J.numeric_goal(c,bytes(machine.state),before_pages[:43*4096]);')
 one("else:\n        oracle=o[178404:354532]", "elif entry==0x4b64f0:goal,after_state=COS.phase_goal(bytes(machine.state),tuple(cpu),before_pages,o,cos_contracts,PAGES);cosine_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,source_events=goal['events'],numerical_oracle=goal['numerical_oracle'],extra_pages_preserved=goal['extra_pages_preserved']));counts['literal_compound_cosine_roots']+=1\n       else:\n        oracle=o[178404:354532]")
 one("m.phasegoal(entry,tuple(cpu),before_pages,oracle,inst[entry],schedule)","m.phasegoal(entry,tuple(cpu),before_pages[:43*4096],oracle,inst[entry],schedule)")
 one('for i,page in enumerate(PAGES):machine.store_bytes(page,goal[', 'for i,page in enumerate(PAGES if entry==0x4b64f0 else LEGACY_PAGES):machine.store_bytes(page,goal[')
 one("need(len(expected_callbacks)==97,'All97 actual callback registrations carried')","need(len(expected_callbacks)==101,'All101 actual callback registrations carried')")
 one("len(machine.lockit_state_reads)==34", "len(machine.lockit_state_reads)==36")
 one("counts['literal_Lockit_CALL_RET_pairs']+=34;counts['actual_native_CS40_source_API_relations']+=34", "counts['literal_Lockit_CALL_RET_pairs']+=36;counts['actual_native_CS40_source_API_relations']+=36")
 one("len(fs_observations)==78", "len(fs_observations)==84")
 one("len(fsframes)==26 and len(rawrecords)==52", "len(fsframes)==28 and len(rawrecords)==56")
 one('not stack and index==26','not stack and index==28')
 one("F.COUNTS['complete125_provider_sequences']==12", "F.COUNTS['complete130_provider_sequences']==12")
 one("rows.append(dict(level=level,sequence=seq,phase=phase,entry=entry", '''if entry in F.FORMAT_ROOTS:
       obs=F.S.CURRENT;allocations=responses.allocations[root_alloc_start:];need(len(allocations)==(4 if entry==0x4e1ca0 else 1),'Exact formatter plus optional three mixed allocation occurrences');owner=allocations[0];need(owner.get('formatter',False)and owner['extent']==16,'Literal formatting allocation caller provenance')
       def owner_result(a):return a|dict(initial=a['initial'].hex(),source_final_hex=machine.bytes(a['guest'],a['extent']).hex())
       local=machine.accesses[root_access_start:];fmt_calls=[]
       for row in obs.formatting_calls:
        if row[1]!=entry:continue
        fmt_calls.append(dict(root=entry,PC=row[2],target=row[3],frame=row[4],args=row[7:7+row[6]],returned=bool(row[14]),result=row[15],returned_ESP=row[4]+4))
       format_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,source_PCs=machine.PCs[root_PC_start:],source_accesses=local,calls=fmt_calls,owner=owner_result(owner),mixed_owners=[owner_result(a)for a in allocations[1:]],owned_accesses=[r for r in local if owner['guest']<=r[1]and r[1]+r[3]<=owner['guest']+owner['extent']],dispatches=[d for d in machine.output_dispatches if d['source_access_index']>=root_access_start],FS_frames=[f for f in fs_observations if f['root']==entry],API_relations=list(responses.lockit_relations),source_access_start=root_access_start))
       counts['literal_formatter_roots']+=1;counts['whole_formatter_native_capacity_derivations']+=1;counts['whole_mixed_native_capacity_derivations']+=len(allocations)-1
      rows.append(dict(level=level,sequence=seq,phase=phase,entry=entry''')
 one("('Tree-source-derivations.json',tree_rows)", "('Formatting-source-derivations.json',format_rows),('Cosine-source-derivations.json',cosine_rows),('Tree-source-derivations.json',tree_rows)")
 one('passed=True\n except Exception:', "for source_path in READS-set(PINS):pin(source_path)\n  need(READS<=set(PINS),'Every executed source/input physical read pinned')\n  pin(ROOT/'tools/m4-formatting-source/prepare_provider130.py');pin(ROOT/'tools/m4-formatting-source/final_observer130.py');pin(ROOT/'tools/m4-formatting-source/continuity130.py')\n  passed=True\n except Exception:")
 one("scope='One true bootstrap", "actual_dependency_reads=len(READS),source_and_provider_combined=True,scope='One true bootstrap")
 s=s.replace('persistent125_sequences','persistent130_sequences').replace('native125','native130').replace('entire43pages','entire46pages').replace('selected125','selected130')
 ast.parse(s);dst.write_text(s)
 continuity_src=R/'tools/m4-tree-source/continuity125.py';continuity_dst=HERE/'continuity130.py';assert not continuity_dst.exists();ct=continuity_src.read_text().replace("'selected-table.bin',125","'selected-table.bin',130").replace("'registration-roots.bin',97","'registration-roots.bin',101").replace('len(pages)==26','len(pages)==29').replace('All26 distinct','All29 distinct');ast.parse(ct);continuity_dst.write_text(ct)
 files={str(p.resolve()):sha(p)for p in(Path(__file__),src,dst,continuity_src,continuity_dst,HERE/'final_observer130.py')}
 report=dict(passed=True,scope='Prepared combined complete persistent130 source/provider gate; no archive read or runtime credit',tool=str(dst),files=files,canonical_reader_changed=False,coverage_reduced=False,separate_duplicate_selected_source_pass=False,source_and_provider_one_reader=True,executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
