"""Reuse the immutable hardware validator transport with fresh fixture semantics."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
s=(ROOT/'tools/m4-crt-heap-create-review/check.py').read_text()
a=s.index('def need(');b=s.index('def main(native_path',a)
s=s[:a]+(HERE/'check_schema.inc').read_text()+'\n\n'+s[b:]
s=s.replace('m4-crt-heap-create-review','m4-crt-heap-mode-review')
s=s.replace("('passed',1),('scenarios',65)","('GetVersionExA_executed',True),('passed',1),('scenarios',65)")
s=s.replace("                for field,value in",'''                for filename,offset,label in (('lower-input-status.bin',0,'declared_initial_pattern'),('declared-lower-input.bin',0x624,'declared_initial_tail_word'),('heap-accesses.bin',13*20+8,'first_probe_read_value'),('heap-accesses.bin',23*20+8,'query_return_store_value'),('heap-undefined-sites.bin',12,'qualified_final_TEST_AF'),('heap-status.bin',128,'probe_reached'),('heap-status.bin',132,'genuine_probe_returned'),('heap-status.bin',136,'query_frontier_reached'),('heap-status.bin',140,'genuine_probe_frame'),('independent-after/page-536870912.bin',0x10,'complete_lower_page_untouched_byte'),('independent-after/page-536870912.bin',0x618,'literal_query_return_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for field,value in''')
s=s.replace("len(inventory_tests)==27","len(inventory_tests)==39")
s=s.replace("'inventory_request_denials':27,'actual_HeapCreate_calls':70,'actual_successful_HeapDestroy_calls':70", "'inventory_request_denials':39,'actual_HeapCreate_calls':84,'actual_successful_HeapDestroy_calls':84")
s=s.replace("'validates_actual_heap_ownership':True", "'validates_actual_heap_ownership':True,'declared_initial_lower_stack_patterns':6,'GetVersionExA_executed':False,'probe_return_proved':True,'original_stack_guard_growth_proved':False")
(HERE/'check.py').write_text(s,encoding='utf-8')
