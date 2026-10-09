"""Preserve the strict hardware validator and author current closed return semantics."""
import hashlib,sys
sys.dont_write_bytecode=True
from pathlib import Path
from checker_package import adapt
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent;OLD=ROOT/'tools/m4-crt-heap-version-review'
def change(s,a,b):
    if a not in s:raise ValueError('Required frozen checker fragment '+a[:120])
    return s.replace(a,b)
def main():
    frozen=(OLD/'check.py').read_bytes()
    if hashlib.sha256(frozen).hexdigest()!='d21d1213a8b99983194765161d509d43d8b8634a69bf3dcf1c7527602bbfec8e':raise ValueError('Frozen accepted checker changed')
    old=frozen.decode().replace('\r\n','\n');header=old[:old.index('def need(')];schema=old[old.index('def need('):old.index('def main(')];main=old[old.index('def main('):].replace('m4-crt-heap-version-review','m4-crt-heap-return-review')
    schema=change(schema,'REQUESTS=[0]*6+list(range(145,157))+list(range(1,81))','REQUESTS=[0]*6+list(range(157,169))+list(range(1,105))')
    schema=change(schema,"PHASE_FILES=set('","PHASE_FILES={'heap-return-progress.bin'}|set('");schema=change(schema,"CASE_FILES=set('","CASE_FILES={'heap-return-progress.bin','heap-return-public.bin'}|set('")
    schema=change(schema,'NEW=set(range(49,81))|set(range(145,157))','NEW=set(range(49,105))|set(range(157,169))')
    schema=change(schema,'QPRE=QUERY-{49,59,71,72,73,74,79,145}','QPRE=QUERY-{49,59,71,72,73,74,79}')
    schema=change(schema,'QCALLED=QUERY-{49,50,59,60,71,72,73,74,79,80,145}','QCALLED=QUERY-{49,50,59,60,71,72,73,74,79,80}')
    schema=change(schema,'QCOMPLETE={0,9,10,55,56,57,58,70,75,76,77,78,151,152,153,154,155,156}','QCOMPLETE={0,9,10,55,56,57,58,70,75,76,77,78,*range(81,105),*range(157,169)}')
    schema=change(schema,'QRETURN_BEFORE=QCOMPLETE-{55,70,151}','QRETURN_BEFORE=QCOMPLETE-{55,70}');schema=change(schema,'QRETURNED=QRETURN_BEFORE-{56,152}','QRETURNED=QRETURN_BEFORE-{56}')
    schema=change(schema,'SELECTOR={0,9,10,58,156}','SELECTOR={0,9,10,58,*range(81,105),*range(157,169)}\nUNWOUND=SELECTOR-{58}\nBEFORE_STORE={81,*range(85,93),157,158}\nMODEPUB=UNWOUND-BEFORE_STORE\nRETBEFORE={0,9,10,83,84,100,101,102,103,104,165,166,167,168}\nINITRET={0,9,10,84,102,167,168}')
    marker='COPY_COUNTS={m:0 for m in REQUESTS}'
    counts="COUNTS.update({58:31});COUNTS.update({m:31 for m in BEFORE_STORE});COUNTS.update({m:32 for m in MODEPUB});COUNTS.update({0:35,9:35,10:35,98:33,162:33,163:33,83:34,99:34,100:34,103:34,104:34,164:34,165:34,84:35,101:35,102:35,166:35,167:35,168:35})\n"
    schema=change(schema,marker,counts+marker)
    schema=change(schema,"result['scenarios']==98 and result['malformed_token_denials']==20","result['scenarios']==122 and result['malformed_token_denials']==22")
    schema=change(schema,'selector_returns=0','selector_returns=initializer_returns=mode_stores=initializer_reads=0')
    schema=change(schema,'ev=11 if mode in SELECTOR','ev=13 if mode in INITRET else 12 if mode in MODEPUB else 11 if mode in SELECTOR')
    schema=change(schema,'mode if mode>=145','mode if mode>=157');schema=change(schema,'int(mode!=156)','int(mode!=168)');schema=change(schema,'registry[17]==int(mode==40)','registry[17]==int(mode in {40,103})')
    schema=change(schema,'qw[3]==q[2]^(1 if mode in {64,147} else 0)','qw[3]==q[2]^(1 if mode in {64,95} else 0)')
    schema=change(schema,'if mode==65:changed[0]^=1','if mode==65:changed[0]^=1\n            if mode==96:changed[4]^=1')
    start=schema.index('major=qw[18];v=');end=schema.index(",'Source POP/LEAVE/RET",start)
    schema=schema[:start]+"flags=0x95;need(after[:4]==(1,before[1],before[2],before[3]) and after[4:8]==(0x2000185c,before[5],before[6],before[7]) and after[8]&0x8d5==flags and after[9]==0x78001843"+schema[end:]
    schema=change(schema,'        expected|={case+\'/\'+name for name in CASE_FILES}',(HERE/'check_return.inc').read_text()+'\n        expected|={case+\'/\'+name for name in CASE_FILES}')
    schema=change(schema,'selector_returns+=q[8]','selector_returns+=q[8];initializer_returns+=progress[6];mode_stores+=progress[3];initializer_reads+=int(mode in INITRET|{101,166})')
    schema=change(schema,'status[7]==98+diagnostic','status[7]==122+diagnostic');schema=change(schema,'return result,len(expected),created,queried,output_commits,selector_returns','return result,len(expected),created,queried,output_commits,selector_returns,initializer_returns,mode_stores,initializer_reads')
    main=main.replace("native['native_scenarios'] == 196","native['native_scenarios'] == 244").replace("'native_scenarios':196","'native_scenarios':244").replace('actual==396','actual==492').replace("'actual_hardware_pairs':396","'actual_hardware_pairs':492").replace("'hardware_pairs':396","'hardware_pairs':492").replace('range(1,99)','range(1,123)').replace('98+diagnostic','122+diagnostic').replace('case-99/heap-status.bin','case-123/heap-status.bin')
    main=change(main,'actual_heaps=actual_queries=actual_output_commits=actual_selector_returns=0','actual_heaps=actual_queries=actual_output_commits=actual_selector_returns=actual_initializer_returns=actual_mode_stores=actual_initializer_reads=0')
    main=change(main,'result, count, heaps, queries, output_commits, selector_returns = semantic_inventory','result, count, heaps, queries, output_commits, selector_returns, initializer_returns, mode_stores, initializer_reads = semantic_inventory')
    main=change(main,'actual_selector_returns+=selector_returns','actual_selector_returns+=selector_returns;actual_initializer_returns+=initializer_returns;actual_mode_stores+=mode_stores;actual_initializer_reads+=initializer_reads')
    main=change(main,'len(inventory_tests)==56','len(inventory_tests)==68');main=change(main,"'inventory_request_denials':56","'inventory_request_denials':68")
    main=change(main,"'actual_selector_RETs':actual_selector_returns","'actual_selector_RETs':actual_selector_returns,'actual_initializer_RETs':actual_initializer_returns,'actual_source_mode_stores':actual_mode_stores,'actual_initializer_RETURN_WORD_reads':actual_initializer_reads")
    main=change(main,"'guest_heap_mode_global_published':False","'guest_heap_mode_global_published':True,'heap_initializer_completed_for_measured_mode1':True,'fragment_caller_TEST_executed':False")
    extra="""                for filename,offset,label in (('heap-return-progress.bin',12,'private_genuine_mode_store'),('heap-return-progress.bin',20,'genuine_RET_before_read'),('heap-return-progress.bin',24,'genuine_initializer_RET'),('heap-return-progress.bin',28,'live_token_after_actual_cleanup'),('heap-return-public.bin',12,'public_source_mode_value'),('heap-return-public.bin',20,'public_initializer_return'),('heap-accesses.bin',31*20+8,'literal_mode_store_value'),('heap-accesses.bin',34*20+8,'genuine_initializer_RETURN_WORD'),('heap-events.bin',11*16+12,'mode_store_event'),('independent-after/page-2013483008.bin',4,'complete_genuine_mode_global_page'),('independent-after/page-536875008.bin',0x858,'original_fragment_return_word'),('heap-create-before/heap-provider.bin',0x49,'immutable_existing_success_source')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
"""
    main=change(main,'                for field,value in',extra+'                for field,value in')
    header,main=adapt(header,main,change)
    (HERE/'check_schema.inc').write_text(schema,encoding='utf-8');(HERE/'check_main.inc').write_text(main,encoding='utf-8');(HERE/'check_header.inc').write_text(header,encoding='utf-8');(HERE/'check.py').write_text(header+schema+'\n\n'+main,encoding='utf-8')
if __name__=='__main__':main()
