"""Retain every actual FS store and selected root checkpoint at its literal event."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v8.py';s=p.read_text()
a='     super().emit(event,**data)\n';assert s.count(a)==1
s=s.replace(a,a+"     if event=='write-after'and data.get('domain')=='source'and data.get('address')==self.word(G.I.BASE['fs']):self.snapshot('locale-source-seh-'+str(len(self.accesses))+'-after')\n")
a="machine.cpu=B.cpu(machine.state);record=records[phase*159716:(phase+1)*159716]";assert s.count(a)==1
s=s.replace(a,a+";machine.snapshot('registry-root-'+str(phase)+'-before')")
a='G.complete_root(machine,api=responses);machine.cpu=B.cpu(machine.state);machine.fx=projection(n,machine.state)[0]';assert s.count(a)==1
s=s.replace(a,a+";machine.snapshot('registry-root-'+str(phase)+'-after')")
target=R/'tools/m4-formatting-source/compare_native_fixture_v9.py';assert not target.exists();target.write_text(s)
