"""Resolve the sealed frontier's actual literal-contract artifact explicitly."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 parent=R/'reports/m4-formatting-source/persistent-model-r1';assert sha(parent/'report.json')=='4beab5397b60936c12ca983980e22a1f37d6bfe7452a216046dbe4627cebdcf7'
 old=json.loads((parent/'report.json').read_bytes());out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 text=Path(old['model']).read_text();a="instructions=checked(game['instructions'],game['instructions_sha256'])";b="instructions=checked(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json','4025c802c6f12a5ff6f81b096c0f1a5366fcb6e2c82e73f509f8853d8b8b92cc')";assert text.count(a)==1;text=text.replace(a,b)
 model=out/'persistent_model.py';model.write_text(text);files=old['files']|{str(parent/'report.json'):sha(parent/'report.json'),str(model):sha(model),str(Path(__file__).resolve()):sha(__file__)}
 report=old|dict(model=str(model),model_sha256=sha(model),files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
