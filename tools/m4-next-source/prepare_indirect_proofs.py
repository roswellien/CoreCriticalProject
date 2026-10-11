"""Add observation-only literal CALL/RET derivations to ABI-safe source gates."""
from pathlib import Path
import hashlib,json
T=Path(__file__).resolve().parent
ROOT=T.parents[1]
pins={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def write(name,s):
 p=T/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s);pins[str(p.resolve())]=sha(p)

p=T/'compare_connected_v3.py';pins[str(p.resolve())]=sha(p);s=p.read_text()
s=one(s,'rows=[];FS_rows=[];header_rows=[]','rows=[];FS_rows=[];header_rows=[];indirect_rows=[]')
s=one(s,"  G=load('persistent54_game'","  V=load('literal120_indirect_trace',ROOT/'tools/m4-next-source/indirect_trace.py');pin(V.P);G=load('persistent54_game'")
s=one(s,'     class ObservedMachine(G.Machine):','     class ObservedMachine(G.Machine):\n      def step(self):\n       V.before_step(self);result=super().step();V.after_step(self);return result')
s=one(s,"     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-before/State.bin')", "     V.configure(machine,lambda model:projection(m,model.state),dict(level=level,sequence=seq))\n     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-before/State.bin')")
s=one(s,"     need(not stack and index==15,'All normal nested game frames close');counts['persistent120_sequences']+=1", "     need(not stack and index==15,'All normal nested game frames close');need(not machine.indirect_pending and len(machine.indirect_derivations)==6,'All six literal fixed indirect CALL/RET prefixes');indirect_rows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=6;counts['persistent120_sequences']+=1")
s=one(s,"(('FS-source-derivations.json',FS_rows),('new-header-derivations.json',header_rows))", "(('FS-source-derivations.json',FS_rows),('new-header-derivations.json',header_rows),('indirect-source-derivations.json',indirect_rows))")
write('compare_connected_v4.py',s)

p=T/'compare_original_game_v3.py';pins[str(p.resolve())]=sha(p);s=p.read_text()
s=one(s,'ownerrows=[];derivations=[];headerrows=[]','ownerrows=[];derivations=[];headerrows=[];indirectrows=[]')
s=one(s,"  O=own(ROOT/'tools/m4-mfc-source/compare_original_game.py'", "  V=own(ROOT/'tools/m4-next-source/indirect_trace.py','actual_original120_indirect_trace');pin(V.P);O=own(ROOT/'tools/m4-mfc-source/compare_original_game.py'")
s=one(s,'       def step(self):\n        if self.cursor','       def step(self):\n        V.before_step(self)\n        if self.cursor')
s=one(s,'        return super().step()','        result=super().step();V.after_step(self);return result')
s=one(s,";allocation_calls=[];api=reader.data", ";V.configure(machine,lambda model:(m.hardwarefx(m.proj(model.state)[0]),m.proj(model.state)[1]),dict(sequence=seq,phase=phase));allocation_calls=[];api=reader.data")
s=one(s,"      for carried_owner in list(fsowners.values())", "      need(not machine.indirect_pending,'Every genuine original indirect helper returns');indirectrows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=len(machine.indirect_derivations)\n      for carried_owner in list(fsowners.values())")
s=one(s,"('new-header-derivations.json',headerrows))", "('new-header-derivations.json',headerrows),('indirect-source-derivations.json',indirectrows))")
write('compare_original_game_v4.py',s)
p=T/'indirect_trace.py';pins[str(p.resolve())]=sha(p);pins[str(Path(__file__).resolve())]=sha(Path(__file__))
out=ROOT/'reports/m4-next-source/indirect-proof-preparation-r1';assert not out.exists();out.mkdir()
(out/'report.json').write_text(json.dumps(dict(passed=True,scope='Observation-only source CALL/RET derivation extensions; syntax checked, no capture/execution/admission',files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),files=pins)))
