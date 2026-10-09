"""Retain the frozen rich hardware validator with current closed query semantics."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
s=(HERE/'check_main.inc').read_text().replace('m4-crt-heap-mode-review','m4-crt-heap-version-review')
s=s.replace("native['native_scenarios'] == 132","native['native_scenarios'] == 196").replace('result, count = semantic_inventory(bundle, records)','result, count, heaps, queries, output_commits, selector_returns = semantic_inventory(bundle, records)')
s=s.replace('actual, counts, inventory_tests, before, after = 0, {}, [], None, None','actual, counts, inventory_tests, before, after = 0, {}, [], None, None\n    actual_heaps=actual_queries=actual_output_commits=actual_selector_returns=0')
s=s.replace('for number in range(1,67):','for number in range(1,99):')
s=s.replace('            counts[level] = count','            for diagnostic in (1,2):\n                validator(reader.path(f"direct-query-failure-{diagnostic}/query-host-before.bin"),reader.path(f"direct-query-failure-{diagnostic}/query-host-after.bin"),98+diagnostic)\n                actual+=1\n            actual_heaps+=heaps;actual_queries+=queries;actual_output_commits+=output_commits;actual_selector_returns+=selector_returns\n            counts[level] = count')
s=s.replace('case-67/heap-status.bin','case-99/heap-status.bin').replace("('GetVersionExA_executed',True)","('actual_GetVersionExA_executed',False),('synthetic_API_results',True)")
a=s.index('                for field,value in')
extra='''                for filename,offset,label in (('query-witness.bin',24,'private_actual_BOOL'),('query-witness.bin',88,'actual_output_commit_count'),('query-witness.bin',144,'actual_native_major'),('query-status.bin',28,'query_returned_flag'),('query-status.bin',32,'genuine_selector_RET_flag'),('query-output-accesses.bin',8,'native_output_commit_value'),('query-output.bin',4,'full_native_major_bytes'),('query-input.bin',0,'original_source_query_size'),('query-api-before.bin',0,'actual_named_query_API'),('heap-api-accesses.bin',24,'second_genuine_API_return_frame'),('heap-undefined-sites.bin',16,'qualified_query_TEST_AF'),('heap-accesses.bin',30*20+8,'genuine_selector_RET_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('status.bin',16,'actual_host_only_failed_BOOL'),('status.bin',12,'nonzero_host_only_incoming_error'),('scratch-before.bin',0,'host_only_invalid_size'),('api-after.bin',0,'actual_host_only_API_identity')):
                    data=bytearray(bundle.read_bytes('direct-query-failure-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'direct-query-failure-1/'+filename:bytes(data)}))
'''
s=s[:a]+extra+s[a:]
s=s.replace('need(actual==264 and len(tests)==548 and len(inventory_tests)==39','need(actual==396 and len(tests)==548 and len(inventory_tests)==56')
s=s.replace("'native_scenarios':132","'native_scenarios':196").replace("'actual_hardware_pairs':264","'actual_hardware_pairs':396").replace("'inventory_request_denials':39,'actual_HeapCreate_calls':84,'actual_successful_HeapDestroy_calls':84","'inventory_request_denials':56,'actual_HeapCreate_calls':actual_heaps,'actual_successful_HeapDestroy_calls':actual_heaps,'actual_integrated_GetVersionExA_calls':actual_queries,'counterfactual_direct_host_failure_queries':4,'actual_output_DWORD_commits':actual_output_commits,'actual_selector_RETs':actual_selector_returns")
s=s.replace("'GetVersionExA_executed':False","'GetVersionExA_executed':False,'validates_actual_query_native_witness':True,'synthetic_API_results':False,'alternate_query_branch_live_coverage':False,'selector_result_produced_by_genuine_source':True,'guest_heap_mode_global_published':False")
s=s.replace("'hardware_pairs':264","'hardware_pairs':396")
(HERE/'check.py').write_text((HERE/'check_header.inc').read_text()+(HERE/'check_schema.inc').read_text()+'\n\n'+s,encoding='utf-8')
