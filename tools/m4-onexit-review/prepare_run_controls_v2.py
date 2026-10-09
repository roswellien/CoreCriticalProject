"""Add direct pressure ownership and physical API checks to frozen controls."""
from pathlib import Path
H=Path(__file__).parent
p=H/'run_controls_v2.py';assert not p.exists();s=(H/'run_controls.py').read_text()
a="                    changed_API_records=[]"
b='''                    if selected==9:
                        pressure=archive.data('case-9/first-pressure.bin');need(len(pressure)==256*96,'Exactly256 genuine bounded research pressure blocks')
                        pressure_rows=list(struct.iter_unpack('<12Q',pressure));native_owned={a[7] for a in allocations}
                        need(len({q[4] for q in pressure_rows})==256,'Every actual research pressure block is distinct')
                        for n,q in enumerate(pressure_rows):
                            need(q[:4]==(1,n,heap[6],128) and q[4] and q[4]%16==0 and q[4] not in native_owned
                                 and 128<=q[5]<=4096 and q[7]==1 and q[8]!=0 and not any(q[10:]),
                                 'Actual research pressure private heap/pointer/extent and one successful independent release')
                        for n,(requested,alias) in enumerate((('HeapAlloc','RtlAllocateHeap'),('HeapSize','RtlSizeHeap'),('HeapFree','HeapFree'))):
                            actual_before=e.identity(archive,f'case-9/first-pressure-{n}-before',pin)
                            actual_after=e.identity(archive,f'case-9/first-pressure-{n}-after',pin)
                            need(actual_before==actual_after,'Actual research pressure API identity stable')
                            rva,forward=e.export(Path(actual_before[2]),alias)
                            need(not forward and actual_before[1]+rva==actual_before[0],'Exact physical direct owning research API alias export')
                            named=pin(Path('C:/Windows/System32/kernel32.dll'));named_rva,named_forward=e.export(named,requested)
                            if requested!='HeapFree':need(named_forward=='NTDLL.'+alias,'Exact physical research allocator forwarder')
                            else:need(not named_forward,'Exact physical research free direct named export')
                            metrics['physical_API_proofs']+=1
                    changed_API_records=[]'''
assert s.count(a)==1;s=s.replace(a,b)
a="                    need(changed_API_records,'Actual changed provider API records exist in every scenario')"
b=a+"\n                    if selected==9:need(any(archive.words(prefix+f'registry-growth-{n}-witness.bin',32,'Q')[18] for n in range(after[14])),'Stale alias control occurs only after genuine physical HeapReAlloc movement')"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("schema='mw34-onexit-independent-compiled-controls-v1'","schema='mw34-onexit-independent-compiled-controls-v2'")
s=s.replace("API_response_injection=False,actual_API_null_failure_claimed=False,callback_execution=False,","API_response_injection=False,actual_API_null_failure_claimed=False,callback_execution=False,\n                    research_pressure_scope='Scenario9 only:256 genuine128-byte allocations on exact live private heap, no guest alias/source API changes; each independently released and physical API identity authenticated',")
p.write_text(s)
print('Derived fresh actual pressure controls checker')
