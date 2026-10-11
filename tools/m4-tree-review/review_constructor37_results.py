"""Independent constructor capture outcome and physical request-repair review."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.zip','.mwb');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prep=read(R/'reports/m4-tree-review/constructor37-prelaunch-r9/report.json','fe05dc30221366ef0aa507aa973fca0cd5c13acdac4e276c9b23402d665f537a')
 execution=read(R/'reports/m4-constructor-original/chronological-execution-r3/report.json','cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4')
 result=read(R/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95')
 audit=read(R/'reports/m4-constructor-validator-audit/cleanup-keys-r1/report.json','638a855c4a297acf5bc8d57c2224180c109157cd9fee02587dcab8016eac908c')
 assert prep['passed']and execution['passed']and result['passed']and result['reader_closed']and audit['passed']
 assert result['execution_sha256']=='cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4'
 assert result['preparation_sha256']=='22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe'and result['build_sha256']=='03b93dd8035e24f091408442662cdcb1cb44532cc8af4d1a137efd9106a9948c'
 assert not result['native_executed']and not result['whole_literal_source_proof']and not result['source_AFTER_seed']and result['initializer_credit']==0
 for p,h in audit['files'].items():pin(p,h)
 physical=read(R/'reports/m4-constructor-original/request-rounding-r1/report.json','c1817707871eda399c126602e2bc6240081f076d914776cb091ff3babc375ee7')
 sp=importlib.util.spec_from_file_location('constructor_outcome_pe',pin(R/'tools/analysis/pe.py'));pe=importlib.util.module_from_spec(sp);sp.loader.exec_module(pe)
 crt=pe.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
 for row in physical['physical_spans']:
  raw=bytes.fromhex(row['raw_hex']);off,_=crt.rva_range(row['PC']-crt.image_base,len(raw));assert off==row['file_offset']and crt.data[off:off+len(raw)]==raw
 assert(physical['zero_normalization'],physical['rounding_addend'],physical['rounding_mask'],physical['source_request_max'],physical['admitted_heap_mode'])==(1,15,0xfffffff0,0xffffffe0,1)
 old=pin(R/'tools/m4-constructor-original/validate_v5.py','e702b75020c12b15a3ade692e66484e5b29c8be4b74ae22ba8e22e93d5e6cb74').read_text()
 new=pin(R/'tools/m4-constructor-original/validate_v6.py','4503f5f40d81138bf47bd08256e08daf32455c241117312ec46f810b932055ab').read_text()
 old=old.replace("        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)","        rounding=read(BASE/'request-rounding-r1/report.json','c1817707871eda399c126602e2bc6240081f076d914776cb091ff3babc375ee7');need(rounding['passed'],'Whole physical CRT mode1 requested-size contract')\n        for path,digest in rounding['files'].items():pin(path,digest)\n        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)",1)
 a="need(v[6]==requested and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and requested bytes')"
 b="need(mode==rounding['admitted_heap_mode']and requested<=rounding['source_request_max'],'Exact finite observed mode1 normal source request domain')\n                            rounded=((requested if requested else rounding['zero_normalization'])+rounding['rounding_addend'])&rounding['rounding_mask']\n                            need(v[6]==api[22]==rounded and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and literal rounded API request')\n                            row['source_MFC_requested']=requested;row['source_derived_HeapAlloc_requested']=rounded;counts['literal_CRT_request_rounding_joins']+=1"
 assert old.count(a)==1;old=old.replace(a,b)
 old=old.replace("pin(Path(__file__).with_name('derive_validator_v5.py'));pin(sys.executable);passed=True","pin(Path(__file__).with_name('derive_validator_v5.py'));pin(Path(__file__).with_name('validate_v5.py'));pin(Path(__file__).with_name('derive_validator_v6.py'));pin(sys.executable);passed=True",1)
 assert old==new,'Only exact source-request rounding, physical proof and lineage changed'
 expected={'whole_phase_records':222,'actual_new_constructor_phases':18,'actual_cdecl_MFC_pairs':36,'actual_new_NULL_free_pairs':12,'actual_getter_entry_preRET_pairs':12,'whole_actual_new_owner_cleanup_returns':36,'literal_CRT_request_rounding_joins':36,'actual_whole_initial_HeapAlloc_backings':126,'whole_source_page_endpoints':20424}
 for k,v in expected.items():assert type(result['counts'][k])is int and result['counts'][k]==v
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Independent current37 genuine capture outcome, exact physical CRT request rounding and preserved exhaustive cleanup-validator guards; original observations only, no native or full literal proof credit',counts=expected,physical_rounding_instructions=18,source_guard_relations_preserved=True,reader_opened=False,worker_launched=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])

