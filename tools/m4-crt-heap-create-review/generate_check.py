"""Retain the unchanged rich hardware validator and adapt new exact fixture schema."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
s=(ROOT/'tools/m4-crt-heap-init-review/check.py').read_text()
prefix=s[:s.index('REQUESTS =')]
main=s[s.index('def main(native_path, output):'):]
main=main.replace('reports/m4-crt-heap-init-review','reports/m4-crt-heap-create-review')
main=main.replace("heap-api-before","heap-create-api-before")
main=main.replace('(109).to_bytes','(121).to_bytes').replace("('active_boundary_depth',32),('active_heap_after_cleanup',48)","('active_boundary_depth',36),('active_heap_after_cleanup',52)")
main=main.replace("('malformed_token_denials',24)","('malformed_token_denials',17)")
main=main.replace("'HeapCreate_executed':False,'heap_initialized':False", "'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'heap_initialized':False")
main=main.replace("'native_executed':False,", "'full_causal_source_model_oracle':False,'native_executed':False,")
main=main.replace("'logical_files':counts,", "'actual_HeapCreate_calls':70,'actual_successful_HeapDestroy_calls':70,'logical_files':counts,")
main=main.replace("for field,value in (('passed',1)","for field,value in (('passed',1)")
# Separate semantic denials for the new private ownership and typed API witness.
anchor="                for field,value in (('passed',1)"
extra='''                for filename,offset,label in (('independent-ownership.bin',24,'actual_create_count'),('independent-ownership.bin',40,'actual_release_success_count'),('independent-ownership.bin',56,'live_handle_after_cleanup'),('heap-registry.bin',32,'full_native_HANDLE_association'),('heap-registry.bin',56,'registry_live_after_cleanup'),('heap-registry.bin',80,'actual_destroy_result'),('heap-witness.bin',48,'actual_full_HANDLE_witness'),('heap-witness.bin',56,'guest_token_witness'),('heap-witness.bin',64,'actual_incoming_error_read'),('heap-witness.bin',80,'actual_restored_error_read'),('heap-api-accesses.bin',4,'real_source_return_frame'),('heap-create-api-before.bin',0,'named_creator_API_identity'),('heap-destroy-api-after.bin',0,'named_release_API_identity')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
'''
if anchor not in main:raise ValueError('Frozen corruption fixture insertion')
main=main.replace(anchor,extra+anchor)
main=main.replace('len(inventory_tests)==14','len(inventory_tests)==27').replace("'inventory_request_denials':14","'inventory_request_denials':27")
(HERE/'check.py').write_text(prefix+(HERE/'check_schema.inc').read_text()+'\n'+main,encoding='utf-8')
