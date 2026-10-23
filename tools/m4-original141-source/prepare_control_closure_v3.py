"""ROOT-only32-control closure plus actual cold retained source lazy imports.

No model import or source execution; uses measured TREE148 import/metadata
closure supplement, and retained constructor-specific descriptor inputs.
"""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('transport.json','index.json','payload.bin');v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 base=pin(R/'reports/m4-original141-source/root-control-closure-r1/required-ordinary-files.json')
 for p,h in json.loads(base.read_bytes()).items():pin(p,h)
 inventorypath=pin(R/'reports/m4-original141-tree-source/import-inventory-r2/report.json','e999db06968951368c1202fd67842e57f32ebfd8ad514a2ea8f4cdb38818f1c2');inventory=json.loads(inventorypath.read_bytes());assert inventory['passed']and inventory['actual_cold_import_and_metadata_reads']==148 and inventory['source_machine_constructed']is False and inventory['source_machine_executed']is False and inventory['ordinary_reader_opened']is False and inventory['canonical_reader_opened']is False and inventory['all_cache_reads_refused']is True
 for p,h in inventory['files'].items():pin(p,h)
 assert files[str(R/'tools/m4-strings-review/provider_model.py')]=='c921a84120077b8810a4060e48cd12eb863aa10f031e85819409fc165bf8cb13'
 assert str(R/'tools/m4-onexit-review/provider_model.py')in files
 pin(__file__);q=out/'required-ordinary-files.json';q.write_text(json.dumps(files,indent=2)+'\n');required_sha=sha(q)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,expected_controls=32,retained_constructor_specific_closure=True,measured_cold_lazy_metadata_import_reads=148,no_claim_current_constructor_model_executed=True,initializer_credit=0,required_ordinary_files=str(out/'required-ordinary-files.json'),required_ordinary_files_sha256=required_sha,files={str(base):sha(base),str(inventorypath):sha(inventorypath),str(Path(__file__).resolve()):sha(Path(__file__)),str(out/'required-ordinary-files.json'):required_sha}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),ordinary_files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
