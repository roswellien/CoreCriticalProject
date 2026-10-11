"""Extend the successful persistent proof through literal producer free and cleanup."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v4.py';s=p.read_text()
a="   reader.close();reader.entries.clear();reader.bundles.clear();reader=None\n";assert s.count(a)==1
extra='''   n.statecpu(machine.state,machine.projected_cpu());machine.cpu=B.cpu(machine.state)
   producer=responses.allocations[0];oldsp=machine.reg('esp');oldpc=machine.word(2472)
   machine.write(oldsp-4,producer['guest'],domain='research',pc=oldpc);machine.reg('esp',oldsp-4);machine.invoke_external(0x78001390,0xffffff80,responses);machine.reg('esp',oldsp);machine.cpu=B.cpu(machine.state)
   need(not producer['live'],'Literal producer free retires genuine acquired mapping');counts['literal_producer_source_frees']+=1
   for guest,section in reversed(list(responses.sections.items())):
    fact=responses.facts[responses.index];w=tuple(fact['words'])
    need(fact['name']=='DeleteCriticalSection'and w[:8]==(1,responses.index,0,0x7802e040,0x3446a,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,section['native'])and w[31]==1 and not fact['inputs']and not fact['outputs'],'Actual reverse-order same native CS cleanup lifecycle witness')
    need(section['initialized']and section['depth']==0 and not section['deletes'],'Live unheld source resource at genuine cleanup');section['deletes']=1;responses.index+=1;counts['actual_native_CS_deletes']+=1
   for owner in reversed(responses.allocations[1:]):
    fact=responses.facts[responses.index];w=tuple(fact['words'])
    need(fact['name']=='HeapFree'and w[:8]==(1,responses.index,0,0x7802e090,0x345ba,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,owner['native'])and w[31]==1 and not fact['inputs']and not fact['outputs'],'Actual reverse-order native formatter cleanup frees same acquired pointer')
    need(owner['live']and owner['extent']==16 and len(machine.memory[owner['guest']])==owner['mapped'],'Source live acquired owner alias remains present until real cleanup');owner['live']=False;machine.memory.pop(owner['guest']);responses.index+=1;counts['actual_native_formatter_cleanup_frees']+=1
   responses.complete();equal(bytes(machine.state),reader.data('sample.bin')[4272:7776],'Whole3504B actual outside-return postcleanup State derived by literal producer free');equal(machine.cpu,reader.data('sample.bin')[8800:8840],'Whole40B outside-return postcleanup CPU from literal source')
   actual_accesses=list(struct.iter_unpack('<IIQII',reader.data('actual-cleaned/locale-source-accesses.bin')));equal([tuple(r)for r in machine.accesses],actual_accesses,'Entire complete source ledger including literal producer cleanup')
   counts['whole_cleaned_source_access_records']+=len(actual_accesses);counts['complete_actual_lifecycles']+=1
   need(set(index)-set(seen)=={'registry-bootstrap-before'},'Every captured provider checkpoint predicted from bootstrap BEFORE')
'''
s=s.replace(a,extra+a)
target=R/'tools/m4-formatting-source/compare_native_fixture_v5.py';assert not target.exists();target.write_text(s)
