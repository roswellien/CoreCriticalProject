"""New closed heap corpus/inventory contract; frozen hardware validator unchanged."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
HERE=Path(__file__).absolute().parent
text=(ROOT/'tools/m4-crt-locale-default-contract/review/check.py').read_text()
text=text.replace('.parents[3]','.parents[2]').replace('reports/m4-crt-locale-default-contract/review','reports/m4-crt-heap-init-review')
start=text.index('REQUESTS =')
end=text.index('def main(',start)
contract='''REQUESTS = [0]*6 + list(range(109,121)) + list(range(1,49))
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin heap-fragment.bin heap-provider.bin'.split()) | {f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin heap-accesses.bin heap-events.bin heap-undefined-sites.bin heap-scheduler.bin heap-status.bin'.split())
BASE_PHASES=set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after heap-before heap-projected heap-after'.split())
PROVIDER_PHASE={0,3,4,19,20,21,22,23,24,25,27,28,29,114,115,116,117,118,119,120}
API_PHASE={0,3,4,19,20,21,22,23,24,25,118,119,120}
API_REACHED={0,4,22,23,24,25,120}
COUNTS={0:8,1:0,2:1,3:8,4:8,5:0,6:0,7:0,8:0,9:0,10:0,11:1,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:8,20:8,21:8,22:8,23:8,24:8,25:8,26:2,27:7,28:8,29:4,30:0,31:0,32:0,109:0,110:0,111:0,112:1,113:2,114:3,115:3,116:3,117:4,118:8,119:8,120:8}
COUNTS.update({m:0 for m in range(33,49)})

def need(value,why):
    if not value: raise ValueError(why)
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def semantic_inventory(reader,records):
    need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed independently authored native completion marker')
    result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==66 and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,'Exact independent fixture result domain')
    need(type(result['checks']) is int and result['checks']>0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials']==25,'Exact actual assertion and malformed-token domain')
    expected={'COMPLETE','controls.json'}
    for number,mode in enumerate(REQUESTS,1):
        case=f'case-{number}'
        need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Fixed independent case request order')
        status=struct.unpack('<26I',reader.read_bytes(case+'/heap-status.bin'))
        event_count=3 if mode in API_REACHED else 2 if mode in PROVIDER_PHASE or mode==12 else 1
        undefined_count=int(mode in PROVIDER_PHASE)
        need(status[:9]==(mode,mode if mode>=109 else int(mode==7),0x20001858+int(mode==5),0x20001860+int(mode==6),COUNTS[mode],event_count,undefined_count,4,0),'Exact independently specified heap progress, undefined sites and cleanup')
        need(status[11:15]==(1,0,int(mode!=32),int(mode in API_REACHED)) and status[15]==status[16],'Exact typed firstfault ownership and actual LastError')
        need(status[17:]==(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6,0x3461e,84),'Exact original source and raw IAT constants')
        if mode in API_REACHED:need(status[9:11]==(0x780039d0,0x7802e0a8),'First genuine unresolved HeapCreate diagnostic survives terminal fault')
        sites=struct.unpack('<8I',reader.read_bytes(case+'/heap-undefined-sites.bin'))
        need(sites==((0x780039bf,)+(0,)*7 if undefined_count else (0,)*8),'Exact source-artifact undefined AF ledger')
        scheduler=struct.unpack('<8I',reader.read_bytes(case+'/heap-scheduler.bin'))
        need(scheduler[0]==1 and scheduler[2:6]==(0x20001860,0x7800183c,0x20001860,0) and scheduler[6:]==(0x5bb514,0x20001860),'Explicit StatePC-only host scheduler without guest stack store')
        phases=set(BASE_PHASES)
        if mode in PROVIDER_PHASE:phases.add('heap-provider-before')
        if mode in API_PHASE:phases.add('heap-api-before')
        expected|={case+'/'+name for name in CASE_FILES}
        for phase in phases:expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
    need(reader.names()==tuple(sorted(expected)),'Exact independent complete request/phase/file inventory')
    T.validate_inventory(reader,records)
    return result,len(expected)

'''
text=text[:start]+contract+text[end:]
text=text.replace('locale-events.bin','heap-events.bin').replace('locale-status.bin','heap-status.bin').replace('locale-malloc-before','heap-api-before')
text=text.replace('missing_required_malloc_phase','missing_required_HeapCreate_phase').replace('invented_malloc_phase_on_early_fault','invented_HeapCreate_phase_on_early_fault')
text=text.replace('(97).to_bytes','(109).to_bytes')
text=text.replace("('active_boundary_depth',28),('active_locale_after_cleanup',44)","('active_boundary_depth',32),('active_heap_after_cleanup',48)")
text=text.replace("'malloc_body_executed':False,","'HeapCreate_executed':False,'heap_initialized':False,")
(HERE/'check.py').write_text(text,encoding='utf-8')
