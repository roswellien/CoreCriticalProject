"""Add explicit flag consumers and exact endpoint exports to frozen reader1."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True)
 parent=ROOT/'tools/m4-joint-startup131/compare_provider.py';target=parent.with_name('compare_provider_v2.py');assert not target.exists();text=parent.read_text();changes=[]
 def one(a,b):
  nonlocal text
  assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b);changes.append(dict(before=a,after=b))
 one('import mfc_source as MF','import mfc_source_v2 as MF\nimport flag_consumers as FC')
 one('loader_rows=[];ori=None;readers_closed=False','loader_rows=[];flag_rows=[];ori=None;readers_closed=False')
 one("     class ObservedMachine(G.Machine):\n      def step(self):\n       V.before_step(self);result=super().step();V.after_step(self);return result", """     class ObservedMachine(G.Machine):
      def __init__(self,*args,**kwargs):
       super().__init__(*args,**kwargs);self._source_undefined_flags={};self._source_flag_consumers=[]
      def step(self):
       row=self.program[self.cursor];consumer=FC.check(self,row,self._source_undefined_flags);domain=FC.advance(self,row,self._source_undefined_flags)
       if consumer:self._source_flag_consumers.append(dict(source_step=len(self.PCs),**consumer))
       V.before_step(self);result=super().step();V.after_step(self);self._source_undefined_flags=domain;return result""")
 one("counts['persistent131_sequences']+=1;F.finish(machine,responses,expected_callbacks,G);", "counts['persistent131_sequences']+=1;F.finish(machine,responses,expected_callbacks,G);flag_rows.append(dict(level=level,sequence=seq,consumers=machine._source_flag_consumers,final_undefined_flags=machine._source_undefined_flags));counts['explicit_defined_flag_consumers']+=len(machine._source_flag_consumers);")
 one("('MFC-source-derivations.json',extension.rows", "('Literal-defined-flag-consumers.json',flag_rows),('MFC-source-derivations.json',extension.rows")
 one("  passed=True\n except Exception:", "  pin(ROOT/'tools/m4-joint-startup131/flag_consumers.py');pin(ROOT/'tools/m4-joint-startup131/mfc_source_v2.py');pin(ROOT/'tools/m4-mfc1168-native/persistent_source_v2.py');pin(ROOT/'tools/m4-joint-startup131/prepare_source_v2.py');need(len(flag_rows)==12,'Every persistent source lifecycle has explicit before-step architectural flag checks')\n  passed=True\n except Exception:")
 one('complete_selected_source=True,','complete_selected_source=True,explicit_defined_flag_consumers=True,')
 ast.parse(text);target.write_text(text)
 files={str(p.resolve()):sha(p)for p in(Path(__file__),parent,target,parent.with_name('mfc_source.py'),parent.with_name('mfc_source_v2.py'),parent.with_name('flag_consumers.py'),ROOT/'tools/m4-mfc1168-native/persistent_source.py',ROOT/'tools/m4-mfc1168-native/persistent_source_v2.py')}
 report=dict(passed=True,scope='Unexecuted additive full131 source/provider with explicit architectural consumers; same canonical reader, same complete source equality',tool=str(target),parent_preparation=str(ROOT/'reports/m4-joint-startup131-source/preparation-r1/report.json'),parent_preparation_sha256=sha(ROOT/'reports/m4-joint-startup131-source/preparation-r1/report.json'),changes=changes,files=files,candidate_AFTER_machine_seed=False,per_phase_BEFORE_machine_seed=False,worker_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
