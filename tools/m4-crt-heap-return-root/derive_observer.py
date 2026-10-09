"""One-time construction of fresh, reviewable root consumers."""
from pathlib import Path
HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'m4-crt-heap-version-root'
def replace(s,a,b):
    assert s.count(a)==1, (a,s.count(a))
    return s.replace(a,b)
s=(OLD/'ownership.py').read_text()
s=s.replace('"""Typed private heap lifecycle and measured finite native version response."""','"""Private heap ownership, measured API response and genuine return progress."""')
start=s.index('def witness('); end=s.index('\ndef phase_ownership')
s=s[:start]+s[start:end].replace('heap-version-','heap-return-').replace("row/'query-input.bin'","row/'heap-return-query-input.bin'").replace("row/'query-output.bin'","row/'heap-return-query-output.bin'")+s[end:]
s=replace(s,"tag.startswith(('heap-create-','heap-mode-','heap-version-'))", "tag.startswith(('heap-create-','heap-mode-','heap-version-','heap-return-'))")
s=replace(s,"tag.startswith('heap-version-')", "tag.startswith(('heap-version-','heap-return-'))")
s=replace(s,"'heap-create-after','entry-after-fault','retry-after'): q[14:16]=[1,1]", "'heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'): q[14:16]=[1,1]")
s=replace(s,"'heap-version-selector-return-after','heap-version-environment-before','heap-create-after','entry-after-fault','retry-after'):\n            q[16:18]", "'heap-version-selector-return-after','heap-version-environment-before','heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'):\n            q[16:18]")
s+='''

def phase_progress(tag, actual):
    closed = tag in ('heap-create-after','entry-after-fault','retry-after')
    active = tag.startswith(('heap-create-','heap-mode-','heap-version-','heap-return-')) or closed
    if not active: words = [0]*8
    else:
        before = tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before')
        words = [1,0,0,0,0,0,0,int(not before and not closed)]
        if tag.startswith('heap-return-') or closed and actual['selector_returned']:
            words[1:3] = [1,1]
            if tag != 'heap-return-mode-store-before': words[3:5] = [1,1]
            if tag not in ('heap-return-mode-store-before','heap-return-mode-store-after'): words[5] = 1
            if tag == 'heap-return-initializer-return-after' or closed: words[6] = 1
    return {'heap-return-progress.bin':struct.pack('<8I',*words)}
'''
(HERE/'ownership.py').write_text(s)
s=(OLD/'positive.py').read_text().replace('heap-version-','heap-return-')
s=s.replace('from ownership import witness,phase_ownership,phase_query,TOKEN','from ownership import witness,phase_ownership,phase_query,phase_progress,TOKEN')
s=s.replace('RAW_QUERY,ENV_CALL','RAW_QUERY,MODE_GLOBAL,INITIALIZER_RET,ENV_CALL')
s=s.replace("row/'query-input.bin'","row/'heap-return-query-input.bin'").replace("row/'query-output.bin'","row/'heap-return-query-output.bin'")
s=s.replace("'query-input.bin','query-output.bin'","'heap-return-query-input.bin','heap-return-query-output.bin'")
s=replace(s,"F.words((row/'heap-return-job.bin').read_bytes(),64)","F.words((row/'heap-return-job.bin').read_bytes(),72)")
s=replace(s,"len(model['accesses']),2,11,5,10,0,pc,target", "len(model['accesses']),2,13 if good else 11,5,10,0,pc,target")
s=replace(s,'job[24:]==','job[24:64]==')
s=replace(s,"'Exact genuine source progress, query response, transport and privately closed heap')", "'Exact genuine source progress, query response, transport and privately closed heap')\n    F.require(job[64:]==(int(good),int(good),int(good),int(good),int(good),int(good),8,4),\n              'Genuine selector unwind, source publication and initializer return progress')")
s=s.replace("len(phases)==40", "len(phases)==(44 if good else 40)").replace('Exact full40-checkpoint','Exact complete ordinary checkpoint')
s=replace(s,"files.update(phase_ownership(tag,actual));files.update(phase_query(tag,actual,model))", "files.update(phase_ownership(tag,actual));files.update(phase_query(tag,actual,model));files.update(phase_progress(tag,actual))")
s=replace(s,"('heap-create-','heap-mode-','heap-return-')", "('heap-create-','heap-mode-','heap-version-','heap-return-')")
s=s.replace('Genuine selector returned; heap mode publication remains unadmitted','Genuine heap initializer returned; fragment caller continuation remains unadmitted')
s=s.replace('Truthful original selector RET or environment CALL boundary','Truthful original initializer RET or environment CALL boundary')
s=replace(s,"raw=b''.join(struct.pack('<4I',*v) for v in events)", "if good: events.extend([(12,0x780039eb,MODE_GLOBAL,1),(13,INITIALIZER_RET,SOURCE_RETURN,0x20001858)])\n    raw=b''.join(struct.pack('<4I',*v) for v in events)")
s=replace(s,"'heap-mode-lower-input.bin':bytes(4096)}", """'heap-mode-lower-input.bin':bytes(4096),
        'heap-version-job.bin':struct.pack('<64I',*([0]*24),FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,21,84,
            0,0x780058b5,PROBE_CALL,PROBE_RETURN,QUERY_CALL,QUERY_SLOT,RAW_QUERY,QUERY_RETURN,0,0,86,2086,
            0,0,0,0,0,0,0,0,0,0,26,23,8,3,ENV_CALL,ENV_SLOT,0x345e6,0x7800ccc5,148,2086),
        'heap-version-accesses.bin':bytes(1280),'heap-version-api-accesses.bin':bytes(160),
        'heap-version-events.bin':bytes(256),'heap-version-undefined.bin':bytes(32),'heap-version-scheduler.bin':bytes(32),
        'heap-version-witness.bin':bytes(128),'heap-version-lower-input.bin':bytes(4096),
        'heap-version-query-witness.bin':bytes(160),'heap-version-output-accesses.bin':bytes(1280),
        'query-input.bin':bytes(148),'query-output.bin':bytes(148)}""")
