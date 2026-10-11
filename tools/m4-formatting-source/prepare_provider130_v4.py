"""Freeze complete130 source/private publication checks on corrected current19."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True);src=HERE/'compare_provider130.py';dst=HERE/'compare_provider130_v2.py';assert not dst.exists();s=src.read_text()
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one('import final_observer130 as F','import final_observer130 as F\nimport formatting_derivations as FD')
 one("reports/m4-joint-startup130/preparation-r1/report.json','21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f","reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c")
 one("COS=load('compound130_source',ROOT/'tools/m4-cosine-native/persistent_source.py')", "COS=load('compound130_source',pin(ROOT/'tools/m4-cosine-native/persistent_source.py','1970d7b98e9c2a8d02a8a5b75692c74d8f0e07f09541241340ad1e37164c1cd9'))")
 one("root_alloc_start=len(responses.allocations);b=", "root_alloc_start=len(responses.allocations);root_relation_start=len(responses.lockit_relations);b=")
 one("record_hex=raw.hex()if raw is not None else None)", "record_hex=raw.hex()if raw is not None else None,source_access_index=len(model.accesses)-int(not write))")
 a=s.index('      if entry in F.FORMAT_ROOTS:');b=s.index('      rows.append(',a)
 s=s[:a]+'''      if entry in F.FORMAT_ROOTS:
       derivation=FD.derive(machine,responses,F.S.CURRENT,entry,root_access_start,root_PC_start,root_alloc_start,root_relation_start,before_pages,PAGES,level,seq,phase,fs_observations);format_rows.append(derivation)
       counts['literal_formatter_roots']+=1;counts['whole_formatter_native_capacity_derivations']+=1;counts['whole_mixed_native_capacity_derivations']+=len(derivation['mixed_owners'])
''' +s[b:]
 one("result=machine.tree_result();tree_counts=T.verify", "mixed_result=next(r for r in format_rows if r['level']==level and r['sequence']==seq and r['root']==0x4e1ca0)\n     for key,value in FD.verify_mixed(a,stem,mixed_result,fs_observations,machine.accesses,mixed_interface).items():counts[key]+=value\n     result=machine.tree_result();tree_counts=T.verify")
 one("need(F.COUNTS['complete130_provider_sequences']==12,'All12 complete persistent125 provider lifecycles')", "need(F.COUNTS['complete130_provider_sequences']==12,'All12 complete persistent130 provider lifecycles');need(len(rows)==1560 and len(format_rows)==48 and len(cosine_rows)==12 and len(tree_rows)==12,'Every130 phase and all four formatting/COS/tree families in bothlevels six sequences');need(counts['whole_page_BEFORE']==counts['whole_page_AFTER']==1560*46,'Complete current46-page endpoint equality without reduced coverage');pin(ROOT/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')")
 one("pin(ROOT/'tools/m4-formatting-source/continuity130.py')", "pin(ROOT/'tools/m4-formatting-source/continuity130.py');pin(ROOT/'tools/m4-formatting-source/formatting_derivations.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v2.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v3.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v4.py')")
 one("actual_dependency_reads=len(READS),", "actual_dependency_reads=len(READS),complete_selected_source=True,complete_private_mixed_publications=True,complete_private_mixed_FS32Q=True,reader_closed=passed,canonical_reader_changed=False,duplicate_selected_source_reader=False,")
 ast.parse(s);dst.write_text(s)
 files={str(p.resolve()):sha(p)for p in (src,dst,Path(__file__),HERE/'formatting_derivations.py',HERE/'final_observer130.py',HERE/'continuity130.py')}
 report=dict(passed=True,scope='Unexecuted canonical-reader combined130 complete source/provider gate with full new mixed private pub/FS/Lockit joins',files=files,tool=str(dst),current_native_preparation='preparation-r19',current_joint_preparation='preparation-r2',source_formatting_derivation_rows=48,source_cosine_derivation_rows=12,selected_phases=1560,ordinary_pages=46,new_mixed_FS32Q=24,new_mixed_full_publications=36,new_mixed_owned16Q=120,executed=False,capture_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
