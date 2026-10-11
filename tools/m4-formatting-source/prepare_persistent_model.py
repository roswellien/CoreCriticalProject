"""Compose literal normal provider semantics with the accepted persistent machine."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 source=R/'tools/m4-formatting-source/provider_model.py';text=source.read_text()
 start=text.index("sp=importlib.util.spec_from_file_location");end=text.index("REC=",start)
 text=text[:start]+"sp=importlib.util.spec_from_file_location('accepted125_format_model',R/'tools/m4-tree-source/game_model_v4.py')\nG=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)\nI=G.I;begin_root=G.begin_root;complete_root=G.complete_root\n"+text[end:]
 text=text.replace('def source_program():','def provider_program():',1)
 anchor='class Machine(I.Machine):';assert text.count(anchor)==1;text=text.replace(anchor,'class Machine(G.Machine):',1)
 text+= '''

def checked(path,digest):
 raw=Path(path).read_bytes();I.need(hashlib.sha256(raw).hexdigest()==digest,'Frozen formatting source input');return json.loads(raw)

def source_program():
 program,callbacks=G.source_program();provider,_=provider_program()
 game=checked(R/'reports/m4-formatting-frontier/recovery-r1/report.json','8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15')
 instructions=checked(game['instructions'],game['instructions_sha256'])
 for row in list(provider.values())+instructions['instructions']:
  pc=row['pc'];I.need(pc not in program or program[pc]==row,'Identical literal accepted/additive formatting row');program[pc]=row
 cb=checked(R/'reports/m4-formatting-source/callbacks-r1/report.json','6cb0a2731d1d682d2af7794ae8d36493ebdaf790d1b6a4a73f3312b9ab9f2eb9')
 data=checked(cb['callbacks'],cb['callbacks_sha256'])
 for pc,offsets in data['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical additive undefined flag callback order');callbacks[pc]=offsets
 return program,callbacks
'''
 model=out/'persistent_model.py';model.write_text(text)
 files={str(p.resolve()):sha(p)for p in(source,Path(__file__),model,R/'tools/m4-tree-source/game_model_v4.py')}
 report=dict(passed=True,scope='Unexecuted composition; provider methods inherited over accepted125 Machine with exact literal rows and callbacks',model=str(model),model_sha256=sha(model),files=files,executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
