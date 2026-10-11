"""Observe genuine NULL-free source instruction entry/RET without model seeds."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'tools/m4-container-source/compare_original_game.py';q=p.with_name('compare_original_game_v2.py');assert not q.exists();s=p.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a[:80];s=s.replace(a,b)
one("lookup={r['entry']:r for r in roots};","lookup={r['entry']:r for r in roots};\n  for item in json.loads(pin(BASE/'allocation-interface-r1/string-inputs.json','b355761251799f245daf8a74dbef07ae008863deb1e2f88c4723af13090ab9f6').read_bytes()):lookup[item['root']]['string']=item\n  ")
one("actual_events=reader.data(f'phase/{seq}/{phase}/fs-events.bin');event_index=[0];event_derivations=[]","actual_events=reader.data(f'phase/{seq}/{phase}/fs-events.bin');event_index=[0];event_derivations=[];nullsnapshots=reader.data(f'phase/{seq}/{phase}/nullfree-snapshots.bin');null_index=[0]")
one('class PrefixMachine(G.Machine):','''class PrefixMachine(G.Machine):
       def step(self):
        if self.cursor in(0x78001390,0x78001424):
         i=null_index[0];need((i+1)*628<=len(nullsnapshots),'One authentic NULL-free entry/RET snapshot per literal source instruction');r=nullsnapshots[i*628:(i+1)*628];cpu=list(self.projected_cpu());cpu[9]=self.cursor;need(tuple(cpu)==words(r,32,10),'Every NULL-free source-derived CPU GPR/flags/PC at actual entry/RET');need(self.bytes(self.reg('esp'),16)==r[612:628],'Actual true nested CRT/MFC/game source CALL/RET frame words');need(self.bytes(0x7ffde000,4)==r[24:28],'Source normal NULL-free restores authentic original FS0');fx,env=m.proj(self.state);need(m.hardwarefx(fx)==r[72:584]and env==r[584:612],'Entire actual NULL-free entry/RET FX/ENV from original BEFORE');null_index[0]+=1;counts['NULLfree_source_CPU_FX_ENV_frame_snapshots']+=1
        return super().step()''')
one("machine.run(stop=lambda x:x.cursor==0x78004a36,api=finite_malloc);","machine.run(stop=lambda x:x.cursor==0x78004a36,api=finite_malloc);need(null_index[0]*628==len(nullsnapshots),'All and only actual true NULL-free entry/RET snapshots derive from BEFORE');")
one("owner=allocation_calls[0];raw=bytes.fromhex(source['bytes_hex']);","owner=allocation_calls[0];raw=bytes.fromhex(source['bytes_hex']);actual_owned=reader.data(f'phase/{seq}/{phase}/strings/{entry}/bytes.bin');need(machine.bytes(owner['pointer'],owner['capacity'])==actual_owned,'Every owned original duplicated byte and untouched true initial API padding');")
q.write_text(s)
