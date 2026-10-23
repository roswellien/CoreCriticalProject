"""Cold MFC ordinary code/data admission supplement, no imports/readers."""
from pathlib import Path
import hashlib,json,ast,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={};deferred={};reads=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('transport.json','manifest.json','bundle.json');v=sha(p);assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 source=pin(R/'tools/m4-original141-source/mfc_source141_v1.py');tree=ast.parse(source.read_text());literal_paths=set()
 # Record every direct literal project reference, including retained footer
 # pin-only comparers. Dynamic current inputs are bound by strict3's exact map.
 for n in ast.walk(tree):
  if isinstance(n,ast.BinOp)and isinstance(n.op,ast.Div)and isinstance(n.left,ast.Name)and n.left.id=='R'and isinstance(n.right,ast.Constant)and isinstance(n.right.value,str):literal_paths.add(n.right.value)
 for rel in sorted(literal_paths):
  p=R/rel
  if p.is_file():pin(p);reads.append(rel)
 probe=pin(R/'reports/m4-mfc1168-probe/validation-r6/report.json');old=json.loads(probe.read_bytes());assert old['passed']and old['counts']['literal_reached_instructions']==142 and old['source_AFTER_seed']is False
 for p,h in old['files'].items():
  q=Path(p)
  if q.suffix.lower()in('.mwb','.mwi','.zip')or q.name in('transport.json','manifest.json','bundle.json'):deferred[p]=h
  else:pin(q,h)
 current=pin(R/'reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c');v=json.loads(current.read_bytes());assert v['passed']and v['reader_closed']and v['counts']['MFC_original_phases']==6
 # Whole current genuine raw MFC export files are ordinary, retained in strict
 # validation.files. No canonical archive or sealed payload is opened here.
 rawbase=current.parent/'actual-MFC-inputs'
 for p,h in v['files'].items():
  q=Path(p).resolve()
  if q.is_relative_to(rawbase):pin(q,h)
 for p in [current.parent/'fresh-MFC-observations.json',R/'reports/m4-original141-source/root-input-metadata-r1/report.json',R/'reports/m4-original141-source/root-input-metadata-r1/contracts.json',R/'reports/m4-original141/source-preparation-r6/pages.bin',R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py',R/'tools/m4-formatting-source/flag_domain.py',Path(sys.executable),Path(__file__).resolve()]:pin(p)
 interpreter=ast.parse((R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py').read_text());imports=[]
 for n in ast.walk(interpreter):
  if isinstance(n,ast.Import):imports.extend(alias.name for alias in n.names)
  elif isinstance(n,ast.ImportFrom):imports.append(n.module)
 assert set(imports)=={'copy','hashlib','json','pathlib','struct'},'No hidden project cold interpreter import'
 q=out/'required-ordinary-files.json';q.write_text(json.dumps(files,indent=2)+'\n');digest=sha(q)
 recipe='ROOT review/rehash supplement before MFC import, merging with exact current source4 ordinary admission and current configuration. Main MFC literal helper unchanged: physical142 cached instruction program and sourcePC closure,6 own currentphase15,7normal+4API percase,whole actualborrowedbackings/nonstackproviders/CPUFXENV/FS/CS24 andsourcewrittenframe equality retained. Direct retained/footer file references enumerated fromAST; allcurrent actual-MFC-inputs raw files physically pinned through strict3; conservative historical probe ordinary physical dependencies additionally pinned, never used as current BEFORE. No archive/payload/source helper import/source execution during preparation. ROOT narrow MFC6 then widgets42; subsequent manifest reuse only independently exact current passed threefamilies.\n'
 (out/'ROOT-recipe.txt').write_text(recipe);r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,current_original_validation_sha256=sha(current),current_MFC_literal_source_rows=142,current_MFC_cases=6,direct_project_literal_read_paths=reads,cold_interpreter_standard_imports=sorted(imports),required_ordinary_files=str(q),required_ordinary_files_sha256=digest,deferred_canonical_identities=deferred,files={str(source):sha(source),str(probe):sha(probe),str(current):sha(current),str(q):digest,str(out/'ROOT-recipe.txt'):sha(out/'ROOT-recipe.txt'),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),ordinary_files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
