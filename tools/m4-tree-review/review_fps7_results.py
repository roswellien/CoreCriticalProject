"""Independent seven-root source result review from the sealed widget reviewer."""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parents[2]
base=R/'tools/m4-widget-source-review/review_results.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='9d786df976563d1dc96361fcb6cfd73f635562661f4698a26113a1f4a362ee77'
text=base.read_text()
changes={
"out=R/'reports/m4-widget-source-review'/name":"out=R/'reports/m4-fps-source-review'/name",
"execution_sha='1b7f14c5b68f43df3389b9d6cddbbf9dd594c794b4420e002349188313a7a12c'":"execution_sha='cfdcce62777df1f69c3ae15cfa1750dfde4e10ba28a83dfabbcdfb5656e77180'",
"m4-widget-native/fixture-execution-r4":"m4-fps-native/fixture-execution-r2",
"m4-widget-native/source-prefix-r1":"m4-fps-native/source-prefix-r1",
"m4-widget-native/source-registry-r4":"m4-fps-native/source-registry-r1",
"38986acdc2600a5f9207d6724ff237beca57fd3facd7d2d3dbb89fffef15088b":"545304f54cdef712f9dfd44bf3b9384ff9769ad5bd722d77c6c8cad890db1486",
"ef11e37177594ded312110b2efc4ae6c4939b15d23e89563bc4ba2a050ffc737":"61949af6d50123ba09402a8eb07e96c62b6fdf34f61d6e379c96eaca427150af",
"expected_p={'literal_prefixes':12,'exact_prefix_operand_rows':49250,'actual_GDI_scalar_response_joins':294,'whole_API_frame64_joins':294,'FS_source_relations':1158,'virtual_source_relations':1010,'array_source_relations':150,'whole_State3504_entry_joins':12,'whole_stack4096_relations':12,'whole_game_bytes_compared':74956800}":"expected_p={'literal_prefixes':14,'exact_prefix_operand_rows':49964,'actual_GDI_scalar_response_joins':298,'whole_API_frame64_joins':298,'FS_source_relations':1176,'virtual_source_relations':1022,'array_source_relations':150,'whole_State3504_entry_joins':14,'whole_stack4096_relations':14,'whole_game_bytes_compared':87449600,'whole_current_provider_source_page_joins':70,'literal_formatter_lifetimes':2,'whole_formatter_defined_CPU40_sides':4,'whole_formatter_frame64_sides':4,'whole_formatter_destination512_sides':4,'whole_formatter_FX512_sides':4,'whole_formatter_va64_sides':4,'literal_character_dispatches':6}",
"expected_r={'literal_provider_operands':804,'actual_source_API_joins':36,'whole_provider_page_or_capacity_relations':720,'literal_tail_instructions':120,'literal_tail_RET_operand_relations':36,'whole_source_root_State3504_relations':12,'whole_source_root_stack4096_relations':12,'unmodeled_cleanup_after_interval_joins':60}":"expected_r={'literal_provider_operands':938,'actual_source_API_joins':42,'whole_provider_page_or_capacity_relations':840,'literal_tail_instructions':140,'literal_tail_RET_operand_relations':42,'whole_source_root_State3504_relations':14,'whole_source_root_stack4096_relations':14,'unmodeled_cleanup_after_interval_joins':70,'physical_additive_FPS_tail_instruction_joins':10}",
"len(pd)==len(rd)==12":"len(pd)==len(rd)==14",
"m4-font479590-original/source-preparation-r1/source-contracts.json":"m4-fps-native/component-preparation-r1/contracts.json",
"roots=[0x40e250,0x40ef50,0x5a3c30,0x5a3ff0,0x5a66f0,0x479590]":"roots=[0x40e250,0x40ef50,0x5a3c30,0x5a3ff0,0x5a66f0,0x479590,0x40f000]",
"phase in range(6)":"phase in range(7)",
"PC_count==42404 and snapshots==84":"PC_count==43562 and snapshots==98",
"root_results=12":"root_results=14",
"current52":"current58",
}
for a,b in changes.items():
 assert a in text,a;text=text.replace(a,b)
needle=" execution_sha='cfdcce62777df1f69c3ae15cfa1750dfde4e10ba28a83dfabbcdfb5656e77180'"
extra=r'''
 for directory,h in [('source-preparation-r1','c02b1a7f71bda4ada0738c522cee6b29a223f3b51f3e6beb614eb2f302fa07bb'),('registry-source-preparation-r2','00ab5f2eca9ea3052588b37b4a49d93c1929400260687f9dc83f96f8af3c8d21')]:
  receipt=read(R/'reports/m4-fps-native'/directory/'report.json',h)
  need(receipt['passed']and not receipt['archive_reader_opened']and receipt['actual_worker_launches']==0,'Exact own-BEFORE FPS source adapter')
  for p,v in receipt['files'].items():pin(p,v)
 admission=read(R/'reports/m4-tree-review/fps7-prelaunch-r4/report.json','0948f36b4ca8c82bf8cb923b8965aa7cda99eb9901caf8f4ae0203deff970633')
 need(admission['passed']and admission['counts']['whole_physical_source_rows']==1246 and admission['counts']['whole_new_owned_provider_PE_pages']==5,'Full current physical rows and complete own CRT mappings independently authenticated')
 for p,v in admission['files'].items():pin(p,v)
 pin(base,'9d786df976563d1dc96361fcb6cfd73f635562661f4698a26113a1f4a362ee77')
'''
assert text.count(needle)==1;text=text.replace(needle,extra+needle)
exec(compile(text,str(base),'exec'),globals())