s=s.replace("('heap-create-registry.bin','heap-mode-registry.bin')", "('heap-create-registry.bin','heap-mode-registry.bin','heap-version-registry.bin')")
s=s.replace("'heap','heap-create','heap-mode')", "'heap','heap-create','heap-mode','heap-version')")
s=s.replace("{'heap-create-registry.bin','heap-mode-registry.bin','input.bin'", "{'heap-create-registry.bin','heap-mode-registry.bin','heap-version-registry.bin','heap-version-reason.txt','input.bin'")
s=replace(s,"struct.unpack_from('<I',model['memory'][0x78035000],4)[0]==0,'Heap-mode global not published by unexecuted caller'", "struct.unpack_from('<I',model['memory'][0x78035000],4)[0]==int(good),'Literal source mode1 publication or authentic alternate frontier'")
s=s.replace('genuine_source_RETs=2 if good else 1','genuine_source_RETs=3 if good else 1').replace('checkpoints=40','checkpoints=len(phases)')
s=s.replace('heap_mode_published=False,','heap_mode_published=good,').replace('heap_initializer_RET=False,','heap_initializer_RET=good,initializer_value=1 if good else None,fragment_caller_executed=False,')
(HERE/'positive.py').write_text(s)
s=(OLD/'observe.py').read_text().replace('m4-crt-heap-version-root','m4-crt-heap-return-root')
s=s.replace("'heap_version_fixed_ancillary'", "'heap_return_fixed_ancillary'")
s=replace(s,"('reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json','fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154')", "('reports/m4-crt-heap-version-root/root-acceptance-r1/report.json','cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1')")
s=replace(s,"('reports/m4-crt-heap-version-recovery/recovery-r1/report.json','90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f')", "('reports/m4-crt-heap-return-recovery/recovery-r1/report.json','c285ece7e08e2c152735629c48aae461d9f28d006895cf87e9f5157b23053684')")
s=replace(s,"('reports/m4-crt-heap-version-review/source-r1/report.json','38ecbbab533d662baa34a7079a864a2ecb0729abb4cdb3a8635ec51e83c44fa7')", "('reports/m4-crt-heap-return-review/source-r3/report.json','814f2fb571baf2c60f88905204bf28ae1552a4e1a1b0d4fe3a2584f8525a8904')")
s=s.replace('i+121','i+133').replace('checkpoints_per_row=40','checkpoints_per_qualifying_row=44').replace('new_compiled_source_bytes=60','new_compiled_source_bytes=0').replace('qualifying_executed_source_bytes=169','qualifying_executed_source_bytes=192').replace('new_guest_objects=8,prior_guest_objects_preserved=30','new_guest_objects=0,prior_guest_objects_preserved=38')
s=s.replace('qualifying_source_PCs=51,qualifying_source_accesses=31','qualifying_source_PCs=59,qualifying_source_accesses=35').replace('qualifying_genuine_source_RETs=2','qualifying_genuine_source_RETs=3')
s=s.replace('heap_mode_global_published=False,heap_initializer_RET=False,heap_initialized=False',"heap_mode_global_published=ordinary_returned>0,heap_initializer_RET=ordinary_returned>0,\n            ordinary_initializer_RET_sequences=sum(row['heap_initializer_RET'] for row in rows),\n            fragment_caller_executed=False,full_heap_allocator_initialized=False,heap_initialized=False")
s=s.replace('native version-query gate','native source heap-mode publication and initializer return gate').replace('Delegated version bridge author','Delegated heap-return author')
(HERE/'observe.py').write_text(s)
